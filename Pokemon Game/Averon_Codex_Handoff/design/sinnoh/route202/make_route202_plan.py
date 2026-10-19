#!/usr/bin/env python3
"""Generate route202-candidate.json: a DESIGN CANDIDATE (not approved; no map file, no map or
section ID, no encounters, no NPCs, no story) for Route 202 on its original DPPt geography, and
its junction-D seam preview against the BUILT Sandgem Town layout.

Footprints were read from the original Diamond/Pearl overhead (Bulbapedia File:Sinnoh_Route_202_DP.png,
592 x 416 px; source, hash and method in ROUTE202_CANDIDATE.md), cross-checked against the Platinum
overhead (File:Sinnoh_Route_202_Pt.png). The render is top-down but foreshortened: 16 px per tile
across, 12.29 px per tile down. Reference column c starts at x = 16c - 8 px, reference row r at
y = 12.292r - 3.29 px. Here x = c - 2 and y = r (map 34 x 34 = reference columns 2-35, rows 0-33).
Ground features (sand, ledges, tall-grass edges) align to that grid; trees, signs and NPCs are
3D models drawn up to a row above their footprint, so their rows are +-1 tile. Lines marked
DEVIATION depart from the reference and say why.

Art: the approved temporary General + Dewford placeholders already used by Sandgem and Route 201
(grass 1, tall grass 13, round trees 468-485, Route 101 dirt road 464-482, ledge 135, sign 3).
Coordinates are metatiles (x right, y down).

  python3 -B make_route202_plan.py [--no-render]

writes route202-candidate.json and route202-sandgem-seam.json, then renders route202-candidate.png,
route202-collision.png and route202-sandgem-seam.png with scripts/sinnoh-placeholder-art.py.
"""
import json
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[3]                       # .../Pokemon Game
ENGINE = GAME / 'engine'
SANDGEM_MAPBIN = ENGINE / 'data' / 'layouts' / 'SandgemTown' / 'map.bin'
SANDGEM_W, SANDGEM_H = 32, 28

W, H = 34, 34
F, G, R, T, L = 'F', 'g', 'R', 'T', 'L'   # forest, grass, road (sand), tall grass, ledge (jump south)
grid = [[F] * W for _ in range(H)]


def fill(x0, y0, x1, y1, k):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            grid[y][x] = k


# Everything not filled below is forest: the tree border (reference columns 0-3 and 32-37, the top
# rows 0-5 and the bottom rows 30-33) and the tree clumps listed at the end.

# --- North section (reference rows 0-11) ---
fill(10, 2, 17, 6, G)          # north clearing below Jubilife (reference c 12-19, r 0-6)
fill(14, 0, 16, 1, G)          # DEVIATION: rows 0-1 open only on x 14-16, the 3 Jubilife stair columns
                               # (reference: grass c 12-19 up to Jubilife's wall). Junction E needs exactly
                               # 3 open tiles, and q = 14 makes the Jubilife offset even (-30); the stairs'
                               # column is itself +-1 (only the Platinum render shows them)
fill(13, 3, 15, 6, R)          # sand stub from the clearing (reference c 15-17, r 3-6)
fill(2, 6, 7, 9, T)            # north-west tall grass (reference c 4-9, r 6-9)
fill(8, 6, 12, 6, G)           # verge (reference c 10-14, r 6)
fill(8, 7, 8, 11, G)           # verge west of the sand (reference c 10, r 7-11)
fill(16, 6, 18, 6, G)          # verge by the route sign (reference c 18-20, r 6)
fill(19, 6, 23, 9, T)          # north-east tall grass (reference c 21-25, r 6-9)
fill(21, 10, 23, 10, T)        # (reference c 23-25, r 10)
fill(24, 6, 29, 6, G)          # flower verge (reference c 26-31, r 6; flowers are walkable decoration)
fill(9, 7, 18, 8, R)           # west sand path (reference c 11-20, r 7-8)
fill(24, 7, 29, 8, R)          # east sand path (reference c 26-31, r 7-8)
fill(9, 9, 11, 10, R)          # west path turns down (reference c 11-13, r 9-10)
fill(9, 11, 12, 11, G)         # verge above the west ledge (reference c 11-14, r 11)
fill(12, 9, 18, 9, G)          # strip under the sand (reference c 14-20, r 9; the clump's canopy overhangs it)
fill(12, 10, 12, 10, G)        # (reference c 14, r 10)
fill(24, 9, 26, 10, G)         # (reference c 26-28, r 9-10)
fill(21, 11, 26, 11, G)        # verge above the east ledge (reference c 23-28, r 11)
fill(27, 9, 29, 12, R)         # east path turns down (reference c 29-31, r 9-12): the only two-way link
                               # between the north section and the east field, as in DPPt

