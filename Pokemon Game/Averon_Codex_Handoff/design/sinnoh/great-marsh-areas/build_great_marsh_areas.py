#!/usr/bin/env python3
"""Great Marsh areas (W18, south-east lane): W10's marsh grows into a 2 x 2 loop of connected areas.

OFF-ENGINE staging, new construction with W10's attested composition (General + Dewford; Lake Verity grass, tall
grass and 2 x 2 trees; Dewford sand; rectangular ponds whose every 8-neighbour pattern occurs in Lake Verity,
strict). W10's GreatMarsh (the south-east area, with the gate house) is re-staged with two 4-cell gaps cut in its
tree ring, whole trees only: north (x 22-25) and west (rows 18-21). Three new 48 x 40 areas join it by map
connections, offset 0, through gaps at the same cells:

    NorthWest --- North
        |           |
      West  --- GreatMarsh (gate house, south; Pastoria)

so every area is reached two ways. All share one tileset pair, so each seam draws its neighbour correctly.
No Safari mechanic, encounters (tall grass is art only), objects, story or sections (MAPSEC_PENDING_OWNER).

  build_great_marsh_areas.py --engine ENGINE --out DIR
"""
import argparse
import importlib.util
import json
import pathlib
import re
import struct

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("w10", HERE.parent / "great-marsh/build_great_marsh.py")
w10 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w10)
pal, w1 = w10.pal, w10.w1
W, H = w10.W, w10.H
GAP_X, GAP_Y = 22, 18                # top-left cell of the 4-cell north/south gap (x) and west/east gap (y)
TREE = (470, 471, 478, 479)
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
LINKS = [("GreatMarsh", "up", "GreatMarsh_North"), ("GreatMarsh", "left", "GreatMarsh_West"),
         ("GreatMarsh_North", "left", "GreatMarsh_NorthWest"), ("GreatMarsh_West", "up", "GreatMarsh_NorthWest")]
# New areas: ponds (x0, y0, x1, y1), tall grass patches, sand walkways ((x0, y0), (x1, y1)).
AREAS = {
    "GreatMarsh_North": dict(
        ponds=[(5, 4, 12, 9), (30, 4, 40, 9), (16, 14, 26, 20), (5, 24, 11, 31), (33, 22, 42, 30)],
        tall=[(14, 4, 19, 8), (29, 13, 35, 18), (14, 26, 21, 31), (24, 31, 30, 35)],
        paths=[((23, 21), (24, 37)), ((3, 12), (44, 12)), ((13, 12), (13, 33)), ((28, 12), (28, 33))]),
    "GreatMarsh_NorthWest": dict(
        ponds=[(4, 4, 14, 10), (20, 5, 27, 10), (33, 4, 42, 11), (6, 17, 13, 26), (19, 20, 30, 27), (36, 24, 42, 31)],
        tall=[(16, 13, 22, 17), (31, 15, 37, 20), (4, 30, 12, 35), (24, 31, 32, 35)],
        paths=[((3, 14), (45, 14)), ((16, 19), (17, 37)), ((33, 21), (45, 21))]),
    "GreatMarsh_West": dict(
        ponds=[(5, 4, 13, 9), (17, 6, 26, 12), (33, 4, 41, 10), (6, 22, 14, 30), (21, 26, 30, 32), (35, 26, 42, 33)],
        tall=[(4, 13, 10, 18), (30, 14, 36, 19), (16, 17, 24, 23), (16, 33, 22, 36)],
        paths=[((23, 2), (24, 24)), ((3, 20), (45, 20)), ((32, 21), (33, 36))]),
}


def gaps_of(name):
    return [d for a, d, b in LINKS if a == name] + [OPPOSITE[d] for a, d, b in LINKS if b == name]


def gap_trees(side):
    """Top-left cells of the 2 x 2 trees removed for a gap on this side."""
    if side == "up":
        return [(GAP_X, 0), (GAP_X + 2, 0)]
    if side == "down":
        return [(GAP_X, H - 2), (GAP_X + 2, H - 2)]
    if side == "left":
        return [(0, GAP_Y), (0, GAP_Y + 2)]
    return [(W - 2, GAP_Y), (W - 2, GAP_Y + 2)]


def gap_cells(side):
    if side in ("up", "down"):
        y = 0 if side == "up" else H - 1
        return [(x, y) for x in range(GAP_X, GAP_X + 4)]
    x = 0 if side == "left" else W - 1
    return [(x, y) for y in range(GAP_Y, GAP_Y + 4)]


def palette(eng):
    verity = eng.words(("LakeVerity",))
    grass, sand = eng.word("LakeVerity", 19, 20, 1), eng.word("DewfordTown", 8, 9, 292)
    tall = next(v for v in eng.cells("LakeVerity")[2] if v & 1023 == 13)
    return verity, grass, sand, tall


