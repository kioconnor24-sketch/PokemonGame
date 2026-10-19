#!/usr/bin/env python3
"""Collision, access and junction proof for the Route 202 design candidate (plan JSON only; no ROM,
no map files are written).

Movement model (the engine's, as in verify_route201_plan.py): a tile with collision 0 is walkable; a
ledge (legend "jump": "south", MB_JUMP_SOUTH) is solid except when entered moving south, which jumps
the player to the tile beyond it. PlayerJumpLedge never checks the landing tile, so every ledge must
land on walkable ground. Exits are walkable edge tiles inside a declared exit span.

Checks:
  0. shape, legend, and (width + 15) x (height + 14) <= MAX_MAP_DATA_SIZE (10,240);
  1. every walkable tile is reachable from the Sandgem (south) exit;
  2. from every walkable tile the Sandgem exit is reachable again (no ledge pocket);
  3. south -> north and north -> south both connect (the DPPt zigzag, respecting the one-way ledges);
  4. the only walkable edge tiles are the declared exits: south (Sandgem) and north (Jubilife);
  5. every ledge lands on walkable ground;
  6. junction D: at the declared offset each open Route 202 bottom-edge column faces an open Sandgem
     row-0 column and vice versa (Sandgem's edge is read from its BUILT map.bin);
  7. junction D tree phase: wherever both seam tiles are round trees they are the same half (left /
     right), and Route 202's bottom row is a bottom half facing Sandgem's top-half row 0;
  8. junction E: the north opening is exactly 3 columns and its proposed Jubilife offset
     (q - 44, Jubilife stairs at x 44-46) is even.

usage: verify_route202_plan.py [PLAN_JSON] [--sandgem-mapbin MAP.BIN] [--self-test]
--self-test also proves each check fails on a deliberately broken copy of the plan.
"""
import argparse
import json
import struct
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAPBIN = HERE.parents[3] / 'engine' / 'data' / 'layouts' / 'SandgemTown' / 'map.bin'
MAX_MAP_DATA_SIZE = 10240

# Sandgem Town's north edge (y = 0) as built in #133 (layout 32 x 28, commit 38100116), measured from
# map.bin: columns 19-24 open (grass 19-20 and 23-24, road 21-22), everything else trees.
SANDGEM_W, SANDGEM_H = 32, 28
SANDGEM_NORTH_OPEN = {19, 20, 21, 22, 23, 24}
SANDGEM_NORTH_TILES = [468, 469, 468, 469, 468, 469, 468, 469, 468, 469, 468, 469, 468, 469, 468, 469,
                       468, 469, 468, 1, 1, 472, 474, 1, 1, 469, 468, 469, 468, 469, 468, 469]
JUBILIFE_STAIRS = 44                     # left column of Jubilife's 3-wide south stairs (SINNOH_JUNCTIONS.md)
TREE_LEFT, TREE_RIGHT = {468, 470, 476, 484}, {469, 471, 477, 485}
TREE_TOP, TREE_BOTTOM = {468, 469, 470, 471}, {476, 477, 484, 485}

STEPS = {'N': (0, -1), 'S': (0, 1), 'W': (-1, 0), 'E': (1, 0)}


def read_sandgem(path):
    blocks = struct.unpack(f'<{SANDGEM_W * SANDGEM_H}H', Path(path).read_bytes())
    row = blocks[:SANDGEM_W]
    return {x for x in range(SANDGEM_W) if (row[x] >> 10) & 3 == 0}, [b & 0x3FF for b in row]


def load(plan):
    legend = plan['legend']
    walk = [[legend[c]['collision'] == 0 for c in row] for row in plan['rows']]
    ledge = [[legend[c].get('jump') for c in row] for row in plan['rows']]
    return plan['width'], plan['height'], walk, ledge


def exit_tiles(plan, w, h):
    tiles = {}
    for ex in plan['exits']:
        a, b = ex['span']
        for i in range(a, b + 1):
            x, y = {'east': (w - 1, i), 'west': (0, i), 'south': (i, h - 1), 'north': (i, 0)}[ex['edge']]
            tiles[(x, y)] = ex['name']
    return tiles


def moves(w, h, walk, ledge, x, y):
    for d, (dx, dy) in STEPS.items():
        nx, ny = x + dx, y + dy
        if not (0 <= nx < w and 0 <= ny < h):
            continue
        if walk[ny][nx]:
            yield nx, ny
        elif ledge[ny][nx] == 'south' and d == 'S':
            if ny + 1 < h and walk[ny + 1][nx]:
                yield nx, ny + 1


