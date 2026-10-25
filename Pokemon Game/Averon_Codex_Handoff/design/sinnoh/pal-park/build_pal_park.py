#!/usr/bin/env python3
"""Pal Park outdoor (W6, south-west): new physical geography in Averon's own banks (OFF-ENGINE staging).

No donor or repo map exists for Pal Park, so nothing here is donor-derived. Built with W1's attested composition
(../iron-island/build_iron_island.py), General + Dewford (the bank pair of Sandgem, Twinleaf and W2's Route 221):

- 40 x 36 park: Lake Verity trees ring the north, west and east; a grass field; a rectangular pond whose every
  8-neighbour pond/grass pattern occurs with the same metatile in Lake Verity; a sand beach meeting the sea along the
  south, every shore cell attested in Route 105/106/107 or Dewford; sand walkways.
- The gate building is Dewford's house; its door pairs with W2's closed Route 221 house shell door (82, 15), so the
  player passes through the building door to door. DEV overlay of W2's Route 221 header only (one appended warp).
No story, migration mechanic, objects, encounters or sections (MAPSEC_PENDING_OWNER).

  build_pal_park.py --engine ENGINE --out DIR
"""
import argparse
import collections
import importlib.util
import json
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("w1", HERE.parent / "iron-island/build_iron_island.py")
w1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w1)
ROUTE221 = HERE.parent / "southwest-coast/staged/Route221/map.json"

W, H = 40, 36
TREE_ROWS = 4                 # rows 0-3 trees (2 tree heights)
SAND_TOP, SEA_TOP = 27, 30    # sand rows 27-29, sea rows 30-35
POND = (22, 9, 32, 16)        # inclusive pond rectangle on grass
GATE = (17, 4)                # Dewford house top-left (5 x 4); door at (+2, +3)
PATH = [((19, 8), (19, 26)), ((8, 22), (19, 22))]
POND_IDS = {161, 176, 177, 178, 184, 186, 192, 194, 203, 204, 510, 511}


def clamp_class(grid, x, y):
    return grid[min(max(y, 0), H - 1)][min(max(x, 0), W - 1)]   # off-map continues the edge


def pond_table(eng):
    """(8 neighbour grass flags) -> pond metatile, learned from Lake Verity's pond water cells."""
    w, h, c = eng.cells("LakeVerity")
    table = collections.defaultdict(collections.Counter)
    land = lambda x, y: 0 <= x < w and 0 <= y < h and c[y * w + x] & 1023 not in POND_IDS
    for y in range(h):
        for x in range(w):
            if c[y * w + x] & 1023 in POND_IDS:
                table[tuple(land(x + dx, y + dy) for dx, dy in w1.NB8)][c[y * w + x] & 1023] += 1
    return table


def build(engine):
    eng = w1.Engine(engine)
    ocean, verity = eng.words(w1.OCEAN_CORPUS), eng.words(("LakeVerity",))
    grass, sand = eng.word("LakeVerity", 19, 20, 1), eng.word("DewfordTown", 8, 9, 292)
    cells = [grass] * (W * H)
    # sea / beach: strict attested shore along the south
    grid = [["S" if y < SEA_TOP else "W" for _ in range(W)] for y in range(H)]
    table = w1.shore_table(eng)
    for y in range(SAND_TOP - 1, H):
        for x in range(W):
            nb = tuple(clamp_class(grid, x + dx, y + dy) == "S" for dx, dy in w1.NB8)
            me = grid[y][x]
            if me == "S" and all(nb):
                if y >= SAND_TOP:
                    cells[y * W + x] = sand
                continue
            key = (me,) + nb
            if key not in table:
                raise SystemExit(f"unattested shore pattern at {(x, y)}: {key}")
            cells[y * W + x] = ocean[table[key].most_common(1)[0][0]]
    for y in range(SAND_TOP, SEA_TOP):
        for x in range(W):
            if cells[y * W + x] == grass:
                cells[y * W + x] = sand
    # pond: strict attested pond shore
    ptab = pond_table(eng)
    x0, y0, x1, y1 = POND
    inside = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            key = tuple(not inside(x + dx, y + dy) for dx, dy in w1.NB8)
            if key not in ptab:
                raise SystemExit(f"unattested pond pattern at {(x, y)}: {key}")
            cells[y * W + x] = verity[ptab[key].most_common(1)[0][0]]
    for (a, b), (c, d) in PATH:
        for y in range(b, d + 1):
            for x in range(a, c + 1):
                cells[y * W + x] = sand
    # tree ring: north rows and west/east two-tile columns down to the beach
    def tree(tx, ty):
        for (dx, dy), mid in zip(((0, 0), (1, 0), (0, 1), (1, 1)), (470, 471, 478, 479)):
            cells[(ty + dy) * W + tx + dx] = verity[mid]
    for ty in range(0, TREE_ROWS, 2):
        for tx in range(0, W, 2):
            tree(tx, ty)
    for ty in range(TREE_ROWS, SEA_TOP, 2):          # down over the beach: no walkable map edge
        for tx in (0, W - 2):
            tree(tx, ty)
    for tx, ty in [(4, 12), (8, 16), (12, 10), (34, 20), (6, 6), (30, 5)]:
        tree(tx, ty)
    gx, gy = GATE
    dew = eng.cells("DewfordTown")[2]
    for j in range(4):
        for i in range(5):
            cells[(gy + j) * W + gx + i] = dew[j * 20 + 1 + i]
    door = (gx + 2, gy + 3)
    assert cells[door[1] * W + door[0]] & 1023 == 549
    hdr = w1.header("MAP_PAL_PARK", "PalPark", "LAYOUT_PAL_PARK", "MUS_ROUTE101", "MAP_TYPE_ROUTE",
                    [(*door, "MAP_ROUTE221", 0)])
    r221 = json.loads(ROUTE221.read_text())
    assert r221["warp_events"] == []
    r221["warp_events"] = [{"x": 82, "y": 15, "elevation": 0, "dest_map": "MAP_PAL_PARK", "dest_warp_id": "0"}]
    return eng, cells, hdr, r221, door


def write(engine, out):
    eng, cells, hdr, r221, door = build(engine)
    d = pathlib.Path(out) / "staged"
    (d / "PalPark").mkdir(parents=True, exist_ok=True)
    (d / "Route221-dev-overlay").mkdir(parents=True, exist_ok=True)
    data = struct.pack("<%dH" % len(cells), *cells)
    (d / "PalPark/map.bin").write_bytes(data)
    (d / "PalPark/border.bin").write_bytes(struct.pack("<4H", *[eng.word("LakeVerity", 0, 0, 478)] * 4))
    (d / "PalPark/map.json").write_text(json.dumps(hdr, indent=2) + "\n")
    (d / "PalPark/scripts.inc").write_text(w1.scripts("PalPark"))
    (d / "Route221-dev-overlay/map.json").write_text(json.dumps(r221, indent=2) + "\n")
    bank = w1.render.Bank(eng.root / "data/tilesets/primary/general", eng.root / "data/tilesets/secondary/dewford")
    w1.render.render_cells(bank, cells, W, d / "PalPark/preview.png")
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "map_sha256": w1.sha(data), "door": door,
               "inputs_sha256": dict(sorted(eng.read.items()))}
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(json.dumps(write(a.engine, a.out), indent=2))
