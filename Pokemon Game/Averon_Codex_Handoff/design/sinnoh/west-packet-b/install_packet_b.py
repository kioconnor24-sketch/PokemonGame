#!/usr/bin/env python3
"""West integrated packet B: install W28's Floaroma interiors and W23's Route 205 South house into the engine.

PRODUCTION integration of already-staged and gated Claude geography, appended after the existing 22 Sinnoh slots:
- W28 (production-interiors, #321): the donor rooms behind production doors at the donor's own coordinates,
  Floaroma Flower Shop (22, 13), House 1 (13, 16), Mart (26, 19), House 2 (26, 28) and the Floaroma Meadow house
  (35, 41), in neutral indoor art from the merged packer. Their tileset pair becomes production's
  gTileset_AveronFloaromaInteriorPrimary/Secondary (metatile banks only; tiles, palettes and callback are the stock
  Building/Shop ones, as gTileset_AveronCorridorRustboro does for Rustboro).
- W23 (eterna-forest-gate, #313): only the house behind Route 205 South's door (21, 22), a stock LAYOUT_HOUSE1
  shell. The tunnel into Eterna Forest waits for the forest itself to reach production, so production Route 205
  South gains the door warp alone (index 0; the staged house's return warp is renumbered to match).

Every door cell is the production one, unchanged: only warps are added (no map.bin of an existing map changes).
Identities: map slots 22-27 appended to gMapGroup_Sinnoh in the order of SLOTS (0-21 untouched); five new layouts
(LAYOUT_<ROOM>) appended; sections are the existing MAPSEC_FLOAROMA_TOWN and MAPSEC_ROUTE_205. No new
section/healer/flag/var/save identity, services, NPCs, encounters or story. Interior headers copy
JubilifeCity_Mart's header fields with the parent map's music, as packet A's do.

The builders' committed staging is the input (no donor tree is needed); the three production headers this packet
changes are pinned in base/, so the staging stays reproducible after integration.

  install_packet_b.py --engine ENGINE           write the engine files (refuses on a tree already installed)
  install_packet_b.py --engine ENGINE --check   verify the engine equals a fresh install (exit 1 otherwise)
"""
import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
BASE = HERE / "base"
W28 = SINNOH / "production-interiors"
W23 = SINNOH / "eterna-forest-gate"
PRIOR_SLOTS = 22
LAST_PRIOR = "OreburghGate_B1F"
# Appended slots, in order: 22-26 (W28, its ROOMS order), 27 (W23's house).
ROOMS = ["FloaromaTown_FlowerShop", "FloaromaTown_House1", "FloaromaTown_Mart", "FloaromaTown_House2",
         "FloaromaMeadow_House"]
HOUSE = "Route205_South_House"
SLOTS = ROOMS + [HOUSE]
PARENT = {"FloaromaTown_FlowerShop": "FloaromaTown", "FloaromaTown_House1": "FloaromaTown",
          "FloaromaTown_Mart": "FloaromaTown", "FloaromaTown_House2": "FloaromaTown",
          "FloaromaMeadow_House": "FloaromaMeadow", HOUSE: "Route205_South"}
HOUSE_DOOR = (21, 22)
TILESETS = {False: "AveronFloaromaInteriorPrimary", True: "AveronFloaromaInteriorSecondary"}
DEV_TILESETS = {"gTileset_ClaudeProdInteriorPrimary": "gTileset_" + TILESETS[False],
                "gTileset_ClaudeProdInteriorSecondary": "gTileset_" + TILESETS[True]}
REGISTRY = "test/data/averon_map_registry_slots.inc"
HEADER_FIELDS = ("region", "weather", "map_type", "allow_cycling", "allow_escaping", "allow_running",
                 "show_map_name", "requires_flash", "battle_scene")


def const(name, prefix="MAP_"):
    """FloaromaTown_FlowerShop -> MAP_FLOAROMA_TOWN_FLOWER_SHOP (the project's map/layout constant naming)."""
    return prefix + re.sub(r"(?<=[a-z])(?=[A-Z])|(?<=[0-9])(?=[A-Z][a-z])", "_", name).upper()


