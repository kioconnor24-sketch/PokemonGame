#!/usr/bin/env python3
"""Collision and access proof for the Route 201 design candidate (plan JSON only;
no ROM, no map files).

Movement model (matches the engine): a tile with collision 0 is walkable; a
ledge (legend "jump": "south", MB_JUMP_SOUTH) is solid except when entered
moving south, which jumps the player to the tile beyond it. The engine does not
check the landing tile (PlayerJumpLedge), so every ledge must land on walkable
ground. Exits are walkable edge tiles inside a declared exit span.

Checks:
  1. every walkable tile is reachable from the Sandgem (east) exit;
  2. from every walkable tile the Sandgem exit is reachable again (no pocket a
     ledge can trap the player in);
  3. every exit reaches every other exit, in both directions;
  4. no walkable edge tile outside a declared exit (an exit that would open by
     accident once a neighbour is connected);
  5. every ledge lands on walkable ground;
  6. the east seam: with the declared offset, each open Route 201 edge row
     faces an open Sandgem west-edge row and vice versa.

usage: verify_route201_plan.py [PLAN_JSON] [--sandgem-mapbin MAP.BIN] [--self-test]
--self-test also proves each check fails on a deliberately broken copy of the plan.
"""
import argparse
import json
import struct
from collections import deque
from pathlib import Path

# Sandgem Town's west edge (x = 0) as built in PR #133 (layout 32 x 28, commit
# 38100116): rows 10-13 are open (grass verge, road rows 11-12), all others trees.
SANDGEM_W, SANDGEM_H = 32, 28
SANDGEM_WEST_OPEN = {10, 11, 12, 13}

STEPS = {'N': (0, -1), 'S': (0, 1), 'W': (-1, 0), 'E': (1, 0)}


def load(plan):
    legend = plan['legend']
    w, h = plan['width'], plan['height']
    walk = [[legend[c]['collision'] == 0 for c in row] for row in plan['rows']]
    ledge = [[legend[c].get('jump') for c in row] for row in plan['rows']]
    return w, h, walk, ledge


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
            lx, ly = nx, ny + 1
            if 0 <= ly < h and walk[ly][lx]:
                yield lx, ly


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


def verify(plan, sandgem_west_open=SANDGEM_WEST_OPEN):
    w, h, walk, ledge = load(plan)
    exits = exit_tiles(plan, w, h)
    results = []

    def check(name, ok, detail=''):
        results.append((name, bool(ok), detail))

    walkable = {(x, y) for y in range(h) for x in range(w) if walk[y][x]}
    bad_exit = sorted(t for t in exits if t not in walkable)
    check('declared exit tiles are walkable', not bad_exit, bad_exit[:8])
    east = [t for t, n in exits.items() if n == 'east' and t in walkable]
    fwd = reach(w, h, walk, ledge, east)
    unreached = sorted(walkable - fwd)
    check('1 every walkable tile reachable from the Sandgem exit', not unreached, unreached[:8])
    back = reach(w, h, walk, ledge, east, reverse=True)
    trapped = sorted(walkable - back)
    check('2 Sandgem exit reachable again from every walkable tile (no ledge trap)', not trapped, trapped[:8])
    names = sorted(set(exits.values()))
    pairs = []
    for a in names:
        got = reach(w, h, walk, ledge, [t for t, n in exits.items() if n == a and t in walkable])
        for b in names:
            if a != b and not any(t in got for t, n in exits.items() if n == b):
                pairs.append(f'{a}->{b}')
    check('3 every exit reaches every other exit (both directions)', not pairs, pairs)
    edge = {(x, y) for (x, y) in walkable if x in (0, w - 1) or y in (0, h - 1)}
    stray = sorted(edge - set(exits))
    check('4 no walkable edge tile outside a declared exit', not stray, stray[:8])
    bad_ledge = sorted((x, y) for y in range(h) for x in range(w)
                       if ledge[y][x] == 'south' and not (y + 1 < h and walk[y + 1][x]))
    check('5 every ledge lands on walkable ground', not bad_ledge, bad_ledge[:8])
    ex = next(e for e in plan['exits'] if e['name'] == 'east')
    offset = ex['offset']           # Sandgem's top row sits at Route 201 y = offset
    mismatch = []
    for y in range(h):
        sy = y - offset
        if 0 <= sy < SANDGEM_H:
            if walk[y][w - 1] != (sy in sandgem_west_open):
                mismatch.append((y, sy))
    for sy in sandgem_west_open:
        if not 0 <= sy + offset < h:
            mismatch.append(('sandgem row off route', sy))
    check(f'6 east seam matches Sandgem west edge at offset {offset} (Sandgem side {-offset})', not mismatch, mismatch)
    return results


