#!/usr/bin/env python3
"""Route 204 + Ravaged Path from LiderMorti00's donor geometry (OFF-ENGINE staging; claim #15 6284624908).

Source: LiderMorti00/Sinnoh-pokeemerald-expansion @ 38228bb574a3557345852b758d5f1a65eb01bb22, read through
scripts/sinnoh-donor-map-pilot.py's read_donor_map (PR #176) and checked against the pinned git blobs below.
Drawn with Averon's own banks: Route 204 on gTileset_General + gTileset_Rustboro, Ravaged Path on
gTileset_General + gTileset_Cave (all 32 Ravaged Path metatiles are record- and attribute-identical to
Averon's Cave, whose tiles.png is byte-identical to the donor's).

Conversion (every change listed and asserted):
- primary metatiles keep their IDs (attribute words differ only on 3, layer type; 215; 510), except the
  two fence junctions 438 and 215, whose Averon art is blank/rock, which become the fence post below them;
- the four donor Rustboro metatiles Route 204 uses become Averon General equivalents (SECONDARY);
- collision/elevation bits are the donor's, cell for cell, except ACCESS_EDITS (one unenterable door).
Warps are engine-native (cave doors on Route 204, south arrow warps in Ravaged Path): the donor's two pairs.
Both Route 204 ends stay closed: Jubilife (south) is Codex's staged #184 and Floaroma (north) is unbuilt.
Excluded: donor trainers/NPCs/items (15 + 2 objects), scripts, music, flags and map/section IDs.

  build_route204.py --donor-root DONOR --stage DIR    off-engine only (no engine mode until IDs are approved)
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("pilot", HERE.parents[3] / "scripts/sinnoh-donor-map-pilot.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)

REVISION = "38228bb574a3557345852b758d5f1a65eb01bb22"
MAPS = {  # donor name -> (width, height, git blob, Averon secondary bank)
    "Route204": (32, 64, "fcc49242b015046580e62d6b9a400c41c8fac226", "gTileset_Rustboro"),
    "RavagedPath": (32, 45, "0940999d1e557750867fbe3e1c83131ed866849d", "gTileset_Cave"),
}
# Donor Rustboro metatile -> Averon General metatile, by the donor's own neighbouring tiles.
SECONDARY = {
    "Route204": {
        798: 320, 799: 322,   # fence bottom corners -> the fence verticals directly above them
        774: 186,             # canopy-over-shore corners -> the vertical shore above them
        704: 2,               # pond south edge -> the shore-edge tile the donor uses just left of it
        # Two primary fence junctions whose Averon art differs (438 is blank, 215 is rock): the post below.
        438: 322, 215: 320,   # used once each, at (9, 1) and (13, 0)
    },
    "RavagedPath": {},        # its Cave metatiles are identical to Averon's: kept as they are
}
# Access fix measured in mGBA: the donor's north cave door carries the collision bit, so stepping into it
# from its doorstep does nothing. Its twin door (11, 31) has no collision bit. Clear it.
ACCESS_EDITS = {"Route204": {(19, 24): (167 | (1 << 10), 167)}}


def git_blob(raw):
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def convert(donor):
    out, receipt = {}, {"donor": pilot.DONOR_URL, "revision": REVISION, "maps": {}}
    for name, (w, h, blob, secondary) in MAPS.items():
        header, layout, raw, blocks = pilot.read_donor_map(donor, name)
        assert git_blob(raw) == blob and (layout["width"], layout["height"]) == (w, h), name
        remap = SECONDARY[name]
        cells = [(c & 0xFC00) | remap.get(c & 1023, c & 1023) for c in blocks]
        for (x, y), (was, new) in ACCESS_EDITS.get(name, {}).items():
            assert cells[y * w + x] == was, (name, x, y, cells[y * w + x])
            cells[y * w + x] = new
        if name == "Route204":
            assert all(c & 1023 < 512 and c & 1023 not in (438, 215) for c in cells), "an unmapped metatile survived"
        fixed = {y * w + x for x, y in ACCESS_EDITS.get(name, {})}
        assert all((a ^ b) & 0xFC00 == 0 for i, (a, b) in enumerate(zip(blocks, cells)) if i not in fixed), "collision changed"
        data = struct.pack("<%dH" % len(cells), *cells)
        out[name] = data
        receipt["maps"][name] = {"git_blob": blob, "source_sha256": hashlib.sha256(raw).hexdigest(),
                                 "output_sha256": hashlib.sha256(data).hexdigest(), "secondary": secondary,
                                 "changed_cells": sum(a != b for a, b in zip(blocks, cells)),
                                 "warps": [(e["x"], e["y"], e["dest_map"], e["dest_warp_id"]) for e in header["warp_events"]]}
    return out, receipt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor-root", type=pathlib.Path, required=True)
    parser.add_argument("--stage", type=pathlib.Path, required=True)
    args = parser.parse_args()
    if "engine" in args.stage.resolve().parts:
        raise SystemExit("--stage must be outside engine/")
    blocks, receipt = convert(args.donor_root)
    args.stage.mkdir(parents=True, exist_ok=True)
    for name, data in blocks.items():
        (args.stage / f"{name}.bin").write_bytes(data)
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
