#!/usr/bin/env python3
"""Jubilife institutional shells (W14, central lane): neutral interiors behind production Jubilife's closed doors.

OFF-ENGINE staging. Production JubilifeCity draws seven door cells (MB_ANIMATED_DOOR) with no warp. A DEV-only
overlay of its map.json (staged/JubilifeCity-dev-overlay; the engine file is not modified) appends one warp per door
into stock Averon interiors, reused unchanged. Each building's stock stair graph is copied warp for warp with only
the map names changed (as W8's Lost Tower); its street mats return to the Jubilife door they came from.

- Global Terminal: the west hall's double door (19-20, 13), Slateport Oceanic Museum 1F/2F layouts.
- Jubilife TV: the east hall's double door (40-41, 13), Mossdeep Space Center 1F/2F layouts.
- Pokétch Company: the tower's door (55, 16), Rustboro Devon Corp 1F/2F/3F layouts (both street mats lead out).
- Two condos: (16, 49) and (42, 49), LAYOUT_HOUSE1.

Names follow the DS buildings for orientation only: no NPCs, services (GTS, TV, Pokétch), objects, story or
sections (MAPSEC_PENDING_OWNER).

  build_jubilife_shells.py --engine ENGINE --out DIR
"""
import argparse
import importlib.util
import json
import pathlib
import re
import struct

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("w1", HERE.parent / "iron-island/build_iron_island.py")
w1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w1)
MUSIC = "MUS_RUSTBORO"
# name, stock map prefix, floors, Jubilife door cells (one per street mat, in mat order)
BUILDINGS = [("JubilifeCity_GlobalTerminal", "SlateportCity_OceanicMuseum", ["1F", "2F"], [(19, 13), (20, 13)]),
             ("JubilifeCity_TV", "MossdeepCity_SpaceCenter", ["1F", "2F"], [(40, 13), (41, 13)]),
             ("JubilifeCity_PoketchCompany", "RustboroCity_DevonCorp", ["1F", "2F", "3F"], [(55, 16), (55, 16)])]
CONDOS = [("JubilifeCity_Condo1", (16, 49)), ("JubilifeCity_Condo2", (42, 49))]


def const(name):
    """MAP_ constant of a map folder name (FooCity_BarBaz_1F -> MAP_FOO_CITY_BAR_BAZ_1F)."""
    return "MAP_" + re.sub(r"(?<=[a-z])(?=[A-Z])", "_", name).upper()


def closed_doors(eng, hdr):
    """Door cells of production Jubilife with no warp (from its own tilesets' behaviour bytes)."""
    names = re.findall(r"^\s*(MB_\w+)", (eng.root / "include/constants/metatile_behaviors.h").read_text(), re.M)
    pa = eng.file("data/tilesets/primary/general/metatile_attributes.bin")
    sa = eng.file("data/tilesets/secondary/averon_corridor_rustboro/metatile_attributes.bin")
    pa += b"\0" * (1024 - len(pa))
    attrs = struct.unpack("<%dH" % ((len(pa) + len(sa)) // 2), pa + sa)
    width, _, cells = eng.cells("JubilifeCity")
    warps = {(w["x"], w["y"]) for w in hdr["warp_events"]}
    return [(i % width, i // width) for i, v in enumerate(cells)
            if names[attrs[v & 1023] & 0xFF] in ("MB_ANIMATED_DOOR", "MB_NON_ANIMATED_DOOR")
            and (i % width, i // width) not in warps]


def build(engine_root):
    eng = w1.Engine(engine_root)
    jub = json.loads(eng.file("data/maps/JubilifeCity/map.json"))
    assert eng.layouts["JubilifeCity"]["secondary_tileset"] == "gTileset_AveronCorridorRustboro"
    doors = closed_doors(eng, jub)
    planned = sorted({d for _, _, _, ds in BUILDINGS for d in ds} | {d for _, d in CONDOS})
    assert sorted(doors) == planned, (doors, planned)
    maps = {}
    for name, stock, floors, street in BUILDINGS:
        index = {}
        for door in dict.fromkeys(street):
            index[door] = len(jub["warp_events"])
            jub["warp_events"].append({"x": door[0], "y": door[1], "elevation": 0,
                                       "dest_map": const(f"{name}_{floors[0]}"), "dest_warp_id": str(street.index(door))})
        for f in floors:
            src = json.loads(eng.file(f"data/maps/{stock}_{f}/map.json"))
            warps, mat = [], 0
            for w in src["warp_events"]:
                if w["dest_map"].startswith(const(stock) + "_"):
                    dest = w["dest_map"].replace(const(stock), const(name))
                    warps.append((w["x"], w["y"], dest, int(w["dest_warp_id"])))
                else:                                               # a street mat
                    assert f == floors[0], (stock, f, w)
                    warps.append((w["x"], w["y"], "MAP_JUBILIFE_CITY", index[street[mat]]))
                    mat += 1
            assert mat in (0, len(street)), (stock, f, mat)
            maps[f"{name}_{f}"] = w1.header(const(f"{name}_{f}"), f"{name}_{f}", src["layout"], MUSIC, "MAP_TYPE_INDOOR",
                                            warps)
    for name, door in CONDOS:
        i = len(jub["warp_events"])
        jub["warp_events"].append({"x": door[0], "y": door[1], "elevation": 0, "dest_map": const(name), "dest_warp_id": "0"})
        maps[name] = w1.header(const(name), name, "LAYOUT_HOUSE1", MUSIC, "MAP_TYPE_INDOOR",
                               [(3, 8, "MAP_JUBILIFE_CITY", i), (4, 8, "MAP_JUBILIFE_CITY", i)])
    for hdr in maps.values():
        assert hdr["layout"] in eng.layout_ids, hdr["layout"]
    return eng, maps, jub


def check(maps, jub):
    """Every warp lands on a warp that leads back to the map it came from."""
    headers = {h["id"]: h for h in maps.values()}
    headers["MAP_JUBILIFE_CITY"] = jub
    for mid, h in headers.items():
        for w in h["warp_events"]:
            if w["dest_map"] not in headers:
                continue
            back = headers[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
            assert back["dest_map"] == mid, (mid, w, back)
    return True


def write(engine_root, out):
    eng, maps, jub = build(engine_root)
    check(maps, jub)
    st = pathlib.Path(out) / "staged"
    for name, hdr in maps.items():
        (st / name).mkdir(parents=True, exist_ok=True)
        (st / name / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (st / name / "scripts.inc").write_text(w1.scripts(name))
    (st / "JubilifeCity-dev-overlay").mkdir(parents=True, exist_ok=True)
    (st / "JubilifeCity-dev-overlay/map.json").write_text(json.dumps(jub, indent=2) + "\n")
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "maps": sorted(maps),
               "inputs_sha256": dict(sorted(eng.read.items()))}
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(write(a.engine, a.out)["status"])
