#!/usr/bin/env python3
"""Jubilife west gate (W27): production Jubilife <-> Codex's staged Route 218 East gatehouse, joining Canalave.

OFF-ENGINE staging (owner-delegated decision, Issue 15 comment 6425492105). Production Jubilife already draws the
Route 218 gatehouse on its west strip (x 4, rows 18-21) with a west-arrow warp cell at (4, 20); the production
conversion sealed it (collision 1). Codex's staged Route218_East gatehouse closed its east mat (11, 5), which in the
donor warps into Jubilife ("unbuilt source destination", source collision 0; canalave-west source-receipt). This
reopens the pair:
- JubilifeCity-dev-overlay: production header + one warp (4, 20) -> Route218_East's east mat; a derived map.bin
  clearing that one cell's collision bit (same metatile, behaviour and elevation).
- Route218_East-dev-overlay: Codex's header + the donor's east-mat warp back to Jubilife; a derived map.bin clearing
  Codex's closure at (11, 5).
No objects, services or story. Production and Codex files are not modified.

  build_jubilife_west_gate.py --engine ENGINE --out DIR
"""
import argparse
import hashlib
import json
import pathlib
import re
import struct

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
CANALAVE = SINNOH / "canalave-west"
JUB_DOOR, GATE_MAT = (4, 20), (11, 5)


def unpack(raw):
    return list(struct.unpack("<%dH" % (len(raw) // 2), raw))


def build(engine):
    engine = pathlib.Path(engine)
    names = re.findall(r"^\s*(MB_\w+)", (engine / "include/constants/metatile_behaviors.h").read_text(), re.M)
    jub = json.loads((engine / "data/maps/JubilifeCity/map.json").read_text())
    layout = next(l for l in json.loads((engine / "data/layouts/layouts.json").read_text())["layouts"]
                  if l.get("id") == jub["layout"])
    width = layout["width"]
    jub_raw = (engine / layout["blockdata_filepath"]).read_bytes()
    jub_cells = unpack(jub_raw)
    attrs = {}
    for kind, name in (("primary", layout["primary_tileset"]), ("secondary", layout["secondary_tileset"])):
        folder = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", name.replace("gTileset_", "")).lower()
        attrs[kind] = unpack((engine / f"data/tilesets/{kind}/{folder}/metatile_attributes.bin").read_bytes())
    v = jub_cells[JUB_DOOR[1] * width + JUB_DOOR[0]]
    mid = v & 1023
    behaviour = names[(attrs["primary"][mid] if mid < 512 else attrs["secondary"][mid - 512]) & 0xFF]
    assert behaviour == "MB_WEST_ARROW_WARP" and v & 0xC00, (behaviour, hex(v))
    assert all((w["x"], w["y"]) != JUB_DOOR for w in jub["warp_events"])
    gate = json.loads((CANALAVE / "staged/Route218_East/map.json").read_text())
    gate_cells = unpack((CANALAVE / "staged/Route218_East/averon-map.bin").read_bytes())
    receipt = json.loads((CANALAVE / "source-receipt.json").read_text())
    closure = next(c for c in receipt["closure_changes"]["Route218_East"] if (c["x"], c["y"]) == GATE_MAT)
    assert closure["reason"] == "unbuilt source destination" and not (closure["before"] >> 10) & 3
    source = receipt["source_geometry_headers"]["Route218_East"]["warp_events"]
    assert any((w["x"], w["y"], w["dest_map"]) == (11, 5, "MAP_JUBILIFE_CITY") for w in source)
    jub_index, gate_index = len(jub["warp_events"]), len(gate["warp_events"])
    jub["warp_events"].append({"x": JUB_DOOR[0], "y": JUB_DOOR[1], "elevation": 0, "dest_map": gate["id"],
                               "dest_warp_id": str(gate_index)})
    gate["warp_events"].append({"x": GATE_MAT[0], "y": GATE_MAT[1], "elevation": 0, "dest_map": jub["id"],
                                "dest_warp_id": str(jub_index)})
    jub_blocks, gate_blocks = list(jub_cells), list(gate_cells)
    jub_blocks[JUB_DOOR[1] * width + JUB_DOOR[0]] &= ~0xC00
    gw = 13
    assert gate_cells[GATE_MAT[1] * gw + GATE_MAT[0]] & 0xC00
    gate_blocks[GATE_MAT[1] * gw + GATE_MAT[0]] &= ~0xC00
    hashes = {"engine/data/maps/JubilifeCity/map.json": hashlib.sha256((engine / "data/maps/JubilifeCity/map.json").read_bytes()).hexdigest(),
              "engine/" + layout["blockdata_filepath"]: hashlib.sha256(jub_raw).hexdigest(),
              **{f"canalave-west/{p}": hashlib.sha256((CANALAVE / p).read_bytes()).hexdigest()
                 for p in ("staged/Route218_East/map.json", "staged/Route218_East/averon-map.bin", "source-receipt.json")}}
    return jub, gate, jub_blocks, gate_blocks, hashes


def write(engine, out):
    jub, gate, jb, gb, hashes = build(engine)
    st = pathlib.Path(out) / "staged"
    for name, hdr, blocks in (("JubilifeCity", jub, jb), ("Route218_East", gate, gb)):
        d = st / f"{name}-dev-overlay"
        d.mkdir(parents=True, exist_ok=True)
        (d / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (d / "map.bin").write_bytes(struct.pack("<%dH" % len(blocks), *blocks))
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "inputs_sha256": hashes}
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(write(a.engine, a.out)["status"])
