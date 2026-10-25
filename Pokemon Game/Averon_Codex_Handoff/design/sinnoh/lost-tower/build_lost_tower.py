#!/usr/bin/env python3
"""Lost Tower (W8): six floors behind Route 209's tower, on Averon's stock Mt. Pyre interiors (OFF-ENGINE staging).

No donor, main or open-PR map exists for Lost Tower. Averon's Mt. Pyre 1F-6F (a graveyard tower) are reused
unchanged as LAYOUT_MT_PYRE_1F..6F; their complete stair graph is copied warp for warp with only the map names
changed (MT_PYRE_nF -> LOST_TOWER_nF). The 1F's four exterior mats (Route 122 / Mt. Pyre exterior in Hoenn) all
return to Route 209.

Route 209 (Codex's hearthome-solaceon staging) draws the tower with a walkable base passage (61, 15)-(62, 17) and no
door; a DEV-only overlay of its map.json appends one step-on portal at (61, 15) (warp + coord trigger on the same
tile, as W1's harbor). Codex's files are not modified.

Route 209's three walled pockets (the ruins) have floor and entry steps at elevation 2 against ground at 3, so the
engine refuses the step in. A DEV-only derived copy of its map.bin (overlay map.bin) sets just those eight step cells
to elevation 0, the transition convention (3 -> 0 -> 2 and back); metatiles and collision are unchanged.
No story, objects, items, encounters or sections (MAPSEC_PENDING_OWNER).

  build_lost_tower.py --engine ENGINE --out DIR
"""
import argparse
import importlib.util
import json
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("w1", HERE.parent / "iron-island/build_iron_island.py")
w1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w1)
ROUTE209 = HERE.parent / "hearthome-solaceon/staged/Route209"
PORTAL = (61, 15)
FLOORS = ["1F", "2F", "3F", "4F", "5F", "6F"]
EXTERIOR = {"MAP_ROUTE122", "MAP_MT_PYRE_EXTERIOR"}
# Solaceon Ruins: Route 209's three walled pockets (floor 610, entered up steps) each get a step-on portal at the back
# centre of the pocket, leading to a stock Averon ruin chamber (unchanged layout, its own internal warp pair kept).
RUINS = [("SolaceonRuins_A", "DesertRuins", (45, 16)), ("SolaceonRuins_B", "IslandCave", (54, 28)),
         ("SolaceonRuins_C", "AncientTomb", (47, 38))]
STEPS = [(44, 18), (45, 18), (46, 18), (53, 30), (54, 30), (55, 30), (47, 40), (48, 40)]


def build(engine):
    engine = pathlib.Path(engine)
    raw = (ROUTE209 / "averon-map.bin").read_bytes()
    cells = struct.unpack("<%dH" % (len(raw) // 2), raw)
    portal = cells[PORTAL[1] * 68 + PORTAL[0]]
    assert not portal & 0xC00, hex(portal)                         # walkable tower base, no door behaviour
    r209 = json.loads((ROUTE209 / "map.json").read_text())
    assert all((w["x"], w["y"]) != PORTAL for w in r209["warp_events"])
    index = len(r209["warp_events"])
    r209["warp_events"].append({"x": PORTAL[0], "y": PORTAL[1], "elevation": 0, "dest_map": "MAP_LOST_TOWER_1F",
                                "dest_warp_id": "0"})
    r209.setdefault("coord_events", []).append({"type": "trigger", "x": PORTAL[0], "y": PORTAL[1], "elevation": 0,
                                                "var": "VAR_TEMP_1", "var_value": "0",
                                                "script": "Route209_EventScript_ToLostTower"})
    maps = {}
    for f in FLOORS:
        src = json.loads((engine / f"data/maps/MtPyre_{f}/map.json").read_text())
        assert src["layout"] == f"LAYOUT_MT_PYRE_{f}"
        warps = []
        for w in src["warp_events"]:
            if w["dest_map"] in EXTERIOR:
                dest, dw = "MAP_ROUTE209", index
            else:
                assert w["dest_map"].startswith("MAP_MT_PYRE_"), w
                dest, dw = w["dest_map"].replace("MAP_MT_PYRE_", "MAP_LOST_TOWER_"), int(w["dest_warp_id"])
            warps.append((w["x"], w["y"], dest, dw))
        maps[f"LostTower_{f}"] = w1.header(f"MAP_LOST_TOWER_{f}", f"LostTower_{f}", src["layout"], "MUS_MT_PYRE",
                                           "MAP_TYPE_INDOOR", warps)
    # The portal must land on a 1F exterior mat: warp 0 of 1F is one (17, 18) in Mt. Pyre.
    assert maps["LostTower_1F"]["warp_events"][0]["dest_map"] == "MAP_ROUTE209"
    script = "Route209_EventScript_ToLostTower::\n\twarp MAP_LOST_TOWER_1F, 0\n\twaitstate\n\tend\n"
    for name, stock, (x, y) in RUINS:
        cell = cells[y * 68 + x]
        assert cell & 1023 == 610 and not cell & 0xC00, (name, hex(cell))          # inside a walled pocket
        src = json.loads((engine / f"data/maps/{stock}/map.json").read_text())
        mid = "MAP_" + name.replace("SolaceonRuins", "SOLACEON_RUINS").upper()
        i = len(r209["warp_events"])
        r209["warp_events"].append({"x": x, "y": y, "elevation": 0, "dest_map": mid, "dest_warp_id": "0"})
        r209["coord_events"].append({"type": "trigger", "x": x, "y": y, "elevation": 0, "var": "VAR_TEMP_1",
                                     "var_value": "0", "script": f"Route209_EventScript_To{name}"})
        script += f"\nRoute209_EventScript_To{name}::\n\twarp {mid}, 0\n\twaitstate\n\tend\n"
        warps = []
        for w in src["warp_events"]:
            own = w["dest_map"] == "MAP_" + "".join("_" + ch if ch.isupper() else ch for ch in stock).lstrip("_").upper()
            warps.append((w["x"], w["y"], mid if own else "MAP_ROUTE209", int(w["dest_warp_id"]) if own else i))
        maps[name] = w1.header(mid, name, src["layout"], "MUS_ROUTE110", "MAP_TYPE_UNDERGROUND", warps)
    blocks = list(cells)
    for x, y in STEPS:
        v = cells[y * 68 + x]
        assert v & 1023 in (175, 35, 207) and not v & 0xC00 and v >> 12 == 2, ((x, y), hex(v))
        assert cells[(y + 1) * 68 + x] >> 12 == 3 and cells[(y - 1) * 68 + x] >> 12 == 2, (x, y)  # ground / floor
        blocks[y * 68 + x] = v & 0x0FFF
    return maps, r209, script, struct.pack("<%dH" % len(blocks), *blocks)


def write(engine, out):
    maps, r209, script, r209_bin = build(engine)
    st = pathlib.Path(out) / "staged"
    for name, hdr in maps.items():
        (st / name).mkdir(parents=True, exist_ok=True)
        (st / name / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (st / name / "scripts.inc").write_text(w1.scripts(name))
    (st / "Route209-dev-overlay").mkdir(parents=True, exist_ok=True)
    (st / "Route209-dev-overlay/map.json").write_text(json.dumps(r209, indent=2) + "\n")
    (st / "Route209-dev-overlay/portal-script.inc").write_text(script)
    (st / "Route209-dev-overlay/map.bin").write_bytes(r209_bin)
    return {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "floors": list(maps), "portal": PORTAL}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(json.dumps(write(a.engine, a.out), indent=2))
