#!/usr/bin/env python3
"""Packet E connected source stage (C51): the 37 maps of PACKET_E_PLAN.md, OFF-ENGINE.

Selects, for every map, the one staged source the plan names (Codex's hearthome-solaceon outdoors and gates, Claude's
overlays and interiors), pins each file by SHA-256, and proves the combined graph is closed and reciprocal:
every warp lands on a warp that leads back, every connection has its opposite with the negated offset, and nothing
leaves the 37 maps. Source files are read only. No section, slot, registry or engine file is written here.

The Route 208 (8,19) <-> Mt. Coronet 1F South (36,20) join stays closed until packet D is real (C50).

  stage_packet_e.py --check              verify pins and the graph
  stage_packet_e.py --pin                rewrite source-pins.json from the current sources
  stage_packet_e.py --out DIR            also write a static_scene batch (DIR/staged/...) for the
                                         hearthome-solaceon DEV family
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
PINS = HERE / "source-pins.json"
BASE = "hearthome-solaceon"   # Codex: the seven outdoor maps and gates, used as the DEV family itself
# Map -> family whose staged/<map> (new map) or staged/<map>-dev-overlay (header over BASE) is used.
OUTDOORS = ["Route208", "Route208_Access", "HearthomeCity", "Route209_Access", "Route209", "SolaceonTown",
            "Route210_South"]
OVERLAYS = {"Route208": "city-shells", "HearthomeCity": "amity-square", "Route209": "lost-tower",
            "SolaceonTown": "solaceon-ruins-entrance", "Route210_South": "city-shells"}
INTERIORS = {
    "Route208_House1": "city-shells", "SolaceonTown_PokemonCenter_1F": "city-shells",
    "SolaceonTown_Mart": "city-shells", "SolaceonTown_House1": "city-shells", "Route210_South_House1": "city-shells",
    **{f"LostTower_{f}F": "lost-tower" for f in range(1, 7)},
    "SolaceonRuins_Entrance": "solaceon-ruins-entrance", "SolaceonRuins_B1F": "solaceon-ruins-entrance",
    "SolaceonRuins_A": "solaceon-depths", "SolaceonRuins_B": "solaceon-depths", "SolaceonRuins_C": "solaceon-depths",
    "SolaceonRuins_B2F_West": "solaceon-depths", "SolaceonRuins_B2F_East": "solaceon-depths",  # no tunnel warp
    "SolaceonRuins_B3F_Sanctum": "solaceon-depths",
    "AmitySquare": "amity-square",
    **{f"HearthomeCity_{n}": "amity-square" for n in ("PokemonCenter_1F", "Mart", "ContestLobby", "ContestHall",
                                                    "House3", "House4", "House6", "House7", "House8", "House9")},
}
MAPS = OUTDOORS + list(INTERIORS)
# Only coord events allowed: Lost Tower's Route 209 trigger warps (the donor draws these buildings without doors).
TRIGGERS = {"Route209": {(61, 15), (45, 16), (54, 28), (47, 38)}}
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
sha = lambda b: hashlib.sha256(b).hexdigest()


def source_dirs():
    """Every staged directory this stage reads, keyed by its path below design/sinnoh."""
    dirs = [f"{BASE}/staged/{m}" for m in OUTDOORS]
    dirs += [f"{fam}/staged/{m}-dev-overlay" for m, fam in OVERLAYS.items()]
    dirs += [f"{fam}/staged/{m}" for m, fam in INTERIORS.items()]
    return dirs


def read_sources():
    files = {}
    for d in source_dirs():
        root = SINNOH / d
        if not root.is_dir():
            raise ValueError("missing staged source: " + d)
        for p in sorted(root.iterdir()):
            if p.is_file():
                files[f"{d}/{p.name}"] = p.read_bytes()
    return files


def headers(files):
    """The effective header of each of the 37 maps: BASE, then its overlay; interiors as staged."""
    out = {}
    for m in OUTDOORS:
        out[m] = json.loads(files[f"{BASE}/staged/{m}/map.json"])
        if m in OVERLAYS:
            out[m] = json.loads(files[f"{OVERLAYS[m]}/staged/{m}-dev-overlay/map.json"])
    for m, fam in INTERIORS.items():
        out[m] = json.loads(files[f"{fam}/staged/{m}/map.json"])
    return out


def graph_errors(hdrs):
    errors = []
    ids = {}
    for m, h in hdrs.items():
        if h["id"] in ids:
            errors.append(f"{m}: duplicate id {h['id']}")
        ids[h["id"]] = m
    for m, h in hdrs.items():
        for i, w in enumerate(h["warp_events"]):
            dest = ids.get(w["dest_map"])
            if dest is None:
                errors.append(f"{m} warp {i}: leaves the packet ({w['dest_map']})")
                continue
            back = hdrs[dest]["warp_events"]
            try:
                k = int(w["dest_warp_id"])
            except (TypeError, ValueError):
                errors.append(f"{m} warp {i}: invalid destination warp index")
                continue
            if not 0 <= k < len(back) or back[k]["dest_map"] != h["id"]:
                errors.append(f"{m} warp {i}: {dest} warp {k} does not lead back")
                continue
            try:
                return_index = int(back[k]["dest_warp_id"])
            except (TypeError, ValueError):
                errors.append(f"{m} warp {i}: {dest} warp {k} has invalid return index")
                continue
            # Adjacent door tiles legitimately share one destination warp. A return to
            # the partner tile is valid; a return to another entrance is not.
            alias = (0 <= return_index < len(h["warp_events"])
                     and h["warp_events"][return_index]["dest_map"] == w["dest_map"]
                     and h["warp_events"][return_index]["dest_warp_id"] == w["dest_warp_id"]
                     and h["warp_events"][return_index]["elevation"] == w["elevation"]
                     and abs(h["warp_events"][return_index]["x"] - w["x"])
                         + abs(h["warp_events"][return_index]["y"] - w["y"]) == 1)
            # build_lost_tower.py intentionally collapses Mt. Pyre's four
            # exterior mats to Route209's single (61,15) portal, arriving at
            # 1F warp 0. Preserve exactly that source contract, not arbitrary
            # nonreciprocal entrances. check() separately verifies source pins.
            tower_exit = (
                m == "LostTower_1F" and h["id"] == "MAP_LOST_TOWER_1F"
                and h["layout"] == "LAYOUT_MT_PYRE_1F"
                and i in (1, 3) and dest == "Route209" and k == 1
                and w == dict(x=3 if i == 1 else 4, y=6, elevation=0,
                              dest_map="MAP_ROUTE209", dest_warp_id="1")
                and back[k] == dict(x=61, y=15, elevation=0,
                                    dest_map="MAP_LOST_TOWER_1F", dest_warp_id="0")
                and h["warp_events"][0] == dict(x=17, y=18, elevation=0,
                                               dest_map="MAP_ROUTE209", dest_warp_id="1"))
            if return_index != i and not alias and not tower_exit:
                errors.append(f"{m} warp {i}: {dest} warp {k} returns to wrong entrance {return_index}")
        seen_connections = set()
        for c in h.get("connections") or []:
            # A second edge to the same map in the same direction cannot be
            # matched one-to-one, including when the destination is external.
            edge = (c["map"], c["direction"])
            if edge in seen_connections:
                errors.append(f"{m}: duplicate {c['direction']} connection to {c['map']}")
            seen_connections.add(edge)
            dest = ids.get(c["map"])
            if dest is None:
                errors.append(f"{m}: connection leaves the packet ({c['map']})")
                continue
            match = [r for r in hdrs[dest].get("connections") or []
                     if r["map"] == h["id"] and r["direction"] == OPPOSITE[c["direction"]]]
            if len(match) != 1 or int(match[0]["offset"]) != -int(c["offset"]):
                errors.append(f"{m}: connection {c['direction']} to {dest} is not reciprocal")
        if h.get("object_events") or h.get("bg_events"):
            errors.append(f"{m}: has object or bg events")
        coords = {(e["x"], e["y"]) for e in h.get("coord_events") or []}
        if coords != TRIGGERS.get(m, set()):
            errors.append(f"{m}: unexpected coord events {sorted(coords)}")
    return errors


def check(files=None):
    files = read_sources() if files is None else files
    pins = json.loads(PINS.read_text())["files"]
    errors = [f"pin mismatch: {p}" for p in sorted(set(pins) | set(files))
              if pins.get(p) != (sha(files[p]) if p in files else None)]
    return errors + graph_errors(headers(files))


def write_batch(files, out):
    """static_scene batch: overlays and new maps only (the BASE family supplies the outdoors)."""
    staged = pathlib.Path(out) / "staged"
    if staged.exists():
        shutil.rmtree(staged)
    for d in source_dirs():
        if d.startswith(BASE + "/"):
            continue
        target = staged / d.split("/staged/", 1)[1]
        target.mkdir(parents=True)
        for path, raw in files.items():
            if path.rsplit("/", 1)[0] == d:
                (target / path.rsplit("/", 1)[1]).write_bytes(raw)
    (pathlib.Path(out) / "SOURCES.txt").write_text(
        "".join(f"{d.split('/staged/', 1)[1]} <- {d.split('/', 1)[0]}\n" for d in source_dirs()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--pin", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()
    files = read_sources()
    if args.pin:
        errors = graph_errors(headers(files))
        if errors:
            sys.exit("\n".join(errors))
        PINS.write_text(json.dumps({"maps": MAPS, "files": {p: sha(b) for p, b in sorted(files.items())}},
                                   indent=2) + "\n")
    errors = check(files)
    if errors:
        sys.exit("\n".join(errors))
    if args.out:
        write_batch(files, args.out)
    print(f"OK: {len(MAPS)} maps, {len(files)} pinned files, graph closed and reciprocal")


if __name__ == "__main__":
    main()

