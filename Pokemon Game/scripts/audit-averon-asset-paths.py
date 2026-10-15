#!/usr/bin/env python3
"""Inventory real on-disk Pokémon graphics, forms, and follower file candidates.

This is deliberately filesystem-grounded: it proves whether conventional
file paths exist, not whether their symbol is linked or the ROM can draw them.
"""
import argparse
import csv
import json
from pathlib import Path

EXPECTED_BASE = {
    "battle_front": ("anim_front.png", "front.png"),
    "battle_back": ("back.png",),
    "icon": ("icon.png",),
    "normal_palette": ("normal.pal",),
    "shiny_palette": ("shiny.pal",),
    "overworld_sheet": ("overworld.png",),
    "overworld_normal_palette": ("overworld_normal.pal",),
    "overworld_shiny_palette": ("overworld_shiny.pal",),
}
COLUMNS = ["asset_folder", "kind", "battle_front", "battle_back", "icon",
           "normal_palette", "shiny_palette", "overworld_sheet",
           "overworld_normal_palette", "overworld_shiny_palette",
           "missing_files", "follower_files_present"]


def is_asset_folder(folder):
    return any((folder / name).is_file() for names in EXPECTED_BASE.values()
               for name in names)


def inspect_folder(folder, root):
    observed = {}
    missing = []
    for key, names in EXPECTED_BASE.items():
        chosen = next((p for p in names if (folder / p).is_file()), None)
        observed[key] = chosen or ""
        if not chosen:
            missing.append(key)
    is_form = folder.relative_to(root).parts
    return {
        "asset_folder": folder.relative_to(root).as_posix(),
        "kind": "form_candidate" if len(is_form) > 1 else "base_folder",
        **observed,
        "missing_files": ";".join(missing),
        "follower_files_present": all(observed[k] for k in
                    ("overworld_sheet", "overworld_normal_palette", "overworld_shiny_palette")),
    }


def inspect(graphics_root):
    if not graphics_root.is_dir():
        raise FileNotFoundError("Missing actual graphics/pokemon source directory: " + str(graphics_root))
    folders = sorted(
        [item for item in graphics_root.iterdir() if item.is_dir()] +
        [child for item in graphics_root.iterdir() if item.is_dir()
         for child in item.rglob("*") if child.is_dir()],
        key=lambda p: p.as_posix()
    )
    rows = [inspect_folder(folder, graphics_root)
            for folder in folders if is_asset_folder(folder)]
    return {
        "scope": "Paths on disk only; no symbol linkage, runtime, or copyright certification",
        "counts": {
            "asset_directories": len(rows),
            "base_directories": sum(r["kind"] == "base_folder" for r in rows),
            "form_directories": sum(r["kind"] == "form_candidate" for r in rows),
            "follower_file_triplets": sum(r["follower_files_present"] for r in rows),
            "missing_any_conventional_asset": sum(bool(r["missing_files"]) for r in rows),
        },
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--json", required=True, type=Path)
    parser.add_argument("--csv", required=True, type=Path)
    args = parser.parse_args()
    report = inspect(args.engine / "graphics/pokemon")
    for path in (args.json, args.csv):
        path.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    with args.csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(report["rows"])
    print(json.dumps(report["counts"], indent=2))


if __name__ == "__main__":
    main()
