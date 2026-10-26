#!/usr/bin/env python3
"""Lake Valor (W26, C28): the donor's lake drawn in Codex's eastern-loop art family, joined to its Valor Lakefront.

OFF-ENGINE staging. Source: LiderMorti00/Sinnoh-pokeemerald-expansion @ 38228bb5 LakeValor (48 x 52, General +
Valor), read through scripts/sinnoh-donor-map-pilot.py and checked against the pinned git blobs below.

Art: Lake Valor shares its secondary tileset with Valor Lakefront, which Codex already converted (eastern-loop:
General + gTileset_EasternDevOutdoorSecondary). The donor -> Averon tile mapping is read from that conversion, donor
Lakefront map.bin against Codex's staged averon-map.bin, cell for cell (only consistent mappings are used). Tiles the
Lakefront never uses:
- primary IDs keep their ID; each one's attribute word is asserted equal in the donor and in Codex's family bank.
  One exception (PRIMARY): the donor's south-west water step 204 is a cliff rock in Averon's General, so it is drawn
  with 192, the left-shore water the donor already uses for the north-west steps (same pond-water attribute word).
  And the donor's canopy-over-water corner 566 (Codex's Lakefront mapping draws it as filler 516, a rock here) is
  drawn with General's 510, the top-left tree canopy over water beside the 511 the donor already uses. The donor
  calls 566 NORMAL and Averon 510 pond water; all four cells are at water level (elevation 1, collision 0) between
  water cells, the same difference Lake Verity's conversion accepted for this canopy;
- the lake's 2 x 3 entrance block (secondary 730-735; east-arrow warps at (40, 3)/(40, 4)) is drawn as Codex drew the
  Lakefront end of the same entrance: its arrow tile and its solid filler, here the family's east arrow (562).
Collision/elevation are the donor's cell for cell, except the island cave door (23, 25): no warp (story-reserved,
Azelf), so it is made solid like Lake Verity's.

ValorLakefront-dev-overlay: Codex's header plus the donor's two entrance warps, and a derived copy of the blockdata
Codex's scene installs (eastern-loop/hotel-link/valor-map.bin) reopening the two cells Codex closed for them (41, 27-28;
source collision 0). No objects, encounters, story, music or sections
(MAPSEC_PENDING_OWNER; the Lakefront's music).

  build_lake_valor.py --donor-root DONOR --out DIR
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import pathlib
import re
import struct

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
REPO_SCRIPTS = HERE.parents[3] / "scripts"
spec = importlib.util.spec_from_file_location("pilot", REPO_SCRIPTS / "sinnoh-donor-map-pilot.py")
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
spec = importlib.util.spec_from_file_location("w1", SINNOH / "iron-island/build_iron_island.py")
w1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w1)
EASTERN = SINNOH / "eastern-loop"
BLOBS = {"LakeValor": "354081cbd22ac227e062438873796c550cb998a6",
         "ValorLakefront": "972daf04538e3ef85fba0c8784e943179491c890"}
BORDER_BLOB = "d198bece6c2319a6c58559f63b55ac233c96e438"
W, H = 48, 52
ENTRANCE = {730: 562, 732: 562, 731: 516, 733: 516, 734: 516, 735: 516}   # donor -> family (as on the Lakefront)
PRIMARY = {204: 192}                                    # donor SW water step -> Averon left-shore water
CANOPY = {566: 510}                                     # donor canopy over water -> General canopy over water
CAVE = (23, 25)
LAKEFRONT_DOOR = [(41, 27), (41, 28)]


def git_blob(raw):
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def unpack(raw):
    return list(struct.unpack("<%dH" % (len(raw) // 2), raw))


def attributes(path):
    raw = pathlib.Path(path).read_bytes()
    return struct.unpack("<%dH" % (len(raw) // 2), raw)


def mapping(donor):
    """Donor tile -> Averon tile, from Codex's own Valor Lakefront conversion (consistent pairs only)."""
    _, _, raw, blocks = pilot.read_donor_map(donor, "ValorLakefront")
    assert git_blob(raw) == BLOBS["ValorLakefront"]
    staged = unpack((EASTERN / "staged/ValorLakefront/averon-map.bin").read_bytes())
    seen = collections.defaultdict(set)
    for d, a in zip(blocks, staged):
        seen[d & 1023].add(a & 1023)
    return {d: a.pop() for d, a in seen.items() if len(a) == 1}


