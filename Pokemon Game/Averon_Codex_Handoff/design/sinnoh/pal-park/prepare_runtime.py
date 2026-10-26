#!/usr/bin/env python3
"""DEV-only install of W6 on top of W2's scene: Routes 219-221 (slots 19-21) + PalPark (22) + PalPark_Gate (23).

Reuses ../southwest-coast/prepare_runtime.py's assemble() unchanged, then swaps in the Route 221 header with its one
appended gate warp and appends the park and the gate (stock LAYOUT_ROUTE110_SEASIDE_CYCLING_ROAD_ENTRANCE). Stand-in
section MAPSEC_ROUTE_201. Marked disposable claude/pal-park-scratch-* branch only.
"""
import argparse
import importlib.util
import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = "Pokemon Game/engine/"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


w2 = load("w6_w2", HERE.parent / "southwest-coast/prepare_runtime.py")
encode = lambda d: (json.dumps(d, indent=2) + "\n").encode()


def assemble(repo):
    files, receipt = w2.assemble(repo)
    st = HERE / "staged"
    r221 = json.loads((st / "Route221-dev-overlay/map.json").read_text())
    r221["region_map_section"] = "MAPSEC_ROUTE_201"
    files["data/maps/Route221/map.json"] = encode(r221)
    groups, layouts = json.loads(files["data/maps/map_groups.json"]), json.loads(files["data/layouts/layouts.json"])
    names, g = groups["gMapGroup_Sinnoh"], groups["group_order"].index("gMapGroup_Sinnoh")
    assert len(names) == 22
    pins = files["test/data/averon_map_registry_slots.inc"].decode()
    m = f"REGISTRY_GROUP({g}, gMapGroup_Sinnoh, 22, 1)"
    assert pins.count(m) == 1
    pins = pins.replace(m, f"REGISTRY_GROUP({g}, gMapGroup_Sinnoh, 24, 1)")
    inc = files["data/event_scripts.s"].decode()
    for slot, name in ((22, "PalPark"), (23, "PalPark_Gate")):
        hdr = json.loads((st / name / "map.json").read_text())
        hdr["region_map_section"] = "MAPSEC_ROUTE_201"
        files[f"data/maps/{name}/map.json"] = encode(hdr)
        files[f"data/maps/{name}/scripts.inc"] = (st / name / "scripts.inc").read_bytes()
        if name == "PalPark":
            for f in ("map.bin", "border.bin"):
                files[f"data/layouts/{name}/{f}"] = (st / name / f).read_bytes()
            layouts["layouts"].append(dict(id="LAYOUT_PAL_PARK", name="PalPark_Layout", width=40, height=36,
                                           primary_tileset="gTileset_General", secondary_tileset="gTileset_Dewford",
                                           layout_version="emerald", border_filepath="data/layouts/PalPark/border.bin",
                                           blockdata_filepath="data/layouts/PalPark/map.bin"))
        names.append(name)
        pins += f"REGISTRY_SLOT({g}, {slot}, {hdr['id']}, {name}, 1)\n"
        inc += f'\t.include "data/maps/{name}/scripts.inc"\n'
    files["data/maps/map_groups.json"] = encode(groups)
    files["data/layouts/layouts.json"] = encode(layouts)
    files["test/data/averon_map_registry_slots.inc"] = pins.encode()
    files["data/event_scripts.s"] = inc.encode()
    receipt["temporary_map_slots"].update(PalPark=22, PalPark_Gate=23)
    return files, receipt


def install(repo):
    repo = pathlib.Path(repo).resolve()
    git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True).stdout.decode()
    if not git("branch", "--show-current").startswith("claude/pal-park-scratch-") or \
            not (repo / ENGINE / ".map_qa_throwaway").is_file():
        raise ValueError("a marked disposable claude/pal-park-scratch-* branch is required")
    files, receipt = assemble(repo)
    for p, d in files.items():
        (repo / ENGINE / p).parent.mkdir(parents=True, exist_ok=True)
        (repo / ENGINE / p).write_bytes(d)
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=pathlib.Path, required=True)
    p.add_argument("--install", action="store_true")
    a = p.parse_args()
    print(json.dumps(install(a.repo) if a.install else assemble(a.repo)[1], indent=2))
