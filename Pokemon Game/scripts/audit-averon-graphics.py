#!/usr/bin/env python3
"""Conservative, read-only Emerald Expansion species graphics source audit.

This inventories references declared by gSpeciesInfo, NOT compiled graphics or
runtime availability. Preprocessor guards are deliberately not evaluated.
"""
import argparse
import csv
import json
import re
from pathlib import Path

ENTRY = re.compile(r"^\s*\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*\{", re.M)
FIELD = re.compile(r"\.(frontPic|backPic|palette|shinyPalette|iconSprite|iconPalIndex)\s*=\s*([^,\n]+)")
OVERWORLD = re.compile(r"\b(OVERWORLD(?:_FEMALE|_PAL|_PAL_FEMALE)?)\s*\(")
SPECIES = re.compile(r"^\s*(SPECIES_[A-Z0-9_]+)\s*(?:=\s*[^,]+)?\s*,?", re.M)
HEADERS = ["species", "source_line", "frontPic", "backPic", "palette",
           "shinyPalette", "iconSprite", "iconPalIndex", "overworld_macro",
           "conditional", "status", "notes"]


def strip_comments(text):
    """Remove comments without changing line counts."""
    text = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group().count("\n"), text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def entries(source):
    """Get bounded entry bodies; brace depth handles nested initializer lists."""
    matches = list(ENTRY.finditer(source))
    for match in matches:
        depth = 1
        start = match.end()
        i = start
        while i < len(source) and depth:
            if source[i] == "{":
                depth += 1
            elif source[i] == "}":
                depth -= 1
            i += 1
        if depth:
            raise ValueError("Unclosed species entry " + match.group(1))
        yield match.group(1), source[start:i - 1], source.count("\n", 0, match.start()) + 1


def expand_local_includes(path, root, visited=None):
    """Resolve quoted C includes under the species_info directory, once each.

    Keep source and engine trees read-only. Refuse path traversal outside root.
    """
    root = root.resolve()
    path = path.resolve()
    if not path.is_relative_to(root):
        raise ValueError("Include escapes species source directory: " + str(path))
    visited = set() if visited is None else visited
    if path in visited:
        return ""
    visited.add(path)
    content = path.read_text(encoding="utf-8")
    lines = []
    for line in content.splitlines(keepends=True):
        found = re.match(r'^\\s*#\\s*include\\s+"(species_info/[^"]+)"', line)
        if found:
            child = (path.parent / found.group(1)).resolve()
            if not child.is_relative_to(root):
                raise ValueError("Include escapes species source directory: " + str(child))
            if not child.is_file():
                raise FileNotFoundError("Missing species family include: " + str(child))
            lines.append(expand_local_includes(child, root, visited))
        else:
            lines.append(line)
    return "".join(lines)


def audit(source, species_header):
    declared = {name for name in SPECIES.findall(strip_comments(species_header))
                if name not in {"SPECIES_NONE"}}
    clean = strip_comments(source)
    results = []
    seen = set()
    for name, body, line in entries(clean):
        if name == "SPECIES_NONE":
            continue
        seen.add(name)
        fields = dict(FIELD.findall(body))
        macros = sorted(set(OVERWORLD.findall(body)))
        conditional = bool(re.search(r"\b(?:P_FAMILY_|P_GEN_|P_GENDER_|OW_POKEMON_)", body))
        # Preprocessor guards may occur OUTSIDE the initializer body.
        # All entries are therefore conservatively conditional until compiled.
        missing = [x for x in ("frontPic", "backPic", "palette", "shinyPalette", "iconSprite")
                   if x not in fields]
        notes = []
        if missing:
            notes.append("No direct assignment: " + ", ".join(missing))
        if not macros:
            notes.append("No overworld macro in entry; follower asset not established")
        notes.append("Assets, link symbols, configuration guards and runtime not verified")
        if conditional:
            notes.append("Body contains feature-condition reference")
        results.append(dict(species=name, source_line=line,
                            **{key: fields.get(key, "") for key in HEADERS[2:8]},
                            overworld_macro=";".join(macros), conditional=True,
                            status="source_references_only",
                            notes="; ".join(notes)))
    return {
        "scope": "Static source references only; not build, sprite path, or follower verification",
        "declared_species_count": len(declared),
        "species_entry_count": len(results),
        "declared_without_entry": sorted(declared - seen),
        "entries_not_in_species_enum": sorted(seen - declared),
        "rows": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args()
    root = args.engine
    source = root / "src/data/pokemon/species_info.h"
    header = root / "include/constants/species.h"
    if not source.is_file() or not header.is_file():
        parser.error("Expected real engine source files: " + str(source) + " and " + str(header))
    report = audit(expand_local_includes(source, source.parent), header.read_text(encoding="utf-8"))
    for output in (args.json, args.csv):
        output.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    with args.csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(report["rows"])
    print(f"Inspected {report['species_entry_count']} species/form entries; "
          f"{len(report['declared_without_entry'])} declared IDs lack direct initializer. "
          "No runtime graphics verified.")


if __name__ == "__main__":
    main()
