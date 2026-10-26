#!/usr/bin/env python3
"""DEV-only install of W3 (Fuego Ironworks outdoor + interior) at temporary Sinnoh slots 19-20 of main.

Stand-in section MAPSEC_ROUTE_201; stock General + Slateport banks; external access stays closed. Refuses anything but
a marked disposable claude/fuego-scratch-* branch with a clean engine tree.
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import struct
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = "Pokemon Game/engine/"
ORDER = ["FuegoIronworks", "FuegoIronworks_Inside"]
spec = importlib.util.spec_from_file_location("w3_builder", HERE / "build_fuego.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
encode = lambda d: (json.dumps(d, indent=2) + "\n").encode()


def assemble(repo):
    engine = pathlib.Path(repo).resolve() / ENGINE
    read = lambda p: (engine / p).read_bytes()
    groups, layouts = json.loads(read("data/maps/map_groups.json")), json.loads(read("data/layouts/layouts.json"))
    names, group = groups["gMapGroup_Sinnoh"], groups["group_order"].index("gMapGroup_Sinnoh")
    if len(names) != 19 or set(ORDER) & set(names):
        raise ValueError("expected main's 19-map Sinnoh group")
    pins = read("test/data/averon_map_registry_slots.inc").decode()
    marker = f"REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 19, 1)"
    if pins.count(marker) != 1:
        raise ValueError("registry count mismatch")
    pins = pins.replace(marker, f"REGISTRY_GROUP({group}, gMapGroup_Sinnoh, {19 + len(ORDER)}, 1)")
    _, maps = builder.build(engine)
    files, includes = {}, []
    for slot, name in enumerate(ORDER, 19):
        hdr, layout = maps[name]
        hdr = dict(hdr, region_map_section="MAPSEC_ROUTE_201")
        files[f"data/maps/{name}/map.json"] = encode(hdr)
        files[f"data/maps/{name}/scripts.inc"] = builder.w1.scripts(name).encode()
        if layout:
            cells, w, h, prim, sec = layout
            files[f"data/layouts/{name}/map.bin"] = struct.pack("<%dH" % len(cells), *cells)
            files[f"data/layouts/{name}/border.bin"] = struct.pack("<4H", *[cells[0]] * 4)
            layouts["layouts"].append(dict(id=hdr["layout"], name=name + "_Layout", width=w, height=h,
                                           primary_tileset=prim, secondary_tileset=sec, layout_version="emerald",
                                           border_filepath=f"data/layouts/{name}/border.bin",
                                           blockdata_filepath=f"data/layouts/{name}/map.bin"))
        names.append(name)
        pins += f"REGISTRY_SLOT({group}, {slot}, {hdr['id']}, {name}, 1)\n"
        includes.append(f'\t.include "data/maps/{name}/scripts.inc"')
    files["data/event_scripts.s"] = read("data/event_scripts.s") + ("\n".join(includes) + "\n").encode()
    files["data/maps/map_groups.json"] = encode(groups)
    files["data/layouts/layouts.json"] = encode(layouts)
    files["test/data/averon_map_registry_slots.inc"] = pins.encode()
    return files, {"status": "DEV_ONLY", "temporary_map_slots": {n: 19 + i for i, n in enumerate(ORDER)},
                   "files": {p: hashlib.sha256(d).hexdigest() for p, d in sorted(files.items())}}


def install(repo):
    repo = pathlib.Path(repo).resolve()
    git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True).stdout.decode()
    if not git("branch", "--show-current").startswith("claude/fuego-scratch-") or \
            not (repo / ENGINE / ".map_qa_throwaway").is_file():
        raise ValueError("a marked disposable claude/fuego-scratch-* branch is required")
    if git("status", "--porcelain", "--", ENGINE).splitlines() not in ([], ['?? "Pokemon Game/engine/.map_qa_throwaway"']):
        raise ValueError("refusing a dirty engine tree")
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
