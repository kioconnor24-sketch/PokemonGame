#!/usr/bin/env python3
"""Generate the Verity DESIGN CANDIDATES (not approved; no map file, no map or section ID, no
encounters, no NPCs, no story): Verity Lakefront and Lake Verity on their original DPPt geography,
as two maps joined by a seam, plus the two seam previews.

Footprints were read from the original Diamond/Pearl overheads on Bulbapedia (File:Verity_Lakefront_DP.png
357 x 303 px and File:Lake_Verity_DP.png 864 x 648 px; sources, hashes and method in VERITY_CANDIDATE.md),
cross-checked against the Platinum overheads. The renders are foreshortened: 16 px per tile across,
12.29-12.38 px down. Ground features (paths, ledges, grass edges, shorelines) align to that grid;
trees and signs are 3D models drawn up to a row above their footprint, so their rows are +-1 tile.
Lines marked DEVIATION depart from the reference and say why.

  Verity Lakefront: x = c - 1, y = r - 3 (reference c 1-22, r 3-20; column c at 16c - 8 px,
                    row r at 12.375r - 2.38 px). 22 x 18.
  Lake Verity:      x = c - 2, y = r - 3 (reference c 2-51, r 3-46; column c at 16c px,
                    row r at 12.292r - 9.79 px). 50 x 44.

Art: the approved temporary General + Dewford placeholders used by Sandgem, Route 201 and Twinleaf
(grass 1, shore grass 2, tall grass 13, round trees 468-485, dirt road 464-482, ledges 133/135/141,
sign 3, Route 102's pond pieces 161-204 at elevation 1 = Surf only).

  python3 -B make_verity_plans.py [--no-render]
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[3]                       # .../Pokemon Game
ENGINE = GAME / 'engine'
ROUTE201 = HERE.parent / 'route201' / 'route201-candidate.json'

F, G, R, T, WA, LS, LW, LC, S = 'F', 'g', 'R', 'T', 'W', 'L', 'w', 'c', 's'
# forest, grass, road (sand), tall grass, water, ledge south, ledge west, ledge corner, sign


class Plan:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.grid = [[F] * w for _ in range(h)]

    def fill(self, x0, y0, x1, y1, k):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.grid[y][x] = k

    def is_(self, k, x, y):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return k == R
        return self.grid[y][x] == k


# ----------------------------------------------------------------- Verity Lakefront (22 x 18) ---
vl = Plan(22, 18)
vl.fill(6, 0, 7, 5, G)         # gap north to Lake Verity (reference c 7-8, r 3-8; DPPt shades r 4-6 as
                               # the transition into the lake map)
vl.fill(4, 6, 15, 6, G)        # top strip, open past the plateau's ledge cap (reference c 5-16, r 9)
vl.fill(6, 6, 7, 6, R)         # sand patch below the gap (reference c 7-8, r 9)
vl.fill(4, 7, 9, 11, G)        # lower west ground: sign, gap and the way to the lake (reference c 5-10, r 10-13;
                               # its tree steps at c 5-6 / c 7-8 sit one row lower, on the 2x2 grid, within +-1)
vl.fill(6, 12, 9, 13, G)       # (reference c 7-10, r 14-15)
vl.fill(8, 13, 21, 14, G)      # lower strip, continues Route 201's strip below its long ledge
                               # (reference c 9-22, r 16-17)
vl.fill(11, 7, 21, 11, G)      # raised flower plateau, continues Route 201's upper corridor
                               # (reference c 12-22, r 10-14)
vl.fill(16, 6, 19, 7, F)       # two trees on the plateau (reference c 17-20, r 10-11; placed one row up on the
                               # 2x2 grid, within their +-1, so they close the plateau's top like Route 201's
                               # corridor)
vl.fill(20, 6, 21, 7, F)       # DEVIATION: the tree line reaches the east edge, rows 6-7 (reference: open
                               # plateau, c 21-22 r 9-10). Route 201's built west opening above its ledge is 4 rows
                               # (8-11); the Bulbapedia renders show that corridor ~6 rows tall but Route 201's
                               # own source shows 4, and the seam follows the built route
vl.fill(10, 7, 10, 11, LW)     # west-facing ledge, the plateau's west side (reference c 11, r 10-14)
vl.fill(10, 12, 10, 12, LC)    # plateau corner (reference c 11, r 15)
vl.fill(11, 12, 21, 12, LS)    # south-facing ledge (reference c 12-16 and 19-22, r 15): meets Route 201's long
                               # ledge (row 12) at the seam
vl.fill(16, 10, 17, 11, F)     # tree at the ledge (reference c 17-18, r 14-15, standing in the ledge line;
                               # placed one row up, within +-1, so it is whole and the ledge runs under it)
vl.grid[5][5] = S              # lakefront sign beside the gap (reference c 6, r 8)

# -------------------------------------------------------------------- Lake Verity (50 x 44) -----
lv = Plan(50, 44)
# Lake (Surf only): the octagon of stepped cliffs, reference shoreline columns per row band
for (y0, y1, x0, x1) in ((4, 5, 14, 33),       # r 7-8:   c 16-35 (the north shore strip at r 6 is folded
                         (6, 7, 12, 35),       # r 9-10:  c 14-37  into the tree line: DEVIATION, it is
                         (8, 9, 10, 37),       # r 11-12: c 12-39  reachable only by Surf in DPPt)
                         (10, 11, 8, 39),      # r 13-14: c 10-41
                         (12, 29, 6, 41),      # r 15-32: c 8-43
                         (30, 31, 8, 39),      # r 33-34: c 10-41 (west step measured at r 32: DEVIATION,
                         (32, 33, 10, 37),     # r 35-36: c 12-39  moved one row so it falls on an even row)
                         (34, 35, 12, 35),     # r 37-38: c 14-37
                         (36, 37, 14, 33)):    # r 39(-40): c 16-35 (DEVIATION: two rows, so the forest below
    lv.fill(x0, y0, x1, y1, WA)                # starts on an even row; r 40 is hidden under the canopy)
lv.fill(20, 16, 27, 23, F)     # central island, story-reserved: neutral closed space, no cave warp
                               # (reference c 23-29 + cliff, r 19-26; DEVIATION: 8 wide (c 22-29) so the
                               # placeholder trees are whole)
# South-east clearing: the only land reachable on foot (reference c 38-49, r 27-46)
lv.fill(42, 24, 45, 25, G)     # (reference c 44-47, r 27-28; trees c 48-49)
lv.fill(42, 26, 47, 29, G)     # (reference c 44-49, r 29-32)
lv.fill(42, 28, 43, 29, T)     # tall grass (reference c 44-45, r 31-32)
lv.fill(40, 30, 45, 31, G)     # (reference c 42-47, r 33-34)
lv.fill(40, 30, 43, 30, T)     # (reference c 42-45, r 33)
lv.fill(41, 31, 43, 31, T)     # (reference c 43-45, r 34)
lv.fill(38, 32, 43, 33, G)     # (reference c 40-45, r 35-36)
lv.fill(39, 32, 43, 32, T)     # (reference c 41-45, r 35)
lv.fill(39, 33, 42, 33, T)     # (reference c 41-44, r 36)
lv.fill(36, 34, 43, 35, G)     # (reference c 38-45, r 37-38)
lv.fill(39, 34, 41, 34, T)     # (reference c 41-43, r 37)
lv.fill(36, 36, 41, 39, G)     # (reference c 38-43, r 39-42)
lv.fill(38, 39, 39, 40, R)     # sand patch (reference c 40-41, r 42-43)
lv.fill(38, 41, 39, 43, G)     # gap south to Verity Lakefront (reference c 40-41, r 44-46; the trees either side
                               # start at r 43, one row above their canopy-hidden footprint, on the 2x2 grid)
# South-west shore: tall grass reachable only by Surf, as in DPPt (reference c 4-19, r 35-44)
lv.fill(4, 32, 6, 33, T)       # (reference c 6-8, r 35-36)
lv.fill(7, 32, 7, 33, G)       # (reference c 9, r 35-36)
lv.fill(2, 34, 7, 34, T)       # (reference c 4-9, r 37)
lv.fill(8, 34, 11, 34, G)      # (reference c 10-13, r 37): the Surf landing
lv.fill(2, 35, 10, 37, T)      # (reference c 4-12, r 38-40)
lv.fill(11, 35, 11, 37, G)     # (reference c 13, r 38-40)
lv.fill(2, 38, 11, 38, T)      # (reference c 4-13, r 41)
lv.fill(12, 38, 13, 38, G)     # (reference c 14-15, r 41)
lv.fill(2, 39, 12, 39, T)      # (reference c 4-14, r 42)
lv.fill(13, 39, 13, 39, G)     # (reference c 15, r 42)
lv.fill(2, 40, 17, 41, T)      # (reference c 4-19, r 43-44)
SURF_ONLY = (2, 32, 17, 41)    # bounding box of the south-west shore, for the verifier


def road(p, x, y):
    PATH = {'C': 473, 'T': 465, 'B': 481, 'L': 472, 'R': 474, 'TL': 464, 'TR': 466, 'BL': 480, 'BR': 482}
    n, s, w, e = p.is_(R, x, y - 1), p.is_(R, x, y + 1), p.is_(R, x - 1, y), p.is_(R, x + 1, y)
    key = ('T' if not n else 'B' if not s else '') + ('L' if not w else 'R' if not e else '')
    return PATH[key or 'C']


def tree(p, x, y):
    top = not p.is_(F, x, y - 1) and y > 0
    bottom = not p.is_(F, x, y + 1) and y < p.h - 1
    if y % 2 == 0:
        return (470, 471)[x % 2] if top else (468, 469)[x % 2]
    return (484, 485)[x % 2] if bottom else (476, 477)[x % 2]


def water(p, x, y):
    """General's pond pieces, as Emerald's own ponds use them: 176/177/178 top edge, 184/186 sides,
    192/194 inner corners (land at NW/NE), 204/203 sides where the shore steps inward, 161 open water."""
    wet = lambda dx, dy: p.is_(WA, x + dx, y + dy) if 0 <= x + dx < p.w and 0 <= y + dy < p.h else True
    n, w, e, nw, ne = wet(0, -1), wet(-1, 0), wet(1, 0), wet(-1, -1), wet(1, -1)
    if not n:
        return 176 if not w else 178 if not e else 177
    if not w:
        return 204 if nw else 184
    if not e:
        return 203 if ne else 186
    return 192 if not nw else 194 if not ne else 161


def encode(p):
    legend, codes = {}, {}
    chars = iter('ABCDEFGHIJKMNOPQSUVWXYZabcdefhijklmnopqrtuvwxyz0123456789')

    def code(m, c, e, note, **extra):
        if (m, c, e) not in codes:
            ch = next(chars)
            codes[(m, c, e)] = ch
            legend[ch] = {'metatile': m, 'collision': c, 'elevation': e, 'note': note, **extra}
        return codes[(m, c, e)]

    rows = []
    for y in range(p.h):
        line = ''
        for x in range(p.w):
            k = p.grid[y][x]
            if k == R:
                line += code(road(p, x, y), 0, 3, 'dirt road')
            elif k == F:
                line += code(tree(p, x, y), 1, 0, 'tree (solid)')
            elif k == T:
                line += code(13, 0, 3, 'tall grass (no encounter table yet)')
            elif k == WA:
                line += code(water(p, x, y), 0, 1, 'lake water (Surf only; elevation 1)', surf=True)
            elif k == LS:
                line += code(135, 1, 3, 'ledge, jump south only', jump='south')
            elif k == LW:
                line += code(133, 1, 3, 'ledge, jump west only', jump='west')
            elif k == LC:
                line += code(141, 1, 3, 'ledge corner (solid; not a jump in this engine)')
            elif k == S:
                line += code(3, 1, 0, 'sign')
            elif p.is_(WA, x, y - 1):
                line += code(2, 0, 3, 'grass with the shoreline above')
            else:
                line += code(1, 0, 3, 'grass')
        rows.append(line)
    return legend, rows


def plan_json(name, p, exits, marks, **extra):
    legend, rows = encode(p)
    return {'name': name, 'primary': 'gTileset_General', 'secondary': 'gTileset_Dewford',
            'width': p.w, 'height': p.h, 'legend': legend, 'rows': rows, 'stamps': [],
            'exits': exits, 'marks': marks, **extra}


LAKEFRONT = plan_json(
    'Verity Lakefront - DESIGN CANDIDATE (not approved; original DPPt geography)', vl,
    exits=[
        {'name': 'east-upper', 'edge': 'east', 'span': [8, 11], 'to': 'Route 201 west edge, upper (rows 8-11)',
         'offset': 0, 'status': 'Route 201 built (#150); Lakefront right 0 / Route 201 left 0, only after approval'},
        {'name': 'east-lower', 'edge': 'east', 'span': [13, 14], 'to': 'Route 201 west edge, below the ledge (rows 13-14)',
         'offset': 0, 'status': 'same connection as east-upper'},
        {'name': 'north', 'edge': 'north', 'span': [6, 7], 'to': 'Lake Verity south gap (x 38-39)',
         'offset': -32, 'status': 'unapproved; both maps new'},
    ],
    marks=[
        {'kind': 'exit', 'at': [21, 8], 'size': [1, 4], 'note': 'east (upper) -> Route 201 rows 8-11 (offset 0)'},
        {'kind': 'exit', 'at': [21, 13], 'size': [1, 2], 'note': 'east (lower) -> Route 201 rows 13-14 (offset 0)'},
        {'kind': 'exit', 'at': [6, 0], 'size': [2, 1], 'note': 'north -> Lake Verity (offset -32)'},
        {'kind': 'reserved', 'at': [6, 1], 'size': [2, 5], 'note': 'lake entrance: DPPt story scenes here (not adopted)'},
    ])

LAKE = plan_json(
    'Lake Verity - DESIGN CANDIDATE (not approved; original DPPt geography)', lv,
    exits=[
        {'name': 'south', 'edge': 'south', 'span': [38, 39], 'to': 'Verity Lakefront north gap (x 6-7)',
         'offset': 32, 'status': 'unapproved; both maps new'},
    ],
    marks=[
        {'kind': 'exit', 'at': [38, 43], 'size': [2, 1], 'note': 'south -> Verity Lakefront (offset +32)'},
        {'kind': 'reserved', 'at': [20, 16], 'size': [8, 8],
         'note': 'central island and cavern: story-reserved, closed (no warp, no event)'},
        {'kind': 'reserved', 'at': list(SURF_ONLY[:2]), 'size': [SURF_ONLY[2] - SURF_ONLY[0] + 1, SURF_ONLY[3] - SURF_ONLY[1] + 1],
         'note': 'south-west shore: tall grass reachable only by Surf (no encounter table yet)'},
        {'kind': 'reserved', 'at': [39, 28], 'size': [5, 7], 'note': 'south-east tall grass (no encounter table yet)'},
    ],
    surf_only=list(SURF_ONLY), island=[20, 16, 27, 23])


def seam_plan(title, parts, marks):
    """Composite preview (not a map): parts = [(plan, x0, y0, x1, y1, at_x, at_y)], pasted into one grid."""
    w = max(ax + x1 - x0 + 1 for _, x0, _, x1, _, ax, _ in parts)
    h = max(ay + y1 - y0 + 1 for _, _, y0, _, y1, _, ay in parts)
    alphabet = iter(chr(c) for c in range(33, 127) if chr(c) not in '"\\')
    legend, codes = {}, {}
    grid = [[None] * w for _ in range(h)]
    for p, x0, y0, x1, y1, ax, ay in parts:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                v = p['legend'][p['rows'][y][x]]
                key = (v['metatile'], v['collision'], v['elevation'])
                if key not in codes:
                    codes[key] = next(alphabet)
                    legend[codes[key]] = {'metatile': key[0], 'collision': key[1], 'elevation': key[2],
                                          'note': v['note']}
                grid[ay + y - y0][ax + x - x0] = codes[key]
    assert all(c is not None for row in grid for c in row), 'seam preview has gaps'
    return {'name': title, 'primary': 'gTileset_General', 'secondary': 'gTileset_Dewford',
            'width': w, 'height': h, 'legend': legend, 'rows': [''.join(r) for r in grid], 'stamps': [],
            'marks': marks}


def render(json_path, png, *flags):
    script = GAME / 'scripts' / 'sinnoh-placeholder-art.py'
    subprocess.run([sys.executable, '-B', str(script), '--engine', str(ENGINE), 'plan', str(json_path),
                    '--out', str(png), *flags], check=True)


def main():
    r201 = json.loads(ROUTE201.read_text())
    outputs = {
        'verity-lakefront-candidate': LAKEFRONT,
        'lake-verity-candidate': LAKE,
        # Junction C: Lakefront x 12-21 beside Route 201 x 0-9, rows 4-17 (offset 0: same rows).
        'route201-lakefront-seam': seam_plan(
            'Junction C preview (not a map): Verity Lakefront x 12-21 | Route 201 x 0-9, rows 4-17, offset 0',
            [(LAKEFRONT, 12, 4, 21, 17, 0, 0), (r201, 0, 4, 9, 17, 10, 0)],
            [{'kind': 'exit', 'at': [9, 4], 'size': [2, 4], 'note': 'seam, upper: rows 8-11'},
             {'kind': 'exit', 'at': [9, 9], 'size': [2, 2], 'note': 'seam, lower: rows 13-14'}]),
        # Lakefront <-> Lake: Lake x 30-49, rows 34-43 over Lakefront x -2..17 -> use Lakefront x 0-17.
        'lakefront-lake-seam': seam_plan(
            'North seam preview (not a map): Lake Verity rows 34-43, x 32-49 over Verity Lakefront rows 0-9, '
            'x 0-17 (Lake x = Lakefront x + 32)',
            [(LAKE, 32, 34, 49, 43, 0, 0), (LAKEFRONT, 0, 0, 17, 9, 0, 10)],
            [{'kind': 'exit', 'at': [6, 9], 'size': [2, 2], 'note': 'seam: Lake y 43 / Lakefront y 0'}]),
    }
    for name, plan in outputs.items():
        (HERE / f'{name}.json').write_text(json.dumps(plan, indent=1) + '\n')
    print('\n'.join(LAKEFRONT['rows']), '\n')
    print('\n'.join(LAKE['rows']))
    if '--no-render' not in sys.argv:
        for name in outputs:
            render(HERE / f'{name}.json', HERE / f'{name}.png')
        for name in ('verity-lakefront', 'lake-verity'):
            render(HERE / f'{name}-candidate.json', HERE / f'{name}-collision.png', '--collision', '--no-marks')
    return 0


if __name__ == '__main__':
    sys.exit(main())
