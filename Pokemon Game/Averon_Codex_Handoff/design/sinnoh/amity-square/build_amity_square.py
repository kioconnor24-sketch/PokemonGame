#!/usr/bin/env python3
"""Amity Square (W11): new physical geography north of Hearthome City, in Averon's own banks (OFF-ENGINE staging).

No donor, main or open-PR map exists for Amity Square. Built with W1/W6's attested composition, General + Dewford:
a 52 x 40 park with a tree ring, a central sand plaza, three rectangular ponds whose every pond/grass pattern occurs
in Lake Verity (strict), walkways, and two gatehouses (Dewford's house) at the south-west and south-east.
Hearthome (Codex's hearthome-solaceon staging) has two pairs of north arrow mats with no warp at (8-9, 6) and
(50-51, 6); a DEV-only overlay of its map.json appends four warps: the west pair to the west gatehouse door, the east
pair to the east one. Its seven warp-less animated doors open into neutral LAYOUT_HOUSE1 shells, except the civic
three (CIVIC): the hall gets Lilycove's contest lobby and hall, the Pokemon Center and Mart their stock interiors (no
services or NPCs). Two more houses,
(20, 19) and (21, 30), draw their door as the closed picture 593 (solid); a DEV-only derived copy of Hearthome's
map.bin puts the family's animated door there, copied from Route 210 South's house door (30, 47), whose left/right/
above pieces are identical (528/528/519), and they get shells too. Codex's files are not modified.
No story, walking-Pokemon mechanic, objects, encounters or sections (MAPSEC_PENDING_OWNER).

  build_amity_square.py --engine ENGINE --out DIR
"""
import argparse
import importlib.util
import json
import pathlib
import re
import struct

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pal", HERE.parent / "pal-park/build_pal_park.py")
pal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pal)
w1 = pal.w1
HEARTHOME = HERE.parent / "hearthome-solaceon/staged/HearthomeCity"
MATS = {"west": [(8, 6), (9, 6)], "east": [(50, 6), (51, 6)]}
# Hearthome's warp-less animated doors open into neutral LAYOUT_HOUSE1 shells (no NPCs/services/contests/gym).
HEARTHOME_DOORS = [(29, 12), (14, 19), (36, 19), (49, 19), (27, 30), (37, 30), (44, 30)]
# Closed door pictures opened with the family's door of the same surroundings (house shells 8 and 9).
PICTURE_DOORS = [(20, 19), (21, 30)]
DOOR_DONOR = ("Route210_South", (30, 47))
# Civic buildings get stock multi-room interiors instead of a house shell (as W12 did for Veilstone): stair graphs
# copied with the floors renamed, street mats -> the Hearthome door, other exits (a Center's 2F) dropped.
CIVIC = {(29, 12): [("HearthomeCity_ContestLobby", "LilycoveCity_ContestLobby"),
                    ("HearthomeCity_ContestHall", "LilycoveCity_ContestHall")],
         (14, 19): [("HearthomeCity_PokemonCenter_1F", "OldaleTown_PokemonCenter_1F")],
         (27, 30): [("HearthomeCity_Mart", "OldaleTown_Mart")]}
W, H = 52, 40
PONDS = [(8, 6, 15, 11), (36, 6, 43, 11), (22, 26, 29, 30)]
PLAZA = (18, 12, 33, 22)
PATHS = [((25, 4), (26, 33)), ((6, 17), (45, 18)), ((8, 30), (43, 31))]
GATES = {"west": (6, 31), "east": (41, 31)}          # Dewford house top-left; door (+2, +3)


