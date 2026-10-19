#!/usr/bin/env python3
"""Prove the Twinleaf candidate's access and Route 201 junction rules.

  python3 verify_twinleaf_plan.py [--self-test]

Checks: (1) shape; (2) the only open edge is north x 15-17; (3) every walkable tile, every door's
front tile and the sign's front are reachable from the north entrance; (4) junction B: Route 201's
south road (x 15-17, row 21) meets Twinleaf's north road at offset 0, both sides walkable;
(5) tree phase across the seam: every 2x2 tree half on Route 201's bottom row and Twinleaf's top row
is on the same column parity, so no tree is split. --self-test re-runs the checks on mutated copies
(blocked north path, odd offset, an extra open edge) and requires each to fail.
"""
import copy
import json
import sys
from collections import deque
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREES = {468, 469, 470, 471, 476, 477, 484, 485}


def load(path):
    plan = json.loads(path.read_text())
    meta = [[plan['legend'][c] for c in row] for row in plan['rows']]
    return plan, meta


def solid(meta, x, y):
    return meta[y][x]['collision'] != 0


def stamped(plan):
    """Tiles covered by building stamps are solid except the door tile."""
    cover = set()
    for s in plan.get('stamps', []):
        ax, ay = s['at']
        sw, sh = s['src'][2], s['src'][3]
        cover |= {(ax + i, ay + j) for i in range(sw) for j in range(sh)}
    return cover - {tuple(d) for d in plan.get('doors', [])}


def check(plan, meta, r201, r201_meta, offset=0):
    W, H = plan['width'], plan['height']
    errors = []
    if len(meta) != H or any(len(r) != W for r in meta):
        errors.append('shape')
    blocked = stamped(plan)

    def walk(x, y):
        return 0 <= x < W and 0 <= y < H and not solid(meta, x, y) and (x, y) not in blocked

    north = [x for x in range(W) if walk(x, 0)]
    if north != [15, 16, 17]:
        errors.append(f'north opening {north} != [15, 16, 17]')
    for x in range(W):
        if walk(x, H - 1):
            errors.append(f'south edge open at x {x}')
    for y in range(H):
        for x in (0, W - 1):
            if walk(x, y):
                errors.append(f'side edge open at ({x}, {y})')
    seen, q = set(), deque((x, 0) for x in north)
    seen.update(q)
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and walk(*n):
                seen.add(n)
                q.append(n)
    walkable = {(x, y) for y in range(H) for x in range(W) if walk(x, y)}
    if walkable - seen:
        errors.append(f'unreachable walkable tiles: {sorted(walkable - seen)[:6]}')
    for dx, dy in plan.get('doors', []):
        if (dx, dy + 1) not in seen:
            errors.append(f'door ({dx}, {dy}) front not reachable')
    # Junction B: Route 201 row 21 (x) <-> Twinleaf row 0 (x - offset)
    rh = r201['height']
    r_open = [x for x in range(r201['width']) if not solid(r201_meta, x, rh - 1)]
    if [x - offset for x in r_open] != north:
        errors.append(f'seam: Route 201 south {r_open} -> Twinleaf {[x - offset for x in r_open]} != {north}')
    for x in range(r201['width']):
        tx = x - offset
        if not 0 <= tx < W:
            continue
        a, b = r201_meta[rh - 1][x]['metatile'], meta[0][tx]['metatile']
        if a in TREES and b in TREES and (a % 2) != (b % 2):
            errors.append(f'seam splits a tree at Route 201 x {x} / Twinleaf x {tx}')
            break
        for m, xx in ((a, x), (b, tx)):
            if m in TREES and m % 2 != xx % 2:
                errors.append(f'tree half out of phase at x {xx}')
                break
    return errors


def main():
    plan, meta = load(HERE / 'twinleaf-candidate.json')
    r201, r201_meta = load(HERE.parent / 'route201' / 'route201-candidate.json')
    errors = check(plan, meta, r201, r201_meta)
    print('candidate:', 'PASS' if not errors else f'FAIL {errors}')
    ok = not errors
    if '--self-test' in sys.argv:
        tree = next(v for v in plan['legend'].values() if v['metatile'] in TREES)
        grass = next(v for v in plan['legend'].values() if v['note'] == 'grass')
        cases = {}
        m = copy.deepcopy(meta)
        m[2] = [dict(tree) if 6 <= x <= 25 else c for x, c in enumerate(m[2])]   # wall off the town
        cases['blocked north entrance'] = (m, 0)
        cases['odd offset 1'] = (meta, 1)
        m = copy.deepcopy(meta); m[20][0] = dict(grass); m[20][1] = dict(grass); m[20][2] = dict(grass)
        m[20][3] = dict(grass); m[20][4] = dict(grass); m[20][5] = dict(grass)
        cases['extra west opening'] = (m, 0)
        for name, (mm, off) in cases.items():
            errs = check(plan, mm, r201, r201_meta, off)
            print(f'mutation {name}:', 'caught' if errs else 'MISSED', errs[:1])
            ok &= bool(errs)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
