#!/usr/bin/env python3
"""Collision, access and junction proof for the Verity Lakefront and Lake Verity design candidates
(plan JSON only; no ROM, no map files are written).

Movement model (the engine's):
  - on foot, a tile with collision 0 and elevation 3 is walkable; water (elevation 1) is an elevation
    mismatch, so it needs Surf;
  - a ledge ("jump": "south" / "west", MB_JUMP_SOUTH / MB_JUMP_WEST) is solid except when entered
    moving in its direction, which jumps the player one tile further; PlayerJumpLedge never checks the
    landing tile;
  - with Surf: from land you may enter adjacent water (IsPlayerFacingSurfableFishableWater), move
    through water, and land on any adjacent walkable elevation-3 tile (CanStopSurfing).

Verity Lakefront checks:
  L0 shape, legend and (width + 15) x (height + 14) <= 10,240;
  L1 declared exit tiles are walkable;
  L2 every walkable tile is reachable on foot from the Route 201 exits;
  L3 the Route 201 exits are reachable again from every walkable tile (no ledge pocket);
  L4 every exit reaches every other exit, in both directions;
  L5 the only walkable edge tiles are the declared exits (east upper, east lower, north);
  L6 every ledge (south and west) lands on walkable ground;
  L7 junction C: at the declared offset (even) the Lakefront's east column and Route 201's west column
     (read from ../route201/route201-candidate.json) match tile for tile: walkable faces walkable,
     ledge faces ledge, and trees are the same top/bottom half (Lakefront right halves, Route 201 left).
Lake Verity checks:
  V0 shape, legend and map-size limit;
  V1 the only walkable edge tiles are the declared south exit;
  V2 on foot, the tiles reachable from the exit are exactly the walkable tiles outside the declared
     Surf-only shore (and none of that shore is reachable on foot);
  V3 with Surf, every walkable tile and every water tile is reachable from the exit, and the exit is
     reachable again from all of them;
  V4 every water tile is Surf-only: collision 0, elevation 1, a pond-water metatile;
  V5 the central island (story-reserved) is closed: no walkable or water tile on it, and no warps;
North seam (Lakefront north <-> Lake south):
  N1 reciprocal, even offsets, and walkable faces walkable column for column over the shared span
     (every other edge tile on either side is solid);
  N2 the round trees stay whole across it (same left/right half; Lake bottom row = bottom halves,
     Lakefront top row = top halves).

usage: verify_verity_plans.py [--self-test]
--self-test also proves each check fails on a deliberately broken copy of the plans.
"""
import argparse
import copy
import json
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROUTE201 = HERE.parent / 'route201' / 'route201-candidate.json'
MAX_MAP_DATA_SIZE = 10240
POND = {161, 176, 177, 178, 184, 186, 192, 194, 203, 204}
TREE_LEFT, TREE_RIGHT = {468, 470, 476, 484}, {469, 471, 477, 485}
TREE_TOP, TREE_BOTTOM = {468, 469, 470, 471}, {476, 477, 484, 485}
STEPS = {'N': (0, -1), 'S': (0, 1), 'W': (-1, 0), 'E': (1, 0)}
JUMP = {'south': 'S', 'west': 'W'}


