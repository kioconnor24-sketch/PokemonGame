#!/usr/bin/env python3
"""Great Marsh (W10): new physical geography behind Pastoria's closed north building (OFF-ENGINE staging).

No donor, main or open-PR map exists for the Great Marsh. Built with W1/W6's attested composition, General + Dewford:
- GreatMarsh (48 x 40): a tree ring around wet grassland with six rectangular ponds whose every 8-neighbour pond/grass
  pattern occurs with the same metatile in Lake Verity (strict), tall-grass patches (art only: no encounter table),
  sand walkways linking them, and the entry gate house (Dewford's house) at the south.
- GreatMarsh_Gate: Averon's stock Seaside Cycling Road entrance (two mat pairs, unchanged): west mats return to
  Pastoria, east mats open onto the marsh.
Pastoria (Codex's eastern-loop staging) draws an animated door at (36, 8) with no warp; a DEV-only overlay of its
map.json appends one warp there. Its map data and files are not modified.
No story, Safari mechanic, encounters, objects or sections (MAPSEC_PENDING_OWNER).

  build_great_marsh.py --engine ENGINE --out DIR
"""
import argparse
import importlib.util
import json
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pal", HERE.parent / "pal-park/build_pal_park.py")
pal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pal)
w1 = pal.w1
PASTORIA = HERE.parent / "eastern-loop/staged/PastoriaCity"
DOOR = (36, 8)
W, H = 48, 40
PONDS = [(6, 5, 12, 10), (18, 4, 27, 8), (33, 6, 41, 12), (5, 17, 11, 24), (20, 15, 29, 21), (34, 20, 42, 26)]
TALL = [(14, 11, 18, 14), (30, 14, 33, 18), (13, 26, 19, 30), (26, 25, 31, 29)]
PATHS = [((23, 22), (23, 33)), ((8, 13), (42, 13)), ((15, 9), (15, 27)), ((31, 9), (31, 31)), ((8, 28), (42, 28))]
# Pastoria's other warp-less animated doors open into neutral LAYOUT_HOUSE1 shells (no NPCs/services).
PASTORIA_DOORS = [(26, 14), (50, 18), (26, 22), (15, 26), (27, 34), (37, 34), (15, 43), (27, 43)]
GATE = (21, 32)                                     # Dewford house top-left; door (+2, +3) = (23, 35)


