#!/usr/bin/env python3
"""Promote the accepted five-map D source after the 41-map production prefix.

Reuses existing source/join producers and the exact payloads tested by #347.
Only the unbuilt Eterna north exit is newly closed: North (4,1) uses its own
solid wall at (4,0), preserving elevation. North's new production road return
becomes warp 0; no installed warp or saved identity moves. No bike is granted.
This installer is not production/native/emulator acceptance.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct

HERE = Path(__file__).resolve().parent
DESIGN = HERE.parent
REPO = HERE.parents[4]
ENGINE = REPO / "Pokemon Game/engine"
PRIOR_SLOTS = 41
SLOTS = ["Route206_North", "Route206", "Route206_South", "Route207", "MtCoronet_1F_South"]
DIMENSIONS = [(9, 11), (28, 120), (9, 11), (64, 32), (42, 32)]
SECTIONS = [dict(id=s, value=v, name=n, region="REGION_SINNOH") for s, v, n in (
    ("MAPSEC_ROUTE_206", 228, "ROUTE 206"), ("MAPSEC_ROUTE_207", 229, "ROUTE 207"),
    ("MAPSEC_MT_CORONET", 230, "MT. CORONET"))]
GROUPS = "data/maps/map_groups.json"
LAYOUTS = "data/layouts/layouts.json"
REGISTRY = "test/data/averon_map_registry_slots.inc"
SECTION_PATH = "src/data/region_map/region_map_sections.json"
PINS = "../scripts/averon-mapsec-pins.json"
CITY = "data/maps/OreburghCity/map.json"
RECEIPT_SHA = "1dca7ef30738c16e121e941fe6a6f7d85197333fd073ccc9814b4854ed4814aa"
ASSET_HASHES = {
    "data/layouts/RustboroCity/map.bin": "5d1838e9e5c8f8a3bd519b0f7adaf1f01ef556deb9f8d5b46ec5996b26d51c4d",
    "data/tilesets/primary/building/metatile_attributes.bin": "7a153a1748dc4bd03e621acad6c6b7e90c2d3acfc467a928ad23d21f34e73128",
    "data/tilesets/primary/building/metatiles.bin": "65e40fece49f8ed09a82b33c3d590716d9740581f087acd1359665331e4683f1",
    "data/tilesets/primary/building/palettes/00.pal": "6008920965897f0fe9e901ab795aacb4c6a6869ea300db6cfb6411da42f750ee",
    "data/tilesets/primary/building/palettes/05.pal": "b81a37f041aeb04428ce37ad1f7a7a476cdc822f534a4cda12f360c4ca5d0a58",
    "data/tilesets/primary/building/tiles.png": "355d5dc8625e332ceb34cbe685092d96540ece0b7a39293e493d27c02b6db300",
    "data/tilesets/primary/general/metatile_attributes.bin": "06c9548a6c70d133b6d47638090f5d36f3fec92aace3d90deca758a4404cfa9b",
    "data/tilesets/primary/general/metatiles.bin": "17974b0ba1bb9d105d5ba255c69a3b80d8484a26ea0b8ff22c6c6567c6c22910",
    "data/tilesets/primary/general/palettes/00.pal": "424a32d1079a61b6b9b4f1e879dd68108708905e8312d18edd134af3918407fd",
    "data/tilesets/primary/general/palettes/01.pal": "9b9d01878137cef9ea6006c3025a3ada5cdf37d9c251b25bc95f71963bd9a447",
    "data/tilesets/primary/general/palettes/02.pal": "8a469b137e6fc97823ab46b903c0ab80c466212cd430340586ccde22afbee949",
    "data/tilesets/primary/general/palettes/03.pal": "821f0a62f0ce995c96e9eaa0b4a32a1cd61e4db1f3216bfbe1fd588cf33b7583",
    "data/tilesets/primary/general/palettes/04.pal": "f99602126046eed3f20545a34ddd46fa6e5fcb96f032b410fa8d5251c7450e22",
    "data/tilesets/primary/general/palettes/05.pal": "53b599be1554c4e1a0684f2339409ee4032ac8507696dae1836a10152f925177",
    "data/tilesets/primary/general/tiles.png": "365ba5482e7564763e614a0009900d1c317790dcd9f7a06c4ab74c363a3ba2f5",
    "data/tilesets/secondary/cave/metatiles.bin": "fca8629264b6ff2324224864ed98d929cc5a93213a5a512a3798d144470e022b",
    "data/tilesets/secondary/cave/palettes/06.pal": "aa7b4ee23247cf3b450244bf3f6bd93261636f9fbbcd5f1aca5e4c2c7b4514d8",
    "data/tilesets/secondary/cave/palettes/10.pal": "b59c1a54bf459f1af44d296fcee008d209bb398517e90666719620f272079d9b",
    "data/tilesets/secondary/cave/tiles.png": "bcffd7ad24c8acb328cee23598dca4dadeb527299c76565e6a9d939e25e40c76",
    "data/tilesets/secondary/mauville/metatile_attributes.bin": "07e8180a08d0592ac94ec2e089e92303527f71aad370aa6df90ff863cca4d9cc",
    "data/tilesets/secondary/mauville/metatiles.bin": "cb89f9ae47ac21b01246a7ffedf69d26028dcaa0a75e453ec3841d40022bda89",
    "data/tilesets/secondary/mauville/tiles.png": "fc7ff5d72e303208245539379ba04f7f7169b402d064d9bcf9281d750098be31",
    "data/tilesets/secondary/rustboro/metatiles.bin": "2e5daf7451ac4a3a003ce569e2132dccefe00b618f3e5763d45b2cef480b3274",
    "data/tilesets/secondary/rustboro/palettes/08.pal": "58548dec58b639dd5495ddf754a75e801c2b57d7b9cb9a0c9622ae7a9da271cf",
    "data/tilesets/secondary/rustboro/palettes/10.pal": "77b5d5106753402ee7fadb6801d7ea06011292b99feec522a6dccf5f103bd74a",
    "data/tilesets/secondary/rustboro/palettes/11.pal": "7a776801783d71cccc318c86ee844499c4c2a43404058417553989536781601f",
    "data/tilesets/secondary/rustboro/tiles.png": "87b3ce4e15674b3ef02b1793df0bc8633b7c49bf4443cb50708293615b048d24",
    "data/tilesets/secondary/shop/metatile_attributes.bin": "195c8f4e535fe202c57331445a5aeb69a5fa95f739def300982f84c7a4246f63",
    "data/tilesets/secondary/shop/metatiles.bin": "f7a58c91b3c84e2c9fc5f6e24d851dccff7a29f1b730d53ab73b76ff31a0a399",
    "data/tilesets/secondary/shop/palettes/06.pal": "91c6471d2d5c8ed31bd09afe6560f5b03a36e0fbb2ac64f05e0af8dbc71f9468",
    "data/tilesets/secondary/shop/palettes/08.pal": "71560cea7b2102a71f4f2196d85648cdd2b2e15037cf4fdb3e7bbefb0e4ddbbc",
    "data/tilesets/secondary/shop/palettes/09.pal": "cb0b85a65027df3c046bfd4c34cac6d2842a9377f051eca18360a5f5c07e026f",
    "data/tilesets/secondary/shop/tiles.png": "126543a3d5b56c106749de8cf3cbde20597898bbea7a991fc7887a2d868f7739"
}
BASE_HASHES = {
    "data/maps/map_groups.json": "a792bac30f20c0bf5fba80c93f3cb35a9dec4e1f006b40fdfdd782f3a96827b5",
    "data/layouts/layouts.json": "3bb95285d46880ce7d9c8d1e985afdaed78104f611538705e2744ff3a804e854",
    "data/event_scripts.s": "b2c7fa83d2490b660eb74969109f548b34ca17a436bdea88aaafec4737de2712",
    "include/tilesets.h": "63011b97317135567d8cb53e311568a2856fb23106ff0ca0deb01d2d8af29e5c",
    "src/data/tilesets/headers.h": "6978ca8b380e89bbebd0e087ea6fe73cfe9a2dc784c90d692f071cb611b93299",
    "src/data/tilesets/metatiles.h": "cfe37788cc7f148eb7f8898e86991f3cd1fa8762af5e45a485acfa2607f03bc8",
    "test/data/averon_map_registry_slots.inc": "78abd91729e35d84c4b049af4c87968fac0f8b5560590de3e18b82e06dc31c40",
    "src/data/region_map/region_map_sections.json": "89c14b9186efc42f345c49b84481b6448432458825fde3a2f4b58073b426db82",
    "data/maps/OreburghCity/map.json": "ae1e3c51b9632f7486f2934bd5db02efed3375680e60b5d6fbed7979ebd1eda6",
    "test/averon_location_compatibility.c": "a6a5e5f8f07ab8e839bb76565e176a3052684668e7f0088052241addad6ad1a5",
    "test/averon_northern_location.c": "33d63df7dae4c1241bdf87ba8c85a8b1419ccbb32e5f4d5f130e4d28cefa97f7",
    "test/averon_sandgem_location.c": "7ae5a7d13edc389fc14df52636e6ffeb0210310da03477480fda764a8ac90d18",
    "test/averon_oreburgh_location.c": "43d98b31426dd8a02444dec2f7256974765356d9adf6653d1f6e05ab7284798b",
    "data/tilesets/primary/averon_oreburgh_city_primary/metatiles.bin": "a610df7e921699e100e7bbe5831492a552e8ef317d23963cac78fbf2875a5ea0",
    "data/tilesets/primary/averon_oreburgh_city_primary/metatile_attributes.bin": "5d29d2955d8f86e187d3aa145f76747bfb9947d54f21c04bd9b9b890f265dcca",
    "data/tilesets/secondary/averon_oreburgh_city_secondary/metatiles.bin": "323a0684dbdbd2be3c60fb5cd318b328d55c6006fe472340a2cd74cdf9b57702",
    "data/tilesets/secondary/averon_oreburgh_city_secondary/metatile_attributes.bin": "858160b569ae7b127588e911422e95450d2b180b5de1acce6865b8a0d9a8c574",
    "../scripts/averon-mapsec-pins.json": "45d67ad6381448d52691af8160bf8e99bfc447676862e45ae4d04ea41046bcf1"
}
sha = lambda b: hashlib.sha256(b).hexdigest()
encode = lambda obj: (json.dumps(obj, indent=2) + "\n").encode()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require(ok, message):
    if not ok:
        raise ValueError(message)


def accepted_source():
    """Read existing source; reject any divergence from #347's tested payloads."""
    receipt = (HERE / "runtime-evidence/RESULTS.json").read_bytes()
    require(sha(receipt) == RECEIPT_SHA, "accepted D evidence identity changed")
    expected = json.loads(receipt)["source"]["receipt"]["files"]
    reused = load("production_d_reused", HERE / "prepare_runtime.py")
    join = load("production_d_join", DESIGN / "cycling-road-join/build_cycling_road_join.py")
    a, b, cells_a, cells_b, _, _ = join.build()
    data, pins = reused.south_inputs(REPO)
    files = {}
    for name in SLOTS[:3]:
        folder = DESIGN / "eterna-cycle/staged" / name
        h = json.loads((folder / "map.json").read_text())
        if name == "Route206":
            h = a
        h["region_map_section"] = "MAPSEC_ROUTE_201"
        files[f"data/maps/{name}/map.json"] = encode(h)
        files[f"data/layouts/{name}/map.bin"] = (struct.pack("<%dH" % len(cells_a), *cells_a)
            if name == "Route206" else (folder / "averon-map.bin").read_bytes())
        files[f"data/layouts/{name}/border.bin"] = (folder / "averon-border.bin").read_bytes()
    b["region_map_section"] = "MAPSEC_ROUTE_201"
    b["warp_events"] = copy.deepcopy(pins["donor_headers"]["data/maps/Route207/map.json"]["warp_events"])
    raw = bytearray(struct.pack("<%dH" % len(cells_b), *cells_b))
    require(struct.unpack_from("<H", raw, 744)[0] == 0x4A7, "Route207 closed doorway changed")
    struct.pack_into("<H", raw, 744, 0xA7)
    files["data/maps/Route207/map.json"] = encode(b)
    files["data/layouts/Route207/map.bin"] = bytes(raw)
    files["data/layouts/Route207/border.bin"] = (DESIGN / "oreburgh-donor/corridor/Route207/border.bin").read_bytes()
    south = json.loads(data["source-header.json"])
    south.update(warp_events=copy.deepcopy(pins["donor_headers"]["data/maps/MtCoronet_1F_South/map.json"]["warp_events"][:1]),
                 region_map_section="MAPSEC_ROUTE_201", music="MUS_PETALBURG_WOODS")
    raw = bytearray(data["averon-map.bin"])
    for index, before, after in ((113, 0x3222, 0x3604), (299, 0x361A, 0x321A), (876, 0x361A, 0x3604)):
        require(struct.unpack_from("<H", raw, index * 2)[0] == before, "South source port changed")
        struct.pack_into("<H", raw, index * 2, after)
    files["data/maps/MtCoronet_1F_South/map.json"] = encode(south)
    files["data/layouts/MtCoronet_1F_South/map.bin"] = bytes(raw)
    files["data/layouts/MtCoronet_1F_South/border.bin"] = data["averon-border.bin"]
    for name in SLOTS:
        files[f"data/maps/{name}/scripts.inc"] = f"{name}_MapScripts::\n\t.byte 0\n".encode()
    banks = {}
    for bank, label, family in (("primary", "OutdoorPrimary", "city-family"),
                                ("secondary", "OutdoorSecondary", "city-family"),
                                ("primary", "GatePrimary", "gate-art"),
                                ("secondary", "GateSecondary", "gate-art")):
        for filename, suffix in (("metatiles.bin", "metatiles.bin"), ("metatile_attributes.bin", "attributes.bin")):
            old = f"data/tilesets/{bank}/eterna_dev_{label.lower()}/{filename}"
            files[old] = (DESIGN / "eterna-cycle" / family / (bank + "-" + suffix)).read_bytes()
        banks[label] = (bank, "AveronRoute206" + label.removeprefix("Outdoor"))
    for bank in ("primary", "secondary"):
        for filename, suffix in (("metatiles.bin", "metatiles.bin"), ("metatile_attributes.bin", "attributes.bin")):
            old = f"data/tilesets/{bank}/packet_d_south/{filename}"
            files[old] = data[bank + "-" + suffix]
    require(all(expected.get(p) == sha(raw) for p, raw in files.items()), "accepted D payload differs")
    # South and Cycling Road share the same General primary metadata, not duplicate banks.
    for filename in ("metatiles.bin", "metatile_attributes.bin"):
        require(files["data/tilesets/primary/packet_d_south/" + filename] ==
                files["data/tilesets/primary/eterna_dev_outdoorprimary/" + filename], "shared primary differs")
    return files