# --- Ledges (MB_JUMP_SOUTH; jump down only) ---
fill(8, 12, 12, 12, L)         # west ledge (reference c 10-14, r 12)
fill(21, 12, 26, 12, L)        # east ledge (reference c 23-28, r 12)
fill(8, 25, 12, 25, L)         # lower west ledge (reference c 10-14, r 25)
fill(21, 25, 29, 25, L)        # lower east ledge (reference c 23-31, r 25)

# --- Middle section (reference rows 13-24) ---
fill(30, 12, 31, 12, T)        # the east field reaches the border trees (reference c 32-33, r 12)
fill(21, 13, 31, 19, T)        # east tall-grass field (reference c 23-33, r 13-19)
fill(23, 20, 31, 21, T)        # (reference c 25-33, r 20-21)
fill(25, 22, 29, 22, T)        # (reference c 27-31, r 22)
fill(28, 23, 29, 23, T)        # (reference c 30-31, r 23)
fill(6, 13, 12, 14, G)         # below the west ledge (reference c 8-14, r 13-14)
fill(6, 12, 7, 12, G)          # opened by the west clump's one-row shift (reference c 8-9, r 12)
fill(2, 14, 5, 14, G)          # (reference c 4-7, r 14): the same shift; see the clump list below
fill(2, 15, 8, 20, G)          # west meadow with flowers and a light pad (reference c 4-10, r 15-20)
fill(8, 21, 8, 24, G)          # (reference c 10, r 21-24)
fill(12, 14, 16, 20, G)        # meadow by the trainer-tips sign (reference c 14-18, r 14-20)
fill(17, 20, 20, 20, G)        # below the central tree column (reference c 19-22, r 20)
fill(12, 23, 27, 23, G)        # (reference c 14-29, r 23; c 15-22 under the canopy of the row below)
fill(12, 24, 12, 24, G)        # (reference c 14, r 24)
fill(21, 24, 29, 24, G)        # verge above the lower east ledge (reference c 23-31, r 24)
fill(9, 15, 11, 24, R)         # west sand path down to the lower ledge (reference c 11-13, r 15-24)
fill(9, 21, 22, 21, R)         # cross path (reference c 11-24, r 21)
fill(9, 22, 24, 22, R)         # (reference c 11-26, r 22)
fill(21, 20, 22, 20, R)        # path meets the field (reference c 23-24, r 20)
fill(2, 21, 5, 29, T)          # south-west tall grass: the walking route north (reference c 4-7, r 21-29)

# --- South section (reference rows 26-33) ---
fill(6, 26, 7, 29, T)          # (reference c 8-9, r 26-29)
fill(8, 26, 29, 27, G)         # strip below the lower ledges (reference c 10-31, r 26-27)
fill(8, 28, 8, 29, G)          # (reference c 10, r 28-29)
fill(14, 27, 19, 29, T)        # south tall grass (reference c 16-21, r 27-29)
fill(9, 27, 11, 29, R)         # dead-end sand bay (reference c 11-13, r 27; c 11-15, r 28-29)
fill(12, 28, 13, 29, R)
fill(20, 28, 27, 29, R)        # south sand path (reference c 22-29, r 28-29)
fill(28, 28, 29, 29, G)        # (reference c 30-31, r 28-29; flowers)
fill(23, 30, 28, 33, G)        # DEVIATION: the south clearing is x 23-28 (reference c 26-31 = x 24-29),
                               # one column west, so it meets Sandgem's measured opening x 19-24 at an
                               # EVEN offset (-4) and the 2x2 trees stay whole across the seam
