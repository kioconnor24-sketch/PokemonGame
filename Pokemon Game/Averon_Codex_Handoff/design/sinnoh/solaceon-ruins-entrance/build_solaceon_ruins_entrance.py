#!/usr/bin/env python3
"""Solaceon Ruins entrance (W20): Solaceon Town's two cliff cave mouths lead into the ruins network, as in DS.

OFF-ENGINE staging joining two Claude batches. Solaceon Town (Codex's hearthome-solaceon staging, read-only) draws two
cave mouths in its east cliff, (55, 19) on the ledge and (54, 23) at the foot: walkable MB_NON_ANIMATED_DOOR cells
with no warp (W12 handled only animated doors). Here W12's SolaceonTown overlay is re-staged with two warps appended
for them, into a new
SolaceonRuins_Entrance chamber (W1 cave kit, General + Cave): two Granite Cave mouths back out, one to each cliff
door, and a down-ladder to W15's B1F hub, which is re-staged with exactly one more up-ladder cell and one appended
warp. Solaceon's 4-wide houses with the door picture
593 beside the end piece 529 stay closed: no door of the family is ever drawn next to 529 (unattested pair).
No objects, Unown, story or sections (MAPSEC_PENDING_OWNER).

  build_solaceon_ruins_entrance.py --engine ENGINE --out DIR
"""
import argparse
import copy
import importlib.util
import json
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


w12 = load("w12", SINNOH / "city-shells/build_city_shells.py")
w15 = load("w15", SINNOH / "solaceon-depths/build_solaceon_depths.py")
w1 = w15.w1
CLIFF_DOORS = [(55, 19), (54, 23)]          # ledge mouth, foot mouth
B1F_LADDER = (21, 4)
ENTRANCE_W, ENTRANCE_H = 30, 20
MOUTHS = [(8, 15), (21, 15)]                # exits back to CLIFF_DOORS, in order
DOWN = (14, 4)


def entrance(eng):
    cv = w1.Cave(eng, ENTRANCE_W, ENTRANCE_H)
    cv.room(3, 3, 26, 15)
    cv.block(10, 7, 18, 11)
    for x, y in MOUTHS:
        cv.exit_south(x, y, eng)
    cv.ladder(*DOWN, eng, down=True)
    return cv


def build(engine_root):
    overlays, shells, _ = w12.build(engine_root)
    eng, w15maps, w15layouts = w15.build(engine_root)
    sol = copy.deepcopy(overlays["SolaceonTown"])
    attrs, names = w12.attributes("hearthome-solaceon"), w12.behaviours(eng.root)
    width_t, town = w12.map_bin("hearthome-solaceon", "SolaceonTown")
    index = {}
    for k, (x, y) in enumerate(CLIFF_DOORS):
        v = town[y * width_t + x]
        assert names[attrs[v & 1023] & 0xFF] == "MB_NON_ANIMATED_DOOR" and not v & 0xC00, (x, y)
        assert all((w["x"], w["y"]) != (x, y) for w in sol["warp_events"]), (x, y)
        index[(x, y)] = len(sol["warp_events"])
        sol["warp_events"].append({"x": x, "y": y, "elevation": 0, "dest_map": "MAP_SOLACEON_RUINS_ENTRANCE",
                                   "dest_warp_id": str(k)})
    b1f_hdr = copy.deepcopy(w15maps["SolaceonRuins_B1F"])
    cells, width, height = w15layouts["SolaceonRuins_B1F"]
    x, y = B1F_LADDER
    assert cells[y * width + x] & 1023 == 513 and not cells[y * width + x] & 0xC00
    assert all(not cells[(y + dy) * width + x + dx] & 0xC00 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    cells = list(cells)
    cells[y * width + x] = eng.word("GraniteCave_B1F", 4, 21, 573)
    b1f_hdr["warp_events"].append({"x": x, "y": y, "elevation": 0, "dest_map": "MAP_SOLACEON_RUINS_ENTRANCE",
                                   "dest_warp_id": "2"})
    cv = entrance(eng)
    ent = w1.header("MAP_SOLACEON_RUINS_ENTRANCE", "SolaceonRuins_Entrance", "LAYOUT_SOLACEON_RUINS_ENTRANCE",
                    w15.MUSIC, "MAP_TYPE_UNDERGROUND",
                    [(*MOUTHS[0], "MAP_SOLACEON_TOWN", index[CLIFF_DOORS[0]]),
                     (*MOUTHS[1], "MAP_SOLACEON_TOWN", index[CLIFF_DOORS[1]]),
                     (*DOWN, "MAP_SOLACEON_RUINS_B1F", len(b1f_hdr["warp_events"]) - 1)])
    return eng, sol, {"SolaceonRuins_Entrance": (ent, (cv.cells, cv.w, cv.h)),
                      "SolaceonRuins_B1F": (b1f_hdr, (cells, width, height))}


def check(sol, maps):
    by_id = {h["id"]: h for h, _ in maps.values()}
    by_id[sol["id"]] = sol
    for mid in ("MAP_SOLACEON_RUINS_ENTRANCE", "MAP_SOLACEON_RUINS_B1F"):
        for i, w in enumerate(by_id[mid]["warp_events"]):
            if w["dest_map"] in by_id and w["dest_map"] != mid:
                back = by_id[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
                assert (back["dest_map"], int(back["dest_warp_id"])) == (mid, i), (mid, i, w, back)
    return True


def write(engine_root, out):
    eng, sol, maps = build(engine_root)
    check(sol, maps)
    st = pathlib.Path(out) / "staged"
    (st / "SolaceonTown-dev-overlay").mkdir(parents=True, exist_ok=True)
    (st / "SolaceonTown-dev-overlay/map.json").write_text(json.dumps(sol, indent=2) + "\n")
    blocks = w12.opened(eng.root, "hearthome-solaceon", "SolaceonTown")
    (st / "SolaceonTown-dev-overlay/map.bin").write_bytes(struct.pack("<%dH" % len(blocks), *blocks))
    bank = w1.render.Bank(eng.root / "data/tilesets/primary/general", eng.root / "data/tilesets/secondary/cave")
    border = struct.pack("<4H", *[w1.Cave(eng, 1, 1).k[529]] * 4)
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "maps": {}}
    for name, (hdr, (cells, w, h)) in maps.items():
        d = st / name
        d.mkdir(parents=True, exist_ok=True)
        data = struct.pack("<%dH" % len(cells), *cells)
        (d / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (d / "scripts.inc").write_text(w1.scripts(name))
        (d / "map.bin").write_bytes(data)
        (d / "border.bin").write_bytes(border)
        (d / "layout.json").write_text(json.dumps({"id": hdr["layout"], "name": name + "_Layout", "width": w,
                                                   "height": h, "primary_tileset": "gTileset_General",
                                                   "secondary_tileset": "gTileset_Cave"}, indent=2) + "\n")
        w1.render.render_cells(bank, cells, w, d / "preview.png")
        receipt["maps"][name] = {"map_sha256": w1.sha(data), "warps": len(hdr["warp_events"])}
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(write(a.engine, a.out)["status"])
