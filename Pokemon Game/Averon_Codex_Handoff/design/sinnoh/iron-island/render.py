#!/usr/bin/env python3
"""Pure-Python renderer for Averon tilesets and map binaries (no PIL; stdlib zlib/struct only).

  render.py bank PRIMARY SECONDARY OUT.png            numbered sheet of every metatile in both banks
  render.py map PRIMARY SECONDARY MAP.bin WIDTH OUT.png [--grid]
PRIMARY/SECONDARY are tileset directories (e.g. engine/data/tilesets/primary/general).
"""
import pathlib
import struct
import sys
import zlib

PRIMARY_TILES, PRIMARY_METATILES, PRIMARY_PALS = 512, 512, 6


def read_png(path):
    data = pathlib.Path(path).read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", path
    pos, idat, plte = 8, b"", None
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h, depth, ctype = struct.unpack(">IIBB", body[:10])
        elif kind == b"PLTE":
            plte = body
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    assert ctype == 3 and depth in (4, 8), (path, ctype, depth)
    raw, stride = zlib.decompress(idat), (w * depth + 7) // 8
    rows, prev = [], bytearray(stride)
    for y in range(h):
        f, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - 1] if i else 0
            b, c = prev[i], prev[i - 1] if i else 0
            if f == 1: line[i] = (line[i] + a) & 255
            elif f == 2: line[i] = (line[i] + b) & 255
            elif f == 3: line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
        prev = line
        rows.append([(line[x // 2] >> (4 if x % 2 == 0 else 0)) & 15 for x in range(w)] if depth == 4 else list(line[:w]))
    return w, h, rows


def write_png(path, w, h, pixels):
    raw = b"".join(b"\0" + bytes(c for px in pixels[y * w:(y + 1) * w] for c in px) for y in range(h))
    chunk = lambda k, b: struct.pack(">I", len(b)) + k + b + struct.pack(">I", zlib.crc32(k + b) & 0xFFFFFFFF)
    pathlib.Path(path).write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                                   + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def read_pal(path):
    lines = pathlib.Path(path).read_text().split()
    vals = list(map(int, lines[3:3 + 48]))
    return [tuple(vals[i:i + 3]) for i in range(0, 48, 3)]


class Bank:
    def __init__(self, primary, secondary):
        p, s = pathlib.Path(primary), pathlib.Path(secondary)
        self.tiles = self._tiles(p)[:PRIMARY_TILES]
        self.tiles += [[[0] * 8 for _ in range(8)]] * (PRIMARY_TILES - len(self.tiles))
        self.tiles += self._tiles(s)
        pals = [read_pal(p / "palettes" / f"{i:02d}.pal") for i in range(PRIMARY_PALS)]
        pals += [read_pal(s / "palettes" / f"{i:02d}.pal") for i in range(PRIMARY_PALS, 13)]
        self.pals = pals
        pm, sm = (p / "metatiles.bin").read_bytes(), (s / "metatiles.bin").read_bytes()
        pm += b"\0" * (PRIMARY_METATILES * 16 - len(pm))
        self.meta = [struct.unpack("<8H", (pm + sm)[i * 16:(i + 1) * 16]) for i in range((len(pm) + len(sm)) // 16)]
        pa, sa = (p / "metatile_attributes.bin").read_bytes(), (s / "metatile_attributes.bin").read_bytes()
        pa += b"\0" * (PRIMARY_METATILES * 2 - len(pa))
        self.attr = list(struct.unpack("<%dH" % ((len(pa) + len(sa)) // 2), pa + sa))
        self.cache = {}

    @staticmethod
    def _tiles(d):
        w, h, rows = read_png(d / "tiles.png")
        return [[rows[ty * 8 + y][tx * 8:tx * 8 + 8] for y in range(8)] for ty in range(h // 8) for tx in range(w // 8)]

    def metatile(self, mid):
        """16x16 RGB pixels (list of 256 tuples)."""
        if mid in self.cache:
            return self.cache[mid]
        out = [(0, 0, 0)] * 256
        words = self.meta[mid] if mid < len(self.meta) else (0,) * 8
        for layer in range(2):
            for q in range(4):
                wd = words[layer * 4 + q]
                t, hf, vf, pal = wd & 1023, wd >> 10 & 1, wd >> 11 & 1, wd >> 12
                tile = self.tiles[t] if t < len(self.tiles) else [[0] * 8] * 8
                colors = self.pals[pal] if pal < len(self.pals) else [(255, 0, 255)] * 16
                ox, oy = (q % 2) * 8, (q // 2) * 8
                for y in range(8):
                    for x in range(8):
                        c = tile[7 - y if vf else y][7 - x if hf else x]
                        if c or layer == 0:
                            out[(oy + y) * 16 + ox + x] = colors[c]
        self.cache[mid] = out
        return out


def render_cells(bank, cells, width, out, grid=False, scale=1):
    height = len(cells) // width
    W, H = width * 16, height * 16
    px = [(0, 0, 0)] * (W * H)
    for i, c in enumerate(cells):
        x0, y0, m = (i % width) * 16, (i // width) * 16, bank.metatile(c & 1023)
        for y in range(16):
            px[(y0 + y) * W + x0:(y0 + y) * W + x0 + 16] = m[y * 16:y * 16 + 16]
        if grid and c & 0x0C00:
            for k in range(16):
                for (x, y) in ((x0 + k, y0 + k), (x0 + 15 - k, y0 + k)):
                    r, g, b = px[y * W + x]
                    px[y * W + x] = (255, g // 2, b // 2)
    if scale > 1:
        px = [px[(y // scale) * W + x // scale] for y in range(H * scale) for x in range(W * scale)]
        W, H = W * scale, H * scale
    write_png(out, W, H, px)


def main():
    cmd = sys.argv[1]
    if cmd == "bank":
        bank = Bank(sys.argv[2], sys.argv[3])
        n = len(bank.meta)
        render_cells(bank, list(range(n)), 16, sys.argv[4])
    elif cmd == "map":
        bank = Bank(sys.argv[2], sys.argv[3])
        raw = pathlib.Path(sys.argv[4]).read_bytes()
        render_cells(bank, list(struct.unpack("<%dH" % (len(raw) // 2), raw)), int(sys.argv[5]), sys.argv[6],
                     grid="--grid" in sys.argv)


if __name__ == "__main__":
    main()
