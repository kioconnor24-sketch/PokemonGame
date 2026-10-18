#!/usr/bin/env python3
"""Generate route201-candidate.json: a DESIGN CANDIDATE (not approved, no map
file, no map/section ID, no encounters) for Route 201 on its original DPPt
geography, 64 x 22 metatiles at the original 16 px tile scale:
- west: open corridor toward Lake Verity (left edge, rows 8-12);
- south: sand path down to Twinleaf Town (columns 15-18);
- east: path up to Sandgem Town (right edge, rows 7-9);
- a long south-facing ledge across the west half and a short one in the east;
- three tall-grass patches (physical only: no encounter table until approved).
Art: the approved temporary General primary pieces already used in Sandgem
(grass, Route 101 dirt road, round trees, tall grass, ledges).
"""
import json
from pathlib import Path

W, H = 64, 22
F, G, R, T, L = 'F', 'g', 'R', 'T', 'L'   # forest, grass, road, tall grass, ledge
grid = [[F] * W for _ in range(H)]


def fill(x0, y0, x1, y1, k):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            grid[y][x] = k


# Open ground (walkable grass) following the original corridor.
fill(0, 8, 40, 12, G)          # west corridor (Lake Verity side) above the long ledge
fill(8, 13, 31, 16, G)         # lower corridor below the ledge
fill(14, 15, 18, 21, G)        # south leg toward Twinleaf
fill(31, 13, 58, 16, G)        # eastern lower corridor
fill(40, 4, 53, 13, G)         # clearing around the big grass patch
fill(52, 6, 63, 10, G)         # approach to the Sandgem exit
# Long south-facing ledge (jump south only) across the west half, with one gap.
fill(0, 12, 30, 12, L)
fill(9, 12, 10, 12, G)         # walk-around gap so the west corridor stays reachable both ways
fill(53, 10, 57, 10, L)        # short ledge in the east
# Tall grass (physical only).
fill(20, 13, 29, 14, T)
fill(42, 5, 51, 12, T)
fill(46, 17, 57, 17, G)
fill(46, 17, 57, 17, T)
# Paths (two wide), as in the original.
fill(10, 14, 18, 15, R)        # from the lower corridor ...
fill(16, 15, 17, 21, R)        # ... down to Twinleaf (south edge)
fill(28, 10, 38, 11, R)        # middle segment
fill(37, 10, 38, 15, R)
fill(31, 14, 56, 15, R)        # main eastern path
fill(54, 8, 55, 15, R)         # up toward Sandgem
fill(54, 7, 63, 8, R)          # east exit (right edge) to Sandgem


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
chars = iter('ABCDEFGHIJKMNOPQSUVWXYZabcdefhijklmnopqrstuvwxyz0123456789')


def code(m, c, e, note):
    if (m, c, e) not in codes:
        ch = next(chars)
        codes[(m, c, e)] = ch
        legend[ch] = {'metatile': m, 'collision': c, 'elevation': e, 'note': note}
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
            line += code(135, 1, 3, 'ledge, jump south only')
        else:
            line += code(1, 0, 3, 'grass')
    rows.append(line)

plan = {
    'name': 'Route 201 - DESIGN CANDIDATE (not approved; original DPPt geography)',
    'primary': 'gTileset_General', 'secondary': 'gTileset_Dewford',
    'width': W, 'height': H, 'legend': legend, 'rows': rows, 'stamps': [],
    'marks': [
        {'kind': 'exit', 'at': [0, 8], 'size': [1, 4], 'note': 'west -> Lake Verity side (unapproved; closed)'},
        {'kind': 'exit', 'at': [16, 21], 'size': [2, 1], 'note': 'south -> Twinleaf Town (unapproved; closed)'},
        {'kind': 'exit', 'at': [63, 7], 'size': [1, 2], 'note': 'east -> Sandgem Town west exit'},
        {'kind': 'reserved', 'at': [42, 5], 'size': [10, 8], 'note': 'big grass patch: future first-encounter space (no table yet)'},
        {'kind': 'npc', 'at': [33, 13], 'note': 'trainer/NPC slot (no roster yet)'},
        {'kind': 'npc', 'at': [57, 9], 'note': 'NPC slot near the Sandgem end'},
    ],
}
Path(__file__).with_name('route201-candidate.json').write_text(json.dumps(plan, indent=1) + '\n')
print('\n'.join(rows))