def build(engine):
    eng = w1.Engine(engine)
    verity = eng.words(("LakeVerity",))
    grass, sand = eng.word("LakeVerity", 19, 20, 1), eng.word("DewfordTown", 8, 9, 292)
    tall = eng.word("LakeVerity", 3, 37, 13) if eng.cells("LakeVerity")[2][37 * 48 + 3] & 1023 == 13 else None
    if tall is None:
        tall = next(v for v in eng.cells("LakeVerity")[2] if v & 1023 == 13)
    cells = [grass] * (W * H)
    ptab = pal.pond_table(eng)
    for x0, y0, x1, y1 in PONDS:
        inside = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                key = tuple(not inside(x + dx, y + dy) for dx, dy in w1.NB8)
                if key not in ptab:
                    raise SystemExit(f"unattested pond pattern at {(x, y)}: {key}")
                cells[y * W + x] = verity[ptab[key].most_common(1)[0][0]]
    for x0, y0, x1, y1 in TALL:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if cells[y * W + x] == grass:
                    cells[y * W + x] = tall
    for (a, b), (c, d) in PATHS:
        for y in range(b, d + 1):
            for x in range(a, c + 1):
                if cells[y * W + x] in (grass, tall):
                    cells[y * W + x] = sand

    def tree(tx, ty):
        for (dx, dy), mid in zip(((0, 0), (1, 0), (0, 1), (1, 1)), (470, 471, 478, 479)):
            cells[(ty + dy) * W + tx + dx] = verity[mid]
    for tx in range(0, W, 2):
        tree(tx, 0), tree(tx, H - 2)
        if tx in (0, W - 2):
            for ty in range(2, H - 2, 2):
                tree(tx, ty)
    for tx in range(2, W - 2, 2):                               # south hedge row behind the gate house
        if tx not in (20, 22, 24):
            tree(tx, H - 4)
    gx, gy = GATE
    dew = eng.cells("DewfordTown")[2]
    for j in range(4):
        for i in range(5):
            cells[(gy + j) * W + gx + i] = dew[j * 20 + 1 + i]
    door = (gx + 2, gy + 3)
    assert cells[door[1] * W + door[0]] & 1023 == 549
    raw = (PASTORIA / "averon-map.bin").read_bytes()
    pc = struct.unpack("<%dH" % (len(raw) // 2), raw)
    assert pc[DOOR[1] * 68 + DOOR[0]] & 1023 == 533                   # Pastoria's animated north door, no warp
    past = json.loads((PASTORIA / "map.json").read_text())
    assert all((w["x"], w["y"]) != DOOR for w in past["warp_events"])
    index = len(past["warp_events"])
    past["warp_events"].append({"x": DOOR[0], "y": DOOR[1], "elevation": 0, "dest_map": "MAP_GREAT_MARSH_GATE",
                                "dest_warp_id": "0"})
    shells = {}
    for k, (x, y) in enumerate(PASTORIA_DOORS, 1):
        assert pc[y * 68 + x] & 0xC00 and all((w["x"], w["y"]) != (x, y) for w in past["warp_events"]), (x, y)
        i = len(past["warp_events"])
        name = f"PastoriaCity_House{k}"
        past["warp_events"].append({"x": x, "y": y, "elevation": 0, "dest_map": f"MAP_PASTORIA_CITY_HOUSE{k}",
                                    "dest_warp_id": "0"})
        shells[name] = w1.header(f"MAP_PASTORIA_CITY_HOUSE{k}", name, "LAYOUT_HOUSE1", "MUS_ROUTE110", "MAP_TYPE_INDOOR",
                                 [(3, 8, "MAP_PASTORIA_CITY", i), (4, 8, "MAP_PASTORIA_CITY", i)])
    marsh = w1.header("MAP_GREAT_MARSH", "GreatMarsh", "LAYOUT_GREAT_MARSH", "MUS_ROUTE110", "MAP_TYPE_ROUTE",
                      [(*door, "MAP_GREAT_MARSH_GATE", 2)])
    assert "LAYOUT_ROUTE110_SEASIDE_CYCLING_ROAD_ENTRANCE" in eng.layout_ids
    gate = w1.header("MAP_GREAT_MARSH_GATE", "GreatMarsh_Gate", "LAYOUT_ROUTE110_SEASIDE_CYCLING_ROAD_ENTRANCE",
                     "MUS_ROUTE110", "MAP_TYPE_INDOOR",
                     [(1, 5, "MAP_PASTORIA_CITY", index), (2, 5, "MAP_PASTORIA_CITY", index),
                      (12, 5, "MAP_GREAT_MARSH", 0), (13, 5, "MAP_GREAT_MARSH", 0)])
    return eng, cells, marsh, gate, past, door, shells


def write(engine, out):
    eng, cells, marsh, gate, past, door, shells = build(engine)
    st = pathlib.Path(out) / "staged"
    for name, hdr in [("GreatMarsh", marsh), ("GreatMarsh_Gate", gate)] + list(shells.items()):
        (st / name).mkdir(parents=True, exist_ok=True)
        (st / name / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (st / name / "scripts.inc").write_text(w1.scripts(name))
    data = struct.pack("<%dH" % len(cells), *cells)
    (st / "GreatMarsh/map.bin").write_bytes(data)
    (st / "GreatMarsh/border.bin").write_bytes(struct.pack("<4H", *[eng.word("LakeVerity", 0, 0, 478)] * 4))
    (st / "PastoriaCity-dev-overlay").mkdir(parents=True, exist_ok=True)
    (st / "PastoriaCity-dev-overlay/map.json").write_text(json.dumps(past, indent=2) + "\n")
    bank = w1.render.Bank(eng.root / "data/tilesets/primary/general", eng.root / "data/tilesets/secondary/dewford")
    w1.render.render_cells(bank, cells, W, st / "GreatMarsh/preview.png")
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
