#!/usr/bin/env python3
"""Eterna Forest south tunnel (W23, C15): production Route 205 South <-> Codex's staged Eterna Forest, as the donor has it.

OFF-ENGINE staging. In the donor (LiderMorti00/Sinnoh-pokeemerald-expansion @ 38228bb5), Route 205 South's tunnel
(x 13-16, rows 9-13) warps (14, 12)/(15, 12) straight into Eterna Forest's south mouth (16, 80)/(17, 80), and its
house door (21, 22) leads to MAP_ROUTE205_HOUSE. Production Route 205 South sealed the tunnel with tree halves
(route205-donor/build_route205.py: same elevation bits, collision forced solid) and dropped all three warps; Codex's
staged forest closed its mouth (collision 1, forest-chateau source-receipt closure_changes). This reopens both:
- Route205_South-dev-overlay: the three donor warps, appended in donor order (tunnel 0/1 -> forest, door -> house);
  a derived copy of its map.bin redraws the tunnel with floaroma-donor's Meadow tunnel recipe (same 2-wide shape and
  tree-half phase): tree halves, two canopy ends, grass floor. Only the donor's four floor cells are walkable again:
  (14-15, 12) at elevation 0 holding the warps, (14-15, 13) at elevation 3 below them. Elevations are unchanged.
  The floor has no arrow behaviour, so (as in the Meadow tunnel) a coord trigger on each warp cell takes it; the
  overlay's portal-script.inc holds their two warp scripts.
- EternaForest-dev-overlay: the mouth's two warps back (16 -> tunnel 0, 17 -> tunnel 1) and a derived map.bin
  clearing exactly those two cells' collision (the source had none).
- Route205_South_House (new): a neutral LAYOUT_HOUSE1 shell behind the house door.
Not reopened: the forest's east exit (70, 26-27) to Route 205 North's gatehouse (43-46, 9-12), whose donor building
art has no Averon equivalent yet.

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
ROUTE_WIDTH, ROUTE_HEIGHT = 32, 96
MOUTH = [(16, 80), (17, 80)]
TUNNEL_WARPS = [(14, 12), (15, 12)]
HOUSE_DOOR = (21, 22)
HOUSE, HOUSE_ID = "Route205_South_House", "MAP_ROUTE205_SOUTH_HOUSE"
# floaroma-donor's Meadow tunnel recipe (its x 3-6, rows 0-3) on this tunnel's x 13-16, rows 10-13 (same phase);
# row 9 keeps the plain tree halves the seal put there.
TUNNEL_ART = {(13, 10): 471, (14, 10): 470, (15, 10): 471, (16, 10): 470,
              (13, 11): 479, (14, 11): 486, (15, 11): 487, (16, 11): 478,
              (13, 12): 471, (14, 12): 1, (15, 12): 1, (16, 12): 470,
              (13, 13): 487, (14, 13): 1, (15, 13): 1, (16, 13): 486}
FLOOR = {(14, 12): 0, (15, 12): 0, (14, 13): 3, (15, 13): 3}       # donor's walkable cells -> elevation


def tree_half(x, y):
    """route205-donor's seal: Averon General tree halves, left halves at even x."""
    left = x % 2 == 0
    return (470 if left else 471) if y % 2 == 0 else (478 if left else 479)


def behaviours(engine):
    return re.findall(r"^\s*(MB_\w+)", (engine / "include/constants/metatile_behaviors.h").read_text(), re.M)


