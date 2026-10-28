#!/usr/bin/env python3
"""Packet G side connection (C53): Solaceon Ruins <-> Maniac Tunnel <-> Route 214, staged on packet E. OFF-ENGINE.

Starts from packet E's 37 maps (../west-packet-e/stage_packet_e.py) and changes exactly three things:
  - SolaceonRuins_B2F_East becomes maniac-ruins-link's variant, whose third warp is the tunnel ladder (24,16);
  - ManiacTunnel and ManiacTunnel_B1F (maniac-ruins-link) are added;
  - Route 214 is added: Codex's eastern-loop map with sendoff-spring's overlay, whose warp 2 is the tunnel mouth.
Every pair is reciprocal. Route 214's other exits are listed in EXTERNAL and must exist exactly as listed: they
lead to packet G's outdoors (Veilstone, Valor Lakefront, the Route 214 gate) and Spring Path, which are not staged here.

  stage_tunnel_link.py --check | --pin | --out DIR    (DIR: static_scene batch for hearthome-solaceon+eastern-loop)
"""
import argparse
import importlib.util
import json
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
SINNOH = HERE.parent
spec = importlib.util.spec_from_file_location("packet_e_stage", SINNOH / "west-packet-e/stage_packet_e.py")
e = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e)
PINS = HERE / "source-pins.json"
TUNNEL = "maniac-ruins-link"
ADDED = {"ManiacTunnel": TUNNEL, "ManiacTunnel_B1F": TUNNEL}
SWAPPED = {"SolaceonRuins_B2F_East": TUNNEL}       # replaces solaceon-depths' two-warp variant
ROUTE = ("Route214", "eastern-loop", "sendoff-spring")   # map, base family, overlay family
MAPS = e.MAPS + list(ADDED) + [ROUTE[0]]
EXTERNAL = {
    "Route214 warp 0: leaves the packet (MAP_ROUTE214_ACCESS)",
    "Route214 warp 1: leaves the packet (MAP_ROUTE214_ACCESS)",
    "Route214: connection leaves the packet (MAP_VEILSTONE_CITY)",
    "Route214: connection leaves the packet (MAP_VALOR_LAKEFRONT)",
    "Route214: connection leaves the packet (MAP_SPRING_PATH)",
}
# DEV scene context only (not part of the packet): the maps Route 214's overlay connects to.
CONTEXT = ["SendoffSpring", "SpringPath", "TurnbackCave_1F", "TurnbackCave_B1F", "TurnbackCave_B2F"]


def source_dirs():
    dirs = [d for d in e.source_dirs() if d != "solaceon-depths/staged/SolaceonRuins_B2F_East"]
    dirs += [f"{fam}/staged/{m}" for m, fam in {**SWAPPED, **ADDED}.items()]
    dirs += [f"{ROUTE[1]}/staged/{ROUTE[0]}", f"{ROUTE[2]}/staged/{ROUTE[0]}-dev-overlay"]
    return dirs


def read_sources(dirs=None):
    files = {}
    for d in dirs or source_dirs():
        root = SINNOH / d
        if not root.is_dir():
            raise ValueError("missing staged source: " + d)
        for p in sorted(root.iterdir()):
            if p.is_file():
                files[f"{d}/{p.name}"] = p.read_bytes()
    return files


def headers(files):
    base = {k: v for k, v in files.items() if not k.startswith("solaceon-depths/staged/SolaceonRuins_B2F_East/")}
    base["solaceon-depths/staged/SolaceonRuins_B2F_East/map.json"] = \
        files[f"{TUNNEL}/staged/SolaceonRuins_B2F_East/map.json"]
    out = e.headers(base)
    for m, fam in ADDED.items():
        out[m] = json.loads(files[f"{fam}/staged/{m}/map.json"])
    out[ROUTE[0]] = json.loads(files[f"{ROUTE[2]}/staged/{ROUTE[0]}-dev-overlay/map.json"])
    return out


def graph_errors(hdrs):
    errors = set(e.graph_errors(hdrs))
    missing = EXTERNAL - errors
    return sorted(errors - EXTERNAL) + [f"declared external exit missing: {x}" for x in sorted(missing)]


def check(files=None):
    files = read_sources() if files is None else files
    pins = json.loads(PINS.read_text())["files"]
    errors = [f"pin mismatch: {p}" for p in sorted(set(pins) | set(files))
              if pins.get(p) != (e.sha(files[p]) if p in files else None)]
    return errors + graph_errors(headers(files))


def write_batch(files, out):
    """Packet E's batch with the swapped B2F East, the tunnel, Route 214's overlay and the Spring Path context."""
    context = [f"sendoff-spring/staged/{m}" for m in CONTEXT]
    everything = {**files, **read_sources(context)}
    staged = pathlib.Path(out) / "staged"
    if staged.exists():
        shutil.rmtree(staged)
    # The two base families supply the outdoors; everything else is an overlay or a new map.
    keep = [d for d in source_dirs() + context if not d.startswith(e.BASE + "/") and not d.startswith(ROUTE[1] + "/")]
    for d in keep:
        target = staged / d.split("/staged/", 1)[1]
        target.mkdir(parents=True)
        for path, raw in everything.items():
            if path.rsplit("/", 1)[0] == d:
                (target / path.rsplit("/", 1)[1]).write_bytes(raw)
    (pathlib.Path(out) / "SOURCES.txt").write_text(
        "".join(f"{d.split('/staged/', 1)[1]} <- {d.split('/', 1)[0]}\n" for d in keep))


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
