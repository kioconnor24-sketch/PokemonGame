#!/usr/bin/env python3
"""Generate twinleaf-candidate.json: a DESIGN CANDIDATE (not approved; no map file, no map or
section ID, no NPCs, no story) for Twinleaf Town on its original DPPt geography.

Footprints were read from the original Diamond/Pearl overhead (Bulbapedia File:Twinleaf_Town_DP.png,
510 x 475 px; method in TWINLEAF_TOWN_CANDIDATE.md). That render is top-down but foreshortened:
16 px per tile across, 12.33 px per tile down (trees repeat every 32 x 24.67 px). Tile (x, y) here
is the reference tile (x, y) with column 0 starting 9 px left of the image and row 0 at y = 5.5 px.
Lines marked DEVIATION depart from the reference and say why.

Art: the approved temporary in-repo General + Dewford placeholders already used by Sandgem and
Route 201 (round trees, dirt road, flowers, shrubs, Route 102's pond, Dewford house stamps).
Coordinates are metatiles (x right, y down).
"""
import json
from pathlib import Path

W, H = 32, 36
F, G, R, P, FL, HG, S = 'F', 'g', 'R', 'P', 'f', 'h', 's'   # forest, grass, road, pond, flowers, hedge, sign
grid = [[F] * W for _ in range(H)]


def fill(x0, y0, x1, y1, k):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            grid[y][x] = k


# --- Town interior (reference: light grass inside a tree border 7 tiles wide each side) ---
fill(6, 2, 25, 29, G)          # DEVIATION: reference interior is x 7-25; x 6 opens so the left border is
                               # whole 2x2 trees (x 0-5). Row 29 is grass full width (reference: grass at
                               # x 12-20 only) so the bottom tree band starts on an even row.
# --- North exit (reference: 3-wide sand path through the tree band, x 15-17) ---
fill(15, 0, 17, 1, R)          # meets Route 201's built south path x 15-17 at offset 0
# --- Roads (reference: sand) ---
fill(15, 5, 17, 28, R)         # main north-south path (reference: grass gap rows 2-4 below the stub)
fill(9, 16, 23, 17, R)         # cross path at the town sign
fill(9, 26, 23, 28, R)         # southern path in front of the lower houses
# --- Fenced gardens (reference: fenced flower beds in both top corners, x 7-11 / 21-25, rows 2-5) ---
for x0 in (7, 21):
    fill(x0, 2, x0 + 4, 5, HG)         # fence stand-in: shrubs (no fence art in General + Dewford)
    fill(x0 + 1, 3, x0 + 3, 4, FL)     # flowers inside
# --- Pond (reference: pond south of the town, x 13-19, rows 30-33, framed by trees) ---
fill(12, 30, 19, 33, P)        # DEVIATION: x 12-19 (reference 13-19) so the trees either side stay whole


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


def pond(x, y):
    """Route 102's pond pieces: 176-178 top edge, 184/186 sides, 161 open water."""
    n, w, e = is_(P, x, y - 1), is_(P, x - 1, y), is_(P, x + 1, y)
    if not n:
        return 176 if not w else 178 if not e else 177
    return 184 if not w else 186 if not e else 161


legend, codes = {}, {}
chars = iter('ABCDEFGHIJKMNOPQSUVWXYZabcdefhijklmnopqrtuvwxyz0123456789')


def code(m, c, e, note):
    if (m, c, e) not in codes:
        ch = next(chars)
        codes[(m, c, e)] = ch
        legend[ch] = {'metatile': m, 'collision': c, 'elevation': e, 'note': note}
    return codes[(m, c, e)]


SIGN = (18, 15)                # reference: the town sign at the crossing, north-east of the path
rows = []
for y in range(H):
    line = ''
    for x in range(W):
        k = grid[y][x]
        if (x, y) == SIGN:
            line += code(3, 1, 0, 'sign')
        elif k == R:
            line += code(road(x, y), 0, 3, 'dirt road')
        elif k == F:
            line += code(tree(x, y), 1, 0, 'tree (solid)')
        elif k == P:
            line += code(pond(x, y), 0, 1, 'pond water (Surf only; closed while Surf is unavailable)')
        elif k == FL:
            line += code(4, 1, 3, 'flowers inside the fence (solid: not enterable, as in DPPt)')
        elif k == HG:
            line += code(22, 1, 3, 'shrub (fence stand-in, solid)')
        else:
            line += code(1, 0, 3, 'grass')
    rows.append(line)

plan = {
    'name': 'Twinleaf Town - DESIGN CANDIDATE (not approved; original DPPt geography)',
    'primary': 'gTileset_General', 'secondary': 'gTileset_Dewford',
    'width': W, 'height': H, 'legend': legend, 'rows': rows,
    'stamps': [
        # Reference doors (door-colour components): (10, 13), (21, 13), (11, 23), (21, 23). The two-storey
        # houses use the 5-wide Dewford block (door +2,+3); the small ones the 4-wide house (door +1,+3).
        {'note': 'north-west house, two-storey in DPPt (UNASSIGNED residence; no interior, no warp)',
         'from': 'LAYOUT_DEWFORD_TOWN', 'src': [1, 0, 5, 4], 'at': [8, 10]},
        {'note': 'north-east house (UNASSIGNED; no interior, no warp)',
         'from': 'LAYOUT_DEWFORD_TOWN', 'src': [16, 11, 4, 4], 'at': [20, 10]},
        {'note': 'south-west house (UNASSIGNED; no interior, no warp)',
         'from': 'LAYOUT_DEWFORD_TOWN', 'src': [16, 11, 4, 4], 'at': [10, 20]},
        {'note': 'south-east house, two-storey in DPPt (UNASSIGNED residence; no interior, no warp)',
         'from': 'LAYOUT_DEWFORD_TOWN', 'src': [1, 0, 5, 4], 'at': [19, 20]},
    ],
    'exits': [
        {'name': 'north', 'edge': 'north', 'span': [15, 17], 'to': 'Route 201 south edge (x 15-17)',
         'offset': 0, 'status': 'Route 201 built (#150); connection only after Twinleaf is approved'},
    ],
    'doors': [[10, 13], [21, 13], [11, 23], [21, 23]],
    'marks': [
        {'kind': 'exit', 'at': [15, 0], 'size': [3, 1], 'note': 'north -> Route 201 (offset 0; unapproved, closed)'},
        {'kind': 'warp', 'at': [10, 13], 'note': 'north-west house door (no interior)'},
        {'kind': 'warp', 'at': [21, 13], 'note': 'north-east house door (no interior)'},
        {'kind': 'warp', 'at': [11, 23], 'note': 'south-west house door (no interior)'},
        {'kind': 'warp', 'at': [21, 23], 'note': 'south-east house door (no interior)'},
        {'kind': 'reserved', 'at': [12, 30], 'size': [8, 4], 'note': 'pond: Surf-only space (Odd Keystone spot in DPPt; unapproved)'},
    ],
}
Path(__file__).with_name('twinleaf-candidate.json').write_text(json.dumps(plan, indent=1) + '\n')
print('\n'.join(rows))