class Grid:
    def __init__(self, plan):
        self.plan, self.w, self.h = plan, plan['width'], plan['height']
        cell = lambda c: plan['legend'][c]
        self.cells = [[cell(c) for c in row] for row in plan['rows']]

    def at(self, x, y):
        return self.cells[y][x]

    def walk(self, x, y):
        v = self.at(x, y)
        return v['collision'] == 0 and v['elevation'] == 3

    def water(self, x, y):
        v = self.at(x, y)
        return v['collision'] == 0 and v['elevation'] == 1

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def foot(self, x, y):
        for d, (dx, dy) in STEPS.items():
            nx, ny = x + dx, y + dy
            if not self.inside(nx, ny):
                continue
            if self.walk(nx, ny):
                yield nx, ny
            elif JUMP.get(self.at(nx, ny).get('jump')) == d:
                lx, ly = nx + dx, ny + dy
                if self.inside(lx, ly) and self.walk(lx, ly):
                    yield lx, ly

    def surf(self, x, y):
        """Foot moves plus Surf: land <-> adjacent water, water <-> water."""
        if self.walk(x, y):
            yield from self.foot(x, y)
        for dx, dy in STEPS.values():
            nx, ny = x + dx, y + dy
            if self.inside(nx, ny) and (self.water(nx, ny) or (self.water(x, y) and self.walk(nx, ny))):
                yield nx, ny

    def reach(self, starts, step, reverse=False, nodes=None):
        if reverse:
            back = {}
            for (x, y) in nodes:
                for t in step(x, y):
                    back.setdefault(t, []).append((x, y))
            step = lambda x, y: back.get((x, y), [])
        seen, queue = set(starts), deque(starts)
        while queue:
            for t in step(*queue.popleft()):
                if t not in seen:
                    seen.add(t)
                    queue.append(t)
        return seen

    def tiles(self, pred):
        return {(x, y) for y in range(self.h) for x in range(self.w) if pred(x, y)}

    def exits(self):
        tiles = {}
        for ex in self.plan['exits']:
            a, b = ex['span']
            for i in range(a, b + 1):
                tiles[{'east': (self.w - 1, i), 'west': (0, i), 'south': (i, self.h - 1),
                       'north': (i, 0)}[ex['edge']]] = ex['name']
        return tiles


def shape_ok(plan):
    w, h = plan['width'], plan['height']
    return len(plan['rows']) == h and all(len(r) == w for r in plan['rows']) \
        and all(c in plan['legend'] for r in plan['rows'] for c in r) and (w + 15) * (h + 14) <= MAX_MAP_DATA_SIZE


def half(v):
    m = v['metatile']
    return ('L' if m in TREE_LEFT else 'R' if m in TREE_RIGHT else None,
            'T' if m in TREE_TOP else 'B' if m in TREE_BOTTOM else None)


