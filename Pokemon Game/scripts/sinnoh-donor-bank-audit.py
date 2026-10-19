#!/usr/bin/env python3
"""Read-only, conservative donor vs Averon map metatile bank feasibility report.

Raw metatile record similarity is NOT proof the visible tiles match; pixel, palette,
behavior callbacks and animations need separate verification before conversion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

METATILE_BYTES = 16
ATTR_BYTES = 2
BANK_START = (0, 512)
BANK_NAMES = ("primary/general", "secondary/petalburg")


def bank_data(root, group):
    base = Path(root) / "data/tilesets" / group
    blocks = (base / "metatiles.bin").read_bytes()
    attributes = (base / "metatile_attributes.bin").read_bytes()
    graphics = (base / "tiles.png").read_bytes()
    if len(blocks) % METATILE_BYTES or len(attributes) % ATTR_BYTES:
        raise ValueError("invalid metatile bank length in " + str(base))
    count = len(blocks) // METATILE_BYTES
    if len(attributes) // ATTR_BYTES != count:
        raise ValueError("metatile records and behavior attributes count differ in " + str(base))
    data = [
        (blocks[i * METATILE_BYTES:(i + 1) * METATILE_BYTES],
         attributes[i * ATTR_BYTES:(i + 1) * ATTR_BYTES])
        for i in range(count)
    ]
    return data, hashlib.sha256(graphics).hexdigest()


def audit(donor_root, engine_root, donor_map):
    source_path = Path(donor_root) / "data/layouts" / donor_map / "map.bin"
    layout_table = json.loads((Path(donor_root) / "data/layouts/layouts.json").read_text())
    layout = next((x for x in layout_table["layouts"] if x["id"] == "LAYOUT_" + donor_map.upper()), None)
    if layout is None:
        raise ValueError("missing donor layout")
    if [layout["primary_tileset"], layout["secondary_tileset"]] != [
        "gTileset_General", "gTileset_Petalburg"
    ]:
        raise ValueError("source map requires a different bank family")
    raw = source_path.read_bytes()
    if len(raw) != 2 * layout["width"] * layout["height"]:
        raise ValueError("donor source block does not match dimensions")
    cells = struct.unpack("<" + str(len(raw) // 2) + "H", raw)
    src_tiles = sorted({c & 1023 for c in cells})
    by_bank = []
    for bank, group in enumerate(BANK_NAMES):
        donor_records, donor_png = bank_data(donor_root, group)
        target_records, target_png = bank_data(engine_root, group)
        subset = [tile for tile in src_tiles if (tile >= 512) == bool(bank)]
        same_index = 0
        any_record_match = 0
        missing_target_index = 0
        unmatched_structure = []
        for absolute in subset:
            rel = absolute - BANK_START[bank]
            if rel >= len(donor_records):
                raise ValueError("source layout references absent donor metatile " + str(absolute))
            record = donor_records[rel]
            if rel >= len(target_records):
                missing_target_index += 1
            elif target_records[rel] == record:
                same_index += 1
            if record in target_records:
                any_record_match += 1
            else:
                unmatched_structure.append(absolute)
        by_bank.append({
            "family": group,
            "source_records": len(donor_records),
            "destination_records": len(target_records),
            "source_referenced": len(subset),
            "identical_index_record_and_attribute": same_index,
            "record_matches_any_destination": any_record_match,
            "out_of_destination_range": missing_target_index,
            "unmatched_structural_ids": unmatched_structure,
            "graphics_png_sha256_equal": donor_png == target_png,
            "donor_graphics_sha256": donor_png,
            "target_graphics_sha256": target_png,
        })
    return {
        "status": "READ_ONLY_STRUCTURAL_COMPARISON_NO_VISUAL_REUSE_CLEARED",
        "source_map": donor_map,
        "source_blocks_sha256": hashlib.sha256(raw).hexdigest(),
        "source_dimensions": [layout["width"], layout["height"]],
        "distinct_referenced_metatiles": len(src_tiles),
        "banks": by_bank,
        "warning": "Even a matching metatile record needs graphics, palette, animation and attribution review.",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--donor-root", type=Path, required=True)
    p.add_argument("--engine-root", type=Path, required=True)
    p.add_argument("--map", dest="map_name", choices=["Route202"], required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = audit(args.donor_root, args.engine_root, args.map_name)
    print(json.dumps(result, indent=2))
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
