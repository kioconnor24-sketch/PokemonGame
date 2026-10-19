#!/usr/bin/env python3
"""Write Twinleaf Town into the engine tree (run once; refuses if it already exists).

Approvals:
- geometry: the owner's geography delegation (Issue #15 comment 6261800483), using the merged #156 candidate;
- section 218: Issue #15 comment 6271044156.

Writes:
- data/layouts/TwinleafTown/map.bin from twinleaf-candidate.json (via sinnoh-placeholder-art.py), plus
  border.bin (Sandgem's tree border);
- the LAYOUT_TWINLEAF_TOWN entry, the gMapGroup_Sinnoh slot and the scripts.inc include;
- data/maps/TwinleafTown/{map.json,scripts.inc}: one town sign; the four houses are closed shells (no warps);
- Route 201's `down` connection (offset 0) and Twinleaf's `up` connection (offset 0).

Section 218 (region_map_sections.json + pins) and the registry/test pins are separate, reviewed edits.
"""
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = HERE.parents[3] / "engine"
PLAN = HERE / "twinleaf-candidate.json"


def dump(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def main():
    plan = json.loads(PLAN.read_text())
    north = next(e for e in plan["exits"] if e["name"] == "north")
    assert north["span"] == [15, 17] and north["offset"] == 0, north
    lay = ENGINE / "data/layouts/TwinleafTown"
    if lay.exists():
        raise SystemExit("TwinleafTown already present")
    lay.mkdir(parents=True)
    subprocess.run([sys.executable, str(ENGINE.parent / "scripts/sinnoh-placeholder-art.py"), "--engine", str(ENGINE),
                    "plan", str(PLAN), "--out", str(HERE / "twinleaf-built.png"), "--no-marks",
                    "--blockdata", str(lay / "map.bin")], check=True)
    assert (lay / "map.bin").stat().st_size == plan["width"] * plan["height"] * 2
    shutil.copyfile(ENGINE / "data/layouts/SandgemTown/border.bin", lay / "border.bin")

    lj = ENGINE / "data/layouts/layouts.json"
    layouts = json.loads(lj.read_text())
    layouts["layouts"].append({
        "id": "LAYOUT_TWINLEAF_TOWN", "name": "TwinleafTown_Layout", "width": plan["width"], "height": plan["height"],
        "primary_tileset": plan["primary"], "secondary_tileset": plan["secondary"],
        "border_filepath": "data/layouts/TwinleafTown/border.bin",
        "blockdata_filepath": "data/layouts/TwinleafTown/map.bin", "layout_version": "emerald"})
    dump(lj, layouts)

    mg = ENGINE / "data/maps/map_groups.json"
    groups = json.loads(mg.read_text())
    assert groups["gMapGroup_Sinnoh"][-1] == "Route201", groups["gMapGroup_Sinnoh"]
    groups["gMapGroup_Sinnoh"].append("TwinleafTown")
    dump(mg, groups)

    sign = (18, 15)
    sign_code = next(k for k, v in plan["legend"].items() if v["note"] == "sign")
    assert plan["rows"][sign[1]][sign[0]] == sign_code, sign
    md = ENGINE / "data/maps/TwinleafTown"
    md.mkdir()
    dump(md / "map.json", {
        "id": "MAP_TWINLEAF_TOWN", "name": "TwinleafTown", "layout": "LAYOUT_TWINLEAF_TOWN", "music": "MUS_LITTLEROOT",
        "region": "REGION_SINNOH", "region_map_section": "MAPSEC_TWINLEAF_TOWN", "weather": "WEATHER_SUNNY",
        "map_type": "MAP_TYPE_TOWN", "allow_cycling": True, "allow_escaping": False, "allow_running": True,
        "show_map_name": True, "requires_flash": False, "battle_scene": "MAP_BATTLE_SCENE_NORMAL",
        "connections": [{"map": "MAP_ROUTE201", "offset": 0, "direction": "up"}],
        "coord_events": [], "object_events": [], "warp_events": [],
        "bg_events": [{"type": "sign", "x": sign[0], "y": sign[1], "elevation": 0,
                       "player_facing_dir": "BG_EVENT_PLAYER_FACING_ANY", "script": "TwinleafTown_EventScript_TownSign"}]})
    (md / "scripts.inc").write_text("""TwinleafTown_MapScripts::
\t.byte 0

TwinleafTown_EventScript_TownSign::
\tmsgbox TwinleafTown_Text_TownSign, MSGBOX_SIGN
\tend

TwinleafTown_Text_TownSign:
\t.string "TWINLEAF TOWN$"
""")

    rj = ENGINE / "data/maps/Route201/map.json"
    route = json.loads(rj.read_text())
    assert not any(c["direction"] == "down" for c in route["connections"])
    route["connections"].append({"map": "MAP_TWINLEAF_TOWN", "offset": 0, "direction": "down"})
    dump(rj, route)

    es = ENGINE / "data/event_scripts.s"
    text = es.read_text()
    anchor = '\t.include "data/maps/Route201/scripts.inc"\n'
    assert text.count(anchor) == 1
    es.write_text(text.replace(anchor, anchor + '\t.include "data/maps/TwinleafTown/scripts.inc"\n'))
    print("Twinleaf written; Route201 down 0 / Twinleaf up 0")


if __name__ == "__main__":
    main()
