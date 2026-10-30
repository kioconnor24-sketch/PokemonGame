#!/usr/bin/env python3
"""Packet E: production Route 208 -> Hearthome -> Route 209 -> Solaceon, Lost Tower and the Solaceon Ruins.

PRODUCTION integration of the 37 maps staged by stage_packet_e.py (PACKET_E_PLAN.md), appended after packet D, with
the owner's section decision recorded in #15 comment 6484040222 (231-238, append-only, REGION_SINNOH).
- Sources come only from the stage's pinned selection (stage_packet_e.check() must be clean): Codex's
  hearthome-solaceon outdoors and gates with their converted metatile banks (production names
  gTileset_AveronCentral{Outdoor,Gate}{Primary,Secondary}, bound to existing General/Rustboro and Building/Shop
  graphics), and Claude's overlays and interiors (stock layouts, or new layouts on stock tilesets).
- The one join packet D left closed is reopened: Route 208 (8,19) door <-> Mt. Coronet 1F South (36,20) arrow, as
  appended warps (Route208 warp 2 <-> South warp 1) so no existing return index moves; each cell gets back exactly
  the donor's walkable word.
- Everything else that leads out of the 37 maps stays closed (Route 212, Route 210 North/215, Maniac Tunnel).
- Route 209 keeps Lost Tower's four trigger warps (VAR_TEMP_1 == 0; no saved state).
Packet D must already be installed: its five maps in gMapGroup_Sinnoh and sections 228-230 as the last entries.
Nothing else of D is assumed. No healer, flag, var, NPC, service, encounter or story.

  install_packet_e.py --engine ENGINE           write the engine files (refuses unless exactly packet D precedes)
  install_packet_e.py --engine ENGINE --check   verify the engine equals a fresh install (exit 1 otherwise)
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
CENTRAL = SINNOH / "hearthome-solaceon"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


stage = load("packet_e_stage", HERE / "stage_packet_e.py")
SLOTS = list(stage.MAPS)
PACKET_D = {"Route206_North", "Route206", "Route206_South", "Route207", "MtCoronet_1F_South"}
LAST_D_SECTION = 230
SECTIONS_NEW = [("MAPSEC_ROUTE_208", 231, "ROUTE 208"), ("MAPSEC_HEARTHOME_CITY", 232, "HEARTHOME CITY"),
                ("MAPSEC_ROUTE_209", 233, "ROUTE 209"), ("MAPSEC_SOLACEON_TOWN", 234, "SOLACEON TOWN"),
                ("MAPSEC_SOLACEON_RUINS", 235, "SOLACEON RUINS"), ("MAPSEC_LOST_TOWER", 236, "LOST TOWER"),
                ("MAPSEC_ROUTE_210", 237, "ROUTE 210"), ("MAPSEC_AMITY_SQUARE", 238, "AMITY SQUARE")]
TILESETS = {"OutdoorPrimary": ("AveronCentralOutdoorPrimary", False, "General", "outdoor-family"),
            "OutdoorSecondary": ("AveronCentralOutdoorSecondary", True, "Rustboro", "outdoor-family"),
            "GatePrimary": ("AveronCentralGatePrimary", False, "Building", "gate-art"),
            "GateSecondary": ("AveronCentralGateSecondary", True, "Shop", "gate-art")}
# Exact stock graphics bindings used by the accepted central source families.
# Do not derive check expectations from a potentially changed installed header.
GRAPHICS_BINDINGS = {
    "General": ("gTilesetTiles_General", "gTilesetPalettes_General", "InitTilesetAnim_General"),
    "Rustboro": ("gTilesetTiles_Rustboro", "gTilesetPalettes_Rustboro", "InitTilesetAnim_Rustboro"),
    "Building": ("gTilesetTiles_InsideBuilding", "gTilesetPalettes_InsideBuilding", "InitTilesetAnim_Building"),
    "Shop": ("gTilesetTiles_Shop", "gTilesetPalettes_Shop", "NULL"),
}
# Route 208 <-> Coronet South: (map, cell, closed word, reopened word, width)
ROUTE208_DOOR = ((8, 19), 0x04A7, 0x00A7, 68)
SOUTH_ARROW = ((36, 20), 0x3604, 0x321A, 42)
SOUTH = "MtCoronet_1F_South"
REGISTRY = "test/data/averon_map_registry_slots.inc"
SECTIONS = "src/data/region_map/region_map_sections.json"
# The exact pre-E production baseline (41 production maps + packet D): see prefix-pins.json.
BASELINE = json.loads((HERE / "prefix-pins.json").read_text())
SECTIONS_THROUGH_227 = 227          # entries covered by sections_through_227_sha256
sha = lambda b: hashlib.sha256(b).hexdigest()


def section_of(name):
    for prefix, sec in (("Route208", 231), ("HearthomeCity", 232), ("Route209", 233), ("SolaceonTown", 234),
                        ("SolaceonRuins", 235), ("LostTower", 236), ("Route210", 237), ("AmitySquare", 238)):
        if name.startswith(prefix):
            return next(i for i, v, _ in SECTIONS_NEW if v == sec)
    raise ValueError("no section for " + name)


def const(name):
    return "MAP_" + re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[0-9])(?=[A-Z][a-z])", "_", name).upper()


def folder(symbol):
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", symbol).lower()


def read_json(path):
    return json.loads(pathlib.Path(path).read_text())


def cells(raw):
    return list(struct.unpack("<%dH" % (len(raw) // 2), raw))


def pack(values):
    return struct.pack("<%dH" % len(values), *values)


def reopen(raw, spec):
    (x, y), closed, opened, width = spec
    values = cells(raw)
    if values[y * width + x] != closed:
        raise ValueError(f"cell {(x, y)} is {values[y * width + x]:#06x}, expected closed {closed:#06x}")
    values[y * width + x] = opened
    return pack(values)


def layout_of(engine, layout_id):
    return next(l for l in read_json(engine / "data/layouts/layouts.json")["layouts"] if l.get("id") == layout_id)


def south_before(engine):
    """Coronet South as packet D installed it: (header, blockdata path, blockdata)."""
    south = read_json(engine / f"data/maps/{SOUTH}/map.json")
    path = layout_of(engine, south["layout"])["blockdata_filepath"]
    return south, path, (engine / path).read_bytes()


def plan(engine, before=None):
    """Every engine file this packet writes or adds, as {relative path: bytes or JSON}, plus the new layouts.
    before: Coronet South's pre-packet (header, path, blockdata); read from the engine when not given."""
    engine = pathlib.Path(engine)
    src = stage.read_sources()
    errors = stage.check(src)
    if errors:
        raise ValueError("packet E stage is not clean: " + "; ".join(errors[:5]))
    hdrs = stage.headers(src)
    stock = {l.get("id") for l in read_json(engine / "data/layouts/layouts.json")["layouts"]}
    out, layouts = {}, []
    # Coronet South (packet D's production map): append the east arrow back to Route 208's appended door.
    south, south_bin, south_raw = before or south_before(engine)
    south = json.loads(json.dumps(south))
    if south["warp_events"] != BASELINE["coronet_south"]["warp_events"]:
        raise ValueError("packet D's Coronet South warps differ from the pinned single Route 207 return")
    route208 = hdrs["Route208"]
    door = dict(x=8, y=19, elevation=0, dest_map=const(SOUTH), dest_warp_id=str(len(south["warp_events"])))
    south["warp_events"].append(dict(x=36, y=20, elevation=0, dest_map="MAP_ROUTE208",
                                     dest_warp_id=str(len(route208["warp_events"]))))
    out[f"data/maps/{SOUTH}/map.json"] = south
    out[south_bin] = reopen(south_raw, SOUTH_ARROW)
    for name in SLOTS:
        hdr = dict(hdrs[name], region_map_section=section_of(name))
        if name == "Route208":
            hdr["warp_events"] = hdr["warp_events"] + [door]
        out[f"data/maps/{name}/map.json"] = hdr
        if name in stage.OUTDOORS:
            base = f"{stage.BASE}/staged/{name}/"
            overlay = f"{stage.OVERLAYS[name]}/staged/{name}-dev-overlay/map.bin" if name in stage.OVERLAYS else None
            raw = src[overlay] if overlay in src else src[base + "averon-map.bin"]
            if len(raw) != len(src[base + "averon-map.bin"]):
                raise ValueError(name + ": overlay blockdata size differs from the staged map")
            if name == "Route208":
                raw = reopen(raw, ROUTE208_DOOR)
            border = src[base + ("border.bin" if name.endswith("_Access") else "averon-border.bin")]
            out[f"data/layouts/{name}/map.bin"], out[f"data/layouts/{name}/border.bin"] = raw, border
            kind = "Gate" if name.endswith("_Access") else "Outdoor"
            width, height = stage_dims(name)
            layouts.append(dict(id=hdr["layout"], name=name + "_Layout", width=width, height=height,
                                primary_tileset="gTileset_" + TILESETS[kind + "Primary"][0],
                                secondary_tileset="gTileset_" + TILESETS[kind + "Secondary"][0],
                                border_filepath=f"data/layouts/{name}/border.bin",
                                blockdata_filepath=f"data/layouts/{name}/map.bin"))
            script = f"{name}_MapScripts::\n\t.byte 0\n"
            portal = f"{stage.OVERLAYS.get(name)}/staged/{name}-dev-overlay/portal-script.inc"
            out[f"data/maps/{name}/scripts.inc"] = script.encode() + (b"\n" + src[portal] if portal in src else b"")
        else:
            d = f"{stage.INTERIORS[name]}/staged/{name}/"
            out[f"data/maps/{name}/scripts.inc"] = src[d + "scripts.inc"]
            if hdr["layout"] in stock:
                continue
            info = json.loads(src[d + "layout.json"])
            if info["id"] != hdr["layout"]:
                raise ValueError(name + ": layout.json does not describe the header's layout")
            out[f"data/layouts/{name}/map.bin"], out[f"data/layouts/{name}/border.bin"] = src[d + "map.bin"], src[d + "border.bin"]
            layouts.append(dict(id=info["id"], name=name + "_Layout", width=info["width"], height=info["height"],
                                primary_tileset=info["primary_tileset"], secondary_tileset=info["secondary_tileset"],
                                border_filepath=f"data/layouts/{name}/border.bin",
                                blockdata_filepath=f"data/layouts/{name}/map.bin"))
    for kind, (symbol, secondary, _, family) in TILESETS.items():
        bank = "secondary" if secondary else "primary"
        dest = f"data/tilesets/{bank}/{folder(symbol)}/"
        out[dest + "metatiles.bin"] = (CENTRAL / family / f"{bank}-metatiles.bin").read_bytes()
        out[dest + "metatile_attributes.bin"] = (CENTRAL / family / f"{bank}-attributes.bin").read_bytes()
    check_links({h["id"]: h for h in [out[f"data/maps/{n}/map.json"] for n in SLOTS] + [south]})
    return out, layouts


