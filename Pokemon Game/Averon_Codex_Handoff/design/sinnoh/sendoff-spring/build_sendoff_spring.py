#!/usr/bin/env python3
"""Spring Path -> Sendoff Spring -> Turnback Cave, and Maniac Tunnel (W13, south-east lane; OFF-ENGINE staging).

New physical geography; no donor map exists for any of these. Nothing of Codex's is modified: Route 214 (his
eastern-loop staging) gets a DEV-only *derived* overlay.

- Route 214 overlay: its east forest is a clean grid of 2 x 2 trees. Rows 20-21 from x 30 to the east edge are cut
  to grass on that grid (one tree row), the trees above get the bank's forest-edge bottom (486/487), and an east
  connection leads to Spring Path. Its existing closed cliff cave
  mouth (9, 35) gets a warp into Maniac Tunnel. Everything else is byte-identical.
- Spring Path and Sendoff Spring are drawn in the eastern-loop bank itself (General + its outdoor secondary),
  because a seam draws the neighbouring map with the current map's tiles. Every cell word is copied from that
  family's staged maps, and every horizontal and vertical metatile pair in them must occur in those maps
  (strict: an unattested pair refuses the build).
- Turnback Cave 1F/B1F/B2F and Maniac Tunnel use W1's cave kit (Oreburgh Gate walls, Granite Cave mouth and
  ladders). Turnback Cave is an ordinary fixed ladder graph, not the DS random-room mechanic.
- Sendoff Spring's way into Turnback Cave is a neutral step-on portal at the end of a forest alcove (the bank has
  no free-standing cave mouth).

No Giratina, Distortion World, story, objects, items, encounters or sections (MAPSEC_PENDING_OWNER).

  build_sendoff_spring.py --engine ENGINE --out DIR
"""
import argparse
import collections
import importlib.util
import json
import pathlib
import shutil
import struct
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
FAMILY = SINNOH / "eastern-loop"
spec = importlib.util.spec_from_file_location("w1", SINNOH / "iron-island/build_iron_island.py")
w1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w1)
render = w1.render
OUTDOOR = ("Route212_North", "Route212_South", "Route213", "Route214", "Route215", "ValorLakefront", "VeilstoneCity",
           "PastoriaCity")
TILESETS = ("gTileset_General", "gTileset_EasternDevOutdoorSecondary")
R214_W = 44
CUT_ROWS, CUT_X = (20, 21), 30          # Route 214: tree row cut to grass, x 30..43
MANIAC_MOUTH = (9, 35)                   # Route 214's closed cliff cave mouth (metatile 570)
SP_W, SP_H, SP_OFFSET = 24, 24, 10       # Spring Path; Route 214 row 20 is its row 10
SS_W, SS_H = 32, 30                      # Sendoff Spring; Spring Path's row r is its row r
# 2 x 2 blocks (bx, by) of grass in a forest of trees; the rest of each map is trees.
SP_PATH = [(0, 5), (1, 5), (2, 5), (3, 5), (3, 4), (3, 3), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (8, 2), (8, 3),
           (8, 4), (8, 5), (8, 6), (8, 7), (8, 8), (9, 8), (10, 8), (11, 8)]
LONE_TREES = [(4, 5), (11, 4), (4, 10), (11, 11)]
SS_OPEN = [(0, 8), (1, 8), (2, 8)] + [(x, y) for x in range(3, 13) for y in range(3, 13) if (x, y) not in LONE_TREES] \
    + [(8, 1), (8, 2)]
POND = (12, 10, 21, 17)                  # Sendoff Spring's spring: inclusive tile rectangle inside the meadow
TURNBACK_PORTAL = (16, 2)


