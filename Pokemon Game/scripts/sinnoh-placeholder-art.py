#!/usr/bin/env python3
"""Sinnoh placeholder art: preview the Emerald tilesets already in the engine and
check the placeholder manifest against the engine's own declarations.

Read-only on engine data and standard-library only. Subcommands:
  sheet   render metatiles of a primary + secondary tileset pair to a PNG
  plan    render a rough layout plan (rows of legend characters) to a PNG
  check   validate SINNOH_PLACEHOLDER_MANIFEST.csv against headers/behaviors

Only tilesets compiled into the Emerald build count (the `#if !IS_FRLG` half
of src/data/tilesets/*.h). FRLG tilesets use a different primary layout (640
metatiles, 7 palettes) and are not linked into Averon's build.
"""

import argparse
import csv
import json
from pathlib import Path
import re
import struct
import sys
import zlib

ENGINE = Path(__file__).resolve().parents[1] / "engine"
NUM_TILES_IN_PRIMARY = 512
NUM_METATILES_IN_PRIMARY = 512
NUM_PALS_IN_PRIMARY = 6
HEADERS = "src/data/tilesets/headers.h"
GRAPHICS = ("src/data/tilesets/graphics.h", "src/graphics.c")  # gTileset_General's art is in graphics.c
METATILES = "src/data/tilesets/metatiles.h"
BEHAVIORS = "include/constants/metatile_behaviors.h"
OBJECT_GRAPHICS = "src/data/object_events/object_event_graphics_info_pointers.h"


# ---------------------------------------------------------------- PNG I/O ---

def _chunks(data):
    pos = 8
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        yield kind, data[pos + 8:pos + 8 + length]
        pos += 12 + length


def _unfilter(raw, width_bytes, height, bpp_bytes):
    rows, prev, pos = [], bytearray(width_bytes), 0
    for _ in range(height):
        kind, line = raw[pos], bytearray(raw[pos + 1:pos + 1 + width_bytes])
        pos += 1 + width_bytes
        for i in range(width_bytes):
            left = line[i - bpp_bytes] if i >= bpp_bytes else 0
            up, upleft = prev[i], prev[i - bpp_bytes] if i >= bpp_bytes else 0
            if kind == 1:
                line[i] = (line[i] + left) & 0xFF
            elif kind == 2:
                line[i] = (line[i] + up) & 0xFF
            elif kind == 3:
                line[i] = (line[i] + (left + up) // 2) & 0xFF
            elif kind == 4:
                p = left + up - upleft
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - upleft)
                pred = left if pa <= pb and pa <= pc else up if pb <= pc else upleft
                line[i] = (line[i] + pred) & 0xFF
        rows.append(bytes(line))
        prev = line
    return rows


def read_indexed_png(path):
    """(width, height, [row of palette indices]) for a non-interlaced 4/8-bit indexed PNG."""
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path}: not a PNG")
    idat, header = b"", None
    for kind, body in _chunks(data):
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat += body
    width, height, depth, ctype, _, _, interlace = header
    if ctype != 3 or depth not in (4, 8) or interlace:
        raise ValueError(f"{path}: expected non-interlaced indexed 4/8-bit PNG")
    width_bytes = (width * depth + 7) // 8
    rows = _unfilter(zlib.decompress(idat), width_bytes, height, 1)
    out = []
    for row in rows:
        if depth == 8:
            out.append(list(row[:width]))
        else:
            out.append([(b >> 4, b & 15)[x & 1] for x, b in ((x, row[x >> 1]) for x in range(width))])
    return width, height, out


