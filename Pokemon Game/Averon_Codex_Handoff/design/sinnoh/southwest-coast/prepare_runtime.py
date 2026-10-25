#!/usr/bin/env python3
"""DEV-only install of the W2 south-west coast (Routes 219-221) in a disposable checkout of main.

Appends the three staged maps at temporary Sinnoh slots 19-21 with the stand-in section MAPSEC_ROUTE_201, and gives
Averon's Sandgem the proposed down connection to Route 219 (DEV only: the production Sandgem header is protected and
untouched). Stock General + Dewford banks; no tileset changes. Refuses anything but a marked disposable
claude/southwest-scratch-* branch with a clean engine tree.

  prepare_runtime.py --repo REPO            print the receipt (no writes)
  prepare_runtime.py --repo REPO --install  write the overlay into REPO's engine tree
"""
import argparse
import hashlib
import importlib.util
import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = "Pokemon Game/engine/"
STAND_IN = "MAPSEC_ROUTE_201"
ORDER = ["Route219", "Route220", "Route221"]
spec = importlib.util.spec_from_file_location("w2_builder", HERE / "build_southwest.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
sha = lambda data: hashlib.sha256(data).hexdigest()
encode = lambda data: (json.dumps(data, indent=2) + "\n").encode()


def assemble(repo):
    engine = pathlib.Path(repo).resolve() / ENGINE
    read = lambda p: (engine / p).read_bytes()
    groups, layouts = json.loads(read("data/maps/map_groups.json")), json.loads(read("data/layouts/layouts.json"))
    names, group = groups["gMapGroup_Sinnoh"], groups["group_order"].index("gMapGroup_Sinnoh")
    if len(names) != 19 or set(ORDER) & set(names) or "SandgemTown" not in names:
        raise ValueError("expected main's 19-map Sinnoh group")
    pins = read("test/data/averon_map_registry_slots.inc").decode()
    marker = f"REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 19, 1)"
    if pins.count(marker) != 1:
        raise ValueError("registry count mismatch")
    pins = pins.replace(marker, f"REGISTRY_GROUP({group}, gMapGroup_Sinnoh, {19 + len(ORDER)}, 1)")
    files, includes = {}, []
    for slot, name in enumerate(ORDER, 19):
        staged = HERE / "staged" / name
        hdr = json.loads((staged / "map.json").read_text())
        w, h, _ = builder.MAPS[name]
        if hdr["region_map_section"] != builder.PENDING or (w + 15) * (h + 14) > 10240:
            raise ValueError(f"{name}: not a pending staged map within the map buffer")
        hdr["region_map_section"] = STAND_IN
        files[f"data/maps/{name}/map.json"] = encode(hdr)
        files[f"data/maps/{name}/scripts.inc"] = (staged / "scripts.inc").read_bytes()
        files[f"data/layouts/{name}/map.bin"] = (staged / "map.bin").read_bytes()
        files[f"data/layouts/{name}/border.bin"] = (staged / "border.bin").read_bytes()
        layouts["layouts"].append(dict(id=hdr["layout"], name=name + "_Layout", width=w, height=h,
                                       primary_tileset="gTileset_General", secondary_tileset="gTileset_Dewford",
                                       layout_version="emerald", border_filepath=f"data/layouts/{name}/border.bin",
                                       blockdata_filepath=f"data/layouts/{name}/map.bin"))
        names.append(name)
        pins += f"REGISTRY_SLOT({group}, {slot}, {hdr['id']}, {name}, 1)\n"
        includes.append(f'\t.include "data/maps/{name}/scripts.inc"')
    sandgem = json.loads(read("data/maps/SandgemTown/map.json"))
    if any(c["direction"] == "down" for c in sandgem["connections"]):
        raise ValueError("Sandgem already has a south connection")
    sandgem["connections"].append(builder.SANDGEM_TO_219)
    files["data/maps/SandgemTown/map.json"] = encode(sandgem)
    files["data/event_scripts.s"] = read("data/event_scripts.s") + ("\n".join(includes) + "\n").encode()
    files["data/maps/map_groups.json"] = encode(groups)
    files["data/layouts/layouts.json"] = encode(layouts)
    files["test/data/averon_map_registry_slots.inc"] = pins.encode()
    return files, dict(status="DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE",
                       temporary_map_slots={n: 19 + i for i, n in enumerate(ORDER)},
                       dev_only_production_file_overlays=["data/maps/SandgemTown/map.json"],
                       files={p: sha(d) for p, d in sorted(files.items())})


def git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True).stdout.decode()


def install(repo):
    repo = pathlib.Path(repo).resolve()
    engine = repo / ENGINE
    if not git(repo, "branch", "--show-current").strip().startswith("claude/southwest-scratch-") \
            or not (engine / ".map_qa_throwaway").is_file():
        raise ValueError("a marked disposable claude/southwest-scratch-* branch is required")
    status = git(repo, "status", "--porcelain", "--untracked-files=normal", "--", ENGINE).splitlines()
    if status not in ([], ['?? "Pokemon Game/engine/.map_qa_throwaway"']):
        raise ValueError("refusing a dirty engine tree")
    files, receipt = assemble(repo)
    for path, data in files.items():
        target = engine / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return receipt


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", type=pathlib.Path, required=True)
    p.add_argument("--install", action="store_true")
    args = p.parse_args()
    print(json.dumps(install(args.repo) if args.install else assemble(args.repo)[1], indent=2))
