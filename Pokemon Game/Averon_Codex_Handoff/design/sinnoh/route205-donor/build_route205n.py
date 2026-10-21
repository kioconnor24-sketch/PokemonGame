#!/usr/bin/env python3
"""Route 205 North from LiderMorti00's donor geometry, drawn with Averon's own banks (OFF-ENGINE staging).

Source: LiderMorti00/Sinnoh-pokeemerald-expansion @ 38228bb574a3557345852b758d5f1a65eb01bb22,
data/layouts/Route205_North/map.bin (80 x 60), read through scripts/sinnoh-donor-map-pilot.py's read_donor_map
(PR #176), git blob checked. The donor draws it with a donor-only gTileset_Jubilife, which Averon does not have;
it is drawn with Averon's gTileset_General + gTileset_Mauville (as Route 205 South, so the shared seam is drawn
consistently). No donor art; the shared banks are not modified.

Conversion, every change listed and asserted:
- primary IDs are kept. Attribute words match Averon's except 3 (layer), 171/172 (layer) and 147/155/163, the
  donor's MB_SIDEWAYS_STAIRS_LEFT_SIDE: Averon's General has no sideways stair, so that 3-cell stair is plain
  walkable ground (elevation bits kept, so it still joins the levels);
- the donor Jubilife IDs become Averon tiles with the same movement behavior (WALKWAY / EDGE below);
- the Eterna Forest gatehouse (x 43-46, rows 9-12, two west arrow warps) is sealed with Averon tree halves:
  Eterna Forest is not built. Its warps are dropped;
- collision/elevation bits are the donor's outside the sealed gatehouse.
Connections in the corridor batch: Route 205 South (down, -20). Valley Windworks (down, +9) and Eterna City
(right) stay closed. Excluded: 8 objects (trainers/NPCs), hidden item, scripts, music and IDs.
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pilot", HERE.parents[3] / "scripts/sinnoh-donor-map-pilot.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)

REVISION = "38228bb574a3557345852b758d5f1a65eb01bb22"
NAME, W, H, BLOB = "Route205_North", 80, 60, "733624c009545b6f78e59aa233337eb35429cca9"
PENDING = "MAPSEC_PENDING_OWNER"
# Walkable plank walkway (NORMAL, elevation 3) -> Averon path pieces (NORMAL) by position in the band.
WALKWAY = {840: 281, 848: 289, 856: 297,              # horizontal band rows 16-18: top edge / middle / bottom
           857: 288, 849: 289, 850: 289, 851: 290, 858: 290}   # vertical band x 60-62: left / middle / right
# Cliff-edge pieces 516/517 (NORMAL): solid ones -> Averon rock 137, walkable ones -> the donor's own floor 268.
EDGE = {516, 517}
GATEHOUSE = {(x, y) for x in range(43, 47) for y in range(9, 13)}
SIGNS = [(70, 18), (79, 16), (50, 9)]


def git_blob(raw):
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def tree_half(x, y):
    left = x % 2 == 0
    return (470 if left else 471) if y % 2 == 0 else (478 if left else 479)


def convert(donor):
    header, layout, raw, blocks = pilot.read_donor_map(donor, NAME)
    assert git_blob(raw) == BLOB and (layout["width"], layout["height"]) == (W, H)
    cells = list(blocks)
    for i, c in enumerate(blocks):
        x, y, mid = i % W, i // W, c & 1023
        if (x, y) in GATEHOUSE:
            cells[i] = (c & 0xF000) | (1 << 10) | tree_half(x, y)
        elif mid in WALKWAY:
            cells[i] = (c & 0xFC00) | WALKWAY[mid]
        elif mid in EDGE:
            cells[i] = (c & 0xFC00) | (137 if (c >> 10) & 3 else 268)
        else:
            assert mid < 512, (x, y, mid)
    assert not {c & 1023 for c in cells if c & 1023 >= 512}
    for x, y in SIGNS:
        assert cells[y * W + x] & 1023 == 3, (x, y)
    for i, (a, b) in enumerate(zip(blocks, cells)):
        if (i % W, i // W) not in GATEHOUSE:
            assert (a ^ b) & 0xFC00 == 0, i
    data = struct.pack("<%dH" % len(cells), *cells)
    return data, {"donor": pilot.DONOR_URL, "revision": REVISION, "map": NAME, "git_blob": BLOB,
                  "source_sha256": hashlib.sha256(raw).hexdigest(), "output_sha256": hashlib.sha256(data).hexdigest(),
                  "changed_cells": sum(a != b for a, b in zip(blocks, cells)),
                  "excluded_donor_warps": [(e["x"], e["y"], e["dest_map"]) for e in header["warp_events"]]}


def headers(section):
    info = {
        "id": "MAP_ROUTE205_NORTH", "name": NAME, "layout": "LAYOUT_ROUTE205_NORTH", "music": "MUS_ROUTE101",
        "region": "REGION_SINNOH", "region_map_section": section, "weather": "WEATHER_SUNNY", "map_type": "MAP_TYPE_ROUTE",
        "allow_cycling": True, "allow_escaping": False, "allow_running": True, "show_map_name": True,
        "requires_flash": False, "battle_scene": "MAP_BATTLE_SCENE_NORMAL",
        "connections": [{"map": "MAP_ROUTE205_SOUTH", "offset": -20, "direction": "down"}],
        "object_events": [], "warp_events": [], "coord_events": [],
        "bg_events": [{"type": "sign", "x": x, "y": y, "elevation": 0, "player_facing_dir": "BG_EVENT_PLAYER_FACING_ANY",
                       "script": f"{NAME}_EventScript_Sign"} for x, y in SIGNS]}
    text = (f"{NAME}_MapScripts::\n\t.byte 0\n\n{NAME}_EventScript_Sign::\n\tmsgbox {NAME}_Text_Sign, MSGBOX_SIGN\n\tend\n"
            f'\n{NAME}_Text_Sign:\n\t.string "ROUTE 205$"\n')
    return json.dumps(info, indent=2) + "\n", text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor-root", type=pathlib.Path, required=True)
    parser.add_argument("--stage", type=pathlib.Path, required=True)
    args = parser.parse_args()
    if "engine" in args.stage.resolve().parts:
        raise SystemExit("--stage must be outside engine/")
    data, receipt = convert(args.donor_root)
    args.stage.mkdir(parents=True, exist_ok=True)
    (args.stage / f"{NAME}.bin").write_bytes(data)
    info, text = headers(PENDING)
    (args.stage / NAME).mkdir(exist_ok=True)
    (args.stage / NAME / "map.json").write_text(info)
    (args.stage / NAME / "scripts.inc").write_text(text)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
