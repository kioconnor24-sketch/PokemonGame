#!/usr/bin/env python3
"""Central donor joins (W24, C41): reopen donor links between Codex's staged central and eastern families.

OFF-ENGINE staging. Codex staged each family on its own and closed every link to a map outside it ("unbuilt source
destination" / "unbuilt external edge", recorded with the original cell in each family's source-receipt.json).
These three links join families that are all staged now (donor LiderMorti00/Sinnoh-pokeemerald-expansion @ 38228bb5):
- HearthomeCity (8-9, 46) <-> Route212_Access (4, 1): the south gate's warps (hearthome-solaceon / eastern-loop);
- Route210_South up <-> Route210_North down, offset -57 (hearthome-solaceon / celestic-north);
- Route210_South right <-> Route215 left, offset 26 (hearthome-solaceon / eastern-loop);
- Route211_West (29, 8) <-> MtCoronet_1F_North_Room1 (3, 33): Mt. Coronet's west entrance (eterna-cycle /
  celestic-north), the "west211" link Codex's Coronet checkpoint leaves as a separate gate. This one joins the west
  and central networks; it only appends a warp on each side, a reversible proposal for Codex's Coronet.
A DEV overlay of each touched map appends the donor warps (indices through Codex's warp_index_translation) and
connections, and a derived map.bin reopens only cells Codex closed whose source collision was 0 and, for an edge,
that face a reopened cell at the same elevation on the other side; every other closure stays.

Codex's files are not modified. No NPCs, services, items, encounters or story. Coronet's other links (Room 2 <-> Route 216) are excluded.

  build_central_joins.py --out DIR
"""
import argparse
import hashlib
import json
import pathlib
import struct

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
FAMILY = {"HearthomeCity": "hearthome-solaceon", "Route210_South": "hearthome-solaceon",
          "Route212_Access": "eastern-loop", "Route215": "eastern-loop", "Route210_North": "celestic-north",
          "Route211_West": "eterna-cycle", "MtCoronet_1F_North_Room1": "celestic-north"}
WARPS = [("HearthomeCity", [(8, 46), (9, 46)], "Route212_Access", [(4, 1)]),
         ("Route211_West", [(29, 8)], "MtCoronet_1F_North_Room1", [(3, 33)])]
CONNECTIONS = [("Route210_South", "up", "Route210_North", -57), ("Route210_South", "right", "Route215", 26)]
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}


