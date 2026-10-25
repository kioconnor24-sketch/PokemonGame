#!/usr/bin/env python3
"""Wayward Cave (W7): new physical geography behind Route 206's open cave mouth, in Averon's own banks (OFF-ENGINE).

No donor, main or open-PR map exists for Wayward Cave, so nothing here is donor-derived. Two floors in W1's cave kit
(../iron-island/build_iron_island.py: Oreburgh Gate 1F wall kit, Granite Cave exit mouth and ladders), General + Cave:
- WaywardCave_1F (44 x 32): one large chamber broken up by five rock blocks; the cave-mouth exit at the bottom returns
  to Route 206 (18, 30); a ladder leads down.
- WaywardCave_B1F (32 x 24): a chamber with two rock blocks and the ladder up.
Route 206 (Codex's eterna-cycle staging) already draws an open cave mouth at (18, 30) with no warp; a DEV-only
overlay of its map.json appends one warp there. Its map data and files are not modified.
No story, objects, items, encounters or sections (MAPSEC_PENDING_OWNER).

  build_wayward_cave.py --engine ENGINE --out DIR
"""
import argparse
import importlib.util
import json
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("w1", HERE.parent / "iron-island/build_iron_island.py")
w1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w1)
ROUTE206 = HERE.parent / "eterna-cycle/staged/Route206"
MOUTH = (18, 30)


def floor_1f(eng):
    cv = w1.Cave(eng, 44, 32)
    cv.room(3, 3, 40, 27)
    for b in [(7, 6, 13, 11), (19, 6, 26, 10), (31, 7, 37, 12), (8, 17, 15, 22), (24, 15, 33, 21)]:
        cv.block(*b)
    cv.exit_south(20, 27, eng)
    cv.ladder(38, 4, eng, down=True)
    return cv, dict(exit=(20, 27), ladder=(38, 4))


def floor_b1f(eng):
    cv = w1.Cave(eng, 32, 24)
    cv.room(3, 3, 28, 19)
    cv.block(7, 7, 13, 12)
    cv.block(18, 10, 25, 15)
    cv.ladder(26, 4, eng, down=False)
    return cv, dict(ladder=(26, 4))


def build(engine):
    eng = w1.Engine(engine)
    c1, p1 = floor_1f(eng)
    c2, p2 = floor_b1f(eng)
    raw = (ROUTE206 / "averon-map.bin").read_bytes()
    cells = struct.unpack("<%dH" % (len(raw) // 2), raw)
    mouth = cells[MOUTH[1] * 28 + MOUTH[0]]
    assert mouth & 1023 == 167 and not mouth & 0xC00, hex(mouth)       # open General cave mouth, no warp yet
    r206 = json.loads((ROUTE206 / "map.json").read_text())
    assert all((w["x"], w["y"]) != MOUTH for w in r206["warp_events"])
    index = len(r206["warp_events"])
    r206["warp_events"].append({"x": MOUTH[0], "y": MOUTH[1], "elevation": 0, "dest_map": "MAP_WAYWARD_CAVE_1F",
                                "dest_warp_id": "0"})
    maps = {
        "WaywardCave_1F": (w1.header("MAP_WAYWARD_CAVE_1F", "WaywardCave_1F", "LAYOUT_WAYWARD_CAVE_1F", "MUS_CAVE_OF_ORIGIN",
                                     "MAP_TYPE_UNDERGROUND", [(*p1["exit"], "MAP_ROUTE206", index),
                                                              (*p1["ladder"], "MAP_WAYWARD_CAVE_B1F", 0)]), c1),
        "WaywardCave_B1F": (w1.header("MAP_WAYWARD_CAVE_B1F", "WaywardCave_B1F", "LAYOUT_WAYWARD_CAVE_B1F",
                                      "MUS_CAVE_OF_ORIGIN", "MAP_TYPE_UNDERGROUND",
                                      [(*p2["ladder"], "MAP_WAYWARD_CAVE_1F", 1)]), c2),
    }
    return eng, maps, r206


def write(engine, out):
    eng, maps, r206 = build(engine)
    st = pathlib.Path(out) / "staged"
    bank = w1.render.Bank(eng.root / "data/tilesets/primary/general", eng.root / "data/tilesets/secondary/cave")
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "maps": {}}
    for name, (hdr, cv) in maps.items():
        d = st / name
        d.mkdir(parents=True, exist_ok=True)
        data = struct.pack("<%dH" % len(cv.cells), *cv.cells)
        (d / "map.bin").write_bytes(data)
        (d / "border.bin").write_bytes(struct.pack("<4H", *[cv.k[529]] * 4))
        (d / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (d / "scripts.inc").write_text(w1.scripts(name))
        w1.render.render_cells(bank, cv.cells, cv.w, d / "preview.png")
        receipt["maps"][name] = {"width": cv.w, "height": cv.h, "map_sha256": w1.sha(data)}
    (st / "Route206-dev-overlay").mkdir(parents=True, exist_ok=True)
    (st / "Route206-dev-overlay/map.json").write_text(json.dumps(r206, indent=2) + "\n")
    receipt["inputs_sha256"] = dict(sorted(eng.read.items()))
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(json.dumps(write(a.engine, a.out), indent=2))
