#!/usr/bin/env python3
"""Neutral building shells (W12) for staged Sinnoh maps whose animated doors have no warp (OFF-ENGINE staging).

For each listed map (Codex's merged staging, read-only), every MB_ANIMATED_DOOR cell without a warp is found from the
family's own attribute bank, and a DEV-only overlay of that map's map.json appends one warp per door into a neutral
LAYOUT_HOUSE1 shell (unchanged stock layout; no NPCs, services, gym, contest or story). Map data and the source files
are not modified. Celestic and Mt. Coronet are excluded (active Codex work); Canalave, Pastoria and Hearthome are
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


def closed_doors(engine, family, name):
    fam = SINNOH / family / "outdoor-family"
    pa = (fam / "primary-attributes.bin").read_bytes()
    sa = (fam / "secondary-attributes.bin").read_bytes()
    pa += b"\0" * (1024 - len(pa))
    attrs = struct.unpack("<%dH" % ((len(pa) + len(sa)) // 2), pa + sa)
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
                 and (i % width, i // width) not in warps and (name, (i % width, i // width)) not in EXCLUDE]


def build(engine):
    engine = pathlib.Path(engine)
    overlays, shells = {}, {}
    for family, name, prefix, music in TARGETS:
        hdr, doors = closed_doors(engine, family, name)
        assert doors, name
        for k, (x, y) in enumerate(doors, 1):
            i = len(hdr["warp_events"])
            shell = f"{name}_House{k}"
            mid = f"{prefix}_HOUSE{k}"
            hdr["warp_events"].append({"x": x, "y": y, "elevation": 0, "dest_map": mid, "dest_warp_id": "0"})
            shells[shell] = w1.header(mid, shell, "LAYOUT_HOUSE1", music, "MAP_TYPE_INDOOR",
                                      [(3, 8, prefix, i), (4, 8, prefix, i)])
        overlays[name] = hdr
    return overlays, shells


def write(engine, out):
    overlays, shells = build(engine)
    st = pathlib.Path(out) / "staged"
    for name, hdr in overlays.items():
        (st / f"{name}-dev-overlay").mkdir(parents=True, exist_ok=True)
        (st / f"{name}-dev-overlay/map.json").write_text(json.dumps(hdr, indent=2) + "\n")
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
