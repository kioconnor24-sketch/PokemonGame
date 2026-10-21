#!/usr/bin/env python3
"""Route 204 + Ravaged Path from LiderMorti00's donor geometry (OFF-ENGINE staging; claim #15 6284624908).

Source: LiderMorti00/Sinnoh-pokeemerald-expansion @ 38228bb574a3557345852b758d5f1a65eb01bb22, read through
scripts/sinnoh-donor-map-pilot.py's read_donor_map (PR #176) and checked against the pinned git blobs below.
Drawn with Averon's own banks: Route 204 on gTileset_General + gTileset_Rustboro, Ravaged Path on
gTileset_General + gTileset_Cave (all 32 Ravaged Path metatiles are record- and attribute-identical to
Averon's Cave, whose tiles.png is byte-identical to the donor's).

Conversion (every change listed and asserted):
- primary metatiles keep their IDs (attribute words differ only on 3, layer type; 215; 510), except the
  two fence junctions 438 and 215, whose Averon art is blank/rock, which become the fence post below them;
- the four donor Rustboro metatiles Route 204 uses become Averon General equivalents (SECONDARY);
- collision/elevation bits are the donor's, cell for cell, except ACCESS_EDITS (one unenterable door).
Warps are engine-native (cave doors on Route 204, south arrow warps in Ravaged Path): the donor's two pairs.
Both Route 204 ends stay closed: Jubilife (south) is Codex's staged #184 and Floaroma (north) is unbuilt.
Excluded: donor trainers/NPCs/items (15 + 2 objects), scripts, music, flags and map/section IDs.

  build_route204.py --donor-root DONOR --stage DIR
      off-engine: both map.bin files plus production map headers/scripts with the section left as
      MAPSEC_PENDING_OWNER (no permanent identity is chosen here)
  build_route204.py --donor-root DONOR --engine --section Route204=MAPSEC_A --section RavagedPath=MAPSEC_B
      production install; refuses unless both sections ALREADY exist in region_map_sections.json, so
      allocating them stays a separate, owner-approved edit
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import shutil
import struct

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pilot", HERE.parents[3] / "scripts/sinnoh-donor-map-pilot.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)

REVISION = "38228bb574a3557345852b758d5f1a65eb01bb22"
MAPS = {  # donor name -> (width, height, git blob, Averon secondary bank)
    "Route204": (32, 64, "fcc49242b015046580e62d6b9a400c41c8fac226", "gTileset_Rustboro"),
    "RavagedPath": (32, 45, "0940999d1e557750867fbe3e1c83131ed866849d", "gTileset_Cave"),
}
# Donor Rustboro metatile -> Averon General metatile, by the donor's own neighbouring tiles.
SECONDARY = {
    "Route204": {
        798: 320, 799: 322,   # fence bottom corners -> the fence verticals directly above them
        774: 186,             # canopy-over-shore corners -> the vertical shore above them
        704: 2,               # pond south edge -> the shore-edge tile the donor uses just left of it
        # Two primary fence junctions whose Averon art differs (438 is blank, 215 is rock): the post below.
        438: 322, 215: 320,   # used once each, at (9, 1) and (13, 0)
    },
    "RavagedPath": {},        # its Cave metatiles are identical to Averon's: kept as they are
}
# Access fix measured in mGBA: the donor's north cave door carries the collision bit, so stepping into it
# from its doorstep does nothing. Its twin door (11, 31) has no collision bit. Clear it.
# Seam fix for the corridor: Route 204's top row has walkable grass (x 4-7, above a fence) and one flower
# cell (x 21) facing Floaroma's tree line at the -2 offset (static seam-mismatch). They become solid bushes.
BUSH = 22 | (1 << 10) | (3 << 12)
ACCESS_EDITS = {"Route204": {(19, 24): (167 | (1 << 10), 167),
                             (4, 0): (0x3001, BUSH), (5, 0): (0x3001, BUSH), (6, 0): (0x3001, BUSH),
                             (7, 0): (0x3001, BUSH), (21, 0): (0x3004, BUSH),
                             # (8, 0) was then a one-tile nook reachable only from Floaroma's (10, 35): both solid.
                             (8, 0): (0x3001, BUSH)}}


def git_blob(raw):
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def convert(donor):
    out, receipt = {}, {"donor": pilot.DONOR_URL, "revision": REVISION, "maps": {}}
    for name, (w, h, blob, secondary) in MAPS.items():
        header, layout, raw, blocks = pilot.read_donor_map(donor, name)
        assert git_blob(raw) == blob and (layout["width"], layout["height"]) == (w, h), name
        remap = SECONDARY[name]
        cells = [(c & 0xFC00) | remap.get(c & 1023, c & 1023) for c in blocks]
        for (x, y), (was, new) in ACCESS_EDITS.get(name, {}).items():
            assert cells[y * w + x] == was, (name, x, y, cells[y * w + x])
            cells[y * w + x] = new
        if name == "Route204":
            assert all(c & 1023 < 512 and c & 1023 not in (438, 215) for c in cells), "an unmapped metatile survived"
        fixed = {y * w + x for x, y in ACCESS_EDITS.get(name, {})}
        assert all((a ^ b) & 0xFC00 == 0 for i, (a, b) in enumerate(zip(blocks, cells)) if i not in fixed), "collision changed"
        data = struct.pack("<%dH" % len(cells), *cells)
        out[name] = data
        receipt["maps"][name] = {"git_blob": blob, "source_sha256": hashlib.sha256(raw).hexdigest(),
                                 "output_sha256": hashlib.sha256(data).hexdigest(), "secondary": secondary,
                                 "changed_cells": sum(a != b for a, b in zip(blocks, cells)),
                                 "warps": [(e["x"], e["y"], e["dest_map"], e["dest_warp_id"]) for e in header["warp_events"]]}
    return out, receipt


ENGINE = HERE.parents[3] / "engine"
PENDING = "MAPSEC_PENDING_OWNER"
HEADER = {  # donor name -> (map id, layout id, map type, music, weather, escape)
    "Route204": ("MAP_ROUTE204", "LAYOUT_ROUTE204", "MAP_TYPE_ROUTE", "MUS_ROUTE101", "WEATHER_SUNNY", False),
    "RavagedPath": ("MAP_RAVAGED_PATH", "LAYOUT_RAVAGED_PATH", "MAP_TYPE_UNDERGROUND", "MUS_CAVE_OF_ORIGIN", "WEATHER_NONE", False),
}
SIGNS = {"Route204": [(17, 7), (10, 32), (4, 39), (14, 48)], "RavagedPath": []}  # the donor's sign cells (metatile 3)
# Edge connections inside the corridor batch (Route 204 -> Floaroma -> Meadow, staged together under
# floaroma-donor/): Route 204's north path meets Floaroma's south path at the donor's -2 / +2 offsets.
# The south edge (Jubilife, Codex #184) stays closed. Install this batch together.
CONNECTIONS = {"Route204": [{"map": "MAP_FLOAROMA_TOWN", "offset": -2, "direction": "up"}], "RavagedPath": []}


def headers(donor, blocks, sections):
    """map.json + scripts.inc per map: the donor's two reciprocal warp pairs, neutral signs, the corridor's
    Floaroma connection (CONNECTIONS), no objects/coord events/hidden items/encounters."""
    out = {}
    for name, (map_id, layout_id, kind, music, weather, escape) in HEADER.items():
        donor_header = pilot.read_donor_map(donor, name)[0]
        w = MAPS[name][0]
        for x, y in SIGNS[name]:
            assert struct.unpack_from("<H", blocks[name], (y * w + x) * 2)[0] & 1023 == 3, (name, x, y)
        info = {
            "id": map_id, "name": name, "layout": layout_id, "music": music, "region": "REGION_SINNOH",
            "region_map_section": sections[name], "weather": weather, "map_type": kind, "allow_cycling": kind == "MAP_TYPE_ROUTE",
            "allow_escaping": escape, "allow_running": True, "show_map_name": True, "requires_flash": False,
            "battle_scene": "MAP_BATTLE_SCENE_NORMAL", "connections": CONNECTIONS[name], "object_events": [], "coord_events": [],
            "warp_events": [{"x": e["x"], "y": e["y"], "elevation": e["elevation"], "dest_map": e["dest_map"],
                             "dest_warp_id": str(e["dest_warp_id"])} for e in donor_header["warp_events"]],
            "bg_events": [{"type": "sign", "x": x, "y": y, "elevation": 0, "player_facing_dir": "BG_EVENT_PLAYER_FACING_ANY",
                           "script": f"{name}_EventScript_Sign"} for x, y in SIGNS[name]]}
        assert {e["dest_map"] for e in info["warp_events"]} <= {h[0] for h in HEADER.values()}, name
        text = f"{name}_MapScripts::\n\t.byte 0\n"
        if SIGNS[name]:
            text += (f"\n{name}_EventScript_Sign::\n\tmsgbox {name}_Text_Sign, MSGBOX_SIGN\n\tend\n"
                     f'\n{name}_Text_Sign:\n\t.string "ROUTE 204$"\n')
        out[name] = (json.dumps(info, indent=2) + "\n", text)
    return out


def install(donor, sections):
    known = {s["id"] for s in json.loads((ENGINE / "src/data/region_map/region_map_sections.json").read_text())["map_sections"]}
    missing = [s for s in sections.values() if s not in known]
    if missing:
        raise SystemExit(f"sections not allocated yet (owner decision): {missing}")
    songs = (ENGINE / "include/constants/songs.h").read_text()
    for music in {h[3] for h in HEADER.values()}:
        if f"#define {music} " not in songs:
            raise SystemExit(f"unknown music constant {music}")
    blocks, receipt = convert(donor)
    staged = headers(donor, blocks, sections)
    lj, mg = ENGINE / "data/layouts/layouts.json", ENGINE / "data/maps/map_groups.json"
    layouts, groups = json.loads(lj.read_text()), json.loads(mg.read_text())
    last = groups["gMapGroup_Sinnoh"][-1]
    for name, (w, h, _, secondary) in MAPS.items():
        lay, md = ENGINE / "data/layouts" / name, ENGINE / "data/maps" / name
        if lay.exists() or md.exists():
            raise SystemExit(name + " already present")
        lay.mkdir(parents=True)
        md.mkdir()
        (lay / "map.bin").write_bytes(blocks[name])
        shutil.copyfile(ENGINE / "data/layouts/SandgemTown/border.bin", lay / "border.bin")
        layouts["layouts"].append({"id": HEADER[name][1], "name": f"{name}_Layout", "width": w, "height": h,
                                   "primary_tileset": "gTileset_General", "secondary_tileset": secondary,
                                   "border_filepath": f"data/layouts/{name}/border.bin",
                                   "blockdata_filepath": f"data/layouts/{name}/map.bin", "layout_version": "emerald"})
        groups["gMapGroup_Sinnoh"].append(name)
        (md / "map.json").write_text(staged[name][0])
        (md / "scripts.inc").write_text(staged[name][1])
    lj.write_text(json.dumps(layouts, indent=2) + "\n")
    mg.write_text(json.dumps(groups, indent=2) + "\n")
    es = ENGINE / "data/event_scripts.s"
    text = es.read_text()
    anchor = f'\t.include "data/maps/{last}/scripts.inc"\n'
    assert text.count(anchor) == 1, anchor
    es.write_text(text.replace(anchor, anchor + "".join(f'\t.include "data/maps/{n}/scripts.inc"\n' for n in MAPS)))
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor-root", type=pathlib.Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage", type=pathlib.Path)
    mode.add_argument("--engine", action="store_true")
    parser.add_argument("--section", action="append", default=[], metavar="MAP=MAPSEC_ID")
    args = parser.parse_args()
    if args.engine:
        sections = dict(s.split("=", 1) for s in args.section)
        if set(sections) != set(MAPS):
            raise SystemExit("--engine needs --section for each of " + ", ".join(MAPS))
        print(json.dumps(install(args.donor_root, sections), indent=2))
        return
    if "engine" in args.stage.resolve().parts:
        raise SystemExit("--stage must be outside engine/")
    blocks, receipt = convert(args.donor_root)
    args.stage.mkdir(parents=True, exist_ok=True)
    for name, data in blocks.items():
        (args.stage / f"{name}.bin").write_bytes(data)
        info, text = headers(args.donor_root, blocks, {n: PENDING for n in MAPS})[name]
        (args.stage / name).mkdir(exist_ok=True)
        (args.stage / name / "map.json").write_text(info)
        (args.stage / name / "scripts.inc").write_text(text)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