def target(engine, path):
    engine = Path(engine).resolve()
    result = (engine / path).resolve()
    allowed = engine.parent / "scripts/averon-mapsec-pins.json" if path == PINS else None
    require(result == allowed or result.is_relative_to(engine), "output escapes approved engine/pins roots")
    return result


def additions(base, source):
    """Pure append plan; original global prefixes remain recoverable and pinned."""
    files = {}
    headers = {}
    for name in SLOTS:
        h = json.loads(source[f"data/maps/{name}/map.json"])
        h["region_map_section"] = SECTIONS[0 if name.startswith("Route206") else 1 if name == "Route207" else 2]["id"]
        if name == "Route206_North":
            require(h["warp_events"][0] == dict(x=4, y=1, elevation=0, dest_map="MAP_ETERNA_CITY", dest_warp_id="0"), "North external port changed")
            h["warp_events"] = h["warp_events"][1:]
        if name == "Route206":
            require(h["connections"][0] == dict(map="MAP_ETERNA_CITY", offset=-1, direction="up"), "north road boundary changed")
            h["connections"] = h["connections"][1:]
            require(h["warp_events"][0]["dest_warp_id"] == "1", "North internal return changed")
            h["warp_events"][0]["dest_warp_id"] = "0"
        require(not any(h[k] for k in ("object_events", "coord_events", "bg_events")), "unexpected gameplay events")
        headers[name] = h
        for filename in ("map.json", "scripts.inc"):
            p = f"data/maps/{name}/{filename}"
            files[p] = encode(h) if filename == "map.json" else source[p]
        for filename in ("map.bin", "border.bin"):
            p = f"data/layouts/{name}/{filename}"
            files[p] = source[p]
    north = bytearray(files["data/layouts/Route206_North/map.bin"])
    require(struct.unpack_from("<H", north, 26)[0] == 0x3323 and struct.unpack_from("<H", north, 8)[0] == 0x721,
            "North closure/own wall source changed")
    struct.pack_into("<H", north, 26, 0x3721)
    files["data/layouts/Route206_North/map.bin"] = bytes(north)
    city = json.loads(base[CITY])
    require(not city["connections"], "City already has an external connection")
    city["connections"] = [dict(map="MAP_ROUTE207", offset=35, direction="up")]
    files[CITY] = encode(city)
    known = {h["id"] for h in headers.values()} | {"MAP_OREBURGH_CITY"}
    for h in headers.values():
        require(all(w["dest_map"] in known for w in h["warp_events"]), "unbuilt production warp")
        require(all(c["map"] in known for c in h["connections"]), "unbuilt production connection")
    groups = json.loads(base[GROUPS]); names = groups["gMapGroup_Sinnoh"]
    require(len(names) == 41 and not set(SLOTS) & set(names), "exact production41 prefix required")
    groups["gMapGroup_Sinnoh"] = names + SLOTS
    files[GROUPS] = encode(groups)
    layouts = json.loads(base[LAYOUTS])
    bank_specs = [("primary", "AveronRoute206Primary", "General", "eterna_dev_outdoorprimary"),
                  ("secondary", "AveronRoute206Secondary", "Rustboro", "eterna_dev_outdoorsecondary"),
                  ("primary", "AveronRoute206GatePrimary", "Building", "eterna_dev_gateprimary"),
                  ("secondary", "AveronRoute206GateSecondary", "Shop", "eterna_dev_gatesecondary"),
                  ("secondary", "AveronCoronetSouthSecondary", "Cave", "packet_d_south")]
    tails = {p: "" for p in ("include/tilesets.h", "src/data/tilesets/headers.h", "src/data/tilesets/metatiles.h")}
    for bank, symbol, graphics, old_folder in bank_specs:
        folder = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", symbol).lower()
        path = f"data/tilesets/{bank}/{folder}/"
        for filename in ("metatiles.bin", "metatile_attributes.bin"):
            files[path + filename] = source[f"data/tilesets/{bank}/{old_folder}/{filename}"]
        block = re.search(r"const struct Tileset gTileset_" + graphics + r" =\s*\{(.*?)\};", base["src/data/tilesets/headers.h"].decode(), re.S)
        require(block is not None, "existing graphics binding absent")
        bind = {key: re.search(r"\." + key + r"\s*=\s*(\w+)\s*,", block[1])[1] for key in ("tiles", "palettes", "callback")}
        tails["include/tilesets.h"] += f"extern const struct Tileset gTileset_{symbol};\n"
        tails["src/data/tilesets/metatiles.h"] += f'const u16 gMetatiles_{symbol}[] = INCBIN_U16("{path}metatiles.bin");\nconst u16 gMetatileAttributes_{symbol}[] = INCBIN_U16("{path}metatile_attributes.bin");\n'
        tails["src/data/tilesets/headers.h"] += f'const struct Tileset gTileset_{symbol} = {{ .isCompressed=TRUE, .isSecondary={"TRUE" if bank == "secondary" else "FALSE"}, .tiles={bind["tiles"]}, .palettes={bind["palettes"]}, .metatiles=gMetatiles_{symbol}, .metatileAttributes = gMetatileAttributes_{symbol}, .callback={bind["callback"]} }};\n'
    pairs = [("AveronRoute206GatePrimary", "AveronRoute206GateSecondary"),
             ("AveronRoute206Primary", "AveronRoute206Secondary"),
             ("AveronRoute206GatePrimary", "AveronRoute206GateSecondary"),
             ("AveronOreburghCityPrimary", "AveronOreburghCitySecondary"),
             ("AveronRoute206Primary", "AveronCoronetSouthSecondary")]
    for name, (w, h), (primary, secondary) in zip(SLOTS, DIMENSIONS, pairs):
        require(not any(l["id"] == headers[name]["layout"] for l in layouts["layouts"]), "layout identity collision")
        require(len(files[f"data/layouts/{name}/map.bin"]) == w*h*2 and (w+15)*(h+14) <= 10240, "invalid map footprint")
        layouts["layouts"].append(dict(id=headers[name]["layout"], name=name+"_Layout", width=w, height=h,
            primary_tileset="gTileset_"+primary, secondary_tileset="gTileset_"+secondary,
            border_filepath=f"data/layouts/{name}/border.bin", blockdata_filepath=f"data/layouts/{name}/map.bin"))
    files[LAYOUTS] = encode(layouts)
    for path, tail in tails.items():
        if path == "include/tilesets.h":
            marker = b"#endif //GUARD_tilesets_H"
            require(base[path].count(marker) == 1, "tileset include guard changed")
            files[path] = base[path].replace(marker, tail.encode() + b"\n" + marker, 1)
        else:
            files[path] = base[path] + tail.encode()
    files["data/event_scripts.s"] = base["data/event_scripts.s"] + "".join(f'\t.include "data/maps/{n}/scripts.inc"\n' for n in SLOTS).encode()
    group = groups["group_order"].index("gMapGroup_Sinnoh")
    registry = base[REGISTRY].decode().replace(f"REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 41, 1)", f"REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 46, 1)")
    registry += "".join(f'REGISTRY_SLOT({group}, {i}, {headers[n]["id"]}, {n}, 1)\n' for i, n in enumerate(SLOTS, 41))
    files[REGISTRY] = registry.encode()
    sections = json.loads(base[SECTION_PATH]); sections["map_sections"] += copy.deepcopy(SECTIONS)
    files[SECTION_PATH] = encode(sections)
    pins = json.loads(base[PINS]); pins["pins"].update({x["id"]: x["value"] for x in SECTIONS})
    files[PINS] = encode(pins)
    for path in ("test/averon_northern_location.c", "test/averon_sandgem_location.c", "test/averon_oreburgh_location.c"):
        require(base[path].count(b"MAPSEC_COUNT == 228") == 1, "legacy native count contract changed")
        files[path] = base[path].replace(b"MAPSEC_COUNT == 228", b"MAPSEC_COUNT == 231")
    path = "test/averon_location_compatibility.c"
    text = base[path].decode(); needle = "|| section == MAPSEC_OREBURGH_CITY"
    require(text.count(needle) == 2, "legacy valid/name contract changed")
    files[path] = text.replace(needle, needle + " || section == MAPSEC_ROUTE_206 || section == MAPSEC_ROUTE_207 || section == MAPSEC_MT_CORONET").encode()
    files["test/averon_packet_d_location.c"] = NATIVE.encode()
    return files


