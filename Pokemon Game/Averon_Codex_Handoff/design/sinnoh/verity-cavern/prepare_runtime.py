#!/usr/bin/env python3
"""DEV-only install of W4: Verity Cavern at temporary Sinnoh slot 19 plus the Lake Verity mouth overlay.

Marked disposable claude/verity-cavern-scratch-* branch only. Stand-in section MAPSEC_ROUTE_201.
"""
import argparse
import importlib.util
import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = "Pokemon Game/engine/"


def install(repo):
    repo = pathlib.Path(repo).resolve()
    eng = repo / ENGINE
    git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True).stdout.decode()
    if not git("branch", "--show-current").startswith("claude/verity-cavern-scratch-") or not (eng / ".map_qa_throwaway").is_file():
        raise ValueError("a marked disposable claude/verity-cavern-scratch-* branch is required")
    st = HERE / "staged"
    groups = json.loads((eng / "data/maps/map_groups.json").read_text())
    names, g = groups["gMapGroup_Sinnoh"], groups["group_order"].index("gMapGroup_Sinnoh")
    if len(names) != 19:
        raise ValueError("expected main's 19-map Sinnoh group")
    names.append("VerityCavern")
    hdr = json.loads((st / "VerityCavern/map.json").read_text())
    hdr["region_map_section"] = "MAPSEC_ROUTE_201"
    files = {"data/maps/VerityCavern/map.json": json.dumps(hdr, indent=2) + "\n",
             "data/maps/VerityCavern/scripts.inc": (st / "VerityCavern/scripts.inc").read_text(),
             "data/maps/LakeVerity/map.json": (st / "LakeVerity-dev-overlay/map.json").read_text(),
             "data/maps/map_groups.json": json.dumps(groups, indent=2) + "\n"}
    layouts = json.loads((eng / "data/layouts/layouts.json").read_text())
    layouts["layouts"].append(dict(id="LAYOUT_VERITY_CAVERN", name="VerityCavern_Layout", width=21, height=16,
                                   primary_tileset="gTileset_General", secondary_tileset="gTileset_Cave",
                                   layout_version="emerald", border_filepath="data/layouts/VerityCavern/border.bin",
                                   blockdata_filepath="data/layouts/VerityCavern/map.bin"))
    files["data/layouts/layouts.json"] = json.dumps(layouts, indent=2) + "\n"
    pins = (eng / "test/data/averon_map_registry_slots.inc").read_text()
    m = f"REGISTRY_GROUP({g}, gMapGroup_Sinnoh, 19, 1)"
    assert pins.count(m) == 1
    files["test/data/averon_map_registry_slots.inc"] = pins.replace(m, f"REGISTRY_GROUP({g}, gMapGroup_Sinnoh, 20, 1)") + \
        f"REGISTRY_SLOT({g}, 19, MAP_VERITY_CAVERN, VerityCavern, 1)\n"
    files["data/event_scripts.s"] = (eng / "data/event_scripts.s").read_text() + '\t.include "data/maps/VerityCavern/scripts.inc"\n'
    for p, d in files.items():
        (eng / p).parent.mkdir(parents=True, exist_ok=True)
        (eng / p).write_text(d)
    (eng / "data/layouts/VerityCavern").mkdir(exist_ok=True)
    (eng / "data/layouts/VerityCavern/map.bin").write_bytes((st / "VerityCavern/map.bin").read_bytes())
    (eng / "data/layouts/VerityCavern/border.bin").write_bytes((st / "VerityCavern/border.bin").read_bytes())
    (eng / "data/layouts/LakeVerity/map.bin").write_bytes((st / "LakeVerity-dev-overlay/map.bin").read_bytes())
    return {"status": "DEV_ONLY", "slot": 19}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=pathlib.Path, required=True)
    print(json.dumps(install(p.parse_args().repo)))