def reach(w, h, walk, ledge, starts, reverse=False):
    if reverse:
        back = {}
        for y in range(h):
            for x in range(w):
                if walk[y][x]:
                    for t in moves(w, h, walk, ledge, x, y):
                        back.setdefault(t, []).append((x, y))
        step = lambda x, y: back.get((x, y), [])
    else:
        step = lambda x, y: moves(w, h, walk, ledge, x, y)
    seen, queue = set(starts), deque(starts)
    while queue:
        for t in step(*queue.popleft()):
            if t not in seen:
                seen.add(t)
                queue.append(t)
    return seen


def verify(plan, sandgem_open=SANDGEM_NORTH_OPEN, sandgem_tiles=SANDGEM_NORTH_TILES):
    results = []

    def check(name, ok, detail=''):
        results.append((name, bool(ok), detail))

    w, h = plan['width'], plan['height']
    shape_ok = len(plan['rows']) == h and all(len(r) == w for r in plan['rows']) \
        and all(c in plan['legend'] for r in plan['rows'] for c in r)
    check('0 shape, legend and map-size limit', shape_ok and (w + 15) * (h + 14) <= MAX_MAP_DATA_SIZE,
          (w, h, (w + 15) * (h + 14)))
    if not shape_ok:
        return results
    w, h, walk, ledge = load(plan)
    exits = exit_tiles(plan, w, h)
    walkable = {(x, y) for y in range(h) for x in range(w) if walk[y][x]}
    bad_exit = sorted(t for t in exits if t not in walkable)
    check('declared exit tiles are walkable', not bad_exit, bad_exit[:8])
    south = [t for t, n in exits.items() if n == 'south' and t in walkable]
    north = [t for t, n in exits.items() if n == 'north' and t in walkable]
    fwd = reach(w, h, walk, ledge, south)
    check('1 every walkable tile reachable from the Sandgem exit', not walkable - fwd, sorted(walkable - fwd)[:8])
    back = reach(w, h, walk, ledge, south, reverse=True)
    check('2 Sandgem exit reachable again from every walkable tile (no ledge pocket)', not walkable - back,
          sorted(walkable - back)[:8])
    n_ok = bool(north) and any(t in fwd for t in north)
    s_ok = bool(north) and any(t in reach(w, h, walk, ledge, north) for t in south)
    check('3 south -> north and north -> south both connect', n_ok and s_ok, (n_ok, s_ok))
    edge = {(x, y) for (x, y) in walkable if x in (0, w - 1) or y in (0, h - 1)}
    stray = sorted(edge - set(exits))
    check('4 only the declared south and north edges are open', not stray and {e['edge'] for e in plan['exits']}
          == {'south', 'north'}, stray[:8])
    bad_ledge = sorted((x, y) for y in range(h) for x in range(w)
                       if ledge[y][x] == 'south' and not (y + 1 < h and walk[y + 1][x]))
    check('5 every ledge lands on walkable ground', not bad_ledge, bad_ledge[:8])
    ex = next(e for e in plan['exits'] if e['name'] == 'south')
    offset = ex['offset']              # Sandgem x = Route 202 x - offset (Route 202 'down' entry)
    mismatch = [(x, x - offset) for x in range(w) if 0 <= x - offset < SANDGEM_W
                and walk[h - 1][x] != ((x - offset) in sandgem_open)]
    mismatch += [('sandgem column off route', sx) for sx in sandgem_open if not 0 <= sx + offset < w]
    check(f'6 south seam matches Sandgem north edge at offset {offset:+d} (Sandgem side {-offset:+d})',
          not mismatch, mismatch[:6])
    meta = lambda x, y: plan['legend'][plan['rows'][y][x]]['metatile']
    side = lambda m: 'L' if m in TREE_LEFT else 'R' if m in TREE_RIGHT else None
    split = [(x, side(meta(x, h - 1)), x - offset, side(sandgem_tiles[x - offset])) for x in range(w)
             if 0 <= x - offset < SANDGEM_W and side(meta(x, h - 1)) and side(sandgem_tiles[x - offset])
             and side(meta(x, h - 1)) != side(sandgem_tiles[x - offset])]
    vertical = [x for x in range(w) if meta(x, h - 1) in TREE_TOP] + \
        [x for x in range(SANDGEM_W) if sandgem_tiles[x] in TREE_BOTTOM]
    check('7 south seam keeps the round trees whole (same half across, bottom row meets top row)',
          not split and not vertical, (split[:4], vertical[:4]))
    nex = next((e for e in plan['exits'] if e['name'] == 'north'), None)
    north_cols = [x for x in range(w) if walk[0][x]]          # measured on the plan, not the declared span
    q_ok = nex is not None and len(north_cols) == 3 and nex['offset'] == north_cols[0] - JUBILIFE_STAIRS \
        and nex['offset'] % 2 == 0
    check('8 north opening is 3 wide with an even Jubilife offset (q - 44)', q_ok,
          (north_cols, nex and nex['offset']))
    return results