def build(donor, engine):
    donor = pathlib.Path(donor)
    header, layout, raw, blocks = pilot.read_donor_map(donor, "LakeValor")
    assert git_blob(raw) == BLOBS["LakeValor"] and (layout["width"], layout["height"]) == (W, H)
    border_raw = (donor / layout["border_filepath"]).read_bytes()
    assert git_blob(border_raw) == BORDER_BLOB
    names = re.findall(r"^\s*(MB_\w+)", (pathlib.Path(engine) / "include/constants/metatile_behaviors.h").read_text(), re.M)
    donor_primary = attributes(donor / "data/tilesets/primary/general/metatile_attributes.bin")
    family_primary = attributes(EASTERN / "outdoor-family/primary-attributes.bin")
    table = mapping(donor)

    def tile(mid):
        if mid in CANOPY:
            return CANOPY[mid]
        if mid in table:
            return table[mid]
        if mid in ENTRANCE:
            return ENTRANCE[mid]
        if mid in PRIMARY:
            assert donor_primary[mid] == family_primary[PRIMARY[mid]], mid
            return PRIMARY[mid]
        assert mid < 512 and donor_primary[mid] == family_primary[mid], mid
        return mid

    cells = [(c & 0xFC00) | tile(c & 1023) for c in blocks]
    for c in blocks:                                    # the canopy cells are water-level, unreachable on foot
        if c & 1023 in CANOPY:
            assert (c >> 10) & 3 == 0 and c >> 12 == 1, hex(c)
    x, y = CAVE
    assert names[donor_primary[blocks[y * W + x] & 1023] & 0xFF] == "MB_NON_ANIMATED_DOOR"
    cells[y * W + x] |= 1 << 10
    border = [(c & 0xFC00) | tile(c & 1023) for c in unpack(border_raw)]
    lakefront = json.loads((EASTERN / "staged/ValorLakefront/map.json").read_text())
    front_cells = unpack((EASTERN / "hotel-link/valor-map.bin").read_bytes())     # what Codex's scene installs
    closed = {(c["x"], c["y"]): c["before"] for c in json.loads((EASTERN / "source-receipt.json").read_text())
              ["closure_changes"]["ValorLakefront"]}
    n = len(lakefront["warp_events"])
    donor_front = json.loads((donor / "data/maps/ValorLakefront/map.json").read_text())["warp_events"]
    assert [(w["x"], w["y"], w["dest_map"]) for w in donor_front] == [(41, 27, "MAP_LAKE_VALOR"), (41, 28, "MAP_LAKE_VALOR")]
    for w in donor_front:                               # donor indices 0/1 become n/n+1 on Codex's Lakefront
        lakefront["warp_events"].append({"x": w["x"], "y": w["y"], "elevation": 0, "dest_map": "MAP_LAKE_VALOR",
                                         "dest_warp_id": w["dest_warp_id"]})
    for x, y in LAKEFRONT_DOOR:
        assert (x, y) in closed and not (closed[(x, y)] >> 10) & 3, (x, y)
        front_cells[y * 56 + x] &= ~0xC00
    warps = [(w["x"], w["y"], "MAP_VALOR_LAKEFRONT", n + int(w["dest_warp_id"])) for w in header["warp_events"]]
    lake = w1.header("MAP_LAKE_VALOR", "LakeValor", "LAYOUT_LAKE_VALOR", lakefront["music"], header["map_type"], warps)
    layout_info = {"width": W, "height": H, "primary_tileset": "gTileset_General",
                   "secondary_tileset": "gTileset_EasternDevOutdoorSecondary"}
    hashes = {"donor LakeValor map.bin": BLOBS["LakeValor"], "donor LakeValor border.bin": BORDER_BLOB,
              "donor ValorLakefront map.bin": BLOBS["ValorLakefront"],
              **{f"eastern-loop/{p}": hashlib.sha256((EASTERN / p).read_bytes()).hexdigest() for p in (
                  "staged/ValorLakefront/map.json", "staged/ValorLakefront/averon-map.bin", "hotel-link/valor-map.bin",
                  "source-receipt.json",
                  "outdoor-family/primary-attributes.bin")}}
    return lake, cells, border, layout_info, lakefront, front_cells, hashes


def check(lake, lakefront):
    for a, b in ((lake, lakefront), (lakefront, lake)):
        for w in a["warp_events"]:
            if w["dest_map"] == b["id"]:
                assert b["warp_events"][int(w["dest_warp_id"])]["dest_map"] == a["id"], (a["id"], w)
    return True


def write(donor, engine, out):
    lake, cells, border, layout_info, lakefront, front_cells, hashes = build(donor, engine)
    check(lake, lakefront)
    st = pathlib.Path(out) / "staged"
    d = st / "LakeValor"
    d.mkdir(parents=True, exist_ok=True)
    (d / "map.json").write_text(json.dumps(lake, indent=2) + "\n")
    (d / "scripts.inc").write_text(w1.scripts("LakeValor"))
    (d / "layout.json").write_text(json.dumps(layout_info, indent=2) + "\n")
    (d / "map.bin").write_bytes(struct.pack("<%dH" % len(cells), *cells))
    (d / "border.bin").write_bytes(struct.pack("<%dH" % len(border), *border))
    o = st / "ValorLakefront-dev-overlay"
    o.mkdir(parents=True, exist_ok=True)
    (o / "map.json").write_text(json.dumps(lakefront, indent=2) + "\n")
    (o / "map.bin").write_bytes(struct.pack("<%dH" % len(front_cells), *front_cells))
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "donor_revision": "38228bb574a3557345852b758d5f1a65eb01bb22",
               "inputs": hashes}
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--donor-root", type=pathlib.Path, required=True)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(write(a.donor_root, a.engine, a.out)["status"])
