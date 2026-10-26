#!/usr/bin/env python3
"""West integrated packet A (C36): install W14's Jubilife interiors and W16's Oreburgh Gate B1F into the engine.

PRODUCTION integration of already-staged Claude geography, appended after the existing 19 Sinnoh slots:
- W14 (jubilife-shells): Global Terminal 1F/2F, TV 1F/2F, Pokétch Company 1F/2F/3F, Condo 1/2 behind the seven
  warp-less doors of production Jubilife; Jubilife gains the seven warps and its two halls' four non-animated door
  cells the walkable 693 word (collision 1 -> 0, nothing else).
- W16 (oreburgh-gate-b1f): Oreburgh Gate B1F under the dead-end north alcove of production Gate 1F (one ladder cell,
  one appended warp).

Identities: map slots 19-28 appended to gMapGroup_Sinnoh (0-18 untouched); layouts reuse stock interiors except one
new layout (LAYOUT_OREBURGH_GATE_B1F, appended); sections are the existing MAPSEC_JUBILIFE_CITY and
MAPSEC_OREBURGH_GATE. No new section/healer/flag/var/save identity, services, NPCs, encounters or story.
Headers follow production conventions: interiors copy JubilifeCity_Mart's header fields with Jubilife's music,
B1F copies Gate 1F's.

The builders read the pinned pre-integration snapshot in base/ (the four production files this packet changes), so
the staging stays reproducible after integration.

  install_packet_a.py --engine ENGINE           write the engine files (refuses on a tree already installed)
  install_packet_a.py --engine ENGINE --check   verify the engine equals a fresh install (exit 1 otherwise)
"""
import argparse
import importlib.util
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
BASE = HERE / "base"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


w14 = load("w14", SINNOH / "jubilife-shells/build_jubilife_shells.py")
w16 = load("w16", SINNOH / "oreburgh-gate-b1f/build_oreburgh_gate_b1f.py")
PRIOR_SLOTS = 19
REGISTRY = "test/data/averon_map_registry_slots.inc"
HEADER_FIELDS = ("music", "region", "region_map_section", "weather", "map_type", "allow_cycling", "allow_escaping",
                 "allow_running", "show_map_name", "requires_flash", "battle_scene")


def production_header(staged, template, music=None):
    """The staged header's identity, layout and warps on a production template's fields (no events)."""
    hdr = {k: staged[k] for k in ("id", "name", "layout")}
    for k in HEADER_FIELDS:
        hdr[k] = template[k]
    if music:
        hdr["music"] = music
    hdr.update(connections=[], object_events=[], coord_events=[], bg_events=[], warp_events=staged["warp_events"])
    return hdr


def plan(engine):
    """Every engine file this packet writes, as {relative path: bytes}, computed from the base snapshot."""
    engine = pathlib.Path(engine)
    base = lambda rel: (BASE / rel).read_bytes()
    _, maps, jub, jub_blocks = w14.build(engine)
    _, gate, gate_blocks, b1f, cv = w16.build(engine)
    mart = json.loads((engine / "data/maps/JubilifeCity_Mart/map.json").read_text())
    gate_src = json.loads(base("data/maps/OreburghGate_1F/map.json"))
    city_music = json.loads(base("data/maps/JubilifeCity/map.json"))["music"]
    files = {}
    names = list(maps) + ["OreburghGate_B1F"]
    for name, staged in maps.items():
        hdr = production_header(staged, mart, city_music)
        files[f"data/maps/{name}/map.json"] = hdr
        files[f"data/maps/{name}/scripts.inc"] = w14.w1.scripts(name).encode()
    files["data/maps/OreburghGate_B1F/map.json"] = production_header(b1f, gate_src)
    files["data/maps/OreburghGate_B1F/scripts.inc"] = w16.w1.scripts("OreburghGate_B1F").encode()
    files["data/maps/JubilifeCity/map.json"] = jub
    files["data/maps/OreburghGate_1F/map.json"] = gate
    files["data/layouts/JubilifeCity/map.bin"] = struct.pack("<%dH" % len(jub_blocks), *jub_blocks)
    files["data/layouts/OreburghGate_1F/map.bin"] = struct.pack("<%dH" % len(gate_blocks), *gate_blocks)
    files["data/layouts/OreburghGate_B1F/map.bin"] = struct.pack("<%dH" % len(cv.cells), *cv.cells)
    files["data/layouts/OreburghGate_B1F/border.bin"] = struct.pack("<4H", *[cv.k[529]] * 4)
    for hdr in [files[f"data/maps/{n}/map.json"] for n in names]:
        assert hdr["region_map_section"] in ("MAPSEC_JUBILIFE_CITY", "MAPSEC_OREBURGH_GATE"), hdr["id"]
    return names, files, cv


