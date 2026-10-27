#!/usr/bin/env python3
"""West integrated packet C: production Oreburgh City (section 227) and its W21 civic interiors.

PRODUCTION integration of already-staged geography, appended after the existing 30 Sinnoh slots, under the owner's
delegated decision of #15 comment 6434228501: one new saved-location code, 227 = MAPSEC_OREBURGH_CITY.
- Oreburgh City comes from Codex's oreburgh-connected candidate (prepare_candidate.assemble(), read only): its map,
  border and isolated city metatile banks (General/Rustboro graphics; production names
  gTileset_AveronOreburghCity{Primary,Secondary}) and its restoration of Oreburgh Gate 1F's east doorway.
- Route 207 and Oreburgh Mine stay out (separate places, no section): the city keeps no Route 207 connection and
  its four mine-entrance cells (50-53, 57) are closed (collision 1, same metatile/elevation), as Codex closes other
  unbuilt destinations. Coronet stays closed as in the candidate.
- W21 (oreburgh-civic, #311): ten neutral interiors behind the city's doors on stock layouts (Gym and Galactic stay
  closed) and its one museum street-door collision change (54, 14). Their city returns are renumbered: the four
  mine warps before them are dropped.
- Oreburgh Gate 1F already carries packet A's B1F ladder warp, so the east return is appended as its warp 2 and
  the city's gate warp points there.
Section 227 itself (region_map_sections.json) is written here; the pins file and native tests are separate
reviewed edits. The two Gate 1F files this packet changes are pinned in base/ (production before the packet). No healer, flag, var or other identity, NPC, service, encounter or story.

  install_packet_c.py --engine ENGINE           write the engine files (refuses on a tree already installed)
  install_packet_c.py --engine ENGINE --check   verify the engine equals a fresh install (exit 1 otherwise)
"""
import argparse
import copy
import importlib.util
import json
import pathlib
import re
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
REPO = HERE.parents[4]
BASE = HERE / "base"
W21 = SINNOH / "oreburgh-civic"
PRIOR_SLOTS = 30
LAST_PRIOR = "ValleyWindworks_Inside"
CITY = "OreburghCity"
ROOMS = ["OreburghCity_PokemonCenter_1F", "OreburghCity_Mart", "OreburghCity_Museum_1F", "OreburghCity_Museum_2F",
         "OreburghCity_Condo", "OreburghCity_House1", "OreburghCity_House2", "OreburghCity_House3",
         "OreburghCity_House4", "OreburghCity_House5"]
SLOTS = [CITY] + ROOMS
SECTION = {"id": "MAPSEC_OREBURGH_CITY", "value": 227, "name": "OREBURGH CITY", "region": "REGION_SINNOH"}
MINE_WARPS = 4                                      # candidate city warps 1-4 lead into the Mine
MINE_CELLS = [(50, 57), (51, 57), (52, 57), (53, 57)]
CITY_WIDTH = 70
TILESETS = {"cityprimary": ("AveronOreburghCityPrimary", False, "General"),
            "citysecondary": ("AveronOreburghCitySecondary", True, "Rustboro")}
REGISTRY = "test/data/averon_map_registry_slots.inc"
SECTIONS = "src/data/region_map/region_map_sections.json"
HEADER_FIELDS = ("region", "weather", "map_type", "allow_cycling", "allow_escaping", "allow_running",
                 "show_map_name", "requires_flash", "battle_scene")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


candidate = load("oreburgh_candidate", SINNOH / "oreburgh-connected/prepare_candidate.py")


def const(name, prefix="MAP_"):
    return prefix + re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[0-9])(?=[A-Z][a-z])", "_", name).upper()


def folder(symbol):
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", symbol).lower()


def read_json(path):
    return json.loads(pathlib.Path(path).read_text())