fill(25, 30, 27, 31, R)        # path down to Sandgem (reference c 27-29, r 30-32)
fill(25, 32, 26, 33, R)        # DEVIATION: the last two rows narrow to 2 wide (x 25-26) to continue
                               # Sandgem's built 2-wide road (x 21-22) road to road

# Tree clumps kept at their measured columns (forest by default, listed for review):
#   x 2-7 / y 10-11 and x 2-5 / y 12-13, west clump (reference c 4-9 r 11-12, c 4-7 r 13-14: placed one
#     row up, within the +-1 of a canopy-hidden footprint, so its trees sit whole on the 2x2 grid)
#   x 13-20 / y 10-13 and x 17-20 / y 14-19 (reference c 15-22 r 10-13, c 19-22 r 14-19), central clump
#   x 6-7 / y 20-25 (reference c 8-9 r 20-25), tree column between the west meadow and the sand path
#   x 13-20 / y 24-25 (reference c 15-22 r 24-25), trees between the two lower ledges
# Round trees are drawn on a fixed 2x2 grid (left halves on even x, top halves on even y). Rows are +-1,
# so clumps sit on even rows; columns are measured exactly, so a clump that starts on an odd column keeps
# it and shows a half tree at that edge, as Route 201's clumps and Sandgem's own north opening do. Only
# the seams are phase-checked (verify_route202_plan.py).

SIGNS = [(16, 5),              # route sign by the north clearing (reference c 18, r 5)
         (14, 17),             # trainer-tips sign on its light pad (reference c 16, r 17)
         (23, 25)]             # DEVIATION: south route sign in the ledge row (reference c 25, r 26, just
                               # below it). The engine never checks a ledge's landing tile, so a sign under
                               # the ledge would be a jump onto a solid tile; in the ledge row it is +-1 row
for sx, sy in SIGNS:
    grid[sy][sx] = 's'


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
        elif k == 's':
            line += code(3, 1, 0, 'sign')
        else:
            line += code(1, 0, 3, 'grass')
    rows.append(line)

plan = {
    'name': 'Route 202 - DESIGN CANDIDATE (not approved; original DPPt geography)',
    'primary': 'gTileset_General', 'secondary': 'gTileset_Dewford',
    'width': W, 'height': H, 'legend': legend, 'rows': rows, 'stamps': [],
    'exits': [
        {'name': 'south', 'edge': 'south', 'span': [23, 28], 'to': 'Sandgem Town north edge (x 19-24, road 21-22)',
         'offset': 4, 'status': 'Sandgem built (#133); Route 202 down +4 / Sandgem up -4, only after approval'},
        {'name': 'north', 'edge': 'north', 'span': [14, 16], 'to': 'Jubilife City south stairs (x 44-46; not built)',
         'offset': -30, 'status': 'unapproved; closed until Jubilife exists'},
    ],
    'marks': [
        {'kind': 'exit', 'at': [23, 33], 'size': [6, 1], 'note': 'south -> Sandgem Town north edge (offset +4; unapproved)'},
        {'kind': 'exit', 'at': [14, 0], 'size': [3, 1], 'note': 'north -> Jubilife City (offset -30 proposed; closed)'},
        {'kind': 'reserved', 'at': [21, 12], 'size': [11, 12], 'note': 'east tall-grass field (no encounter table yet)'},
        {'kind': 'reserved', 'at': [2, 21], 'size': [6, 9], 'note': 'south-west tall grass: the walking route north (no table yet)'},
        {'kind': 'reserved', 'at': [23, 31], 'size': [6, 2], 'note': 'DPPt catching-tutorial spot at the Sandgem end (story; not adopted)'},
        {'kind': 'npc', 'at': [9, 9], 'note': 'NPC slot (reference: trainer on the west path)'},
        {'kind': 'npc', 'at': [25, 6], 'note': 'NPC slot (reference: trainer at the flower verge)'},
        {'kind': 'npc', 'at': [6, 14], 'note': 'NPC slot (reference: trainer below the west ledge)'},
        {'kind': 'npc', 'at': [21, 19], 'note': 'NPC slot (reference: trainer at the field edge)'},
    ],
}


