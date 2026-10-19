#!/usr/bin/env python3
"""Generate route201-candidate.json: a DESIGN CANDIDATE (not approved, no map
file, no map/section ID, no encounters) for Route 201 on its original DPPt
geography, 64 x 22 metatiles at the original 16 px tile scale.

Every footprint below was read tile by tile from the original DPPt overhead
(1024 x 347 px = 64 x 22 tiles of 16 px; source and method in
ROUTE201_CANDIDATE.md). A line marked DEVIATION departs from the reference and
says why. Art: the approved temporary General primary pieces already used in
Sandgem (grass, Route 101 dirt road, round trees, tall grass, ledges).
Coordinates are metatiles (x right, y down).
"""
import json
from pathlib import Path

W, H = 64, 22
F, G, R, T, L, S = 'F', 'g', 'R', 'T', 'L', 's'   # forest, grass, road, tall grass, ledge, sign
grid = [[F] * W for _ in range(H)]


def fill(x0, y0, x1, y1, k):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            grid[y][x] = k


# --- Open ground (reference: light grass) ---
fill(0, 8, 17, 11, G)          # west corridor, Lake Verity side
fill(18, 10, 41, 11, G)        # corridor continues east under the tree line
fill(24, 9, 25, 9, G)          # notches in the tree line (reference row 9)
fill(28, 9, 31, 9, G)
fill(34, 9, 35, 9, G)
fill(40, 9, 41, 9, G)
fill(0, 13, 19, 13, G)         # strip below the long ledge
fill(0, 14, 10, 14, G)
fill(9, 15, 10, 15, G)
fill(19, 14, 19, 15, G)
fill(30, 13, 35, 13, G)        # the long ledge ends at x 31: walk-around between the levels
fill(32, 12, 35, 12, G)
fill(30, 14, 31, 14, G)
fill(38, 12, 41, 13, G)
fill(38, 13, 56, 13, G)        # under the big grass patch
fill(53, 11, 57, 12, G)        # verge below the short ledge (every ledge tile lands on grass)
fill(56, 13, 56, 15, G)
fill(45, 16, 56, 16, G)        # strip above the southern tall grass
fill(52, 5, 63, 7, G)          # north-east clearing, open to the Sandgem (east) edge
fill(53, 8, 57, 9, G)
fill(61, 8, 63, 9, G)          # DEVIATION: the edge opening spans rows 6-9 so it meets Sandgem's
fill(60, 5, 63, 5, F)          # whole west verge (rows 10-13) at offset 4; row 5 closes with trees
fill(58, 9, 60, 9, G)          # open the verge so no tree is cut in half under the road

# --- Trees inside the corridors (reference clumps) ---
fill(1, 9, 2, 10, F)          # DEVIATION: reference tree touches x 0; moved one tile in so the
                               # Lake Verity edge stays open on all four rows 8-11
fill(10, 9, 13, 10, F)
fill(4, 11, 7, 12, F)          # clump that interrupts the long ledge at x 4-7

# --- Ledges (MB_JUMP_SOUTH; jump down only) ---
fill(0, 12, 3, 12, L)
fill(8, 12, 31, 12, L)         # long ledge: no gap in the original, the walk-around is its east end
fill(53, 10, 57, 10, L)        # short ledge: one-way shortcut from the Sandgem clearing down to the path

# --- Tall grass (physical only: no encounter table until wild Pokemon are approved) ---
fill(20, 13, 29, 14, T)        # middle patch south of the ledge
fill(42, 5, 52, 7, T)          # big patch: the only walking route east to Sandgem, as in DPPt
fill(42, 8, 50, 12, T)
fill(46, 17, 56, 17, T)        # southern strip

# --- Roads (reference: sand paths) ---
fill(11, 14, 18, 15, R)        # lower path
fill(15, 16, 17, 21, R)        # three wide down to Twinleaf (south edge)
fill(29, 10, 38, 11, R)        # upper path
fill(36, 12, 38, 13, R)        # joins the upper and lower paths east of the long ledge
fill(32, 14, 55, 15, R)        # main eastern path
fill(54, 12, 55, 13, R)        # up to the short ledge (which blocks it: north access is via the grass)
fill(54, 7, 63, 8, R)          # DEVIATION: reference path rows 7-8 kept; it runs on from x 60 to the
                               # edge to meet Sandgem's road (rows 11-12). An even offset (4) keeps the
                               # 2x2 trees in phase across the seam (an odd offset splits every tree row)
fill(54, 8, 55, 9, R)          # down to the short ledge

