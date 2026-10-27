#!/usr/bin/env python3
"""Route 212 North mansion (W17, south-east lane): the facade's door opened onto a stock five-room mansion.

OFF-ENGINE staging. Codex's eastern-loop Route212_North (read-only) draws a large mansion facade south of a fenced
garden, at the DS Pokemon Mansion's place. Its door cell (24, 38) is the bank's closed door picture 529 (solid; the
source receipt lists no closure there, so it is solid in the source itself). As W12 did for Veilstone's identical
picture, a DEV-only derived copy of the map.bin puts the same family's animated door there: the word of Veilstone's
north-east door (41, 14), after asserting both cells have the same 528 / 528 / 525 surroundings. A header overlay
appends its warp; nothing else changes.

Inside: Emerald's Cove Lily Motel 1F and 2F (a two-storey guest house), unchanged stock layouts, the stair pair copied
with the floors renamed (W12's civic()); the 1F mats return to the door. (FRLG interiors such as Celadon's
condominiums are not an option: mapjson skips layout_version "frlg" layouts in the Emerald build.)

The fenced garden behind the facade (the DS Trophy Garden) is solid in the source and stays closed: nothing in the
source supports a walkable garden. No NPCs, services, objects, story or sections (MAPSEC_PENDING_OWNER).

  build_route212_mansion.py --engine ENGINE --out DIR
"""
import argparse
import importlib.util
import json
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
spec = importlib.util.spec_from_file_location("w12", SINNOH / "city-shells/build_city_shells.py")
w12 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w12)
FAMILY = "eastern-loop"
DOOR = (24, 38)
DONOR_DOOR = ("VeilstoneCity", (41, 14))
PREFIX = "Route212_North_Mansion"
FLOORS = [(f"{PREFIX}_{f}", f"LilycoveCity_CoveLilyMotel_{f}") for f in ("1F", "2F")]


def surroundings(cells, width, x, y):
    return [cells[(y + dy) * width + x + dx] & 1023 for dx, dy in ((-1, 0), (1, 0), (0, -1))]


def build(engine):
    engine = pathlib.Path(engine)
    hdr = json.loads((SINNOH / FAMILY / "staged/Route212_North/map.json").read_text())
    width, cells = w12.map_bin(FAMILY, "Route212_North")
    vwidth, vcells = w12.map_bin(FAMILY, DONOR_DOOR[0])
    (x, y), (sx, sy) = DOOR, DONOR_DOOR[1]
    assert cells[y * width + x] & 1023 == 529 and cells[y * width + x] & 0xC00, "door picture moved"
    assert vcells[sy * vwidth + sx] & 1023 == 533
    assert surroundings(cells, width, x, y) == surroundings(vcells, vwidth, sx, sy) == [528, 528, 525]
    assert all((w["x"], w["y"]) != DOOR for w in hdr["warp_events"])
    blocks = list(cells)
    blocks[y * width + x] = vcells[sy * vwidth + sx]
    i = len(hdr["warp_events"])
    hdr["warp_events"].append({"x": x, "y": y, "elevation": 0, "dest_map": w12.const(FLOORS[0][0]),
                               "dest_warp_id": "0"})
    rooms = w12.civic(engine, FLOORS, "MAP_ROUTE212_NORTH", [i])
    return hdr, blocks, rooms


def check(hdr, rooms):
    """Every warp lands on a warp leading back to the map it came from."""
    by_id = {h["id"]: h for h in rooms.values()}
    by_id[hdr["id"]] = hdr
    for mid, h in by_id.items():
        for w in h["warp_events"]:
            if w["dest_map"] in by_id:
                assert by_id[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]["dest_map"] == mid, (mid, w)
    return True


def write(engine, out):
    hdr, blocks, rooms = build(engine)
    check(hdr, rooms)
    st = pathlib.Path(out) / "staged"
    d = st / "Route212_North-dev-overlay"
    d.mkdir(parents=True, exist_ok=True)
    (d / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
    (d / "map.bin").write_bytes(struct.pack("<%dH" % len(blocks), *blocks))
    for name, room in rooms.items():
        (st / name).mkdir(parents=True, exist_ok=True)
        (st / name / "map.json").write_text(json.dumps(room, indent=2) + "\n")
        (st / name / "scripts.inc").write_text(w12.w1.scripts(name))
    return {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "rooms": list(rooms)}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(json.dumps(write(a.engine, a.out), indent=2))