def appended(engine, names, cv):
    """map_groups.json, layouts.json, event_scripts.s and the registry slot list with this packet appended."""
    engine = pathlib.Path(engine)
    groups = json.loads((engine / "data/maps/map_groups.json").read_text())
    layouts = json.loads((engine / "data/layouts/layouts.json").read_text())
    scripts = (engine / "data/event_scripts.s").read_text()
    registry = (engine / REGISTRY).read_text()
    sinnoh = groups["gMapGroup_Sinnoh"]
    assert len(sinnoh) == PRIOR_SLOTS, len(sinnoh)
    groups["gMapGroup_Sinnoh"] = sinnoh + names
    layouts["layouts"].append({"id": "LAYOUT_OREBURGH_GATE_B1F", "name": "OreburghGate_B1F_Layout", "width": cv.w,
                               "height": cv.h, "primary_tileset": "gTileset_General",
                               "secondary_tileset": "gTileset_Cave",
                               "border_filepath": "data/layouts/OreburghGate_B1F/border.bin",
                               "blockdata_filepath": "data/layouts/OreburghGate_B1F/map.bin"})
    last = '\t.include "data/maps/Route205_North/scripts.inc"\n'
    assert last in scripts
    scripts = scripts.replace(last, last + "".join(f'\t.include "data/maps/{n}/scripts.inc"\n' for n in names), 1)
    old = f"REGISTRY_GROUP(76, gMapGroup_Sinnoh, {PRIOR_SLOTS}, 1)"
    assert old in registry and registry.endswith("REGISTRY_SLOT(76, 18, MAP_ROUTE205_NORTH, Route205_North, 1)\n")
    registry = registry.replace(old, f"REGISTRY_GROUP(76, gMapGroup_Sinnoh, {PRIOR_SLOTS + len(names)}, 1)")
    for i, n in enumerate(names, PRIOR_SLOTS):
        mid = w14.const(n)
        registry += f"REGISTRY_SLOT(76, {i}, {mid}, {n}, 1)\n"
    return {"data/maps/map_groups.json": groups, "data/layouts/layouts.json": layouts,
            "data/event_scripts.s": scripts.encode(), REGISTRY: registry.encode()}


def encode(value):
    return value if isinstance(value, bytes) else (json.dumps(value, indent=2) + "\n").encode()


def install(engine):
    engine = pathlib.Path(engine)
    groups = json.loads((engine / "data/maps/map_groups.json").read_text())["gMapGroup_Sinnoh"]
    if len(groups) != PRIOR_SLOTS:
        sys.exit(f"refusing: gMapGroup_Sinnoh has {len(groups)} slots, expected {PRIOR_SLOTS} (already installed?)")
    names, files, cv = plan(engine)
    files.update(appended(engine, names, cv))
    for rel, value in files.items():
        (engine / rel).parent.mkdir(parents=True, exist_ok=True)
        (engine / rel).write_bytes(encode(value))
    return names


def check(engine):
    """Recompute the install against the base snapshot and the pre-packet prefixes; compare with the engine."""
    engine = pathlib.Path(engine)
    names, files, cv = plan(engine)
    bad = [rel for rel, value in files.items() if (engine / rel).read_bytes() != encode(value)]
    groups = json.loads((engine / "data/maps/map_groups.json").read_text())["gMapGroup_Sinnoh"]
    if groups[PRIOR_SLOTS:] != names:
        bad.append("data/maps/map_groups.json")
    layouts = json.loads((engine / "data/layouts/layouts.json").read_text())["layouts"]
    if not any(l.get("id") == "LAYOUT_OREBURGH_GATE_B1F" and l["width"] == cv.w and l["height"] == cv.h for l in layouts):
        bad.append("data/layouts/layouts.json")
    scripts = (engine / "data/event_scripts.s").read_text()
    if any(f'\t.include "data/maps/{n}/scripts.inc"\n' not in scripts for n in names):
        bad.append("data/event_scripts.s")
    registry = (engine / REGISTRY).read_text()
    if any(f"REGISTRY_SLOT(76, {i}, {w14.const(n)}, {n}, 1)" not in registry for i, n in enumerate(names, PRIOR_SLOTS)):
        bad.append(REGISTRY)
    return bad


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    if a.check:
        bad = check(a.engine)
        print("OK" if not bad else "MISMATCH: " + ", ".join(bad))
        sys.exit(1 if bad else 0)
    print("installed:", ", ".join(install(a.engine)))
