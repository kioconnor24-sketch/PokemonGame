#!/usr/bin/env python3
"""Find (and optionally fix) orphan quarters of the General tileset's 2x2 round trees in a layout.

The placeholder generators pick a tree quarter by global x/y parity, so a forest edge on an odd row or
column leaves a quarter whose 2x2 partner is grass or road: a visibly cut tree. A quarter is an orphan
when any cell of its aligned 2x2 block (x - x%2, y - y%2) inside the map is not a tree quarter; cells
outside the map count as trees (the neighbour or border continues them).

--fix swaps only the metatile id of each orphan for a one-tile bush (default 22, General primary),
keeping that cell's collision and elevation bits, so collision geometry is unchanged.

  sinnoh-tree-repair.py --engine ENGINE LAYOUT_ID [LAYOUT_ID ...] [--fix] [--bush 22]
"""
import argparse
import json
import struct
import sys
from pathlib import Path

TREE = {468, 469, 470, 471, 476, 477, 484, 485}


def orphans(blocks, width, height):
    tree = lambda x, y: not (0 <= x < width and 0 <= y < height) or (blocks[y * width + x] & 0x3FF) in TREE
    out = []
    for y in range(height):
        for x in range(width):
            if (blocks[y * width + x] & 0x3FF) not in TREE:
                continue
            bx, by = x - x % 2, y - y % 2
            if not all(tree(xx, yy) for xx in (bx, bx + 1) for yy in (by, by + 1)):
                out.append((x, y))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--engine', required=True)
    ap.add_argument('layouts', nargs='+')
    ap.add_argument('--fix', action='store_true')
    ap.add_argument('--bush', type=int, default=22)
    a = ap.parse_args(argv)
    engine = Path(a.engine)
    table = {l['id']: l for l in json.loads((engine / 'data/layouts/layouts.json').read_text())['layouts'] if 'id' in l}
    total = 0
    for lid in a.layouts:
        lay = table[lid]
        path = engine / lay['blockdata_filepath']
        raw = path.read_bytes()
        blocks = list(struct.unpack(f'<{len(raw) // 2}H', raw))
        found = orphans(blocks, lay['width'], lay['height'])
        total += len(found)
        print(f'{lid}: {len(found)} orphan tree quarters' + (' -> fixed' if a.fix and found else ''))
        if a.fix and found:
            for x, y in found:
                i = y * lay['width'] + x
                blocks[i] = (blocks[i] & ~0x3FF) | a.bush
            path.write_bytes(struct.pack(f'<{len(blocks)}H', *blocks))
            assert not orphans(blocks, lay['width'], lay['height'])
    return 0 if a.fix or total == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