def baseline(engine):
    """Permit a pristine pre-D tree or a byte-exact installed D tree, not a stale prefix."""
    engine = Path(engine)
    raw = {p: target(engine, p).read_bytes() for p in BASE_HASHES}
    if all(sha(raw[p]) == h for p, h in BASE_HASHES.items()):
        return raw
    # Undo only this install's exact metadata edits, then require every original
    # input hash. This works in shallow checkouts without fetching old commits.
    # No geometry or historical source is reconstructed.
    base = dict(raw)
    groups = json.loads(raw[GROUPS]); names = groups["gMapGroup_Sinnoh"]
    require(len(names) == 46 and names[41:] == SLOTS, "expected installed46 registry")
    groups["gMapGroup_Sinnoh"] = names[:41]; base[GROUPS] = encode(groups)
    layouts = json.loads(raw[LAYOUTS])
    require([x["name"] for x in layouts["layouts"][-5:]] == [n+"_Layout" for n in SLOTS], "installed D layout tail differs")
    layouts["layouts"] = layouts["layouts"][:-5]; base[LAYOUTS] = encode(layouts)
    sections = json.loads(raw[SECTION_PATH])
    require(sections["map_sections"][-3:] == SECTIONS, "installed D section tail differs")
    sections["map_sections"] = sections["map_sections"][:-3]; base[SECTION_PATH] = encode(sections)
    pins = json.loads(raw[PINS])
    for section in SECTIONS:
        require(pins["pins"].pop(section["id"], None) == section["value"], "installed D identity pin differs")
    base[PINS] = encode(pins)
    city = json.loads(raw[CITY])
    require(city["connections"] == [dict(map="MAP_ROUTE207", offset=35, direction="up")], "installed City connection differs")
    city["connections"] = []; base[CITY] = encode(city)
    source = accepted_source()
    group = groups["group_order"].index("gMapGroup_Sinnoh")
    tail = "".join(f'REGISTRY_SLOT({group}, {i}, {json.loads(source[f"data/maps/{n}/map.json"])["id"]}, {n}, 1)\n' for i, n in enumerate(SLOTS, 41)).encode()
    require(raw[REGISTRY].endswith(tail), "installed slot pins differ")
    base[REGISTRY] = raw[REGISTRY][:-len(tail)].replace(f"REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 46, 1)".encode(), f"REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 41, 1)".encode())
    tail = "".join(f'\t.include "data/maps/{n}/scripts.inc"\n' for n in SLOTS).encode()
    require(raw["data/event_scripts.s"].endswith(tail), "installed include tail differs")
    base["data/event_scripts.s"] = raw["data/event_scripts.s"][:-len(tail)]
    for path, marker in (("include/tilesets.h", b"extern const struct Tileset gTileset_AveronRoute206Primary;"),
                         ("src/data/tilesets/headers.h", b"const struct Tileset gTileset_AveronRoute206Primary ="),
                         ("src/data/tilesets/metatiles.h", b"const u16 gMetatiles_AveronRoute206Primary[] =")):
        require(raw[path].count(marker) == 1, "installed tileset declaration differs")
        if path == "include/tilesets.h":
            start = raw[path].index(marker)
            end = raw[path].index(b"#endif //GUARD_tilesets_H", start)
            base[path] = raw[path][:start] + raw[path][end:]
        else:
            base[path] = raw[path].split(marker, 1)[0]
    for path in ("test/averon_northern_location.c", "test/averon_sandgem_location.c", "test/averon_oreburgh_location.c"):
        require(raw[path].count(b"MAPSEC_COUNT == 231") == 1, "installed count fixture differs")
        base[path] = raw[path].replace(b"MAPSEC_COUNT == 231", b"MAPSEC_COUNT == 228")
    extra = b" || section == MAPSEC_ROUTE_206 || section == MAPSEC_ROUTE_207 || section == MAPSEC_MT_CORONET"
    path = "test/averon_location_compatibility.c"
    require(raw[path].count(extra) == 2, "installed valid/name fixture differs")
    base[path] = raw[path].replace(extra, b"")
    require(all(sha(base[p]) == h for p, h in BASE_HASHES.items()), "pinned baseline blobs differ")
    expected = additions(base, source)
    require(all(raw[p] == expected.get(p, base[p]) for p in BASE_HASHES), "production41/installed46 baseline differs")
    return base


