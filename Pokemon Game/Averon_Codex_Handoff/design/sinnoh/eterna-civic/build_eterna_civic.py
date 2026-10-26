#!/usr/bin/env python3
"""Eterna civic shells (W22, C40): interiors behind the warp-less doors of Codex's staged Eterna City.

OFF-ENGINE staging. Codex's city (eterna-cycle/staged/EternaCity and the city-family attribute banks) is read only.
A DEV-only overlay of the city's map.json appends one warp per closed door; the new maps reuse stock Averon interiors
unchanged, each stair graph copied with its floors renamed (W12's civic()):
- Pokemon Center (16, 17): stock Center 1F. Mart (19, 33): stock Mart.
- The central hall's double door (19-20, 25): a LAYOUT_HOUSE1 shell, one street mat per door. Both cells are
  non-animated doors drawn with collision 1, which the engine only takes when the player steps onto them, so they
  could never open: a derived copy of the city's map.bin (overlay map.bin) clears those two cells' collision.
- The six other doors: neutral LAYOUT_HOUSE1 shells.
Closed on purpose: the Gym (22, 44); a gym's interior is design content, not a neutral shell.

No NPCs, services, items, encounters, story or sections (MAPSEC_PENDING_OWNER). Codex's files are not modified.

  build_eterna_civic.py --engine ENGINE --out DIR
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
spec = importlib.util.spec_from_file_location("w12", SINNOH / "city-shells/build_city_shells.py")
w12 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w12)
w1 = w12.w1
FAMILY = SINNOH / "eterna-cycle"
CITY, PREFIX, WIDTH, HEIGHT = "EternaCity", "MAP_ETERNA_CITY", 60, 55
CLOSED = {(22, 44): "Gym: a gym's interior is design content (layout, puzzle, leader), not a neutral shell"}
UNBLOCK = [(19, 25), (20, 25)]                          # non-animated double door drawn with collision 1
# doors (one per street mat, in mat order) -> floors (new name, stock map)
CIVIC = [([(16, 17)], [("EternaCity_PokemonCenter_1F", "OldaleTown_PokemonCenter_1F")]),
         ([(19, 33)], [("EternaCity_Mart", "OldaleTown_Mart")])]
HALL = ("EternaCity_Hall", [(19, 25), (20, 25)])


def inputs():
    """Codex's staged city: header, blockdata and the family's attribute banks, with their hashes."""
    raw = {p: (FAMILY / p).read_bytes() for p in (
        "staged/EternaCity/map.json", "staged/EternaCity/averon-map.bin",
        "city-family/primary-attributes.bin", "city-family/secondary-attributes.bin")}
    hdr = json.loads(raw["staged/EternaCity/map.json"])
    blob = raw["staged/EternaCity/averon-map.bin"]
    cells = list(struct.unpack("<%dH" % (len(blob) // 2), blob))
    assert len(cells) == WIDTH * HEIGHT, len(cells)
    pa, sa = raw["city-family/primary-attributes.bin"], raw["city-family/secondary-attributes.bin"]
    pa += b"\0" * (1024 - len(pa))
    attrs = struct.unpack("<%dH" % ((len(pa) + len(sa)) // 2), pa + sa)
    return hdr, cells, attrs, {f"eterna-cycle/{p}": hashlib.sha256(b).hexdigest() for p, b in sorted(raw.items())}


def closed_doors(engine, hdr, cells, attrs):
    """Door cells (animated or non-animated) with no warp, in map order."""
    names = w12.behaviours(engine)
    warps = {(w["x"], w["y"]) for w in hdr["warp_events"]}
    return [(i % WIDTH, i // WIDTH) for i, v in enumerate(cells)
            if names[attrs[v & 1023] & 0xFF] in ("MB_ANIMATED_DOOR", "MB_NON_ANIMATED_DOOR")
            and (i % WIDTH, i // WIDTH) not in warps]


def build(engine):
    engine = pathlib.Path(engine)
    hdr, cells, attrs, hashes = inputs()
    names = w12.behaviours(engine)
    music = hdr["music"]
    doors = closed_doors(engine, hdr, cells, attrs)
    planned = [d for ds, _ in CIVIC for d in ds] + HALL[1] + list(CLOSED)
    houses = [d for d in doors if d not in planned]
    assert set(planned) <= set(doors) and len(houses) == 6, (doors, houses)
    assert all(names[attrs[cells[y * WIDTH + x] & 1023] & 0xFF] == "MB_ANIMATED_DOOR" for x, y in houses), houses
    for x, y in doors:                                          # every door has a walkable doorstep below it
        assert not cells[(y + 1) * WIDTH + x] & 0xC00, (x, y)
    index = {}
    for door in [d for d in doors if d not in CLOSED]:
        index[door] = len(hdr["warp_events"])
        hdr["warp_events"].append({"x": door[0], "y": door[1], "elevation": 0, "dest_map": None, "dest_warp_id": "0"})
    maps = {}
    for street, floors in CIVIC:
        built = w12.civic(engine, floors, PREFIX, [index[d] for d in street])
        for mat, door in enumerate(street):
            w = hdr["warp_events"][index[door]]
            w["dest_map"], w["dest_warp_id"] = w12.const(floors[0][0]), str(mat)
        for h in built.values():
            h["music"] = music
        maps.update(built)
    hall, hall_doors = HALL
    for mat, door in enumerate(hall_doors):
        w = hdr["warp_events"][index[door]]
        w["dest_map"], w["dest_warp_id"] = w12.const(hall), str(mat)
    maps[hall] = w1.header(w12.const(hall), hall, "LAYOUT_HOUSE1", music, "MAP_TYPE_INDOOR",
                           [(3, 8, PREFIX, index[hall_doors[0]]), (4, 8, PREFIX, index[hall_doors[1]])])
    for k, door in enumerate(houses, 1):
        name = f"{CITY}_House{k}"
        hdr["warp_events"][index[door]]["dest_map"] = w12.const(name)
        maps[name] = w1.header(w12.const(name), name, "LAYOUT_HOUSE1", music, "MAP_TYPE_INDOOR",
                               [(3, 8, PREFIX, index[door]), (4, 8, PREFIX, index[door])])
    blocks = list(cells)
    for x, y in UNBLOCK:
        v = cells[y * WIDTH + x]
        assert names[attrs[v & 1023] & 0xFF] == "MB_NON_ANIMATED_DOOR" and v & 0xC00, (x, y)
        blocks[y * WIDTH + x] = v & ~0xC00
    layouts = {l.get("id") for l in json.loads((engine / "data/layouts/layouts.json").read_text())["layouts"]}
    for h in maps.values():
        assert h["layout"] in layouts, h["layout"]
    return hdr, maps, blocks, hashes


def check(hdr, maps):
    """Every warp lands on a warp that leads back to the map it came from."""
    headers = {h["id"]: h for h in maps.values()}
    headers[hdr["id"]] = hdr
    for mid, h in headers.items():
        for w in h["warp_events"]:
            if w["dest_map"] in headers:
                back = headers[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
                assert back["dest_map"] == mid, (mid, w, back)
    return True


def write(engine, out):
    hdr, maps, blocks, hashes = build(engine)
    check(hdr, maps)
    st = pathlib.Path(out) / "staged"
    (st / f"{CITY}-dev-overlay").mkdir(parents=True, exist_ok=True)
    (st / f"{CITY}-dev-overlay/map.json").write_text(json.dumps(hdr, indent=2) + "\n")
    (st / f"{CITY}-dev-overlay/map.bin").write_bytes(struct.pack("<%dH" % len(blocks), *blocks))
    for name, h in maps.items():
        (st / name).mkdir(parents=True, exist_ok=True)
        (st / name / "map.json").write_text(json.dumps(h, indent=2) + "\n")
        (st / name / "scripts.inc").write_text(w1.scripts(name))
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "maps": sorted(maps),
               "closed": {f"{x},{y}": why for (x, y), why in CLOSED.items()}, "inputs_sha256": hashes}
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(write(a.engine, a.out)["status"])
