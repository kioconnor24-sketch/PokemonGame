#!/usr/bin/env python3
"""Valley Windworks outdoor + interior (W5) from LiderMorti00's donor geometry, in Averon's own banks (OFF-ENGINE).

Source: donor @ 38228bb574a3557345852b758d5f1a65eb01bb22 through scripts/sinnoh-donor-map-pilot.py's read_donor_map,
git blobs checked. Drawn with Averon's General + Mauville (outdoor) and Building + BikeShop (interior), unmodified.

Conversion, asserted:
- primary IDs kept (attribute words identical except 3, the sign's layer type, as in the earlier corridor maps);
- donor secondary IDs whose attribute word equals Averon's at the same ID are kept (the building, fences, flowers);
- the wind turbines (donor art, IDs 848-910) become Averon's solid rock mound (137) on their solid cells and the
  surrounding ground on walkable ones: a neutral stand-in, turbine art is an owner decision; the lone water piece
  1020 becomes Averon water 368;
- interior: machine-top overhangs 760/761 (walkable) become the surrounding floor 528;
- collision/elevation bits are the donor's, cell for cell.
Connections (DEV overlay only, production Route 205 untouched): left Route 205 South (0), up Route 205 North (-9).
Excluded: objects (4 + 5), scripts, items, music, sections (MAPSEC_PENDING_OWNER).
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
sys.path.insert(0, str(HERE.parent / "iron-island"))
import render  # noqa: E402

PENDING = "MAPSEC_PENDING_OWNER"
MAPS = {"ValleyWindworks": (32, 99, "general", "mauville"), "ValleyWindoworks_Indoor": (22, 16, "building", "bike_shop")}
OUT_NAME = {"ValleyWindworks": "ValleyWindworks", "ValleyWindoworks_Indoor": "ValleyWindworks_Inside"}
TURBINE = range(848, 911)
GROUND_WALK = {"ValleyWindworks": 1, "ValleyWindoworks_Indoor": 528}
OVERRIDE = {"ValleyWindworks": {1020: 368}, "ValleyWindoworks_Indoor": {760: 528, 761: 528}}
ROCK = 137
# The donor's tree at (0-1, 86-87) faces Route 205 South's walkable grass (31, 86-87) across the seam: open it to
# grass (elevation 3, as the grass beside it) so the seam is walkable both ways (static seam-mismatch otherwise).
SEAM_OPEN = {(0, 86): 470, (1, 86): 471, (0, 87): 486, (1, 87): 487}
CONNECTIONS = [("MAP_ROUTE205_SOUTH", 0, "left"), ("MAP_ROUTE205_NORTH", -9, "up")]
OPPOSITE = {"left": "right", "up": "down"}


def sha(d):
    return hashlib.sha256(d).hexdigest()


def attributes(root, primary, secondary):
    pa = (root / f"data/tilesets/primary/{primary}/metatile_attributes.bin").read_bytes()
    sa = (root / f"data/tilesets/secondary/{secondary}/metatile_attributes.bin").read_bytes()
    pa += b"\0" * (1024 - len(pa))
    return struct.unpack("<%dH" % ((len(pa) + len(sa)) // 2), pa + sa)


def convert(donor, engine, name):
    header, layout, raw, blocks = pilot.read_donor_map(donor, name)
    w, h, pri, sec = MAPS[name]
    assert (layout["width"], layout["height"]) == (w, h)
    D, A = attributes(pathlib.Path(donor), pri, sec), attributes(engine, pri, sec)
    cells, turbines = list(blocks), 0
    for i, c in enumerate(blocks):
        mid, bits = c & 1023, c & 0xFC00
        if mid < 512:
            assert D[mid] == A[mid] or mid == 3, (name, mid)
        elif mid in OVERRIDE[name]:
            new = OVERRIDE[name][mid]
            assert (D[mid] & 0xFF) == (A[new] & 0xFF) or name == "ValleyWindoworks_Indoor", (mid, new)
            cells[i] = bits | new
        elif name == "ValleyWindworks" and mid in TURBINE:
            cells[i] = bits | (ROCK if bits & 0xC00 else GROUND_WALK[name])
            turbines += 1
        else:
            assert D[mid] == A[mid], (name, mid)
    owned = set()
    if name == "ValleyWindworks":
        for (x, y), mid in SEAM_OPEN.items():
            assert cells[y * w + x] & 1023 == mid and cells[y * w + x] & 0xC00, (x, y)
            cells[y * w + x] = (3 << 12) | 1
            owned.add(y * w + x)
    for i, (a, b) in enumerate(zip(blocks, cells)):
        assert i in owned or (a ^ b) & 0xFC00 == 0
    data = struct.pack("<%dH" % len(cells), *cells)
    border = pilot._inside(pathlib.Path(donor), layout["border_filepath"]).read_bytes()
    return data, border, {"map": name, "source_git_blob": hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest(),
                          "source_sha256": sha(raw), "output_sha256": sha(data), "turbine_cells_replaced": turbines,
                          "changed_cells": sum(a != b for a, b in zip(blocks, cells)),
                          "excluded_objects": len(header.get("object_events", []))}


def headers():
    out = OUT_NAME
    outdoor = {"id": "MAP_VALLEY_WINDWORKS", "name": "ValleyWindworks", "layout": "LAYOUT_VALLEY_WINDWORKS",
               "music": "MUS_ROUTE110", "region": "REGION_SINNOH", "region_map_section": PENDING, "weather": "WEATHER_SUNNY",
               "map_type": "MAP_TYPE_ROUTE", "allow_cycling": True, "allow_escaping": False, "allow_running": True,
               "show_map_name": True, "requires_flash": False, "battle_scene": "MAP_BATTLE_SCENE_NORMAL",
               "connections": [{"map": m, "offset": o, "direction": d} for m, o, d in CONNECTIONS],
               "object_events": [], "coord_events": [], "bg_events": [],
               "warp_events": [{"x": 21, "y": 79, "elevation": 0, "dest_map": "MAP_VALLEY_WINDWORKS_INSIDE", "dest_warp_id": "0"}]}
    inside = dict(outdoor, id="MAP_VALLEY_WINDWORKS_INSIDE", name=out["ValleyWindoworks_Indoor"],
                  layout="LAYOUT_VALLEY_WINDWORKS_INSIDE", map_type="MAP_TYPE_INDOOR", weather="WEATHER_NONE",
                  allow_cycling=False, allow_running=False, show_map_name=False, connections=[],
                  warp_events=[{"x": x, "y": 15, "elevation": 0, "dest_map": "MAP_VALLEY_WINDWORKS", "dest_warp_id": "0"}
                               for x in (10, 11)])
    return {"ValleyWindworks": outdoor, "ValleyWindoworks_Indoor": inside}


def route205_overlay(engine):
    """DEV-only reciprocal connections on the production Route 205 headers."""
    result = {}
    for (m, o, d), name in zip(CONNECTIONS, ("Route205_South", "Route205_North")):
        hdr = json.loads((engine / f"data/maps/{name}/map.json").read_text())
        assert not any(c["map"] == "MAP_VALLEY_WINDWORKS" for c in hdr["connections"])
        hdr["connections"].append({"map": "MAP_VALLEY_WINDWORKS", "offset": -o, "direction": OPPOSITE[d]})
        result[name] = hdr
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--donor-root", type=pathlib.Path, required=True)
    p.add_argument("--engine", type=pathlib.Path, default=HERE.parents[3] / "engine")
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    receipts, hdrs = {}, headers()
    for name, (w, h, pri, sec) in MAPS.items():
        data, border, receipt = convert(a.donor_root, a.engine, name)
        d = a.out / "staged" / OUT_NAME[name]
        d.mkdir(parents=True, exist_ok=True)
        (d / "map.bin").write_bytes(data)
        (d / "border.bin").write_bytes(border)
        (d / "map.json").write_text(json.dumps(hdrs[name], indent=2) + "\n")
        (d / "scripts.inc").write_text(f"{OUT_NAME[name]}_MapScripts::\n\t.byte 0\n")
        bank = render.Bank(a.engine / f"data/tilesets/primary/{pri}", a.engine / f"data/tilesets/secondary/{sec}")
        render.render_cells(bank, list(struct.unpack("<%dH" % (w * h), data)), w, d / "preview.png")
        receipts[OUT_NAME[name]] = receipt
    for name, hdr in route205_overlay(a.engine).items():
        d = a.out / "staged" / f"{name}-dev-overlay"
        d.mkdir(parents=True, exist_ok=True)
        (d / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
    (a.out / "receipt.json").write_text(json.dumps(receipts, indent=2) + "\n")
    print(json.dumps(receipts, indent=2))


if __name__ == "__main__":
    main()
