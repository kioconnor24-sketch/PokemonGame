#!/usr/bin/env python3
"""Compose several Codex DEV family scenes into one (DEV only; for testing joins between families).

Each family's prepare_runtime.assemble(repo) appends to the same main files. Composition keeps every map/layout/art
file (each must belong to one family only), concatenates the families' appends to the text index files, merges
map_groups.json/layouts.json structurally and renumbers the registry slot list in final order. Any other overlap,
a non-append change to an index file, or a tileset symbol declared twice fails closed.
"""
import importlib.util
import json
import pathlib
import re

ENGINE = "Pokemon Game/engine/"
DESIGN = "Pokemon Game/Averon_Codex_Handoff/design/sinnoh/"
APPEND = ("data/event_scripts.s", "include/tilesets.h", "src/data/tilesets/headers.h", "src/data/tilesets/metatiles.h")
GROUPS, LAYOUTS, REGISTRY = "data/maps/map_groups.json", "data/layouts/layouts.json", "test/data/averon_map_registry_slots.inc"


def family_files(repo, family):
    module = family if family.endswith(".py") else family + "/prepare_runtime.py"
    spec = importlib.util.spec_from_file_location("fam_" + re.sub(r"\W", "_", family), repo / DESIGN / module)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.assemble(repo)[0]


def assemble(repo, families):
    repo = pathlib.Path(repo)
    eng = repo / ENGINE
    base = {p: (eng / p).read_bytes() for p in APPEND + (GROUPS, LAYOUTS, REGISTRY)}
    parts = [family_files(repo, f) for f in families]
    files, owner = {}, {}
    for fam, part in zip(families, parts):
        for path, data in part.items():
            if path in base:
                continue
            if path in files and files[path] != data:
                raise ValueError(f"{path} differs between {owner[path]} and {fam}")
            files[path], owner[path] = data, fam
    for path in APPEND:
        extras = []
        for fam, part in zip(families, parts):
            data = part.get(path, base[path])
            if not data.startswith(base[path]):
                raise ValueError(f"{fam} does not append to {path}")
            extras.append(data[len(base[path]):])
        files[path] = base[path] + b"".join(extras)
    pattern = rb"^(?:extern )?const struct Tileset (\w+)"
    declared = re.findall(pattern, files["include/tilesets.h"][len(base["include/tilesets.h"]):], re.M)
    if len(declared) != len(set(declared)) or set(declared) & set(re.findall(pattern, base["include/tilesets.h"], re.M)):
        raise ValueError("a tileset is declared twice")
    groups, layouts = json.loads(base[GROUPS]), json.loads(base[LAYOUTS])
    prefix, layout_prefix = list(groups["gMapGroup_Sinnoh"]), len(layouts["layouts"])
    lines = {}
    for fam, part in zip(families, parts):
        g, l = json.loads(part[GROUPS]), json.loads(part[LAYOUTS])
        if g["gMapGroup_Sinnoh"][:len(prefix)] != prefix or l["layouts"][:layout_prefix] != layouts["layouts"][:layout_prefix]:
            raise ValueError(f"{fam} changed existing map or layout entries")
        added = g["gMapGroup_Sinnoh"][len(prefix):]
        if set(added) & set(groups["gMapGroup_Sinnoh"]):
            raise ValueError(f"{fam} registers a map twice")
        groups["gMapGroup_Sinnoh"] += added
        layouts["layouts"] += l["layouts"][layout_prefix:]
        for line in part[REGISTRY].decode().splitlines():
            m = re.match(r"REGISTRY_SLOT\((\d+), \d+, (\w+), (\w+), 1\)$", line)
            if m and m.group(3) in added:
                lines[m.group(3)] = (m.group(1), m.group(2))
    ids = [x["id"] for x in layouts["layouts"]]
    if len(ids) != len(set(ids)):
        raise ValueError("a layout is registered twice")
    files[GROUPS] = (json.dumps(groups, indent=2) + "\n").encode()
    files[LAYOUTS] = (json.dumps(layouts, indent=2) + "\n").encode()
    registry = base[REGISTRY].decode()
    group = groups["group_order"].index("gMapGroup_Sinnoh")
    marker = f"REGISTRY_GROUP({group}, gMapGroup_Sinnoh, {len(prefix)}, 1)"
    if registry.count(marker) != 1:
        raise ValueError("registry count differs from main")
    registry = registry.replace(marker, f"REGISTRY_GROUP({group}, gMapGroup_Sinnoh, {len(groups['gMapGroup_Sinnoh'])}, 1)")
    for slot, name in enumerate(groups["gMapGroup_Sinnoh"][len(prefix):], len(prefix)):
        g, mid = lines[name]
        registry += f"REGISTRY_SLOT({g}, {slot}, {mid}, {name}, 1)\n"
    files[REGISTRY] = registry.encode()
    return files, {"families": families, "maps": groups["gMapGroup_Sinnoh"][len(prefix):]}