def stage_dims(name):
    """Width and height of a hearthome-solaceon outdoor map, from its own DEV assembler's table."""
    text = (CENTRAL / "prepare_runtime.py").read_text()
    table = re.search(r"MAPS=\{(.*?)\}\n", text, re.S)[1]
    return tuple(int(v) for v in re.search(r"'" + re.escape(name) + r"':\((\d+),(\d+)\)", table).groups())


def check_links(headers):
    """Every warp between the packet's maps (and Coronet South) lands on a warp that leads back."""
    for mid, h in headers.items():
        for w in h["warp_events"]:
            if w["dest_map"] in headers:
                back = headers[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
                if back["dest_map"] != mid:
                    raise ValueError(f"{mid} warp to {w['dest_map']} {w['dest_warp_id']} does not lead back")


def tileset_fields(symbol, secondary, graphics):
    tiles, palettes, callback = GRAPHICS_BINDINGS[graphics]
    return dict(isCompressed="TRUE", isSecondary="TRUE" if secondary else "FALSE",
                tiles=tiles, palettes=palettes, metatiles="gMetatiles_" + symbol,
                metatileAttributes="gMetatileAttributes_" + symbol, callback=callback)


def metatile_declarations(symbol, secondary):
    bank = "secondary" if secondary else "primary"
    return [f'const u16 {prefix}_{symbol}[] = INCBIN_U16("data/tilesets/{bank}/{folder(symbol)}/{filename}");'
            for prefix, filename in (("gMetatiles", "metatiles.bin"),
                                     ("gMetatileAttributes", "metatile_attributes.bin"))]


def tileset_sources(engine):
    """include/tilesets.h, headers.h and metatiles.h with the four central banks declared (packet C's style)."""
    engine = pathlib.Path(engine)
    tilesets = (engine / "include/tilesets.h").read_text()
    end = "\n#endif //GUARD_tilesets_H"
    # Inside the include guard, wherever it closes (earlier installers may have appended after it).
    if tilesets.count(end) != 1 or "AveronCentral" in tilesets:
        raise ValueError("tilesets.h is not in the expected pre-packet form")
    decls = "".join(f"extern const struct Tileset gTileset_{s};\n" for s, _, _, _ in TILESETS.values())
    out = {"include/tilesets.h": tilesets.replace(end, "\n" + decls.rstrip("\n") + "\n" + end, 1)}
    headers = (engine / "src/data/tilesets/headers.h").read_text()
    metatiles = (engine / "src/data/tilesets/metatiles.h").read_text()
    for symbol, secondary, graphics, _ in TILESETS.values():
        bind = tileset_fields(symbol, secondary, graphics)
        headers += (f"\nconst struct Tileset gTileset_{symbol} =\n{{\n .isCompressed=TRUE, "
                    f".isSecondary={'TRUE' if secondary else 'FALSE'},\n"
                    f" .tiles={bind['tiles']}, .palettes={bind['palettes']},\n"
                    f" .metatiles=gMetatiles_{symbol},\n .metatileAttributes = gMetatileAttributes_{symbol},\n"
                    f" .callback={bind['callback']},\n}};\n")
        metatiles += "\n".join(metatile_declarations(symbol, secondary)) + "\n"
    out["src/data/tilesets/headers.h"] = headers
    out["src/data/tilesets/metatiles.h"] = metatiles
    return {k: v.encode() for k, v in out.items()}


def tileset_source_errors(engine):
    """Check complete central structs and declarations, not merely their symbol names."""
    paths = ("include/tilesets.h", "src/data/tilesets/headers.h", "src/data/tilesets/metatiles.h")
    text = {p: re.sub(r"/\*.*?\*/|//[^\n]*", "", (engine / p).read_text(), flags=re.S) for p in paths}
    bad = set()
    field_pattern = r"\.(\w+)\s*=\s*([^,{}]+?)\s*,"
    for symbol, secondary, graphics, _ in TILESETS.values():
        declaration = f"extern const struct Tileset gTileset_{symbol};"
        include = text[paths[0]]
        if include.count(declaration) != 1 or declaration not in include.split("#endif", 1)[0]:
            bad.add(paths[0])
        blocks = re.findall(r"const\s+struct\s+Tileset\s+gTileset_" + re.escape(symbol)
                            + r"\s*=\s*\{(.*?)\};", text[paths[1]], re.S)
        if len(blocks) != 1:
            bad.add(paths[1])
        else:
            fields = re.findall(field_pattern, blocks[0])
            values = {key: value.strip() for key, value in fields}
            if (len(fields) != len(values) or values != tileset_fields(symbol, secondary, graphics)
                    or re.sub(field_pattern, "", blocks[0]).strip()):
                bad.add(paths[1])
        for declaration in metatile_declarations(symbol, secondary):
            prefix = declaration.split(" =", 1)[0]
            if text[paths[2]].count(declaration) != 1 or text[paths[2]].count(prefix) != 1:
                bad.add(paths[2])
    return sorted(bad)


def baseline_errors(engine, installed):
    """Differences from the pinned pre-E baseline (prefix-pins.json): the exact ordered Sinnoh prefix and its
    registry slots, sections through 227 and packet D's 228-230, and Coronet South's complete warps and blockdata.
    installed: the engine should additionally hold exactly this packet's appended part."""
    engine = pathlib.Path(engine)
    prefix = BASELINE["sinnoh_prefix"]
    errors = []
    sinnoh = read_json(engine / "data/maps/map_groups.json")["gMapGroup_Sinnoh"]
    if not PACKET_D <= set(sinnoh):
        errors.append("packet D is not installed: " + ", ".join(sorted(PACKET_D - set(sinnoh))))
    if sinnoh != prefix + (SLOTS if installed else []):
        errors.append("gMapGroup_Sinnoh is not the pinned prefix" + (" followed by packet E" if installed else ""))
    registry = (engine / REGISTRY).read_text()
    total = len(prefix) + (len(SLOTS) if installed else 0)
    if f"REGISTRY_GROUP(76, gMapGroup_Sinnoh, {total}, 1)" not in registry or any(
            f"REGISTRY_SLOT(76, {i}, {const(m)}, {m}, 1)\n" not in registry for i, m in enumerate(prefix)):
        errors.append("registry slots differ from the pinned prefix")
    entries = read_json(engine / SECTIONS)["map_sections"]
    d = BASELINE["packet_d_sections"]
    if (sha(json.dumps(entries[:SECTIONS_THROUGH_227], sort_keys=True).encode())
            != BASELINE["sections_through_227_sha256"]
            or entries[SECTIONS_THROUGH_227:SECTIONS_THROUGH_227 + len(d)] != d
            or len(entries) != SECTIONS_THROUGH_227 + len(d) + (len(SECTIONS_NEW) if installed else 0)):
        errors.append("sections differ from the pinned 0-227 and packet D's 228-230")
    if not (engine / f"data/maps/{SOUTH}/map.json").exists():
        return errors + ["packet D's Coronet South is missing"]
    south, _, raw = south_before(engine)
    pinned = BASELINE["coronet_south"]["warp_events"]
    if south["warp_events"][:len(pinned)] != pinned or (not installed and len(south["warp_events"]) != len(pinned)):
        errors.append("Coronet South's packet D warps differ from the pinned baseline")
    values = cells(raw)
    (x, y), closed, opened, width = SOUTH_ARROW
    if installed:
        if values[y * width + x] != opened:
            errors.append("Coronet South's east arrow is not reopened")
        values[y * width + x] = closed
    if sha(pack(values)) != BASELINE["coronet_south"]["blockdata_sha256"]:
        errors.append("Coronet South's blockdata differs from packet D's pinned baseline")
    return errors


def prior(engine):
    """The production Sinnoh group before this packet; refuses anything but the exact pinned packet D baseline."""
    errors = baseline_errors(engine, installed=False)
    if errors:
        raise ValueError("; ".join(errors))
    return read_json(pathlib.Path(engine) / "data/maps/map_groups.json")["gMapGroup_Sinnoh"]


def appended(engine, layouts):
    """map_groups, layouts, event_scripts, the registry slot list, the tileset sources and sections 231-238."""
    engine = pathlib.Path(engine)
    groups = read_json(engine / "data/maps/map_groups.json")
    all_layouts = read_json(engine / "data/layouts/layouts.json")
    scripts = (engine / "data/event_scripts.s").read_text()
    registry = (engine / REGISTRY).read_text()
    sections = read_json(engine / SECTIONS)
    sinnoh = prior(engine)
    n, last = len(sinnoh), sinnoh[-1]
    groups["gMapGroup_Sinnoh"] = sinnoh + SLOTS
    if {l.get("id") for l in all_layouts["layouts"]} & {l["id"] for l in layouts}:
        raise ValueError("a packet E layout id already exists")
    all_layouts["layouts"] += layouts
    include = f'\t.include "data/maps/{last}/scripts.inc"\n'
    if include not in scripts:
        raise ValueError("event_scripts.s does not include the last Sinnoh map")
    scripts = scripts.replace(include, include + "".join(f'\t.include "data/maps/{m}/scripts.inc"\n' for m in SLOTS), 1)
    old = f"REGISTRY_GROUP(76, gMapGroup_Sinnoh, {n}, 1)"
    if old not in registry or not registry.endswith(f"REGISTRY_SLOT(76, {n - 1}, {const(last)}, {last}, 1)\n"):
        raise ValueError("registry does not end with the current Sinnoh prefix")
    registry = registry.replace(old, f"REGISTRY_GROUP(76, gMapGroup_Sinnoh, {n + len(SLOTS)}, 1)")
    registry += "".join(f"REGISTRY_SLOT(76, {i}, {const(m)}, {m}, 1)\n" for i, m in enumerate(SLOTS, n))
    entries = sections["map_sections"]
    if entries[-1].get("value") != LAST_D_SECTION:
        raise ValueError(f"the last section is {entries[-1].get('value')}, expected packet D's {LAST_D_SECTION}")
    if {i for i, _, _ in SECTIONS_NEW} & {e["id"] for e in entries}:
        raise ValueError("a packet E section already exists")
    entries += [dict(id=i, value=v, name=t, region="REGION_SINNOH") for i, v, t in SECTIONS_NEW]
    out = {"data/maps/map_groups.json": groups, "data/layouts/layouts.json": all_layouts,
           "data/event_scripts.s": scripts.encode(), REGISTRY: registry.encode(), SECTIONS: sections}
    out.update(tileset_sources(engine))
    return out


def check(engine):
    """Recompute the packet's own files and confirm every appended entry; lists every mismatching path."""
    engine = pathlib.Path(engine)
    sinnoh = read_json(engine / "data/maps/map_groups.json")["gMapGroup_Sinnoh"]
    bad = baseline_errors(engine, installed=True)
    if bad:
        return bad
    files, layouts = plan_installed(engine)
    bad += [rel for rel, value in files.items()
            if not (engine / rel).exists() or (engine / rel).read_bytes() != encode(value)]
    have = {l.get("id"): l for l in read_json(engine / "data/layouts/layouts.json")["layouts"]}
    if any(have.get(l["id"]) != l for l in layouts):
        bad.append("data/layouts/layouts.json")
    scripts = (engine / "data/event_scripts.s").read_text()
    if any(scripts.count(f'\t.include "data/maps/{m}/scripts.inc"\n') != 1 for m in SLOTS):
        bad.append("data/event_scripts.s")
    registry = (engine / REGISTRY).read_text()
    first = len(sinnoh) - len(SLOTS)
    if any(f"REGISTRY_SLOT(76, {i}, {const(m)}, {m}, 1)" not in registry for i, m in enumerate(SLOTS, first)):
        bad.append(REGISTRY)
    entries = read_json(engine / SECTIONS)["map_sections"]
    if entries[-len(SECTIONS_NEW):] != [dict(id=i, value=v, name=t, region="REGION_SINNOH") for i, v, t in SECTIONS_NEW]:
        bad.append(SECTIONS)
    bad += tileset_source_errors(engine)
    return bad


def plan_installed(engine):
    """plan() as it ran before the install: South's appended warp and reopened arrow are undone first (and only
    if they are exactly what this packet wrote, so a tampered South still mismatches)."""
    south, path, raw = south_before(engine)
    (x, y), closed, opened, width = SOUTH_ARROW
    values = cells(raw)
    values[y * width + x] = closed          # baseline_errors() has already proved the rest equals the pin
    return plan(engine, (dict(south, warp_events=BASELINE["coronet_south"]["warp_events"]), path, pack(values)))


def encode(value):
    return value if isinstance(value, bytes) else (json.dumps(value, indent=2) + "\n").encode()


def install(engine):
    engine = pathlib.Path(engine)
    try:
        prior(engine)
        files, layouts = plan(engine)
        files.update(appended(engine, layouts))
    except ValueError as err:
        sys.exit("refusing: " + str(err))
    for rel, value in files.items():
        (engine / rel).parent.mkdir(parents=True, exist_ok=True)
        (engine / rel).write_bytes(encode(value))
    return SLOTS


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
