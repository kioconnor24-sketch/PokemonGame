#!/usr/bin/env python3
"""Report configured encounter references for registered Averon maps.

This is a static *candidate encounter* inventory, not a guarantee that a map is
reachable or that an encounter is possible in the compiled game. In particular,
preprocessor flags, encounter conditions and the map's event gating are not
resolved here. It deliberately excludes unrelated upstream Hoenn wild tables.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

DEFAULT_MAP_GROUP = "gMapGroup_AveronOpening"
SPECIES_PREFIX = "SPECIES_"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def registered_maps(engine, group=DEFAULT_MAP_GROUP):
    groups = read_json(engine / "data/maps/map_groups.json")
    names = groups.get(group)
    if not isinstance(names, list) or not names:
        raise ValueError(f"No nonempty registered map group {group!r}")
    result = {}
    for name in names:
        if not isinstance(name, str):
            raise ValueError(f"Invalid name in map group {group}: {name!r}")
        path = engine / "data/maps" / name / "map.json"
        data = read_json(path)
        map_id = data.get("id")
        if not isinstance(map_id, str) or not map_id.startswith("MAP_"):
            raise ValueError(f"Invalid map ID in {path}: {map_id!r}")
        if map_id in result:
            raise ValueError(f"Duplicate map ID {map_id} in {group}")
        result[map_id] = {"directory": name, "type": data.get("map_type", "UNKNOWN")}
    return result


def encounter_entries(data):
    """Yield each wild-encounter map record regardless of group nesting.

    A map field in an encounter entry is different from a map reference in
    travel connections: this function is only called on wild_encounters.json.
    If the format includes nested map records, the nearest map owns its species.
    """
    def visit(node):
        if isinstance(node, dict):
            if isinstance(node.get("map"), str) and node["map"].startswith("MAP_"):
                yield node["map"], node
                return
            for child in node.values():
                yield from visit(child)
        elif isinstance(node, list):
            for child in node:
                yield from visit(child)
    yield from visit(data)


def referenced_species(entry):
    """Return a Counter for literal SPECIES_* encounter slots in an entry."""
    counted = Counter()

    def visit(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "species" and isinstance(child, str) and child.startswith(SPECIES_PREFIX):
                    counted[child] += 1
                else:
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(entry)
    return counted


def create_report(engine, group=DEFAULT_MAP_GROUP):
    maps = registered_maps(engine, group)
    wild = read_json(engine / "src/data/wild_encounters.json")
    counts = {map_id: Counter() for map_id in maps}
    matching_records = Counter()
    for map_id, entry in encounter_entries(wild):
        if map_id in counts:
            matching_records[map_id] += 1
            counts[map_id].update(referenced_species(entry))

    per_map = []
    union = set()
    for map_id, meta in maps.items():
        species = counts[map_id]
        union.update(species)
        per_map.append({
            "map_id": map_id,
            "directory": meta["directory"],
            "map_type": meta["type"],
            "wild_record_count": matching_records[map_id],
            "unique_species_references": len(species),
            "encounter_slot_references": sum(species.values()),
            "species_slot_counts": dict(sorted(species.items())),
        })
    return {
        "scope": "registered Averon maps only, not unrelated upstream regions",
        "interpretation": "Static wild encounter references only; NOT confirmed reachability, catchability or full Pokédex availability.",
        "map_group": group,
        "registered_map_count": len(maps),
        "maps_with_wild_species": sum(bool(counts[name]) for name in maps),
        "maps_with_wild_records_but_no_literal_species": sorted(
            name for name in maps if matching_records[name] and not counts[name]
        ),
        "unique_species_references": len(union),
        "map_records": per_map,
        "limitations": [
            "Map wild encounter source references can be inaccessible or overridden at runtime.",
            "Towns and interiors can legitimately have no wild encounters.",
            "A configured encounter does not establish compiled species enablement or gameplay reachability.",
            "Gifts, trades, scripted encounters, evolutions, breeding and fishing conditions are not independently verified.",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--group", default=DEFAULT_MAP_GROUP)
    parser.add_argument("--json-out", type=Path, help="Write machine-readable inventory to this path")
    args = parser.parse_args(argv)
    try:
        report = create_report(args.project.resolve() / "engine", args.group)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Map encounter inventory failed: {exc}\n")
    print(f"Map group: {report['map_group']}; registered maps: {report['registered_map_count']}")
    print(f"Maps with wild species: {report['maps_with_wild_species']}; unique literal species: {report['unique_species_references']}")
    for row in report["map_records"]:
        print(f"  {row['directory']}: {row['unique_species_references']} species / {row['encounter_slot_references']} slots / {row['wild_record_count']} records")
    print("STATIC SOURCE ONLY — not a claim of playable encounters or complete obtainability.")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Report: {args.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