class Family:
    """The eastern-loop staged maps: cell words, metatile adjacency pairs."""

    def __init__(self):
        self.maps, self.read = {}, {}
        for name in OUTDOOR:
            d = FAMILY / "staged" / name
            raw = (d / "averon-map.bin").read_bytes()
            width = struct.unpack(">I", (d / "averon.png").read_bytes()[16:20])[0] // 16
            cells = struct.unpack("<%dH" % (len(raw) // 2), raw)
            assert len(cells) % width == 0, name
            self.maps[name] = (width, cells)
            self.read[f"eastern-loop/staged/{name}/averon-map.bin"] = w1.sha(raw)
        self.pairs = set()
        for width, cells in self.maps.values():
            h = len(cells) // width
            for y in range(h):
                for x in range(width):
                    a = cells[y * width + x] & 1023
                    if x + 1 < width:
                        self.pairs.add(("h", a, cells[y * width + x + 1] & 1023))
                    if y + 1 < h:
                        self.pairs.add(("v", a, cells[(y + 1) * width + x] & 1023))

    def word(self, name, x, y, mid):
        width, cells = self.maps[name]
        assert cells[y * width + x] & 1023 == mid, (name, x, y, cells[y * width + x] & 1023, mid)
        return cells[y * width + x]

    def check(self, name, cells, width):
        h = len(cells) // width
        for y in range(h):
            for x in range(width):
                a = cells[y * width + x] & 1023
                for kind, nx, ny in (("h", x + 1, y), ("v", x, y + 1)):
                    if nx < width and ny < h and (kind, a, cells[ny * width + nx] & 1023) not in self.pairs:
                        raise SystemExit(f"{name}: unattested {kind} pair at {(x, y)}: {a} / {cells[ny * width + nx] & 1023}")


def tree_words(fam):
    """Tree top, bottom, and the bottom drawn over grass (the bank's forest edge: 486/487 under 470/471)."""
    return ([fam.word("Route214", 30, 12, 470), fam.word("Route214", 31, 12, 471)],
            [fam.word("Route214", 30, 13, 478), fam.word("Route214", 31, 13, 479)],
            [fam.word("Route214", 20, 5, 486), fam.word("Route214", 21, 5, 487)])


def forest(fam, width, height, open_blocks):
    """Trees on the 2 x 2 grid of Route 214's east forest; open blocks are grass."""
    top, bottom, edge = tree_words(fam)
    grass = fam.word("Route214", 24, 19, 1)
    cells = [0] * (width * height)
    for by in range(height // 2):
        for bx in range(width // 2):
            for dx in (0, 1):
                x = 2 * bx + dx
                if (bx, by) in open_blocks:
                    cells[2 * by * width + x] = cells[(2 * by + 1) * width + x] = grass
                    continue
                cells[2 * by * width + x] = top[dx]
                cells[(2 * by + 1) * width + x] = (edge if (bx, by + 1) in open_blocks else bottom)[dx]
    return cells


def route214(fam):
    width, src = fam.maps["Route214"]
    assert width == R214_W
    cells = list(src)
    grass = fam.word("Route214", 24, 19, 1)
    _, bottom, edge = tree_words(fam)
    for y in CUT_ROWS:
        for x in range(CUT_X, width):
            assert src[y * width + x] & 1023 in (470, 471, 478, 479), (x, y)
            cells[y * width + x] = grass
    for x in range(CUT_X, width):                                 # trees above the cut get the forest-edge bottom
        y = CUT_ROWS[0] - 1
        assert src[y * width + x] == bottom[x % 2], (x, y)
        cells[y * width + x] = edge[x % 2]
    mx, my = MANIAC_MOUTH
    assert src[my * width + mx] & 1023 == 570 and not src[my * width + mx] & 0xC00
    return cells


def spring_path(fam):
    return forest(fam, SP_W, SP_H, set(SP_PATH))


def sendoff_spring(fam):
    cells = forest(fam, SS_W, SS_H, set(SS_OPEN))
    x0, y0, x1, y1 = POND
    piece = {"tl": fam.word("Route214", 20, 6, 176), "t": fam.word("Route214", 21, 6, 177),
             "tr": fam.word("Route214", 26, 6, 178), "l": fam.word("Route214", 20, 7, 184),
             "c": fam.word("Route214", 21, 7, 161), "r": fam.word("Route214", 29, 9, 186)}
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            row = "t" if y == y0 else ""
            col = "l" if x == x0 else "r" if x == x1 else ""
            key = (row + col) if row and col else row or col or "c"
            cells[y * SS_W + x] = piece[key]
    shore = fam.word("Route214", 20, 17, 2)                      # the grass drawn under Route 214's pond
    for x in range(x0, x1 + 1):
        cells[(y1 + 1) * SS_W + x] = shore
    return cells


def caves(eng):
    out = {}
    cv = w1.Cave(eng, 22, 16)                                     # Maniac Tunnel: one dug-out room
    cv.room(3, 3, 18, 11)
    cv.block(8, 5, 12, 9)
    cv.exit_south(5, 11, eng)
    out["ManiacTunnel"] = (cv, dict(exit=(5, 11)))
    cv = w1.Cave(eng, 24, 18)
    cv.room(3, 3, 20, 13)
    cv.block(9, 5, 14, 9)
    cv.exit_south(11, 13, eng)
    cv.ladder(19, 4, eng, down=True)
    out["TurnbackCave_1F"] = (cv, dict(exit=(11, 13), down=(19, 4)))
    cv = w1.Cave(eng, 28, 22)                                     # pillar hall
    cv.room(3, 3, 24, 18)
    for bx, by in ((7, 6), (16, 6), (7, 13), (16, 13)):
        cv.block(bx, by, bx + 3, by + 3)
    cv.ladder(4, 4, eng, down=False)
    cv.ladder(23, 17, eng, down=True)
    out["TurnbackCave_B1F"] = (cv, dict(up=(4, 4), down=(23, 17)))
    cv = w1.Cave(eng, 24, 20)                                     # innermost chamber
    cv.room(3, 3, 20, 16)
    cv.block(9, 8, 14, 12)
    cv.ladder(19, 15, eng, down=False)
    out["TurnbackCave_B2F"] = (cv, dict(up=(19, 15)))
    return out


def build(engine_root):
    eng, fam = w1.Engine(engine_root), Family()
    r214, sp, ss = route214(fam), spring_path(fam), sendoff_spring(fam)
    for name, cells, width in (("Route214", r214, R214_W), ("SpringPath", sp, SP_W), ("SendoffSpring", ss, SS_W)):
        fam.check(name, cells, width)
    cv = caves(eng)
    hdr = json.loads((FAMILY / "staged/Route214/map.json").read_text())
    assert not [c for c in hdr["connections"] if c["direction"] == "right"]
    maniac_warp = len(hdr["warp_events"])
    hdr["warp_events"].append({"x": MANIAC_MOUTH[0], "y": MANIAC_MOUTH[1], "elevation": 0,
                               "dest_map": "MAP_MANIAC_TUNNEL", "dest_warp_id": "0"})
    hdr["connections"].append({"map": "MAP_SPRING_PATH", "offset": SP_OFFSET, "direction": "right"})
    tp = TURNBACK_PORTAL
    maps = {
        "SpringPath": (dict(w1.header("MAP_SPRING_PATH", "SpringPath", "LAYOUT_SPRING_PATH", "MUS_ROUTE110",
                                      "MAP_TYPE_ROUTE", []),
                            connections=[{"map": "MAP_ROUTE214", "offset": -SP_OFFSET, "direction": "left"},
                                         {"map": "MAP_SENDOFF_SPRING", "offset": 0, "direction": "right"}]),
                       (sp, SP_W, SP_H) + TILESETS),
        "SendoffSpring": (dict(w1.header("MAP_SENDOFF_SPRING", "SendoffSpring", "LAYOUT_SENDOFF_SPRING", "MUS_ROUTE110",
                                         "MAP_TYPE_ROUTE", [(*tp, "MAP_TURNBACK_CAVE_1F", 0)],
                                         [(*tp, "ToTurnbackCave", ("MAP_TURNBACK_CAVE_1F", 0))]),
                               connections=[{"map": "MAP_SPRING_PATH", "offset": 0, "direction": "left"}]),
                          (ss, SS_W, SS_H) + TILESETS),
        "ManiacTunnel": (w1.header("MAP_MANIAC_TUNNEL", "ManiacTunnel", "LAYOUT_MANIAC_TUNNEL", "MUS_CAVE_OF_ORIGIN",
                                   "MAP_TYPE_UNDERGROUND", [(*cv["ManiacTunnel"][1]["exit"], "MAP_ROUTE214", maniac_warp)])),
        "TurnbackCave_1F": (w1.header("MAP_TURNBACK_CAVE_1F", "TurnbackCave_1F", "LAYOUT_TURNBACK_CAVE_1F",
                                      "MUS_CAVE_OF_ORIGIN", "MAP_TYPE_UNDERGROUND",
                                      [(*cv["TurnbackCave_1F"][1]["exit"], "MAP_SENDOFF_SPRING", 0),
                                       (*cv["TurnbackCave_1F"][1]["down"], "MAP_TURNBACK_CAVE_B1F", 0)])),
        "TurnbackCave_B1F": (w1.header("MAP_TURNBACK_CAVE_B1F", "TurnbackCave_B1F", "LAYOUT_TURNBACK_CAVE_B1F",
                                       "MUS_CAVE_OF_ORIGIN", "MAP_TYPE_UNDERGROUND",
                                       [(*cv["TurnbackCave_B1F"][1]["up"], "MAP_TURNBACK_CAVE_1F", 1),
                                        (*cv["TurnbackCave_B1F"][1]["down"], "MAP_TURNBACK_CAVE_B2F", 0)])),
        "TurnbackCave_B2F": (w1.header("MAP_TURNBACK_CAVE_B2F", "TurnbackCave_B2F", "LAYOUT_TURNBACK_CAVE_B2F",
                                       "MUS_CAVE_OF_ORIGIN", "MAP_TYPE_UNDERGROUND",
                                       [(*cv["TurnbackCave_B2F"][1]["up"], "MAP_TURNBACK_CAVE_B1F", 1)])),
    }
    for name, (c, _) in cv.items():
        maps[name] = (maps[name], (c.cells, c.w, c.h, "gTileset_General", "gTileset_Cave"))
    coords = {"SendoffSpring": [(*tp, "ToTurnbackCave", ("MAP_TURNBACK_CAVE_1F", 0))]}
    return eng, fam, maps, coords, (r214, hdr)


def check(maps, r214_hdr):
    """Every warp lands on a warp leading back to its own map; connections are mutual with opposite offsets."""
    headers = {h["id"]: h for h, _ in maps.values()}
    headers["MAP_ROUTE214"] = r214_hdr
    for mid, h in headers.items():
        for w in h["warp_events"]:
            if w["dest_map"] not in headers:
                continue
            back = headers[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
            assert back["dest_map"] == mid, (mid, w, back)
        for c in h["connections"]:
            if c["map"] not in headers:
                continue
            opposite = {"left": "right", "right": "left", "up": "down", "down": "up"}[c["direction"]]
            assert {"map": mid, "offset": -c["offset"], "direction": opposite} in headers[c["map"]]["connections"], (mid, c)
    return True


def banks(eng, tmp):
    """Renderer banks: General + Cave, and General + the eastern-loop runtime secondary (Rustboro graphics with the
    family's metatile records, as its prepare_runtime binds them)."""
    sec = pathlib.Path(tmp) / "eastern"
    shutil.copytree(eng.root / "data/tilesets/secondary/rustboro", sec)
    for kind, name in (("metatiles", "metatiles.bin"), ("attributes", "metatile_attributes.bin")):
        shutil.copy(FAMILY / f"hotel-link/outdoor-family/secondary-{kind}.bin", sec / name)
    general = eng.root / "data/tilesets/primary/general"
    return {TILESETS[1]: render.Bank(general, sec),
            "gTileset_Cave": render.Bank(general, eng.root / "data/tilesets/secondary/cave")}


def write(engine_root, out):
    eng, fam, maps, coords, (r214, r214_hdr) = build(engine_root)
    check(maps, r214_hdr)
    st = pathlib.Path(out) / "staged"
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "maps": {}}
    tmp = tempfile.mkdtemp()
    bank = banks(eng, tmp)
    for name, (hdr, (cells, w, h, prim, sec)) in maps.items():
        d = st / name
        d.mkdir(parents=True, exist_ok=True)
        data = struct.pack("<%dH" % len(cells), *cells)
        border = struct.pack("<4H", *([cells[0]] * 4))           # tree or cave rock
        (d / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (d / "scripts.inc").write_text(w1.scripts(name, coords.get(name, ())))
        (d / "map.bin").write_bytes(data)
        (d / "border.bin").write_bytes(border)
        (d / "layout.json").write_text(json.dumps({"id": hdr["layout"], "name": name + "_Layout", "width": w, "height": h,
                                                   "primary_tileset": prim, "secondary_tileset": sec}, indent=2) + "\n")
        render.render_cells(bank[sec], cells, w, d / "preview.png")
        receipt["maps"][name] = {"width": w, "height": h, "map_sha256": w1.sha(data), "border_sha256": w1.sha(border)}
    d = st / "Route214-dev-overlay"
    d.mkdir(parents=True, exist_ok=True)
    (d / "map.json").write_text(json.dumps(r214_hdr, indent=2) + "\n")
    (d / "map.bin").write_bytes(struct.pack("<%dH" % len(r214), *r214))
    render.render_cells(bank[TILESETS[1]], r214, R214_W, d / "preview.png")
    shutil.rmtree(tmp)
    receipt["inputs_sha256"] = dict(sorted({**fam.read, **eng.read}.items()))
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(write(a.engine, a.out)["status"])