def family_bin(name):
    d = HERE.parent / "hearthome-solaceon/staged" / name
    raw = (d / "averon-map.bin").read_bytes()
    width = struct.unpack(">I", (d / "averon.png").read_bytes()[16:20])[0] // 16
    return width, list(struct.unpack("<%dH" % (len(raw) // 2), raw))


def opened_hearthome(engine):
    """Hearthome's blockdata with PICTURE_DOORS given the family's animated door word."""
    fam = HERE.parent / "hearthome-solaceon/outdoor-family"
    pa = (fam / "primary-attributes.bin").read_bytes()
    pa += b"\0" * (1024 - len(pa))
    sa = (fam / "secondary-attributes.bin").read_bytes()
    attrs = struct.unpack("<%dH" % ((len(pa) + len(sa)) // 2), pa + sa)
    names = re.findall(r"^\s*(MB_\w+)", (pathlib.Path(engine) / "include/constants/metatile_behaviors.h").read_text(), re.M)
    width, cells = family_bin("HearthomeCity")
    dwidth, dcells = family_bin(DOOR_DONOR[0])
    sx, sy = DOOR_DONOR[1]
    door = dcells[sy * dwidth + sx]
    assert names[attrs[door & 1023] & 0xFF] == "MB_ANIMATED_DOOR"
    out = list(cells)
    for x, y in PICTURE_DOORS:
        picture = cells[y * width + x]
        assert picture & 0xC00 and "DOOR" not in names[attrs[picture & 1023] & 0xFF], (x, y)
        assert not cells[(y + 1) * width + x] & 0xC00, (x, y)                   # a walkable doorstep below
        for dx, dy in ((-1, 0), (1, 0), (0, -1)):
            assert cells[(y + dy) * width + x + dx] & 1023 == dcells[(sy + dy) * dwidth + sx + dx] & 1023, (x, y)
        out[y * width + x] = door
    return out


def const(name):
    return "MAP_" + re.sub(r"(?<=[a-z])(?=[A-Z])", "_", name).upper()


def civic(engine, floors, door_warp):
    """Stock floors renamed; warps to the stock city -> door_warp on Hearthome; warps outside the floors dropped."""
    srcs = {n: json.loads((pathlib.Path(engine) / f"data/maps/{s}/map.json").read_text()) for n, s in floors}
    stock_ids = {src["id"]: n for n, src in srcs.items()}
    city = const(floors[0][1].split("_")[0])
    keep = {n: [i for i, w in enumerate(src["warp_events"]) if w["dest_map"] in stock_ids or w["dest_map"] == city]
            for n, src in srcs.items()}
    out = {}
    for n, src in srcs.items():
        warps = []
        for i in keep[n]:
            w = src["warp_events"][i]
            if w["dest_map"] == city:
                assert n == floors[0][0], (n, w)
                warps.append((w["x"], w["y"], "MAP_HEARTHOME_CITY", door_warp))
            else:
                dest = stock_ids[w["dest_map"]]
                warps.append((w["x"], w["y"], const(dest), keep[dest].index(int(w["dest_warp_id"]))))
        out[n] = w1.header(const(n), n, src["layout"], "MUS_ROUTE110", "MAP_TYPE_INDOOR", warps)
    return out


def build(engine):
    eng = w1.Engine(engine)
    verity = eng.words(("LakeVerity",))
    grass, sand = eng.word("LakeVerity", 19, 20, 1), eng.word("DewfordTown", 8, 9, 292)
    cells = [grass] * (W * H)
    x0, y0, x1, y1 = PLAZA
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            cells[y * W + x] = sand
    for (a, b), (c, d) in PATHS:
        for y in range(b, d + 1):
            for x in range(a, c + 1):
                cells[y * W + x] = sand
    ptab = pal.pond_table(eng)
    for px0, py0, px1, py1 in PONDS:
        inside = lambda x, y: px0 <= x <= px1 and py0 <= y <= py1
        for y in range(py0, py1 + 1):
            for x in range(px0, px1 + 1):
                key = tuple(not inside(x + dx, y + dy) for dx, dy in w1.NB8)
                if key not in ptab:
                    raise SystemExit(f"unattested pond pattern at {(x, y)}: {key}")
                cells[y * W + x] = verity[ptab[key].most_common(1)[0][0]]

    def tree(tx, ty):
        for (dx, dy), mid in zip(((0, 0), (1, 0), (0, 1), (1, 1)), (470, 471, 478, 479)):
            cells[(ty + dy) * W + tx + dx] = verity[mid]
    for tx in range(0, W, 2):
        tree(tx, 0), tree(tx, H - 2), tree(tx, H - 4)
    for ty in range(2, H - 4, 2):
        tree(0, ty), tree(2, ty), tree(W - 2, ty), tree(W - 4, ty)
    for tx, ty in [(18, 6), (30, 6), (8, 22), (40, 22), (14, 26), (34, 26)]:
        tree(tx, ty)
    dew = eng.cells("DewfordTown")[2]
    doors = {}
    for side, (gx, gy) in GATES.items():
        for j in range(4):
            for i in range(5):
                cells[(gy + j) * W + gx + i] = dew[j * 20 + 1 + i]
        doors[side] = (gx + 2, gy + 3)
        assert cells[(gy + 3) * W + gx + 2] & 1023 == 549
    hh = json.loads((HEARTHOME / "map.json").read_text())
    n = len(hh["warp_events"])
    for side, mats in MATS.items():
        for x, y in mats:
            assert all((w["x"], w["y"]) != (x, y) for w in hh["warp_events"])
            hh["warp_events"].append({"x": x, "y": y, "elevation": 0, "dest_map": "MAP_AMITY_SQUARE",
                                      "dest_warp_id": "0" if side == "west" else "1"})
    shells = {}
    for k, (x, y) in enumerate(HEARTHOME_DOORS + PICTURE_DOORS, 1):
        assert all((w["x"], w["y"]) != (x, y) for w in hh["warp_events"]), (x, y)
        i = len(hh["warp_events"])
        if (x, y) in CIVIC:
            floors = CIVIC[(x, y)]
            hh["warp_events"].append({"x": x, "y": y, "elevation": 0, "dest_map": const(floors[0][0]),
                                      "dest_warp_id": "0"})
            shells.update(civic(engine, floors, i))
            continue
        name = f"HearthomeCity_House{k}"
        hh["warp_events"].append({"x": x, "y": y, "elevation": 0, "dest_map": f"MAP_HEARTHOME_CITY_HOUSE{k}",
                                  "dest_warp_id": "0"})
        shells[name] = w1.header(f"MAP_HEARTHOME_CITY_HOUSE{k}", name, "LAYOUT_HOUSE1", "MUS_ROUTE110",
                                 "MAP_TYPE_INDOOR", [(3, 8, "MAP_HEARTHOME_CITY", i), (4, 8, "MAP_HEARTHOME_CITY", i)])
    amity = w1.header("MAP_AMITY_SQUARE", "AmitySquare", "LAYOUT_AMITY_SQUARE", "MUS_ROUTE110", "MAP_TYPE_ROUTE",
                      [(*doors["west"], "MAP_HEARTHOME_CITY", n), (*doors["east"], "MAP_HEARTHOME_CITY", n + 2)])
    return eng, cells, amity, hh, doors, shells, opened_hearthome(engine)


def write(engine, out):
    eng, cells, amity, hh, doors, shells, hh_bin = build(engine)
    st = pathlib.Path(out) / "staged"
    for name, hdr in shells.items():
        (st / name).mkdir(parents=True, exist_ok=True)
        (st / name / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (st / name / "scripts.inc").write_text(w1.scripts(name))
    (st / "AmitySquare").mkdir(parents=True, exist_ok=True)
    data = struct.pack("<%dH" % len(cells), *cells)
    (st / "AmitySquare/map.bin").write_bytes(data)
    (st / "AmitySquare/layout.json").write_text(json.dumps({"id": "LAYOUT_AMITY_SQUARE", "width": W, "height": H,
                                                            "primary_tileset": "gTileset_General",
                                                            "secondary_tileset": "gTileset_Dewford"}, indent=2) + "\n")
    (st / "AmitySquare/border.bin").write_bytes(struct.pack("<4H", *[eng.word("LakeVerity", 0, 0, 478)] * 4))
    (st / "AmitySquare/map.json").write_text(json.dumps(amity, indent=2) + "\n")
    (st / "AmitySquare/scripts.inc").write_text(w1.scripts("AmitySquare"))
    (st / "HearthomeCity-dev-overlay").mkdir(parents=True, exist_ok=True)
    (st / "HearthomeCity-dev-overlay/map.json").write_text(json.dumps(hh, indent=2) + "\n")
    (st / "HearthomeCity-dev-overlay/map.bin").write_bytes(struct.pack("<%dH" % len(hh_bin), *hh_bin))
    bank = w1.render.Bank(eng.root / "data/tilesets/primary/general", eng.root / "data/tilesets/secondary/dewford")
    w1.render.render_cells(bank, cells, W, st / "AmitySquare/preview.png")
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "map_sha256": w1.sha(data), "doors": doors,
               "inputs_sha256": dict(sorted(eng.read.items()))}
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(json.dumps(write(a.engine, a.out), indent=2))