def verify(vl_plan, lv_plan, r201_plan):
    results = []

    def check(name, ok, detail=''):
        results.append((name, bool(ok), detail))

    # ---- Verity Lakefront ----
    check('L0 Lakefront shape, legend and map-size limit', shape_ok(vl_plan))
    check('V0 Lake shape, legend and map-size limit', shape_ok(lv_plan))
    if not (shape_ok(vl_plan) and shape_ok(lv_plan)):
        return results
    vl, lv, r201 = Grid(vl_plan), Grid(lv_plan), Grid(r201_plan)
    vex = vl.exits()
    walkable = vl.tiles(vl.walk)
    check('L1 Lakefront exit tiles are walkable', all(t in walkable for t in vex), sorted(t for t in vex if t not in walkable))
    east = [t for t, n in vex.items() if n.startswith('east') and t in walkable]
    fwd = vl.reach(east, vl.foot)
    check('L2 every Lakefront tile reachable on foot from Route 201', not walkable - fwd, sorted(walkable - fwd)[:6])
    back = vl.reach(east, vl.foot, reverse=True, nodes=walkable)
    check('L3 Route 201 reachable again from every Lakefront tile (no ledge pocket)', not walkable - back,
          sorted(walkable - back)[:6])
    pairs = []
    names = sorted(set(vex.values()))
    for a in names:
        got = vl.reach([t for t, n in vex.items() if n == a and t in walkable], vl.foot)
        pairs += [f'{a}->{b}' for b in names if b != a and not any(t in got for t, n in vex.items() if n == b)]
    check('L4 every Lakefront exit reaches every other exit', not pairs, pairs)
    edge = {(x, y) for (x, y) in walkable if x in (0, vl.w - 1) or y in (0, vl.h - 1)}
    check('L5 only the declared Lakefront edges are open', not edge - set(vex), sorted(edge - set(vex))[:6])
    bad = []
    for (x, y) in vl.tiles(lambda x, y: vl.at(x, y).get('jump')):
        dx, dy = STEPS[JUMP[vl.at(x, y)['jump']]]
        if not (vl.inside(x + dx, y + dy) and vl.walk(x + dx, y + dy)):
            bad.append((x, y))
    check('L6 every Lakefront ledge lands on walkable ground', not bad, bad[:6])
    off = {e['offset'] for e in vl_plan['exits'] if e['edge'] == 'east'}
    seam_err = []
    if len(off) != 1 or next(iter(off)) % 2:
        seam_err.append(('offset', sorted(off)))
    else:
        k = next(iter(off))                  # Route 201 y = Lakefront y - k
        for y in range(vl.h):
            ry = y - k
            if not 0 <= ry < r201.h:
                if vl.walk(vl.w - 1, y):
                    seam_err.append((y, 'faces no Route 201 row'))
                continue
            a, b = vl.at(vl.w - 1, y), r201.at(0, ry)
            if vl.walk(vl.w - 1, y) != r201.walk(0, ry) or a.get('jump') != b.get('jump'):
                seam_err.append((y, ry, 'walk/ledge'))
            ha, hb = half(a), half(b)
            if ha[0] and hb[0] and (ha[0] != 'R' or hb[0] != 'L' or ha[1] != hb[1]):
                seam_err.append((y, ry, ha, hb))
        for ry in range(r201.h):
            if r201.walk(0, ry) and not 0 <= ry + k < vl.h:
                seam_err.append((ry, 'Route 201 row faces no Lakefront row'))
    check('L7 junction C matches Route 201 west edge (walk, ledge, tree halves; even offset)', not seam_err, seam_err[:5])

    # ---- Lake Verity ----
    lex = lv.exits()
    land = lv.tiles(lv.walk)
    edge = {(x, y) for (x, y) in land if x in (0, lv.w - 1) or y in (0, lv.h - 1)}
    check('V1 only the declared Lake exit is open', not edge - set(lex) and all(t in land for t in lex),
          sorted(edge ^ set(lex))[:6])
    x0, y0, x1, y1 = lv_plan['surf_only']
    shore = {(x, y) for (x, y) in land if x0 <= x <= x1 and y0 <= y <= y1}
    start = [t for t in lex if t in land]
    on_foot = lv.reach(start, lv.foot)
    check('V2 on foot: everything but the Surf-only shore is reachable, the shore is not',
          on_foot == land - shore and shore, (sorted((land - shore) - on_foot)[:4], sorted(on_foot & shore)[:4]))
    wet = lv.tiles(lv.water)
    nodes = land | wet
    with_surf = lv.reach(start, lv.surf)
    back = lv.reach(start, lv.surf, reverse=True, nodes=nodes)
    check('V3 with Surf: every land and water tile reachable from the exit and back', not nodes - with_surf
          and not nodes - back, (sorted(nodes - with_surf)[:4], sorted(nodes - back)[:4]))
    pond_any = lv.tiles(lambda x, y: lv.at(x, y)['metatile'] in POND or lv.at(x, y).get('surf'))
    bad_water = sorted(t for t in pond_any if not lv.water(*t) or lv.at(*t)['metatile'] not in POND)
    check('V4 every water tile is Surf-only (collision 0, elevation 1, pond water)', wet and not bad_water
          and wet == pond_any, bad_water[:6])
    ix0, iy0, ix1, iy1 = lv_plan['island']
    island = {(x, y) for x in range(ix0, ix1 + 1) for y in range(iy0, iy1 + 1)}
    open_island = sorted(t for t in island if t in land or t in wet)
    check('V5 the story-reserved island is closed (solid, no warps)', not open_island and not lv_plan.get('warps')
          and not lv_plan.get('stamps'), open_island[:6])

    # ---- North seam: Lakefront north <-> Lake south ----
    up = next(e for e in vl_plan['exits'] if e['edge'] == 'north')['offset']        # Lake x = VL x - up
    down = next(e for e in lv_plan['exits'] if e['edge'] == 'south')['offset']      # VL x = Lake x - down
    err, split = [], []
    if up != -down or up % 2:
        err.append(('offsets', up, down))
    else:
        for x in range(vl.w):
            lx = x - up
            if not 0 <= lx < lv.w:
                if vl.walk(x, 0):
                    err.append((x, 'faces no Lake column'))
                continue
            if vl.walk(x, 0) != lv.walk(lx, lv.h - 1):
                err.append((x, lx))
            ha, hb = half(vl.at(x, 0)), half(lv.at(lx, lv.h - 1))
            if ha[0] and hb[0] and (ha[0] != hb[0] or ha[1] != 'T' or hb[1] != 'B'):
                split.append((x, lx, ha, hb))
        for lx in range(lv.w):
            if lv.walk(lx, lv.h - 1) and not 0 <= lx + up < vl.w:
                err.append((lx, 'Lake column faces no Lakefront column'))
    check(f'N1 north seam: reciprocal even offsets ({up:+d} / {down:+d}), open faces open', not err, err[:5])
    check('N2 north seam keeps the round trees whole', not split and not err, split[:5])
    return results


