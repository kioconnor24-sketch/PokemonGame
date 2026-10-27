"""Connected-area graphical QA for an approved batch of maps.

Two layers, both derived from the built source of the batch (map.json warps
and connections, map.bin collision, tileset behaviours):

  static   Collision and pathfinding only, which the #125 source preflight
           explicitly leaves out. It finds ledges that land on a solid tile,
           seams where a walkable tile faces a solid one, exits (warps or
           connection seams) that no entry can reach, and one-way pockets: tiles
           a player can get into but never out of. It does not re-check warp
           targets, return indices or offset reciprocity (#125 does that).

  run      Real mGBA, ordinary controller input, read-only GDB observation.
           For every map it walks closed edges (must block), every
           connection-seam tile out and back (must return to the same tile),
           and every warp in and back. After each arrival it checks the
           follower is visible and that an exit is still reachable. It also
           probes static pockets (must strand) and the Start menu, and can
           SAVE. With --expect, a fresh process CONTINUEs and must restore
           the saved state.

  fixture  Applies a test-only placement (connections, warps, blocks) to a
           THROWAWAY engine tree only, i.e. a tree carrying the
           .map_qa_throwaway marker. Fixtures are never production map data.

The entry into a batch can be the disclosed DEV-only continue-warp save
fixture (`fixture-save`). It sets the engine's own CONTINUE_GAME_WARP on a copy
of a real save; no source or map changes.

usage:
  map_qa.py static  --engine E --map MAP_A [--map MAP_B ...] [--json OUT]
  map_qa.py fixture-save --engine E IN.sav OUT.sav MAP_ID X Y
  map_qa.py fixture --engine E FIXTURE.json
  map_qa.py run --engine E --rom ROM --build normal|release --scratch DIR --out DIR
                --map MAP_A [--map ...] [--save LABEL] [--expect SAVED.json]
  map_qa.py selftest --engine THROWAWAY_E --save REAL.sav --out DIR [--only NAME]
      For each map_qa_fixtures/*.json: restore the throwaway tree, apply the fixture,
      run the static layer, rebuild (CRIES=off), enter with the DEV continue-warp save,
      run in a fresh process (positives also SAVE, then a second fresh process CONTINUEs),
      and require positives to PASS and negatives to FAIL on the named check.
"""
import argparse
import json
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import time
from collections import deque

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mapdata  # noqa: E402

DIRS = mapdata.DIRS
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
REGION_UI_CONSTANTS = ("ITEM_TOWN_MAP", "BAG_KEYITEMS_COUNT", "POCKET_KEY_ITEMS",
                       "FLAG_SYS_POKENAV_GET", "FLAG_AVERON_LICENSE_FLY")
JUMP = {"MB_JUMP_SOUTH": "down", "MB_JUMP_NORTH": "up", "MB_JUMP_EAST": "right", "MB_JUMP_WEST": "left"}
MARKER = ".map_qa_throwaway"


# ---------------------------------------------------------------- static layer
def is_door(m, x, y):
    return "DOOR" in m.behavior(x, y)


def warp_push(m, x, y):
    """Direction to press to take the warp at (x, y)."""
    entry = mapdata.trigger_entry(m, x, y)
    if entry:
        return entry[1]
    b = m.behavior(x, y)
    for word, d in (("SOUTH", "down"), ("NORTH", "up"), ("EAST", "right"), ("WEST", "left")):
        if word + "_ARROW" in b:
            return d
    return "up"


def warp_stand(m, x, y):
    """Tile the player stands on to take the warp (for arrow warps and doors, also where it arrives)."""
    entry = mapdata.trigger_entry(m, x, y)
    if entry:
        return entry[0]
    if is_door(m, x, y) or not m.walkable(x, y):
        return (x, y + 1)
    return (x, y)


def warp_arrive(m, x, y):
    """Where a warp into (x, y) lands the player: on a step-on (trigger) warp, the warp tile itself."""
    return mapdata.warp_arrival(m, x, y)


def moves(m, x, y):
    """Tiles reachable in one press from (x, y): a walk or a ledge jump (no landing check, as in the engine)."""
    for d, (dx, dy) in DIRS.items():
        if not mapdata.can_walk_direction(m, (x, y), d):
            continue
        nx, ny = x + dx, y + dy
        if not m.inside(nx, ny):
            continue
        if m.walkable(nx, ny):
            yield nx, ny
        elif JUMP.get(m.behavior(nx, ny)) == d:
            yield nx + dx, ny + dy


def edge_tiles(m, direction, connection=None):
    """Walkable tiles on one edge; with connection=(other_id, offset), only those that connection spans.

    A map may have several connections on one side (Route 205 North opens down to two maps): the engine
    (GetIncomingConnection) uses the one whose span contains the tile, so each seam owns only its own tiles.
    """
    if direction in ("up", "down"):
        y = 0 if direction == "up" else m.height - 1
        tiles = [(x, y) for x in range(m.width) if m.walkable(x, y)]
    else:
        x = 0 if direction == "left" else m.width - 1
        tiles = [(x, y) for y in range(m.height) if m.walkable(x, y)]
    world = getattr(m, "world", None)
    if connection is None or world is None:
        return tiles
    other = world.map(connection[0])
    return [t for t in tiles if other.inside(*across(m, other, direction, connection[1], t))]


def uncovered_edge_tiles(m, direction):
    """Walkable edge tiles no connection on that side spans: a closed edge for the player."""
    spans = [(o, off) for d, o, off in m.connections if d == direction]
    covered = {t for c in spans for t in edge_tiles(m, direction, c)}
    return [t for t in edge_tiles(m, direction) if t not in covered]


across = mapdata.across


def state_moves(m, x, y, e):
    """(tile, elevation) states reachable in one press from (x, y) at elevation e: a walk or a ledge jump,
    with the engine's elevation rules (mapdata.step_elevation)."""
    for t in moves(m, x, y):
        if m.inside(*t) and m.walkable(*t):
            ne = mapdata.step_elevation(m, e, (x, y), t)
            if ne is not None:
                yield t, ne


def reach(m, starts, reverse=False):
    """Tiles reachable from starts (or, reverse, tiles that can reach a start), honouring elevations."""
    starts = [s for s in starts if m.inside(*s) and m.walkable(*s)]
    if reverse:
        levels = {mapdata.elevation_at(m, x, y) for y in range(m.height) for x in range(m.width)} | {0}
        # The player's elevation is the tile's own, except on a 15 (bridge) tile, which keeps the previous one.
        valid = lambda x, y: levels if mapdata.elevation_at(m, x, y) == 15 else {mapdata.elevation_at(m, x, y)}
        back = {}
        for y in range(m.height):
            for x in range(m.width):
                if m.walkable(x, y):
                    for e in valid(x, y):
                        for t in state_moves(m, x, y, e):
                            back.setdefault(t, []).append(((x, y), e))
        step = lambda s: back.get(s, [])
        first = [(s, e) for s in starts for e in valid(*s)]
    else:
        step = lambda s: list(state_moves(m, *s[0], s[1]))
        first = [(s, e) for s in starts for e in mapdata.start_elevations(m, s)]
    seen, queue = set(first), deque(first)
    while queue:
        for n in step(queue.popleft()):
            if n not in seen:
                seen.add(n)
                queue.append(n)
    return {s for s, _ in seen}