class Staged:
    def __init__(self, name):
        self.name, fam = name, SINNOH / FAMILY[name]
        d = fam / "staged" / name
        self.raw = {f"{FAMILY[name]}/staged/{name}/{p}": (d / p).read_bytes() for p in ("map.json", "averon-map.bin")}
        self.header = json.loads((d / "map.json").read_text())
        self.width = struct.unpack(">I", (d / "averon.png").read_bytes()[16:20])[0] // 16
        blob = (d / "averon-map.bin").read_bytes()
        self.cells = list(struct.unpack("<%dH" % (len(blob) // 2), blob))
        self.height = len(self.cells) // self.width
        receipt = json.loads((fam / "source-receipt.json").read_text())
        self.raw[f"{FAMILY[name]}/source-receipt.json"] = (fam / "source-receipt.json").read_bytes()
        self.source = receipt["source_geometry_headers"][name]
        self.translation = {int(k): v for k, v in receipt["warp_index_translation"].get(name, {}).items()}
        self.closed = {(c["x"], c["y"]): c["before"] for c in receipt["closure_changes"].get(name, [])}
        self.blocks = list(self.cells)

    def cell(self, x, y):
        return self.cells[y * self.width + x]

    def reopen(self, x, y):
        """A Codex closure whose source cell was walkable: clear exactly its collision bits."""
        assert (x, y) in self.closed and not (self.closed[(x, y)] >> 10) & 3, (self.name, x, y)
        assert self.cell(x, y) & 0xC00, (self.name, x, y)
        self.blocks[y * self.width + x] = self.cell(x, y) & ~0xC00


def edge(m, direction):
    return {"up": [(x, 0) for x in range(m.width)], "down": [(x, m.height - 1) for x in range(m.width)],
            "left": [(0, y) for y in range(m.height)], "right": [(m.width - 1, y) for y in range(m.height)]}[direction]


def build():
    maps = {n: Staged(n) for n in FAMILY}
    for a, a_cells, b, b_cells in WARPS:
        ma, mb = maps[a], maps[b]
        for m, xy in [(ma, c) for c in a_cells] + [(mb, c) for c in b_cells]:
            assert all((w["x"], w["y"]) != xy for w in m.header["warp_events"]), (m.name, xy)
        # appended warps get the next indices on each side; donor indices map through Codex's translation
        for m, cells in ((ma, a_cells), (mb, b_cells)):
            for xy in cells:
                src = next(i for i, w in enumerate(m.source["warp_events"]) if (w["x"], w["y"]) == xy)
                m.translation[src] = len(m.header["warp_events"])
                m.header["warp_events"].append({"x": xy[0], "y": xy[1], "elevation": 0, "dest_map": None,
                                                "dest_warp_id": None})
                m.reopen(*xy)
        for m in (ma, mb):
            for src, new in m.translation.items():
                w, sw = m.header["warp_events"][new], m.source["warp_events"][src]
                if w["dest_map"] is None:
                    other = maps[a if m is mb else b]
                    assert sw["dest_map"] == other.header["id"], (m.name, sw)
                    w["dest_map"], w["dest_warp_id"] = sw["dest_map"], str(other.translation[int(sw["dest_warp_id"])])
    for a, direction, b, offset in CONNECTIONS:
        ma, mb = maps[a], maps[b]
        assert {"map": mb.header["id"], "offset": offset, "direction": direction} in ma.source["connections"]
        assert {"map": ma.header["id"], "offset": -offset, "direction": OPPOSITE[direction]} in mb.source["connections"]
        for x, y in edge(ma, direction):
            bx, by = (x - offset, mb.height - 1 if direction == "up" else 0) if direction in ("up", "down") \
                else (mb.width - 1 if direction == "left" else 0, y - offset)
            if not (0 <= bx < mb.width and 0 <= by < mb.height):
                continue
            if (x, y) in ma.closed and (bx, by) in mb.closed and not (ma.closed[(x, y)] >> 10) & 3 \
                    and not (mb.closed[(bx, by)] >> 10) & 3 and ma.cell(x, y) >> 12 == mb.cell(bx, by) >> 12:
                ma.reopen(x, y)
                mb.reopen(bx, by)
        ma.header["connections"] = (ma.header["connections"] or []) + [
            {"map": mb.header["id"], "offset": offset, "direction": direction}]
        mb.header["connections"] = (mb.header["connections"] or []) + [
            {"map": ma.header["id"], "offset": -offset, "direction": OPPOSITE[direction]}]
    return maps


def check(maps):
    """Every appended warp lands on a warp leading back; every connection has its reciprocal."""
    headers = {m.header["id"]: m.header for m in maps.values()}
    for mid, h in headers.items():
        for w in h["warp_events"]:
            if w["dest_map"] in headers:
                back = headers[w["dest_map"]]["warp_events"][int(w["dest_warp_id"])]
                assert back["dest_map"] == mid, (mid, w, back)
        for c in h["connections"] or []:
            if c["map"] in headers:
                assert {"map": mid, "offset": -c["offset"], "direction": OPPOSITE[c["direction"]]} \
                    in headers[c["map"]]["connections"], (mid, c)
    return True


def write(out):
    maps = build()
    check(maps)
    st = pathlib.Path(out) / "staged"
    hashes, reopened = {}, {}
    for name, m in maps.items():
        d = st / f"{name}-dev-overlay"
        d.mkdir(parents=True, exist_ok=True)
        (d / "map.json").write_text(json.dumps(m.header, indent=2) + "\n")
        (d / "map.bin").write_bytes(struct.pack("<%dH" % len(m.blocks), *m.blocks))
        hashes.update({p: hashlib.sha256(b).hexdigest() for p, b in m.raw.items()})
        reopened[name] = [[i % m.width, i // m.width] for i, (a, b) in enumerate(zip(m.cells, m.blocks)) if a != b]
    receipt = {"status": "OFF_ENGINE_STAGING_NOT_PRODUCTION", "reopened_cells": reopened,
               "inputs_sha256": dict(sorted(hashes.items()))}
    (pathlib.Path(out) / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", type=pathlib.Path, required=True)
    a = p.parse_args()
    print(json.dumps(write(a.out)["reopened_cells"]))
