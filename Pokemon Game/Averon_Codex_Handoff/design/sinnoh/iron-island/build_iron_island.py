#!/usr/bin/env python3
"""Iron Island + Canalave harbor batch (W1, western lane): new physical geography in Averon's own banks.

OFF-ENGINE staging. The pinned donor (LiderMorti00 @ 38228bb5) has no Iron Island and no Canalave interiors, so
nothing here is donor-derived. Every metatile word (ID + collision + elevation) is copied from a cell of an existing
Averon layout, and every composition rule is checked against those layouts:

- Iron Island (40 x 32, General + Dewford, the bank pair of Averon's Sandgem/Twinleaf/Verity maps): an ocean
  island with a sand beach and grass interior. Every shore cell's 8-neighbour sand/water pattern occurs in Averon's
  Route 105/106/107 or Dewford with the same metatile (strict; an unattested pattern refuses the build). The hill is
  Lake Verity's islet hill stretched along its uniform rows/columns, with Route 106's open cave mouth; the house is
  Dewford's house; the pier is Dewford's pier.
- Iron Island 1F / B1F (General + Cave): rectangular chambers and rock blocks drawn with the wall kit of Averon's
  Oreburgh Gate 1F, the cave-mouth exit and ladders of Granite Cave.
- Iron Island house, Canalave Harbor and Canalave Pokemon Center 1F reuse the existing shared layouts
  LAYOUT_HOUSE1, LAYOUT_HARBOR and LAYOUT_POKEMON_CENTER_1F unchanged (no new layout, no services or NPCs).
- Canalave City overlay: derived from the merged canalave-west staging (read-only). Two of its closed buildings get
  doors: the Pokemon Center door gets a warp, and the closed pier house at (27-30, 13) gets the door metatile (537)
  of the same bank's north-west house in place of its doorless door picture (525). Nothing else changes.

The Canalave Harbor <-> Iron Island pier link is a neutral DEV portal pair (step-on triggers, as Floaroma Meadow's):
no boat, ferry story, NPC, flag or unlock. Keeping it in production is an owner decision. No objects, trainers,
encounters, items, music beyond stock constants, section IDs (MAPSEC_PENDING_OWNER) or save changes.

  build_iron_island.py --engine ENGINE --out DIR       staged maps, renders and receipt (DIR outside engine/)
"""
import argparse
import collections
import hashlib
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render  # noqa: E402

