#!/usr/bin/env python3
"""Route 205 South from LiderMorti00's donor geometry, drawn with Averon's own banks (OFF-ENGINE staging).

Source: LiderMorti00/Sinnoh-pokeemerald-expansion @ 38228bb574a3557345852b758d5f1a65eb01bb22,
data/layouts/Route205_South/map.bin, read through scripts/sinnoh-donor-map-pilot.py's read_donor_map (PR #176),
git blob checked. Banks: Averon gTileset_General + gTileset_Mauville (unchanged; no donor art).

Conversion, every change listed and asserted:
- primary IDs are kept. Their attribute words match Averon's except 3 (sign, layer type) and 148/156/164, which
  are MB_SIDEWAYS_STAIRS_RIGHT_SIDE in the donor: Averon's General has no metatile with that behavior, so the
  3-cell stair at (19, 60-62) is plain walkable ground (elevation 0 still joins the levels; no stair animation);
- every donor Mauville (secondary) ID is replaced by an Averon tile with the SAME movement behavior (SECONDARY),
  except the south plank bridge (NORMAL, elevation 3 in the donor), drawn with Averon's log bridge, whose
  behavior is MB_BRIDGE_OVER_OCEAN. Crossing is governed by the kept elevation-3/no-collision bits, so walking
  over it is unchanged and a surfer (elevation 1) still cannot pass under it (checked in mGBA);
- the Eterna Forest tunnel is sealed with Averon tree halves (Eterna Forest is not built); its warps are dropped;
- the house is replaced by the Averon house template door-on-door (closed shell; no interior yet);
- collision/elevation bits are the donor's, cell for cell, except the sealed tunnel (solid).
Connections in the corridor batch: Floaroma Town (left, +64). Route 205 North (up) and Valley Windworks (right)
stay closed. Excluded: donor trainers/NPCs (16 objects), 24 coord events, hidden item, scripts, music, IDs.

  build_route205.py --donor-root DONOR --stage DIR      map.bin + map.json/scripts.inc (section pending owner)
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
spec = importlib.util.spec_from_file_location("floaroma", HERE.parent / "floaroma-donor/build_floaroma.py")
floaroma = importlib.util.module_from_spec(spec)
spec.loader.exec_module(floaroma)   # reuses its asserted Averon building templates

REVISION = "38228bb574a3557345852b758d5f1a65eb01bb22"
NAME, W, H, BLOB = "Route205_South", 32, 96, "569eaa93e653697627c3b0534ea012cdd6b60ece"
PENDING = "MAPSEC_PENDING_OWNER"
GRASS = 1 | (3 << 12)
# Donor Mauville ID -> Averon tile with the same behavior (General unless noted).
SECONDARY = {
    # south garden fences and the riverbank rail (NORMAL, solid)
    566: 329, 944: 312, 945: 314, 946: 306, 947: 307,
    # south plank bridge, 3 wide (NORMAL, elevation 3): Averon Mauville log bridge (see the docstring)
    956: 706, 957: 707, 958: 708, 948: 706, 949: 707, 950: 708,
    # north log bridge: same IDs, same behavior (MB_BRIDGE_OVER_OCEAN) and log art in Averon's Mauville
    706: 706, 707: 707, 708: 708, 714: 714, 715: 715, 716: 716,
    940: 213, 941: 135, 942: 214,     # MB_JUMP_SOUTH ledge: left end, middle, right end
    935: 13,                          # MB_TALL_GRASS
    926: 113,                         # MB_MOUNTAIN_TOP
    925: 136, 927: 138, 933: 137, 934: 121,   # small rock mounds (NORMAL, solid)
    932: 268,                         # cliff-top strip: the donor's own surrounding floor tile
    924: 121,                         # shore rock (NORMAL)
}
TUNNEL_IDS = {539, 540, 541, 542, 543, 547, 548, 549, 550, 557, 565, 567}   # sealed with tree halves
HOUSE = (19, 19, 23, 22, 21, 22, "house")
SIGNS = [(17, 18), (23, 85)]


def git_blob(raw):
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def tree_half(x, y):
    left = x % 2 == 0
    return (470 if left else 471) if y % 2 == 0 else (478 if left else 479)


def convert(donor):
    header, layout, raw, blocks = pilot.read_donor_map(donor, NAME)
    assert git_blob(raw) == BLOB and (layout["width"], layout["height"]) == (W, H)
    cells, owned = list(blocks), set()
    for i, c in enumerate(blocks):
        mid = c & 1023
        if mid in TUNNEL_IDS:
            x, y = i % W, i // W
            cells[i] = (c & 0xF000) | (1 << 10) | tree_half(x, y)
            owned.add((x, y))
        elif mid >= 512:
            cells[i] = (c & 0xFC00) | SECONDARY[mid]
    x0, y0, x1, y1, dx, dy, kind = HOUSE
    block, ddx, ddy, _ = floaroma.template(kind)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            cells[y * W + x] = GRASS
            owned.add((x, y))
    for j, row in enumerate(block):
        for i, c in enumerate(row):
            cells[(dy - ddy + j) * W + dx - ddx + i] = c
    for x, y in SIGNS:
        assert cells[y * W + x] & 1023 == 3, (x, y)
    survived = sorted({c & 1023 for i, c in enumerate(cells) if c & 1023 >= 512 and (i % W, i // W) not in owned}
                      - set(SECONDARY.values()))   # owned cells hold the Averon house template's own Mauville IDs
    assert not survived, survived
    for i, (a, b) in enumerate(zip(blocks, cells)):
        if (i % W, i // W) not in owned:
            assert (a ^ b) & 0xFC00 == 0, i          # collision/elevation kept outside the sealed/rebuilt cells
    data = struct.pack("<%dH" % len(cells), *cells)
    return data, {"donor": pilot.DONOR_URL, "revision": REVISION, "map": NAME, "git_blob": BLOB,
                  "source_sha256": hashlib.sha256(raw).hexdigest(), "output_sha256": hashlib.sha256(data).hexdigest(),
                  "changed_cells": sum(a != b for a, b in zip(blocks, cells)),
                  "excluded_donor_warps": [(e["x"], e["y"], e["dest_map"]) for e in header["warp_events"]]}


def headers(section):
    info = {
        "id": "MAP_ROUTE205_SOUTH", "name": NAME, "layout": "LAYOUT_ROUTE205_SOUTH", "music": "MUS_ROUTE101",
        "region": "REGION_SINNOH", "region_map_section": section, "weather": "WEATHER_SUNNY", "map_type": "MAP_TYPE_ROUTE",
        "allow_cycling": True, "allow_escaping": False, "allow_running": True, "show_map_name": True,
        "requires_flash": False, "battle_scene": "MAP_BATTLE_SCENE_NORMAL",
        "connections": [{"map": "MAP_FLOAROMA_TOWN", "offset": 64, "direction": "left"}],
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
