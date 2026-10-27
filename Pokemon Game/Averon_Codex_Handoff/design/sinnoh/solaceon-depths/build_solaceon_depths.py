#!/usr/bin/env python3
"""Solaceon Ruins depths (W15, central lane): a branching chamber network under W8's three ruin chambers.

OFF-ENGINE staging, new construction in Averon's own General + Cave banks (no donor has these floors). W8 put three
stock ruin chambers (Desert Ruins, Island Cave, Ancient Tomb layouts, unchanged) behind Route 209's walled pockets.
Here each of them gets its own derived layout, a copy of its stock blockdata with one Granite Cave down-ladder at
(8, 5) in the inner room, so the shared Hoenn layouts stay untouched. The headers keep W8's three warps in order
and append the ladder (warp 3).

Below them, four new floors drawn with W1's cave kit (Oreburgh Gate 1F's wall pieces, Granite Cave ladders) plus the
ruin chambers' own pillar (725, always on open floor as in the source rooms):

  A / B / C (inner rooms) --ladder--> B1F hub (three up-ladders, two down-ladders)
  B1F --west ladder--> B2F West --ladder--> B3F Sanctum <--ladder-- B2F East <--east ladder-- B1F

so the hub reaches the sanctum two ways (a loop), and every chamber on Route 209 joins the same network. Every warp
is a ladder pair, reciprocal. No objects, Unown, braille, encounters, items, story or sections
(MAPSEC_PENDING_OWNER).

  build_solaceon_depths.py --engine ENGINE --out DIR
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import struct

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


w1 = load("w1", SINNOH / "iron-island/build_iron_island.py")
w8 = load("w8", SINNOH / "lost-tower/build_lost_tower.py")
MUSIC = "MUS_CAVE_OF_ORIGIN"
CHAMBER_LADDER = (8, 5)
PILLAR = ("DesertRuins", 6, 4, 725)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def const(name):
    """MAP_ constant of a map folder name (SolaceonRuins_B2F_West -> MAP_SOLACEON_RUINS_B2F_WEST)."""
    return "MAP_" + re.sub(r"(?<=[a-z])(?=[A-Z])", "_", name).upper()


class Floor(w1.Cave):
    """The W1 cave kit plus the ruin pillar and named ladders."""

    def __init__(self, eng, width, height):
        super().__init__(eng, width, height)
        self.eng = eng
        self.pillar_word = eng.word(*PILLAR)
        self.ladders = {}

    def pillar(self, x, y):
        assert all((x + dx, y + dy) in self.floor for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1))), (x, y)
        self.cells[y * self.w + x] = self.pillar_word
        self.floor.discard((x, y))

    def stair(self, name, x, y, down):
        self.ladder(x, y, self.eng, down)
        self.ladders[name] = (x, y)


def b1f(eng):
    f = Floor(eng, 44, 30)
    f.room(3, 3, 40, 26)
    f.block(10, 8, 17, 13)
    f.block(26, 8, 33, 13)
    f.block(17, 17, 26, 21)
    for x in (6, 9, 34, 37):
        f.pillar(x, 16)
    f.stair("up_a", 5, 4, down=False)
    f.stair("up_b", 38, 4, down=False)
    f.stair("up_c", 21, 25, down=False)
    f.stair("down_w", 5, 24, down=True)
    f.stair("down_e", 38, 24, down=True)
    return f


def b2f_west(eng):
    f = Floor(eng, 30, 22)
    f.room(3, 3, 26, 17)
    f.block(8, 7, 13, 12)
    f.block(18, 6, 23, 10)
    for x in (17, 20, 23):
        f.pillar(x, 14)
    f.stair("up", 5, 4, down=False)
    f.stair("down", 24, 16, down=True)
    return f


def b2f_east(eng):
    f = Floor(eng, 30, 22)
    f.room(3, 3, 26, 17)
    f.block(15, 7, 20, 12)
    f.block(6, 9, 11, 13)
    for x in (6, 9, 12):
        f.pillar(x, 5)
    f.stair("up", 24, 4, down=False)
    f.stair("down", 5, 16, down=True)
    return f


def b3f_sanctum(eng):
    f = Floor(eng, 36, 24)
    f.room(3, 3, 32, 19)
    f.block(14, 7, 21, 12)
    for y in (6, 9, 12):
        f.pillar(10, y)
        f.pillar(25, y)
    f.stair("up_w", 5, 18, down=False)
    f.stair("up_e", 30, 18, down=False)
    return f


def chamber(eng, stock):
    """A copy of a stock ruin chamber's blockdata with a down-ladder in the inner room."""
    width, height, cells = eng.cells(stock)
    x, y = CHAMBER_LADDER
    assert cells[y * width + x] & 1023 == 513 and not cells[y * width + x] & 0xC00, stock
    assert all(not cells[(y + dy) * width + x + dx] & 0xC00 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))), stock
    cells = list(cells)
    cells[y * width + x] = eng.word("GraniteCave_1F", 17, 11, 575)
    return cells, width, height


