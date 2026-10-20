#!/usr/bin/env python3
"""Fail-closed, OFF-ENGINE Sinnoh donor layout inspector and explicit metatile remapper.

This never copies events/scripts, assigns saved IDs, or edits pokeemerald sources.
Source and destination metatile IDs are NOT interchangeable. The conversion
output is a scratch candidate, not an accepted map or a license determination.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct

DONOR_URL = "https://github.com/LiderMorti00/Sinnoh-pokeemerald-expansion"
MAP_NAME = re.compile(r"[A-Za-z0-9_]+\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
MAX_METATILE = 1023


def _inside(root, relative):
    """Prevent donor metadata from escaping the selected checkout."""
    root = Path(root).resolve()
    result = (root / relative).resolve()
    if not result.is_relative_to(root):
        raise ValueError("donor path escapes checkout")
    return result


def read_donor_map(root, map_name):
    root = Path(root).resolve()
    if not MAP_NAME.fullmatch(map_name):
        raise ValueError("invalid donor map name")
    header = json.loads(_inside(root, "data/maps/" + map_name + "/map.json").read_text())
    layout_table = json.loads(_inside(root, "data/layouts/layouts.json").read_text())
    layouts = [l for l in layout_table["layouts"] if l["id"] == header["layout"]]
    if len(layouts) != 1:
        raise ValueError("donor layout missing or ambiguous")
    layout = layouts[0]
    width, height = layout["width"], layout["height"]
    if type(width) is not int or type(height) is not int or width < 1 or height < 1:
        raise ValueError("invalid donor dimensions")
    block_path = _inside(root, layout["blockdata_filepath"])
    raw = block_path.read_bytes()
    if len(raw) != 2 * width * height:
        raise ValueError("donor block length does not match layout dimensions")
    blocks = struct.unpack("<" + str(width * height) + "H", raw)
    if header.get("id") != "MAP_" + map_name.upper():
        # Real donor map IDs can omit a word boundary (e.g., MAP_ROUTE202).
        # The exact header and layout IDs are preserved in the receipt.
        if not isinstance(header.get("id"), str) or not header["id"].startswith("MAP_"):
            raise ValueError("invalid donor map ID")
    return header, layout, raw, blocks


def analyze(root, map_name, revision):
    if not COMMIT.fullmatch(revision):
        raise ValueError("revision must be a pinned 40-character commit SHA")
    header, layout, raw, blocks = read_donor_map(root, map_name)
    frequencies = {}
    for cell in blocks:
        tile = cell & MAX_METATILE
        frequencies[str(tile)] = frequencies.get(str(tile), 0) + 1
    return {
        "donor": DONOR_URL,
        "donor_revision": revision,
        "source_map": map_name,
        "source_map_id": header["id"],
        "source_layout_id": layout["id"],
        "block_sha256": hashlib.sha256(raw).hexdigest(),
        "dimensions": [layout["width"], layout["height"]],
        "tilesets": [layout["primary_tileset"], layout["secondary_tileset"]],
        "metatile_frequency": frequencies,
        "event_counts": {
            key: len(header.get(key, []))
            for key in ("object_events", "warp_events", "coord_events", "bg_events")
        },
        "connection_count": len(header.get("connections") or []),
        "status": "SOURCE_ANALYSIS_ONLY",
    }


def draft_manifest(analysis):
    """All mappings start unverified. Never guess source/destination equality."""
    return {
        "source_map": analysis["source_map"],
        "source_map_id": analysis["source_map_id"],
        "source_layout_id": analysis["source_layout_id"],
        "donor_revision": analysis["donor_revision"],
        "block_sha256": analysis["block_sha256"],
        "target_map_id": None,
        "target_primary_tileset": None,
        "target_secondary_tileset": None,
        "metatiles": {
            tile: {"target": None, "behavior_verified": False, "graphics_verified": False}
            for tile in sorted(analysis["metatile_frequency"], key=int)
        },
    }


def convert(root, map_name, manifest, output):
    """Stage a mapped block file outside all engine directories; no code/IDs/events."""
    header, layout, raw, blocks = read_donor_map(root, map_name)
    if manifest.get("source_map") != map_name or manifest.get("source_map_id") != header["id"]:
        raise ValueError("donor map identity mismatch")
    if manifest.get("source_layout_id") != layout["id"]:
        raise ValueError("donor layout identity mismatch")
    if not COMMIT.fullmatch(str(manifest.get("donor_revision", ""))):
        raise ValueError("unpinned donor revision")
    if manifest.get("block_sha256") != hashlib.sha256(raw).hexdigest():
        raise ValueError("donor blob hash mismatch")
    for key in ("target_map_id", "target_primary_tileset", "target_secondary_tileset"):
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            raise ValueError("missing verified destination " + key)
    if (layout["width"] + 15) * (layout["height"] + 14) > 10240:
        raise ValueError("donor layout exceeds Averon's padded field buffer")
    tiles = manifest.get("metatiles")
    if not isinstance(tiles, dict):
        raise ValueError("missing metatile mapping")

    remap = {}
    for original in sorted({cell & MAX_METATILE for cell in blocks}):
        entry = tiles.get(str(original))
        if not isinstance(entry, dict):
            raise ValueError("unmapped donor metatile " + str(original))
        new_id = entry.get("target")
        if type(new_id) is not int or not 0 <= new_id <= MAX_METATILE:
            raise ValueError("invalid destination metatile " + str(original))
        if entry.get("behavior_verified") is not True or entry.get("graphics_verified") is not True:
            raise ValueError("unverified visual/behavior mapping " + str(original))
        # Keep donor primary in target primary and donor secondary in target secondary.
        if (original < 512) != (new_id < 512):
            raise ValueError("metatile mapping crosses the primary/secondary bank")
        remap[original] = new_id

    changed = [((cell & ~MAX_METATILE) | remap[cell & MAX_METATILE]) for cell in blocks]
    for old, new in zip(blocks, changed):
        if (old & 0xFC00) != (new & 0xFC00):
            raise ValueError("collision or elevation changed")
    result = struct.pack("<" + str(len(changed)) + "H", *changed)
    output = Path(output).resolve()
    if "engine" in output.parts or output.suffix != ".bin":
        raise ValueError("output must be an off-engine scratch .bin file")
    if output.is_relative_to(Path(root).resolve()):
        raise ValueError("output must not be inside donor checkout")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(result)
    receipt = {
        "status": "STAGED_NOT_INTEGRATED_OR_PLAYTESTED",
        "donor": DONOR_URL,
        "revision": manifest["donor_revision"],
        "source_map": header["id"],
        "target_map": manifest["target_map_id"],
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "output_sha256": hashlib.sha256(result).hexdigest(),
        "mapped_unique_metatiles": len(remap),
        "dimensions": [layout["width"], layout["height"]],
        "preserved_collision_elevation": True,
        "excluded": ["events", "scripts", "connections", "warps", "flags", "map IDs", "saved sections", "assets"],
    }
    output.with_suffix(".receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inspect", "convert"))
    parser.add_argument("--donor-root", type=Path, required=True)
    parser.add_argument("--map", required=True, dest="map_name")
    parser.add_argument("--donor-revision", help="required in inspect mode")
    parser.add_argument("--template-out", type=Path)
    parser.add_argument("--mapping-json", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.mode == "inspect":
            if not args.donor_revision:
                raise ValueError("--donor-revision required for inspect")
            report = analyze(args.donor_root, args.map_name, args.donor_revision)
            if args.template_out:
                args.template_out.parent.mkdir(parents=True, exist_ok=True)
                with args.template_out.open("x") as f:
                    json.dump(draft_manifest(report), f, indent=2)
                    f.write("\n")
        else:
            if not args.mapping_json or not args.output:
                raise ValueError("--mapping-json and --output required for convert")
            report = convert(args.donor_root, args.map_name,
                             json.loads(args.mapping_json.read_text()), args.output)
        print(json.dumps(report, indent=2))
    except (KeyError, ValueError, OSError, json.JSONDecodeError) as error:
        parser.exit(2, "ERROR: " + str(error) + "\n")


if __name__ == "__main__":
    main()
