#!/usr/bin/env python3
"""Eterna Forest south gate (W23, C15): production Route 205 South -> gatehouse -> Codex's staged Eterna Forest.

OFF-ENGINE staging. Production Route 205 South draws an animated door (21, 22) with no warp near its north end, where
the forest's entrance building stands; Codex's staged Eterna Forest ends its south path in two south-arrow warp cells
(16-17, 80) that are closed with collision 1 because they had no destination. This joins them:
- Route205_South-dev-overlay: one appended warp, door (21, 22) -> the gate's street mat.
- EternaForest_SouthGate (new): stock LAYOUT_ROUTE114_FOSSIL_MANIACS_HOUSE unchanged. Its two south mats return to
  Route 205 South; its back door (4, 1), a walkable non-animated door, opens north into the forest.
- EternaForest-dev-overlay: two appended warps on (16-17, 80) -> the gate's back door, and a derived copy of the
  forest's map.bin clearing exactly those two cells' collision (same metatile, elevation and behaviour).

Production map data and Codex's files are not modified. No NPCs, services, items, encounters, story or sections
(MAPSEC_PENDING_OWNER).

  build_eterna_forest_gate.py --engine ENGINE --out DIR
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import struct

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
spec = importlib.util.spec_from_file_location("w1", SINNOH / "iron-island/build_iron_island.py")
w1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w1)
FOREST = SINNOH / "forest-chateau"
FOREST_WIDTH, FOREST_HEIGHT = 82, 84
ROUTE_DOOR = (21, 22)
MOUTH = [(16, 80), (17, 80)]
GATE, GATE_ID, GATE_LAYOUT = "EternaForest_SouthGate", "MAP_ETERNA_FOREST_SOUTH_GATE", "LAYOUT_ROUTE114_FOSSIL_MANIACS_HOUSE"
GATE_MATS, GATE_BACK = [(4, 7), (5, 7)], (4, 1)


def behaviours(engine):
    return re.findall(r"^\s*(MB_\w+)", (engine / "include/constants/metatile_behaviors.h").read_text(), re.M)


def forest_inputs():
    raw = {p: (FOREST / p).read_bytes() for p in (
        "staged/EternaForest/map.json", "staged/EternaForest/averon-map.bin",
        "forest-art/primary-attributes.bin", "forest-art/secondary-attributes.bin")}
    blob = raw["staged/EternaForest/averon-map.bin"]
    cells = list(struct.unpack("<%dH" % (len(blob) // 2), blob))
    assert len(cells) == FOREST_WIDTH * FOREST_HEIGHT, len(cells)
    pa, sa = raw["forest-art/primary-attributes.bin"], raw["forest-art/secondary-attributes.bin"]
    pa += b"\0" * (1024 - len(pa))
    attrs = struct.unpack("<%dH" % ((len(pa) + len(sa)) // 2), pa + sa)
    hashes = {f"forest-chateau/{p}": hashlib.sha256(b).hexdigest() for p, b in sorted(raw.items())}
    return json.loads(raw["staged/EternaForest/map.json"]), cells, attrs, hashes


def build(engine):
    engine = pathlib.Path(engine)
    names = behaviours(engine)
    route = json.loads((engine / "data/maps/Route205_South/map.json").read_text())
    stock = json.loads((engine / "data/maps/Route114_FossilManiacsHouse/map.json").read_text())
    assert stock["layout"] == GATE_LAYOUT
    assert [(w["x"], w["y"]) for w in stock["warp_events"]] == GATE_MATS + [GATE_BACK], stock["warp_events"]
    assert all((w["x"], w["y"]) != ROUTE_DOOR for w in route["warp_events"])
    forest, cells, attrs, hashes = forest_inputs()
    assert all((w["x"], w["y"]) not in MOUTH for w in forest["warp_events"])
    for x, y in MOUTH:                     # closed south arrows below a walkable path
        v = cells[y * FOREST_WIDTH + x]
        assert names[attrs[v & 1023] & 0xFF] == "MB_SOUTH_ARROW_WARP" and v & 0xC00, (x, y)
        assert not cells[(y - 1) * FOREST_WIDTH + x] & 0xC00, (x, y)
    door = len(route["warp_events"])
    route["warp_events"].append({"x": ROUTE_DOOR[0], "y": ROUTE_DOOR[1], "elevation": 0, "dest_map": GATE_ID,
                                 "dest_warp_id": "0"})
    mouth = len(forest["warp_events"])
    for x, y in MOUTH:
        forest["warp_events"].append({"x": x, "y": y, "elevation": 0, "dest_map": GATE_ID, "dest_warp_id": "2"})
    gate = w1.header(GATE_ID, GATE, GATE_LAYOUT, route["music"], "MAP_TYPE_INDOOR",
                     [(x, y, "MAP_ROUTE205_SOUTH", door) for x, y in GATE_MATS]
                     + [(GATE_BACK[0], GATE_BACK[1], "MAP_ETERNA_FOREST", mouth)])
    blocks = list(cells)
    for x, y in MOUTH:
        blocks[y * FOREST_WIDTH + x] &= ~0xC00
    hashes["engine/data/maps/Route205_South/map.json"] = hashlib.sha256(
        (engine / "data/maps/Route205_South/map.json").read_bytes()).hexdigest()
    return route, forest, gate, blocks, hashes


def check(route, forest, gate):
    """Every warp lands on a warp that leads back to the map it came from."""
    headers = {h["id"]: h for h in (route, forest, gate)}
    for mid, h in headers.items():
        for w in h["warp_events"]:
            if w["dest_map"] in headers:
                back = headers[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
                assert back["dest_map"] == mid, (mid, w, back)
    return True


def write(engine, out):
    route, forest, gate, blocks, hashes = build(engine)
    check(route, forest, gate)
    st = pathlib.Path(out) / "staged"
    for name, hdr in (("Route205_South-dev-overlay", route), ("EternaForest-dev-overlay", forest), (GATE, gate)):
        (st / name).mkdir(parents=True, exist_ok=True)
        (st / name / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
    (st / "EternaForest-dev-overlay/map.bin").write_bytes(struct.pack("<%dH" % len(blocks), *blocks))
    (st / GATE / "scripts.inc").write_text(w1.scripts(GATE))
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "maps": [GATE],
               "overlays": ["EternaForest", "Route205_South"], "inputs_sha256": hashes}
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(write(a.engine, a.out)["status"])
