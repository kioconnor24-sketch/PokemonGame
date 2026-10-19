#!/usr/bin/env python3
"""Write the owner-approved permanent Route 201 into the engine tree (run once; idempotent check).

Owner approval: Issue #15 comment 6258911084 (geometry + 3 deviations, section 217, Route 201
right -4 <-> Sandgem left +4, Twinleaf / Lake Verity closed, grass physical only).

Writes:
- data/layouts/Route201/map.bin from route201-candidate.json (via sinnoh-placeholder-art.py),
  plus border.bin (Sandgem's tree border);
- the LAYOUT_ROUTE201 entry, the gMapGroup_Sinnoh slot and the scripts.inc include;
- data/maps/Route201/{map.json,scripts.inc} with three signs that name only built places;
- Sandgem's `left` connection (+4).

Section 217 (region_map_sections.json + pins) and the registry slot pins are separate, reviewed edits.
"""
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = HERE.parents[3] / "engine"
PLAN = HERE / "route201-candidate.json"


def dump(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def main():
    plan = json.loads(PLAN.read_text())
    off = next(e for e in plan["exits"] if e["name"] == "east")["offset"]
    assert off == -4, off
    lay = ENGINE / "data/layouts/Route201"
    if lay.exists():
        raise SystemExit("Route201 already present")
    lay.mkdir(parents=True)
    subprocess.run([sys.executable, str(ENGINE.parent / "scripts/sinnoh-placeholder-art.py"), "--engine", str(ENGINE),
                    "plan", str(PLAN), "--out", str(HERE / "route201-built.png"), "--no-marks",
                    "--blockdata", str(lay / "map.bin")], check=True)
    assert (lay / "map.bin").stat().st_size == plan["width"] * plan["height"] * 2
    shutil.copyfile(ENGINE / "data/layouts/SandgemTown/border.bin", lay / "border.bin")

    lj = ENGINE / "data/layouts/layouts.json"
    layouts = json.loads(lj.read_text())
    layouts["layouts"].append({
        "id": "LAYOUT_ROUTE201", "name": "Route201_Layout", "width": plan["width"], "height": plan["height"],
        "primary_tileset": plan["primary"], "secondary_tileset": plan["secondary"],
        "border_filepath": "data/layouts/Route201/border.bin",
        "blockdata_filepath": "data/layouts/Route201/map.bin", "layout_version": "emerald"})
    dump(lj, layouts)

    mg = ENGINE / "data/maps/map_groups.json"
    groups = json.loads(mg.read_text())
    groups["gMapGroup_Sinnoh"].append("Route201")
    dump(mg, groups)

    signs = [((13, 15), "Route201_EventScript_WestSign"), ((40, 11), "Route201_EventScript_MiddleSign"),
             ((55, 5), "Route201_EventScript_SandgemSign")]
    for (x, y), _ in signs:
        assert plan["rows"][y][x] == next(k for k, v in plan["legend"].items() if v["note"].startswith("sign")), (x, y)
    md = ENGINE / "data/maps/Route201"
    md.mkdir()
    dump(md / "map.json", {
        "id": "MAP_ROUTE201", "name": "Route201", "layout": "LAYOUT_ROUTE201", "music": "MUS_ROUTE101",
        "region": "REGION_SINNOH", "region_map_section": "MAPSEC_ROUTE_201", "weather": "WEATHER_SUNNY",
        "map_type": "MAP_TYPE_ROUTE", "allow_cycling": True, "allow_escaping": False, "allow_running": True,
        "show_map_name": True, "requires_flash": False, "battle_scene": "MAP_BATTLE_SCENE_NORMAL",
        "connections": [{"map": "MAP_SANDGEM_TOWN", "offset": off, "direction": "right"}],
        "coord_events": [], "object_events": [], "warp_events": [],
        "bg_events": [{"type": "sign", "x": x, "y": y, "elevation": 0,
                       "player_facing_dir": "BG_EVENT_PLAYER_FACING_ANY", "script": script}
                      for (x, y), script in signs]})
    (md / "scripts.inc").write_text("""Route201_MapScripts::
\t.byte 0

Route201_EventScript_WestSign::
\tmsgbox Route201_Text_RouteSign, MSGBOX_SIGN
\tend

Route201_EventScript_MiddleSign::
\tmsgbox Route201_Text_RouteSign, MSGBOX_SIGN
\tend

Route201_EventScript_SandgemSign::
\tmsgbox Route201_Text_SandgemSign, MSGBOX_SIGN
\tend

Route201_Text_RouteSign:
\t.string "ROUTE 201$"

Route201_Text_SandgemSign:
\t.string "ROUTE 201\\n"
\t.string "EAST: SANDGEM TOWN$"
""")

    sj = ENGINE / "data/maps/SandgemTown/map.json"
    sandgem = json.loads(sj.read_text())
    assert sandgem["connections"] is None
    sandgem["connections"] = [{"map": "MAP_ROUTE201", "offset": -off, "direction": "left"}]
    dump(sj, sandgem)

    es = ENGINE / "data/event_scripts.s"
    text = es.read_text()
    anchor = '\t.include "data/maps/SandgemTown_PokemonCenter_1F/scripts.inc"\n'
    assert text.count(anchor) == 1
    es.write_text(text.replace(anchor, anchor + '\t.include "data/maps/Route201/scripts.inc"\n'))
    print("Route 201 written; connection Route201 right", off, "/ Sandgem left", -off)


if __name__ == "__main__":
    main()
