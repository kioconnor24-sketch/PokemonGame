#!/usr/bin/env python3
"""Read-only, conservative donor vs Averon map metatile bank feasibility report.

Raw metatile record similarity is NOT proof the visible tiles match; pixel, palette,
behavior callbacks and animations need separate verification before conversion.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

_spec = importlib.util.spec_from_file_location("donor_pilot", Path(__file__).with_name("sinnoh-donor-map-pilot.py"))
_pilot = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_pilot)

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


def audit(donor_root, engine_root, donor_map, target_secondary="petalburg"):
    if donor_map not in ("Route202", "VerityLakefront", "LakeVerity") or target_secondary not in ("petalburg", "dewford"):
        raise ValueError("unsupported map or destination secondary family")
    _, layout, raw, cells = _pilot.read_donor_map(donor_root, donor_map)
    if [layout["primary_tileset"], layout["secondary_tileset"]] != [
        "gTileset_General", "gTileset_Petalburg"
    ]:
        raise ValueError("source map requires a different bank family")
    src_tiles = sorted({c & 1023 for c in cells})
    by_bank = []
    used_records = []
    for bank, group in enumerate(BANK_NAMES):
        donor_records, donor_png = bank_data(donor_root, group)
        target_group = group if bank == 0 else "secondary/" + target_secondary
        target_records, target_png = bank_data(engine_root, target_group)
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
            words = struct.unpack("<8H", record[0])
            used_records.append({
                "id": absolute, "bank": bank,
                "cells": sum((c & 1023) == absolute for c in cells),
                "attribute_u16": struct.unpack("<H", record[1])[0],
                "graphic_tile_ids": sorted({w & 1023 for w in words}),
                "palette_ids": sorted({w >> 12 for w in words}),
                "destination_index_available": rel < len(target_records),
                "same_index_record_and_attribute": rel < len(target_records) and target_records[rel] == record,
                "matching_destination_ids": [i + BANK_START[bank] for i, r in enumerate(target_records) if r == record],
            })
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
            "destination_family": target_group,
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
        "used_records": used_records,
        "primary_cells": sum((c & 1023) < 512 for c in cells),
        "secondary_cells": sum((c & 1023) >= 512 for c in cells),
        "warning": "Even a matching metatile record needs graphics, palette, animation and attribution review.",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--donor-root", type=Path, required=True)
    p.add_argument("--engine-root", type=Path, required=True)
    p.add_argument("--map", dest="map_name", choices=["Route202", "VerityLakefront", "LakeVerity"], required=True)
    p.add_argument("--target-secondary", choices=["petalburg", "dewford"], default="petalburg")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    result = audit(args.donor_root, args.engine_root, args.map_name, args.target_secondary)
    print(json.dumps(result, indent=2))
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