def seam_plan(route):
    """Junction D preview: Route 202's last 8 rows over Sandgem's first 10 rows (read from the built
    map.bin), cropped to the columns both maps cover at the proposed offset (Route 202 x = Sandgem x + 4)."""
    offset = next(e for e in route['exits'] if e['name'] == 'south')['offset']
    blocks = struct.unpack(f'<{SANDGEM_W * SANDGEM_H}H', SANDGEM_MAPBIN.read_bytes())
    x0, x1 = max(0, offset), min(W, SANDGEM_W + offset)          # Route 202 columns shared with Sandgem
    alphabet = iter(chr(c) for c in range(33, 127) if chr(c) not in '"\\')
    seam_legend, seam_codes, out = {}, {}, []

    def put(m, c, e, note):
        if (m, c, e) not in seam_codes:
            ch = next(alphabet)
            seam_codes[(m, c, e)] = ch
            seam_legend[ch] = {'metatile': m, 'collision': c, 'elevation': e, 'note': note}
        return seam_codes[(m, c, e)]

    for y in range(H - 8, H):
        out.append(''.join(put(route['legend'][ch]['metatile'], route['legend'][ch]['collision'],
                               route['legend'][ch]['elevation'], 'Route 202')
                           for ch in route['rows'][y][x0:x1]))
    for y in range(10):
        line = ''
        for x in range(x0, x1):
            b = blocks[y * SANDGEM_W + x - offset]
            line += put(b & 0x3FF, (b >> 10) & 3, b >> 12, 'Sandgem Town (built map.bin)')
        out.append(line)
    return {
        'name': f'Junction D preview (not a map): Route 202 rows {H - 8}-{H - 1}, x {x0}-{x1 - 1} over '
                f'Sandgem Town rows 0-9, x {x0 - offset}-{x1 - 1 - offset} (offset {offset:+d})',
        'primary': 'gTileset_General', 'secondary': 'gTileset_Dewford',
        'width': x1 - x0, 'height': len(out), 'legend': seam_legend, 'rows': out, 'stamps': [],
        'marks': [{'kind': 'exit', 'at': [23 - x0, 7], 'size': [6, 2], 'note': 'the seam: Route 202 y 33 / Sandgem y 0'}],
    }


def render(json_path, png, *flags):
    script = GAME / 'scripts' / 'sinnoh-placeholder-art.py'
    subprocess.run([sys.executable, '-B', str(script), '--engine', str(ENGINE), 'plan', str(json_path),
                    '--out', str(png), *flags], check=True)


def main():
    out = HERE / 'route202-candidate.json'
    out.write_text(json.dumps(plan, indent=1) + '\n')
    seam = HERE / 'route202-sandgem-seam.json'
    seam.write_text(json.dumps(seam_plan(plan), indent=1) + '\n')
    print('\n'.join(rows))
    if '--no-render' not in sys.argv:
        render(out, HERE / 'route202-candidate.png')
        render(out, HERE / 'route202-collision.png', '--collision', '--no-marks')
        render(seam, HERE / 'route202-sandgem-seam.png')
    return 0


if __name__ == '__main__':
    sys.exit(main())
