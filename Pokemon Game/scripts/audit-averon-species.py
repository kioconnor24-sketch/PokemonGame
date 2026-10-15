#!/usr/bin/env python3
"""Inventory engine species and wild encounter references for Averon planning.

This is a *source inventory*, not an obtainability or runtime test. An entry in
species_info may be compile-time disabled; a wild reference may belong to an
unused map, and species may instead be obtained by evolution, gifts or scripts.
"""

import argparse
import collections
import csv
import json
import re
from pathlib import Path

SPECIES_TOKEN = re.compile(r"\bSPECIES_[A-Z][A-Z0-9_]*\b")
ENUM_MEMBER = re.compile(r"^\s*(SPECIES_[A-Z][A-Z0-9_]*)\s*(?:=[^,]+)?\s*,", re.M)
INFO_ENTRY = re.compile(r"^\s*\[(SPECIES_[A-Z][A-Z0-9_]*)\]\s*=", re.M)
GEN_FILE = re.compile(r"gen_([1-9])_families\.h$")
NON_POKEMON = {"SPECIES_NONE", "SPECIES_EGG"}


def names_in_enum(path):
    text = path.read_text(encoding="utf-8")
    # Limit parsing to the enum body; macros/other enums are not species IDs.
    match = re.search(r"\benum\s+(?:__attribute__\s*\(\(.*?\)\)\s*)?Species\s*\{(.*?)\};", text, re.S)
    if not match:
        raise ValueError(f"Species enum not found: {path}")
    return set(ENUM_MEMBER.findall(match.group(1))) - NON_POKEMON


def info_by_generation(directory):
    grouped = {}
    for path in sorted(directory.glob("gen_*_families.h")):
        match = GEN_FILE.fullmatch(path.name)
        if match:
            grouped[f"gen_{match.group(1)}"] = set(INFO_ENTRY.findall(path.read_text(encoding="utf-8")))
    if len(grouped) != 9:
        raise ValueError(f"Expected nine generation family files in {directory}; found {len(grouped)}")
    return grouped


def wild_species(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    references = collections.Counter()

    def walk(value):
        if isinstance(value, dict):
            for field, child in value.items():
                if field == "species" and isinstance(child, str):
                    # Count encounter slots, not unique occurrences or guaranteed captures.
                    if SPECIES_TOKEN.fullmatch(child):
                        references[child] += 1
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)
    return references


def config_generation_flags(path):
    text = path.read_text(encoding="utf-8")
    flags = {}
    for number in range(1, 10):
        match = re.search(rf"^\s*#define\s+P_GEN_{number}_POKEMON\s+(TRUE|FALSE)\b", text, re.M)
        flags[f"gen_{number}"] = match.group(1) if match else "UNKNOWN"
    return flags


def habitat_names(path):
    """Keep design placeholders distinct from verified engine species IDs."""
    rows = []
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            for part in row["example_species"].split(","):
                name = part.strip()
                if name:
                    rows.append({"zone": row["ecology_zone"], "name": name})
    return rows


def compile_report(project_root):
    engine = project_root / "engine"
    constants = names_in_enum(engine / "include/constants/species.h")
    grouped = info_by_generation(engine / "src/data/pokemon/species_info")
    defined = set().union(*grouped.values())
    encounters = wild_species(engine / "src/data/wild_encounters.json")
    flags = config_generation_flags(engine / "include/config/species_enabled.h")
    habitats = habitat_names(project_root / "Averon_Codex_Handoff/data/habitat_examples.csv")

    by_gen = []
    for gen, species in sorted(grouped.items()):
        by_gen.append({
            "generation": gen,
            "family_config": flags[gen],
            "source_entries": len(species),
            "referenced_in_wild_tables": len(species & encounters.keys()),
        })

    # Note: script/event gifts, evolution chains, form switches, quest encounters,
    # version toggles and map reachability require additional engine-aware analysis.
    return {
        "interpretation": "Static source inventory only: NOT a complete Pokédex, wild availability, or obtainability certification.",
        "generation_summary": by_gen,
        "declared_species_ids": len(constants),
        "species_info_source_entries": len(defined),
        "unique_wild_reference_ids": len(encounters),
        "wild_encounter_slots": sum(encounters.values()),
        "species_info_without_enum_id": sorted(defined - constants),
        "wild_references_without_species_info": sorted(set(encounters) - defined),
        "sample_wild_references": sorted(encounters)[:30],
        "habitat_design_examples": habitats,
        "limitations": [
            "Source family entries can be removed by C preprocessor switches; P_GEN flags alone are insufficient.",
            "Wild tables can include inaccessible maps, conditional species, or upstream Hoenn content.",
            "Gifts, evolutions, quests, scripted encounters, regional forms and breeding are not counted as available.",
            "No independent National Dex reference or sprite/form audit is included yet.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1], help="Pokemon Game project directory")
    parser.add_argument("--json-out", type=Path, help="Optional output path for full machine-readable report")
    args = parser.parse_args()
    try:
        report = compile_report(args.project.resolve())
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Unable to inventory source: {exc}\n")
    print("Averon species source inventory (NOT an obtainability audit)")
    for gen in report["generation_summary"]:
        print(f"  {gen['generation']}: config={gen['family_config']}, definitions={gen['source_entries']}, wild references={gen['referenced_in_wild_tables']}")
    print(f"Species IDs: {report['declared_species_ids']}; source definitions: {report['species_info_source_entries']}; unique wild-table IDs: {report['unique_wild_reference_ids']}")
    print(f"Unmatched wild references: {len(report['wild_references_without_species_info'])}; unmatched source definitions: {len(report['species_info_without_enum_id'])}")
    print("Important: wild species counts include upstream maps and do not establish capture availability.")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {args.json_out}")


if __name__ == "__main__":
    main()
