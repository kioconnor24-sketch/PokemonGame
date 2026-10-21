#!/usr/bin/env python3
"""Reuse Claude's six staged maps in an explicitly disposable connected test tree.

This is NOT a production installer. Pending saved identities stay pending in the
published staging. Only the throwaway ROM uses existing Sinnoh section217 as a
surrogate name; no section is allocated, no save encoding is changed, and its
generated saves must never become production saves or acceptance of origin names.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
MAPS = (
    ("route204-donor", "Route204", 32, 64, "gTileset_AveronCorridorRustboro"),
    ("route204-donor", "RavagedPath", 32, 45, "gTileset_Cave"),
    ("floaroma-donor", "FloaromaTown", 34, 36, "gTileset_Mauville"),
    ("floaroma-donor", "FloaromaMeadow", 60, 60, "gTileset_Mauville"),
    ("route205-donor", "Route205_South", 32, 96, "gTileset_Mauville"),
    ("route205-donor", "Route205_North", 80, 60, "gTileset_Mauville"),
)


def prepare(repo):
    repo = Path(repo).resolve()
    engine = repo / "Pokemon Game/engine"
    branch = subprocess.check_output(["git", "-C", str(repo), "branch", "--show-current"], text=True).strip()
    if not branch.startswith("codex/north-scratch-") or not (engine / ".map_qa_throwaway").is_file():
        raise ValueError("explicit codex/north-scratch-* branch and disposable engine marker required")
    groups_path = engine / "data/maps/map_groups.json"
    layouts_path = engine / "data/layouts/layouts.json"
    groups = json.loads(groups_path.read_text())
    layouts = json.loads(layouts_path.read_text())
    names = groups["gMapGroup_Sinnoh"]
    required = {"JubilifeCity", "Route203", "OreburghGate_1F", "LakeVerity", "VerityLakefront"}
    if not required <= set(names):
        raise ValueError("reconciled Verity and six-map Jubilife corridor required first")
    if any(name in names for _, name, *_ in MAPS):
        raise ValueError("northern corridor already registered")
    sections_path = engine / "src/data/region_map/region_map_sections.json"
    sections_before = sections_path.read_bytes()
    sections = json.loads(sections_before)["map_sections"]
    if next(row for row in sections if row["id"] == "MAPSEC_ROUTE_201").get("value") != 217:
        raise ValueError("existing Sinnoh surrogate must retain section217")
    if any(row.get("value", 0) >= 224 for row in sections):
        raise ValueError("refresh the owner decision before using this frozen placeholder experiment")
    city_header_path = engine / "data/maps/JubilifeCity/map.json"
    city_header = json.loads(city_header_path.read_text())
    if any(c["direction"] == "up" for c in city_header["connections"]):
        raise ValueError("Jubilife north connection already exists")
    city_path = engine / "data/layouts/JubilifeCity/map.bin"
    city_before = city_path.read_bytes()
    city = bytearray(city_before)
    if len(city) != 70 * 64 * 2:
        raise ValueError("unexpected Jubilife dimensions")
    # Source-pinned donor offsets are +36/-36. Its separate east pocket cannot
    # reach the corridor's exits on foot. Expose the four-cell main path only;
    # keep City's pocket shut and visibly close the corresponding Route204 edge.
    opening = (48, 49, 50, 51)
    for x in opening:
        if int.from_bytes(city[2*x:2*x+2], "little") != 0x3401:
            raise ValueError(f"Jubilife north closure changed at ({x},0)")
        city[2*x:2*x+2] = (0x3001).to_bytes(2, "little")
    staged = []
    for area, name, width, height, secondary in MAPS:
        source = HERE.parent / area / "staged"
        raw = (source / (name + ".bin")).read_bytes()
        header = json.loads((source / name / "map.json").read_text())
        scripts = (source / name / "scripts.inc").read_bytes()
        if len(raw) != 2 * width * height or header["region_map_section"] != "MAPSEC_PENDING_OWNER":
            raise ValueError("invalid pending staging: " + name)
        if header["object_events"]:
            raise ValueError("unexpected gameplay objects: " + name)
        if (engine / "data/maps" / name).exists() or (engine / "data/layouts" / name).exists():
            raise ValueError("refusing to overwrite " + name)
        header["region_map_section"] = "MAPSEC_ROUTE_201"
        if name == "Route204":
            cells = bytearray(raw)
            for x in (22, 23):
                offset = 2 * (63 * width + x)
                if int.from_bytes(cells[offset:offset+2], "little") != 0x3001:
                    raise ValueError("Route204 isolated south pocket changed")
                cells[offset:offset+2] = (0x3416).to_bytes(2, "little")
            raw = bytes(cells)
            header["connections"].append({"map": "MAP_JUBILIFE_CITY", "offset": -36, "direction": "down"})
        staged.append((name, width, height, secondary, raw, header, scripts))
    pins_path = engine / "test/data/averon_map_registry_slots.inc"
    pins = pins_path.read_text()
    group_index = groups["group_order"].index("gMapGroup_Sinnoh")
    original = f"REGISTRY_GROUP({group_index}, gMapGroup_Sinnoh, {len(names)}, 1)"
    if pins.count(original) != 1:
        raise ValueError("registry golden disagrees with source")
    pins = pins.replace(original, f"REGISTRY_GROUP({group_index}, gMapGroup_Sinnoh, {len(names)+len(MAPS)}, 1)")
    if not re.search(r"const struct Tileset gTileset_AveronCorridorRustboro", (engine / "src/data/tilesets/headers.h").read_text()):
        raise ValueError("existing corridor graphics bank required")

    # Every precondition above precedes writes. Reuse map bytes, never reconvert.
    includes, receipt = [], []
    for index, (name, width, height, secondary, raw, header, scripts) in enumerate(staged, len(names)):
        md, ld = engine / "data/maps" / name, engine / "data/layouts" / name
        md.mkdir(); ld.mkdir()
        (md / "map.json").write_text(json.dumps(header, indent=2) + "\n")
        (md / "scripts.inc").write_bytes(scripts)
        (ld / "map.bin").write_bytes(raw)
        border = "GraniteCave_1F" if name == "RavagedPath" else "SandgemTown"
        shutil.copyfile(engine / "data/layouts" / border / "border.bin", ld / "border.bin")
        layouts["layouts"].append(dict(id=header["layout"], name=name + "_Layout", width=width, height=height,
            primary_tileset="gTileset_General", secondary_tileset=secondary, layout_version="emerald",
            border_filepath=f"data/layouts/{name}/border.bin", blockdata_filepath=f"data/layouts/{name}/map.bin"))
        names.append(name)
        pins += f"REGISTRY_SLOT({group_index}, {index}, {header['id']}, {name}, 1)\n"
        includes.append(f'\t.include "data/maps/{name}/scripts.inc"')
        receipt.append(dict(name=name, sha256=hashlib.sha256(raw).hexdigest(), group=group_index, slot=index))
    city_header["connections"].append({"map": "MAP_ROUTE204", "offset": 36, "direction": "up"})
    city_header_path.write_text(json.dumps(city_header, indent=2) + "\n")
    city_path.write_bytes(city)
    groups_path.write_text(json.dumps(groups, indent=2) + "\n")
    layouts_path.write_text(json.dumps(layouts, indent=2) + "\n")
    pins_path.write_text(pins)
    with (engine / "data/event_scripts.s").open("a") as fp:
        fp.write("\n" + "\n".join(includes) + "\n")
    assert sections_path.read_bytes() == sections_before
    return dict(status="DISPOSABLE_SOURCE_ONLY_NOT_PRODUCTION", branch=branch, maps=receipt,
        surrogate="MAPSEC_ROUTE_201 (217), not an owner allocation or production origin-name acceptance",
        city_opened=[(x, 0) for x in opening], city_before_sha256=hashlib.sha256(city_before).hexdigest(),
        city_after_sha256=hashlib.sha256(city).hexdigest(), route204_closed=[(22, 63), (23, 63)],
        sections_unchanged=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.repo), indent=2))