def route_inputs(engine):
    layouts = json.loads((engine / "data/layouts/layouts.json").read_text())["layouts"]
    layout = next(l for l in layouts if l.get("id") == "LAYOUT_ROUTE205_SOUTH")
    assert (layout["width"], layout["height"]) == (ROUTE_WIDTH, ROUTE_HEIGHT)
    raw = {"data/maps/Route205_South/map.json": (engine / "data/maps/Route205_South/map.json").read_bytes(),
           layout["blockdata_filepath"]: (engine / layout["blockdata_filepath"]).read_bytes()}
    cells = list(struct.unpack("<%dH" % (ROUTE_WIDTH * ROUTE_HEIGHT), raw[layout["blockdata_filepath"]]))
    hashes = {f"engine/{p}": hashlib.sha256(b).hexdigest() for p, b in raw.items()}
    return json.loads(raw["data/maps/Route205_South/map.json"]), cells, hashes


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
    route, route_cells, hashes = route_inputs(engine)
    forest, forest_cells, attrs, forest_hashes = forest_inputs()
    hashes.update(forest_hashes)
    assert route["warp_events"] == [], route["warp_events"]
    assert all((w["x"], w["y"]) not in MOUTH for w in forest["warp_events"])
    for y in range(9, 14):                              # the tunnel is still exactly the production seal
        for x in range(13, 17):
            v = route_cells[y * ROUTE_WIDTH + x]
            assert v & 1023 == tree_half(x, y) and (v >> 10) & 3 == 1, (x, y, hex(v))
            if (x, y) in FLOOR:
                assert v >> 12 == FLOOR[(x, y)], (x, y, hex(v))
    for x, y in MOUTH:                                  # Codex's closed south arrows below a walkable path
        v = forest_cells[y * FOREST_WIDTH + x]
        assert names[attrs[v & 1023] & 0xFF] == "MB_SOUTH_ARROW_WARP" and v & 0xC00, (x, y)
        assert not forest_cells[(y - 1) * FOREST_WIDTH + x] & 0xC00, (x, y)
    mouth = len(forest["warp_events"])
    route["warp_events"] = [{"x": x, "y": y, "elevation": 0, "dest_map": "MAP_ETERNA_FOREST",
                             "dest_warp_id": str(mouth + i)} for i, (x, y) in enumerate(TUNNEL_WARPS)]
    route["warp_events"].append({"x": HOUSE_DOOR[0], "y": HOUSE_DOOR[1], "elevation": 0, "dest_map": HOUSE_ID,
                                 "dest_warp_id": "0"})
    # The tunnel floor is plain grass (no arrow behaviour), so, as in floaroma-donor's Meadow tunnel, a coord trigger
    # on each warp cell takes it (portal-script.inc below).
    route["coord_events"] = route.get("coord_events", []) + [
        {"type": "trigger", "x": x, "y": y, "elevation": 0, "var": "VAR_TEMP_1", "var_value": "0",
         "script": f"Route205_South_EventScript_ToForest{i}"} for i, (x, y) in enumerate(TUNNEL_WARPS)]
    for i, (x, y) in enumerate(MOUTH):
        forest["warp_events"].append({"x": x, "y": y, "elevation": 0, "dest_map": "MAP_ROUTE205_SOUTH",
                                      "dest_warp_id": str(i)})
    house = w1.header(HOUSE_ID, HOUSE, "LAYOUT_HOUSE1", route["music"], "MAP_TYPE_INDOOR",
                      [(3, 8, "MAP_ROUTE205_SOUTH", 2), (4, 8, "MAP_ROUTE205_SOUTH", 2)])
    route_blocks = list(route_cells)
    for (x, y), mid in TUNNEL_ART.items():
        v = route_cells[y * ROUTE_WIDTH + x]
        route_blocks[y * ROUTE_WIDTH + x] = (v & 0xF000) | (0 if (x, y) in FLOOR else 1 << 10) | mid
    forest_blocks = list(forest_cells)
    for x, y in MOUTH:
        forest_blocks[y * FOREST_WIDTH + x] &= ~0xC00
    return route, forest, house, route_blocks, forest_blocks, hashes


def check(route, forest, house):
    """Every warp lands on a warp that leads back to the map it came from."""
    headers = {h["id"]: h for h in (route, forest, house)}
    for mid, h in headers.items():
        for w in h["warp_events"]:
            if w["dest_map"] in headers:
                back = headers[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
                assert back["dest_map"] == mid, (mid, w, back)
    return True


def portal_script(route):
    """The tunnel triggers' scripts, appended to production Route 205 South's scripts.inc in the DEV scene."""
    return "".join(f"\n{c['script']}::\n\twarp MAP_ETERNA_FOREST, {route['warp_events'][i]['dest_warp_id']}\n"
                   "\twaitstate\n\tend\n" for i, c in enumerate(route["coord_events"][-len(TUNNEL_WARPS):]))


def write(engine, out):
    route, forest, house, route_blocks, forest_blocks, hashes = build(engine)
    check(route, forest, house)
    st = pathlib.Path(out) / "staged"
    for name, hdr, blocks in (("Route205_South-dev-overlay", route, route_blocks),
                              ("EternaForest-dev-overlay", forest, forest_blocks), (HOUSE, house, None)):
        (st / name).mkdir(parents=True, exist_ok=True)
        (st / name / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        if blocks:
            (st / name / "map.bin").write_bytes(struct.pack("<%dH" % len(blocks), *blocks))
    (st / HOUSE / "scripts.inc").write_text(w1.scripts(HOUSE))
    (st / "Route205_South-dev-overlay" / "portal-script.inc").write_text(portal_script(route))
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "maps": [HOUSE],
               "overlays": ["EternaForest", "Route205_South"], "inputs_sha256": hashes}
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(write(a.engine, a.out)["status"])