def repaint(plan, cells, value):
    """Copy of a plan with cells repainted to a legend value (added under a free key)."""
    out = copy.deepcopy(plan)
    key = next(c for c in '!#$%&*+-./:;<=>?@' if c not in out['legend'])
    out['legend'][key] = value
    rows = [list(r) for r in out['rows']]
    for x0, y0, x1, y1 in cells:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rows[y][x] = key
    out['rows'] = [''.join(r) for r in rows]
    return out


def with_offset(plan, edge, offset):
    out = copy.deepcopy(plan)
    out['exits'] = [dict(e, offset=offset) if e['edge'] == edge else e for e in out['exits']]
    return out


TREE = {'metatile': 468, 'collision': 1, 'elevation': 0, 'note': 'tree'}
GRASS = {'metatile': 1, 'collision': 0, 'elevation': 3, 'note': 'grass'}
SHALLOW = {'metatile': 161, 'collision': 0, 'elevation': 3, 'note': 'water at ground level (no Surf needed)'}

NEGATIVE = [  # (label, which plan, mutation, check that must FAIL)
    ('odd junction C offset (Lakefront right +1)', 'vl', lambda p: with_offset(p, 'east', 1), 'L7'),
    ('a gap in the Lakefront west border', 'vl', lambda p: repaint(p, [(0, 9, 3, 9)], GRASS), 'L5'),
    ('the west-facing ledge lands on a tree', 'vl', lambda p: repaint(p, [(9, 8, 9, 8)], TREE), 'L6'),
    ('trees across the gap: the lake is cut off', 'vl', lambda p: repaint(p, [(6, 3, 7, 3)], TREE), 'L4'),
    ('Route 201 ledge row faces grass (Lakefront ledge removed at the seam)', 'vl',
     lambda p: repaint(p, [(21, 12, 21, 12)], GRASS), 'L7'),
    ('a walkable tile on the story-reserved island', 'lv', lambda p: repaint(p, [(23, 19, 23, 19)], GRASS), 'V5'),
    ('lake water walkable without Surf', 'lv', lambda p: repaint(p, [(20, 30, 25, 30)], SHALLOW), 'V4'),
    ('a land path into the Surf-only shore', 'lv', lambda p: repaint(p, [(12, 38, 37, 38)], GRASS), 'V2'),
    ('trees across the lake exit corridor', 'lv', lambda p: repaint(p, [(38, 41, 39, 41)], TREE), 'V3'),
    ('odd north-seam offsets (-31 / +31)', 'both', None, 'N1'),
]


def self_test(vl_plan, lv_plan, r201_plan):
    missed = 0
    for label, which, fn, must_fail in NEGATIVE:
        a, b = vl_plan, lv_plan
        if which == 'vl':
            a = fn(vl_plan)
        elif which == 'lv':
            b = fn(lv_plan)
        else:
            a, b = with_offset(vl_plan, 'north', -31), with_offset(lv_plan, 'south', 31)
        failed = [n.split()[0] for n, ok, _ in verify(a, b, r201_plan) if not ok]
        ok = must_fail in failed
        missed += not ok
        print(('PASS ' if ok else 'FAIL ') + f'negative: {label} -> caught by {failed}')
    return missed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lakefront', type=Path, default=HERE / 'verity-lakefront-candidate.json')
    parser.add_argument('--lake', type=Path, default=HERE / 'lake-verity-candidate.json')
    parser.add_argument('--route201', type=Path, default=ROUTE201)
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    vl_plan, lv_plan, r201_plan = (json.loads(p.read_text()) for p in (args.lakefront, args.lake, args.route201))
    results = verify(vl_plan, lv_plan, r201_plan)
    for name, ok, detail in results:
        print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else f'  {detail}'))
    failed = sum(not ok for _, ok, _ in results)
    print(f'{len(results) - failed}/{len(results)} checks pass')
    if args.self_test:
        missed = self_test(vl_plan, lv_plan, r201_plan)
        print(f'{len(NEGATIVE) - missed}/{len(NEGATIVE)} broken plans caught')
        failed += missed
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
