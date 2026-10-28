#!/usr/bin/env python3
"""Verity Cavern (W4): a one-room cave behind Lake Verity's islet cave mouth, in Averon's own banks (OFF-ENGINE).

Lake Verity (on main) draws a cave mouth at (23, 19) with its collision bit set and no warp. This adds the room it
leads to, drawn with W1's cave kit (Oreburgh Gate 1F walls, Granite Cave exit mouth), and a DEV-only overlay of
Lake Verity's map.bin/map.json that clears that one collision bit and adds the reciprocal warp. The production Lake
Verity files are not modified; opening the mouth for real is an owner decision. The islet is reached by Surf only.
No legendary, story, objects or sections (MAPSEC_PENDING_OWNER).

  build_verity_cavern.py --engine ENGINE --out DIR
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
MOUTH = (23, 19)
EXIT = (10, 11)


def build(engine):
    eng = w1.Engine(engine)
    cv = w1.Cave(eng, 21, 16)
    cv.room(3, 3, 17, 11)
    cv.block(7, 5, 13, 8)
    cv.exit_south(*EXIT, eng)
    w, h, lake = eng.cells("LakeVerity")
    i = MOUTH[1] * w + MOUTH[0]
    assert lake[i] & 1023 == 167 and lake[i] & 0xC00, hex(lake[i])
    lake = list(lake)
    lake[i] &= ~0xC00
    lake_hdr = json.loads((pathlib.Path(engine) / "data/maps/LakeVerity/map.json").read_text())
    assert len(lake_hdr["warp_events"]) == 2
    lake_hdr["warp_events"].append({"x": MOUTH[0], "y": MOUTH[1], "elevation": 0, "dest_map": "MAP_VERITY_CAVERN",
                                    "dest_warp_id": "0"})
    hdr = w1.header("MAP_VERITY_CAVERN", "VerityCavern", "LAYOUT_VERITY_CAVERN", "MUS_CAVE_OF_ORIGIN",
                    "MAP_TYPE_UNDERGROUND", [(*EXIT, "MAP_LAKE_VERITY", 2)])
    return eng, hdr, cv, lake, lake_hdr


def write(engine, out):
    eng, hdr, cv, lake, lake_hdr = build(engine)
    d = pathlib.Path(out) / "staged"
    (d / "VerityCavern").mkdir(parents=True, exist_ok=True)
    (d / "LakeVerity-dev-overlay").mkdir(parents=True, exist_ok=True)
    data = struct.pack("<%dH" % len(cv.cells), *cv.cells)
    (d / "VerityCavern/map.bin").write_bytes(data)
    (d / "VerityCavern/border.bin").write_bytes(struct.pack("<4H", *[cv.k[529]] * 4))
    (d / "VerityCavern/map.json").write_text(json.dumps(hdr, indent=2) + "\n")
    (d / "VerityCavern/scripts.inc").write_text(w1.scripts("VerityCavern"))
    bank = w1.render.Bank(eng.root / "data/tilesets/primary/general", eng.root / "data/tilesets/secondary/cave")
    w1.render.render_cells(bank, cv.cells, cv.w, d / "VerityCavern/preview.png")
    lake_bin = struct.pack("<%dH" % len(lake), *lake)
    (d / "LakeVerity-dev-overlay/map.bin").write_bytes(lake_bin)
    (d / "LakeVerity-dev-overlay/map.json").write_text(json.dumps(lake_hdr, indent=2) + "\n")
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "cavern_sha256": w1.sha(data),
               "lake_overlay_sha256": w1.sha(lake_bin), "lake_changed_cells": [MOUTH],
               "inputs_sha256": dict(sorted(eng.read.items()))}
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(json.dumps(write(a.engine, a.out), indent=2))
