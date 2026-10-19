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
JUMP = {"MB_JUMP_SOUTH": "down", "MB_JUMP_NORTH": "up", "MB_JUMP_EAST": "right", "MB_JUMP_WEST": "left"}
MARKER = ".map_qa_throwaway"


# ---------------------------------------------------------------- static layer
def is_door(m, x, y):
    return "DOOR" in m.behavior(x, y)


def warp_push(m, x, y):
    """Direction to press to take the warp at (x, y)."""
    b = m.behavior(x, y)
    for word, d in (("SOUTH", "down"), ("NORTH", "up"), ("EAST", "right"), ("WEST", "left")):
        if word + "_ARROW" in b:
            return d
    return "up"


def warp_stand(m, x, y):
    """Tile the player stands on to take the warp, which is also where it arrives."""
    if is_door(m, x, y) or not m.walkable(x, y):
        return (x, y + 1)
    return (x, y)


def moves(m, x, y):
    """Tiles reachable in one press from (x, y): a walk or a ledge jump (no landing check, as in the engine)."""
    for d, (dx, dy) in DIRS.items():
        nx, ny = x + dx, y + dy
        if not m.inside(nx, ny):
            continue
        if m.walkable(nx, ny):
            yield nx, ny
        elif JUMP.get(m.behavior(nx, ny)) == d:
            yield nx + dx, ny + dy


def edge_tiles(m, direction):
    if direction in ("up", "down"):
        y = 0 if direction == "up" else m.height - 1
        return [(x, y) for x in range(m.width) if m.walkable(x, y)]
    x = 0 if direction == "left" else m.width - 1
    return [(x, y) for y in range(m.height) if m.walkable(x, y)]


def across(m, other, direction, offset, tile):
    """Where stepping off m at tile lands in the connected map (fieldmap: pos -= offset)."""
    x, y = tile
    if direction == "up":
        return (x - offset, other.height - 1)
    if direction == "down":
        return (x - offset, 0)
    if direction == "left":
        return (other.width - 1, y - offset)
    return (0, y - offset)


def reach(m, starts, reverse=False):
    starts = [s for s in starts if m.inside(*s) and m.walkable(*s)]
    if reverse:
        back = {}
        for y in range(m.height):
            for x in range(m.width):
                if m.walkable(x, y):
                    for t in moves(m, x, y):
                        back.setdefault(t, []).append((x, y))
        step = lambda t: back.get(t, [])
    else:
        step = lambda t: [n for n in moves(m, *t) if m.inside(*n) and m.walkable(*n)]
    seen, queue = set(starts), deque(starts)
    while queue:
        for n in step(queue.popleft()):
            if n not in seen:
                seen.add(n)
                queue.append(n)
    return seen


def map_points(m):
    """Entries and exits of one map: every warp's standing tile and every connection seam tile."""
    points = []
    for i, (x, y, dest, warp) in enumerate(m.warps):
        points.append(dict(kind="warp", index=i, tile=warp_stand(m, x, y), warp=(x, y), dest=dest, dest_warp=warp,
                           push=warp_push(m, x, y)))
    for direction, other_id, offset in m.connections:
        for t in edge_tiles(m, direction):
            points.append(dict(kind="connection", tile=t, direction=direction, dest=other_id, offset=offset))
    return points


