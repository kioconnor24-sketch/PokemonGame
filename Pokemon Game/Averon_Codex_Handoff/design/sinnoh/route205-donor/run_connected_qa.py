#!/usr/bin/env python3
"""Run existing map_qa checks with a pinned controller route for the high seam.

The shared runner's BFS ignores elevation. This fixture guides navigation only;
seam/warp/follower/menu/save checks are inherited unchanged. No source or live
game memory is modified. The original unassisted65/67 result remains evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys

HERE = Path(__file__).resolve().parent
BATCH = ["MAP_ROUTE205_NORTH", "MAP_ROUTE205_SOUTH", "MAP_FLOAROMA_TOWN",
         "MAP_FLOAROMA_MEADOW", "MAP_ROUTE204", "MAP_RAVAGED_PATH"]
DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
REVERSE = {"up": "down", "down": "up", "left": "right", "right": "left"}


def validate_route(spec, raw, *, allow_bridges=False):
    if hashlib.sha256(raw).hexdigest() != spec["map_sha256"]:
        raise ValueError("North source changed; revalidate elevation route")
    width, height = spec["width"], spec["height"]
    if type(width) is not int or type(height) is not int or width < 1 or height < 1:
        raise ValueError("invalid route dimensions")
    if len(raw) != width * height * 2:
        raise ValueError("route dimensions disagree with map")
    cells = struct.unpack("<%dH" % (width * height), raw)
    for key in ("start", "goal"):
        point = spec[key]
        if (not isinstance(point, list) or len(point) != 2 or any(type(v) is not int for v in point)
                or not (0 <= point[0] < width and 0 <= point[1] < height)):
            raise ValueError("invalid route endpoint")
    if not isinstance(spec["steps"], list) or not spec["steps"]:
        raise ValueError("route needs controller steps")
    x, y = spec["start"]
    points = [(x, y)]
    elevation = cells[y * width + x] >> 12
    if elevation == 15:
        raise ValueError("route must start on an unambiguous ground elevation")
    for direction in spec["steps"]:
        if direction not in DIRS:
            raise ValueError("unsupported controller direction")
        previous_level = cells[y * width + x] >> 12
        dx, dy = DIRS[direction]
        x, y = x + dx, y + dy
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError("route escapes map")
        cell = cells[y * width + x]
        level = cell >> 12
        if (cell >> 10) & 3 or (level == 15 and not allow_bridges):
            raise ValueError("route crosses collision or an ambiguous bridge")
        if elevation and level not in (0, 15, elevation):
            raise ValueError("route crosses an incompatible elevation")
        # Mirrors ObjectEventUpdateElevation: both entering multi-level tiles
        # and the first step off them retain the prior object elevation.
        if level != 15 and previous_level != 15:
            elevation = level
        points.append((x, y))
    if (x, y) != tuple(spec["goal"]):
        raise ValueError("route misses the high seam")
    return points


def guided_runner(qa, spec, points):
    class GuidedRunner(qa.Runner):
        def follow(self, reverse=False):
            expected = list(reversed(points)) if reverse else points
            directions = [REVERSE[d] for d in reversed(spec["steps"])] if reverse else spec["steps"]
            if self.d.here() != (spec["map"], expected[0]):
                raise RuntimeError("controller route started on the wrong tile")
            for direction, target in zip(directions, expected[1:]):
                self.d.step(direction)
                actual = self.wait_settled()
                self.d.log("elevation-route-step", direction=direction, expected=(spec["map"], target), actual=actual)
                if actual != (spec["map"], target):
                    raise RuntimeError("controller route did not reach its exact next tile")

        def go(self, map_id, tile, _depth=0):
            high = (map_id, tuple(tile)) in ((spec["map"], tuple(spec["goal"])), ("MAP_ROUTE205_SOUTH", (25, 0)))
            if high and self.d.here() != (map_id, tuple(tile)):
                self.d.travel_to(spec["map"])
                if not super().go(spec["map"], spec["start"], _depth):
                    return False
                self.follow()
                if map_id == "MAP_ROUTE205_SOUTH":
                    self.d.step("down")
                    self.wait_settled()
            return super().go(map_id, tile, _depth)

        def seam(self, map_id, point):
            # All exact out/back assertions still execute in the shared tester.
            result = super().seam(map_id, point)
            if result and (map_id, tuple(point["tile"])) in (
                    (spec["map"], tuple(spec["goal"])), ("MAP_ROUTE205_SOUTH", (25, 0))):
                if map_id == "MAP_ROUTE205_SOUTH":
                    self.d.step("up")
                    self.wait_settled()
                self.follow(reverse=True)  # Return to the lower walking network for the next check.
            return result
    return GuidedRunner


def run(args):
    engine = args.engine.resolve()
    sys.path.insert(0, str(engine.parent / "scripts/claude_play"))
    import map_qa as qa
    w = qa._wrapper(engine)
    from codex_cry_gameplay import driver, emu, game, play
    spec = json.loads((HERE / "north-elevation-route.json").read_text())
    points = validate_route(spec, (engine / "data/layouts/Route205_North/map.bin").read_bytes())
    world = qa.mapdata.World(engine)
    if any(not world.map(spec["map"]).walkable(*p) for p in points):
        raise ValueError("route crosses non-walking terrain")
    args.out.mkdir(parents=True, exist_ok=True)
    if any(args.out.iterdir()):
        raise ValueError("OUT must be empty")
    args.scratch.mkdir(parents=True, exist_ok=True)
    rom = args.scratch / "game.gba"
    shutil.copyfile(args.rom, rom)
    flash = rom.with_suffix(".sav")
    info = emu.load_build_info(args.rom.with_suffix(".elf"), engine, args.scratch / "symbol-cache")
    info["symbols"] = w.lto_aliases(info["symbols"])
    sizes = w.chunk_sizes(*w.save_struct_sizes(engine, args.scratch / "save-sizes", "off", release=args.profile == "release"))
    findings, plan = qa.static_audit(world, BATCH)
    if findings:
        raise ValueError("connected source must pass static audit before guided gameplay")
    e = emu.Emulator(rom, args.out, audio=False)
    g = game.Game(e, info)
    w.use_source_function_names(g)
    d = driver.Driver(e, g, world, args.out / "events.jsonl")
    d.moves = game.MoveTable(rom, info)
    g.map_names = d.w.by_num
    r = guided_runner(qa, spec, points)(d, world, plan, args.out)
    result = dict(maps=BATCH, build=args.profile, rom_sha256=play.sha256(rom), static_findings=findings,
        navigation="hash-pinned52-step height route; existing checks unchanged, ordinary controller only",
        dev_entry="continue-warp DEV fixture unless --expect; no production origin-name acceptance")
    try:
        play.boot(d, False)
        if args.expect:
            w.check_continue(d, args.expect)
            r.check("fresh CONTINUE restores the saved state", True, at=d.here())
        r.wait_settled()
        r.check("starts inside the batch", d.here()[0] in plan, at=d.here())
        r.follower("start")
        if not args.expect:
            for mid in BATCH:
                r.run_map(mid)
            r.blocked("MAP_ROUTE205_SOUTH", 26, 81, "right")
            d.e.tap("START", after=.8)
            d.shot("start-menu")
            d.e.tap("B", after=.6)
            r.check("Start menu opens and returns to the field", d.field_ready(d.state()))
            w.release_save(d, "northern-corridor", sizes, flash)
            r.check("SAVE (northern-corridor)", True, at=d.here())
        result["alive"] = True
    except BaseException as exc:
        result.update(alive=False, error=repr(exc))
        r.check("run completed without the driver getting stuck", False, error=repr(exc))
    finally:
        e.close()
        result["checks"] = r.checks
        saved = args.out / "saved-northern-corridor.json"
        if saved.exists():
            before = json.loads(saved.read_text())["flash_before"]
            result["flash_problems"] = w.flash_verdict(before, w.flash_slots(w.read_flash(flash), sizes), 1)
        expected_count = 3 if args.expect else 67
        if len(r.checks) != expected_count:
            result.update(alive=False, error=f"expected {expected_count} unchanged checks, got {len(r.checks)}")
        result["verdict"] = "PASS" if result["alive"] and all(c["ok"] for c in r.checks) and not result.get("flash_problems") else "FAIL"
        (args.out / "result.json").write_text(json.dumps(result, indent=2, default=list) + "\n")
    print(result["verdict"], sum(c["ok"] for c in r.checks), "/", len(r.checks))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("engine", "rom", "scratch", "out"):
        parser.add_argument("--" + arg, type=Path, required=True)
    parser.add_argument("--profile", choices=("normal", "release"), required=True)
    parser.add_argument("--expect", type=Path)
    sys.exit(run(parser.parse_args()))