def write_rgb_png(path, width, height, pixels):
    """pixels: list of rows, each a list of (r, g, b)."""
    raw = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in pixels)

    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    Path(path).write_bytes(b"\x89PNG\r\n\x1a\n"
                           + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
                           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


# ------------------------------------------------------- engine catalogue ---

def emerald_text(text):
    """Drop FRLG-only branches (`#if IS_FRLG` bodies, the `#else` of `#if !IS_FRLG`)."""
    out, stack = [], []
    for line in text.splitlines():
        directive = line.strip()
        if directive.startswith("#if"):
            if re.match(r"#if\s+!\s*IS_FRLG\b", directive):
                stack.append(["frlg", True])
            elif re.match(r"#if\s+IS_FRLG\b", directive):
                stack.append(["frlg", False])
            else:
                stack.append(["other", True])
            continue
        if directive.startswith("#else") and stack:
            if stack[-1][0] == "frlg":
                stack[-1][1] = not stack[-1][1]
            continue
        if directive.startswith("#endif") and stack:
            stack.pop()
            continue
        if all(active for _, active in stack):
            out.append(line)
    return "\n".join(out)


def tileset_catalogue(engine=ENGINE):
    """{gTileset_X: {secondary, tiles, palettes, metatiles, attributes}} for Emerald-build tilesets."""
    headers = emerald_text((engine / HEADERS).read_text())
    graphics = "\n".join(emerald_text((engine / path).read_text()) for path in GRAPHICS)
    metas = emerald_text((engine / METATILES).read_text())
    tiles = dict(re.findall(r'(gTilesetTiles_\w+)\[\]\s*=\s*INC\w+\("([^"]+)"', graphics))
    palettes = {}
    for name, body in re.findall(r'(gTilesetPalettes_\w+)\[\]\[16\]\s*=\s*\{(.*?)\};', graphics, re.S):
        palettes[name] = re.findall(r'"([^"]+\.pal)"', body)
    binaries = dict(re.findall(r'(g(?:Metatiles|MetatileAttributes)_\w+)\[\]\s*=\s*INCBIN_U16\("([^"]+)"', metas))
    catalogue = {}
    for name, body in re.findall(r'const struct Tileset (gTileset_\w+)\s*=\s*\{(.*?)\};', headers, re.S):
        fields = dict(re.findall(r'\.(\w+)\s*=\s*([\w]+)', body))
        if fields.get("tiles") not in tiles or fields.get("metatiles") not in binaries:
            continue
        catalogue[name] = dict(secondary=fields.get("isSecondary") == "TRUE",
                               tiles=tiles[fields["tiles"]], palettes=palettes.get(fields.get("palettes"), []),
                               metatiles=binaries[fields["metatiles"]],
                               attributes=binaries.get(fields.get("metatileAttributes")))
    return catalogue


def behavior_names(engine=ENGINE):
    """[name by value] from the MB_* enum (implicit sequential values)."""
    body = (engine / BEHAVIORS).read_text()
    body = body[body.index("enum"):]
    names = []
    for token in re.findall(r'\b(MB_\w+)\b(?:\s*=\s*(\w+))?\s*,', body):
        name, value = token
        if value:
            names.extend([None] * (int(value, 0) - len(names)))
        names.append(name)
    return names


class Tileset:
    def __init__(self, engine, entry):
        _, _, pixels = read_indexed_png(engine / entry["tiles"])
        self.tiles = []
        for ty in range(len(pixels) // 8):
            for tx in range(len(pixels[0]) // 8):
                self.tiles.append([pixels[ty * 8 + y][tx * 8:tx * 8 + 8] for y in range(8)])
        self.palettes = [read_jasc(engine / p) for p in entry["palettes"]]
        raw = (engine / entry["metatiles"]).read_bytes()
        self.metatiles = [struct.unpack_from("<8H", raw, i) for i in range(0, len(raw) - 15, 16)]
        attrs = (engine / entry["attributes"]).read_bytes() if entry["attributes"] else b""
        self.attributes = list(struct.unpack(f"<{len(attrs) // 2}H", attrs))


def read_jasc(path):
    lines = Path(path).read_text().split()
    count = int(lines[2])
    values = list(map(int, lines[3:3 + 3 * count]))
    return [tuple(values[i:i + 3]) for i in range(0, len(values), 3)]


class Pair:
    """A primary + secondary tileset as the game combines them."""

    def __init__(self, primary, secondary, engine=ENGINE):
        cat = tileset_catalogue(engine)
        for name in (primary, secondary):
            if name not in cat:
                raise KeyError(f"{name} is not an Emerald-build tileset")
        self.primary, self.secondary = Tileset(engine, cat[primary]), Tileset(engine, cat[secondary])
        # Palettes 0-5 come from the primary, 6-12 from the secondary.
        self.palettes = self.primary.palettes[:NUM_PALS_IN_PRIMARY] + self.secondary.palettes[NUM_PALS_IN_PRIMARY:]

    def metatile(self, metatile_id):
        if metatile_id < NUM_METATILES_IN_PRIMARY:
            return self.primary.metatiles[metatile_id], self.primary.attributes[metatile_id]
        index = metatile_id - NUM_METATILES_IN_PRIMARY
        return self.secondary.metatiles[index], self.secondary.attributes[index]

    def count(self):
        return NUM_METATILES_IN_PRIMARY + len(self.secondary.metatiles)

    def tile(self, index):
        if index < NUM_TILES_IN_PRIMARY:
            return self.primary.tiles[index] if index < len(self.primary.tiles) else None
        index -= NUM_TILES_IN_PRIMARY
        return self.secondary.tiles[index] if index < len(self.secondary.tiles) else None

    def render(self, metatile_id):
        """16x16 list of RGB rows: backdrop, bottom layer, then top layer."""
        entries, _ = self.metatile(metatile_id)
        backdrop = self.palettes[0][0]
        canvas = [[backdrop] * 16 for _ in range(16)]
        for layer in (entries[:4], entries[4:]):
            for quarter, entry in enumerate(layer):
                tile = self.tile(entry & 0x3FF)
                palette = self.palettes[(entry >> 12) & 0xF] if ((entry >> 12) & 0xF) < len(self.palettes) else None
                if tile is None or palette is None:
                    continue
                ox, oy = (quarter & 1) * 8, (quarter >> 1) * 8
                for y in range(8):
                    sy = 7 - y if entry & 0x800 else y
                    for x in range(8):
                        sx = 7 - x if entry & 0x400 else x
                        colour = tile[sy][sx]
                        if colour:
                            canvas[oy + y][ox + x] = palette[colour]
        return canvas


def compose(cells, columns, gap=1, gap_colour=(40, 40, 40)):
    """Grid of 16x16 cells (None = blank) into one RGB image."""
    rows = (len(cells) + columns - 1) // columns
    width, height = columns * (16 + gap) - gap, rows * (16 + gap) - gap
    image = [[gap_colour] * width for _ in range(height)]
    for i, cell in enumerate(cells):
        if cell is None:
            continue
        ox, oy = (i % columns) * (16 + gap), (i // columns) * (16 + gap)
        for y in range(16):
            image[oy + y][ox:ox + 16] = cell[y]
    return width, height, image


# ------------------------------------------------------------- commands ---

def cmd_sheet(args):
    pair = Pair(args.primary, args.secondary, args.engine)
    first = NUM_METATILES_IN_PRIMARY if args.range == "secondary" else 0
    last = pair.count() if args.range != "primary" else NUM_METATILES_IN_PRIMARY
    ids = list(range(first, last))
    names = behavior_names(args.engine)
    width, height, image = compose([pair.render(i) for i in ids], args.columns)
    write_rgb_png(args.out, width, height, image)
    if args.index:
        with open(args.index, "w", newline="") as handle:
            out = csv.writer(handle)
            out.writerow(["metatile", "row", "column", "behavior"])
            for n, i in enumerate(ids):
                behavior = pair.metatile(i)[1] & 0xFF
                out.writerow([i, n // args.columns, n % args.columns,
                              names[behavior] if behavior < len(names) and names[behavior] else behavior])
    print(f"{args.out}: {len(ids)} metatiles ({args.primary} + {args.secondary}), {width}x{height}")
    return 0


LAYOUTS = "data/layouts/layouts.json"


def pack_block(metatile, collision=0, elevation=0):
    """A map grid block: metatile id bits 0-9, collision 10-11, elevation 12-15."""
    return (metatile & 0x3FF) | ((collision & 3) << 10) | ((elevation & 0xF) << 12)


def layout_entry(engine, layout_id):
    for entry in json.loads((engine / LAYOUTS).read_text())["layouts"]:
        if entry.get("id") == layout_id:
            return entry
    raise KeyError(f"{layout_id} is not in {LAYOUTS}")


def read_blocks(engine, entry):
    raw = (engine / entry["blockdata_filepath"]).read_bytes()
    width, height = entry["width"], entry["height"]
    if len(raw) != width * height * 2:
        raise ValueError(f"{entry['id']}: blockdata is {len(raw)} B, expected {width * height * 2}")
    values = struct.unpack(f"<{width * height}H", raw)
    return [list(values[y * width:(y + 1) * width]) for y in range(height)]


def compose_plan(plan, engine=ENGINE):
    """Grid of map blocks from a plan: legend-painted rows, then exact block
    stamps copied from existing layouts that use the same tileset pair."""
    rows = plan["rows"]
    width, height = plan["width"], plan["height"]
    if len(rows) != height or any(len(row) != width for row in rows):
        raise ValueError(f"rows must be {height} strings of {width} characters")
    missing = sorted({c for row in rows for c in row} - set(plan["legend"]))
    if missing:
        raise ValueError(f"legend has no entry for {missing}")
    legend = {c: pack_block(v["metatile"], v.get("collision", 0), v.get("elevation", 3))
              for c, v in plan["legend"].items()}
    grid = [[legend[c] for c in row] for row in rows]
    for stamp in plan.get("stamps", []):
        entry = layout_entry(engine, stamp["from"])
        source = read_blocks(engine, entry)
        sx, sy, sw, sh = stamp["src"]
        ax, ay = stamp["at"]
        if sx < 0 or sy < 0 or sx + sw > entry["width"] or sy + sh > entry["height"]:
            raise ValueError(f"stamp {stamp.get('note', '')}: source rectangle leaves {stamp['from']}")
        if entry["primary_tileset"] != plan["primary"]:
            raise ValueError(f"stamp from {stamp['from']} uses primary {entry['primary_tileset']}")
        if entry["secondary_tileset"] != plan["secondary"]:
            # Another secondary is fine only for art that lives in the shared primary.
            secondary_ids = sorted({b & 0x3FF for row in source[sy:sy + sh] for b in row[sx:sx + sw]
                                    if (b & 0x3FF) >= NUM_METATILES_IN_PRIMARY})
            if secondary_ids:
                raise ValueError(f"stamp {stamp.get('note', '')} from {stamp['from']} uses "
                                 f"{entry['secondary_tileset']} metatiles {secondary_ids[:6]}")
        if ax < 0 or ay < 0 or ax + sw > width or ay + sh > height:
            raise ValueError(f"stamp {stamp.get('note', '')}: lands outside the {width}x{height} plan")
        for y in range(sh):
            grid[ay + y][ax:ax + sw] = source[sy + y][sx:sx + sw]
    return grid


MARK_COLOURS = {"exit": (255, 255, 0), "warp": (0, 255, 255), "npc": (255, 0, 255),
                "reserved": (255, 128, 0), "path": (255, 255, 255)}


def render_grid(pair, grid, collision=False, marks=()):
    cache, cells = {}, []
    for row in grid:
        for block in row:
            metatile = block & 0x3FF
            if metatile not in cache:
                cache[metatile] = pair.render(metatile) if metatile < pair.count() else [[(255, 0, 255)] * 16] * 16
            cell = cache[metatile]
            if collision and block & 0x0C00:
                cell = [[((r + 255) // 2, g // 2, b // 2) for r, g, b in line] for line in cell]
            cells.append(cell)
    width = len(grid[0])
    w, h, image = compose(cells, width, gap=0)
    for mark in marks:
        colour = MARK_COLOURS.get(mark.get("kind"), (255, 255, 255))
        x, y = mark["at"]
        mw, mh = mark.get("size", [1, 1])
        x0, y0, x1, y1 = x * 16, y * 16, min(w, (x + mw) * 16) - 1, min(h, (y + mh) * 16) - 1
        for px in range(x0, x1 + 1):
            for py in (y0, y0 + 1, y1 - 1, y1):
                image[py][px] = colour
        for py in range(y0, y1 + 1):
            for px in (x0, x0 + 1, x1 - 1, x1):
                image[py][px] = colour
    return w, h, image


def cmd_plan(args):
    plan = json.loads(Path(args.plan).read_text())
    grid = compose_plan(plan, args.engine)
    pair = Pair(plan["primary"], plan["secondary"], args.engine)
    w, h, image = render_grid(pair, grid, args.collision, () if args.no_marks else plan.get("marks", []))
    write_rgb_png(args.out, w, h, image)
    if args.blockdata:
        args.blockdata.write_bytes(struct.pack(f"<{plan['width'] * plan['height']}H", *[b for row in grid for b in row]))
    print(f"{args.out}: {plan['width']}x{plan['height']} metatiles ({w}x{h} px), {len(plan.get('stamps', []))} stamps")
    return 0


def recolor_snow(image):
    """Preview only: push green and brown ground toward snow white/ice blue.
    Real snow would need an owner-approved derived palette, not this filter."""
    out = []
    for row in image:
        line = []
        for r, g, b in row:
            if g >= r and g >= b and g - min(r, b) > 24:          # foliage and grass
                level = min(255, 150 + g // 2)
                line.append((level - 10, level, 255))
            elif r > b and g > b and r - b > 40 and r < 230:        # earth and paths
                level = min(255, 120 + (r + g) // 4)
                line.append((level, level, min(255, level + 25)))
            else:
                line.append((r, g, b))
        out.append(line)
    return out


def cmd_gallery(args):
    """One review image: a labelled-by-order grid of biome crops from real layouts."""
    spec = json.loads(Path(args.spec).read_text())
    cell_w, cell_h = spec["crop"]
    cells, pairs = [], {}
    for item in spec["biomes"]:
        entry = layout_entry(args.engine, item["layout"])
        grid = read_blocks(args.engine, entry)
        x, y = item["at"]
        grid = [row[x:x + cell_w] for row in grid[y:y + cell_h]]
        if len(grid) != cell_h or any(len(row) != cell_w for row in grid):
            raise ValueError(f"{item['biome']}: crop leaves {item['layout']}")
        key = (entry["primary_tileset"], entry["secondary_tileset"])
        if key not in pairs:
            pairs[key] = Pair(*key, engine=args.engine)
        _, _, image = render_grid(pairs[key], grid)
        cells.append(recolor_snow(image) if item.get("recolor") == "snow" else image)
    columns, gap = spec.get("columns", 3), 4
    pw, ph = cell_w * 16, cell_h * 16
    rows = (len(cells) + columns - 1) // columns
    width, height = columns * (pw + gap) - gap, rows * (ph + gap) - gap
    canvas = [[(20, 20, 20)] * width for _ in range(height)]
    for i, image in enumerate(cells):
        ox, oy = (i % columns) * (pw + gap), (i // columns) * (ph + gap)
        for yy in range(ph):
            canvas[oy + yy][ox:ox + pw] = image[yy]
    write_rgb_png(args.out, width, height, canvas)
    print(f"{args.out}: {len(cells)} biomes in {columns} columns ({width}x{height} px)")
    return 0


def cmd_layout(args):
    entry = layout_entry(args.engine, args.layout)
    grid = read_blocks(args.engine, entry)
    if args.crop:
        x, y, cw, ch = args.crop
        grid = [row[x:x + cw] for row in grid[y:y + ch]]
    pair = Pair(entry["primary_tileset"], entry["secondary_tileset"], args.engine)
    w, h, image = render_grid(pair, grid, args.collision)
    write_rgb_png(args.out, w, h, image)
    print(f"{args.out}: {args.layout} {len(grid[0])}x{len(grid)} ({entry['primary_tileset']} + {entry['secondary_tileset']})")
    return 0


MANIFEST_COLUMNS = ["token", "role", "biome", "primary", "secondary", "metatiles", "behaviors",
                    "object_graphics", "footprint", "source", "license", "collision", "replace_when",
                    "final_owner", "placements", "status"]


def object_graphics_ids(engine=ENGINE):
    text = (engine / OBJECT_GRAPHICS).read_text()
    return set(re.findall(r'\[(OBJ_EVENT_GFX_\w+)\]', text))


def check_manifest(path, engine=ENGINE):
    """Problems with each manifest row; [] when every reference is real."""
    cat, names = tileset_catalogue(engine), behavior_names(engine)
    gfx = object_graphics_ids(engine)
    problems, pairs = [], {}
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != MANIFEST_COLUMNS:
            return [f"columns must be {MANIFEST_COLUMNS}"]
        rows = list(reader)
    seen = set()
    for n, row in enumerate(rows, start=2):
        where = f"line {n} ({row['token']})"
        if row["token"] in seen:
            problems.append(f"{where}: duplicate token")
        seen.add(row["token"])
        for field in ("primary", "secondary"):
            if row[field] and row[field] not in cat:
                problems.append(f"{where}: {field} {row[field]} is not an Emerald-build tileset")
        if row["primary"] in cat and cat[row["primary"]]["secondary"]:
            problems.append(f"{where}: {row['primary']} is a secondary tileset")
        if row["secondary"] in cat and not cat[row["secondary"]]["secondary"]:
            problems.append(f"{where}: {row['secondary']} is a primary tileset")
        ids = [int(x, 0) for x in row["metatiles"].split()] if row["metatiles"] else []
        wanted = row["behaviors"].split() if row["behaviors"] else []
        if wanted and len(wanted) != len(ids):
            problems.append(f"{where}: {len(ids)} metatiles but {len(wanted)} behaviors")
        if ids and row["primary"] in cat and row["secondary"] in cat:
            key = (row["primary"], row["secondary"])
            if key not in pairs:
                pairs[key] = Pair(*key, engine=engine)
            pair = pairs[key]
            for i, metatile in enumerate(ids):
                if not 0 <= metatile < pair.count():
                    problems.append(f"{where}: metatile {metatile} outside 0..{pair.count() - 1}")
                    continue
                behavior = pair.metatile(metatile)[1] & 0xFF
                name = names[behavior] if behavior < len(names) else str(behavior)
                if i < len(wanted) and wanted[i] != name:
                    problems.append(f"{where}: metatile {metatile} behaves as {name}, manifest says {wanted[i]}")
        if row["object_graphics"] and row["object_graphics"] not in gfx:
            problems.append(f"{where}: {row['object_graphics']} is not an object event graphics id")
        for field in ("source", "license", "replace_when", "status"):
            if not row[field]:
                problems.append(f"{where}: {field} is empty")
        if "FRLG" in row["source"].upper() and row["status"] == "USABLE":
            problems.append(f"{where}: FRLG art is not linked into the Emerald build")
    return problems


def cmd_check(args):
    problems = check_manifest(args.manifest, args.engine)
    for problem in problems:
        print("MANIFEST ERROR: " + problem)
    if not problems:
        with open(args.manifest, newline="") as handle:
            count = sum(1 for _ in csv.DictReader(handle))
        print(f"{count} placeholder rows resolve to real Emerald-build tilesets, metatiles, behaviors and graphics")
    return 1 if problems else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--engine", type=Path, default=ENGINE)
    sub = parser.add_subparsers(dest="command", required=True)
    sheet = sub.add_parser("sheet")
    sheet.add_argument("primary")
    sheet.add_argument("secondary")
    sheet.add_argument("--range", choices=("secondary", "primary", "all"), default="secondary")
    sheet.add_argument("--columns", type=int, default=16)
    sheet.add_argument("--out", type=Path, required=True)
    sheet.add_argument("--index", type=Path, help="CSV of metatile id, grid position and behavior")
    plan = sub.add_parser("plan")
    plan.add_argument("plan", type=Path)
    plan.add_argument("--out", type=Path, required=True)
    plan.add_argument("--collision", action="store_true", help="tint blocks with collision set")
    plan.add_argument("--no-marks", action="store_true", help="omit exit/warp/NPC/reserved outlines")
    plan.add_argument("--blockdata", type=Path, help="also write the composed map.bin (u16 blocks)")
    layout = sub.add_parser("layout")
    layout.add_argument("layout", help="layout id from layouts.json, e.g. LAYOUT_DEWFORD_TOWN")
    layout.add_argument("--crop", type=int, nargs=4, metavar=("X", "Y", "W", "H"))
    layout.add_argument("--collision", action="store_true")
    layout.add_argument("--out", type=Path, required=True)
    gallery = sub.add_parser("gallery")
    gallery.add_argument("spec", type=Path, help="JSON: crop [w, h], columns, biomes [{biome, layout, at, recolor?}]")
    gallery.add_argument("--out", type=Path, required=True)
    check = sub.add_parser("check")
    check.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    commands = {"sheet": cmd_sheet, "plan": cmd_plan, "layout": cmd_layout, "gallery": cmd_gallery,
                "check": cmd_check}
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
