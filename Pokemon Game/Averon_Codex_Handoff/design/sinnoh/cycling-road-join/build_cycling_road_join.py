#!/usr/bin/env python3
"""Cycling Road <-> Route 207 seam (W25, C17): the donor's Route 206 / Route 207 link between two Codex families.

OFF-ENGINE staging. The donor (LiderMorti00/Sinnoh-pokeemerald-expansion @ 38228bb5) joins Route206 down to Route207
up at offset -2 (Route207 up -> Route206 at +2). Codex staged the two in different families and closed both ends:
- eterna-cycle Route206 (11-19, 119): "unbuilt external edge" (source-receipt closure_changes, source collision 0);
- oreburgh Route207 (13-21, 0): "unbuilt north edge" (oreburgh-donor/stage_corridor.py); source collision 0 per
  oreburgh-donor/corridor/Route207/source.bin.
DEV overlays add the reciprocal connections, and derived map.bin copies reopen exactly those cells (elevation 3 on
both sides; only the collision bits change). Route207's base is the blockdata Codex's oreburgh-connected recipe
installs: city-family/Route207/map.bin with the recipe's seam_closure applied, checked against the recipe's hash.

Codex's files are not modified. No NPCs, items, encounters or story.

  build_cycling_road_join.py --out DIR
"""
import argparse
import hashlib
import json
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
OFFSET = -2                                             # Route206 down -> Route207; Route207 up -> Route206 at +2
R206 = SINNOH / "eterna-cycle"
R207 = SINNOH / "oreburgh-donor"
RECIPE = SINNOH / "oreburgh-connected/current-recipe.json"


def unpack(blob):
    return list(struct.unpack("<%dH" % (len(blob) // 2), blob))


def inputs():
    raw = {"eterna-cycle/staged/Route206/map.json": (R206 / "staged/Route206/map.json").read_bytes(),
           "eterna-cycle/staged/Route206/averon-map.bin": (R206 / "staged/Route206/averon-map.bin").read_bytes(),
           "eterna-cycle/source-receipt.json": (R206 / "source-receipt.json").read_bytes(),
           "oreburgh-donor/city-family/Route207/map.bin": (R207 / "city-family/Route207/map.bin").read_bytes(),
           "oreburgh-donor/corridor/Route207/source.bin": (R207 / "corridor/Route207/source.bin").read_bytes(),
           "oreburgh-connected/current-recipe.json": RECIPE.read_bytes()}
    return raw, {p: hashlib.sha256(b).hexdigest() for p, b in sorted(raw.items())}


def build():
    raw, hashes = inputs()
    recipe = json.loads(raw["oreburgh-connected/current-recipe.json"])
    r206 = json.loads(raw["eterna-cycle/staged/Route206/map.json"])
    r207 = json.loads(json.dumps(recipe["source_headers"]["Route207"]))
    c206 = unpack(raw["eterna-cycle/staged/Route206/averon-map.bin"])
    w206 = len(c206) // 120
    assert w206 * 120 == len(c206)
    c207 = unpack(raw["oreburgh-donor/city-family/Route207/map.bin"])
    w207 = recipe["maps"]["Route207"][0]
    seam = recipe["seam_closure"]                       # the recipe's one extra closure on Route207
    assert seam["map"] == "Route207" and c207[seam["y"] * w207 + seam["x"]] == seam["before"]
    c207[seam["y"] * w207 + seam["x"]] = seam["after"]
    installed = struct.pack("<%dH" % len(c207), *c207)
    assert hashlib.sha256(installed).hexdigest() == recipe["files"]["data/layouts/Route207/map.bin"]
    source207 = unpack(raw["oreburgh-donor/corridor/Route207/source.bin"])
    closed206 = {(c["x"], c["y"]): c["before"] for c in
                 json.loads(raw["eterna-cycle/source-receipt.json"])["closure_changes"]["Route206"]}
    pairs = []
    for x in range(w206):
        bx = x - OFFSET
        if (x, 119) not in closed206 or not 0 <= bx < w207:
            continue
        a, b = c206[119 * w206 + x], c207[bx]
        if (closed206[(x, 119)] >> 10) & 3 or (source207[bx] >> 10) & 3 or not a & 0xC00 or not b & 0xC00:
            continue
        assert a >> 12 == b >> 12 == source207[bx] >> 12 == closed206[(x, 119)] >> 12, (x, bx)
        assert (b ^ source207[bx]) & ~0xC00 == 0, bx    # Codex only closed it
        pairs.append(((x, 119), (bx, 0)))
    blocks206, blocks207 = list(c206), list(c207)
    for (x, y), (bx, by) in pairs:
        blocks206[y * w206 + x] &= ~0xC00
        blocks207[by * w207 + bx] &= ~0xC00
    assert all(c["map"] != "MAP_ROUTE207" for c in r206["connections"])
    assert all(c["map"] != "MAP_ROUTE206" for c in r207["connections"])
    r206["connections"] = r206["connections"] + [{"map": "MAP_ROUTE207", "offset": OFFSET, "direction": "down"}]
    r207["connections"] = r207["connections"] + [{"map": "MAP_ROUTE206", "offset": -OFFSET, "direction": "up"}]
    return r206, r207, blocks206, blocks207, pairs, hashes


def write(out):
    r206, r207, b206, b207, pairs, hashes = build()
    st = pathlib.Path(out) / "staged"
    for name, hdr, blocks in (("Route206", r206, b206), ("Route207", r207, b207)):
        d = st / f"{name}-dev-overlay"
        d.mkdir(parents=True, exist_ok=True)
        (d / "map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (d / "map.bin").write_bytes(struct.pack("<%dH" % len(blocks), *blocks))
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "reopened_pairs": pairs, "inputs_sha256": hashes}
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(json.dumps(write(a.out)["reopened_pairs"]))
