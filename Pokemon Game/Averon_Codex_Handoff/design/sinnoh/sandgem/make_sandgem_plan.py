#!/usr/bin/env python3
"""Generate sandgem-town.json: Sandgem Town on its original DPPt road layout.

Geometry follows the original town (owner direction 2026-10-18: "keep the same
road layout"): one east-west main road entering from Route 201 on the west
edge; Professor Rowan's lab (west) and the Pokemon Center north of it; the
Route 202 path north beside the Poke Mart; a south road between the small
south-west house and the larger south-east house; a bottom road east into the
beach that runs south to Route 219. Art is the approved temporary in-repo
General + Dewford set; buildings are exact vanilla stamps. Coordinates are
metatiles (x right, y down).
"""
import json
from pathlib import Path

W, H = 32, 28
FOREST, GRASS, ROAD, BEACH = 'F', 'g', 'R', 'b'
grid = [[FOREST] * W for _ in range(H)]


def fill(x0, y0, x1, y1, kind):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            grid[y][x] = kind


# Town interior (grass), framed by forest on the west, east and south.
fill(4, 5, 28, 21, GRASS)        # main body below the northern tree line
fill(0, 10, 3, 13, GRASS)        # verge either side of the Route 201 road
fill(19, 0, 24, 5, GRASS)        # clearing around the Route 202 path
# Roads (two metatiles wide, as in the original).
fill(0, 11, 28, 12, ROAD)        # main road: west edge (Route 201) to the east end
fill(21, 0, 22, 10, ROAD)        # north path to Route 202, beside the Mart
fill(10, 13, 11, 21, ROAD)       # south road between the two houses
fill(4, 20, 18, 21, ROAD)        # bottom road east into the beach
# Beach running south to Route 219 (south-east of town).
fill(19, 14, 28, 19, BEACH)
fill(19, 20, 24, 27, BEACH)
fill(25, 20, 28, 21, FOREST)    # trees close the beach's east side, as in the original


def is_(kind, x, y):
    if not (0 <= x < W and 0 <= y < H):
        return kind == ROAD          # roads continue off the map edge
    return grid[y][x] == kind


PATH = {  # Route 101's light dirt path (General primary), keyed by missing neighbours
    'C': 473, 'T': 465, 'B': 481, 'L': 472, 'R': 474,
    'TL': 464, 'TR': 466, 'BL': 480, 'BR': 482,
}


def road_tile(x, y):
    n, s, w, e = (is_(ROAD, x, y - 1), is_(ROAD, x, y + 1), is_(ROAD, x - 1, y), is_(ROAD, x + 1, y))
    key = ('T' if not n else 'B' if not s else '') + ('L' if not w else 'R' if not e else '')
    return PATH[key or 'C']


def forest_tile(x, y):
    """Route 101's 2x2 round trees; top and bottom rows of a stand blend into grass."""
    top = not is_(FOREST, x, y - 1) and y > 0
    bottom = not is_(FOREST, x, y + 1) and y < H - 1
    if y % 2 == 0:
        return (470, 471)[x % 2] if top else (468, 469)[x % 2]
    return (484, 485)[x % 2] if bottom else (476, 477)[x % 2]


LEGEND = {
    'g': {'metatile': 1, 'collision': 0, 'elevation': 3, 'note': 'grass (no encounters)'},
    'b': {'metatile': 292, 'collision': 0, 'elevation': 3, 'note': 'beach sand (Dewford)'},
    's': {'metatile': 3, 'collision': 1, 'elevation': 0, 'note': 'sign'},
}
CHARS = iter('ABCDEFGHIJKLMNOPQUVWXYZacdefhijklmnopqrtuvwxyz0123456789')
by_metatile = {}


def char_for(metatile, collision, elevation, note):
    key = (metatile, collision, elevation)
    if key not in by_metatile:
        c = next(CHARS)
        by_metatile[key] = c
        LEGEND[c] = {'metatile': metatile, 'collision': collision, 'elevation': elevation, 'note': note}
    return by_metatile[key]


rows = []
for y in range(H):
    line = []
    for x in range(W):
        kind = grid[y][x]
        if kind == ROAD:
            line.append(char_for(road_tile(x, y), 0, 3, 'dirt road (General primary)'))
        elif kind == FOREST:
            line.append(char_for(forest_tile(x, y), 1, 0, 'tree (General primary, solid)'))
        else:
            line.append(kind)
    rows.append(line)
for x, y in ((19, 9), (23, 9), (13, 17), (21, 18)):   # town, PC, house and beach signs
    rows[y][x] = 's'
rows = [''.join(r) for r in rows]

plan = {
    'name': 'Sandgem Town (permanent first Sinnoh map; original DPPt road layout)',
    'primary': 'gTileset_General', 'secondary': 'gTileset_Dewford',
    'width': W, 'height': H, 'legend': LEGEND, 'rows': rows,
    'stamps': [
        {'note': "Rowan's lab main block (RESERVED story site; no interior yet)", 'from': 'LAYOUT_DEWFORD_TOWN',
         'src': [1, 0, 5, 4], 'at': [4, 6]},
        {'note': "Rowan's lab annex", 'from': 'LAYOUT_DEWFORD_TOWN', 'src': [16, 11, 4, 4], 'at': [9, 6]},
        {'note': 'Pokemon Center (primary-only art, grass roof row; door +1,+3)', 'from': 'LAYOUT_PETALBURG_CITY',
         'src': [19, 13, 4, 4], 'at': [14, 6]},
        {'note': 'Poke Mart beside the Route 202 path (primary-only; door +1,+3)', 'from': 'LAYOUT_MAUVILLE_CITY',
         'src': [22, 11, 4, 4], 'at': [24, 6]},
        {'note': 'south-west house (door +1,+3)', 'from': 'LAYOUT_DEWFORD_TOWN', 'src': [16, 11, 4, 4], 'at': [5, 15]},
        {'note': 'south-east house (RESERVED residence; door +2,+3)', 'from': 'LAYOUT_DEWFORD_TOWN',
         'src': [1, 0, 5, 4], 'at': [14, 14]},
    ],
    'marks': [
        {'kind': 'exit', 'at': [0, 11], 'size': [1, 2], 'note': 'west exit -> Route 201 (closed until the route exists)'},
        {'kind': 'exit', 'at': [21, 0], 'size': [2, 1], 'note': 'north exit -> Route 202 (closed until the route exists)'},
        {'kind': 'exit', 'at': [19, 27], 'size': [6, 1], 'note': 'south exit -> Route 219 beach (closed until the route exists)'},
        {'kind': 'warp', 'at': [15, 9], 'note': 'Pokemon Center door (warp 0)'},
        {'kind': 'warp', 'at': [25, 9], 'note': 'Poke Mart door (no interior yet)'},
        {'kind': 'warp', 'at': [6, 9], 'note': "Rowan's lab door (reserved; no warp)"},
        {'kind': 'warp', 'at': [6, 18], 'note': 'south-west house door (no interior yet)'},
        {'kind': 'warp', 'at': [16, 17], 'note': 'south-east residence door (reserved; no warp)'},
        {'kind': 'npc', 'at': [8, 12], 'note': 'townsfolk on the main road'},
        {'kind': 'npc', 'at': [23, 16], 'note': 'beachgoer'},
        {'kind': 'reserved', 'at': [4, 10], 'size': [9, 1], 'note': "space in front of Rowan's lab"},
    ],
}
out = Path(__file__).with_name('sandgem-town.json')
out.write_text(json.dumps(plan, indent=1) + '\n')
print('\n'.join(rows))