def area(eng, spec, gaps):
    verity, grass, sand, tall = palette(eng)
    cells = [grass] * (W * H)
    ptab = pal.pond_table(eng)
    for x0, y0, x1, y1 in spec["ponds"]:
        assert 3 <= x0 and x1 <= W - 4 and 3 <= y0 and y1 <= H - 4, (x0, y0)
        inside = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                assert cells[y * W + x] == grass, ("ponds overlap", x, y)
                key = tuple(not inside(x + dx, y + dy) for dx, dy in w1.NB8)
                if key not in ptab:
                    raise SystemExit(f"unattested pond pattern at {(x, y)}: {key}")
                cells[y * W + x] = verity[ptab[key].most_common(1)[0][0]]
    for x0, y0, x1, y1 in spec["tall"]:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if cells[y * W + x] == grass:
                    cells[y * W + x] = tall
    for (a, b), (c, d) in spec["paths"]:
        for y in range(b, d + 1):
            for x in range(a, c + 1):
                if cells[y * W + x] in (grass, tall):
                    cells[y * W + x] = sand
    removed = {t for side in gaps for t in gap_trees(side)}

    def tree(tx, ty):
        if (tx, ty) in removed:
            return
        for (dx, dy), mid in zip(((0, 0), (1, 0), (0, 1), (1, 1)), TREE):
            cells[(ty + dy) * W + tx + dx] = verity[mid]
    for tx in range(0, W, 2):
        tree(tx, 0), tree(tx, H - 2)
        if tx in (0, W - 2):
            for ty in range(2, H - 2, 2):
                tree(tx, ty)
    return cells


def cut(eng, cells, gaps):
    """W10's marsh with whole ring trees removed at the gaps (grass in their place)."""
    verity, grass, _, _ = palette(eng)
    out = list(cells)
    for side in gaps:
        for tx, ty in gap_trees(side):
            for (dx, dy), mid in zip(((0, 0), (1, 0), (0, 1), (1, 1)), TREE):
                assert out[(ty + dy) * W + tx + dx] == verity[mid], (side, tx, ty)
                out[(ty + dy) * W + tx + dx] = grass
    return out


def build(engine):
    eng, marsh_cells, marsh, gate, past, door, shells = w10.build(engine)
    maps = {"GreatMarsh": (marsh, cut(eng, marsh_cells, gaps_of("GreatMarsh")))}
    for name, spec_ in AREAS.items():
        const = "MAP_" + re.sub(r"(?<=[a-z])(?=[A-Z])", "_", name).upper()
        hdr = w1.header(const, name, "LAYOUT_" + const[4:], "MUS_ROUTE110", "MAP_TYPE_ROUTE", [])
        maps[name] = (hdr, area(eng, spec_, gaps_of(name)))
    for a, d, b in LINKS:
        maps[a][0]["connections"].append({"map": maps[b][0]["id"], "offset": 0, "direction": d})
        maps[b][0]["connections"].append({"map": maps[a][0]["id"], "offset": 0, "direction": OPPOSITE[d]})
    return eng, maps


def check(maps):
    """Every connection has its reciprocal, and both sides of every seam are open on the same cells."""
    by_id = {h["id"]: (n, h) for n, (h, _) in maps.items()}
    for name, (hdr, cells) in maps.items():
        for c in hdr["connections"]:
            other_name, other = by_id[c["map"]]
            back = [k for k in other["connections"] if k["map"] == hdr["id"]]
            assert back == [{"map": hdr["id"], "offset": -c["offset"], "direction": OPPOSITE[c["direction"]]}], (name, c)
            mine = [cells[y * W + x] & 0xC00 for x, y in gap_cells(c["direction"])]
            theirs = [maps[other_name][1][y * W + x] & 0xC00 for x, y in gap_cells(OPPOSITE[c["direction"]])]
            assert not any(mine) and not any(theirs), (name, c)
    return True


def write(engine, out):
    eng, maps = build(engine)
    check(maps)
    st = pathlib.Path(out) / "staged"
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "maps": {}}
    border = struct.pack("<4H", *[eng.word("LakeVerity", 0, 0, 478)] * 4)
    bank = w1.render.Bank(eng.root / "data/tilesets/primary/general", eng.root / "data/tilesets/secondary/dewford")
    for name, (hdr, cells) in maps.items():
        d = st / name
        d.mkdir(parents=True, exist_ok=True)
        data = struct.pack("<%dH" % len(cells), *cells)
        (d / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (d / "scripts.inc").write_text(w1.scripts(name))
        (d / "map.bin").write_bytes(data)
        (d / "border.bin").write_bytes(border)
        (d / "layout.json").write_text(json.dumps({"id": hdr["layout"], "width": W, "height": H,
                                                   "primary_tileset": "gTileset_General",
                                                   "secondary_tileset": "gTileset_Dewford"}, indent=2) + "\n")
        w1.render.render_cells(bank, cells, W, d / "preview.png")
        receipt["maps"][name] = {"map_sha256": w1.sha(data), "connections": hdr["connections"]}
    receipt["inputs_sha256"] = dict(sorted(eng.read.items()))
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(write(a.engine, a.out)["status"])
