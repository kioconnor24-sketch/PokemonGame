#!/usr/bin/env python3
"""Add four neutral house interiors to the built Twinleaf Town (run once; refuses if present).

Each interior reuses an existing vanilla generic house layout (no new art, no new layout), shares Twinleaf's
section 218 (no new section ID), and has no NPCs, items or scripts: the houses stay UNASSIGNED rooms whose
story role is the owner's. Writes the four maps, their gMapGroup_Sinnoh slots, scripts.inc includes, and the
four exterior door warps on Twinleaf.
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = HERE.parents[3] / "engine"

# exterior door (from the stamps) -> interior layout and its two exit mats
HOUSES = [
    ("TwinleafTown_House1", "MAP_TWINLEAF_TOWN_HOUSE1", (10, 13), "LAYOUT_HOUSE1", [(3, 8), (4, 8)], "north-west"),
    ("TwinleafTown_House2", "MAP_TWINLEAF_TOWN_HOUSE2", (21, 13), "LAYOUT_HOUSE3", [(3, 7), (4, 7)], "north-east"),
    ("TwinleafTown_House3", "MAP_TWINLEAF_TOWN_HOUSE3", (11, 23), "LAYOUT_HOUSE4", [(3, 8), (4, 8)], "south-west"),
    ("TwinleafTown_House4", "MAP_TWINLEAF_TOWN_HOUSE4", (21, 23), "LAYOUT_HOUSE2", [(3, 7), (4, 7)], "south-east"),
]


def dump(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def main():
    town = ENGINE / "data/maps/TwinleafTown/map.json"
    tw = json.loads(town.read_text())
    if tw["warp_events"]:
        raise SystemExit("Twinleaf already has warps")
    mg = ENGINE / "data/maps/map_groups.json"
    groups = json.loads(mg.read_text())
    assert groups["gMapGroup_Sinnoh"][-1] == "TwinleafTown", groups["gMapGroup_Sinnoh"]
    includes = []
    for i, (name, ident, door, layout, mats, where) in enumerate(HOUSES):
        md = ENGINE / "data/maps" / name
        md.mkdir()
        dump(md / "map.json", {
            "id": ident, "name": name, "layout": layout, "music": "MUS_LITTLEROOT", "region": "REGION_SINNOH",
            "region_map_section": "MAPSEC_TWINLEAF_TOWN", "weather": "WEATHER_NONE", "map_type": "MAP_TYPE_INDOOR",
            "allow_cycling": False, "allow_escaping": False, "allow_running": False, "show_map_name": False,
            "requires_flash": False, "battle_scene": "MAP_BATTLE_SCENE_NORMAL", "connections": None,
            "object_events": [], "coord_events": [], "bg_events": [],
            "warp_events": [{"x": x, "y": y, "elevation": 0, "dest_map": "MAP_TWINLEAF_TOWN", "dest_warp_id": str(i)}
                            for x, y in mats]})
        (md / "scripts.inc").write_text(f"{name}_MapScripts::\n\t.byte 0\n")
        tw["warp_events"].append({"x": door[0], "y": door[1], "elevation": 0, "dest_map": ident, "dest_warp_id": "0"})
        groups["gMapGroup_Sinnoh"].append(name)
        includes.append(f'\t.include "data/maps/{name}/scripts.inc"\n')
        print(f"{where} house: door {door} -> {ident} ({layout})")
    dump(town, tw)
    dump(mg, groups)
    es = ENGINE / "data/event_scripts.s"
    text = es.read_text()
    anchor = '\t.include "data/maps/TwinleafTown/scripts.inc"\n'
    assert text.count(anchor) == 1
    es.write_text(text.replace(anchor, anchor + "".join(includes)))


if __name__ == "__main__":
    main()
