#!/usr/bin/env python3
"""Neutral building shells (W12) for staged Sinnoh maps whose animated doors have no warp (OFF-ENGINE staging).

For each listed map (Codex's merged staging, read-only), every MB_ANIMATED_DOOR cell without a warp is found from the
family's own attribute bank, and a DEV-only overlay of that map's map.json appends one warp per door into a neutral
LAYOUT_HOUSE1 shell (unchanged stock layout; no NPCs, services, gym, contest or story). Codex's files are not modified.

Civic buildings (C7) get stock multi-room interiors instead, each stair graph copied with its floors renamed and any
warp leaving the building other than the street mats (elevators, a Center's 2F) dropped:
Veilstone's Pokemon Center (stock Center 1F), the north-east block's middle door (Stern's Shipyard 1F/2F as a
warehouse) and the north-west block, whose door is drawn as a closed picture (529): a derived copy of Veilstone's
map.bin puts the bank's animated door (533, copied from the north-east door, same 525/528 surroundings) there, and it
opens onto Lilycove's department store 1F-5F and rooftop by the stairs. Solaceon's west house is drawn the same way
(picture 593); it gets the family's door from Route 210 South's house (identical 528/528/519 surroundings) and a
plain shell. Celestic and Mt. Coronet are excluded (active Codex work); Canalave, Pastoria and Hearthome are
handled by W1, W10 and W11.

  build_city_shells.py --engine ENGINE --out DIR
"""
import argparse
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
# Doors left closed: their doorstep is a sealed pocket (static audit on the eastern-loop scene: reaches no exit).
EXCLUDE = {("Route213", (74, 4)): "doorstep (74, 5) is on a rock-walled plateau with no way in"}
# Closed door pictures (solid, non-door) -> the family's animated door cell with the same left/right/above pieces.
# Solaceon's (11, 11) picture (593) has no such door on its own map; Route 210 South's house door matches exactly.
# Not opened: Veilstone's (43, 67) picture is on the map's bottom row, so it has no doorstep to arrive on.
OPEN = {"VeilstoneCity": {(18, 10): ("VeilstoneCity", (41, 14))},
        "SolaceonTown": {(11, 11): ("Route210_South", (30, 47))}}
CIVIC = {("VeilstoneCity", (41, 36)): [("VeilstoneCity_PokemonCenter_1F", "OldaleTown_PokemonCenter_1F")],
         ("VeilstoneCity", (41, 14)): [("VeilstoneCity_Warehouse_1F", "SlateportCity_SternsShipyard_1F"),
                                       ("VeilstoneCity_Warehouse_2F", "SlateportCity_SternsShipyard_2F")],
         ("VeilstoneCity", (18, 10)): [(f"VeilstoneCity_DepartmentStore_{f}", f"LilycoveCity_DepartmentStore_{f}")
                                       for f in ("1F", "2F", "3F", "4F", "5F")]
                                      + [("VeilstoneCity_DepartmentStore_Rooftop", "LilycoveCity_DepartmentStoreRooftop")]}
TARGETS = [  # family folder, staged map, map constant prefix, music
    ("eastern-loop", "VeilstoneCity", "MAP_VEILSTONE_CITY", "MUS_ROUTE110"),
    ("eastern-loop", "Route213", "MAP_ROUTE213", "MUS_ROUTE110"),
    ("eastern-loop", "ValorLakefront", "MAP_VALOR_LAKEFRONT", "MUS_ROUTE110"),
    ("eastern-loop", "Route212_South", "MAP_ROUTE212_SOUTH", "MUS_ROUTE110"),
    ("hearthome-solaceon", "SolaceonTown", "MAP_SOLACEON_TOWN", "MUS_ROUTE110"),
    ("hearthome-solaceon", "Route208", "MAP_ROUTE208", "MUS_ROUTE110"),
    ("hearthome-solaceon", "Route210_South", "MAP_ROUTE210_SOUTH", "MUS_ROUTE110"),
]


def behaviours(engine):
    return re.findall(r"^\s*(MB_\w+)", (engine / "include/constants/metatile_behaviors.h").read_text(), re.M)


def const(name):
    return "MAP_" + re.sub(r"(?<=[a-z])(?=[A-Z])", "_", name).upper()