def plan(engine):
    for path, expected in ASSET_HASHES.items():
        raw = target(engine, path).read_bytes()
        if path.endswith(".pal"):
            raw = raw.replace(b"\r\n", b"\n")
        require(sha(raw) == expected, "existing graphics/palette dependency changed: " + path)
    base = baseline(engine)
    return additions(base, accepted_source())


def check(engine):
    files = plan(engine)
    return [p for p, raw in files.items() if not target(engine, p).is_file() or target(engine, p).read_bytes() != raw]


def install(engine):
    engine = Path(engine).resolve()
    require(all(sha(target(engine, p).read_bytes()) == h for p, h in BASE_HASHES.items()), "exact clean production41 inputs required")
    files = plan(engine)
    require(all(p in BASE_HASHES or not target(engine, p).exists() for p in files), "refusing existing/untracked D outputs")
    # All inputs/output paths are checked before the first write.
    targets = {p: target(engine, p) for p in files}
    for p, raw in files.items():
        targets[p].parent.mkdir(parents=True, exist_ok=True)
        targets[p].write_bytes(raw)
    return files


NATIVE = '''#include "global.h"
#include "test/test.h"
#include "overworld.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"
STATIC_ASSERT(MAPSEC_ROUTE_206 == 228, packet_d_route206_fixed);
STATIC_ASSERT(MAPSEC_ROUTE_207 == 229, packet_d_route207_fixed);
STATIC_ASSERT(MAPSEC_MT_CORONET == 230, packet_d_coronet_fixed);
STATIC_ASSERT(MAPSEC_COUNT == 231, packet_d_only_approved_origins);
TEST("Averon packet D production map slots and section meanings are append only")
{
    const u32 maps[] = {MAP_ROUTE206_NORTH,MAP_ROUTE206,MAP_ROUTE206_SOUTH,MAP_ROUTE207,MAP_MT_CORONET_1F_SOUTH};
    const u32 sections[] = {228,228,228,229,230};
    for (u32 i=0;i<ARRAY_COUNT(maps);i++)
    {
        const struct MapHeader *h=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(maps[i]),MAP_NUM(maps[i]));
        EXPECT_EQ(MAP_GROUP(maps[i]),76); EXPECT_EQ(MAP_NUM(maps[i]),41+i);
        EXPECT_EQ(h->regionMapSectionId,sections[i]);
    }
}
TEST("Averon packet D retains west Coronet return and closes unbuilt north east and upper ports")
{
    const struct MapHeader *s=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_MT_CORONET_1F_SOUTH),MAP_NUM(MAP_MT_CORONET_1F_SOUTH));
    const struct MapHeader *n=Overworld_GetMapHeaderByGroupAndId(MAP_GROUP(MAP_ROUTE206_NORTH),MAP_NUM(MAP_ROUTE206_NORTH));
    EXPECT_EQ(s->events->warpCount,1); EXPECT_EQ(s->events->warps[0].mapNum,MAP_NUM(MAP_ROUTE207));
    EXPECT_EQ(s->events->warps[0].warpId,0); EXPECT_EQ(s->mapLayout->map[299],0x321a);
    EXPECT_EQ(s->mapLayout->map[876],0x3604); EXPECT_EQ(s->mapLayout->map[113],0x3604);
    EXPECT_EQ(n->events->warpCount,1); EXPECT_EQ(n->mapLayout->map[13],0x3721);
}
'''


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        errors = check(args.engine)
        if errors:
            raise SystemExit("\n".join(errors))
        print("OK: production D matches accepted source and approved228-230 records")
    else:
        files = install(args.engine)
        print("Installed %d files; production acceptance is still required" % len(files))