# --- Signs (reference positions) ---
for x, y in ((13, 15), (40, 11), (55, 5)):
    grid[y][x] = S


def is_(k, x, y):
    if not (0 <= x < W and 0 <= y < H):
        return k == R
    return grid[y][x] == k


PATH = {'C': 473, 'T': 465, 'B': 481, 'L': 472, 'R': 474, 'TL': 464, 'TR': 466, 'BL': 480, 'BR': 482}


def road(x, y):
    n, s, w, e = is_(R, x, y - 1), is_(R, x, y + 1), is_(R, x - 1, y), is_(R, x + 1, y)
    key = ('T' if not n else 'B' if not s else '') + ('L' if not w else 'R' if not e else '')
    return PATH[key or 'C']


def tree(x, y):
    top = not is_(F, x, y - 1) and y > 0
    bottom = not is_(F, x, y + 1) and y < H - 1
    if y % 2 == 0:
        return (470, 471)[x % 2] if top else (468, 469)[x % 2]
    return (484, 485)[x % 2] if bottom else (476, 477)[x % 2]


legend, codes = {}, {}
chars = iter('ABCDEFGHIJKMNOPQSUVWXYZabcdefhijklmnopqrtuvwxyz0123456789')


def code(m, c, e, note, **extra):
    if (m, c, e) not in codes:
        ch = next(chars)
        codes[(m, c, e)] = ch
        legend[ch] = {'metatile': m, 'collision': c, 'elevation': e, 'note': note, **extra}
    return codes[(m, c, e)]


rows = []
for y in range(H):
    line = ''
    for x in range(W):
        k = grid[y][x]
        if k == R:
            line += code(road(x, y), 0, 3, 'dirt road')
        elif k == F:
            line += code(tree(x, y), 1, 0, 'tree (solid)')
        elif k == T:
            line += code(13, 0, 3, 'tall grass (no encounter table yet)')
        elif k == L:
            line += code(135, 1, 3, 'ledge, jump south only', jump='south')
        elif k == S:
            line += code(3, 1, 0, 'sign')
        else:
            line += code(1, 0, 3, 'grass')
    rows.append(line)

plan = {
    'name': 'Route 201 - DESIGN CANDIDATE (not approved; original DPPt geography)',
    'primary': 'gTileset_General', 'secondary': 'gTileset_Dewford',
    'width': W, 'height': H, 'legend': legend, 'rows': rows, 'stamps': [],
    'exits': [
        {'name': 'east', 'edge': 'east', 'span': [6, 9], 'to': 'Sandgem Town west edge (rows 10-13)',
         'offset': -4, 'status': 'Sandgem built (PR #133); connection only after Route 201 is approved'},
        {'name': 'south', 'edge': 'south', 'span': [15, 17], 'to': 'Twinleaf Town', 'status': 'unapproved; closed'},
        {'name': 'west-upper', 'edge': 'west', 'span': [8, 11], 'to': 'Lake Verity side', 'status': 'unapproved; closed'},
        {'name': 'west-lower', 'edge': 'west', 'span': [13, 14], 'to': 'Lake Verity side (below the ledge)',
         'status': 'unapproved; closed'},
    ],
    'marks': [
        {'kind': 'exit', 'at': [0, 8], 'size': [1, 4], 'note': 'west (upper) -> Lake Verity side (unapproved; closed)'},
        {'kind': 'exit', 'at': [0, 13], 'size': [1, 2], 'note': 'west (lower) -> Lake Verity side (unapproved; closed)'},
        {'kind': 'exit', 'at': [15, 21], 'size': [3, 1], 'note': 'south -> Twinleaf Town (unapproved; closed)'},
        {'kind': 'exit', 'at': [63, 6], 'size': [1, 4], 'note': 'east -> Sandgem Town west edge (offset -4)'},
        {'kind': 'reserved', 'at': [42, 5], 'size': [11, 8], 'note': 'big grass patch: future first-encounter space (no table yet)'},
        {'kind': 'npc', 'at': [28, 14], 'note': 'NPC slot (reference: townsperson in the middle grass)'},
        {'kind': 'npc', 'at': [44, 15], 'note': 'NPC slot on the main path'},
        {'kind': 'npc', 'at': [44, 5], 'note': 'NPC slot at the top of the big patch'},
        {'kind': 'npc', 'at': [56, 9], 'note': 'NPC slot near the Sandgem end'},
    ],
}
Path(__file__).with_name('route201-candidate.json').write_text(json.dumps(plan, indent=1) + '\n')
print('\n'.join(rows))