def map_bin(family, name):
    d = SINNOH / family / "staged" / name
    raw = (d / "averon-map.bin").read_bytes()
    width = struct.unpack(">I", (d / "averon.png").read_bytes()[16:20])[0] // 16
    return width, list(struct.unpack("<%dH" % (len(raw) // 2), raw))


def opened(engine, family, name):
    """Derived blockdata with OPEN's door pictures replaced by animated door cells, or None."""
    if name not in OPEN:
        return None
    width, cells = map_bin(family, name)
    attrs, names = attributes(family), behaviours(engine)
    out = list(cells)
    for (x, y), (donor, (sx, sy)) in OPEN[name].items():
        dwidth, dcells = map_bin(family, donor)
        door, picture = dcells[sy * dwidth + sx], cells[y * width + x]
        assert names[attrs[door & 1023] & 0xFF] == "MB_ANIMATED_DOOR", (donor, sx, sy)
        assert picture & 0xC00 and "DOOR" not in names[attrs[picture & 1023] & 0xFF], (name, x, y)
        assert not cells[(y + 1) * width + x] & 0xC00, (name, x, y)       # a walkable doorstep below
        for dx, dy in ((-1, 0), (1, 0), (0, -1)):          # same surroundings as the copied door
            assert cells[(y + dy) * width + x + dx] & 1023 == dcells[(sy + dy) * dwidth + sx + dx] & 1023, (name, x, y)
        out[y * width + x] = door
    return out


def attributes(family):
    fam = SINNOH / family / "outdoor-family"
    pa = (fam / "primary-attributes.bin").read_bytes()
    sa = (fam / "secondary-attributes.bin").read_bytes()
    pa += b"\0" * (1024 - len(pa))
    return struct.unpack("<%dH" % ((len(pa) + len(sa)) // 2), pa + sa)


def civic(engine, floors, prefix, door_warps):
    """Stock building floors renamed; street mats -> door_warps (one per mat, in order); other exits dropped."""
    srcs = {n: json.loads((engine / f"data/maps/{s}/map.json").read_text()) for n, s in floors}
    stock_ids = {src["id"]: n for n, src in srcs.items()}
    city = const(floors[0][1].split("_")[0])
    keep = {}
    for n, src in srcs.items():
        kept = [i for i, w in enumerate(src["warp_events"]) if w["dest_map"] in stock_ids or (n == floors[0][0]
                                                                                           and w["dest_map"] == city)]
        keep[n] = {old: new for new, old in enumerate(kept)}
    out, mat = {}, 0
    for n, src in srcs.items():
        warps = []
        for i in keep[n]:
            w = src["warp_events"][i]
            if w["dest_map"] == city:
                warps.append((w["x"], w["y"], prefix, door_warps[min(mat, len(door_warps) - 1)]))
                mat += 1
            else:
                dest = stock_ids[w["dest_map"]]
                warps.append((w["x"], w["y"], const(dest), keep[dest][int(w["dest_warp_id"])]))
        out[n] = w1.header(const(n), n, src["layout"], "MUS_ROUTE110", "MAP_TYPE_INDOOR", warps)
    assert mat >= 1
    return out


def closed_doors(engine, family, name):
    attrs = attributes(family)
    names = behaviours(engine)
    d = SINNOH / family / "staged" / name
    hdr = json.loads((d / "map.json").read_text())
    raw = (d / "averon-map.bin").read_bytes()
    cells = struct.unpack("<%dH" % (len(raw) // 2), raw)
    width = struct.unpack(">I", (d / "averon.png").read_bytes()[16:20])[0] // 16
    assert width * (len(cells) // width) == len(cells)
    warps = {(w["x"], w["y"]) for w in hdr["warp_events"]}
    return hdr, [(i % width, i // width) for i, v in enumerate(cells)
                 if (v & 1023) < len(attrs) and names[attrs[v & 1023] & 0xFF] == "MB_ANIMATED_DOOR"
                 and (i % width, i // width) not in warps and (name, (i % width, i // width)) not in EXCLUDE] \
        + sorted(OPEN.get(name, {}))


def build(engine):
    engine = pathlib.Path(engine)
    overlays, shells = {}, {}
    for family, name, prefix, music in TARGETS:
        hdr, doors = closed_doors(engine, family, name)
        assert doors, name
        k = 0
        for x, y in doors:
            i = len(hdr["warp_events"])
            if (name, (x, y)) in CIVIC:
                floors = CIVIC[(name, (x, y))]
                shells.update(civic(engine, floors, prefix, [i]))
                hdr["warp_events"].append({"x": x, "y": y, "elevation": 0, "dest_map": const(floors[0][0]),
                                           "dest_warp_id": "0"})
                continue
            k += 1
            shell = f"{name}_House{k}"
            mid = f"{prefix}_HOUSE{k}"
            hdr["warp_events"].append({"x": x, "y": y, "elevation": 0, "dest_map": mid, "dest_warp_id": "0"})
            shells[shell] = w1.header(mid, shell, "LAYOUT_HOUSE1", music, "MAP_TYPE_INDOOR",
                                      [(3, 8, prefix, i), (4, 8, prefix, i)])
        overlays[name] = hdr
    return overlays, shells, {n: opened(engine, f, n) for f, n, _, _ in TARGETS if n in OPEN}


def write(engine, out):
    overlays, shells, bins = build(engine)
    st = pathlib.Path(out) / "staged"
    for name, hdr in overlays.items():
        (st / f"{name}-dev-overlay").mkdir(parents=True, exist_ok=True)
        (st / f"{name}-dev-overlay/map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        if name in bins:
            (st / f"{name}-dev-overlay/map.bin").write_bytes(struct.pack("<%dH" % len(bins[name]), *bins[name]))
    for name, hdr in shells.items():
        (st / name).mkdir(parents=True, exist_ok=True)
        (st / name / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (st / name / "scripts.inc").write_text(w1.scripts(name))
    return {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "overlays": list(overlays), "shells": len(shells)}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(json.dumps(write(a.engine, a.out), indent=2))