def folder(symbol):
    """AveronFloaromaInteriorPrimary -> averon_floaroma_interior_primary."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", symbol).lower()


def read_json(path):
    return json.loads(pathlib.Path(path).read_text())


def production_header(staged, template, parent, layout):
    """The staged header's identity and warps on a production interior template, with the parent's music/section."""
    hdr = {"id": staged["id"], "name": staged["name"], "layout": layout, "music": parent["music"]}
    for k in HEADER_FIELDS:
        hdr[k] = template[k]
    hdr["region_map_section"] = parent["region_map_section"]
    hdr.update(connections=[], object_events=[], coord_events=[], bg_events=[], warp_events=staged["warp_events"])
    return hdr


def with_door_warps(base, overlay):
    """The overlay must be base plus appended warps only; returns it."""
    n = len(base["warp_events"])
    assert {k: v for k, v in overlay.items() if k != "warp_events"} == {k: v for k, v in base.items()
                                                                        if k != "warp_events"}, base["id"]
    assert overlay["warp_events"][:n] == base["warp_events"], base["id"]
    return overlay


def plan(engine):
    """Every engine file this packet writes or adds, as {relative path: bytes or JSON}, plus the new layouts."""
    engine = pathlib.Path(engine)
    template = read_json(engine / "data/maps/JubilifeCity_Mart/map.json")
    base = {m: read_json(BASE / f"data/maps/{m}/map.json") for m in ("FloaromaTown", "FloaromaMeadow", "Route205_South")}
    files, layouts = {}, []
    for town in ("FloaromaTown", "FloaromaMeadow"):
        files[f"data/maps/{town}/map.json"] = with_door_warps(base[town],
                                                              read_json(W28 / f"staged/{town}-dev-overlay/map.json"))
    route = dict(base["Route205_South"])
    assert route["warp_events"] == [], route["warp_events"]
    w23_route = read_json(W23 / "staged/Route205_South-dev-overlay/map.json")
    door = [w for w in w23_route["warp_events"] if (w["x"], w["y"]) == HOUSE_DOOR]
    assert len(door) == 1 and door[0]["dest_map"] == const(HOUSE), door
    route["warp_events"] = door
    files["data/maps/Route205_South/map.json"] = route
    parents = {m: files[f"data/maps/{m}/map.json"] for m in ("FloaromaTown", "FloaromaMeadow", "Route205_South")}
    for room in ROOMS:
        d = W28 / "staged" / room
        staged, dims = read_json(d / "map.json"), read_json(d / "layout.json")
        parent = parents[PARENT[room]]
        for w in staged["warp_events"]:                     # each street mat returns through the room's own door
            back = parent["warp_events"][int(w["dest_warp_id"])]
            assert w["dest_map"] == parent["id"] and back["dest_map"] == staged["id"], (room, w, back)
        layout = const(room, "LAYOUT_")
        files[f"data/maps/{room}/map.json"] = production_header(staged, template, parent, layout)
        files[f"data/maps/{room}/scripts.inc"] = (d / "scripts.inc").read_bytes()
        files[f"data/layouts/{room}/map.bin"] = (d / "map.bin").read_bytes()
        files[f"data/layouts/{room}/border.bin"] = (d / "border.bin").read_bytes()
        assert len(files[f"data/layouts/{room}/map.bin"]) == dims["width"] * dims["height"] * 2, room
        layouts.append({"id": layout, "name": f"{room}_Layout", "width": dims["width"], "height": dims["height"],
                        "primary_tileset": DEV_TILESETS[dims["primary_tileset"]],
                        "secondary_tileset": DEV_TILESETS[dims["secondary_tileset"]],
                        "border_filepath": f"data/layouts/{room}/border.bin",
                        "blockdata_filepath": f"data/layouts/{room}/map.bin"})
    house = read_json(W23 / f"staged/{HOUSE}/map.json")
    for w in house["warp_events"]:
        assert w["dest_map"] == route["id"], w
        w["dest_warp_id"] = "0"                             # production Route 205 South has only the door warp
    files[f"data/maps/{HOUSE}/map.json"] = production_header(house, template, route, house["layout"])
    files[f"data/maps/{HOUSE}/scripts.inc"] = (W23 / f"staged/{HOUSE}/scripts.inc").read_bytes()
    for t in read_json(W28 / "staged/tilesets.json"):
        dest = f"data/tilesets/{'secondary' if t['secondary'] else 'primary'}/{folder(TILESETS[t['secondary']])}/"
        files[dest + "metatiles.bin"] = (W28 / t["metatiles"]).read_bytes()
        files[dest + "metatile_attributes.bin"] = (W28 / t["attributes"]).read_bytes()
    for name in SLOTS:
        assert files[f"data/maps/{name}/map.json"]["region_map_section"] in ("MAPSEC_FLOAROMA_TOWN",
                                                                             "MAPSEC_ROUTE_205"), name
    return files, layouts


def tileset_sources(engine):
    """include/tilesets.h, headers.h and metatiles.h with the pair declared, in gTileset_AveronCorridorRustboro's style."""
    engine = pathlib.Path(engine)
    out = {}
    tilesets = (engine / "include/tilesets.h").read_text()
    end = "\n#endif //GUARD_tilesets_H"
    assert tilesets.rstrip().endswith(end.strip()) and "AveronFloaromaInterior" not in tilesets
    decls = "".join(f"extern const struct Tileset gTileset_{TILESETS[s]};\n" for s in (False, True))
    out["include/tilesets.h"] = tilesets.replace(end, "\n" + decls.rstrip("\n") + "\n" + end, 1)
    headers = (engine / "src/data/tilesets/headers.h").read_text()
    metatiles = (engine / "src/data/tilesets/metatiles.h").read_text()
    for secondary, graphics in ((False, "Building"), (True, "Shop")):
        block = re.search(r"const struct Tileset gTileset_" + graphics + r" =\s*\{(.*?)\};", headers, re.S)[1]
        bind = {f: re.search(r"\." + f + r"\s*=\s*(\w+)\s*,", block)[1] for f in ("tiles", "palettes", "callback")}
        sym, bank = TILESETS[secondary], "secondary" if secondary else "primary"
        headers += (f"\nconst struct Tileset gTileset_{sym} =\n{{\n .isCompressed=TRUE, "
                    f".isSecondary={'TRUE' if secondary else 'FALSE'},\n"
                    f" .tiles={bind['tiles']}, .palettes={bind['palettes']},\n"
                    f" .metatiles=gMetatiles_{sym},\n .metatileAttributes = gMetatileAttributes_{sym},\n"
                    f" .callback={bind['callback']},\n}};\n")
        metatiles += (f'const u16 gMetatiles_{sym}[] = INCBIN_U16("data/tilesets/{bank}/{folder(sym)}/metatiles.bin");\n'
                      f'const u16 gMetatileAttributes_{sym}[] = '
                      f'INCBIN_U16("data/tilesets/{bank}/{folder(sym)}/metatile_attributes.bin");\n')
    out["src/data/tilesets/headers.h"] = headers
    out["src/data/tilesets/metatiles.h"] = metatiles
    return {k: v.encode() for k, v in out.items()}