def mutated(plan, kind, cells, **change):
    """Copy of the plan with cells repainted as a solid tree, grass or a tree half, or a new offset."""
    legend = dict(plan['legend'])
    pick = {'tree': ('t', {'metatile': 468, 'collision': 1, 'elevation': 0}),
            'grass': ('g', {'metatile': 1, 'collision': 0, 'elevation': 3}),
            'treetop': ('u', {'metatile': 469, 'collision': 1, 'elevation': 0})}[kind]
    legend[pick[0]] = pick[1]
    rows = [list(r) for r in plan['rows']]
    for x0, y0, x1, y1 in cells:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rows[y][x] = pick[0]
    out = dict(plan, legend=legend, rows=[''.join(r) for r in rows])
    if change:
        out['exits'] = [dict(e, offset=change[e['name']]) if e['name'] in change else e for e in plan['exits']]
    return out


NEGATIVE = [  # (label, mutation, check that must FAIL)
    ('trees over the east path turn: the north section is cut off from the field', ('tree', [(27, 12, 31, 12)]), '1 '),
    ('trees across the south-west tall grass: no walking route north from Sandgem', ('tree', [(2, 20, 5, 20)]), '3 '),
    ('trees under the strip below the west ledge: jumping it leaves no way back', ('tree', [(6, 14, 12, 14)]), '2 '),
    ('the west ledge lands on a tree', ('tree', [(8, 13, 8, 13)]), '5 '),
    ('a gap in the west tree border opens an undeclared edge', ('grass', [(0, 16, 1, 16)]), '4 '),
    ('odd offset +5 misaligns the Sandgem seam and splits the trees', ('tree', [], {'south': 5}), '6 '),
    ('a top-half tree on the bottom row facing Sandgem', ('treetop', [(31, 33, 31, 33)]), '7 '),
    ('north opening widened to 4 columns', ('grass', [(13, 0, 13, 1)]), '8 '),
]


def self_test(plan, open_cols, tiles):
    bad = 0
    for label, (kind, cells, *extra), must_fail in NEGATIVE:
        res = verify(mutated(plan, kind, cells, **(extra[0] if extra else {})), open_cols, tiles)
        failed = [n for n, ok, _ in res if not ok]
        ok = any(n.startswith(must_fail) for n in failed)
        bad += not ok
        print(('PASS ' if ok else 'FAIL ') + f'negative: {label} -> caught by {[n.split()[0] for n in failed]}')
    return bad


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plan', nargs='?', type=Path, default=HERE / 'route202-candidate.json')
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--sandgem-mapbin', type=Path, default=MAPBIN if MAPBIN.exists() else None,
                        help="read Sandgem's north edge from its built map.bin (default: the in-repo layout)")
    args = parser.parse_args()
    open_cols, tiles = SANDGEM_NORTH_OPEN, SANDGEM_NORTH_TILES
    failed = 0
    if args.sandgem_mapbin:
        open_cols, tiles = read_sandgem(args.sandgem_mapbin)
        same = open_cols == SANDGEM_NORTH_OPEN and tiles == SANDGEM_NORTH_TILES
        print(f'Sandgem north edge from {args.sandgem_mapbin.name}: open columns {sorted(open_cols)}'
              f' ({"matches" if same else "DIFFERS FROM"} the recorded measurement)')
        failed += not same
    plan = json.loads(args.plan.read_text())
    results = verify(plan, open_cols, tiles)
    for name, ok, detail in results:
        print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else f'  {detail}'))
    failed += sum(not ok for _, ok, _ in results)
    print(f'{sum(ok for _, ok, _ in results)}/{len(results)} checks pass')
    if args.self_test:
        missed = self_test(plan, open_cols, tiles)
        print(f'{len(NEGATIVE) - missed}/{len(NEGATIVE)} broken plans caught')
        failed += missed
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
