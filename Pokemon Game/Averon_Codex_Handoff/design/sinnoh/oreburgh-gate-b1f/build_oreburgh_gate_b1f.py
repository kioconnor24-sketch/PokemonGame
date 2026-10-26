#!/usr/bin/env python3
"""Oreburgh Gate B1F (W16, western lane): the lower floor under production Oreburgh Gate 1F (OFF-ENGINE staging).

Production OreburghGate_1F (29 x 27, General + Cave) has a dead-end alcove north of its west room (rows 4-6,
x 7-20) where the DS gate's stairs lead down; nothing is there. A DEV-only derived copy of its blockdata (overlay
map.bin; the engine file is not modified) puts a Granite Cave down-ladder at (18, 5), and a header overlay appends
its warp. Nothing else changes: the Route 203 exit keeps index 0. Codex's DEV restoration of the east exit
(oreburgh-donor warp-plan, warp 1 at (25, 20)) is independent of this cell and is appended after it at integration.

B1F (44 x 34) is new, drawn with W1's cave kit (Oreburgh Gate 1F's own wall pieces) in Averon General + Cave: one
wide chamber whose rock outcrops split it into lanes, with the up-ladder in the north-west corner. No boulders,
items, objects, encounters, story or sections (MAPSEC_PENDING_OWNER).

  build_oreburgh_gate_b1f.py --engine ENGINE --out DIR
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("w1", HERE.parent / "iron-island/build_iron_island.py")
w1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w1)
MUSIC = "MUS_CAVE_OF_ORIGIN"
LADDER_1F = (18, 5)
ALCOVE = [(x, y) for y in (4, 5, 6) for x in range(7, 21)]
BLOCKS = [(8, 7, 15, 12), (20, 7, 27, 11), (32, 6, 37, 13), (8, 17, 14, 25), (19, 16, 30, 20), (19, 24, 26, 28),
          (34, 19, 38, 26)]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def b1f(eng):
    cv = w1.Cave(eng, 44, 34)
    cv.room(3, 3, 40, 30)
    for b in BLOCKS:
        cv.block(*b)
    cv.ladder(5, 4, eng, down=False)
    return cv, (5, 4)


def build(engine_root):
    eng = w1.Engine(engine_root)
    gate = json.loads(eng.file("data/maps/OreburghGate_1F/map.json"))
    assert gate["layout"] == "LAYOUT_OREBURGH_GATE_1F"
    width, height, cells = eng.cells("OreburghGate_1F")
    floor = cells[LADDER_1F[1] * width + LADDER_1F[0]]
    assert all(cells[y * width + x] == floor for x, y in ALCOVE), "alcove is no longer plain floor"
    assert all((w["x"], w["y"]) not in ALCOVE for w in gate["warp_events"])
    blocks = list(cells)
    blocks[LADDER_1F[1] * width + LADDER_1F[0]] = eng.word("GraniteCave_1F", 17, 11, 575)
    i = len(gate["warp_events"])
    gate["warp_events"].append({"x": LADDER_1F[0], "y": LADDER_1F[1], "elevation": 0,
                                "dest_map": "MAP_OREBURGH_GATE_B1F", "dest_warp_id": "0"})
    cv, up = b1f(eng)
    hdr = w1.header("MAP_OREBURGH_GATE_B1F", "OreburghGate_B1F", "LAYOUT_OREBURGH_GATE_B1F", MUSIC,
                    "MAP_TYPE_UNDERGROUND", [(*up, "MAP_OREBURGH_GATE_1F", i)])
    return eng, gate, blocks, hdr, cv


def write(engine_root, out):
    eng, gate, blocks, hdr, cv = build(engine_root)
    st = pathlib.Path(out) / "staged"
    d = st / "OreburghGate_1F-dev-overlay"
    d.mkdir(parents=True, exist_ok=True)
    (d / "map.json").write_text(json.dumps(gate, indent=2) + "\n")
    (d / "map.bin").write_bytes(struct.pack("<%dH" % len(blocks), *blocks))
    d = st / "OreburghGate_B1F"
    d.mkdir(parents=True, exist_ok=True)
    (d / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
    (d / "scripts.inc").write_text(w1.scripts("OreburghGate_B1F"))
    data = struct.pack("<%dH" % len(cv.cells), *cv.cells)
    border = struct.pack("<4H", *[cv.k[529]] * 4)
    (d / "map.bin").write_bytes(data)
    (d / "border.bin").write_bytes(border)
    (d / "layout.json").write_text(json.dumps({"id": hdr["layout"], "name": "OreburghGate_B1F_Layout", "width": cv.w,
                                               "height": cv.h, "primary_tileset": "gTileset_General",
                                               "secondary_tileset": "gTileset_Cave"}, indent=2) + "\n")
    bank = w1.render.Bank(eng.root / "data/tilesets/primary/general", eng.root / "data/tilesets/secondary/cave")
    w1.render.render_cells(bank, cv.cells, cv.w, d / "preview.png")
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "b1f_sha256": sha(data), "border_sha256": sha(border),
               "ladder_1f": LADDER_1F, "inputs_sha256": dict(sorted(eng.read.items()))}
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(write(a.engine, a.out)["status"])