def map_points(m):
    """Entries and exits of one map: every warp's standing tile and every connection seam tile."""
    points = []
    for i, (x, y, dest, warp) in enumerate(m.warps):
        points.append(dict(kind="warp", index=i, tile=warp_stand(m, x, y), warp=(x, y), dest=dest, dest_warp=warp,
                           push=warp_push(m, x, y), exit=mapdata.takeable(m, x, y)))
    for direction, other_id, offset in m.connections:
        for t in edge_tiles(m, direction, (other_id, offset)):
            points.append(dict(kind="connection", tile=t, direction=direction, dest=other_id, offset=offset, exit=True))
    return points


def batch_arrival(world, map_ids, p):
    """(map, tile) where taking exit point p lands the player, if its destination is in the batch."""
    if p["dest"] not in map_ids:
        return None
    dest = world.map(p["dest"])
    if p["kind"] == "warp":
        if p["dest_warp"] >= len(dest.warps):
            return None
        return p["dest"], warp_arrive(dest, *dest.warps[p["dest_warp"]][:2])
    return None  # connections need the source map: batch_reach resolves them


def batch_reach(world, map_ids, map_id, tile):
    """Every (map, tile) reachable from (map_id, tile) on foot, through warps and seams inside the batch."""
    seen_regions, seen, queue = [], set(), deque([(map_id, tuple(tile))])
    while queue:
        mid, start = queue.popleft()
        if (mid, start) in seen:
            continue
        m = world.map(mid)
        region = reach(m, [start])
        seen |= {(mid, t) for t in region}
        for p in map_points(m):
            if tuple(p["tile"]) not in region or not p["exit"]:
                continue
            if p["kind"] == "warp":
                nxt = batch_arrival(world, map_ids, p)
            elif p["dest"] in map_ids:
                other = world.map(p["dest"])
                o = across(m, other, p["direction"], p["offset"], p["tile"])
                ok = other.inside(*o) and other.walkable(*o) and mapdata.crossable(m, p["tile"], other, o)
                nxt = (p["dest"], tuple(o)) if ok else None
            else:
                nxt = None
            if nxt and nxt not in seen:
                queue.append(nxt)
    return seen


