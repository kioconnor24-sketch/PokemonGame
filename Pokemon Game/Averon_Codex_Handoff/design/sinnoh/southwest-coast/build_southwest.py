#!/usr/bin/env python3
"""Routes 219, 220 and 221 (south-west coast) from LiderMorti00's donor geometry, in Averon's own banks (OFF-ENGINE).

Source: LiderMorti00/Sinnoh-pokeemerald-expansion @ 38228bb574a3557345852b758d5f1a65eb01bb22, read through
scripts/sinnoh-donor-map-pilot.py's read_donor_map, git blobs checked (the same blobs #237's selection.json lists).
The donor draws them with General + its Petalburg; they are drawn with Averon's General + Dewford, the bank pair of
Averon's Sandgem and Twinleaf. No donor art; the shared banks are not modified.

Conversion, every change listed and asserted:
- primary IDs are kept: every primary attribute word these maps use is identical in Averon's General;
- the donor's few secondary (Petalburg) IDs become Averon tiles with the same behaviour (SECONDARY);
- Route 221's large building (x 79-85, rows 10-15, door (82, 15)) is replaced by Averon's Dewford house
  door-on-door (closed shell, no warp); its other cells become the surrounding collision-marked plateau grass and
  the two walkable yard ornaments become plain grass. The house above it loses its donor roof-top row to the tree
  row it sits in;
- collision/elevation bits are the donor's, cell for cell.
Connections: Route 219 <-> Route 220 (+5) and Route 220 <-> Route 221 (-4) as the donor; Route 219 up to Averon's
Sandgem at +3 (Sandgem's open south edge x 19-24 meets Route 219's x 22-27). The donor's Route 220 <-> Twinleaf link
is dropped: Averon's Twinleaf has a closed south edge. Route 221's duplicated left connection is listed once.
Excluded: objects, scripts, items, encounters, music, sections (MAPSEC_PENDING_OWNER), Surf grants.

  build_southwest.py --donor-root DONOR --out DIR [--engine ENGINE]   staged maps (+ previews with --engine)
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pilot", HERE.parents[3] / "scripts/sinnoh-donor-map-pilot.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)

REVISION = "38228bb574a3557345852b758d5f1a65eb01bb22"
PENDING = "MAPSEC_PENDING_OWNER"
MAPS = {  # name: (width, height, git blob of map.bin)
    "Route219": (36, 30, "f7b58ab3f50aecf461f6f62cc9994867ee68959a"),
    "Route220": (62, 30, "1dd4fc0ebfbf1ffb09931336463aa2cea4f3a1af"),
    "Route221": (96, 40, "6f6145b5e0b1eeb72f287ec5bfe3e03b37978438"),
}
SECONDARY = {
    "Route219": {542: 289, 541: 290},      # sand meeting the tree line (NORMAL, walkable): sand / right-edge sand
    "Route221": {565: 337, 566: 337},      # rock pieces in the water (NORMAL, solid): Averon's rock top
}
ROOF_ROW = ("Route221", 36, 3, [611, 612, 613, 614])   # house roof-top row inside a tree-bottom row
BUILDING = ("Route221", 79, 10, 85, 15)                # x0, y0, x1, y1 (inclusive); door (82, 15)
HOUSE = (80, 12)                                       # Dewford house (5 x 4) top-left; its door is at +2, +3
YARD = [(81, 16, 718), (83, 16, 719)]
CONNECTIONS = {
    "Route219": [("MAP_SANDGEM_TOWN", 3, "up"), ("MAP_ROUTE220", 5, "down")],
    "Route220": [("MAP_ROUTE219", -5, "up"), ("MAP_ROUTE221", -4, "right")],
    "Route221": [("MAP_ROUTE220", 4, "left")],
}
SANDGEM_TO_219 = {"map": "MAP_ROUTE219", "offset": -3, "direction": "down"}


def git_blob(raw):
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tree_bottom(x):
    return 478 if x % 2 == 0 else 479


def attributes(root, primary, secondary):
    pa = (root / f"data/tilesets/primary/{primary}/metatile_attributes.bin").read_bytes()
    sa = (root / f"data/tilesets/secondary/{secondary}/metatile_attributes.bin").read_bytes()
    pa += b"\0" * (1024 - len(pa))
    return struct.unpack("<%dH" % ((len(pa) + len(sa)) // 2), pa + sa)


def dewford_house(engine):
    """Dewford's 5 x 4 house (DewfordTown rows 0-3, x 1-5), door 549 at (+2, +3)."""
    raw = (engine / "data/layouts/DewfordTown/map.bin").read_bytes()
    c = struct.unpack("<%dH" % (len(raw) // 2), raw)
    rows = [[c[y * 20 + x] for x in range(1, 6)] for y in range(4)]
    assert rows[3][2] & 1023 == 549, rows
    return rows, sha(raw)


def convert(donor, engine, name):
    header, layout, raw, blocks = pilot.read_donor_map(donor, name)
    w, h, blob = MAPS[name]
    assert git_blob(raw) == blob and (layout["width"], layout["height"]) == (w, h), name
    donor_attr = attributes(pathlib.Path(donor), "general", "petalburg")
    averon_attr = attributes(engine, "general", "dewford")
    cells, owned = list(blocks), set()
    for i, c in enumerate(blocks):
        mid = c & 1023
        if mid < 512:
            assert donor_attr[mid] == averon_attr[mid], (name, mid)
    if name == ROOF_ROW[0]:
        _, x0, y, ids = ROOF_ROW
        for i, mid in enumerate(ids):
            assert cells[y * w + x0 + i] & 1023 == mid
            cells[y * w + x0 + i] = (cells[y * w + x0 + i] & 0xFC00) | tree_bottom(x0 + i)
            owned.add((x0 + i, y))
    if name == BUILDING[0]:
        _, x0, y0, x1, y1 = BUILDING
        plateau = cells[9 * w + 79]
        assert plateau & 1023 == 2 and plateau & 0xC00, hex(plateau)
        grass = (plateau & ~1023) | 1
        assert cells[15 * w + 82] & 1023 == 461
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                assert cells[y * w + x] & 0xC00, (x, y)          # the whole footprint was solid
                cells[y * w + x] = grass
                owned.add((x, y))
        house, _ = dewford_house(engine)
        hx, hy = HOUSE
        for j, row in enumerate(house):
            for i, c in enumerate(row):
                cells[(hy + j) * w + hx + i] = c
        assert (hx + 2, hy + 3) == (82, 15)
        for x, y, mid in YARD:
            assert cells[y * w + x] & 1023 == mid and not cells[y * w + x] & 0xC00
            cells[y * w + x] = (cells[y * w + x] & 0xFC00) | 1
            owned.add((x, y))
    for i, c in enumerate(cells):
        mid = c & 1023
        if mid >= 512 and (i % w, i // w) not in owned:
            new = SECONDARY[name][mid]
            assert donor_attr[mid] & 0xFF == averon_attr[new] & 0xFF, (name, mid, new)
            cells[i] = (c & 0xFC00) | new
    for i, (a, b) in enumerate(zip(blocks, cells)):
        if (i % w, i // w) not in owned:
            assert (a ^ b) & 0xFC00 == 0, (name, i)
    data = struct.pack("<%dH" % len(cells), *cells)
    border = pilot._inside(pathlib.Path(donor), layout["border_filepath"]).read_bytes()
    border_cells = struct.unpack("<%dH" % (len(border) // 2), border)
    assert all(c & 1023 < 512 for c in border_cells)
    return data, border, {"donor": pilot.DONOR_URL, "revision": REVISION, "map": name, "git_blob": blob,
                          "source_sha256": sha(raw), "output_sha256": sha(data), "border_sha256": sha(border),
                          "changed_cells": sum(a != b for a, b in zip(blocks, cells)),
                          "excluded_donor_objects": len(header.get("object_events", [])),
                          "excluded_donor_warps": [(e["x"], e["y"], e["dest_map"]) for e in header["warp_events"]]}


def headers(name, section=PENDING):
    info = {
        "id": "MAP_" + name.upper(), "name": name, "layout": "LAYOUT_" + name.upper(), "music": "MUS_ROUTE101",
        "region": "REGION_SINNOH", "region_map_section": section, "weather": "WEATHER_SUNNY",
        "map_type": "MAP_TYPE_ROUTE", "allow_cycling": True, "allow_escaping": False, "allow_running": True,
        "show_map_name": True, "requires_flash": False, "battle_scene": "MAP_BATTLE_SCENE_NORMAL",
        "connections": [{"map": m, "offset": o, "direction": d} for m, o, d in CONNECTIONS[name]],
        "object_events": [], "warp_events": [], "coord_events": [], "bg_events": []}
    return json.dumps(info, indent=2) + "\n", f"{name}_MapScripts::\n\t.byte 0\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--donor-root", type=pathlib.Path, required=True)
    parser.add_argument("--engine", type=pathlib.Path, default=HERE.parents[3] / "engine")
    parser.add_argument("--out", type=pathlib.Path, required=True)
    args = parser.parse_args()
    if "engine" in args.out.resolve().parts:
        raise SystemExit("--out must be outside engine/")
    receipts = {}
    for name in MAPS:
        data, border, receipt = convert(args.donor_root, args.engine, name)
        d = args.out / "staged" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "map.bin").write_bytes(data)
        (d / "border.bin").write_bytes(border)
        info, text = headers(name)
        (d / "map.json").write_text(info)
        (d / "scripts.inc").write_text(text)
        sys.path.insert(0, str(HERE.parent / "iron-island"))
        import render
        bank = render.Bank(args.engine / "data/tilesets/primary/general", args.engine / "data/tilesets/secondary/dewford")
        render.render_cells(bank, list(struct.unpack("<%dH" % (len(data) // 2), data)), MAPS[name][0], d / "preview.png")
        receipts[name] = receipt
    receipts["sandgem_connection_proposal"] = SANDGEM_TO_219
    (args.out / "receipt.json").write_text(json.dumps(receipts, indent=2) + "\n")
    print(json.dumps(receipts, indent=2))


if __name__ == "__main__":
    main()
