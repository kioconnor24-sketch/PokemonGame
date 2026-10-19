#!/usr/bin/env python3
"""Write Route 202 into the engine tree from the donor-converted block file (run once; refuses if present).

Source: LiderMorti00/Sinnoh-pokeemerald-expansion @ 38228bb574a3557345852b758d5f1a65eb01bb22,
data/layouts/Route202/map.bin (git blob 25c724524810a7a188d30947cb885a4e5e44e8b9), staged by
scripts/sinnoh-donor-map-pilot.py (PR #176) with route202-remap.json -> route202-convert-receipt.json.
Only the 30x34 block geometry is imported; it is drawn with Averon's own gTileset_General (no donor art).
Donor events, trainers, NPCs, hidden item, scripts, music and connections are NOT imported.

Approvals: owner donor-reuse report (Issue #15 comment 6274520543); section 219 MAPSEC_ROUTE_202 (owner
decision "Append, share sub-areas", recorded in #15); Sandgem junction D from the merged #167 design.

Writes: data/layouts/Route202/{map.bin,border.bin}, LAYOUT_ROUTE202, the gMapGroup_Sinnoh slot,
data/maps/Route202/{map.json,scripts.inc} (three route signs), the scripts.inc include,
Route 202 `down` +4 <-> Sandgem `up` -4. The north edge (toward unbuilt Jubilife) stays closed.
"""
import argparse
import hashlib
import json
import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = HERE.parents[3] / "engine"
WIDTH, HEIGHT = 30, 34
SIGNS = ((14, 3, "Route202_Text_NorthSign"), (11, 14, "Route202_Text_RouteSign"), (21, 25, "Route202_Text_RouteSign"))


def dump(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("staged", type=pathlib.Path, help="converter output .bin (outside engine/)")
    args = parser.parse_args()
    receipt = json.loads((HERE / "route202-convert-receipt.json").read_text())
    raw = args.staged.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == receipt["output_sha256"], "staged block does not match the receipt"
    assert len(raw) == WIDTH * HEIGHT * 2 and receipt["dimensions"] == [WIDTH, HEIGHT]
    lay = ENGINE / "data/layouts/Route202"
    if lay.exists():
        raise SystemExit("Route202 already present")
    lay.mkdir(parents=True)
    (lay / "map.bin").write_bytes(raw)
    shutil.copyfile(ENGINE / "data/layouts/SandgemTown/border.bin", lay / "border.bin")

    lj = ENGINE / "data/layouts/layouts.json"
    layouts = json.loads(lj.read_text())
    layouts["layouts"].append({
        "id": "LAYOUT_ROUTE202", "name": "Route202_Layout", "width": WIDTH, "height": HEIGHT,
        "primary_tileset": "gTileset_General", "secondary_tileset": "gTileset_Dewford",
        "border_filepath": "data/layouts/Route202/border.bin",
        "blockdata_filepath": "data/layouts/Route202/map.bin", "layout_version": "emerald"})
    dump(lj, layouts)

    mg = ENGINE / "data/maps/map_groups.json"
    groups = json.loads(mg.read_text())
    assert groups["gMapGroup_Sinnoh"][-1] == "TwinleafTown", groups["gMapGroup_Sinnoh"]
    groups["gMapGroup_Sinnoh"].append("Route202")
    dump(mg, groups)

    md = ENGINE / "data/maps/Route202"
    md.mkdir()
    dump(md / "map.json", {
        "id": "MAP_ROUTE202", "name": "Route202", "layout": "LAYOUT_ROUTE202", "music": "MUS_ROUTE101",
        "region": "REGION_SINNOH", "region_map_section": "MAPSEC_ROUTE_202", "weather": "WEATHER_SUNNY",
        "map_type": "MAP_TYPE_ROUTE", "allow_cycling": True, "allow_escaping": False, "allow_running": True,
        "show_map_name": True, "requires_flash": False, "battle_scene": "MAP_BATTLE_SCENE_NORMAL",
        "connections": [{"map": "MAP_SANDGEM_TOWN", "offset": 4, "direction": "down"}],
        "coord_events": [], "object_events": [], "warp_events": [],
        "bg_events": [{"type": "sign", "x": x, "y": y, "elevation": 0, "player_facing_dir": "BG_EVENT_PLAYER_FACING_ANY",
                       "script": text.replace("_Text_", "_EventScript_")} for x, y, text in SIGNS]})
    scripts = ["Route202_MapScripts::\n\t.byte 0\n"]
    for text in sorted({t for _, _, t in SIGNS}):
        scripts.append(f"{text.replace('_Text_', '_EventScript_')}::\n\tmsgbox {text}, MSGBOX_SIGN\n\tend\n")
    scripts.append('Route202_Text_NorthSign:\n\t.string "ROUTE 202\\n"\n\t.string "SOUTH: SANDGEM TOWN$"\n')
    scripts.append('Route202_Text_RouteSign:\n\t.string "ROUTE 202$"\n')
    (md / "scripts.inc").write_text("\n".join(scripts))

    sj = ENGINE / "data/maps/SandgemTown/map.json"
    town = json.loads(sj.read_text())
    assert not any(c["direction"] == "up" for c in town["connections"])
    town["connections"].append({"map": "MAP_ROUTE202", "offset": -4, "direction": "up"})
    dump(sj, town)

    es = ENGINE / "data/event_scripts.s"
    text = es.read_text()
    anchor = '\t.include "data/maps/TwinleafTown/scripts.inc"\n'
    assert text.count(anchor) == 1
    es.write_text(text.replace(anchor, anchor + '\t.include "data/maps/Route202/scripts.inc"\n'))
    print("Route202 written; Route202 down +4 / Sandgem up -4")


if __name__ == "__main__":
    main()
