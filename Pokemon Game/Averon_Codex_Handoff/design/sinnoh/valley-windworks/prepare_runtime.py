#!/usr/bin/env python3
"""DEV-only install of W5 (Valley Windworks + inside, slots 19-20) with the Route 205 South/North connection overlays.

Marked disposable claude/windworks-scratch-* branch with a clean engine tree only; stand-in section MAPSEC_ROUTE_201; stock banks.
"""
import argparse
import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).resolve().parent
ENGINE = "Pokemon Game/engine/"
MAPS = [("ValleyWindworks", 32, 99, "gTileset_General", "gTileset_Mauville"),
        ("ValleyWindworks_Inside", 22, 16, "gTileset_Building", "gTileset_BikeShop")]


def install(repo):
    repo = pathlib.Path(repo).resolve()
    eng = repo / ENGINE
    git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True).stdout.decode()
    if not git("branch", "--show-current").startswith("claude/windworks-scratch-") or not (eng / ".map_qa_throwaway").is_file():
        raise ValueError("a marked disposable claude/windworks-scratch-* branch is required")
    # As W1-W3: never overwrite unique scratch work (anything but the throwaway marker changed in the engine tree).
    status = git("status", "--porcelain", "--untracked-files=normal", "--", ENGINE).splitlines()
    if status not in ([], ['?? "Pokemon Game/engine/.map_qa_throwaway"']):
        raise ValueError("refusing a dirty engine tree")
    st = HERE / "staged"
    groups = json.loads((eng / "data/maps/map_groups.json").read_text())
    layouts = json.loads((eng / "data/layouts/layouts.json").read_text())
    names, g = groups["gMapGroup_Sinnoh"], groups["group_order"].index("gMapGroup_Sinnoh")
    if len(names) != 19:
        raise ValueError("expected main's 19-map Sinnoh group")
    pins = (eng / "test/data/averon_map_registry_slots.inc").read_text()
    m = f"REGISTRY_GROUP({g}, gMapGroup_Sinnoh, 19, 1)"
    assert pins.count(m) == 1
    pins = pins.replace(m, f"REGISTRY_GROUP({g}, gMapGroup_Sinnoh, 21, 1)")
    inc = (eng / "data/event_scripts.s").read_text()
    for slot, (name, w, h, pri, sec) in enumerate(MAPS, 19):
        hdr = json.loads((st / name / "map.json").read_text())
        hdr["region_map_section"] = "MAPSEC_ROUTE_201"
        (eng / f"data/maps/{name}").mkdir(parents=True, exist_ok=True)
        (eng / f"data/maps/{name}/map.json").write_text(json.dumps(hdr, indent=2) + "\n")
        (eng / f"data/maps/{name}/scripts.inc").write_text((st / name / "scripts.inc").read_text())
        (eng / f"data/layouts/{name}").mkdir(parents=True, exist_ok=True)
        for f in ("map.bin", "border.bin"):
            (eng / f"data/layouts/{name}/{f}").write_bytes((st / name / f).read_bytes())
        layouts["layouts"].append(dict(id=hdr["layout"], name=name + "_Layout", width=w, height=h, primary_tileset=pri,
                                       secondary_tileset=sec, layout_version="emerald",
                                       border_filepath=f"data/layouts/{name}/border.bin",
                                       blockdata_filepath=f"data/layouts/{name}/map.bin"))
        names.append(name)
        pins += f"REGISTRY_SLOT({g}, {slot}, {hdr['id']}, {name}, 1)\n"
        inc += f'\t.include "data/maps/{name}/scripts.inc"\n'
    for name in ("Route205_South", "Route205_North"):
        (eng / f"data/maps/{name}/map.json").write_text((st / f"{name}-dev-overlay/map.json").read_text())
    (eng / "data/maps/map_groups.json").write_text(json.dumps(groups, indent=2) + "\n")
    (eng / "data/layouts/layouts.json").write_text(json.dumps(layouts, indent=2) + "\n")
    (eng / "test/data/averon_map_registry_slots.inc").write_text(pins)
    (eng / "data/event_scripts.s").write_text(inc)
    return {"status": "DEV_ONLY", "slots": {"ValleyWindworks": 19, "ValleyWindworks_Inside": 20}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=pathlib.Path, required=True)
    print(json.dumps(install(p.parse_args().repo)))
