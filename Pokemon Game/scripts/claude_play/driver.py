"""Gameplay primitives: menus and text, walking, talking, battling.

Everything is done with ordinary button presses; the state reads in game.py
only decide which button to press next.
"""
import json
import struct
import time

import mapdata

OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
KEY = {"up": "UP", "down": "DOWN", "left": "LEFT", "right": "RIGHT"}


class Stuck(RuntimeError):
    pass


class Driver:
    def __init__(self, emulator, game, world, log_path):
        self.e = emulator
        self.g = game
        self.w = world
        self.log_file = open(log_path, "a")
        self.blocked = {}  # map id -> set of tiles learned to be impassable

    # -- logging --------------------------------------------------------------
    def log(self, event, **data):
        rec = dict(t=round(time.time(), 2), event=event, **data)
        self.log_file.write(json.dumps(rec) + "\n")
        self.log_file.flush()
        print(event, json.dumps(data)[:300], flush=True)

    def shot(self, label):
        path = self.e.capture(label)
        self.log("capture", file=path.name)
        return path

    def state(self, battle=True, halt=False):
        return self.g.snapshot(battle=battle, halt=halt)

    def here(self, s=None):
        s = s or self.state(battle=False)
        return self.w.by_num.get((s.group, s.num)), (s.x, s.y)

    # -- text and menus -------------------------------------------------------
    def field_ready(self, s):
        return s.cb2 == "CB2_Overworld" and not s.locked

    def advance_until(self, done, limit=400, key="A", label=None):
        """Press `key` until done(state) is true."""
        for i in range(limit):
            s = self.state()
            if done(s):
                return s
            if s.in_battle:
                return s
            self.e.tap(key, after=0.25)
        if label:
            self.shot(label)
        raise Stuck(f"advance_until: no progress after {limit} presses")

    def clear_text(self, limit=200, capture=None, frames=8):
        """Press A through dialogue until the player can move again (or a battle
        starts). With `capture`, screenshot up to `frames` messages, each after
        it has had time to print, so the dialogue itself is on record."""
        if capture:
            for n in range(frames):
                s = self.state()
                if self.field_ready(s) or s.in_battle:
                    return s
                time.sleep(0.9)
                self.shot(f"{capture}-{n + 1:02d}")
                self.e.tap("A", after=0.25)
        return self.advance_until(lambda s: self.field_ready(s), limit=limit, label="stuck-text")

    # -- walking --------------------------------------------------------------
    def step(self, direction, timeout=2.5):
        """Hold a direction until the player leaves the current tile; returns new state."""
        s0 = self.state(battle=False, halt=False)
        start = (s0.group, s0.num, s0.x, s0.y)
        self.e.key(KEY[direction], True)
        try:
            end = time.monotonic() + timeout
            while time.monotonic() < end:
                time.sleep(0.04)
                s = self.state(battle=False, halt=False)
                if (s.group, s.num, s.x, s.y) != start or s.cb2 != "CB2_Overworld" or s.locked:
                    return s
            return None
        finally:
            self.e.key(KEY[direction], False)

    def settle(self):
        """Wait until the player is standing still in control, handling any script."""
        for _ in range(60):
            time.sleep(0.12)
            s = self.state()
            if s.in_battle:
                return s
            if s.cb2 == "CB2_Overworld" and not s.locked:
                time.sleep(0.12)
                s2 = self.state()
                if (s2.x, s2.y, s2.group, s2.num) == (s.x, s.y, s.group, s.num) and not s2.locked:
                    return s2
            elif s.cb2 == "CB2_Overworld" and s.locked:
                self.e.tap("A", after=0.2)
        return self.state()

    def walk_path(self, map_id, goals, max_replans=40, on_event=None):
        """Walk on map_id to any tile in goals, learning blocked tiles as we go."""
        blocked = self.blocked.setdefault(map_id, set())
        for _ in range(max_replans):
            mid, pos = self.here()
            if mid != map_id:
                return mid, pos
            if pos in goals:
                return mid, pos
            m = self.live_map(map_id)
            dyn = set(blocked) | {(x, y) for x, y, *_ in m.objects}
            path = mapdata.bfs(m, pos, goals, frozenset(dyn - set(goals)))
            if path is None:
                raise Stuck(f"no path on {map_id} from {pos} to {sorted(goals)[:5]}")
            for d in path:
                dx, dy = mapdata.DIRS[d]
                target = (pos[0] + dx, pos[1] + dy)
                s = self.step(d)
                if s is None:
                    # Didn't move: something is there. Turned instead? try once more.
                    s = self.step(d, timeout=1.0)
                if s is None:
                    blocked.add(target)
                    self.log("blocked", map=map_id, tile=target)
                    break
                if s.in_battle or s.cb2 != "CB2_Overworld" or s.locked:
                    s = self.settle()
                    if s.in_battle and on_event:
                        on_event(s)
                    break
                newmid, newpos = self.here(s)
                if newmid != map_id:
                    self.settle()
                    return newmid, newpos
                if newpos != target:
                    break  # ledge, slide or a script moved us: replan
                pos = newpos
        return self.here()

    def go_map(self, route, on_event=None):
        """Follow a list of (map_id, how, arg) legs: ('edge', dir) or ('warp', (x, y), dir)."""
        for map_id, how, *rest in route:
            same_map_arrival = None
            if how == "warp":
                source = self.w.map(map_id)
                target = source.warp_at(*rest[0])
                if target and target[0] == map_id:
                    if not 0 <= target[1] < len(source.warps):
                        raise Stuck("invalid same-map warp destination")
                    same_map_arrival = (map_id, mapdata.warp_arrival(source, *source.warps[target[1]][:2]))
            for attempt in range(6):
                mid, pos = self.here()
                if mid != map_id:
                    break
                m = self.w.map(map_id)
                if how == "edge":
                    d = rest[0]
                    goals = set(rest[1]) if len(rest) > 1 else set(mapdata.edge_exits(m, d))
                    mid, pos = self.walk_path(map_id, goals, on_event=on_event)
                    if mid == map_id and pos in goals:
                        s = self.step(d)
                        self.settle()
                elif mapdata.trigger_entry(m, *rest[0]):
                    # Step-on warp: walking onto the tile is the warp, so approach it and step once.
                    before, push = mapdata.trigger_entry(m, *rest[0])
                    mid, pos = self.walk_path(map_id, {before}, on_event=on_event)
                    if mid == map_id and pos == before:
                        self.step(push)
                        time.sleep(1.0)
                        self.settle()
                else:
                    # A map split by a cliff can have the leg's warp out of reach: any of its warps to the
                    # same destination will do (e.g. a route's two cave doors). Doors are entered from
                    # their doorstep.
                    wanted = m.warp_at(*rest[0])
                    dest = (wanted or (None,))[0]
                    # Another room in the same map is not an interchangeable
                    # destination. Only paired mats sharing its target index
                    # are equivalent; external-map fallback is unchanged.
                    tiles = [tuple(rest[0])] + [(x, y) for x, y, d, di in m.warps
                             if d == dest and (dest != map_id or di == wanted[1]) and (x, y) != tuple(rest[0])]
                    for tile in tiles:
                        push = self.warp_push(m, tile)
                        before = (tile[0] - mapdata.DIRS[push][0], tile[1] - mapdata.DIRS[push][1])
                        goal = tile if m.walkable(*tile) and "DOOR" not in m.behavior(*tile) else before
                        try:
                            mid, pos = self.walk_path(map_id, {goal}, on_event=on_event)
                        except Stuck:
                            continue
                        if mid == map_id and pos == goal:
                            self.step(push)
                            time.sleep(1.0)
                            self.settle()
                        break
                if same_map_arrival is not None and self.here() == same_map_arrival:
                    break
            mid, pos = self.here()
            self.log("map", map=mid, pos=pos)

    def live_map(self, map_id):
        m = self.w.map(map_id)
        blocks = self.g.live_blocks(m.width, m.height)
        return m.with_live_blocks(blocks) if blocks else m

    # -- map graph travel ------------------------------------------------------
    def warp_push(self, m, tile):
        b = m.behavior(*tile)
        for word, d in (("SOUTH", "down"), ("NORTH", "up"), ("EAST", "right"), ("WEST", "left")):
            if word + "_ARROW" in b:
                return d
        return "up" if "DOOR" in b else "down"

    def warp_goal(self, m, tile):
        """(tile to walk to, direction to press) to take the warp at tile."""
        entry = mapdata.trigger_entry(m, *tile)
        if entry:
            return entry
        push = self.warp_push(m, tile)
        before = (tile[0] - mapdata.DIRS[push][0], tile[1] - mapdata.DIRS[push][1])
        return (tile if m.walkable(*tile) and "DOOR" not in m.behavior(*tile) else before), push

    def map_route(self, src, dst, pos=None):
        """Breadth-first route over map connections and warps.

        With pos (the player's tile on src), the search is over (map, position): a leg is only used if its
        exit is reachable on foot from there, so a map split by a cliff (a route whose halves only meet
        through a cave) is handled. Without pos it is the plain map-level search.
        """
        from collections import deque
        if pos is None:
            return self._map_route_maps(src, dst)
        start = (src, tuple(pos))
        prev, seen = {start: None}, {}
        q = deque([start])
        goal = None
        while q:
            cur = q.popleft()
            mid, pos = cur
            if mid == dst:
                goal = cur
                break
            m = self.w.map(mid)
            # Skip a position already covered by an explored one in the same part of this map.
            if any(mapdata.bfs(m, p, {pos}) is not None for p in seen.get(mid, [])):
                continue
            seen.setdefault(mid, []).append(pos)
            nexts = []
            for d, other, off in m.connections:
                if other not in self.w.map_ids:
                    continue
                om = self.w.map(other)
                exits = [t for t in mapdata.edge_exits(m, d) if mapdata.bfs(m, pos, {t}) is not None]
                by_arrival = {}
                for t in exits:
                    a = mapdata.across(m, om, d, off, t)
                    if om.inside(*a) and om.walkable(*a):
                        by_arrival.setdefault(a, []).append(t)
                for a, ts in by_arrival.items():
                    nexts.append(((mid, "edge", d, tuple(ts)), (other, a)))
            for x, y, dest, dw in m.warps:
                if dest not in self.w.map_ids:
                    continue
                stand, push = self.warp_goal(m, (x, y))
                if mapdata.bfs(m, pos, {stand}) is None:
                    continue
                dm = self.w.map(dest)
                if dw >= len(dm.warps):
                    continue
                nexts.append(((mid, "warp", (x, y), push), (dest, mapdata.warp_arrival(dm, *dm.warps[dw][:2]))))
            for leg, nxt in nexts:
                if nxt not in prev:
                    prev[nxt] = (cur, leg)
                    q.append(nxt)
        if goal is None:
            raise Stuck(f"no map route {src} -> {dst}")
        route, node = [], goal
        while prev[node]:
            node, leg = prev[node]
            route.append(leg)
        return route[::-1]

    def _map_route_maps(self, src, dst):
        from collections import deque
        prev = {src: None}
        q = deque([src])
        while q:
            cur = q.popleft()
            if cur == dst:
                break
            m = self.w.map(cur)
            legs = [((cur, "edge", d), other) for d, other, _ in m.connections if mapdata.edge_exits(m, d)]
            legs += [((cur, "warp", (x, y), self.warp_push(m, (x, y))), dest) for x, y, dest, _ in m.warps
                     if dest in self.w.map_ids]
            for leg, nxt in legs:
                if nxt not in prev:
                    prev[nxt] = (cur, leg)
                    q.append(nxt)
        if dst not in prev:
            raise Stuck(f"no map route {src} -> {dst}")
        route = []
        node = dst
        while prev[node]:
            node, leg = prev[node]
            route.append(leg)
        return route[::-1]

    def travel_to(self, dst, on_event=None):
        on_event = on_event or (lambda s: self.battle())
        for _ in range(12):
            mid, pos = self.here()
            if mid == dst:
                return
            for leg in self.map_route(mid, dst, pos):
                self.go_map([leg], on_event=on_event)
                if self.here()[0] != leg[0] and self.here()[0] == dst:
                    return
                if self.state().in_battle:
                    self.battle()
        if self.here()[0] != dst:
            raise Stuck(f"could not travel to {dst}")

    def heal_at_clinic(self):
        """Alderfield clinic nurse across the counter: stand at (7,4), face up, A, YES."""
        self.travel_to("MAP_ALDERFIELDCLINIC")
        self.walk_path("MAP_ALDERFIELDCLINIC", {(7, 4)})
        self.e.tap("UP", hold=0.05, after=0.3)
        self.e.tap("A", after=0.6)
        s = self.clear_text()
        self.log("healed", party=s.party)
        return s

    def talk(self, map_id, npc, answer_yes=True, clear=True):
        """Stand next to the NPC tile, face it and press A."""
        m = self.w.map(map_id)
        options = {}
        for d, (dx, dy) in mapdata.DIRS.items():
            t = (npc[0] - dx, npc[1] - dy)
            if m.walkable(*t):
                options[t] = d
        # Wild encounters on the way are fought (run26 lost the walk to one).
        for _ in range(6):
            mid, pos = self.walk_path(map_id, set(options), on_event=lambda s: self.battle())
            if pos in options or mid != map_id:
                break
        if pos not in options:
            raise Stuck(f"could not reach {npc} on {map_id}, at {pos}")
        face = options[pos]
        # Holding toward the NPC turns the player without moving (the NPC
        # blocks the tile); a too-short tap was seen to leave the player
        # facing elsewhere, so retry until a script actually starts.
        for attempt in range(4):
            self.e.tap(KEY[face], hold=0.15 + 0.05 * attempt, after=0.3)
            self.e.tap("A", after=0.5)
            s = self.state()
            if s.locked or s.in_battle or s.cb2 != "CB2_Overworld":
                label = f"talk-{map_id.removeprefix('MAP_').lower()}-{npc[0]}-{npc[1]}"
                return self.clear_text(capture=label) if clear else s
            self.log("talk-retry", map=map_id, npc=npc, attempt=attempt)
        raise Stuck(f"talking to {npc} on {map_id} started no script")

    # -- battles --------------------------------------------------------------
    def trainer_move(self, s):
        """Against trainers: lower a physical attacker's Attack (Baby-Doll Eyes,
        Charm or Growl), then attack with the strongest move. Lower it twice
        while we are healthy and the foe is above half HP, and again whenever
        the foe has boosted itself (Work Up) unless it is nearly knocked out
        (run16: a +2 Lillipup knocked out Piplup from 32/44 HP in one hit)."""
        c = self.g.c
        me, foe = s.mons[0], s.mons[1]
        atk_stage = foe["stages"][c["STAT_ATK"]] - c["DEFAULT_STAT_STAGE"]
        opening = me["hp"] * 10 > me["maxhp"] * 6 and foe["hp"] * 2 > foe["maxhp"] and atk_stage > -2
        boosted = atk_stage > 0 and foe["hp"] * 4 > foe["maxhp"] and me["hp"] * 3 > me["maxhp"]
        if opening or boosted:
            for move in (c["MOVE_BABY_DOLL_EYES"], c["MOVE_CHARM"], c["MOVE_GROWL"]):
                if move in me["moves"]:
                    slot = me["moves"].index(move)
                    if me["pp"][slot]:
                        return slot
        return self.best_move(s)

    def best_move(self, s):
        """Highest expected damage among moves with PP, by ROM power/type/STAB."""
        me, foe = s.mons[0], s.mons[1]
        best, best_score = None, -1.0
        for slot, (move, pp) in enumerate(zip(me["moves"], me["pp"])):
            if not move or not pp:
                continue
            info = self.moves.move(move)
            score = info["power"] * self.moves.effectiveness(info["type"], foe["types"])
            if info["type"] in me["types"]:
                score *= 1.5
            if info["category"] == 3:  # status move: only if nothing else has PP
                score = 0.01
            if score > best_score:
                best, best_score = slot, score
        return best if best is not None else 0

    def battle(self, choose_move=None, run_if=None, label="battle", catch_if=None, switch_if=None,
               never_b=False, capture_win=False):
        """Play a battle to the end with ordinary menu inputs.

        switch_if(s) -> True switches the lead out (POKeMON in the action
        menu) for the lowest-level healthy party member that turn.
        capture_win: screenshot each message once the foe's active Pokemon
        has fainted (faint, "defeated", the trainer's speech, prize money).
        never_b: advance text with A only. B also answers NO to "Use next
        Pokemon?" in a wild battle, which flees (seen in run41)."""
        choose_move = choose_move or self.best_move
        self.switch_pref = None
        shots = defeat_shots = win_shots = 0
        last = None
        idle = 0
        for _ in range(100):
            first = self.state()
            if first.in_battle and first.mons and first.mons[0]["level"] and first.mons[1]["level"]:
                break
            time.sleep(0.1)
        self.log("battle-start", flags=hex(first.battle_flags or 0),
                 foe=[(m["species"], m["level"]) for m in (first.mons or [])[1:2]],
                 me=[(m["species"], m["level"], m["hp"]) for m in (first.mons or [])[:1]],
                 moves=[(mv, pp) for mv, pp in zip(first.mons[0]["moves"], first.mons[0]["pp"]) if mv]
                 if first.mons else [])
        while True:
            s = self.state()
            if s.cb2 == "CB2_Overworld" and not s.in_battle:
                self.log("battle-end", party=s.party)
                return s
            if not s.in_battle:
                # Post-battle screens (move learning summary, evolution, Pokedex
                # registration, naming): B declines replacing a move; the naming
                # screen keeps the default name (START moves to OK); A advances
                # everything else.
                idle += 1
                cb = s.cb2 or ""
                if "Naming" in cb:
                    # Keep the species name: erase anything typed, then OK.
                    for _ in range(3):
                        self.e.tap("B", after=0.2)
                    self.e.tap("START", after=0.4)
                    self.e.tap("A", after=0.8)
                elif cb == "CB2_UpdatePartyMenu":
                    self.choose_replacement(s)
                else:
                    self.e.tap("B" if "Summary" in cb else "A", after=0.3)
                continue
            ctrl = s.controller
            if ctrl != last:
                idle = 0
                last = ctrl
            if ctrl == "HandleInputChooseAction":
                if shots < 3:
                    self.shot(f"{label}-action")
                    shots += 1
                if catch_if and catch_if(s):
                    # R throws the last-used ball (B_LAST_USED_BALL_BUTTON).
                    self.log("throw-ball", foe=(s.mons[1]["species"], s.mons[1]["level"], s.mons[1]["hp"]))
                    self.e.tap("R", hold=0.15, after=0.8)
                    continue
                if switch_if and switch_if(s):
                    self.log("switch-out", label=label, me=(s.mons[0]["species"], s.mons[0]["hp"]),
                             foe=(s.mons[1]["species"], s.mons[1]["level"], s.mons[1]["hp"]))
                    self.switch_pref = "fodder"
                    self.move_cursor(s.action_cursor, 2)
                    self.e.tap("A", after=0.8)
                    continue
                want = 3 if (run_if and run_if(s)) else 0
                self.move_cursor(s.action_cursor, want)
                self.e.tap("A", after=0.4)
            elif ctrl == "HandleInputChooseMove":
                slot = choose_move(s)
                me, foe = s.mons[0], s.mons[1]
                self.log("turn", label=label, me=(me["species"], me["level"], me["hp"], me["maxhp"]),
                         foe=(foe["species"], foe["level"], foe["hp"], foe["maxhp"]),
                         move=me["moves"][slot], pp=me["pp"][slot])
                self.move_cursor(s.move_cursor, slot)
                self.e.tap("A", after=0.6)
            else:
                idle += 1
                if (capture_win and win_shots < 16 and s.mons and len(s.mons) > 1
                        and s.mons[1]["level"] and s.mons[1]["hp"] == 0):
                    time.sleep(0.5)
                    self.shot(f"{label}-foe-down")
                    win_shots += 1
                if defeat_shots < 12 and s.party and not any(m["hp"] for m in s.party):
                    # The whole party has fainted: keep each defeat/whiteout
                    # message as evidence before advancing it.
                    time.sleep(0.5)
                    self.shot(f"{label}-defeat")
                    defeat_shots += 1
                # Text and animations: A advances messages; B declines
                # optional prompts (nickname, move replacement) safely.
                self.e.tap("A" if never_b or idle % 6 else "B", after=0.3)

    def choose_replacement(self, s):
        """Party menu during battle: pick a healthy Pokemon other than the one
        in battle (the menu shows battle order, so slot 0 is the active one):
        the highest level after a faint, the lowest level for a voluntary
        switch. Move the cursor to it, then A (choose) and A (SHIFT)."""
        healthy = [i for i, m in enumerate(s.party) if m["hp"] > 0 and i > 0]
        fodder = getattr(self, "switch_pref", None) == "fodder"
        self.switch_pref = None
        key = (lambda i: (s.party[i]["level"], i)) if fodder else (lambda i: (-s.party[i]["level"], i))
        target = min(healthy, key=key) if healthy else None
        if target is None:
            self.e.tap("B", after=0.4)
            return
        slot_addr = self.g.sym["gPartyMenu"] + self.g.off["pm.slotId"]
        for _ in range(8):
            cur = struct.unpack("<b", self.g.gdb.read(slot_addr, 1))[0]
            if cur == target:
                break
            self.e.tap("DOWN" if cur < target else "UP", after=0.25)
        self.log("replacement", slot=target, mon=s.party[target])
        self.e.tap("A", after=0.6)
        self.e.tap("A", after=1.0)

    def move_cursor(self, cur, want):
        # 2x2 grids: 0 top-left, 1 top-right, 2 bottom-left, 3 bottom-right.
        if (cur & 1) != (want & 1):
            self.e.tap("RIGHT" if want & 1 else "LEFT", after=0.15)
        if (cur >> 1) != (want >> 1):
            self.e.tap("DOWN" if want >> 1 else "UP", after=0.15)
