#!/usr/bin/env python3
"""DEV-only install of the W1 batch (Canalave four maps + Iron Island/Harbor/Center) in a disposable checkout.

Reuses the merged canalave-west installer unchanged (its assemble() supplies Route218_East/Route218/Route218_West/
CanalaveCity at temporary slots 19-22 and their adapted banks), then replaces CanalaveCity's map.bin/map.json with
this batch's two-door overlay and appends this batch's six maps at temporary slots 23-28. Sections are the DEV
stand-in MAPSEC_ROUTE_201 (as canalave-west); production sections stay owner-only. Refuses anything but a marked
disposable claude/iron-island-scratch-* branch with a clean engine tree.

  prepare_runtime.py --repo REPO            print the receipt (no writes)
  prepare_runtime.py --repo REPO --install  write the overlay into REPO's engine tree
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
STAND_IN = "MAPSEC_ROUTE_201"
ORDER = ["IronIsland", "IronIsland_House", "IronIsland_1F", "IronIsland_B1F", "CanalaveCity_Harbor",
         "CanalaveCity_PokemonCenter_1F"]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


canalave = load("w1_canalave_runtime", HERE.parent / "canalave-west/prepare_runtime.py")
builder = load("w1_builder", HERE / "build_iron_island.py")
sha = lambda data: hashlib.sha256(data).hexdigest()
encode = lambda data: (json.dumps(data, indent=2) + "\n").encode()


def assemble(repo):
    repo = pathlib.Path(repo).resolve()
    files, receipt = canalave.assemble(repo)
    eng, maps, coords, (canal_bin, canal_header, canal_receipt) = builder.build(repo / ENGINE)
    builder.check(eng, maps, (canal_bin, canal_header, canal_receipt))
    old = json.loads(files["data/maps/CanalaveCity/map.json"])
    assert old["region_map_section"] == STAND_IN
    canal_header = dict(canal_header, region_map_section=STAND_IN)
    files["data/maps/CanalaveCity/map.json"] = encode(canal_header)
    assert sha(files["data/layouts/CanalaveCity/map.bin"]) == canal_receipt["source_sha256"]
    files["data/layouts/CanalaveCity/map.bin"] = canal_bin
    groups = json.loads(files["data/maps/map_groups.json"])
    layouts = json.loads(files["data/layouts/layouts.json"])
    names = groups["gMapGroup_Sinnoh"]
    group = groups["group_order"].index("gMapGroup_Sinnoh")
    if len(names) != 23 or set(ORDER) & set(names):
        raise ValueError("expected the canalave-west 23-map scene")
    pins = files["test/data/averon_map_registry_slots.inc"].decode()
    marker = f"REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 23, 1)"
    if pins.count(marker) != 1:
        raise ValueError("registry count mismatch")
    pins = pins.replace(marker, f"REGISTRY_GROUP({group}, gMapGroup_Sinnoh, {23 + len(ORDER)}, 1)")
    includes = []
    for slot, name in enumerate(ORDER, 23):
        hdr, layout = maps[name]
        hdr = dict(hdr, region_map_section=STAND_IN)
        files[f"data/maps/{name}/map.json"] = encode(hdr)
        files[f"data/maps/{name}/scripts.inc"] = builder.scripts(name, coords.get(name, ())).encode()
        if layout:
            cells, w, h, prim, sec = layout
            if (w + 15) * (h + 14) > 10240:
                raise ValueError("map footprint exceeds the map buffer")
            files[f"data/layouts/{name}/map.bin"] = struct.pack("<%dH" % len(cells), *cells)
            border = cells[0] if name == "IronIsland" else builder.Cave(eng, 1, 1).k[529]
            files[f"data/layouts/{name}/border.bin"] = struct.pack("<4H", *[border] * 4)
            layouts["layouts"].append(dict(id=hdr["layout"], name=name + "_Layout", width=w, height=h,
                                           primary_tileset=prim, secondary_tileset=sec, layout_version="emerald",
                                           border_filepath=f"data/layouts/{name}/border.bin",
                                           blockdata_filepath=f"data/layouts/{name}/map.bin"))
        names.append(name)
        pins += f"REGISTRY_SLOT({group}, {slot}, {hdr['id']}, {name}, 1)\n"
        includes.append(f'\t.include "data/maps/{name}/scripts.inc"')
    files["data/event_scripts.s"] += ("\n".join(includes) + "\n").encode()
    files["data/maps/map_groups.json"] = encode(groups)
    files["data/layouts/layouts.json"] = encode(layouts)
    files["test/data/averon_map_registry_slots.inc"] = pins.encode()
    receipt.update(status="DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE",
                   w1_temporary_map_slots={n: 23 + i for i, n in enumerate(ORDER)},
                   canalave_overlay=canal_receipt, files={p: sha(d) for p, d in sorted(files.items())})
    return files, receipt


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout.decode()


def install(repo):
    repo = pathlib.Path(repo).resolve()
    engine = repo / ENGINE
    if not git(repo, "branch", "--show-current").strip().startswith("claude/iron-island-scratch-") \
            or not (engine / ".map_qa_throwaway").is_file():
        raise ValueError("a marked disposable claude/iron-island-scratch-* branch is required")
    status = git(repo, "status", "--porcelain", "--untracked-files=normal", "--", ENGINE).splitlines()
    if status not in ([], ['?? "Pokemon Game/engine/.map_qa_throwaway"']):
        raise ValueError("refusing a dirty engine tree")
    files, receipt = assemble(repo)
    for path, data in files.items():
        target = engine / path
        if not target.resolve().is_relative_to(engine.resolve()):
            raise ValueError("output path escapes engine")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", type=pathlib.Path, required=True)
    p.add_argument("--install", action="store_true")
    args = p.parse_args()
    result = install(args.repo) if args.install else assemble(args.repo)[1]
    print(json.dumps(result, indent=2))
