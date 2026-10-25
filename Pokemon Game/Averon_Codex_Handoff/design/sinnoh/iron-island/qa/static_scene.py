#!/usr/bin/env python3
"""Static map_qa audit of a Claude overlay batch on top of a Codex family scene (no build, DEV only).

  static_scene.py REPO FAMILY BATCH_DIR [--map MAP_ID ...]

REPO is a disposable checkout of main (marked .map_qa_throwaway, engine tree reset first). FAMILY is a Codex design
folder whose prepare_runtime.assemble() supplies the base scene. BATCH_DIR/staged holds *-dev-overlay/map.json
(headers replacing the family's) and new maps (map.json [+ map.bin/border.bin + layout dims from map.bin size]).
"""
import importlib.util
import json
import pathlib
import struct
import subprocess
import sys

ENGINE = "Pokemon Game/engine/"


def main():
    repo, family, batch = pathlib.Path(sys.argv[1]).resolve(), sys.argv[2], pathlib.Path(sys.argv[3]).resolve()
    maps = sys.argv[4:]
    eng = repo / ENGINE
    assert (eng / ".map_qa_throwaway").is_file()
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "--", ENGINE], check=True)
    subprocess.run(["git", "-C", str(repo), "clean", "-qfd", "--", ENGINE + "data", ENGINE + "test", ENGINE + "src",
                    ENGINE + "include"], check=True)
    design = repo / "Pokemon Game/Averon_Codex_Handoff/design/sinnoh"
    spec = importlib.util.spec_from_file_location("fam", design / family / "prepare_runtime.py")
    fam = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fam)
    files, _ = fam.assemble(repo)
    groups = json.loads(files["data/maps/map_groups.json"])
    layouts = json.loads(files["data/layouts/layouts.json"])
    names = groups["gMapGroup_Sinnoh"]
    inc = files["data/event_scripts.s"].decode()
    layout_ids = {l["id"] for l in layouts["layouts"]}
    st = batch / "staged"
    for d in sorted(st.iterdir()):
        hdr_path = d / "map.json"
        if not hdr_path.exists():
            continue
        hdr = json.loads(hdr_path.read_text())
        hdr["region_map_section"] = "MAPSEC_ROUTE_201"
        if d.name.endswith("-dev-overlay"):
            name = d.name[: -len("-dev-overlay")]
            key = f"data/maps/{name}/map.json"
            if key not in files:
                print("skip overlay (not in this family scene):", name)
                continue
            files[key] = (json.dumps(hdr, indent=2) + "\n").encode()
            script = d / "portal-script.inc"
            if script.exists():
                files[f"data/maps/{name}/scripts.inc"] += b"\n" + script.read_bytes()
            continue
        name = d.name
        files[f"data/maps/{name}/map.json"] = (json.dumps(hdr, indent=2) + "\n").encode()
        files[f"data/maps/{name}/scripts.inc"] = (d / "scripts.inc").read_bytes()
        if (d / "map.bin").exists() and hdr["layout"] not in layout_ids:
            info = json.loads((d / "layout.json").read_text()) if (d / "layout.json").exists() else None
            raw = (d / "map.bin").read_bytes()
            w, h = (info["width"], info["height"]) if info else (None, None)
            if w is None:
                raise SystemExit(f"{name}: layout.json with width/height required")
            files[f"data/layouts/{name}/map.bin"] = raw
            files[f"data/layouts/{name}/border.bin"] = (d / "border.bin").read_bytes()
            layouts["layouts"].append(dict(id=hdr["layout"], name=name + "_Layout", width=w, height=h,
                                           primary_tileset=info["primary_tileset"], secondary_tileset=info["secondary_tileset"],
                                           layout_version="emerald", border_filepath=f"data/layouts/{name}/border.bin",
                                           blockdata_filepath=f"data/layouts/{name}/map.bin"))
            layout_ids.add(hdr["layout"])
        names.append(name)
        inc += f'\t.include "data/maps/{name}/scripts.inc"\n'
    files["data/maps/map_groups.json"] = (json.dumps(groups, indent=2) + "\n").encode()
    files["data/layouts/layouts.json"] = (json.dumps(layouts, indent=2) + "\n").encode()
    files["data/event_scripts.s"] = inc.encode()
    for p, data in files.items():
        (eng / p).parent.mkdir(parents=True, exist_ok=True)
        (eng / p).write_bytes(data)
    cmd = [sys.executable, "-B", "map_qa.py", "static", "--engine", "../../engine"] + sum((["--map", m] for m in maps), [])
    r = subprocess.run(cmd, cwd=repo / "Pokemon Game/scripts/claude_play", capture_output=True, text=True)
    print(r.stdout[-3000:], r.stderr[-1500:])


if __name__ == "__main__":
    main()
