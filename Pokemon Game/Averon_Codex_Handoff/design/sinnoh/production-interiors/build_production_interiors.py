#!/usr/bin/env python3
"""Donor interiors behind production Floaroma doors (W28, C40), in neutral Averon indoor art.

OFF-ENGINE staging. Source: LiderMorti00/Sinnoh-pokeemerald-expansion @ 38228bb5. These donor rooms sit behind doors
that production Floaroma Town and Floaroma Meadow draw at the donor's own coordinates, with no warp:
  FloaromaTown_FlowerShop (22, 13), FloaromaTown_House1 (13, 16), FloaromaTown_Mart (26, 19),
  FloaromaTown_House2 (26, 28), FloaromaMeadow_House (35, 41).
(The Center (18, 28) is left to Codex's #238, which stages the donor Center.)

1. source/staged/<Room>/: the donor floor plan unchanged (map.bin; border: stock interiors' black void), its used attribute words
   (attributes.json) and a neutral header whose only warps are the donor's street mats.
2. interior-art/: Codex's merged neutral indoor packer (hearthome-solaceon/adapt_gate_art.py build()) draws every
   room from the existing Building/Shop art: floor, wall, counter, exit mat; collision/elevation/behaviour preserved.
3. staged/<Room>/: the DEV map (adapted map.bin, a wall border, layout.json on this batch's own tileset pair) and
   tilesets.json declaring that pair for the DEV scene; FloaromaTown/FloaromaMeadow-dev-overlay: the production
   headers plus one warp per door (donor street mats return to the same door).
No objects, services, items or story (MAPSEC_PENDING_OWNER). Production and Codex files are not modified.

  build_production_interiors.py --donor-root DONOR --engine ENGINE --out DIR
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import shutil
import struct
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pilot = load("pilot", HERE.parents[3] / "scripts/sinnoh-donor-map-pilot.py")
w1 = load("w1", SINNOH / "iron-island/build_iron_island.py")
packer = load("indoor_packer", SINNOH / "hearthome-solaceon/adapt_gate_art.py")
# room -> (production town, door)
ROOMS = {"FloaromaTown_FlowerShop": ("FloaromaTown", (22, 13)), "FloaromaTown_House1": ("FloaromaTown", (13, 16)),
         "FloaromaTown_Mart": ("FloaromaTown", (26, 19)), "FloaromaTown_House2": ("FloaromaTown", (26, 28)),
         "FloaromaMeadow_House": ("FloaromaMeadow", (35, 41))}
BLOBS = {}                                              # filled from the donor tree and recorded in the receipt
BORDER = struct.pack("<4H", *[1] * 4)          # stock interiors' black void: Building metatile 1, kept as-is in the packed primary
TILESETS = [{"symbol": "ClaudeProdInteriorPrimary", "secondary": False, "graphics": "Building",
             "metatiles": "interior-art/primary-metatiles.bin", "attributes": "interior-art/primary-attributes.bin"},
            {"symbol": "ClaudeProdInteriorSecondary", "secondary": True, "graphics": "Shop",
             "metatiles": "interior-art/secondary-metatiles.bin", "attributes": "interior-art/secondary-attributes.bin"}]


def const(name, prefix="MAP_"):
    """MAP_ constant of a map name (FloaromaTown_FlowerShop -> MAP_FLOAROMA_TOWN_FLOWER_SHOP)."""
    return prefix + re.sub(r"(?<=[a-z0-9])(?=[A-Z])", "_", name).upper()


def pre_integration(engine, rel):
    """A production file as it was before west packet B integrated these rooms (its pinned base/ copy)."""
    base = SINNOH / "west-packet-b/base" / rel
    return base.read_bytes() if base.exists() else (pathlib.Path(engine) / rel).read_bytes()


def git_blob(raw):
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def tileset_dir(name):
    return re.sub(r"(?<=[a-z])(?=[A-Z])", "_", name.replace("gTileset_", "")).lower()


def stage_sources(donor, out):
    """Donor floor plans with neutral headers (street mats only) and their used attribute words."""
    donor = pathlib.Path(donor)
    dims, anchors = {}, {}
    for room in ROOMS:
        header, layout, raw, blocks = pilot.read_donor_map(donor, room)
        BLOBS[room] = git_blob(raw)
        town = header["warp_events"][0]["dest_map"]
        mats = [w for w in header["warp_events"] if w["dest_map"] == town]
        assert len(mats) == len(header["warp_events"]) == 2, (room, header["warp_events"])
        words = {}
        for kind, name in (("primary", layout["primary_tileset"]), ("secondary", layout["secondary_tileset"])):
            raw_attrs = (donor / f"data/tilesets/{kind}/{tileset_dir(name)}/metatile_attributes.bin").read_bytes()
            attrs = struct.unpack("<%dH" % (len(raw_attrs) // 2), raw_attrs)
            for c in blocks:
                mid = c & 1023
                if (mid >= 512) == (kind == "secondary"):
                    words[str(mid)] = attrs[mid % 512]
        d = out / "staged" / room
        d.mkdir(parents=True)
        (d / "map.bin").write_bytes(raw)
        (d / "border.bin").write_bytes(BORDER)          # donor border tiles are not in the packer's banks
        (d / "attributes.json").write_text(json.dumps({"used_source_attribute_words": words}, indent=2) + "\n")
        neutral = w1.header(const(room), room, layout["id"], "MUS_PETALBURG", "MAP_TYPE_INDOOR",
                            [(w["x"], w["y"], "MAP_PLACEHOLDER", 0) for w in mats])
        (d / "map.json").write_text(json.dumps(neutral, indent=2) + "\n")
        dims[room] = (layout["width"], layout["height"])
        anchors[room] = [(w["x"], w["y"]) for w in mats]
    return dims, anchors


def build(donor, engine, out):
    out = pathlib.Path(out)
    engine = pathlib.Path(engine).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        source = pathlib.Path(tmp) / "source"
        dims, anchors = stage_sources(donor, source)
        art = pathlib.Path(tmp) / "art"
        receipt = packer.build(engine, art, source_root=source, maps=dims, expected_anchors=anchors)
        shutil.copytree(source, out / "source")
        (out / "interior-art").mkdir(parents=True, exist_ok=True)
        for p in sorted(art.iterdir()):
            if p.suffix == ".bin" and p.stem not in ROOMS:
                shutil.copy(p, out / "interior-art" / p.name)
        adapted = {room: (art / f"{room}.bin").read_bytes() for room in ROOMS}
    towns = {t: json.loads(pre_integration(engine, f"data/maps/{t}/map.json")) for t, _ in ROOMS.values()}
    music = {t: h["music"] for t, h in towns.items()}
    for room, (town, door) in ROOMS.items():
        hdr = towns[town]
        assert all((w["x"], w["y"]) != door for w in hdr["warp_events"]), (town, door)
        index = len(hdr["warp_events"])
        hdr["warp_events"].append({"x": door[0], "y": door[1], "elevation": 0, "dest_map": const(room),
                                   "dest_warp_id": "0"})
        w, h = dims[room]
        cells = struct.unpack("<%dH" % (w * h), adapted[room])
        d = out / "staged" / room
        d.mkdir(parents=True, exist_ok=True)
        hdr_room = w1.header(const(room), room, const(room, "LAYOUT_CLAUDE_"), music[town],
                             "MAP_TYPE_INDOOR", [(x, y, towns[town]["id"], index) for x, y in anchors[room]])
        (d / "map.json").write_text(json.dumps(hdr_room, indent=2) + "\n")
        (d / "scripts.inc").write_text(w1.scripts(room))
        (d / "map.bin").write_bytes(adapted[room])
        (d / "border.bin").write_bytes(BORDER)
        (d / "layout.json").write_text(json.dumps({"width": w, "height": h,
                                                   "primary_tileset": "gTileset_" + TILESETS[0]["symbol"],
                                                   "secondary_tileset": "gTileset_" + TILESETS[1]["symbol"]},
                                                  indent=2) + "\n")
    for town, hdr in towns.items():
        d = out / "staged" / f"{town}-dev-overlay"
        d.mkdir(parents=True, exist_ok=True)
        (d / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
    (out / "staged" / "tilesets.json").write_text(json.dumps(TILESETS, indent=2) + "\n")
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "donor_revision": "38228bb574a3557345852b758d5f1a65eb01bb22",
               "donor_map_blobs": dict(sorted(BLOBS.items())), "packer": "hearthome-solaceon/adapt_gate_art.py build()",
               "packer_secondary_records": receipt["secondary_records"],
               "packer_verified_cells": receipt["verified_physics_behavior_cells"]}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--donor-root", type=pathlib.Path, required=True)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(json.dumps(build(a.donor_root, a.engine, a.out), indent=2))