CANALAVE = HERE.parent / "canalave-west"
PENDING = "MAPSEC_PENDING_OWNER"
COLL = 1 << 10
OCEAN_CORPUS = ("Route105", "Route106", "Route107", "DewfordTown")
CAVE_CORPUS = ("OreburghGate_1F", "GraniteCave_1F", "GraniteCave_B1F")


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Engine:
    def __init__(self, root):
        self.root = pathlib.Path(root)
        layouts = json.loads((self.root / "data/layouts/layouts.json").read_text())["layouts"]
        self.layouts = {l["name"].removesuffix("_Layout"): l for l in layouts}
        self.layout_ids = {l["id"]: l for l in layouts}
        self.read = {}

    def cells(self, name):
        l = self.layouts[name]
        raw = self.file(l["blockdata_filepath"])
        assert len(raw) == l["width"] * l["height"] * 2, name
        return l["width"], l["height"], list(struct.unpack("<%dH" % (len(raw) // 2), raw))

    def file(self, rel):
        data = (self.root / rel).read_bytes()
        self.read[rel] = sha(data)
        return data

    def word(self, name, x, y, mid):
        """The exact cell word of an existing layout, asserting its metatile ID."""
        w, _, c = self.cells(name)
        assert c[y * w + x] & 1023 == mid, (name, x, y, c[y * w + x] & 1023, mid)
        return c[y * w + x]

    def words(self, names):
        """Most common full word for every metatile ID in these layouts (collision/elevation as drawn there)."""
        seen = collections.defaultdict(collections.Counter)
        for n in names:
            for v in self.cells(n)[2]:
                seen[v & 1023][v] += 1
        return {m: c.most_common(1)[0][0] for m, c in seen.items()}


# ---------------------------------------------------------------------------------------------- ocean / island
NB8 = ((0, -1), (1, 0), (0, 1), (-1, 0), (1, -1), (1, 1), (-1, 1), (-1, -1))
WATER_IDS = {283, 285, 291, 293, 299, 300, 301, 325, 326, 368}
SAND_IDS = {284, 292, 317, 318}


def shore_table(eng):
    """(class, 8 neighbour sand flags) -> metatile, learned from pure sand/water cells of existing ocean maps."""
    table = collections.defaultdict(collections.Counter)
    for name in OCEAN_CORPUS:
        w, h, c = eng.cells(name)

        def cls(x, y):
            if not (0 <= x < w and 0 <= y < h):
                return None
            v = c[y * w + x]
            return "W" if v & 1023 in WATER_IDS and not v & 0xC00 else "S" if v & 1023 in SAND_IDS else "X"

        for y in range(h):
            for x in range(w):
                me = cls(x, y)
                nb = [cls(x + dx, y + dy) for dx, dy in NB8]
                if me in ("W", "S") and None not in nb and "X" not in nb:
                    table[(me,) + tuple(n == "S" for n in nb)][c[y * w + x] & 1023] += 1
    return table


ISLAND_W, ISLAND_H = 40, 32
# Land outline (sand ring + grass), rows of [x0, x1] spans; everything else is open water.
LAND = {y: (5, 33) for y in range(4, 29)}   # a rectangle: every edge and corner pattern is attested
GRASS = {y: (7, 31) for y in range(7, 26)}
HILL = (11, 7, 17, 6)          # x, y, width, height on grass; cave mouth at the bottom row's centre
HILL_SMALL = [(24, 15, 7, 4)]  # Verity's islet size, no mouth
HOUSE_AT = (8, 19)             # Dewford house (5 x 4), door at +2, +3
PIER = (34, 20, 5)             # x (first plank), row, planks; pilings on the row below
BOULDERS = [(6, 9), (32, 13), (6, 24), (32, 26), (13, 27)]
TREES = [(7, 7), (9, 7), (7, 9), (28, 7), (30, 7), (30, 9), (7, 11), (7, 13), (7, 15), (28, 23), (30, 23)]  # 2x2 tops
PATH = [((19, 13), (19, 23)), ((19, 20), (31, 20)), ((10, 23), (19, 23))]   # sand walkways (inclusive spans)


def island(eng):
    dew = eng.words(OCEAN_CORPUS)
    water, sand, grass = eng.word("Route106", 26, 8, 368), eng.word("DewfordTown", 8, 9, 292), \
        eng.word("LakeVerity", 19, 20, 1)
    grid = [["W"] * ISLAND_W for _ in range(ISLAND_H)]
    for y, (x0, x1) in LAND.items():
        for x in range(x0, x1 + 1):
            grid[y][x] = "S"
    table = shore_table(eng)
    cells = [water] * (ISLAND_W * ISLAND_H)
    used = collections.Counter()
    for y in range(ISLAND_H):
        for x in range(ISLAND_W):
            nb = tuple((0 <= x + dx < ISLAND_W and 0 <= y + dy < ISLAND_H and grid[y + dy][x + dx] == "S")
                       for dx, dy in NB8)
            key = (grid[y][x],) + nb
            if not any(nb) and grid[y][x] == "W":
                continue
            if key not in table:
                raise SystemExit(f"unattested shore pattern at {(x, y)}: {key}")
            mid = table[key].most_common(1)[0][0]
            cells[y * ISLAND_W + x] = dew[mid]
            used[mid] += 1
    for y, (x0, x1) in GRASS.items():
        for x in range(x0, x1 + 1):
            cells[y * ISLAND_W + x] = grass
    for (x0, y0), (x1, y1) in PATH:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                cells[y * ISLAND_W + x] = sand
    verity = eng.words(("LakeVerity",))
    for tx, ty in TREES:                                  # Lake Verity's 2 x 2 tree on grass
        for (dx, dy), mid in zip(((0, 0), (1, 0), (0, 1), (1, 1)), (470, 471, 478, 479)):
            assert cells[(ty + dy) * ISLAND_W + tx + dx] == grass, (tx, ty)
            cells[(ty + dy) * ISLAND_W + tx + dx] = verity[mid]
    stamp_hill(eng, cells, ISLAND_W, *HILL, door=True)
    for h in HILL_SMALL:
        stamp_hill(eng, cells, ISLAND_W, *h, door=False)
    hx, hy = HOUSE_AT
    for j in range(4):
        for i in range(5):
            cells[(hy + j) * ISLAND_W + hx + i] = eng.cells("DewfordTown")[2][j * 20 + 1 + i]
    assert cells[(hy + 3) * ISLAND_W + hx + 2] & 1023 == 549   # Dewford's animated house door
    px, py, n = PIER
    for i in range(n):
        cells[py * ISLAND_W + px + i] = eng.word("DewfordTown", 11 if i == 0 else 12, 9, 552 if i == 0 else 553)
        cells[(py + 1) * ISLAND_W + px + i] = eng.word("DewfordTown", 11 if i == 0 else 12, 10, 560 if i == 0 else 561)
    boulder = eng.word("DewfordTown", 18, 15, 226)
    for x, y in BOULDERS:
        assert cells[y * ISLAND_W + x] & 1023 in (292, 1), (x, y)
        cells[y * ISLAND_W + x] = boulder
    door = (HILL[0] + HILL[2] // 2, HILL[1] + HILL[3] - 1)
    house_door = (hx + 2, hy + 3)
    # Step-on portal (as Floaroma Meadow's): the warp and its coord trigger share the pier's end plank. Arriving by
    # warp never fires a coord trigger; walking onto it from the plank before does.
    return cells, dict(cave=door, house=house_door, pier_arrive=(px + n - 1, py), pier_trigger=(px + n - 1, py),
                       shore_metatiles=dict(sorted(used.items())))


def stamp_hill(eng, cells, width, x0, y0, w, h, door):
    """Lake Verity's islet hill (7 x 4) stretched along its uniform middle column and top rows."""
    islet = {(x, y): eng.cells("LakeVerity")[2][y * 48 + x] for x in range(20, 27) for y in range(16, 20)}
    src = lambda x, y: islet[(x, y)]
    assert [src(x, 16) & 1023 for x in range(20, 27)] == [227, 108, 108, 108, 108, 108, 228]
    assert [src(x, 19) & 1023 for x in range(20, 27)] == [120, 121, 121, 167, 121, 121, 122]
    rows = [16] + [16] * (h - 4) + [17, 18, 19]       # repeat the top row (all 108 between the corners)
    for j, sy in enumerate(rows):
        for i in range(w):
            sx = 20 if i == 0 else 26 if i == w - 1 else 21 if i == 1 else 25 if i == w - 2 else 22
            v = src(sx, sy)
            if j >= 1 and j < h - 3:                     # extra top rows: mountain-top fill with the side edges
                v = src(20 if i == 0 else 26 if i == w - 1 else 22, 17) if i in (0, w - 1) else src(22, 16)
            if v & 1023 == 167:
                v = src(22, 19)
            cells[(y0 + j) * width + x0 + i] = v
    if door:
        cells[(y0 + h - 1) * width + x0 + w // 2] = eng.word("Route106", 48, 16, 167)   # open cave mouth


# ---------------------------------------------------------------------------------------------- cave kit
class Cave:
    """Oreburgh Gate 1F's wall kit: walls by the side they face, diagonal corner pieces (see the module doc)."""

    def __init__(self, eng, width, height):
        self.w, self.h = width, height
        self.k = eng.words(CAVE_CORPUS)
        self.cells = [self.k[529]] * (width * height)
        self.floor = set()

    def put(self, x, y, mid):
        self.cells[y * self.w + x] = self.k[mid]

    def room(self, x0, y0, x1, y1):
        for y in range(y0 - 2, y1 + 3):
            for x in range(x0 - 2, x1 + 3):
                self.put(x, y, 529)
        for x in range(x0 - 1, x1 + 2):
            self.put(x, y0 - 2, 537)
        self.put(x0 - 2, y0 - 2, 539), self.put(x1 + 2, y0 - 2, 540)
        for x in range(x0, x1 + 1):
            self.put(x, y0 - 1, 537)
        self.put(x0 - 2, y0 - 1, 530), self.put(x0 - 1, y0 - 1, 539)
        self.put(x1 + 1, y0 - 1, 540), self.put(x1 + 2, y0 - 1, 528)
        for y in range(y0, y1 + 1):
            self.put(x0 - 2, y, 530), self.put(x0 - 1, y, 530)
            self.put(x1 + 1, y, 528), self.put(x1 + 2, y, 528)
            for x in range(x0, x1 + 1):
                self.put(x, y, 513)
                self.floor.add((x, y))
        self.put(x0 - 2, y1 + 1, 530), self.put(x1 + 2, y1 + 1, 528)
        for x in range(x0 - 1, x1 + 2):
            self.put(x, y1 + 1, 521)
        for x in range(x0 - 2, x1 + 3):
            self.put(x, y1 + 2, 521)

    def block(self, x0, y0, x1, y1):
        assert x1 - x0 >= 3 and y1 - y0 >= 3
        assert all((x, y) in self.floor for x in range(x0 - 2, x1 + 3) for y in range(y0 - 2, y1 + 3))
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, 529)
                self.floor.discard((x, y))
        for x in range(x0 + 1, x1):
            self.put(x, y0, 521)
        self.put(x0, y0, 520), self.put(x1, y0, 522)
        for x in range(x0 + 2, x1 - 1):
            self.put(x, y0 + 1, 521)
        self.put(x0, y0 + 1, 528), self.put(x0 + 1, y0 + 1, 520), self.put(x1 - 1, y0 + 1, 522), self.put(x1, y0 + 1, 530)
        for y in range(y0 + 2, y1 - 1):
            self.put(x0, y, 528), self.put(x0 + 1, y, 528), self.put(x1 - 1, y, 530), self.put(x1, y, 530)
        for x in range(x0 + 2, x1 - 1):
            self.put(x, y1 - 1, 537)
        self.put(x0, y1 - 1, 528), self.put(x0 + 1, y1 - 1, 536), self.put(x1 - 1, y1 - 1, 538), self.put(x1, y1 - 1, 530)
        for x in range(x0 + 1, x1):
            self.put(x, y1, 537)
        self.put(x0, y1, 536), self.put(x1, y1, 538)

    def exit_south(self, x, y, eng):
        """Granite Cave 1F's cave-mouth exit: arrow-warp floor over the 600/601/602 opening."""
        assert (x, y) in self.floor and (x, y + 1) not in self.floor
        self.cells[y * self.w + x] = eng.word("GraniteCave_1F", 37, 12, 519)
        for i, m in enumerate((600, 601, 602)):
            self.cells[(y + 1) * self.w + x - 1 + i] = eng.word("GraniteCave_1F", 36 + i, 13, m)

    def ladder(self, x, y, eng, down):
        assert (x, y) in self.floor
        self.cells[y * self.w + x] = eng.word("GraniteCave_1F", 17, 11, 575) if down else \
            eng.word("GraniteCave_B1F", 4, 21, 573)


def cave_1f(eng):
    cv = Cave(eng, 26, 19)
    cv.room(3, 3, 22, 14)
    cv.block(8, 6, 15, 10)
    cv.exit_south(12, 14, eng)
    cv.ladder(20, 4, eng, down=True)
    return cv, dict(exit=(12, 14), ladder=(20, 4))


def cave_b1f(eng):
    cv = Cave(eng, 32, 25)
    cv.room(3, 3, 28, 20)
    cv.block(7, 7, 12, 11)
    cv.block(17, 12, 24, 16)
    cv.ladder(5, 4, eng, down=False)
    cv.ladder(26, 18, eng, down=True)
    return cv, dict(ladder=(5, 4), down=(26, 18))


def cave_b2f(eng):
    cv = Cave(eng, 30, 22)
    cv.room(3, 3, 26, 17)
    cv.block(7, 6, 12, 10)
    cv.block(16, 9, 22, 13)
    cv.ladder(24, 15, eng, down=False)
    cv.ladder(5, 16, eng, down=True)
    return cv, dict(ladder=(24, 15), down=(5, 16))


def cave_b3f(eng):
    cv = Cave(eng, 36, 26)
    cv.room(3, 3, 32, 21)
    cv.block(7, 6, 13, 11)
    cv.block(20, 6, 27, 10)
    cv.block(12, 14, 22, 18)
    cv.ladder(30, 19, eng, down=False)
    return cv, dict(ladder=(30, 19))


# ---------------------------------------------------------------------------------------------- Canalave overlay
PIER_HOUSE_ROW = 13
PIER_HOUSE_X = 27
MORE_HOUSE_DOORS = [(25, 31), (9, 39), (10, 45), (25, 45)]    # closed shells with a doorless door picture (525)


def canalave_overlay():
    """Merged canalave-west staging + two doors. Returns (map.bin, map.json dict, receipt)."""
    folder = CANALAVE / "staged/CanalaveCity"
    raw = (folder / "averon-map.bin").read_bytes()
    header = json.loads((folder / "map.json").read_text())
    cells = list(struct.unpack("<%dH" % (len(raw) // 2), raw))
    w = 38
    row = [cells[PIER_HOUSE_ROW * w + PIER_HOUSE_X + i] for i in range(4)]
    assert [c & 1023 for c in row] == [523, 524, 525, 526], row
    # 525 draws the door picture without door behaviour; 537 (the north-west house's door at (7, 17)) is the same
    # picture with MB_ANIMATED_DOOR. Collision/elevation bits of the cell are kept.
    assert cells[17 * w + 7] & 1023 == 537
    door = PIER_HOUSE_ROW * w + PIER_HOUSE_X + 2
    cells[door] = (cells[door] & 0xFC00) | 537
    for x, y in MORE_HOUSE_DOORS:                                   # same door-picture swap, same kept bits
        i = y * w + x
        assert cells[i] & 1023 == 525 and not cells[i + w] & 0xC00, (x, y)
        cells[i] = (cells[i] & 0xFC00) | 537
    assert cells[22 * w + 28] & 1023 == 545                         # Pokemon Center door (closed: no warp)
    assert header["warp_events"] == [{"x": 33, "y": 50, "elevation": 0, "dest_map": "MAP_ROUTE218_WEST",
                                      "dest_warp_id": "1"}]
    header["warp_events"] += [
        {"x": 28, "y": 22, "elevation": 0, "dest_map": "MAP_CANALAVE_CITY_POKEMON_CENTER_1F", "dest_warp_id": "0"},
        {"x": PIER_HOUSE_X + 2, "y": PIER_HOUSE_ROW, "elevation": 0, "dest_map": "MAP_CANALAVE_CITY_HARBOR",
         "dest_warp_id": "0"},
        {"x": 7, "y": 17, "elevation": 0, "dest_map": "MAP_CANALAVE_CITY_LIBRARY_1F", "dest_warp_id": "0"},
        {"x": 9, "y": 31, "elevation": 0, "dest_map": "MAP_CANALAVE_CITY_HOUSE2", "dest_warp_id": "0"}] + [
        {"x": x, "y": y, "elevation": 0, "dest_map": f"MAP_CANALAVE_CITY_HOUSE{n}", "dest_warp_id": "0"}
        for n, (x, y) in enumerate(MORE_HOUSE_DOORS, 3)]
    assert cells[17 * w + 7] & 1023 == 537 and cells[31 * w + 9] & 1023 == 537   # existing animated doors
    data = struct.pack("<%dH" % len(cells), *cells)
    changed = [(i % w, i // w) for i, (a, b) in enumerate(zip(struct.unpack("<%dH" % (len(raw) // 2), raw), cells)) if a != b]
    return data, header, dict(source_sha256=sha(raw), output_sha256=sha(data), changed_cells=changed)


# ---------------------------------------------------------------------------------------------- headers
def header(map_id, name, layout, music, kind, warps, coords=(), escape=False):
    return {"id": map_id, "name": name, "layout": layout, "music": music, "region": "REGION_SINNOH",
            "region_map_section": PENDING, "weather": "WEATHER_NONE" if kind != "MAP_TYPE_ROUTE" else "WEATHER_SUNNY",
            "map_type": kind, "allow_cycling": kind == "MAP_TYPE_ROUTE", "allow_escaping": escape,
            "allow_running": kind != "MAP_TYPE_INDOOR", "show_map_name": kind != "MAP_TYPE_INDOOR",
            "requires_flash": False, "battle_scene": "MAP_BATTLE_SCENE_NORMAL", "connections": [],
            "object_events": [],
            "warp_events": [{"x": x, "y": y, "elevation": 0, "dest_map": d, "dest_warp_id": str(i)} for x, y, d, i in warps],
            "coord_events": [{"type": "trigger", "x": x, "y": y, "elevation": 0, "var": "VAR_TEMP_1", "var_value": "0",
                              "script": f"{name}_EventScript_{label}"} for x, y, label, _ in coords],
            "bg_events": []}


def scripts(name, coords=()):
    text = f"{name}_MapScripts::\n\t.byte 0\n"
    for _, _, label, (dest, warp) in coords:
        text += f"\n{name}_EventScript_{label}::\n\twarp {dest}, {warp}\n\twaitstate\n\tend\n"
    return text


def build(engine_root):
    eng = Engine(engine_root)
    out = {}
    isl, ipts = island(eng)
    c1, p1 = cave_1f(eng)
    c2, p2 = cave_b1f(eng)
    c3, p3 = cave_b2f(eng)
    c4, p4 = cave_b3f(eng)
    canal_bin, canal_header, canal_receipt = canalave_overlay()
    (cx, cy), (hx, hy), (ax, ay), (tx, ty) = ipts["cave"], ipts["house"], ipts["pier_arrive"], ipts["pier_trigger"]
    maps = {
        "IronIsland": (header("MAP_IRON_ISLAND", "IronIsland", "LAYOUT_IRON_ISLAND", "MUS_DEWFORD", "MAP_TYPE_ROUTE",
                              [(cx, cy, "MAP_IRON_ISLAND_1F", 0), (hx, hy, "MAP_IRON_ISLAND_HOUSE", 0),
                               (ax, ay, "MAP_CANALAVE_CITY_HARBOR", 2)],
                              [(tx, ty, "ToHarbor", ("MAP_CANALAVE_CITY_HARBOR", 2))]),
                       (isl, ISLAND_W, ISLAND_H, "gTileset_General", "gTileset_Dewford")),
        "IronIsland_House": (header("MAP_IRON_ISLAND_HOUSE", "IronIsland_House", "LAYOUT_HOUSE1", "MUS_DEWFORD",
                                    "MAP_TYPE_INDOOR", [(3, 8, "MAP_IRON_ISLAND", 1), (4, 8, "MAP_IRON_ISLAND", 1)]), None),
        "IronIsland_1F": (header("MAP_IRON_ISLAND_1F", "IronIsland_1F", "LAYOUT_IRON_ISLAND_1F", "MUS_CAVE_OF_ORIGIN",
                                 "MAP_TYPE_UNDERGROUND", [(*p1["exit"], "MAP_IRON_ISLAND", 0),
                                                          (*p1["ladder"], "MAP_IRON_ISLAND_B1F", 0)]),
                          (c1.cells, c1.w, c1.h, "gTileset_General", "gTileset_Cave")),
        "IronIsland_B1F": (header("MAP_IRON_ISLAND_B1F", "IronIsland_B1F", "LAYOUT_IRON_ISLAND_B1F", "MUS_CAVE_OF_ORIGIN",
                                  "MAP_TYPE_UNDERGROUND", [(*p2["ladder"], "MAP_IRON_ISLAND_1F", 1),
                                                           (*p2["down"], "MAP_IRON_ISLAND_B2F", 0)]),
                           (c2.cells, c2.w, c2.h, "gTileset_General", "gTileset_Cave")),
        "IronIsland_B2F": (header("MAP_IRON_ISLAND_B2F", "IronIsland_B2F", "LAYOUT_IRON_ISLAND_B2F", "MUS_CAVE_OF_ORIGIN",
                                  "MAP_TYPE_UNDERGROUND", [(*p3["ladder"], "MAP_IRON_ISLAND_B1F", 1),
                                                           (*p3["down"], "MAP_IRON_ISLAND_B3F", 0)]),
                           (c3.cells, c3.w, c3.h, "gTileset_General", "gTileset_Cave")),
        "IronIsland_B3F": (header("MAP_IRON_ISLAND_B3F", "IronIsland_B3F", "LAYOUT_IRON_ISLAND_B3F", "MUS_CAVE_OF_ORIGIN",
                                  "MAP_TYPE_UNDERGROUND", [(*p4["ladder"], "MAP_IRON_ISLAND_B2F", 1)]),
                           (c4.cells, c4.w, c4.h, "gTileset_General", "gTileset_Cave")),
        # The large north-west building: two floors in Lilycove Museum's stock layouts (neutral; no exhibits/NPCs).
        "CanalaveCity_Library_1F": (header("MAP_CANALAVE_CITY_LIBRARY_1F", "CanalaveCity_Library_1F",
                                           "LAYOUT_LILYCOVE_CITY_LILYCOVE_MUSEUM_1F", "MUS_ROUTE110", "MAP_TYPE_INDOOR",
                                           [(9, 13, "MAP_CANALAVE_CITY", 3), (10, 13, "MAP_CANALAVE_CITY", 3),
                                            (16, 1, "MAP_CANALAVE_CITY_LIBRARY_2F", 0)]), None),
        "CanalaveCity_Library_2F": (header("MAP_CANALAVE_CITY_LIBRARY_2F", "CanalaveCity_Library_2F",
                                           "LAYOUT_LILYCOVE_CITY_LILYCOVE_MUSEUM_2F", "MUS_ROUTE110", "MAP_TYPE_INDOOR",
                                           [(13, 1, "MAP_CANALAVE_CITY_LIBRARY_1F", 2)]), None),
        "CanalaveCity_House2": (header("MAP_CANALAVE_CITY_HOUSE2", "CanalaveCity_House2", "LAYOUT_HOUSE1", "MUS_ROUTE110",
                                       "MAP_TYPE_INDOOR", [(3, 8, "MAP_CANALAVE_CITY", 4), (4, 8, "MAP_CANALAVE_CITY", 4)]), None),
        **{f"CanalaveCity_House{n}": (header(f"MAP_CANALAVE_CITY_HOUSE{n}", f"CanalaveCity_House{n}", "LAYOUT_HOUSE1",
                                             "MUS_ROUTE110", "MAP_TYPE_INDOOR",
                                             [(3, 8, "MAP_CANALAVE_CITY", n + 2), (4, 8, "MAP_CANALAVE_CITY", n + 2)]), None)
           for n in range(3, 7)},
        "CanalaveCity_Harbor": (header("MAP_CANALAVE_CITY_HARBOR", "CanalaveCity_Harbor", "LAYOUT_HARBOR", "MUS_ROUTE110",
                                       "MAP_TYPE_INDOOR", [(11, 14, "MAP_CANALAVE_CITY", 2), (12, 14, "MAP_CANALAVE_CITY", 2),
                                                           (8, 10, "MAP_IRON_ISLAND", 2)],
                                       [(8, 10, "ToIronIsland", ("MAP_IRON_ISLAND", 2))]), None),
        "CanalaveCity_PokemonCenter_1F": (header("MAP_CANALAVE_CITY_POKEMON_CENTER_1F", "CanalaveCity_PokemonCenter_1F",
                                                 "LAYOUT_POKEMON_CENTER_1F", "MUS_POKE_CENTER", "MAP_TYPE_INDOOR",
                                                 [(6, 8, "MAP_CANALAVE_CITY", 1), (7, 8, "MAP_CANALAVE_CITY", 1)]), None),
    }
    coords = {"IronIsland": [(tx, ty, "ToHarbor", ("MAP_CANALAVE_CITY_HARBOR", 2))],
              "CanalaveCity_Harbor": [(8, 10, "ToIronIsland", ("MAP_IRON_ISLAND", 2))]}
    # Shared layouts must exist unchanged; their warp tiles are the stock ones.
    for name, (hdr, layout) in maps.items():
        if layout is None:
            assert hdr["layout"] in eng.layout_ids, hdr["layout"]
    return eng, maps, coords, (canal_bin, canal_header, canal_receipt)


def check(eng, maps, canal):
    """Reciprocal warps and walkable warp/trigger tiles; the runtime map_qa audit is separate."""
    canal_bin, canal_header, _ = canal
    headers = {h["id"]: h for h, _ in maps.values()}
    headers["MAP_CANALAVE_CITY"] = canal_header
    allowed_foreign = {("MAP_CANALAVE_CITY", "MAP_ROUTE218_WEST")}
    for mid, h in headers.items():
        for i, w in enumerate(h["warp_events"]):
            if (mid, w["dest_map"]) in allowed_foreign:
                continue
            dest = headers[w["dest_map"]]
            back = dest["warp_events"][int(w["dest_warp_id"])]
            assert back["dest_map"] == mid, (mid, i, w, back)
            assert any(int(back["dest_warp_id"]) == j for j, x in enumerate(h["warp_events"])
                       if (x["x"], x["y"]) == (h["warp_events"][int(back["dest_warp_id"])]["x"],
                                               h["warp_events"][int(back["dest_warp_id"])]["y"]))
    return True


def write(engine_root, out):
    out = pathlib.Path(out)
    if "engine" in out.resolve().parts:
        raise SystemExit("--out must be outside engine/")
    eng, maps, coords, canal = build(engine_root)
    check(eng, maps, canal)
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "maps": {}, "inputs_sha256": None}
    for name, (hdr, layout) in maps.items():
        d = out / "staged" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (d / "scripts.inc").write_text(scripts(name, coords.get(name, ())))
        entry = {"layout": hdr["layout"]}
        if layout:
            cells, w, h, prim, sec = layout
            data = struct.pack("<%dH" % len(cells), *cells)
            (d / "map.bin").write_bytes(data)
            water = cells[0] if name == "IronIsland" else Cave(eng, 1, 1).k[529]
            border = struct.pack("<4H", *[water] * 4)
            (d / "border.bin").write_bytes(border)
            (d / "layout.json").write_text(json.dumps({"id": hdr["layout"], "name": name + "_Layout", "width": w,
                                                       "height": h, "primary_tileset": prim, "secondary_tileset": sec},
                                                      indent=2) + "\n")
            bank = render.Bank(eng.root / f"data/tilesets/primary/{prim[9:].lower()}",
                               eng.root / f"data/tilesets/secondary/{sec[9:].lower()}")
            render.render_cells(bank, cells, w, d / "preview.png")
            entry.update(width=w, height=h, map_sha256=sha(data), border_sha256=sha(border))
        receipt["maps"][name] = entry
    d = out / "staged" / "CanalaveCity"
    d.mkdir(parents=True, exist_ok=True)
    canal_bin, canal_header, canal_receipt = canal
    (d / "averon-map.bin").write_bytes(canal_bin)
    (d / "map.json").write_text(json.dumps(canal_header, indent=2) + "\n")
    receipt["canalave_overlay"] = canal_receipt
    receipt["inputs_sha256"] = dict(sorted(eng.read.items()))
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    args = p.parse_args()
    print(json.dumps(write(args.engine, args.out), indent=2))


if __name__ == "__main__":
    main()
