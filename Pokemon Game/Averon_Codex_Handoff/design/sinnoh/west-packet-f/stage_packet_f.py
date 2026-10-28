#!/usr/bin/env python3
"""Packet F corridor stage (C52): Hearthome -> Route 212 -> Pastoria -> Great Marsh, on packet E. OFF-ENGINE.

Adds 20 maps to packet E's 37 (../west-packet-e/stage_packet_e.py):
  Route212_Access, Route212_North (+ W17 mansion 1F/2F), Route212_South (+ house), PastoriaCity (+ stock Center and
  houses 2-8), GreatMarsh_Gate and the four Great Marsh areas.
Sources are read only. Three files are derived, each with an asserted, minimal change:
  - HearthomeCity map.json: W11's header (packet E order, warps 0-14) with central-joins' two Route 212 Access door
    warps APPENDED at 15-16, so no packet E return index moves;
  - HearthomeCity map.bin: W11's map with exactly those two door cells reopened the way central-joins does
    (collision bits cleared; asserted equal to central-joins' reopened words);
  - Route212_Access map.json: central-joins' header with its Hearthome return moved from 2 to 15.
Route 212 South uses Codex's route212-foot-crossing map (one cell, receipt-checked against eastern-loop's source).
Pastoria's Route 213 exits lead to packet G and are declared in EXTERNAL.

  stage_packet_f.py --check | --pin | --out DIR    (DIR: static_scene batch for hearthome-solaceon+eastern-loop)
"""
import argparse
import importlib.util
import json
import pathlib
import shutil
import struct
import sys

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
spec = importlib.util.spec_from_file_location("packet_e_stage", SINNOH / "west-packet-e/stage_packet_e.py")
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
PINS = HERE / "source-pins.json"
FAMILY = "eastern-loop"          # Codex: Route 212 Access/North/South and Pastoria, the second DEV family
OUTDOORS = ["Route212_Access", "Route212_North", "Route212_South", "PastoriaCity"]
OVERLAYS = {"Route212_North": "route212-mansion", "Route212_South": "city-shells", "PastoriaCity": "great-marsh"}
JOINS = "central-joins"          # Hearthome <-> Route 212 Access door pair (reconciled below)
CROSSING = "route212-foot-crossing"
INTERIORS = {
    "Route212_North_Mansion_1F": "route212-mansion", "Route212_North_Mansion_2F": "route212-mansion",
    "Route212_South_House1": "city-shells",
    "PastoriaCity_PokemonCenter_1F": "great-marsh",
    **{f"PastoriaCity_House{n}": "great-marsh" for n in range(2, 9)},
    "GreatMarsh_Gate": "great-marsh",
    **{m: "great-marsh-areas" for m in ("GreatMarsh", "GreatMarsh_North", "GreatMarsh_NorthWest", "GreatMarsh_West")},
}
MAPS = e.MAPS + OUTDOORS + list(INTERIORS)
DOORS = [(8, 46), (9, 46)]       # Hearthome's Route 212 Access doors
HEARTHOME_WIDTH = 58
EXTERNAL = {
    "PastoriaCity warp 0: leaves the packet (MAP_ROUTE213_ACCESS)",
    "PastoriaCity: connection leaves the packet (MAP_ROUTE213)",
}
W11 = "amity-square/staged/HearthomeCity-dev-overlay"
CJ_HEARTHOME = f"{JOINS}/staged/HearthomeCity-dev-overlay"
CJ_ACCESS = f"{JOINS}/staged/Route212_Access-dev-overlay"
encode = lambda x: (json.dumps(x, indent=2) + "\n").encode()
words = lambda b: list(struct.unpack("<%dH" % (len(b) // 2), b))


def source_dirs():
    dirs = e.source_dirs()
    dirs += [f"{FAMILY}/staged/{m}" for m in OUTDOORS]
    dirs += [f"{fam}/staged/{m}-dev-overlay" for m, fam in OVERLAYS.items()]
    dirs += [f"{fam}/staged/{m}" for m, fam in INTERIORS.items()]
    return dirs + [CJ_HEARTHOME, CJ_ACCESS]


def read_sources():
    files = {}
    for d in source_dirs():
        root = SINNOH / d
        if not root.is_dir():
            raise ValueError("missing staged source: " + d)
        for p in sorted(root.iterdir()):
            if p.is_file():
                files[f"{d}/{p.name}"] = p.read_bytes()
    for name in ("receipt.json", "route212-south-map.bin"):
        files[f"{CROSSING}/{name}"] = (SINNOH / CROSSING / name).read_bytes()
    return files


def derive(files):
    """The three reconciled files and Route 212 South's crossing map; raises if any source assumption changed."""
    w11 = json.loads(files[f"{W11}/map.json"])
    cj = json.loads(files[f"{CJ_HEARTHOME}/map.json"])
    if len(w11["warp_events"]) != 15 or any(w["dest_map"] == "MAP_ROUTE212_ACCESS" for w in w11["warp_events"]):
        raise ValueError("W11 Hearthome order changed")
    doors = [w for w in cj["warp_events"] if w["dest_map"] == "MAP_ROUTE212_ACCESS"]
    if [(w["x"], w["y"], w["dest_warp_id"]) for w in doors] != [(x, y, "1") for x, y in DOORS]:
        raise ValueError("central-joins Hearthome doors changed")
    w11["warp_events"] = w11["warp_events"] + doors
    blocks, opened = words(files[f"{W11}/map.bin"]), words(files[f"{CJ_HEARTHOME}/map.bin"])
    for x, y in DOORS:
        i = y * HEARTHOME_WIDTH + x
        if not blocks[i] & 0xC00 or blocks[i] & ~0xC00 != opened[i]:
            raise ValueError(f"Hearthome door cell {(x, y)} differs from central-joins' reopening")
        blocks[i] &= ~0xC00
    access = json.loads(files[f"{CJ_ACCESS}/map.json"])
    back = access["warp_events"][1]
    if (back["dest_map"], back["dest_warp_id"]) != ("MAP_HEARTHOME_CITY", "2"):
        raise ValueError("central-joins Route 212 Access return changed")
    back["dest_warp_id"] = str(len(w11["warp_events"]) - len(doors))       # 15: the first appended door
    receipt = json.loads(files[f"{CROSSING}/receipt.json"])
    crossing = files[f"{CROSSING}/route212-south-map.bin"]
    if (receipt["before_sha256"] != e.sha(files[f"{FAMILY}/staged/Route212_South/averon-map.bin"])
            or receipt["after_sha256"] != e.sha(crossing) or receipt["changed_cells"] != 1):
        raise ValueError("Route 212 South foot crossing no longer matches its source")
    return {"HearthomeCity-dev-overlay/map.json": encode(w11),
            "HearthomeCity-dev-overlay/map.bin": struct.pack("<%dH" % len(blocks), *blocks),
            "Route212_Access-dev-overlay/map.json": encode(access),
            "Route212_Access-dev-overlay/map.bin": files[f"{CJ_ACCESS}/map.bin"],
            "Route212_South-dev-overlay/map.bin": crossing}


def headers(files):
    derived = derive(files)
    out = e.headers(files)
    out["HearthomeCity"] = json.loads(derived["HearthomeCity-dev-overlay/map.json"])
    out["Route212_Access"] = json.loads(derived["Route212_Access-dev-overlay/map.json"])
    for m in OUTDOORS[1:]:
        out[m] = json.loads(files[f"{OVERLAYS[m]}/staged/{m}-dev-overlay/map.json"])
    for m, fam in INTERIORS.items():
        out[m] = json.loads(files[f"{fam}/staged/{m}/map.json"])
    return out


def graph_errors(hdrs):
    errors = set(e.graph_errors(hdrs))
    return sorted(errors - EXTERNAL) + [f"declared external exit missing: {x}" for x in sorted(EXTERNAL - errors)]


def check(files=None):
    files = read_sources() if files is None else files
    pins = json.loads(PINS.read_text())["files"]
    errors = [f"pin mismatch: {p}" for p in sorted(set(pins) | set(files))
              if pins.get(p) != (e.sha(files[p]) if p in files else None)]
    try:
        return errors + graph_errors(headers(files))
    except ValueError as err:
        return errors + [str(err)]


def write_batch(files, out):
    """Packet E's batch, then packet F's overlays and maps; the derived files replace their sources."""
    e.write_batch(files, out)
    staged = pathlib.Path(out) / "staged"
    for d in [f"{fam}/staged/{m}-dev-overlay" for m, fam in OVERLAYS.items()] + \
             [f"{fam}/staged/{m}" for m, fam in INTERIORS.items()]:
        target = staged / d.split("/staged/", 1)[1]
        target.mkdir(parents=True)
        for path, raw in files.items():
            if path.rsplit("/", 1)[0] == d:
                (target / path.rsplit("/", 1)[1]).write_bytes(raw)
    (staged / "Route212_Access-dev-overlay").mkdir()
    for rel, raw in derive(files).items():
        (staged / rel).write_bytes(raw)
    with open(pathlib.Path(out) / "SOURCES.txt", "a") as f:
        f.write("".join(f"{m}-dev-overlay <- {fam}\n" for m, fam in OVERLAYS.items()))
        f.write("".join(f"{m} <- {fam}\n" for m, fam in INTERIORS.items()))
        f.write(f"HearthomeCity-dev-overlay <- derived: {W11} + {CJ_HEARTHOME} doors at 15-16\n"
                f"Route212_Access-dev-overlay <- derived: {CJ_ACCESS}, Hearthome return 15\n"
                f"Route212_South-dev-overlay/map.bin <- {CROSSING}\n")


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
        PINS.write_text(json.dumps({"maps": MAPS, "files": {p: e.sha(b) for p, b in sorted(files.items())}},
                                   indent=2) + "\n")
    errors = check(files)
    if errors:
        sys.exit("\n".join(errors))
    if args.out:
        write_batch(files, args.out)
    print(f"OK: {len(MAPS)} maps, {len(files)} pinned files, {len(EXTERNAL)} declared external exits")


if __name__ == "__main__":
    main()
