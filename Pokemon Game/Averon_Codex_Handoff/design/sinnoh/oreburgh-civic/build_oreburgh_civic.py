#!/usr/bin/env python3
"""Oreburgh civic shells (W21, C14): interiors behind the warp-less doors of Codex's staged Oreburgh City.

OFF-ENGINE staging. Codex's city (oreburgh-donor/city-family map.bin and banks, the oreburgh-connected recipe's
header) is read only. A DEV-only overlay of the city's map.json appends one warp per closed door; the new maps reuse
stock Averon interiors unchanged, each stair graph copied with its floors renamed (W12's civic()):
- Pokemon Center (51, 22): stock Center 1F. Mart (31, 13): stock Mart.
- The gold museum's two entrances, (54, 14) and (62, 12): Lilycove Museum 1F/2F, one street mat each.
  (54, 14) is a non-animated door drawn with collision 1, which the engine only takes when the player steps onto it,
  so it could never open: a derived copy of the city's map.bin (overlay map.bin) clears that one cell's collision.
- The condo (40, 19) and the five houses: neutral LAYOUT_HOUSE1 shells.
Closed on purpose: the Gym (30, 22); a gym's interior is design content, not a neutral shell.

No NPCs, services, items, encounters, story or sections (MAPSEC_PENDING_OWNER). Codex's files are not modified.

  build_oreburgh_civic.py --engine ENGINE --out DIR
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


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


w12 = load("w12", SINNOH / "city-shells/build_city_shells.py")
w1 = w12.w1
FAMILY = SINNOH / "oreburgh-donor/city-family"
RECIPE = SINNOH / "oreburgh-connected/current-recipe.json"
CITY, PREFIX, WIDTH, MUSIC = "OreburghCity", "MAP_OREBURGH_CITY", 70, "MUS_RUSTBORO"
CLOSED = {(30, 22): "Gym: a gym's interior is design content (layout, puzzle, leader), not a neutral shell"}
UNBLOCK = [(54, 14)]                                    # non-animated door drawn with collision 1
# doors (one per street mat, in mat order) -> floors (new name, stock map)
CIVIC = [([(51, 22)], [("OreburghCity_PokemonCenter_1F", "OldaleTown_PokemonCenter_1F")]),
         ([(31, 13)], [("OreburghCity_Mart", "OldaleTown_Mart")]),
         ([(54, 14), (62, 12)], [("OreburghCity_Museum_1F", "LilycoveCity_LilycoveMuseum_1F"),
                                 ("OreburghCity_Museum_2F", "LilycoveCity_LilycoveMuseum_2F")])]
CONDO = (40, 19)


def inputs():
    """Codex's staged city: header (recipe), blockdata and the family's attribute banks, with their hashes."""
    raw = {p: (SINNOH / p).read_bytes() for p in (
        "oreburgh-connected/current-recipe.json", "oreburgh-donor/city-family/OreburghCity/map.bin",
        "oreburgh-donor/city-family/banks/primary/metatile_attributes.bin",
        "oreburgh-donor/city-family/banks/secondary/metatile_attributes.bin")}
    hdr = json.loads(raw["oreburgh-connected/current-recipe.json"])["source_headers"][CITY]
    blob = raw["oreburgh-donor/city-family/OreburghCity/map.bin"]
    cells = list(struct.unpack("<%dH" % (len(blob) // 2), blob))
    assert len(cells) % WIDTH == 0 and len(cells) // WIDTH == 59, len(cells)
    pa = raw["oreburgh-donor/city-family/banks/primary/metatile_attributes.bin"]
    sa = raw["oreburgh-donor/city-family/banks/secondary/metatile_attributes.bin"]
    pa += b"\0" * (1024 - len(pa))
    attrs = struct.unpack("<%dH" % ((len(pa) + len(sa)) // 2), pa + sa)
    return hdr, cells, attrs, {p: hashlib.sha256(b).hexdigest() for p, b in sorted(raw.items())}


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
    doors = closed_doors(engine, hdr, cells, attrs)
    planned = sorted([d for ds, _ in CIVIC for d in ds] + [CONDO] + list(CLOSED), key=lambda d: (d[1], d[0]))
    houses = [d for d in doors if d not in planned]
    assert len(houses) == 5 and all(names[attrs[cells[y * WIDTH + x] & 1023] & 0xFF] == "MB_ANIMATED_DOOR"
                                    for x, y in houses), houses
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
            h["music"] = MUSIC
        maps.update(built)
    shells = [("OreburghCity_Condo", CONDO)] + [(f"OreburghCity_House{k}", d) for k, d in enumerate(houses, 1)]
    for name, door in shells:
        hdr["warp_events"][index[door]]["dest_map"] = w12.const(name)
        maps[name] = w1.header(w12.const(name), name, "LAYOUT_HOUSE1", MUSIC, "MAP_TYPE_INDOOR",
                               [(3, 8, PREFIX, index[door]), (4, 8, PREFIX, index[door])])
    blocks = list(cells)
    for x, y in UNBLOCK:
        v = cells[y * WIDTH + x]
        assert names[attrs[v & 1023] & 0xFF] == "MB_NON_ANIMATED_DOOR" and v & 0xC00, (x, y)
        blocks[y * WIDTH + x] = v & ~0xC00
    for h in maps.values():
        assert h["layout"] in {l["id"] for l in json.loads((engine / "data/layouts/layouts.json").read_text())["layouts"]}
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
