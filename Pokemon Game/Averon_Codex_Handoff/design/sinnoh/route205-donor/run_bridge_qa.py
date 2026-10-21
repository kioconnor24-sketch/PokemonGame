#!/usr/bin/env python3
"""Supplement existing connected QA with ordinary over/under bridge walking.

Uses a game-written scratch save, never writes live memory. The lower approach
is source-pinned because the shared navigator ignores elevation and can choose
the upper bridge when asked to walk underneath. Original failed evidence stays.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys

from run_connected_qa import DIRS, validate_route

HERE = Path(__file__).resolve().parent


def run(args):
    engine = args.engine.resolve()
    sys.path.insert(0, str(engine.parent / "scripts/claude_play"))
    import map_qa as qa
    w = qa._wrapper(engine)
    from codex_cry_gameplay import driver, emu, game, play
    spec = json.loads((HERE / "south-lower-route.json").read_text())
    points = validate_route(spec, (engine / "data/layouts/Route205_South/map.bin").read_bytes())
    exit_spec = json.loads((HERE / "south-exit-route.json").read_text())
    exit_points = validate_route(exit_spec, (engine / "data/layouts/Route205_South/map.bin").read_bytes(), allow_bridges=True)
    world = qa.mapdata.World(engine)
    if any(not world.map(spec["map"]).walkable(*p) for p in points + exit_points):
        raise ValueError("lower approach crosses non-walking terrain")
    args.out.mkdir(parents=True, exist_ok=True)
    if any(args.out.iterdir()):
        raise ValueError("OUT must be empty")
    args.scratch.mkdir(parents=True, exist_ok=True)
    rom = args.scratch / "game.gba"
    shutil.copyfile(args.rom, rom)
    shutil.copyfile(args.save, rom.with_suffix(".sav"))
    info = emu.load_build_info(args.rom.with_suffix(".elf"), engine, args.scratch / "symbol-cache")
    info["symbols"] = w.lto_aliases(info["symbols"])
    findings, plan = qa.static_audit(world, ["MAP_ROUTE205_SOUTH", "MAP_ROUTE205_NORTH"])
    if findings:
        raise ValueError("source must pass static audit before bridge gameplay")
    e = emu.Emulator(rom, args.out, display=args.display, audio=False)
    g = game.Game(e, info)
    w.use_source_function_names(g)
    d = driver.Driver(e, g, world, args.out / "events.jsonl")
    d.moves = game.MoveTable(rom, info)
    g.map_names = d.w.by_num
    r = qa.Runner(d, world, plan, args.out)
    error = None

    def go(mid, tile, label):
        if d.here()[0] != mid:
            d.travel_to(mid)
        ok = r.go(mid, tile)
        actual = r.wait_settled()
        reached = ok and actual == (mid, tile)
        r.check(label, reached, at=actual)
        if not reached:
            raise RuntimeError("cannot reach " + label)
        d.shot(label)
        r.follower(label)

    try:
        play.boot(d, False)
        r.wait_settled()
        mid = "MAP_ROUTE205_SOUTH"
        go(mid, (25, 84), "south-bridge-south-ground")
        for tile in [(25, 83), (25, 82), (25, 81), (25, 80), (25, 79)]:
            go(mid, tile, "south-bridge-up-" + str(tile))
        r.blocked(mid, 26, 81, "right")  # Real water; the fixture has no Surf.
        go(mid, (25, 84), "south-bridge-return")
        for tile, label in [((20, 61), "stair-lower-ground"), ((19, 61), "stair-transition"),
                            ((18, 61), "stair-upper-ground"), ((15, 48), "upper-bridge-south-ground"),
                            ((15, 39), "upper-bridge-north-ground")]:
            go(mid, tile, label)
        for y in range(40, 49):
            go(mid, (15, y), "upper-bridge-over-" + str(y))
        for tile, label in [((18, 61), "stair-upper-return"), ((19, 61), "stair-transition-return"),
                            ((20, 61), "stair-lower-return")]:
            go(mid, tile, label)
        # The shared follower probe walks independently. Reestablish the exact
        # route anchor after it, then validate every subsequent controller step.
        if not r.go(spec["map"], points[0]) or d.here() != (spec["map"], points[0]):
            raise RuntimeError("lower approach started on the wrong tile")
        for direction, target in zip(spec["steps"], points[1:]):
            d.step(direction)
            actual = r.wait_settled()
            d.log("lower-route-step", direction=direction, expected=(mid, target), actual=actual)
            if actual != (mid, target):
                raise RuntimeError("lower approach missed its exact next tile")
        go(mid, (17, 44), "upper-bridge-east-grass")
        for x in range(16, 12, -1):
            go(mid, (x, 44), "upper-bridge-under-" + str(x))
        if not r.go(mid, exit_points[0]) or d.here() != (mid, exit_points[0]):
            raise RuntimeError("North exit approach started on the wrong tile")
        for direction, target in zip(exit_spec["steps"], exit_points[1:]):
            d.step(direction)
            actual = r.wait_settled()
            d.log("north-exit-route-step", direction=direction, expected=(mid, target), actual=actual)
            if actual != (mid, target):
                raise RuntimeError("North exit approach missed its exact next tile")
        d.step("up")
        if r.wait_settled() != ("MAP_ROUTE205_NORTH", (2, 59)):
            raise RuntimeError("North exit approach missed its exact seam landing")
        mid = "MAP_ROUTE205_NORTH"
        for tile in [(60, 16), (60, 17), (60, 18), (61, 18), (62, 18)]:
            go(mid, tile, "north-converted-walkway-" + str(tile))
    except BaseException as exc:
        error = repr(exc)
    finally:
        e.close()
        result = dict(profile=args.profile, rom_sha256=play.sha256(rom), checks=r.checks, error=error,
            scope="ordinary walking/followers over and under bridges, no-Surf water refusal and converted walkway; NOT Surf or production-origin acceptance")
        result["verdict"] = "PASS" if error is None and len(r.checks) == 69 and all(c["ok"] for c in r.checks) else "FAIL"
        (args.out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(result["verdict"], sum(c["ok"] for c in r.checks), "/", len(r.checks))
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("engine", "rom", "save", "scratch", "out"):
        parser.add_argument("--" + arg, type=Path, required=True)
    parser.add_argument("--profile", choices=("normal", "release"), required=True)
    parser.add_argument("--display", type=int, default=77)
    sys.exit(run(parser.parse_args()))
