#!/usr/bin/env python3
"""Measure and classify an original-game overhead into a metatile grid (geometry reference only).

Bulbapedia/Bulbagarden DP/Pt overheads are clean top-down renders, often foreshortened vertically
(16 px per tile across, ~12.33 px down). This tool:
  1. measures the horizontal and vertical tile periods from the tree border (trees are 2x2 tiles),
  2. finds the horizontal grid phase that minimises distinct 16-px column blocks, and the vertical
     phase that maximises cell purity,
  3. classifies each cell by majority colour: T tree, S sand path, G grass, g tall grass, W water,
     B building/roof, F fence/stone, o other (lowercase = under 50 % pure),
and prints the grid with row numbers. The image is read via ImageMagick (`convert`); nothing from it is
written into the repo by this tool. Use it to read footprints; the design generator remains the source.

  sinnoh-ref-grid.py IMAGE.png [--tile-w 16] [--tile-h auto] [--x-phase auto] [--y-phase auto]
"""
import argparse
import subprocess
import sys


def load(path):
    w, h = map(int, subprocess.run(['identify', '-format', '%w %h', path], capture_output=True, text=True,
                                   check=True).stdout.split())
    raw = subprocess.run(['convert', path, '-depth', '8', 'rgb:-'], capture_output=True, check=True).stdout
    return w, h, raw


def classify(c):
    r, g, b = c
    if r > 200 and g > 170 and b < 170 and r - b > 60:
        return 'S'
    if b > 200 and r < 170 and g > 170 and g < 235:
        return 'W'
    if g > 200 and r < 150 and b < 170:
        return 'G'
    if g > 120 and r < 110 and b < 110 and g - r > 50 and g < 200:
        return 'g'
    if g < 170 and r < 120 and b < 110:
        return 'T'
    if r > 150 and g > 150 and b > 150 and abs(r - g) < 30 and abs(g - b) < 40:
        return 'F'
    if g > 120 and b > 120 and r < 110:
        return 'B'
    return 'o'


def period(w, h, raw, axis, x0, x1, lo, hi):
    """Best repeat distance of pixel equality along an axis over a column band (the tree border)."""
    px = lambda x, y: raw[3 * (y * w + x):3 * (y * w + x) + 3]
    best = []
    for p in range(lo, hi):
        same = tot = 0
        if axis == 'y':
            for x in range(x0, x1):
                for y in range(0, h - p, 2):
                    tot += 1
                    same += px(x, y) == px(x, y + p)
        else:
            for y in range(0, h, 3):
                for x in range(x0, min(x1, w - p)):
                    tot += 1
                    same += px(x, y) == px(x + p, y)
        best.append((same / max(tot, 1), p))
    return sorted(best, reverse=True)


def grid(w, h, raw, tw, th, xp, yp):
    px = lambda x, y: tuple(raw[3 * (y * w + x):3 * (y * w + x) + 3])
    rows = []
    r = 0
    while yp + r * th < h:
        y0, y1 = yp + r * th, yp + (r + 1) * th
        line, pur = '', []
        c = 0
        while xp + c * tw < w:
            x0, x1 = xp + c * tw, xp + (c + 1) * tw
            cnt = {}
            for y in range(max(0, round(y0)), min(h, round(y1))):
                for x in range(max(0, x0), min(w, x1)):
                    k = classify(px(x, y))
                    cnt[k] = cnt.get(k, 0) + 1
            n = sum(cnt.values())
            k = max(cnt, key=cnt.get) if n else '?'
            p = cnt.get(k, 0) / n if n else 0
            line += k if p >= 0.5 else k.lower()
            pur.append(p)
            c += 1
        rows.append((r, y0, line, sum(pur) / len(pur)))
        r += 1
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('image')
    ap.add_argument('--tile-w', type=int, default=16)
    ap.add_argument('--tile-h', type=float)
    ap.add_argument('--x-phase', type=int)
    ap.add_argument('--y-phase', type=float)
    ap.add_argument('--border', type=int, default=80, help='left band width used to measure tree periods')
    a = ap.parse_args(argv)
    w, h, raw = load(a.image)
    tw = a.tile_w
    if a.tile_h is None:
        vert = period(w, h, raw, 'y', 0, a.border, 10, 80)
        tree_v = vert[0][1]
        # the best repeat may be one, two or three tree heights; prefer the smallest consistent one
        for mult in (1, 2, 3):
            if any(abs(p - tree_v / mult * k) <= 1 for _, p in vert[:6] for k in (1, 2)):
                pass
        cands = [p for s, p in vert[:6]]
        base = min(cands)
        th = base / 2 if base > 1.6 * tw else base / 2 if base > 20 else base
        # refine: average spacing from the strongest candidates that are near multiples of th
        ks = [(p, round(p / th)) for p in cands if round(p / th) and abs(p / round(p / th) - th) < 1]
        th = sum(p for p, _ in ks) / sum(k for _, k in ks)
        print(f'vertical tree period candidates {vert[:4]} -> tile height {th:.3f} px')
    else:
        th = a.tile_h
    if a.x_phase is None:
        # Full tw x tw pixel blocks repeat exactly in a tilemap; the true column phase minimises the share
        # of distinct blocks (best over a few row phases; rows are foreshortened, columns are not).
        rows_ = [raw[3 * w * y:3 * w * (y + 1)] for y in range(h)]
        best = None
        for xp in range(tw):
            for yp0 in range(0, tw, 2):
                seen, n = set(), 0
                for y in range(yp0, h - tw + 1, tw):
                    for x in range(xp, w - tw + 1, tw):
                        seen.add(b''.join(rows_[y + k][3 * x:3 * (x + tw)] for k in range(tw)))
                        n += 1
                score = len(seen) / max(n, 1)
                if best is None or score < best[0]:
                    best = (score, xp)
        xp = best[1] - tw if best[1] else 0
    else:
        xp = a.x_phase
    if a.y_phase is None:
        best = None
        for t in range(0, int(th * 2)):
            yp = t / 2 - th
            rows = grid(w, h, raw, tw, th, xp, yp)
            pur = sum(r[3] for r in rows) / len(rows)
            if best is None or pur > best[0]:
                best = (pur, yp)
        yp = best[1]
    else:
        yp = a.y_phase
    print(f'image {w}x{h}; tile {tw}x{th:.3f}; x phase {xp}; y phase {yp:.2f}')
    rows = grid(w, h, raw, tw, th, xp, yp)
    width = len(rows[0][2])
    print('     ' + ''.join(str(c % 10) for c in range(width)))
    for r, y0, line, _ in rows:
        print(f'{r:3d}  {line}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