def cells(raw):
    return list(struct.unpack("<%dH" % (len(raw) // 2), raw))


def pack(values):
    return struct.pack("<%dH" % len(values), *values)


def plan(engine):
    """Every engine file this packet writes or adds, as {relative path: bytes or JSON}, plus the new layouts."""
    engine = pathlib.Path(engine)
    files, receipt = candidate.assemble(REPO)
    city = copy.deepcopy(receipt["source_headers"][CITY])
    assert city["connections"] == [{"map": "MAP_ROUTE207", "offset": 35, "direction": "up"}], city["connections"]
    assert [w["dest_map"] for w in city["warp_events"][1:1 + MINE_WARPS]] == ["MAP_OREBURGH_MINE_B1F"] * MINE_WARPS
    overlay = read_json(W21 / f"staged/{CITY}-dev-overlay/map.json")
    assert overlay["warp_events"][:1 + MINE_WARPS] == city["warp_events"], "W21 overlay no longer extends the city"
    doors = overlay["warp_events"][1 + MINE_WARPS:]
    assert len(doors) == 10 and {w["dest_map"] for w in doors} == {const(r) for r in ROOMS if r != "OreburghCity_Museum_2F"}
    # Production Gate 1F: Route 203 (0), packet A's B1F ladder (1); the candidate's east return is appended as 2.
    gate = read_json(BASE / "data/maps/OreburghGate_1F/map.json")     # production before this packet (pinned)
    assert [w["dest_map"] for w in gate["warp_events"]] == ["MAP_ROUTE203", "MAP_OREBURGH_GATE_B1F"], gate["warp_events"]
    east = json.loads(files["data/maps/OreburghGate_1F/map.json"])["warp_events"][1]
    assert (east["x"], east["y"], east["dest_map"], east["dest_warp_id"]) == (25, 20, const(CITY), "0")
    gate["warp_events"].append(east)
    city["warp_events"] = [dict(city["warp_events"][0], dest_warp_id=str(len(gate["warp_events"]) - 1))] + doors
    city["connections"] = []
    city["region_map_section"] = SECTION["id"]
    gate_cells = cells(files["data/layouts/OreburghGate_1F/map.bin"])
    production_gate = cells((BASE / "data/layouts/OreburghGate_1F/map.bin").read_bytes())
    opened = [(i % 29, i // 29) for i, (a, b) in enumerate(zip(candidate_base_gate(), gate_cells)) if a != b]
    assert sorted(opened) == sorted([(25, 20), (24, 21), (25, 21), (26, 21)]), opened
    for x, y in opened:                                 # the candidate's four east cells, on production's own Gate
        production_gate[y * 29 + x] = gate_cells[y * 29 + x]
    city_cells = cells(files[f"data/layouts/{CITY}/map.bin"])
    w21_cells = cells((W21 / f"staged/{CITY}-dev-overlay/map.bin").read_bytes())
    changed = [i for i, (a, b) in enumerate(zip(city_cells, w21_cells)) if a != b]
    assert [(i % CITY_WIDTH, i // CITY_WIDTH) for i in changed] == [(54, 14)], changed
    city_cells = w21_cells
    for x, y in MINE_CELLS:
        v = city_cells[y * CITY_WIDTH + x]
        assert not (v >> 10) & 3, (x, y, hex(v))
        city_cells[y * CITY_WIDTH + x] = v | (1 << 10)
    out = {f"data/maps/{CITY}/map.json": city,
           f"data/maps/{CITY}/scripts.inc": files[f"data/maps/{CITY}/scripts.inc"],
           f"data/layouts/{CITY}/map.bin": pack(city_cells),
           f"data/layouts/{CITY}/border.bin": files[f"data/layouts/{CITY}/border.bin"],
           "data/maps/OreburghGate_1F/map.json": gate,
           "data/layouts/OreburghGate_1F/map.bin": pack(production_gate)}
    layout = next(l for l in json.loads(files["data/layouts/layouts.json"])["layouts"] if l["id"] == city["layout"])
    layouts = [dict(layout, primary_tileset="gTileset_" + TILESETS["cityprimary"][0],
                    secondary_tileset="gTileset_" + TILESETS["citysecondary"][0])]
    layouts[0].pop("layout_version", None)
    for kind, (symbol, secondary, _) in TILESETS.items():
        src = f"data/tilesets/{'secondary' if secondary else 'primary'}/oreburgh_candidate_{kind}/"
        dest = f"data/tilesets/{'secondary' if secondary else 'primary'}/{folder(symbol)}/"
        for name in ("metatiles.bin", "metatile_attributes.bin"):
            out[dest + name] = files[src + name]
    template = read_json(engine / "data/maps/JubilifeCity_Mart/map.json")
    shift = MINE_WARPS
    for room in ROOMS:
        staged = read_json(W21 / f"staged/{room}/map.json")
        hdr = {"id": staged["id"], "name": staged["name"], "layout": staged["layout"], "music": city["music"]}
        for k in HEADER_FIELDS:
            hdr[k] = template[k]
        hdr["region_map_section"] = SECTION["id"]
        warps = []
        for w in staged["warp_events"]:
            w = dict(w)
            if w["dest_map"] == const(CITY):
                w["dest_warp_id"] = str(int(w["dest_warp_id"]) - shift)
            warps.append(w)
        hdr.update(connections=[], object_events=[], coord_events=[], bg_events=[], warp_events=warps)
        out[f"data/maps/{room}/map.json"] = hdr
        out[f"data/maps/{room}/scripts.inc"] = (W21 / f"staged/{room}/scripts.inc").read_bytes()
    check_links({h["id"]: h for h in [out[f"data/maps/{n}/map.json"] for n in SLOTS] + [gate]})
    return out, layouts


def candidate_base_gate():
    """The Gate 1F blockdata the candidate opened (its pinned base), to find exactly the cells it changed."""
    return cells(candidate.blob(REPO, candidate.BASE, candidate.ENGINE + "data/layouts/OreburghGate_1F/map.bin"))


def check_links(headers):
    """Every warp between the packet's maps (and the Gate) lands on a warp that leads back."""
    for mid, h in headers.items():
        for w in h["warp_events"]:
            if w["dest_map"] in headers:
                back = headers[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
                assert back["dest_map"] == mid, (mid, w, back)


def tileset_sources(engine):
    """include/tilesets.h, headers.h and metatiles.h with the city pair declared (AveronCorridorRustboro's style)."""
    engine = pathlib.Path(engine)
    tilesets = (engine / "include/tilesets.h").read_text()
    end = "\n#endif //GUARD_tilesets_H"
    assert tilesets.rstrip().endswith(end.strip()) and "AveronOreburghCity" not in tilesets
    decls = "".join(f"extern const struct Tileset gTileset_{s};\n" for s, _, _ in TILESETS.values())
    out = {"include/tilesets.h": tilesets.replace(end, "\n" + decls.rstrip("\n") + "\n" + end, 1)}
    headers = (engine / "src/data/tilesets/headers.h").read_text()
    metatiles = (engine / "src/data/tilesets/metatiles.h").read_text()
    for symbol, secondary, graphics in TILESETS.values():
        block = re.search(r"const struct Tileset gTileset_" + graphics + r" =\s*\{(.*?)\};", headers, re.S)[1]
        bind = {f: re.search(r"\." + f + r"\s*=\s*(\w+)\s*,", block)[1] for f in ("tiles", "palettes", "callback")}
        bank = "secondary" if secondary else "primary"
        headers += (f"\nconst struct Tileset gTileset_{symbol} =\n{{\n .isCompressed=TRUE, "
                    f".isSecondary={'TRUE' if secondary else 'FALSE'},\n"
                    f" .tiles={bind['tiles']}, .palettes={bind['palettes']},\n"
                    f" .metatiles=gMetatiles_{symbol},\n .metatileAttributes = gMetatileAttributes_{symbol},\n"
                    f" .callback={bind['callback']},\n}};\n")
        metatiles += (f'const u16 gMetatiles_{symbol}[] = INCBIN_U16("data/tilesets/{bank}/{folder(symbol)}/metatiles.bin");\n'
                      f'const u16 gMetatileAttributes_{symbol}[] = '
                      f'INCBIN_U16("data/tilesets/{bank}/{folder(symbol)}/metatile_attributes.bin");\n')
    out["src/data/tilesets/headers.h"] = headers
    out["src/data/tilesets/metatiles.h"] = metatiles
    return {k: v.encode() for k, v in out.items()}


def appended(engine, layouts):
    """map_groups, layouts, event_scripts, the registry slot list, the tileset sources and section 227, appended."""
    engine = pathlib.Path(engine)
    groups = read_json(engine / "data/maps/map_groups.json")
    all_layouts = read_json(engine / "data/layouts/layouts.json")
    scripts = (engine / "data/event_scripts.s").read_text()
    registry = (engine / REGISTRY).read_text()
    sections = read_json(engine / SECTIONS)
    sinnoh = groups["gMapGroup_Sinnoh"]
    assert len(sinnoh) == PRIOR_SLOTS and sinnoh[-1] == LAST_PRIOR, sinnoh[-3:]
    groups["gMapGroup_Sinnoh"] = sinnoh + SLOTS
    assert not {l.get("id") for l in all_layouts["layouts"]} & {l["id"] for l in layouts}
    all_layouts["layouts"] += layouts
    last = f'\t.include "data/maps/{LAST_PRIOR}/scripts.inc"\n'
    assert last in scripts
    scripts = scripts.replace(last, last + "".join(f'\t.include "data/maps/{n}/scripts.inc"\n' for n in SLOTS), 1)
    old = f"REGISTRY_GROUP(76, gMapGroup_Sinnoh, {PRIOR_SLOTS}, 1)"
    assert old in registry and registry.endswith(
        f"REGISTRY_SLOT(76, {PRIOR_SLOTS - 1}, {const(LAST_PRIOR)}, {LAST_PRIOR}, 1)\n")
    registry = registry.replace(old, f"REGISTRY_GROUP(76, gMapGroup_Sinnoh, {PRIOR_SLOTS + len(SLOTS)}, 1)")
    for i, n in enumerate(SLOTS, PRIOR_SLOTS):
        registry += f"REGISTRY_SLOT(76, {i}, {const(n)}, {n}, 1)\n"
    entries = sections["map_sections"]
    assert entries[-1]["id"] == "MAPSEC_ROUTE_205" and entries[-1]["value"] == SECTION["value"] - 1
    assert SECTION["id"] not in {e["id"] for e in entries} and SECTION["value"] not in {e.get("value") for e in entries}
    entries.append(dict(SECTION))
    out = {"data/maps/map_groups.json": groups, "data/layouts/layouts.json": all_layouts,
           "data/event_scripts.s": scripts.encode(), REGISTRY: registry.encode(), SECTIONS: sections}
    out.update(tileset_sources(engine))
    return out


def check(engine):
    """Recompute the install against base/ and the pre-packet prefixes; compare with the engine."""
    engine = pathlib.Path(engine)
    files, layouts = plan(engine)
    bad = [rel for rel, value in files.items() if not (engine / rel).exists() or (engine / rel).read_bytes() != encode(value)]
    if read_json(engine / "data/maps/map_groups.json")["gMapGroup_Sinnoh"][PRIOR_SLOTS:PRIOR_SLOTS + len(SLOTS)] != SLOTS:
        bad.append("data/maps/map_groups.json")
    have = {l.get("id"): l for l in read_json(engine / "data/layouts/layouts.json")["layouts"]}
    if any(have.get(l["id"]) != l for l in layouts):
        bad.append("data/layouts/layouts.json")
    scripts = (engine / "data/event_scripts.s").read_text()
    if any(f'\t.include "data/maps/{n}/scripts.inc"\n' not in scripts for n in SLOTS):
        bad.append("data/event_scripts.s")
    registry = (engine / REGISTRY).read_text()
    if any(f"REGISTRY_SLOT(76, {i}, {const(n)}, {n}, 1)" not in registry for i, n in enumerate(SLOTS, PRIOR_SLOTS)):
        bad.append(REGISTRY)
    if SECTION not in read_json(engine / SECTIONS)["map_sections"]:
        bad.append(SECTIONS)
    for path, sym in (("include/tilesets.h", "extern const struct Tileset gTileset_{}"),
                      ("src/data/tilesets/headers.h", "const struct Tileset gTileset_{} ="),
                      ("src/data/tilesets/metatiles.h", "const u16 gMetatiles_{}[]")):
        text = (engine / path).read_text()
        if any(text.count(sym.format(s)) != 1 for s, _, _ in TILESETS.values()):
            bad.append(path)
    return bad


def encode(value):
    return value if isinstance(value, bytes) else (json.dumps(value, indent=2) + "\n").encode()


def install(engine):
    engine = pathlib.Path(engine)
    groups = read_json(engine / "data/maps/map_groups.json")["gMapGroup_Sinnoh"]
    if len(groups) != PRIOR_SLOTS:
        sys.exit(f"refusing: gMapGroup_Sinnoh has {len(groups)} slots, expected {PRIOR_SLOTS} (already installed?)")
    files, layouts = plan(engine)
    files.update(appended(engine, layouts))
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