# The network: (map, ladder) <-> (map, ladder). Indices follow each floor's warp order below.
FLOORS = {"SolaceonRuins_B1F": (b1f, ["up_a", "up_b", "up_c", "down_w", "down_e"]),
          "SolaceonRuins_B2F_West": (b2f_west, ["up", "down"]),
          "SolaceonRuins_B2F_East": (b2f_east, ["up", "down"]),
          "SolaceonRuins_B3F_Sanctum": (b3f_sanctum, ["up_w", "up_e"])}
PAIRS = [(("SolaceonRuins_A", "ladder"), ("SolaceonRuins_B1F", "up_a")),
         (("SolaceonRuins_B", "ladder"), ("SolaceonRuins_B1F", "up_b")),
         (("SolaceonRuins_C", "ladder"), ("SolaceonRuins_B1F", "up_c")),
         (("SolaceonRuins_B1F", "down_w"), ("SolaceonRuins_B2F_West", "up")),
         (("SolaceonRuins_B1F", "down_e"), ("SolaceonRuins_B2F_East", "up")),
         (("SolaceonRuins_B2F_West", "down"), ("SolaceonRuins_B3F_Sanctum", "up_w")),
         (("SolaceonRuins_B2F_East", "down"), ("SolaceonRuins_B3F_Sanctum", "up_e"))]


def build(engine_root):
    eng = w1.Engine(engine_root)
    w8_maps = w8.build(engine_root)[0]
    stock = {name: s for name, s, _ in w8.RUINS}
    layouts, slots = {}, {}                 # name -> (cells, w, h); (map, ladder name) -> (x, y, warp index)
    for name, (make, order) in FLOORS.items():
        f = make(eng)
        layouts[name] = (f.cells, f.w, f.h)
        for i, ladder in enumerate(order):
            slots[(name, ladder)] = (*f.ladders[ladder], i)
    for name in stock:
        layouts[name] = chamber(eng, stock[name])
        slots[(name, "ladder")] = (*CHAMBER_LADDER, len(w8_maps[name]["warp_events"]))
    links = {}
    for a, b in PAIRS:
        links[a], links[b] = b, a
    maps = {}
    for name in layouts:
        warps = [(w["x"], w["y"], w["dest_map"], int(w["dest_warp_id"])) for w in w8_maps[name]["warp_events"]] \
            if name in stock else []
        own = sorted((i, ladder) for (m, ladder), (_, _, i) in slots.items() if m == name)
        for i, ladder in own:
            assert i == len(warps), (name, ladder)
            x, y, _ = slots[(name, ladder)]
            dest = links[(name, ladder)]
            warps.append((x, y, const(dest[0]), slots[dest][2]))
        maps[name] = w1.header(const(name), name, f"LAYOUT_{const(name)[4:]}", MUSIC, "MAP_TYPE_UNDERGROUND", warps)
    return eng, maps, layouts


def check(maps):
    """Every warp lands on a warp leading back to where it came from; W8's own warps outside the network are kept."""
    by_id = {h["id"]: h for h in maps.values()}
    for mid, h in by_id.items():
        for i, w in enumerate(h["warp_events"]):
            if w["dest_map"] not in by_id:
                continue
            back = by_id[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
            assert back["dest_map"] == mid, (mid, w, back)
            if w["dest_map"] != mid:
                assert int(back["dest_warp_id"]) == i, (mid, i, w, back)
    return True


def write(engine_root, out):
    eng, maps, layouts = build(engine_root)
    check(maps)
    out = pathlib.Path(out)
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "maps": {}}
    for name, hdr in maps.items():
        d = out / "staged" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (d / "scripts.inc").write_text(w1.scripts(name))
        cells, w, h = layouts[name]
        data = struct.pack("<%dH" % len(cells), *cells)
        border = struct.pack("<4H", *[w1.Cave(eng, 1, 1).k[529]] * 4)
        (d / "map.bin").write_bytes(data)
        (d / "border.bin").write_bytes(border)
        (d / "layout.json").write_text(json.dumps({"id": hdr["layout"], "name": name + "_Layout", "width": w,
                                                   "height": h, "primary_tileset": "gTileset_General",
                                                   "secondary_tileset": "gTileset_Cave"}, indent=2) + "\n")
        bank = w1.render.Bank(eng.root / "data/tilesets/primary/general", eng.root / "data/tilesets/secondary/cave")
        w1.render.render_cells(bank, cells, w, d / "preview.png")
        receipt["maps"][name] = {"width": w, "height": h, "map_sha256": sha(data), "border_sha256": sha(border),
                                 "warps": len(hdr["warp_events"])}
    receipt["inputs_sha256"] = dict(sorted(eng.read.items()))
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(write(a.engine, a.out)["status"])