def appended(engine, layouts):
    """map_groups.json, layouts.json, event_scripts.s, the registry slot list and the tileset sources, appended."""
    engine = pathlib.Path(engine)
    groups = read_json(engine / "data/maps/map_groups.json")
    all_layouts = read_json(engine / "data/layouts/layouts.json")
    scripts = (engine / "data/event_scripts.s").read_text()
    registry = (engine / REGISTRY).read_text()
    sinnoh = groups["gMapGroup_Sinnoh"]
    assert len(sinnoh) == PRIOR_SLOTS and sinnoh[-1] == LAST_PRIOR, sinnoh[-3:]
    groups["gMapGroup_Sinnoh"] = sinnoh + SLOTS
    known = {l.get("id") for l in all_layouts["layouts"]}
    assert not known & {l["id"] for l in layouts}
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
    out = {"data/maps/map_groups.json": groups, "data/layouts/layouts.json": all_layouts,
           "data/event_scripts.s": scripts.encode(), REGISTRY: registry.encode()}
    out.update(tileset_sources(engine))
    return out


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


def check(engine):
    """Recompute the install against the base snapshot and the pre-packet prefixes; compare with the engine."""
    engine = pathlib.Path(engine)
    files, layouts = plan(engine)
    bad = [rel for rel, value in files.items() if not (engine / rel).exists() or (engine / rel).read_bytes() != encode(value)]
    if read_json(engine / "data/maps/map_groups.json")["gMapGroup_Sinnoh"][PRIOR_SLOTS:] != SLOTS:
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
    for path, sym in (("include/tilesets.h", "extern const struct Tileset gTileset_{}"),
                      ("src/data/tilesets/headers.h", "const struct Tileset gTileset_{} ="),
                      ("src/data/tilesets/metatiles.h", "const u16 gMetatiles_{}[]")):
        text = (engine / path).read_text()
        if any(text.count(sym.format(s)) != 1 for s in TILESETS.values()):
            bad.append(path)
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
