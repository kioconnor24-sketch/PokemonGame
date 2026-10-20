#!/usr/bin/env python3
"""Verity Lakefront + Lake Verity from LiderMorti00's donor geometry (one connected batch).

Source: LiderMorti00/Sinnoh-pokeemerald-expansion @ 38228bb574a3557345852b758d5f1a65eb01bb22, read through
scripts/sinnoh-donor-map-pilot.py's read_donor_map (PR #176) and checked against the pinned git blobs below.
Both maps are drawn with Averon's own gTileset_General + gTileset_Dewford (no donor art; General untouched).

What the conversion does (all of it is listed here and asserted):
- primary metatiles keep their IDs (attribute words match Averon's General except ID 3, layer type only,
  and ID 510, which Averon defines as pond water under a tree canopy where the donor says normal);
- every donor secondary (Petalburg) metatile is replaced by its Averon General equivalent (SECONDARY);
- SEAM_EDITS make the Lakefront east edge walk-reciprocal with the built Route 201 west edge at offset -1,
  and open the top of the donor's L-ledge so every Lakefront exit is reachable on foot (ledges stay one-way);
- the island cave mouth (MB_NON_ANIMATED_DOOR, no warp: story-reserved) gets its collision bit set;
- collision/elevation bits are otherwise the donor's, cell for cell.
The tunnel entrances use step-on triggers (one `warp` line each): Averon's banks have no north arrow warp.
Excluded: all donor objects, coord/story events, hidden items, scripts, music, flags and map/section IDs.

  build_verity.py --donor-root DONOR --stage DIR   off-engine: writes both map.bin files + a receipt
  build_verity.py --donor-root DONOR --engine      writes into ../../../../engine (needs Route 202 / section 219)
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import shutil
import struct

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = HERE.parents[3] / "engine"
spec = importlib.util.spec_from_file_location("pilot", HERE.parents[3] / "scripts/sinnoh-donor-map-pilot.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)

REVISION = "38228bb574a3557345852b758d5f1a65eb01bb22"
MAPS = {  # donor name -> (Averon map id, layout id, width, height, git blob)
    "VerityLakefront": ("MAP_VERITY_LAKEFRONT", "LAYOUT_VERITY_LAKEFRONT", 20, 20, "916c66be28572f75c70af7a0ff25bcec17a78c05"),
    "LakeVerity": ("MAP_LAKE_VERITY", "LAYOUT_LAKE_VERITY", 48, 46, "1fba9218763961d1e2298f404d2bed0ed6a13c41"),
}
# Donor Petalburg metatile -> Averon General metatile. Tree quarters become Averon tree halves in the same
# 2-wide phase as their neighbours; tunnel floors become grass (the warp is a step-on trigger); the two
# canopy-over-shore corners become the plain vertical shore tile above them.
SECONDARY = {
    589: 478, 590: 479, 597: 470, 598: 471, 605: 486, 606: 487,   # tree pair over the Lakefront tunnel
    619: 486, 620: 487, 621: 470, 622: 471,                       # Lakefront tunnel sides
    624: 478, 625: 479, 628: 470, 629: 471,                       # Lake tunnel top and sides
    574: 1, 575: 1, 626: 1,                                       # tunnel floors (warp cells)
    532: 204, 533: 203,                                           # canopy-over-shore corners
}
# Lakefront east edge vs built Route 201 west edge (Route 201 walkable rows 8-11 and 13-14, ledge 12).
# At offset -1 (Lakefront row = Route 201 row - 1) the ledges meet; these edits make walkability exact.
GRASS = 1 | (3 << 12)          # grass, elevation 3, no collision
BUSH = 22 | (1 << 10) | (3 << 12)
SEAM_EDITS = {  # (x, y): (expected donor cell, new cell)
    (18, 7): (462 | (3 << 12), GRASS), (19, 7): (463 | (3 << 12), GRASS),   # remove the edge tree...
    (18, 8): (470 | (1 << 10), GRASS), (19, 8): (471 | (1 << 10), GRASS),
    (18, 9): (486 | (1 << 10), GRASS), (19, 9): (487 | (1 << 10), GRASS),   # ...so rows 7-9 meet R201 8-10
    (19, 6): (1 | (3 << 12), BUSH),                                         # faces a Route 201 tree
    (19, 14): (1 | (3 << 12), BUSH),                                        # faces a Route 201 tree
    (19, 15): (463 | (3 << 12), 463 | (1 << 10) | (3 << 12)),               # canopy kept, now solid
    # Access: the donor's L-shaped ledge makes the upper-east pocket one-way (enter from Route 201, jump out).
    # Opening its top cell lets the lake entrance reach that seam on foot; both ledges remain shortcuts.
    (6, 6): (254 | (1 << 10), GRASS), (6, 7): (133 | (1 << 10), 254 | (1 << 10)),
}
CAVE = (23, 19)
WARPS = {"MAP_VERITY_LAKEFRONT": [(2, 4), (3, 4)], "MAP_LAKE_VERITY": [(38, 43), (39, 43)]}
OTHER = {"MAP_VERITY_LAKEFRONT": "MAP_LAKE_VERITY", "MAP_LAKE_VERITY": "MAP_VERITY_LAKEFRONT"}
NAME = {"MAP_VERITY_LAKEFRONT": "VerityLakefront", "MAP_LAKE_VERITY": "LakeVerity"}


def git_blob(raw):
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def convert(donor):
    out, receipt = {}, {"donor": pilot.DONOR_URL, "revision": REVISION, "maps": {}}
    for name, (map_id, _, w, h, blob) in MAPS.items():
        header, layout, raw, blocks = pilot.read_donor_map(donor, name)
        assert git_blob(raw) == blob and (layout["width"], layout["height"]) == (w, h), name
        cells = list(blocks)
        for i, cell in enumerate(cells):
            mid = cell & 1023
            if mid >= 512:
                cells[i] = (cell & 0xFC00) | SECONDARY[mid]
        if name == "VerityLakefront":
            for (x, y), (was, new) in SEAM_EDITS.items():
                assert cells[y * w + x] == was, (x, y, cells[y * w + x])
                cells[y * w + x] = new
        else:
            x, y = CAVE
            assert cells[y * w + x] & 1023 == 167 and not cells[y * w + x] & (3 << 10)
            cells[y * w + x] |= 1 << 10
        assert all(c & 1023 < 512 for c in cells), "a donor secondary metatile survived"
        changed = [i for i, (a, b) in enumerate(zip(blocks, cells)) if a != b]
        for i in changed:  # only the listed seam/cave cells may change collision or elevation
            if (blocks[i] ^ cells[i]) & 0xFC00:
                assert (name == "VerityLakefront" and (i % w, i // w) in SEAM_EDITS) or (i % w, i // w) == CAVE, i
        data = struct.pack("<%dH" % len(cells), *cells)
        out[map_id] = data
        receipt["maps"][map_id] = {"source": name, "git_blob": blob, "source_sha256": hashlib.sha256(raw).hexdigest(),
                                   "output_sha256": hashlib.sha256(data).hexdigest(), "changed_cells": len(changed)}
    return out, receipt


def dump(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def header(map_id, connections, warps, bg):
    other = OTHER[map_id]
    name = NAME[map_id]
    return {
        "id": map_id, "name": name, "layout": MAPS[name][1], "music": "MUS_ROUTE101", "region": "REGION_SINNOH",
        "region_map_section": "MAPSEC_LAKE_VERITY", "weather": "WEATHER_SUNNY", "map_type": "MAP_TYPE_ROUTE",
        "allow_cycling": True, "allow_escaping": False, "allow_running": True, "show_map_name": True,
        "requires_flash": False, "battle_scene": "MAP_BATTLE_SCENE_NORMAL", "connections": connections,
        "object_events": [],
        "warp_events": [{"x": x, "y": y, "elevation": 0, "dest_map": other, "dest_warp_id": str(i)}
                        for i, (x, y) in enumerate(warps)],
        "coord_events": [{"type": "trigger", "x": x, "y": y, "elevation": 0, "var": "VAR_TEMP_1", "var_value": "0",
                          "script": f"{name}_EventScript_ToWarp{i}"} for i, (x, y) in enumerate(warps)],
        "bg_events": bg}


def scripts(map_id, extra=""):
    name, other = NAME[map_id], OTHER[map_id]
    text = f"{name}_MapScripts::\n\t.byte 0\n"
    for i in range(2):
        # Measured in mGBA: without waitstate the trigger ends before the warp runs and the player stays put.
        text += f"\n{name}_EventScript_ToWarp{i}::\n\twarp {other}, {i}\n\twaitstate\n\tend\n"
    return text + extra


def install(donor):
    blocks, receipt = convert(donor)
    for name, (map_id, layout_id, w, h, _) in MAPS.items():
        lay = ENGINE / "data/layouts" / name
        if lay.exists():
            raise SystemExit(name + " already present")
    lj = ENGINE / "data/layouts/layouts.json"
    layouts = json.loads(lj.read_text())
    mg = ENGINE / "data/maps/map_groups.json"
    groups = json.loads(mg.read_text())
    assert groups["gMapGroup_Sinnoh"][-1] == "Route202", groups["gMapGroup_Sinnoh"]
    for name, (map_id, layout_id, w, h, _) in MAPS.items():
        lay = ENGINE / "data/layouts" / name
        lay.mkdir(parents=True)
        (lay / "map.bin").write_bytes(blocks[map_id])
        shutil.copyfile(ENGINE / "data/layouts/SandgemTown/border.bin", lay / "border.bin")
        layouts["layouts"].append({
            "id": layout_id, "name": f"{name}_Layout", "width": w, "height": h,
            "primary_tileset": "gTileset_General", "secondary_tileset": "gTileset_Dewford",
            "border_filepath": f"data/layouts/{name}/border.bin", "blockdata_filepath": f"data/layouts/{name}/map.bin",
            "layout_version": "emerald"})
        groups["gMapGroup_Sinnoh"].append(name)
    dump(lj, layouts)
    dump(mg, groups)

    lf, lake = ENGINE / "data/maps/VerityLakefront", ENGINE / "data/maps/LakeVerity"
    lf.mkdir()
    lake.mkdir()
    sign = [{"type": "sign", "x": 1, "y": 6, "elevation": 0, "player_facing_dir": "BG_EVENT_PLAYER_FACING_ANY",
             "script": "VerityLakefront_EventScript_Sign"}]
    assert struct.unpack_from("<H", blocks["MAP_VERITY_LAKEFRONT"], (6 * 20 + 1) * 2)[0] & 1023 == 3
    dump(lf / "map.json", header("MAP_VERITY_LAKEFRONT",
                                 [{"map": "MAP_ROUTE201", "offset": -1, "direction": "right"}],
                                 WARPS["MAP_VERITY_LAKEFRONT"], sign))
    (lf / "scripts.inc").write_text(scripts("MAP_VERITY_LAKEFRONT",
        "\nVerityLakefront_EventScript_Sign::\n\tmsgbox VerityLakefront_Text_Sign, MSGBOX_SIGN\n\tend\n"
        '\nVerityLakefront_Text_Sign:\n\t.string "LAKE VERITY$"\n'))
    dump(lake / "map.json", header("MAP_LAKE_VERITY", [], WARPS["MAP_LAKE_VERITY"], []))
    (lake / "scripts.inc").write_text(scripts("MAP_LAKE_VERITY"))

    rj = ENGINE / "data/maps/Route201/map.json"
    route = json.loads(rj.read_text())
    assert not any(c["direction"] == "left" for c in route["connections"])
    route["connections"].append({"map": "MAP_VERITY_LAKEFRONT", "offset": 1, "direction": "left"})
    dump(rj, route)

    es = ENGINE / "data/event_scripts.s"
    text = es.read_text()
    anchor = '\t.include "data/maps/Route202/scripts.inc"\n'
    assert text.count(anchor) == 1
    es.write_text(text.replace(anchor, anchor + '\t.include "data/maps/VerityLakefront/scripts.inc"\n'
                                                '\t.include "data/maps/LakeVerity/scripts.inc"\n'))
    return receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor-root", type=pathlib.Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage", type=pathlib.Path)
    mode.add_argument("--engine", action="store_true")
    args = parser.parse_args()
    if args.stage:
        if "engine" in args.stage.resolve().parts:
            raise SystemExit("--stage must be outside engine/")
        blocks, receipt = convert(args.donor_root)
        args.stage.mkdir(parents=True, exist_ok=True)
        for map_id, data in blocks.items():
            (args.stage / f"{NAME[map_id]}.bin").write_bytes(data)
    else:
        receipt = install(args.donor_root)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
