#!/usr/bin/env python3
"""Static map_qa audit of a Claude overlay batch on top of a Codex family scene (no build, DEV only).

  static_scene.py REPO FAMILY BATCH_DIR [MAP_ID ...]

REPO is a disposable checkout of main (marked .map_qa_throwaway, engine tree reset first). FAMILY is a Codex design
folder whose prepare_runtime.assemble() supplies the base scene, or '-' for the production scene itself. BATCH_DIR/staged holds *-dev-overlay/map.json
(headers replacing the family's; an optional same-size map.bin replaces its blockdata) and new maps (map.json [+ map.bin/border.bin + layout dims from map.bin size]).
"""
import importlib.util
import json
import pathlib
import re
import struct
import subprocess
import sys

ENGINE = "Pokemon Game/engine/"


IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")


def inside(root, rel):
    """root/rel resolved (symlinks followed); refuses anything that leaves root."""
    root = pathlib.Path(root).resolve()
    path = (root / rel).resolve()
    if path != root and root not in path.parents:
        raise SystemExit(f"refused: {rel} leaves {root}")
    return path


def declare_tilesets(files, eng, batch, decls):
    """Each declared tileset as its own symbol: metatile banks under data/tilesets/<bank>/<symbol>/ plus extern,
    INCBIN and a Tileset bound to an existing tileset's tiles/palettes/callback. Every input is validated before
    anything is added to files: identifiers, a real boolean bank, sources inside the batch, no existing symbol."""
    for path in ("include/tilesets.h", "src/data/tilesets/headers.h", "src/data/tilesets/metatiles.h"):
        files.setdefault(path, (eng / path).read_bytes())
    seen = set()
    for t in decls:
        sym, graphics = t.get("symbol"), t.get("graphics")
        for value in (sym, graphics):
            if not (isinstance(value, str) and IDENT.match(value)):
                raise SystemExit(f"tilesets.json: {value!r} is not a C identifier")
        if not isinstance(t.get("secondary"), bool):
            raise SystemExit(f"tilesets.json: {sym}: secondary must be true or false")
        if sym in seen or re.search(r"\bgTileset_" + re.escape(sym) + r"\b", files["include/tilesets.h"].decode()):
            raise SystemExit(f"tilesets.json: gTileset_{sym} already exists")
        seen.add(sym)
        bank = "secondary" if t["secondary"] else "primary"
        folder = f"data/tilesets/{bank}/{sym.lower()}/"
        if (eng / folder).exists() or any(k.startswith(folder) for k in files):
            raise SystemExit(f"tilesets.json: {folder} already exists")
        text = files["src/data/tilesets/headers.h"].decode()
        found = re.search(r"const struct Tileset gTileset_" + re.escape(graphics) + r" =\s*\{(.*?)\};", text, re.S)
        if not found:
            raise SystemExit(f"tilesets.json: no gTileset_{graphics} to bind {sym} to")
        bind = {f: re.search(r"\." + f + r"\s*=\s*(\w+)\s*,", found[1])[1] for f in ("tiles", "palettes", "callback")}
        files[folder + "metatiles.bin"] = inside(batch, t["metatiles"]).read_bytes()
        files[folder + "metatile_attributes.bin"] = inside(batch, t["attributes"]).read_bytes()
        files["include/tilesets.h"] += f"\nextern const struct Tileset gTileset_{sym};\n".encode()
        files["src/data/tilesets/metatiles.h"] += (f'\nconst u16 gMetatiles_{sym}[] = INCBIN_U16("{folder}metatiles.bin");\n'
                                                   f'const u16 gMetatileAttributes_{sym}[] = INCBIN_U16("{folder}metatile_attributes.bin");\n').encode()
        files["src/data/tilesets/headers.h"] += (f"\nconst struct Tileset gTileset_{sym} = {{ .isCompressed=TRUE, "
                                                 f".isSecondary={'TRUE' if t['secondary'] else 'FALSE'}, .tiles={bind['tiles']}, "
                                                 f".palettes={bind['palettes']}, .metatiles=gMetatiles_{sym}, "
                                                 f".metatileAttributes = gMetatileAttributes_{sym}, .callback={bind['callback']} }};\n").encode()


def write_files(eng, files):
    """Writes the scene into the engine tree; every target is checked to stay inside it before the first write."""
    targets = {rel: inside(eng, rel) for rel in files}
    for rel, path in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(files[rel])


