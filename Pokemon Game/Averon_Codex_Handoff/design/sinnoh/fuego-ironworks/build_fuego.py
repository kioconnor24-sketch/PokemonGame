#!/usr/bin/env python3
"""Fuego Ironworks (W3, west/south lane): new physical geography in Averon's own banks (OFF-ENGINE staging).

The pinned donor (LiderMorti00 @ 38228bb5) declares LAYOUT_FUEGO_IRONWORKS without any map.bin (a #237 ledger gap),
so nothing here is donor-derived. It reuses W1's attested composition (../iron-island/build_iron_island.py):

- Fuego Ironworks outdoor (40 x 30, General + Slateport): a coastal yard. Every shore cell's 8-neighbour pattern is
  attested in Averon's Route 105/106/107 or Dewford (all shore pieces are General IDs); the ironworks is Slateport's
  shipyard building (8 x 7, door at (+2, +6)) copied cell for cell; Lake Verity hills, trees and Dewford boulders
  (General IDs) and sand walkways shape the yard.
- The ironworks interior reuses LAYOUT_SLATEPORT_CITY_STERNS_SHIPYARD_1F unchanged; its upstairs (3, 1) gets no
  warp (closed).
External water access (the original's Surf river off Route 205 South, a production map) stays closed: an owner
decision. No objects, story, items, encounters or section IDs (MAPSEC_PENDING_OWNER).

  build_fuego.py --engine ENGINE --out DIR
"""
import argparse
import importlib.util
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("w1", HERE.parent / "iron-island/build_iron_island.py")
w1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w1)
render = w1.render

W, H = 40, 30
LAND = {y: (4, 30) for y in range(3, 26)}           # rectangle: every shore pattern attested
GRASS = {y: (6, 28) for y in range(5, 24)}
WORKS = (14, 6)                                     # shipyard building top-left; door at (+2, +6)
HILLS = [(6, 15, 7, 4), (22, 16, 7, 4)]
TREES = [(6, 5), (8, 5), (25, 5), (27, 5), (6, 7), (27, 7)]
PATH = [((16, 13), (16, 23)), ((9, 21), (27, 21))]
BOULDERS = [(5, 10), (29, 12), (11, 24), (24, 24), (5, 22)]


def outdoor(eng):
    ocean = eng.words(w1.OCEAN_CORPUS)
    water, sand, grass = eng.word("Route106", 26, 8, 368), eng.word("DewfordTown", 8, 9, 292), \
        eng.word("LakeVerity", 19, 20, 1)
    grid = [["W"] * W for _ in range(H)]
    for y, (x0, x1) in LAND.items():
        for x in range(x0, x1 + 1):
            grid[y][x] = "S"
    table = w1.shore_table(eng)
    cells = [water] * (W * H)
    for y in range(H):
        for x in range(W):
            nb = tuple(0 <= x + dx < W and 0 <= y + dy < H and grid[y + dy][x + dx] == "S" for dx, dy in w1.NB8)
            if grid[y][x] == "W" and not any(nb):
                continue
            key = (grid[y][x],) + nb
            if key not in table:
                raise SystemExit(f"unattested shore pattern at {(x, y)}: {key}")
            cells[y * W + x] = ocean[table[key].most_common(1)[0][0]]
    for y, (x0, x1) in GRASS.items():
        for x in range(x0, x1 + 1):
            cells[y * W + x] = grass
    for (x0, y0), (x1, y1) in PATH:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                cells[y * W + x] = sand
    verity = eng.words(("LakeVerity",))
    for tx, ty in TREES:
        for (dx, dy), mid in zip(((0, 0), (1, 0), (0, 1), (1, 1)), (470, 471, 478, 479)):
            assert cells[(ty + dy) * W + tx + dx] == grass, (tx, ty)
            cells[(ty + dy) * W + tx + dx] = verity[mid]
    for h in HILLS:
        w1.stamp_hill(eng, cells, W, *h, door=False)
    sw, _, sc = eng.cells("SlateportCity")
    bx, by = WORKS
    for j in range(7):
        for i in range(8):
            cells[(by + j) * W + bx + i] = sc[(32 + j) * sw + 24 + i]
    door = (bx + 2, by + 6)
    assert cells[door[1] * W + door[0]] & 1023 == 692 and sc[38 * sw + 26] & 1023 == 692
    boulder = eng.word("DewfordTown", 18, 15, 226)
    for x, y in BOULDERS:
        assert cells[y * W + x] & 1023 in (292, 1), (x, y)
        cells[y * W + x] = boulder
    return cells, door


def build(engine):
    eng = w1.Engine(engine)
    cells, (dx, dy) = outdoor(eng)
    out = {
        "FuegoIronworks": (w1.header("MAP_FUEGO_IRONWORKS", "FuegoIronworks", "LAYOUT_FUEGO_IRONWORKS", "MUS_ROUTE110",
                                     "MAP_TYPE_ROUTE", [(dx, dy, "MAP_FUEGO_IRONWORKS_INSIDE", 0)]),
                           (cells, W, H, "gTileset_General", "gTileset_Slateport")),
        "FuegoIronworks_Inside": (w1.header("MAP_FUEGO_IRONWORKS_INSIDE", "FuegoIronworks_Inside",
                                            "LAYOUT_SLATEPORT_CITY_STERNS_SHIPYARD_1F", "MUS_ROUTE110", "MAP_TYPE_INDOOR",
                                            [(2, 14, "MAP_FUEGO_IRONWORKS", 0), (3, 14, "MAP_FUEGO_IRONWORKS", 0)]), None),
    }
    assert "LAYOUT_SLATEPORT_CITY_STERNS_SHIPYARD_1F" in eng.layout_ids
    return eng, out


def write(engine, out):
    out = pathlib.Path(out)
    if "engine" in out.resolve().parts:
        raise SystemExit("--out must be outside engine/")
    eng, maps = build(engine)
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "maps": {}}
    for name, (hdr, layout) in maps.items():
        d = out / "staged" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (d / "scripts.inc").write_text(w1.scripts(name))
        entry = {"layout": hdr["layout"]}
        if layout:
            cells, w, h, prim, sec = layout
            data = struct.pack("<%dH" % len(cells), *cells)
            border = struct.pack("<4H", *[cells[0]] * 4)
            (d / "map.bin").write_bytes(data)
            (d / "border.bin").write_bytes(border)
            bank = render.Bank(eng.root / "data/tilesets/primary/general", eng.root / "data/tilesets/secondary/slateport")
            render.render_cells(bank, cells, w, d / "preview.png")
            entry.update(width=w, height=h, map_sha256=w1.sha(data), border_sha256=w1.sha(border))
        receipt["maps"][name] = entry
    receipt["inputs_sha256"] = dict(sorted(eng.read.items()))
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(json.dumps(write(a.engine, a.out), indent=2))
