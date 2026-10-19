"""Route 201 DRY RUN: build the #135 candidate in a THROWAWAY tree only (never committed).

Dry-run-only choices, disclosed: region_map_section MAPSEC_NONE with the popup off (no 217),
music MUS_ROUTE101, no events/encounters, Sandgem's tree border reused, and the reciprocal
connection read from the plan's east exit (Route 201 right = offset, Sandgem left = -offset).
"""
import json
import pathlib
import shutil
import subprocess
import sys

engine = pathlib.Path(sys.argv[1]).resolve()
plan = pathlib.Path(sys.argv[2]).resolve()          # route201-candidate.json from #135
assert (engine / ".map_qa_throwaway").exists(), "refusing: not a throwaway tree"
scripts = engine.parent / "scripts"

off = next(e for e in json.loads(plan.read_text())["exits"] if e["name"] == "east")["offset"]
lay = engine / "data/layouts/Route201"
lay.mkdir(parents=True, exist_ok=True)
subprocess.run([sys.executable, str(scripts / "sinnoh-placeholder-art.py"), "--engine", str(engine), "plan", str(plan),
                "--out", str(lay.parent.parent.parent / "route201-dryrun.png"), "--no-marks",
                "--blockdata", str(lay / "map.bin")], check=True)
shutil.copyfile(engine / "data/layouts/SandgemTown/border.bin", lay / "border.bin")
assert (lay / "map.bin").stat().st_size == 64 * 22 * 2

lj = engine / "data/layouts/layouts.json"
layouts = json.loads(lj.read_text())
layouts["layouts"].append({
    "id": "LAYOUT_ROUTE201", "name": "Route201_Layout", "width": 64, "height": 22,
    "primary_tileset": "gTileset_General", "secondary_tileset": "gTileset_Dewford",
    "border_filepath": "data/layouts/Route201/border.bin",
    "blockdata_filepath": "data/layouts/Route201/map.bin", "layout_version": "emerald"})
lj.write_text(json.dumps(layouts, indent=2) + "\n")

mg = engine / "data/maps/map_groups.json"
groups = json.loads(mg.read_text())
group = next(g for g in groups["group_order"] if "SandgemTown" in groups[g])
groups[group].append("Route201")
mg.write_text(json.dumps(groups, indent=2) + "\n")

md = engine / "data/maps/Route201"
md.mkdir(parents=True, exist_ok=True)
(md / "scripts.inc").write_text("Route201_MapScripts::\n\t.byte 0\n")
(md / "map.json").write_text(json.dumps({
    "id": "MAP_ROUTE201", "name": "Route201", "layout": "LAYOUT_ROUTE201", "music": "MUS_ROUTE101",
    "region": "REGION_SINNOH", "region_map_section": "MAPSEC_NONE", "weather": "WEATHER_SUNNY",
    "map_type": "MAP_TYPE_ROUTE", "allow_cycling": True, "allow_escaping": False, "allow_running": True,
    "show_map_name": False, "requires_flash": False, "battle_scene": "MAP_BATTLE_SCENE_NORMAL",
    "connections": [{"map": "MAP_SANDGEM_TOWN", "offset": off, "direction": "right"}],
    "coord_events": [], "object_events": [], "warp_events": [], "bg_events": []}, indent=2) + "\n")

sj = engine / "data/maps/SandgemTown/map.json"
sandgem = json.loads(sj.read_text())
sandgem["connections"] = [{"map": "MAP_ROUTE201", "offset": -off, "direction": "left"}]
sj.write_text(json.dumps(sandgem, indent=2) + "\n")

es = engine / "data/event_scripts.s"
text = es.read_text()
anchor = '\t.include "data/maps/SandgemTown_PokemonCenter_1F/scripts.inc"\n'
assert text.count(anchor) == 1
es.write_text(text.replace(anchor, anchor + '\t.include "data/maps/Route201/scripts.inc"\n'))
print("dry-run Route 201 applied to", engine, "group", group)
