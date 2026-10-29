"""Pinned-current W25 DEV composition; no production installer or saved origins.

Keep the legacy Oreburgh recipe immutable. Rebase its append-only registries
and explicitly reconcile the accepted B1F ladder before composing with Eterna.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import struct

HERE = Path(__file__).resolve().parent
ENGINE = "Pokemon Game/engine/"
GATE = "data/maps/OreburghGate_1F/map.json"
GROUPS = "data/maps/map_groups.json"
LAYOUTS = "data/layouts/layouts.json"
REGISTRY = "test/data/averon_map_registry_slots.inc"
APPENDS = ("data/event_scripts.s", "include/tilesets.h", "src/data/tilesets/headers.h",
           "src/data/tilesets/metatiles.h")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


legacy = load("w25_legacy_oreburgh", HERE.parent / "oreburgh-connected/prepare_current.py")
encode = legacy.frozen.encode
sha = lambda b: hashlib.sha256(b).hexdigest()


def current_inputs(repo):
    pins = json.loads((HERE / "current-runtime-base-pins.json").read_text())
    engine = Path(repo) / ENGINE
    tree = subprocess.check_output(["git", "rev-parse", "HEAD:" + ENGINE.rstrip("/")], cwd=repo).decode().strip()
    profiles = [p for p in pins["profiles"] if p["engine_tree"] == tree]
    if len(profiles) != 1:
        raise ValueError("exact pinned engine tree required")
    data = {}
    for path, expected in profiles[0]["files"].items():
        blob = subprocess.check_output(["git", "show", "HEAD:" + ENGINE + path], cwd=repo)
        if sha(blob) != expected or (engine / path).read_bytes() != blob:
            raise ValueError("current base differs: " + path)
        data[path] = blob
    return data


def rebase(files, old, current):
    """Pure bounded adaptation, preserving accepted map slots and the B1F warp."""
    result = dict(files)
    before_gate, patched_gate, live_gate = (json.loads(x[GATE]) for x in (old, files, current))
    baseline = before_gate["warp_events"]
    ladder = dict(x=18, y=5, elevation=0, dest_map="MAP_OREBURGH_GATE_B1F", dest_warp_id="0")
    if live_gate != dict(before_gate, warp_events=baseline + [ladder]):
        raise ValueError("unexpected production Gate header change")
    east = dict(x=25, y=20, elevation=0, dest_map="MAP_OREBURGH_CITY", dest_warp_id="0")
    if patched_gate != dict(before_gate, warp_events=baseline + [east]):
        raise ValueError("unexpected staged Gate header change")
    block = "data/layouts/OreburghGate_1F/map.bin"
    words = lambda raw: list(struct.unpack("<%dH" % (len(raw) // 2), raw))
    a, b, dev = (words(x[block]) for x in (old, current, files))
    if len(a) != len(b) or len(a) != len(dev):
        raise ValueError("production Gate dimensions changed")
    changed = [(i, x, y) for i, (x, y) in enumerate(zip(a, b)) if x != y]
    if changed != [(163, 0x3201, 0x323F)] or dev[163] != a[163]:
        raise ValueError("unexpected production/DEV Gate geometry change")
    dev[163] = b[163]  # accepted B1F ladder, disjoint from the DEV east restoration
    result[block] = struct.pack("<%dH" % len(dev), *dev)
    result[GATE] = encode(dict(live_gate, warp_events=live_gate["warp_events"] + [east]))
    city_path = "data/maps/OreburghCity/map.json"
    city = json.loads(result[city_path])
    returns = [w for w in city["warp_events"] if w["dest_map"] == "MAP_OREBURGH_GATE_1F"]
    if len(returns) != 1 or returns[0]["dest_warp_id"] != "1":
        raise ValueError("unexpected City return")
    returns[0]["dest_warp_id"] = "2"
    result[city_path] = encode(city)
    for path in APPENDS:
        if not files[path].startswith(old[path]):
            raise ValueError("legacy index is not append-only: " + path)
        result[path] = current[path] + files[path][len(old[path]):]
    old_groups, new_groups, live = (json.loads(x[GROUPS]) for x in (old, files, current))
    group = "gMapGroup_Sinnoh"
    if any(live[k] != v for k, v in old_groups.items() if k != group):
        raise ValueError("non-Sinnoh registry changed")
    if live[group][:len(old_groups[group])] != old_groups[group]:
        raise ValueError("legacy slot prefix changed")
    added = new_groups[group][len(old_groups[group]):]
    if len(added) != 4 or set(added) & set(live[group]) or len(live[group]) + len(added) > 256:
        raise ValueError("temporary map identity collision/capacity")
    start = len(live[group])
    live[group] += added
    result[GROUPS] = encode(live)
    old_layouts, new_layouts, layouts = (json.loads(x[LAYOUTS]) for x in (old, files, current))
    n = len(old_layouts["layouts"])
    if layouts["layouts"][:n] != old_layouts["layouts"]:
        raise ValueError("layout prefix changed")
    extra = new_layouts["layouts"][n:]
    if {l["id"] for l in extra} & {l["id"] for l in layouts["layouts"]}:
        raise ValueError("layout identity collision")
    layouts["layouts"] += extra
    result[LAYOUTS] = encode(layouts)
    index = live["group_order"].index(group)
    marker = f"REGISTRY_GROUP({index}, {group}, {start}, 1)"
    pins = current[REGISTRY].decode()
    if pins.count(marker) != 1:
        raise ValueError("registry count mismatch")
    pins = pins.replace(marker, f"REGISTRY_GROUP({index}, {group}, {start + 4}, 1)")
    for slot, name in enumerate(added, start):
        pins += f"REGISTRY_SLOT({index}, {slot}, {legacy.frozen.IDS[name]}, {name}, 1)\n"
    result[REGISTRY] = pins.encode()
    return result


CITY = "data/maps/OreburghCity/map.json"
CITY_BLOCKS = "data/layouts/OreburghCity/map.bin"
CITY_WIDTH = 70
MINE_CELLS = [(50, 57), (51, 57), (52, 57), (53, 57)]


def production_city(current):
    """True once west packet C (#337) made Oreburgh City a production map."""
    return "OreburghCity" in json.loads(current[GROUPS])["gMapGroup_Sinnoh"]


def rebase_on_production_city(files, old, current):
    """Post-packet-C adaptation: production already holds the City, its Gate east return and the B1F ladder.

    W25 then appends only Route207 and the two mine floors; a DEV-only overlay of the production City
    restores the Route207 connection and the four mine doors (appended after production's warps)."""
    result = dict(files)
    before_gate, patched_gate, live_gate = (json.loads(x[GATE]) for x in (old, files, current))
    baseline = before_gate["warp_events"]
    ladder = dict(x=18, y=5, elevation=0, dest_map="MAP_OREBURGH_GATE_B1F", dest_warp_id="0")
    east = dict(x=25, y=20, elevation=0, dest_map="MAP_OREBURGH_CITY", dest_warp_id="0")
    if live_gate != dict(before_gate, warp_events=baseline + [ladder, east]):
        raise ValueError("unexpected production Gate header change")
    if patched_gate != dict(before_gate, warp_events=baseline + [east]):
        raise ValueError("unexpected staged Gate header change")
    block = "data/layouts/OreburghGate_1F/map.bin"
    words = lambda raw: list(struct.unpack("<%dH" % (len(raw) // 2), raw))
    a, b, dev = (words(x[block]) for x in (old, current, files))
    if len(a) != len(b) or len(a) != len(dev):
        raise ValueError("production Gate dimensions changed")
    opened = [i for i, (x, y) in enumerate(zip(a, dev)) if x != y]
    if ([i for i, (x, y) in enumerate(zip(a, b)) if x != y] != sorted([163] + opened)
            or b[163] != 0x323F or any(b[i] != dev[i] for i in opened)):
        raise ValueError("unexpected production/DEV Gate geometry change")
    result[GATE], result[block] = current[GATE], current[block]   # production already equals the W25 Gate
    city, staged = json.loads(current[CITY]), json.loads(files[CITY])
    if city["connections"] or [w["dest_map"] for w in staged["warp_events"]] != ["MAP_OREBURGH_GATE_1F"] + ["MAP_OREBURGH_MINE_B1F"] * 4:
        raise ValueError("unexpected production or staged City")
    if city["warp_events"][0] != dict(staged["warp_events"][0], dest_warp_id="2"):
        raise ValueError("unexpected production City return")
    first = len(city["warp_events"])
    city["connections"] = staged["connections"]
    city["warp_events"] += staged["warp_events"][1:]
    result[CITY] = encode(city)
    prod_cells, staged_cells = words(current[CITY_BLOCKS]), words(files[CITY_BLOCKS])
    for x, y in MINE_CELLS:
        prod_cells[y * CITY_WIDTH + x] = staged_cells[y * CITY_WIDTH + x]   # DEV-only reopened mine doors
    result[CITY_BLOCKS] = struct.pack("<%dH" % len(prod_cells), *prod_cells)
    for path in ("data/layouts/OreburghCity/border.bin", "data/maps/OreburghCity/scripts.inc"):
        result.pop(path)                                                       # production keeps its own
    b1f = json.loads(files["data/maps/OreburghMine_B1F/map.json"])
    for w in b1f["warp_events"]:
        if w["dest_map"] == "MAP_OREBURGH_CITY":
            w["dest_warp_id"] = str(first - 1 + int(w["dest_warp_id"]))
    result["data/maps/OreburghMine_B1F/map.json"] = encode(b1f)
    include = '\t.include "data/maps/OreburghCity/scripts.inc"\n'
    for path in APPENDS:
        if not files[path].startswith(old[path]):
            raise ValueError("legacy index is not append-only: " + path)
        tail = files[path][len(old[path]):]
        if path == "data/event_scripts.s":
            if tail.decode().count(include) != 1:
                raise ValueError("unexpected legacy City include")
            tail = tail.decode().replace(include, "").encode()
        result[path] = current[path] + tail
    old_groups, new_groups, live = (json.loads(x[GROUPS]) for x in (old, files, current))
    group = "gMapGroup_Sinnoh"
    if any(live[k] != v for k, v in old_groups.items() if k != group):
        raise ValueError("non-Sinnoh registry changed")
    if live[group][:len(old_groups[group])] != old_groups[group]:
        raise ValueError("legacy slot prefix changed")
    added = new_groups[group][len(old_groups[group]):]
    if added[0] != "OreburghCity" or len(added) != 4:
        raise ValueError("unexpected legacy additions")
    added = added[1:]
    if set(added) & set(live[group]) or len(live[group]) + len(added) > 256:
        raise ValueError("temporary map identity collision/capacity")
    start = len(live[group])
    live[group] += added
    result[GROUPS] = encode(live)
    old_layouts, new_layouts, layouts = (json.loads(x[LAYOUTS]) for x in (old, files, current))
    n = len(old_layouts["layouts"])
    if layouts["layouts"][:n] != old_layouts["layouts"]:
        raise ValueError("layout prefix changed")
    extra = [l for l in new_layouts["layouts"][n:] if l["id"] != "LAYOUT_OREBURGH_CITY"]
    if len(extra) != 3 or {l["id"] for l in extra} & {l["id"] for l in layouts["layouts"]}:
        raise ValueError("layout identity collision")
    layouts["layouts"] += extra
    result[LAYOUTS] = encode(layouts)
    index = live["group_order"].index(group)
    marker = f"REGISTRY_GROUP({index}, {group}, {start}, 1)"
    pins = current[REGISTRY].decode()
    if pins.count(marker) != 1:
        raise ValueError("registry count mismatch")
    pins = pins.replace(marker, f"REGISTRY_GROUP({index}, {group}, {start + len(added)}, 1)")
    for slot, name in enumerate(added, start):
        pins += f"REGISTRY_SLOT({index}, {slot}, {legacy.frozen.IDS[name]}, {name}, 1)\n"
    result[REGISTRY] = pins.encode()
    return result


def assemble(repo):
    """Oreburgh family for the existing compose_scene tool; does not write."""
    current = current_inputs(repo)
    files, _ = legacy.assemble(repo)
    adapt = rebase_on_production_city if production_city(current) else rebase
    files = adapt(files, legacy.current_inputs(), current)
    return files, dict(status="DEV_ONLY_NOT_BUILD_OR_GAMEPLAY_ACCEPTANCE",
                       files={p: sha(b) for p, b in sorted(files.items())})


def compose(repo):
    """Reuse W25's exact two overlays, keeping accepted production headers."""
    composer = load("w25_composer", Path(repo) / "Pokemon Game/scripts/claude_play/compose_scene.py")
    files, receipt = composer.assemble(repo, ["eterna-cycle", "cycling-road-join/prepare_current_runtime.py"])
    join = load("w25_existing_join", HERE / "build_cycling_road_join.py")
    a, b, ca, cb, pairs, _ = join.build()
    for name, hdr, cells in (("Route206", a, ca), ("Route207", b, cb)):
        path = f"data/maps/{name}/map.json"
        existing = json.loads(files[path])
        existing["connections"] = hdr["connections"]
        files[path] = encode(existing)
        files[f"data/layouts/{name}/map.bin"] = struct.pack("<%dH" % len(cells), *cells)
    # The historical Eterna fixture predates the accepted appended maps.
    # Keep its source immutable and pin this generated expectation to the
    # independently verified production prefix, not the temporary map list.
    path = "test/averon_eterna_runtime.c"
    native = files[path].decode()
    expected = "EXPECT_EQ(MAP_NUM(maps[i]), 19+i);"
    if native.count(expected) != 1:
        raise ValueError("Eterna native fixture precondition changed")
    count = len(json.loads(current_inputs(repo)[GROUPS])["gMapGroup_Sinnoh"])
    native = native.replace(expected, f"EXPECT_EQ(MAP_NUM(maps[i]), {count}+i);")
    if production_city(current_inputs(repo)):   # approved section 227 is the one origin W25 itself does not add
        old = "STATIC_ASSERT(MAPSEC_COUNT == 227, eterna_no_new_origins);"
        if native.count(old) != 1:
            raise ValueError("Eterna native section precondition changed")
        native = native.replace(old, "STATIC_ASSERT(MAPSEC_OREBURGH_CITY == 227, eterna_only_oreburgh_added);\n"
                                     "STATIC_ASSERT(MAPSEC_COUNT == 228, eterna_no_new_origins);")
    files[path] = native.encode()
    # Adapt only the generated fixture, preserving its immutable source.
    path = "test/averon_oreburgh_candidate.c"
    native = files[path].decode()
    replacements = {
        "EXPECT_EQ(gate->warpCount, 2)": "EXPECT_EQ(gate->warpCount, 3)",
        "gate->warps[1]": "gate->warps[2]",
        "EXPECT_EQ(city->warps[0].warpId, 1)": "EXPECT_EQ(city->warps[0].warpId, 2)",
        "EXPECT_EQ(route->count, 1)": "EXPECT_EQ(route->count, 2)",
    }
    if production_city(current_inputs(repo)):   # production City: 11 warps, mine doors appended at 11-14
        replacements.update({
            "static const u8 ids[] = {1,4,0,0,0,0};": "static const u8 ids[] = {11,14,0,0,0,0};",
            "EXPECT_EQ(city->warpCount, 5);": "EXPECT_EQ(city->warpCount, 15);",
            "for (u32 i = 1; i < 5; i++)": "for (u32 i = 11; i < 15; i++)",
            "EXPECT_EQ(city->warps[i].x, 49+i);": "EXPECT_EQ(city->warps[i].x, 39+i);",
            "EXPECT_EQ(city->warps[i].warpId, i < 3 ? 0 : 1);": "EXPECT_EQ(city->warps[i].warpId, i < 13 ? 0 : 1);",
            "static const u16 maps[] = {MAP_OREBURGH_CITY,MAP_ROUTE207,": "static const u16 maps[] = {MAP_ROUTE207,",
            "EXPECT_EQ(HEADER(MAP_OREBURGH_GATE_1F)->regionMapSectionId, MAPSEC_OREBURGH_GATE);":
                "EXPECT_EQ(HEADER(MAP_OREBURGH_GATE_1F)->regionMapSectionId, MAPSEC_OREBURGH_GATE);\n"
                "    EXPECT_EQ(HEADER(MAP_OREBURGH_CITY)->regionMapSectionId, MAPSEC_OREBURGH_CITY);",
        })
    for old, new in replacements.items():
        if old not in native:
            raise ValueError("native fixture precondition changed: " + old)
        native = native.replace(old, new)
    native += '''
TEST("Averon DEV W25 retains the accepted Gate B1F ladder and northern join")
{
    const struct MapEvents *gate = HEADER(MAP_OREBURGH_GATE_1F)->events;
    const struct MapConnections *route = HEADER(MAP_ROUTE207)->connections;
    EXPECT_EQ(gate->warps[1].mapNum, MAP_NUM(MAP_OREBURGH_GATE_B1F));
    EXPECT_EQ(gate->warps[1].mapGroup, MAP_GROUP(MAP_OREBURGH_GATE_B1F));
    EXPECT_EQ(gate->warps[1].warpId, 0);
    EXPECT_EQ(gate->warps[1].x, 18); EXPECT_EQ(gate->warps[1].y, 5);
    EXPECT_EQ(route->connections[1].direction, CONNECTION_NORTH);
    EXPECT_EQ(route->connections[1].offset, 2);
    EXPECT_EQ(route->connections[1].mapNum, MAP_NUM(MAP_ROUTE206));
    EXPECT_EQ(route->connections[1].mapGroup, MAP_GROUP(MAP_ROUTE206));
}
'''
    files[path] = native.encode()
    receipt.update(status="DEV_SOURCE_ONLY_NOT_BUILD_OR_GAMEPLAY_ACCEPTANCE",
                   reopened_pairs=pairs, files={p: sha(b) for p, b in sorted(files.items())})
    return files, receipt
