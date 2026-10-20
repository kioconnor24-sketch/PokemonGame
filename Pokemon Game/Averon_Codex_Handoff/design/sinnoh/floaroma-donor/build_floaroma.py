#!/usr/bin/env python3
"""Floaroma Town from LiderMorti00's donor geometry, rebuilt with Averon-native buildings (OFF-ENGINE staging).

Source: LiderMorti00/Sinnoh-pokeemerald-expansion @ 38228bb574a3557345852b758d5f1a65eb01bb22, read through
scripts/sinnoh-donor-map-pilot.py's read_donor_map (PR #176), git blob checked. Drawn with Averon's own
gTileset_General + gTileset_Mauville; the shared banks are not modified and no donor art is used.

What is kept: the donor's street plan, flower fields, tree walls, paths, fences, signs and building
footprints/doors. The flower beds (Mauville 521/528) are record-, attribute- and pixel-identical in both banks.
What is replaced:
- each donor building (its Sinnoh-style Center, two houses, Mart, flower shop) by an Averon building TEMPLATE
  read from an existing Averon layout and asserted, stamped so its door lands on the donor's door tile;
  cells of the donor footprint the template does not cover become grass (TEMPLATES);
- the Meadow tunnel's donor Petalburg-style secondary cells by Averon General tree halves and grass. Its two
  north arrow warps become step-on warps (coord triggers), as on Verity: Averon has no north arrow warp art here.
Buildings are closed shells (no interiors yet: no door warps). Edges: Route 204 (south, +2) is in this batch;
Route 205 South (east, -64) is in the batch too. Excluded: donor NPCs, hidden item, scripts, music, flags and IDs.

  build_floaroma.py --donor-root DONOR --stage DIR     off-engine: map.bin + map.json/scripts.inc (section pending)
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = HERE.parents[3] / "engine"
spec = importlib.util.spec_from_file_location("pilot", HERE.parents[3] / "scripts/sinnoh-donor-map-pilot.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)

REVISION = "38228bb574a3557345852b758d5f1a65eb01bb22"
NAME, W, H, BLOB = "FloaromaTown", 34, 36, "0bc532f6ac4fdd6d0b57c3ed66837d56c9b473ed"
PENDING = "MAPSEC_PENDING_OWNER"
GRASS = 1 | (3 << 12)

# Averon building templates: (layout id, x0, y0, width, height, door x, door y, expected top-left metatile).
TEMPLATE_SOURCES = {
    "center": ("LAYOUT_SANDGEM_TOWN", 14, 6, 4, 4, 15, 9, 72),     # Averon's Pokemon Center (Sandgem)
    "house": ("LAYOUT_MAUVILLE_CITY", 18, 11, 4, 4, 19, 14, 643),  # Mauville house
    "mart": ("LAYOUT_MAUVILLE_CITY", 22, 11, 4, 4, 23, 14, 40),    # Mauville Mart
    "shop": ("LAYOUT_MAUVILLE_CITY", 33, 2, 6, 4, 35, 5, 642),     # Mauville bike shop (for the flower shop)
}
# Donor building: (donor footprint x0, y0, x1, y1, donor door x, y, template).
BUILDINGS = {
    "center": (16, 24, 20, 28, 18, 28, "center"),
    "house1": (12, 13, 15, 16, 13, 16, "house"),
    "house2": (25, 25, 28, 28, 26, 28, "house"),
    "mart": (25, 16, 28, 19, 26, 19, "mart"),
    "flower_shop": (20, 9, 24, 13, 22, 13, "shop"),
}
# Meadow tunnel (donor x 3-6, rows 0-3): tree halves in the neighbouring 2-wide phase, grass floor.
TUNNEL = {(3, 0): 471, (3, 1): 479, (3, 2): 471, (3, 3): 487,
          (6, 0): 470, (6, 1): 478, (6, 2): 470, (6, 3): 486,
          (4, 0): 470, (5, 0): 471, (4, 1): 486, (5, 1): 487,
          (4, 2): 1, (5, 2): 1, (4, 3): 1, (5, 3): 1}
MEADOW_WARPS = [(4, 2), (5, 2)]
SIGNS = [(19, 13), (31, 17), (15, 20)]
# Seam with Route 204 (+2): (10, 35) faced a one-tile nook at Route 204 (8, 0) beside the path fence; both become
# solid bushes (Route 204's side is in route204-donor ACCESS_EDITS).
SEAM_EDITS = {(10, 35): (1 | (3 << 12), 22 | (1 << 10) | (3 << 12))}
KEPT_SECONDARY = {521, 528}  # flower beds: identical in both banks


def git_blob(raw):
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def template(kind):
    lid, x0, y0, w, h, dx, dy, first = TEMPLATE_SOURCES[kind]
    layout = next(l for l in json.loads((ENGINE / "data/layouts/layouts.json").read_text())["layouts"] if l.get("id") == lid)
    lw = layout["width"]
    cells = struct.unpack("<%dH" % (lw * layout["height"]), (ENGINE / layout["blockdata_filepath"]).read_bytes())
    block = [[cells[(y0 + j) * lw + x0 + i] for i in range(w)] for j in range(h)]
    assert block[0][0] & 1023 == first, (kind, block[0][0] & 1023)
    return block, dx - x0, dy - y0, layout["secondary_tileset"]


def convert(donor):
    header, layout, raw, blocks = pilot.read_donor_map(donor, NAME)
    blob = git_blob(raw)
    assert blob == BLOB, (blob, BLOB)
    assert (layout["width"], layout["height"]) == (W, H), NAME
    cells = list(blocks)
    owned = set()
    for name, (x0, y0, x1, y1, door_x, door_y, kind) in BUILDINGS.items():
        block, ddx, ddy, secondary = template(kind)
        assert secondary in ("gTileset_Mauville", "gTileset_Dewford"), secondary
        if secondary == "gTileset_Dewford":  # the Center is primary-only, so it is valid with Mauville too
            assert all(c & 1023 < 512 for row in block for c in row), kind
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                cells[y * W + x] = GRASS
                owned.add((x, y))
        tx, ty = door_x - ddx, door_y - ddy
        for j, row in enumerate(block):
            for i, c in enumerate(row):
                cells[(ty + j) * W + tx + i] = c
                owned.add((tx + i, ty + j))
    for (x, y), mid in TUNNEL.items():
        cells[y * W + x] = (blocks[y * W + x] & 0xFC00) | mid
        owned.add((x, y))
    for (x, y), (was, new) in SEAM_EDITS.items():
        assert cells[y * W + x] == was, (x, y, hex(cells[y * W + x]))
        cells[y * W + x] = new
        owned.add((x, y))
    for x, y in SIGNS:
        assert cells[y * W + x] & 1023 == 3, (x, y)
    left = sorted({c & 1023 for (i, c) in enumerate(cells) if c & 1023 >= 512 and (i % W, i // W) not in owned})
    assert set(left) <= KEPT_SECONDARY, left
    for i, (a, b) in enumerate(zip(blocks, cells)):
        if (i % W, i // W) not in owned:
            assert a == b, i
    data = struct.pack("<%dH" % len(cells), *cells)
    receipt = {"donor": pilot.DONOR_URL, "revision": REVISION, "map": NAME, "git_blob": blob,
               "source_sha256": hashlib.sha256(raw).hexdigest(), "output_sha256": hashlib.sha256(data).hexdigest(),
               "changed_cells": sum(a != b for a, b in zip(blocks, cells)), "buildings": sorted(BUILDINGS),
               "excluded_donor_warps": [(e["x"], e["y"], e["dest_map"]) for e in header["warp_events"]
                                        if (e["x"], e["y"]) not in MEADOW_WARPS]}
    return data, receipt


def headers(data, section):
    info = {
        "id": "MAP_FLOAROMA_TOWN", "name": NAME, "layout": "LAYOUT_FLOAROMA_TOWN", "music": "MUS_LILYCOVE",
        "region": "REGION_SINNOH", "region_map_section": section, "weather": "WEATHER_SUNNY", "map_type": "MAP_TYPE_TOWN",
        "allow_cycling": True, "allow_escaping": False, "allow_running": True, "show_map_name": True,
        "requires_flash": False, "battle_scene": "MAP_BATTLE_SCENE_NORMAL",
        "connections": [{"map": "MAP_ROUTE204", "offset": 2, "direction": "down"},
                        {"map": "MAP_ROUTE205_SOUTH", "offset": -64, "direction": "right"}],
        "object_events": [],
        "warp_events": [{"x": x, "y": y, "elevation": 0, "dest_map": "MAP_FLOAROMA_MEADOW", "dest_warp_id": str(i)}
                        for i, (x, y) in enumerate(MEADOW_WARPS)],
        "coord_events": [{"type": "trigger", "x": x, "y": y, "elevation": 0, "var": "VAR_TEMP_1", "var_value": "0",
                          "script": f"{NAME}_EventScript_ToMeadow{i}"} for i, (x, y) in enumerate(MEADOW_WARPS)],
        "bg_events": [{"type": "sign", "x": x, "y": y, "elevation": 0, "player_facing_dir": "BG_EVENT_PLAYER_FACING_ANY",
                       "script": f"{NAME}_EventScript_Sign"} for x, y in SIGNS]}
    text = f"{NAME}_MapScripts::\n\t.byte 0\n"
    for i in range(len(MEADOW_WARPS)):
        text += f"\n{NAME}_EventScript_ToMeadow{i}::\n\twarp MAP_FLOAROMA_MEADOW, {i}\n\twaitstate\n\tend\n"
    text += (f"\n{NAME}_EventScript_Sign::\n\tmsgbox {NAME}_Text_Sign, MSGBOX_SIGN\n\tend\n"
             f'\n{NAME}_Text_Sign:\n\t.string "FLOAROMA TOWN$"\n')
    return json.dumps(info, indent=2) + "\n", text


# ---------------------------------------------------------------- Floaroma Meadow (60 x 60)
MEADOW, MW, MH, MEADOW_BLOB = "FloaromaMeadow", 60, 60, "6ed0b03973020ca45fca8442c70f5cafaaa67c72"
MEADOW_HOUSE = (33, 38, 37, 41, 35, 41, "house")       # closed shell (no interior yet)
MEADOW_WARPS_IN = [(10, 50), (11, 50)]                  # the SW tunnel back to the town: Town warps 0/1


def tree_half(x, y, top_rows_even=True):
    """Averon General tree half in the 2-wide/2-tall phase used around these tunnels (left halves at even x)."""
    left = x % 2 == 0
    top = (y % 2 == 0) == top_rows_even
    return (470 if left else 471) if top else (478 if left else 479)


def convert_meadow(donor):
    header, layout, raw, blocks = pilot.read_donor_map(donor, MEADOW)
    assert git_blob(raw) == MEADOW_BLOB and (layout["width"], layout["height"]) == (MW, MH)
    cells, owned = list(blocks), set()
    # SW tunnel: tree halves either side, grass floor (rows 49-50), a bush back wall (row 51).
    for y in (49, 50, 51):
        for x in (9, 12):
            cells[y * MW + x] = (blocks[y * MW + x] & 0xFC00) | tree_half(x, y)
            owned.add((x, y))
        for x in (10, 11):
            cells[y * MW + x] = (blocks[y * MW + x] & 0xFC00) | (22 if y == 51 else 1)
            owned.add((x, y))
    # NE tunnel and its two pillars: the donor warps them into this same map (a placeholder) -> sealed trees.
    ne = [(47, y) for y in range(4, 7)] + [(50, y) for y in range(4, 7)] + [(x, y) for x in range(47, 51) for y in range(8, 12)]
    for x, y in ne:
        mid = (486 if x % 2 == 0 else 487) if y == 11 else tree_half(x, y)
        cells[y * MW + x] = (blocks[y * MW + x] & 0xF000) | (1 << 10) | mid
        owned.add((x, y))
    # The house: an Averon house on the donor's door.
    x0, y0, x1, y1, dx, dy, kind = MEADOW_HOUSE
    block, ddx, ddy, _ = template(kind)
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            cells[y * MW + x] = GRASS
            owned.add((x, y))
    for j, row in enumerate(block):
        for i, c in enumerate(row):
            cells[(dy - ddy + j) * MW + dx - ddx + i] = c
    left = sorted({c & 1023 for (i, c) in enumerate(cells) if c & 1023 >= 512 and (i % MW, i // MW) not in owned})
    assert not left, left
    for i, (a, b) in enumerate(zip(blocks, cells)):
        if (i % MW, i // MW) not in owned:
            assert a == b, i
    data = struct.pack("<%dH" % len(cells), *cells)
    receipt = {"map": MEADOW, "git_blob": MEADOW_BLOB, "source_sha256": hashlib.sha256(raw).hexdigest(),
               "output_sha256": hashlib.sha256(data).hexdigest(), "changed_cells": sum(a != b for a, b in zip(blocks, cells)),
               "excluded_donor_warps": [(e["x"], e["y"], e["dest_map"]) for e in header["warp_events"]
                                        if (e["x"], e["y"]) not in MEADOW_WARPS_IN]}
    return data, receipt


def meadow_headers(section):
    info = {
        "id": "MAP_FLOAROMA_MEADOW", "name": MEADOW, "layout": "LAYOUT_FLOAROMA_MEADOW", "music": "MUS_LILYCOVE",
        "region": "REGION_SINNOH", "region_map_section": section, "weather": "WEATHER_SUNNY", "map_type": "MAP_TYPE_ROUTE",
        "allow_cycling": True, "allow_escaping": False, "allow_running": True, "show_map_name": True,
        "requires_flash": False, "battle_scene": "MAP_BATTLE_SCENE_NORMAL", "connections": [], "object_events": [],
        "warp_events": [{"x": x, "y": y, "elevation": 0, "dest_map": "MAP_FLOAROMA_TOWN", "dest_warp_id": str(i)}
                        for i, (x, y) in enumerate(MEADOW_WARPS_IN)],
        "coord_events": [{"type": "trigger", "x": x, "y": y, "elevation": 0, "var": "VAR_TEMP_1", "var_value": "0",
                          "script": f"{MEADOW}_EventScript_ToTown{i}"} for i, (x, y) in enumerate(MEADOW_WARPS_IN)],
        "bg_events": []}
    text = f"{MEADOW}_MapScripts::\n\t.byte 0\n"
    for i in range(len(MEADOW_WARPS_IN)):
        text += f"\n{MEADOW}_EventScript_ToTown{i}::\n\twarp MAP_FLOAROMA_TOWN, {i}\n\twaitstate\n\tend\n"
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
    info, text = headers(data, PENDING)
    (args.stage / NAME).mkdir(exist_ok=True)
    (args.stage / NAME / "map.json").write_text(info)
    (args.stage / NAME / "scripts.inc").write_text(text)
    mdata, mreceipt = convert_meadow(args.donor_root)
    (args.stage / f"{MEADOW}.bin").write_bytes(mdata)
    info, text = meadow_headers(PENDING)
    (args.stage / MEADOW).mkdir(exist_ok=True)
    (args.stage / MEADOW / "map.json").write_text(info)
    (args.stage / MEADOW / "scripts.inc").write_text(text)
    print(json.dumps({"town": receipt, "meadow": mreceipt}, indent=2))


if __name__ == "__main__":
    main()