def mutated(plan, kind, cells, **change):
    """Copy of the plan with cells repainted as solid tree, grass or ledge."""
    legend = dict(plan['legend'])
    pick = {'tree': ('t', {'metatile': 468, 'collision': 1, 'elevation': 0}),
            'grass': ('g', {'metatile': 1, 'collision': 0, 'elevation': 3})}[kind]
    legend[pick[0]] = pick[1]
    rows = [list(r) for r in plan['rows']]
    for x0, y0, x1, y1 in cells:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rows[y][x] = pick[0]
    out = dict(plan, legend=legend, rows=[''.join(r) for r in rows])
    if 'offset' in change:
        out['exits'] = [dict(e, offset=change['offset']) if e['name'] == 'east' else e for e in plan['exits']]
    return out


NEGATIVE = [  # (label, mutation, check that must FAIL)
    ('trees over the big grass patch cut the only walk to Sandgem', ('tree', [(42, 5, 52, 7)]), '3 '),
    ('the short ledge lands on a tree', ('tree', [(57, 11, 57, 11)]), '5 '),
    ('trees between the middle grass and the main path: below the long ledge becomes a one-way pocket',
     ('tree', [(30, 12, 31, 15)]), '2 '),
    ('an accidental gap in the east tree line opens an undeclared edge', ('grass', [(62, 12, 63, 12)]), '4 '),
    ('wrong connection offset misaligns the Sandgem seam', ('tree', [], {'offset': -4}), '6 '),
]


def self_test(plan, open_rows):
    bad = 0
    for label, (kind, cells, *extra), must_fail in NEGATIVE:
        res = verify(mutated(plan, kind, cells, **(extra[0] if extra else {})), open_rows)
        failed = [n for n, ok, _ in res if not ok]
        ok = any(n.startswith(must_fail) for n in failed)
        bad += not ok
        print(('PASS ' if ok else 'FAIL ') + f'negative: {label} -> caught by {failed}')
    return bad


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plan', nargs='?', type=Path, default=Path(__file__).with_name('route201-candidate.json'))
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--sandgem-mapbin', type=Path, help="read Sandgem's west edge from its built map.bin")
    args = parser.parse_args()
    open_rows = SANDGEM_WEST_OPEN
    if args.sandgem_mapbin:
        raw = args.sandgem_mapbin.read_bytes()
        blocks = struct.unpack(f'<{SANDGEM_W * SANDGEM_H}H', raw)
        open_rows = {y for y in range(SANDGEM_H) if (blocks[y * SANDGEM_W] >> 10) & 3 == 0}
        print(f'Sandgem west edge from {args.sandgem_mapbin}: open rows {sorted(open_rows)}')
    plan = json.loads(args.plan.read_text())
    results = verify(plan, open_rows)
    for name, ok, detail in results:
        print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else f'  {detail}'))
    failed = sum(not ok for _, ok, _ in results)
    print(f'{len(results) - failed}/{len(results)} checks pass')
    if args.self_test:
        missed = self_test(plan, open_rows)
        print(f'{len(NEGATIVE) - missed}/{len(NEGATIVE)} broken plans caught')
        failed += missed
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