def static_audit(world, map_ids):
    findings, plan = [], {}

    def find(map_id, code, detail):
        findings.append(dict(map=map_id, code=code, detail=detail))

    for map_id in map_ids:
        m = world.map(map_id)
        points = map_points(m)
        tiles = [p["tile"] for p in points]
        for p in points:
            if not (m.inside(*p["tile"]) and m.walkable(*p["tile"])):
                find(map_id, "exit-not-walkable", p)
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
            for t in edge_tiles(m, direction):
                o = across(m, other, direction, offset, t)
                if not (other.inside(*o) and other.walkable(*o)):
                    find(map_id, "seam-mismatch", dict(direction=direction, tile=t, faces=(other_id, o)))
        # Every entry must reach every exit inside the map (cross-map routes are run-time checks).
        cut = []
        for p in points:
            got = reach(m, [p["tile"]])
            cut += [(p["tile"], q["tile"]) for q in points if q["tile"] not in got]
        if cut:
            find(map_id, "exit-unreachable", dict(pairs=cut[:8], count=len(cut)))
        # Pockets: tiles a player can get into but never back out of.
        fwd = reach(m, tiles)
        back = reach(m, tiles, reverse=True)
        pocket = sorted(fwd - back)
        if pocket:
            find(map_id, "one-way-pocket", dict(tiles=pocket[:12], count=len(pocket)))
        # Runtime plan: closed edges (one tile per contiguous run), seams, warps, pockets.
        connected = {d for d, _, _ in m.connections}
        closed = []
        for direction in DIRS:
            if direction in connected:
                continue
            run = []
            plain = [t for t in edge_tiles(m, direction) if not m.warp_at(*t)]   # pressing out on a mat warps
            for t in plain + [None]:
                if run and (t is None or abs(t[0] - run[-1][0]) + abs(t[1] - run[-1][1]) != 1):
                    middle = run[len(run) // 2]
                    if middle in fwd:
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
        else:
            raise SystemExit(f"unknown fixture op {edit['op']}")


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
        for direction, (dx, dy) in DIRS.items():
            n = (x + dx, y + dy)
            if m.walkable(*n) and not m.warp_at(*n) and n not in {(o[0], o[1]) for o in m.objects}:
                if self.d.step(direction):
                    self.d.step(OPPOSITE[direction])
                break
        obs = play.observe(self.d, label)
        f = obs.get("follower") or {}
        return self.check(f"follower visible ({label})", bool(f) and not f.get("invisible"), follower=f)

    def can_leave(self, label):
        mid, pos = self.d.here()
        m = self.d.live_map(mid)
        exits = {p["tile"] for p in map_points(m)}
        ok = bool(reach(m, [pos]) & exits)
        return self.check(f"an exit is reachable after {label}", ok, at=(mid, pos))

    def go(self, map_id, tile):
        """Walk to tile; an unreachable tile is a failed check for the caller, not a crashed run."""
        from driver import Stuck
        try:
            self.d.walk_path(map_id, {tuple(tile)})
        except Stuck as exc:
            self.d.log("unreachable", map=map_id, tile=tuple(tile), reason=str(exc))
            return False
        return self.d.here() == (map_id, tuple(tile))

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
        self.press(p["direction"], hold=0.3, after=0.4)
        there = self.wait_settled()
        self.d.shot(f"seam-{map_id}-{p['direction']}")
        if there != (p["dest"], expect):
            return self.check(name, False, leg="out", expected=(p["dest"], expect), got=there)
        self.press(OPPOSITE[p["direction"]], hold=0.3, after=0.4)
        back = self.wait_settled()
        return self.check(name, back == (map_id, tuple(p["tile"])), leg="back", expected=(map_id, p["tile"]), got=back)

    def warp(self, map_id, p):
        dest = self.w.map(p["dest"])
        dx, dy, dpush = None, None, None
        if p["dest_warp"] < len(dest.warps):
            wx, wy = dest.warps[p["dest_warp"]][:2]
            arrive = warp_stand(dest, wx, wy)
            dpush = warp_push(dest, wx, wy)
        else:
            arrive = None
        name = f"{map_id} warp {p['index']} {tuple(p['warp'])} -> {p['dest']} and back"
        if not self.go(map_id, p["tile"]):
            return self.check(name, False, reason="could not reach the warp", at=self.d.here())
        for _ in range(4):
            self.press(p["push"], hold=0.3, after=1.2)
            if self.d.here()[0] != map_id:
                break
        there = self.wait_settled()
        self.d.shot(f"warp-{map_id}-{p['index']}")
        if arrive is None or there != (p["dest"], arrive):
            return self.check(name, False, leg="in", expected=(p["dest"], arrive), got=there)
        self.follower(f"{p['dest']} via warp")
        self.can_leave(f"warping into {p['dest']}")
        self.go(p["dest"], arrive)
        for _ in range(4):
            self.press(dpush, hold=0.3, after=1.2)
            if self.d.here()[0] != p["dest"]:
                break
        back = self.wait_settled()
        # Several warps may share one destination (a Center's two exit mats); any of them is a correct return.
        m = self.w.map(map_id)
        group = {warp_stand(m, x, y) for x, y, dst, dw in m.warps if (dst, dw) == (p["dest"], p["dest_warp"])}
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
        exits = {tuple(p["tile"]) for p in map_points(self.d.live_map(map_id))}
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
            if p["kind"] == "warp" and p["dest"] in self.plan:
                self.warp(map_id, p)

    def passable_seams(self, map_id, direction):
        return set(mapdata.edge_exits(self.w.map(map_id), direction))


def cmd_run(args):
    engine = pathlib.Path(args.engine).resolve()
    w = _wrapper(engine)
    from codex_cry_gameplay import driver, emu, game, play
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
        cmd = base + ["--out", str(play_out)] + (["--save", "map-qa"] if spec["expect"] == "PASS" else [])
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