def static_audit(world, map_ids):
    findings, plan = [], {}

    def find(map_id, code, detail):
        findings.append(dict(map=map_id, code=code, detail=detail))

    for map_id in map_ids:
        m = world.map(map_id)
        points = map_points(m)
        tiles = [p["tile"] for p in points]
        exits = [p for p in points if p["exit"]]        # arrival-only warps are entries, never exits
        for p in points:
            if not (m.inside(*p["tile"]) and m.walkable(*p["tile"])):
                find(map_id, "exit-not-walkable", p)
            if p["kind"] == "warp" and not p["exit"] and any(k in m.behavior(*p["warp"]) for k in ("DOOR", "LADDER")):
                find(map_id, "warp-closed", dict(warp=p["warp"], behavior=m.behavior(*p["warp"]), dest=p["dest"]))
        # Ledges must land on walkable ground (PlayerJumpLedge never checks).
        for y in range(m.height):
            for x in range(m.width):
                d = JUMP.get(m.behavior(x, y))
                if not d:
                    continue
                dx, dy = DIRS[d]
                before, land = (x - dx, y - dy), (x + dx, y + dy)
                if m.inside(*before) and m.walkable(*before) and not (m.inside(*land) and m.walkable(*land)):
                    find(map_id, "ledge-landing", dict(ledge=(x, y), lands=land))
        # Seams: each walkable tile must face a walkable tile across the connection.
        for direction, other_id, offset in m.connections:
            other = world.map(other_id)
            for t in edge_tiles(m, direction, (other_id, offset)):
                o = across(m, other, direction, offset, t)
                if not (other.inside(*o) and other.walkable(*o)
                        and mapdata.crossable(m, t, other, o)):
                    find(map_id, "seam-mismatch", dict(direction=direction, tile=t, faces=(other_id, o)))
        # Every entry must reach every exit inside the map (cross-map routes are run-time checks).
        cut = []
        for p in points:
            got = reach(m, [p["tile"]])
            cut += [(p["tile"], q["tile"]) for q in exits if q["tile"] not in got]
        # A pair split inside this map is fine when the batch joins it (e.g. a route's halves through a cave).
        cut = [(a, b) for a, b in cut if (map_id, tuple(b)) not in batch_reach(world, map_ids, map_id, a)]
        if cut:
            find(map_id, "exit-unreachable", dict(pairs=cut[:8], count=len(cut)))
        # Pockets: tiles a player can get into but never back out of.
        fwd = reach(m, tiles)
        back = reach(m, [p["tile"] for p in exits], reverse=True)
        pocket = sorted(fwd - back)
        if pocket:
            find(map_id, "one-way-pocket", dict(tiles=pocket[:12], count=len(pocket)))
        # Runtime plan: closed edges (one tile per contiguous run), seams, warps, pockets. A probe tile must be
        # walkable to from where the player stands at an entry, never across a warp (behind a stair door is dead).
        walk = set()
        for p in points:
            walk |= set(mapdata.reach_states(m, tuple(p["tile"])))
        closed = []
        for direction in DIRS:
            run = []
            plain = [t for t in uncovered_edge_tiles(m, direction) if not mapdata.takeable(m, *t)]   # a mat warps
            for t in plain + [None]:
                if run and (t is None or abs(t[0] - run[-1][0]) + abs(t[1] - run[-1][1]) != 1):
                    middle = run[len(run) // 2]
                    if middle in fwd and middle in walk:
                        closed.append(dict(tile=middle, direction=direction, span=[run[0], run[-1]]))
                    run = []
                if t is not None:
                    run.append(t)
        pocket_entry = None
        if pocket:
            for y in range(m.height):
                for x in range(m.width):
                    if (x, y) in fwd and any(n in pocket for n in moves(m, x, y)) and (x, y) not in pocket:
                        pocket_entry = pocket_entry or dict(stand=(x, y), into=[n for n in moves(m, x, y) if n in pocket][0],
                                                            tiles=pocket)
        plan[map_id] = dict(closed=closed, points=points, pocket=pocket_entry)
    return findings, plan


# ------------------------------------------------------------ fixtures (DEV)
def apply_fixture(engine, fixture):
    engine = pathlib.Path(engine)
    if not (engine / MARKER).exists():
        raise SystemExit(f"refusing: {engine} has no {MARKER} marker (fixtures only go into throwaway trees)")
    for edit in fixture["edits"]:
        if edit["op"] in ("connection", "warp"):
            path = engine / "data/maps" / edit["map"] / "map.json"
            info = json.loads(path.read_text())
            key = "connections" if edit["op"] == "connection" else "warp_events"
            items = info.get(key) or []
            if "add" in edit:
                items.append(edit["add"])
            if "set" in edit:
                items[edit["index"]].update(edit["set"])
            info[key] = items
            path.write_text(json.dumps(info, indent=2) + "\n")
        elif edit["op"] == "blocks":
            layout = next(l for l in json.loads((engine / "data/layouts/layouts.json").read_text())["layouts"]
                          if l.get("id") == edit["layout"])
            path = engine / layout["blockdata_filepath"]
            data = bytearray(path.read_bytes())
            for x, y, metatile, collision, elevation in edit["set"]:
                struct.pack_into("<H", data, 2 * (y * layout["width"] + x),
                                 (metatile & 0x3FF) | (collision << 10) | (elevation << 12))
            path.write_bytes(bytes(data))
        elif edit["op"] == "grant":
            grant_script(engine, edit["map"], edit.get("flags", []), edit.get("items", []))
        elif edit["op"] == "wildbattle":
            wildbattle_script(engine, edit["map"], edit["script"], edit["species"], edit["level"])
        elif edit["op"] == "strip":
            path = engine / edit["file"]
            lines = path.read_text().split("\n")
            if lines.count(edit["line"]) != 1:
                raise SystemExit(f"{path}: expected exactly one line {edit['line']!r}")
            lines.remove(edit["line"])
            path.write_text("\n".join(lines))
        elif edit["op"] == "section":
            path = engine / "data/maps" / edit["map"] / "map.json"
            info = json.loads(path.read_text())
            info["region_map_section"] = edit["section"]
            path.write_text(json.dumps(info, indent=2) + "\n")
        else:
            raise SystemExit(f"unknown fixture op {edit['op']}")


def grant_script(engine, name, flags, items):
    """TEST-ONLY: an on-transition script that sets flags and gives items once (throwaway trees only)."""
    path = pathlib.Path(engine) / "data/maps" / name / "scripts.inc"
    text = path.read_text()
    head = f"{name}_MapScripts::\n"
    if head not in text:
        raise SystemExit(f"{path}: no {head.strip()} block")
    start = text.index(head) + len(head)
    end = text.index(".byte 0", start)
    if "MAP_SCRIPT_ON_TRANSITION" in text[start:end]:
        raise SystemExit(f"{name} already has an on-transition script; grant would shadow it")
    label = f"{name}_OnTransition_MapQaGrant"
    body = [f"{label}:"] + [f"\tsetflag {f}" for f in flags]
    for i, item in enumerate(items):
        skip = f"{label}_Have{i}"
        body += [f"\tcheckitem {item}", f"\tgoto_if_eq VAR_RESULT, TRUE, {skip}", f"\tadditem {item}", f"{skip}:"]
    body.append("\tend")
    text = text[:start] + f"\tmap_script MAP_SCRIPT_ON_TRANSITION, {label}\n" + text[start:]
    path.write_text(text + "\n@ TEST-ONLY map_qa fixture grant (throwaway tree)\n" + "\n".join(body) + "\n")


def wildbattle_script(engine, name, label, species, level):
    """TEST-ONLY: make an existing NPC/sign script start a wild battle (throwaway trees only)."""
    path = pathlib.Path(engine) / "data/maps" / name / "scripts.inc"
    text = path.read_text()
    head = f"{label}::\n"
    if text.count(head) != 1:
        raise SystemExit(f"{path}: expected exactly one {label}:: label")
    battle = f"\tlock\n\tsetwildbattle {species}, {level}\n\tdowildbattle\n\trelease\n\tend\n"
    path.write_text(text.replace(head, head + "@ TEST-ONLY map_qa fixture wild battle (throwaway tree)\n" + battle))


def enum_values(text, anchor):
    """Values of a simple sequential C enum containing `anchor`."""
    start = text.rfind("enum", 0, text.index(anchor))
    body = text[text.index("{", start) + 1:text.index("}", start)]
    names = [m.group(1) for m in (re.match(r"\s*(\w+)", part) for part in body.split(",")) if m]
    return {n: i for i, n in enumerate(names)}


def party_menu_layout(engine):
    """Offsets of sPartyMenuInternal->actions/numActions and sMenu.cursorPos, read from source.

    Both structs are private to their .c files, so the offset probe cannot see them; fail closed if
    their leading fields ever change instead of reading the wrong bytes.
    """
    engine = pathlib.Path(engine)
    src = (engine / "src/party_menu.c").read_text()
    head = re.search(r"struct PartyMenuInternal\s*\{\s*TaskFunc task;\s*MainCallback exitCallback;\s*"
                     r"u32 chooseHalf:1;\s*u32 lastSelectedSlot:3;[^\n]*\n\s*u32 spriteIdConfirmPokeball:7;\s*"
                     r"u32 spriteIdCancelPokeball:7;\s*u32 messageId:14;\s*u8 windowId\[3\];\s*"
                     r"u8 actions\[(\d+)\];[^\n]*\n\s*u8 numActions;", src)
    menu_c = (engine / "src/menu.c").read_text()
    cursor = re.search(r"struct Menu\s*\{\s*u8 left;\s*u8 top;\s*s8 cursorPos;", menu_c)
    if not head or not cursor:
        raise SystemExit("party/menu struct layout changed: update map_qa.party_menu_layout")
    out = dict(actions=4 + 4 + 4 + 3, count=int(head.group(1)), cursor=2)
    out.update(enum_values(src, "MENU_FIELD_TOOLKIT,"))
    out.update(enum_values((engine / "include/constants/field_move.h").read_text(), "FIELD_MOVE_FLY,"))
    return out


def continue_warp_fixture(engine, src, dst, group, num, x, y, scratch):
    """DEV-ONLY (disclose in every report): CONTINUE warps to (group, num, x, y)."""
    w = _wrapper(engine)
    sizes = w.chunk_sizes(*w.save_struct_sizes(engine, pathlib.Path(scratch) / "fixture-sizes", "off", release=False))
    data = bytearray(pathlib.Path(src).read_bytes())
    slots = w.flash_slots(bytes(data), sizes)
    newest = max((i for i, s in enumerate(slots) if s["status"] == "valid"), key=lambda i: slots[i]["counter"])
    base = newest * w.SECTORS_PER_SLOT * w.SECTOR_SIZE
    patched = set()
    for n in range(w.SECTORS_PER_SLOT):
        off = base + n * w.SECTOR_SIZE
        sid = struct.unpack_from("<H", data, off + 0xFF4)[0]
        if sid == 0:      # SaveBlock2: specialSaveWarpFlags |= CONTINUE_GAME_WARP
            data[off + 0x09] |= 1
        elif sid == 1:    # SaveBlock1: continueGameWarp
            struct.pack_into("<bbbBhh", data, off + 0x0C, group, num, -1, 0, x, y)
        else:
            continue
        struct.pack_into("<H", data, off + 0xFF6, w.sector_checksum(bytes(data[off:off + w.SECTOR_DATA_SIZE]), sizes[sid]))
        patched.add(sid)
    assert patched == {0, 1} and w.flash_slots(bytes(data), sizes)[newest]["status"] == "valid"
    pathlib.Path(dst).write_bytes(bytes(data))
    return dict(slot=newest, counter=slots[newest]["counter"], group=group, num=num, x=x, y=y)


def _wrapper(engine):
    sys.path.insert(0, str(pathlib.Path(engine).resolve().parent / "scripts/coordination"))
    import codex_cry_gameplay as w
    return w


# ----------------------------------------------------------------- run layer
class Runner:
    def __init__(self, d, world, plan, out):
        self.d, self.w, self.plan, self.out = d, world, plan, out
        self.checks = []

    def check(self, name, ok, **detail):
        self.checks.append(dict(name=name, ok=bool(ok), **detail))
        self.d.log("map-qa-check", name=name, ok=bool(ok), **detail)
        return ok

    def wait_settled(self, tries=40):
        for _ in range(tries):
            time.sleep(0.25)
            s = self.d.state()
            if self.d.field_ready(s):
                time.sleep(0.2)
                return self.d.here()
        return self.d.here()

    def press(self, direction, hold=0.3, after=0.5):
        self.d.e.tap(direction.upper(), hold=hold, after=after)

    def follower(self, label):
        """Step to a plain neighbour and back so the follower is placed, then look for it."""
        import run as play
        mid, (x, y) = self.d.here()
        m = self.w.map(mid)
        # Standing on a step-on warp (coord trigger or ladder): stepping back onto it would take the warp again,
        # so step off only (one step already places the follower).
        on_step_warp = mapdata.trigger_entry(m, x, y) is not None
        for direction, (dx, dy) in DIRS.items():
            if not mapdata.can_walk_direction(m, (x, y), direction):
                continue
            n = (x + dx, y + dy)
            if m.walkable(*n) and not m.warp_at(*n) and n not in {(o[0], o[1]) for o in m.objects}:
                if self.d.step(direction) is not None and not on_step_warp:
                    self.d.step(OPPOSITE[direction])
                break
        obs = play.observe(self.d, label)
        f = obs.get("follower") or {}
        return self.check(f"follower visible ({label})", bool(f) and not f.get("invisible"), follower=f)

    def can_leave(self, label):
        mid, pos = self.d.here()
        m = self.d.live_map(mid)
        exits = {p["tile"] for p in map_points(m) if p["exit"]}
        ok = bool(reach(m, [pos]) & exits)
        return self.check(f"an exit is reachable after {label}", ok, at=(mid, pos))

    def go(self, map_id, tile, _depth=0):
        """Walk to tile; an unreachable tile is a failed check for the caller, not a crashed run.

        When the player is on another map (after a one-way drop), travel back first. When the tile is in another
        part of the map than the player (a route split by a cliff and joined
        by a cave, or a plateau reached only across a seam), travel there through neighbouring maps with
        elevation-aware routing; failing that, enter that part through a batch warp whose arrival can reach it.
        """
        from driver import Stuck
        tile = tuple(tile)
        if self.d.here()[0] != map_id:      # e.g. left on the floor below by a one-way hole drop
            try:
                self.d.travel_to(map_id)
            except Stuck as exc:
                self.d.log("no-route-to-map", map=map_id, reason=str(exc))
        here = self.d.here()
        # On foot means without stepping onto a takeable warp (a strip behind stairs is reached by coming down them).
        if here[0] == map_id and tile not in mapdata.reach_states(self.d.live_map(map_id), here[1]) and _depth < 2:
            try:
                self.d.go_map(self.d.map_route(map_id, map_id, here[1], target=tile))
            except Stuck as exc:
                self.d.log("no-route-to-tile", map=map_id, tile=tile, reason=str(exc))
                self.enter_region(map_id, tile, _depth)
        try:
            self.d.walk_path(map_id, {tile})
        except Stuck as exc:
            self.d.log("unreachable", map=map_id, tile=tile, reason=str(exc))
            return False
        return self.d.here() == (map_id, tile)

    def enter_region(self, map_id, tile, depth):
        target = self.w.map(map_id)
        for src in self.plan:
            for p in self.plan[src]["points"]:
                if p["kind"] != "warp" or not p["exit"] or p["dest"] != map_id or p["dest_warp"] >= len(target.warps):
                    continue
                arrive = warp_arrive(target, *target.warps[p["dest_warp"]][:2])
                if tile not in reach(target, [arrive]):
                    continue
                self.d.log("enter-region", map=map_id, tile=tile, via=(src, tuple(p["tile"])))
                if self.d.here()[0] != src:
                    self.d.travel_to(src)
                if not self.go(src, p["tile"], depth + 1):
                    continue
                for _ in range(4):
                    self.press(p["push"], hold=0.3, after=1.2)
                    here = self.d.here()
                    if here[0] != src or (src == map_id and here == (map_id, arrive)):
                        break
                here = self.wait_settled()
                if here[0] == map_id and (src != map_id or here[1] == arrive):
                    return True
        return False

    def blocked(self, map_id, x, y, direction):
        """Targeted probe (e.g. a shore facing water without Surf): stand there, push, must not move."""
        tile = (int(x), int(y))
        name = f"{map_id} {tile} pushing {direction} is blocked"
        if self.d.here()[0] != map_id:
            self.d.travel_to(map_id)
        if not self.go(map_id, tile):
            return self.check(name, False, reason="could not reach the probe tile", at=self.d.here())
        before = self.d.here()
        self.press(direction, hold=0.35, after=0.6)
        after = self.d.here()
        self.d.shot(f"blocked-{map_id}-{tile[0]}-{tile[1]}-{direction}")
        return self.check(name, after == before, before=before, after=after)

    def closed_edge(self, map_id, c):
        name = f"{map_id} closed {c['direction']} edge at {tuple(c['tile'])} blocks"
        if not self.go(map_id, c["tile"]):
            return self.check(name, False, reason="could not reach the edge tile", at=self.d.here())
        before = self.d.here()
        self.press(c["direction"], hold=0.35, after=0.6)
        after = self.d.here()
        self.d.shot(f"edge-{map_id}-{c['direction']}")
        return self.check(name, after == before, before=before, after=after)

    def seam(self, map_id, p):
        m = self.w.map(map_id)
        other = self.w.map(p["dest"])
        expect = across(m, other, p["direction"], p["offset"], p["tile"])
        name = f"{map_id} {p['direction']} seam {tuple(p['tile'])} -> {p['dest']} {expect} and back"
        if not self.go(map_id, p["tile"]):
            return self.check(name, False, reason="could not reach the seam tile", at=self.d.here())
        # One real step, released as soon as the tile changes: a timed hold can start a second step.
        self.d.step(p["direction"])
        there = self.wait_settled()
        self.d.shot(f"seam-{map_id}-{p['direction']}")
        if there != (p["dest"], expect):
            return self.check(name, False, leg="out", expected=(p["dest"], expect), got=there)
        self.d.step(OPPOSITE[p["direction"]])
        back = self.wait_settled()
        return self.check(name, back == (map_id, tuple(p["tile"])), leg="back", expected=(map_id, p["tile"]), got=back)

    def warp(self, map_id, p):
        dest = self.w.map(p["dest"])
        dx, dy, dpush = None, None, None
        if p["dest_warp"] < len(dest.warps):
            wx, wy = dest.warps[p["dest_warp"]][:2]
            arrive, dstand = warp_arrive(dest, wx, wy), warp_stand(dest, wx, wy)
            dpush = warp_push(dest, wx, wy)
        else:
            arrive = None
        name = f"{map_id} warp {p['index']} {tuple(p['warp'])} -> {p['dest']} and back"
        if not self.go(map_id, p["tile"]):
            return self.check(name, False, reason="could not reach the warp", at=self.d.here())
        for _ in range(4):
            self.press(p["push"], hold=0.3, after=1.2)
            here = self.d.here()
            if here[0] != map_id or (p["dest"] == map_id and here == (p["dest"], arrive)):
                break
        there = self.wait_settled()
        self.d.shot(f"warp-{map_id}-{p['index']}")
        if arrive is None or there != (p["dest"], arrive):
            return self.check(name, False, leg="in", expected=(p["dest"], arrive), got=there)
        self.follower(f"{p['dest']} via warp")
        left = self.can_leave(f"warping into {p['dest']}")
        if not mapdata.takeable(dest, wx, wy):
            # A one-way drop (a Mt. Pyre hole): the landing warp is an arrival point the engine never takes back.
            return self.check(name.replace("and back", "(one-way)"), left, leg="in", at=there)
        self.go(p["dest"], dstand)
        # A same-map warp changes coordinates, not its map ID. Stop on the
        # exact accepted source-derived return group before another input moves
        # the player away; shared exit mats remain valid as before.
        m = self.w.map(map_id)
        group = {warp_arrive(m, x, y) for x, y, dst, dw in m.warps if (dst, dw) == (p["dest"], p["dest_warp"])}
        for _ in range(4):
            self.press(dpush, hold=0.3, after=1.2)
            here = self.d.here()
            if here[0] != p["dest"] or (p["dest"] == map_id and here[0] == map_id and here[1] in group):
                break
        back = self.wait_settled()
        # Several warps may share one destination (a Center's two exit mats); any of them is a correct return.
        ok = self.check(name, back[0] == map_id and back[1] in group, leg="back", expected=(map_id, sorted(group)), got=back)
        if ok:
            self.follower(f"{map_id} after warp round trip")
        return ok

    def pocket(self, map_id, entry):
        """Jump into a static one-way pocket for real, then try to walk out of it.

        Reaching the entry or landing in the pocket is setup, reported under its own name, so a driver
        problem can never count as the pocket check the negative fixture expects to fail.
        """
        from driver import Stuck
        if self.d.here()[0] != map_id:
            self.d.travel_to(map_id)
        if not self.go(map_id, entry["stand"]):
            return self.check(f"pocket probe reached {tuple(entry['stand'])} on {map_id}", False, at=self.d.here())
        x, y = entry["stand"]
        direction = next(d for d, (dx, dy) in DIRS.items()
                         if (x + 2 * dx, y + 2 * dy) == tuple(entry["into"]) or (x + dx, y + dy) == tuple(entry["into"]))
        self.press(direction, hold=0.3, after=1.0)
        landed = self.wait_settled()
        if landed != (map_id, tuple(entry["into"])):
            return self.check(f"pocket probe landed at {tuple(entry['into'])} on {map_id}", False, got=landed)
        self.d.shot(f"pocket-{map_id}-in")
        # Escape attempt with real input: route to any warp/seam point, then push every direction.
        exits = {tuple(p["tile"]) for p in map_points(self.d.live_map(map_id)) if p["exit"]}
        try:
            self.d.walk_path(map_id, exits)
        except Stuck as exc:
            self.d.log("pocket-no-route", reason=str(exc))
        inside = {tuple(t) for t in entry["tiles"]}
        for d in DIRS:
            if self.d.here()[0] != map_id or self.d.here()[1] not in inside:
                break
            self.press(d, hold=0.3, after=0.5)
        end = self.wait_settled()
        self.d.shot(f"pocket-{map_id}-end")
        escaped = end[0] != map_id or end[1] not in inside
        return self.check(f"{map_id} has no one-way pocket", escaped, entry=entry, ended=end)

    # --- unsupported-region UI (Town Map item, PokeNav map, Field Kit Fly) -----------------------
    def flag(self, name):
        n = self.d.g.c[name]
        sb1 = struct.unpack("<I", self.d.g.gdb.read(self.d.g.sym["gSaveBlock1Ptr"], 4))[0]
        return bool(self.d.g.gdb.read(sb1 + self.d.g.off["sb1.flags"] + n // 8, 1)[0] & (1 << (n % 8)))

    def last_heal(self):
        """gSaveBlock1Ptr->lastHealLocation as (map id, x, y): the whiteout anchor."""
        g = self.d.g
        sb1 = struct.unpack("<I", g.gdb.read(g.sym["gSaveBlock1Ptr"], 4))[0]
        group, num, _, x, y = struct.unpack("<bbbxhh", g.gdb.read(sb1 + g.off["sb1.lastHealLocation"], 8))
        return self.d.w.by_num.get((group, num)), x, y

    def whiteout(self, heal_id, npc, engine):
        """Lose a real battle on purpose and require the whiteout to land at heal_id's nurse.

        Needs the TEST-ONLY `wildbattle` fixture on the NPC (map, x, y): ordinary input talks to it,
        the battle is played with the weakest move every turn, and the game's own whiteout runs.
        The anchor itself must already be set by ordinary play (e.g. entering the Center).
        """
        import run as play
        from driver import Stuck
        heals = json.loads((pathlib.Path(engine) / "src/data/heal_locations.json").read_text())["heal_locations"]
        heal = next((h for h in heals if h["id"] == heal_id), None)
        if not self.check(f"whiteout: {heal_id} exists in this tree", heal is not None):
            return
        anchor = self.last_heal()
        self.check(f"whiteout: ordinary play set the {heal_id} anchor", anchor == (heal["map"], heal["x"], heal["y"]),
                   got=anchor, expected=(heal["map"], heal["x"], heal["y"]))
        before = play.observe(self.d, "whiteout-before")
        npc_map, x, y = npc
        try:
            if self.d.here()[0] != npc_map:
                self.d.travel_to(npc_map)
            self.d.talk(npc_map, (x, y), clear=False)
        except Stuck as exc:
            return self.check("whiteout: the TEST-ONLY wild battle started", False, reason=str(exc))
        started = False
        for _ in range(40):
            if self.d.state().in_battle:
                started = True
                break
            time.sleep(0.25)
        if not self.check("whiteout: the TEST-ONLY wild battle started", started, npc=npc):
            return
        self.d.battle(choose_move=play.weakest_move(self.d), label="whiteout-loss", never_b=True)
        for n in range(4):  # the whiteout message prints slowly over black
            self.d.shot(f"whiteout-after-{n + 1}")
            time.sleep(0.7)
        self.d.clear_text(capture="whiteout-nurse", frames=12)
        landed = self.wait_settled()
        want = (heal["respawn_map"], (heal.get("respawn_x", 7), heal.get("respawn_y", 4)))
        self.check(f"whiteout: respawned in front of the {heal_id} nurse", landed == want, got=landed, expected=want)
        try:
            after = play.observe(self.d, "whiteout-after")
        except play.ExpectationFailed as exc:
            return self.check("whiteout: back in the overworld", False, reason=str(exc))
        self.check("whiteout: party fully healed", play.party_fully_restored(self.d, after))
        self.check("whiteout: money lost (or none to lose)", after["money"] < before["money"] or not before["money"],
                   before=before["money"], after=after["money"])
        self.can_leave(f"the whiteout to {heal['respawn_map']}")

    def ui_back(self, label, opened, expect):
        """After a UI path: back to the field, screen not black, a real step moves the player."""
        import run as play
        from driver import Stuck
        try:
            play.back_to_field(self.d, limit=16)
        except Stuck:
            pass
        self.d.settle()
        faded = self.d.g.gdb.read(self.d.g.sym["gPlttBufferFaded"], 0x200)
        black = not any(faded)
        moved = self.follower_step()
        want_open = expect == "opens"
        self.check(f"region UI: {label} {'opens its map' if want_open else 'refused'}", opened == want_open, opened=opened)
        self.check(f"region UI: back in the field after {label} (not black, player can move)",
                   self.d.field_ready(self.d.state()) and not black and moved, black=black, moved=moved)

    def follower_step(self):
        mid, pos = self.d.here()
        m = self.d.live_map(mid)
        on_step_warp = mapdata.trigger_entry(m, *pos) is not None   # never step back onto a step-on warp
        for direction, (dx, dy) in DIRS.items():
            if not mapdata.can_walk_direction(m, pos, direction):
                continue
            n = (pos[0] + dx, pos[1] + dy)
            if m.walkable(*n) and not m.warp_at(*n) and n not in {(o[0], o[1]) for o in m.objects}:
                if self.d.step(direction) is not None:
                    if not on_step_warp:
                        self.d.step(OPPOSITE[direction])
                    return True
        return False

    def timeline(self, seconds, press_a_when_locked=False):
        names, end = [], time.monotonic() + seconds
        while time.monotonic() < end:
            s = self.d.state()
            if not names or names[-1] != s.cb2:
                names.append(s.cb2)
            if press_a_when_locked and s.cb2 == "CB2_Overworld" and s.locked:
                self.d.e.tap("A", after=0.4)
            time.sleep(0.2)
        return names

    def region_ui(self, map_id, expect, engine):
        """Drive the three region-map entry points with real input in map_id.

        expect="refused" for regions without an approved Town Map/Fly grid (Sinnoh today, #138);
        expect="opens" for regions that have one. Needs the TEST-ONLY `grant` fixture (PokeNav flag,
        Fly licence, Town Map item); without it the run fails closed on the precondition check.
        """
        import run as play
        w = _wrapper(engine)
        if self.d.here()[0] != map_id:
            self.d.travel_to(map_id)
        g, gd, sym = self.d.g, self.d.g.gdb, self.d.g.sym
        town = g.c["ITEM_TOWN_MAP"]
        keys = [i for i, q in g.bag_pocket("bag.keyItems", "BAG_KEYITEMS_COUNT") if i]
        ready = (self.d.here()[0] == map_id and self.flag("FLAG_SYS_POKENAV_GET")
                 and self.flag("FLAG_AVERON_LICENSE_FLY") and town in keys)
        if not self.check(f"region UI: fixture grant present in {map_id}", ready, at=self.d.here(), key_items=keys):
            return
        # PokeNav -> MAP. The PokeNav map runs under generic looped tasks; what changes is that the
        # main menu's own tasks are freed when the map feature replaces it.
        play.open_start_menu_action(self.d, 3)
        self.timeline(3.0)
        menu_tasks = {"Task_MoveBgDots", "Task_CurrentMenuOptionGlow"}
        before = set(w.active_tasks(g))
        self.d.e.tap("A", after=0.2)
        self.timeline(4.0)
        self.d.shot(f"region-ui-pokenav-{map_id}")
        after = set(w.active_tasks(g))
        self.ui_back("PokeNav MAP", bool(menu_tasks & before) and not (menu_tasks & after), expect)
        # Bag -> Key Items -> Town Map -> USE
        play.open_start_menu_action(self.d, 2)
        time.sleep(1.0)
        pos, pocket = sym["gBagPosition"], g.c["POCKET_KEY_ITEMS"]
        for _ in range(6):
            if gd.read(pos + g.off["bagpos.pocket"], 1)[0] == pocket:
                break
            self.d.e.tap("RIGHT", after=0.8)
        index = keys.index(town)
        for _ in range(40):
            cur = struct.unpack("<H", gd.read(pos + g.off["bagpos.cursor"] + 2 * pocket, 2))[0]
            scr = struct.unpack("<H", gd.read(pos + g.off["bagpos.scroll"] + 2 * pocket, 2))[0]
            if cur + scr == index:
                break
            self.d.e.tap("DOWN" if cur + scr < index else "UP", after=0.3)
        self.d.e.tap("A", after=0.8)
        self.d.e.tap("A", after=0.5)
        seen = self.timeline(10.0, press_a_when_locked=True)
        self.d.shot(f"region-ui-townmap-{map_id}")
        self.ui_back("Town Map", any("RegionMap" in c for c in seen), expect)
        # Party -> FIELD KIT -> FLY (Averon's licence-unlocked moves live in the Field Kit)
        menu = party_menu_layout(engine)
        play.open_start_menu_action(self.d, 1)
        time.sleep(1.0)
        self.d.e.tap("A", after=0.8)
        internal = struct.unpack("<I", gd.read(sym["sPartyMenuInternal"], 4))[0]

        def actions():
            raw = gd.read(internal + menu["actions"], menu["count"] + 1)
            return list(raw[:menu["count"]])[:raw[menu["count"]]]

        def cursor_to(i):
            for _ in range(12):
                cur = struct.unpack("<b", gd.read(sym["sMenu"] + menu["cursor"], 1))[0]
                if cur == i:
                    return
                self.d.e.tap("DOWN" if cur < i else "UP", after=0.25)

        first = actions()
        if menu["MENU_FIELD_TOOLKIT"] not in first:
            return self.check("region UI: FIELD KIT listed in the party menu", False, actions=first)
        cursor_to(first.index(menu["MENU_FIELD_TOOLKIT"]))
        self.d.e.tap("A", after=0.8)
        kit = actions()
        fly = menu["MENU_FIELD_MOVES"] + menu["FIELD_MOVE_FLY"]
        if fly not in kit:
            return self.check("region UI: FLY listed in the FIELD KIT", False, actions=kit)
        cursor_to(kit.index(fly))
        self.d.e.tap("A", after=0.3)
        seen = self.timeline(5.0)
        self.d.shot(f"region-ui-fly-{map_id}")
        self.ui_back("Fly", any("Fly" in c or "RegionMap" in c for c in seen), expect)

    def run_map(self, map_id):
        if self.d.here()[0] != map_id:
            self.d.travel_to(map_id)
        self.check(f"reached {map_id}", self.d.here()[0] == map_id, at=self.d.here())
        plan = self.plan[map_id]
        for c in plan["closed"]:
            self.closed_edge(map_id, c)
        seams = {}
        for p in plan["points"]:
            if p["kind"] == "connection" and tuple(p["tile"]) in self.passable_seams(map_id, p["direction"]):
                seams.setdefault(p["direction"], []).append(p)
        for run in seams.values():
            for p in {id(q): q for q in (run[0], run[len(run) // 2], run[-1])}.values():
                self.seam(map_id, p)
        for p in plan["points"]:
            if p["kind"] == "warp" and p["exit"] and p["dest"] in self.plan:
                self.warp(map_id, p)

    def passable_seams(self, map_id, direction):
        return set(mapdata.edge_exits(self.w.map(map_id), direction))


def cmd_run(args):
    engine = pathlib.Path(args.engine).resolve()
    w = _wrapper(engine)
    from codex_cry_gameplay import driver, emu, game, play
    # The driver modules come from the engine tree under test (_wrapper), which may predate these
    # probe entries; register them here so --region-ui works against any tree.
    emu.OFFSET_EXPRS.setdefault("bag.keyItems", "offsetof(struct Bag, keyItems)")
    emu.OFFSET_EXPRS.setdefault("sb1.lastHealLocation", "offsetof(struct SaveBlock1, lastHealLocation)")
    for name in REGION_UI_CONSTANTS:
        if name not in emu.CONSTANTS:
            emu.CONSTANTS.append(name)
    scratch, out = pathlib.Path(args.scratch).resolve(), pathlib.Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit("OUT must be new or empty")
    out.mkdir(parents=True, exist_ok=True)
    rom_source = pathlib.Path(args.rom).resolve()
    rom = scratch / "game.gba"
    shutil.copyfile(rom_source, rom)
    flash = rom.with_suffix(".sav")
    world = mapdata.World(engine)
    findings, plan = static_audit(world, args.map)
    result = dict(maps=args.map, build=args.build, rom_sha256=play.sha256(rom), static_findings=findings,
                  save_before=play.sha256(flash) if flash.exists() else None, checks=[],
                  dev_entry="continue-warp save fixture (DEV-only) unless --expect")
    info = emu.load_build_info(rom_source.with_suffix(".elf"), engine, scratch / "symbol-cache")
    info["symbols"] = w.lto_aliases(info["symbols"])
    sizes = w.chunk_sizes(*w.save_struct_sizes(engine, scratch / "save-sizes", "off", release=args.build == "release"))
    e = emu.Emulator(rom, out, audio=False)
    g = game.Game(e, info)
    w.use_source_function_names(g)
    d = driver.Driver(e, g, world, out / "events.jsonl")
    d.moves = game.MoveTable(rom, info)
    g.map_names = d.w.by_num
    r = Runner(d, world, plan, out)
    try:
        play.boot(d, False)
        if args.expect:
            w.check_continue(d, pathlib.Path(args.expect))
            r.check("fresh CONTINUE restores the saved state", True, at=d.here())
        r.wait_settled()
        r.check("starts inside the batch", d.here()[0] in plan, at=d.here())
        r.follower("start")
        if not args.expect:
            for map_id in args.map:
                r.run_map(map_id)
            for probe in args.blocked or []:
                r.blocked(*probe.split(","))
            if args.region_ui:
                r.region_ui(args.region_ui_map or args.map[0], args.region_ui, engine)
            if args.whiteout:
                if not args.whiteout_npc:
                    raise SystemExit("--whiteout needs --whiteout-npc MAP_ID,X,Y")
                npc_map, x, y = args.whiteout_npc.split(",")
                r.whiteout(args.whiteout, (npc_map, int(x), int(y)), engine)
            for map_id in args.map:
                if plan[map_id]["pocket"]:
                    r.pocket(map_id, plan[map_id]["pocket"])
                    break
            else:
                d.e.tap("START", after=0.8)
                d.shot("start-menu")
                d.e.tap("B", after=0.6)
                r.check("Start menu opens and returns to the field", d.field_ready(d.state()))
                if args.save:
                    w.release_save(d, args.save, sizes, flash)
                    r.check(f"SAVE ({args.save})", True, at=d.here())
        result["alive"] = True
    except BaseException as exc:
        result["alive"] = False
        result["error"] = repr(exc)
        r.check("run completed without the driver getting stuck", False, error=repr(exc)[:300], at=_safe_here(d))
    finally:
        try:
            e.close()
        except Exception:
            pass
        result["checks"] = r.checks
        saves = sorted(out.glob("saved-*.json"))
        if saves:
            before = json.loads(saves[0].read_text())["flash_before"]
            result["flash_problems"] = w.flash_verdict(before, w.flash_slots(w.read_flash(flash), sizes), len(saves))
        result["save_after"] = play.sha256(flash) if flash.exists() else None
        result["verdict"] = "PASS" if result["alive"] and all(c["ok"] for c in r.checks) and not result.get("flash_problems") else "FAIL"
        (out / "result.json").write_text(json.dumps(result, indent=1, default=list) + "\n")
    print(result["verdict"], f"{sum(c['ok'] for c in r.checks)}/{len(r.checks)} checks")
    return 0 if result["verdict"] == "PASS" else 1


def cmd_selftest(args):
    engine = pathlib.Path(args.engine).resolve()
    if not (engine / MARKER).exists():
        raise SystemExit(f"refusing: {engine} has no {MARKER} marker")
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    fixtures = sorted((HERE / "map_qa_fixtures").glob("*.json"))
    for fx in fixtures:
        if args.only and args.only not in fx.stem:
            continue
        spec = json.loads(fx.read_text())
        subprocess.run(["git", "-C", str(engine), "checkout", "--", "data"], check=True)
        apply_fixture(engine, spec)
        findings, _ = static_audit(mapdata.World(engine), spec["batch"])
        codes = sorted({f["code"] for f in findings})
        static_ok = (set(spec.get("static_codes", [])) <= set(codes)) if spec["expect"] == "FAIL" else not codes
        build = subprocess.run(["make", f"-j{args.jobs}", "CRIES=off"], cwd=engine, capture_output=True, text=True)
        row = dict(fixture=fx.stem, expect=spec["expect"], static_codes=codes, static_ok=static_ok,
                   build=build.returncode)
        if build.returncode:
            row.update(verdict="BUILD-FAIL", ok=False, log=build.stderr[-800:])
            rows.append(row)
            continue
        rom = engine / "pokeemerald-cries-off.gba"
        row["rom_sha256"] = __import__("hashlib").sha256(rom.read_bytes()).hexdigest()
        scratch = out / f"{fx.stem}-scratch"
        shutil.rmtree(scratch, ignore_errors=True)
        scratch.mkdir()
        world = mapdata.World(engine)
        g, n, _ = world.map_ids[spec["entry"][0]]
        row["dev_entry"] = continue_warp_fixture(engine, args.save, scratch / "game.sav", g, n,
                                                 spec["entry"][1], spec["entry"][2], scratch)
        base = [sys.executable, "-I", str(HERE / "map_qa.py"), "run", "--engine", str(engine), "--rom", str(rom),
                "--build", "normal", "--scratch", str(scratch)] + sum((["--map", m] for m in spec["batch"]), [])
        play_out = out / fx.stem
        shutil.rmtree(play_out, ignore_errors=True)
        cmd = (base + ["--out", str(play_out)] + (["--save", "map-qa"] if spec["expect"] == "PASS" else [])
               + spec.get("run_args", []))
        subprocess.run(cmd, timeout=args.timeout)
        res = json.loads((play_out / "result.json").read_text())
        failed = [c["name"] for c in res["checks"] if not c["ok"]]
        row.update(verdict=res["verdict"], checks=len(res["checks"]), failed=failed)
        if spec["expect"] == "PASS":
            ok = res["verdict"] == "PASS"
            saved = play_out / "saved-map-qa.json"
            if ok and saved.exists():
                cont = out / f"{fx.stem}-continue"
                shutil.rmtree(cont, ignore_errors=True)
                subprocess.run(base + ["--out", str(cont), "--expect", str(saved)], timeout=args.timeout)
                cres = json.loads((cont / "result.json").read_text())
                row["continue_verdict"] = cres["verdict"]
                ok = cres["verdict"] == "PASS"
            elif ok:
                ok, row["continue_verdict"] = False, "no save written"
        else:
            ok = res["verdict"] == "FAIL" and any(m in name for m in spec.get("must_fail", []) for name in failed)
        row["ok"] = bool(ok and static_ok)
        rows.append(row)
        print(("OK   " if row["ok"] else "BAD  ") + f"{fx.stem}: expect {spec['expect']}, run {row['verdict']}, "
              f"static {codes or 'clean'}, failed {failed[:3]}", flush=True)
    subprocess.run(["git", "-C", str(engine), "checkout", "--", "data"], check=True)
    (out / "selftest.json").write_text(json.dumps(rows, indent=1, default=list) + "\n")
    good = sum(r["ok"] for r in rows)
    print(f"{good}/{len(rows)} fixtures behaved as expected")
    return 0 if good == len(rows) else 1


def _safe_here(d):
    try:
        return d.here()
    except Exception:
        return None


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("static")
    s.add_argument("--engine", required=True)
    s.add_argument("--map", action="append", required=True)
    s.add_argument("--json")
    f = sub.add_parser("fixture")
    f.add_argument("--engine", required=True)
    f.add_argument("fixture")
    fs = sub.add_parser("fixture-save")
    fs.add_argument("--engine", required=True)
    fs.add_argument("src")
    fs.add_argument("dst")
    fs.add_argument("map_id")
    fs.add_argument("x", type=int)
    fs.add_argument("y", type=int)
    r = sub.add_parser("run")
    for a in ("--engine", "--rom", "--scratch", "--out"):
        r.add_argument(a, required=True)
    r.add_argument("--build", choices=("normal", "release"), required=True)
    r.add_argument("--map", action="append", required=True)
    r.add_argument("--save")
    r.add_argument("--expect")
    r.add_argument("--blocked", action="append", metavar="MAP_ID,X,Y,DIR",
                   help="after the map checks: walk to (X, Y), push DIR, and require the player not to move")
    r.add_argument("--region-ui", choices=("refused", "opens"),
                   help="drive PokeNav MAP, the Town Map item and Field Kit FLY (needs the TEST-ONLY grant fixture)")
    r.add_argument("--region-ui-map", help="outdoor map for --region-ui (default: first --map)")
    r.add_argument("--whiteout", metavar="HEAL_LOCATION_ID",
                   help="lose a battle on purpose and require a respawn at this healer (needs the TEST-ONLY wildbattle fixture)")
    r.add_argument("--whiteout-npc", metavar="MAP_ID,X,Y", help="the NPC the wildbattle fixture was put on")
    st = sub.add_parser("selftest")
    st.add_argument("--engine", required=True)
    st.add_argument("--save", required=True)
    st.add_argument("--out", required=True)
    st.add_argument("--only")
    st.add_argument("--jobs", type=int, default=8)
    st.add_argument("--timeout", type=int, default=1800)
    args = p.parse_args(argv)
    if args.cmd == "selftest":
        return cmd_selftest(args)
    if args.cmd == "static":
        findings, plan = static_audit(mapdata.World(args.engine), args.map)
        report = dict(maps=args.map, findings=findings, plan=plan)
        if args.json:
            pathlib.Path(args.json).write_text(json.dumps(report, indent=1, default=list) + "\n")
        for fnd in findings:
            print(f"FINDING {fnd['map']} {fnd['code']}: {fnd['detail']}")
        for map_id, pl in plan.items():
            print(f"{map_id}: {len(pl['closed'])} closed edge runs, "
                  f"{sum(q['kind'] == 'connection' for q in pl['points'])} seam tiles, "
                  f"{sum(q['kind'] == 'warp' for q in pl['points'])} warps, pocket={bool(pl['pocket'])}")
        print(f"{'PASS' if not findings else 'FAIL'}: {len(findings)} findings")
        return 1 if findings else 0
    if args.cmd == "fixture":
        apply_fixture(args.engine, json.loads(pathlib.Path(args.fixture).read_text()))
        print(f"applied {args.fixture} to throwaway {args.engine}")
        return 0
    if args.cmd == "fixture-save":
        world = mapdata.World(args.engine)
        g, n, _ = world.map_ids[args.map_id]
        print("DEV fixture:", continue_warp_fixture(pathlib.Path(args.engine).resolve(), args.src, args.dst,
                                                    g, n, args.x, args.y, pathlib.Path(args.dst).parent))
        return 0
    return cmd_run(args)


if __name__ == "__main__":
    raise SystemExit(main())