def main():
    repo, family, batch = pathlib.Path(sys.argv[1]).resolve(), sys.argv[2], pathlib.Path(sys.argv[3]).resolve()
    maps = sys.argv[4:]
    eng = repo / ENGINE
    assert (eng / ".map_qa_throwaway").is_file()
    subprocess.run(["git", "-C", str(repo), "checkout", "-q", "--", ENGINE], check=True)
    subprocess.run(["git", "-C", str(repo), "clean", "-qfd", "--", ENGINE + "data", ENGINE + "test", ENGINE + "src",
                    ENGINE + "include"], check=True)
    design = repo / "Pokemon Game/Averon_Codex_Handoff/design/sinnoh"
    if family == "-":  # the production scene itself: overlays replace files of the engine tree
        files = {k: (eng / k).read_bytes() for k in
                 ("data/maps/map_groups.json", "data/layouts/layouts.json", "data/event_scripts.s")}
    else:
        if "+" in family:   # several families composed into one scene (compose_scene.py)
            spec = importlib.util.spec_from_file_location("compose", pathlib.Path(__file__).with_name("compose_scene.py"))
            comp = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(comp)
            files, _ = comp.assemble(repo, family.split("+"))
        else:
            module = family if family.endswith(".py") else family + "/prepare_runtime.py"   # FAMILY may name its module
            spec = importlib.util.spec_from_file_location("fam", design / module)
            fam = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fam)
            files, _ = fam.assemble(repo)
    groups = json.loads(files["data/maps/map_groups.json"])
    layouts = json.loads(files["data/layouts/layouts.json"])
    names = groups["gMapGroup_Sinnoh"]
    inc = files["data/event_scripts.s"].decode()
    layout_ids = {l["id"] for l in layouts["layouts"]}
    st = batch / "staged"
    skipped = set()      # ids of overlays outside this scene: new maps leading into them are skipped too
    dirs = sorted(st.iterdir(), key=lambda d: (not d.name.endswith("-dev-overlay"), d.name))
    # New maps reaching a skipped overlay through other new maps are skipped too (to a fixed point).
    news = {json.loads((d / "map.json").read_text())["id"]: {w["dest_map"] for w in
            json.loads((d / "map.json").read_text())["warp_events"]}
            for d in dirs if (d / "map.json").exists() and not d.name.endswith("-dev-overlay")}
    for d in dirs:
        hdr_path = d / "map.json"
        if not hdr_path.exists():
            continue
        hdr = json.loads(hdr_path.read_text())
        hdr["region_map_section"] = "MAPSEC_ROUTE_201"
        if d.name.endswith("-dev-overlay"):
            name = d.name[: -len("-dev-overlay")]
            key = f"data/maps/{name}/map.json"
            if key not in files and (eng / key).exists():   # a production map overlaid in any scene
                files.setdefault(key, (eng / key).read_bytes())
                files.setdefault(f"data/maps/{name}/scripts.inc", (eng / f"data/maps/{name}/scripts.inc").read_bytes())
                if (d / "map.bin").exists():
                    layout = json.loads(files[key])["layout"]
                    rel = next(l["blockdata_filepath"] for l in layouts["layouts"] if l.get("id") == layout)
                    files.setdefault(f"data/layouts/{name}/map.bin", (eng / rel).read_bytes())
            if key not in files:
                print("skip overlay (not in this family scene):", name)
                skipped.add(hdr["id"])
                continue
            files[key] = (json.dumps(hdr, indent=2) + "\n").encode()
            if (d / "map.bin").exists():  # DEV-derived blockdata of the family's own layout (same dimensions)
                key = f"data/layouts/{name}/map.bin"
                assert key in files and len(files[key]) == (d / "map.bin").stat().st_size, key
                files[key] = (d / "map.bin").read_bytes()
            script = d / "portal-script.inc"
            if script.exists():
                files[f"data/maps/{name}/scripts.inc"] += b"\n" + script.read_bytes()
            continue
        name = d.name
        while True:
            more = {m for m, dests in news.items() if m not in skipped and dests & skipped}
            if not more:
                break
            skipped |= more
        if hdr["id"] in skipped:
            print("skip map (leads into a skipped overlay):", name)
            continue
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
    tilesets = st / "tilesets.json"     # a batch's own tileset pair, declared as Codex's family assemblers do
    if tilesets.exists():
        declare_tilesets(files, eng, batch, json.loads(tilesets.read_text()))
    files["data/maps/map_groups.json"] = (json.dumps(groups, indent=2) + "\n").encode()
    files["data/layouts/layouts.json"] = (json.dumps(layouts, indent=2) + "\n").encode()
    files["data/event_scripts.s"] = inc.encode()
    write_files(eng, files)
    cmd = [sys.executable, "-B", "map_qa.py", "static", "--engine", "../../engine"] + sum((["--map", m] for m in maps), [])
    r = subprocess.run(cmd, cwd=repo / "Pokemon Game/scripts/claude_play", capture_output=True, text=True)
    print(r.stdout[-3000:], r.stderr[-1500:])


if __name__ == "__main__":
    main()
