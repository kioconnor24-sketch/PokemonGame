#!/usr/bin/env python3
"""Inventory the 8-bit map-section / met-location namespace (read-only).

Legacy map sections (MAPSEC_*) retain their original order in
src/data/region_map/region_map_sections.json. The numeric value is what a
saved Pokemon keeps in its 8-bit metLocation and what MapHeader stores in its
8-bit regionMapSectionId; 0xFD-0xFF are reserved met-location codes
(gametypes.h, constants/region_map_sections.h). MAPSEC_NONE stays 215; approved new sections explicitly allocate 216..252.

For every section this reports which maps use it (Averon's registered group
versus upstream maps), and which source files name it. It allocates nothing,
renames nothing and is not a decision: a section that no Averon map uses and
no behavioural code names is only a *candidate* for a future owner-approved
reuse. Whether old saves can contain a value is judged from the maps that
assign it, not proven here.
"""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

DEFAULT_MAP_GROUP = "gMapGroup_AveronOpening"
SECTIONS_JSON = "src/data/region_map/region_map_sections.json"
RESERVED_MET_CODES = {0xFD: "METLOC_SPECIAL_EGG", 0xFE: "METLOC_IN_GAME_TRADE",
                      0xFF: "METLOC_FATEFUL_ENCOUNTER"}
FIRST_RESERVED = min(RESERVED_MET_CODES)
TOKEN = re.compile(r"\bMAPSEC_[A-Z0-9_]+\b")
# Files whose MAPSEC references are per-section lookup tables (names, region
# map layout, popup themes, previews, landmarks) rather than behaviour. A
# heuristic for triage, reported separately; it does not prove a file inert.
TABLE_FILES = frozenset({
    "src/region_map.c", "src/map_name_popup.c", "src/landmark.c",
    "src/map_preview_screen.c", "src/pokenav_match_call_data.c",
})
TABLE_PREFIXES = ("src/data/region_map/",)


def is_table(rel):
    return rel in TABLE_FILES or rel.startswith(TABLE_PREFIXES)
GENERATED = frozenset({"include/constants/region_map_sections.h"})
SCAN_SUFFIXES = (".c", ".h", ".inc", ".s", ".json")
SCAN_DIRS = ("src", "include", "data")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sections(engine):
    data = read_json(engine / SECTIONS_JSON)
    entries = data["map_sections"] if isinstance(data, dict) else data
    ids = [entry["id"] for entry in entries]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate MAPSEC ids in region_map_sections.json")
    for entry in entries:
        if "region" in entry and (not isinstance(entry["region"], str)
                                  or entry["region"] not in ENGINE_REGIONS | {"REGION_NONE"}):
            raise ValueError(f"{entry['id']}: invalid region metadata; use a declared REGION_* enum")
    manifest = engine / "src/data/region_map/region_map_sections.legacy.json"
    if manifest.is_file():
        legacy = read_json(manifest)
        if not isinstance(legacy, list) or len(legacy) != 215 or not 215 <= len(entries) <= 252:
            raise ValueError("expected 215 legacy entries and at most 37 new named sections")
        for index, entry in enumerate(entries):
            expected = index if index < 215 else index + 1
            value = entry.get("value", expected)
            if type(value) is not int or value != expected:
                raise ValueError(f"{entry['id']}: duplicate, sparse, reserved or moved value")
            if not re.fullmatch(r"MAPSEC_[A-Z0-9_]+", entry['id']) or entry['id'] in {"MAPSEC_NONE", "MAPSEC_COUNT"}:
                raise ValueError("invalid or reserved section identifier")
            if index < 215:
                old = legacy[index]
                if old['value'] != index or old['id'] != entry['id'] or old['name'] != entry.get('name') or 'region' in entry:
                    raise ValueError(f"{entry['id']}: legacy value, name or region changed")
            elif ('value' not in entry or entry.get('region') not in ENGINE_REGIONS
                  or not isinstance(entry.get('name'), str) or not entry['name']):
                raise ValueError(f"{entry['id']}: new section requires explicit value, name and engine region")
    elif (any('value' in e for e in entries)
          or (engine / 'tools/jsonproc/map_sections.h').is_file()):
        raise ValueError("missing frozen legacy manifest")
    # Also supports inventories of historical implicit-only trees.
    return [dict(entry, value=entry.get('value', index)) for index, entry in enumerate(entries)]


def section_none(engine, entries):
    return 215 if (engine / 'src/data/region_map/region_map_sections.legacy.json').is_file() else len(entries)


def map_sections(engine, group):
    """{map directory: (section, in Averon group)} for every map.json."""
    groups = read_json(engine / "data/maps/map_groups.json")
    averon = set(groups.get(group, []))
    result = {}
    for path in sorted((engine / "data/maps").glob("*/map.json")):
        data = read_json(path)
        result[path.parent.name] = (data.get("region_map_section"), path.parent.name in averon)
    return result


def references(engine):
    """{MAPSEC token: {relative file: count}} over source, headers and data."""
    found = defaultdict(lambda: defaultdict(int))
    for top in SCAN_DIRS:
        for path in sorted((engine / top).rglob("*")):
            if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
                continue
            rel = path.relative_to(engine).as_posix()
            if rel in GENERATED or rel == SECTIONS_JSON or rel.startswith("data/maps/"):
                continue  # definitions and map assignments are counted elsewhere
            for token in TOKEN.findall(path.read_text(encoding="utf-8", errors="replace")):
                found[token][rel] += 1
    return found


FLY_TABLE_FILE = "src/region_map.c"
FLY_TABLE = "sMapHealLocations"
LAYOUT_GLOB = "src/data/region_map/region_map_layout*.h"
SPECIES_INFO_GLOB = "src/data/pokemon/species_info/*.h"
# GetRegionForSectionId (src/region_map.c): explicit ROM metadata overrides
# the legacy [KANTO_MAPSEC_START, MAPSEC_SPECIAL_AREA) Kanto / else Hoenn rule.
KANTO_RANGE = ("MAPSEC_PALLET_TOWN", "MAPSEC_SPECIAL_AREA")
ENGINE_REGIONS = frozenset("REGION_" + name for name in (
    "KANTO", "JOHTO", "HOENN", "SINNOH", "UNOVA", "KALOS", "ALOLA",
    "GALAR", "HISUI", "PALDEA"))
REGION_CONDITION = re.compile(r"\b(IF_(?:NOT_)?REGION)\s*,\s*(REGION_[A-Z_]+)")


def fly_rows(engine):
    """Sections with a row in sMapHealLocations. FilterFlyDestination and
    SetFlyDestination bounds-check against the table, so a section past its
    last row has no Fly destination. Empty when the table is absent."""
    path = engine / FLY_TABLE_FILE
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    start = text.find(FLY_TABLE + "[]")
    if start < 0:
        return set()
    body = text[start:text.find("\n};", start)]
    return set(re.findall(r"\[(MAPSEC_[A-Z0-9_]+)\]\s*=", body))


def town_map_cells(engine):
    """{section id: cells} over the region-map layout grids (Hoenn, Kanto, Sevii)."""
    cells = defaultdict(int)
    for path in sorted(engine.glob(LAYOUT_GLOB)):
        for token in TOKEN.findall(path.read_text(encoding="utf-8", errors="replace")):
            cells[token] += 1
    return cells


def region_conditioned_evolutions(engine):
    """{'IF_REGION REGION_X': count} in species data: what a section's engine
    region (GetCurrentRegion) changes for evolution."""
    counts = defaultdict(int)
    for path in sorted(engine.glob(SPECIES_INFO_GLOB)):
        for condition, region in REGION_CONDITION.findall(path.read_text(encoding="utf-8", errors="replace")):
            counts[f"{condition} {region}"] += 1
    return dict(sorted(counts.items()))


def engine_region(value, values, declared=None):
    """The engine region GetRegionForSectionId gives this section's value."""
    if isinstance(declared, str) and declared in ENGINE_REGIONS:
        return declared
    start, end = (values.get(name) for name in KANTO_RANGE)
    if start is not None and end is not None and start <= value < end:
        return "REGION_KANTO"
    return "REGION_HOENN"


def inventory(engine, group=DEFAULT_MAP_GROUP):
    entries = sections(engine)
    maps = map_sections(engine, group)
    refs = references(engine)
    values = {entry["id"]: entry["value"] for entry in entries}
    fly = fly_rows(engine)
    cells = town_map_cells(engine)
    rows = []
    for entry in entries:
        value = entry["value"]
        ident = entry["id"]
        averon_maps = sorted(m for m, (sec, mine) in maps.items() if sec == ident and mine)
        other_maps = sorted(m for m, (sec, mine) in maps.items() if sec == ident and not mine)
        files = refs.get(ident, {})
        behaviour = sorted(f for f in files if not is_table(f))
        rows.append(dict(
            value=value, id=ident, name=entry.get("name"),
            averon_maps=averon_maps, upstream_map_count=len(other_maps),
            table_files=sorted(f for f in files if is_table(f)),
            behaviour_files=behaviour,
            saved_by_averon=bool(averon_maps),
            reuse_candidate=not averon_maps and not behaviour,
            fly_row=ident in fly,
            town_map_cells=cells.get(ident, 0),
            engine_region=engine_region(value, values, entry.get("region")),
        ))
    none_value = section_none(engine, entries)
    unknown = sorted({sec for sec, _ in maps.values() if sec and sec not in {e["id"] for e in entries}
                      and sec != "MAPSEC_NONE"})
    averon_rows = [r for r in rows if r["averon_maps"]]
    return dict(
        fly_table_rows=len(fly),
        fly_table_end=max((values[s] for s in fly if s in values), default=-1) + 1,
        averon_without_fly=[r["id"] for r in averon_rows if not r["fly_row"]],
        averon_off_town_map=[r["id"] for r in averon_rows if not r["town_map_cells"]],
        averon_engine_regions=sorted({r["engine_region"] for r in averon_rows}),
        region_conditioned_evolutions=region_conditioned_evolutions(engine),
        sections=len(entries), mapsec_none=none_value,
        spare_codes_before_reserved=max(0, FIRST_RESERVED - len(entries) - 1),
        reserved_met_codes={f"0x{k:02X}": v for k, v in sorted(RESERVED_MET_CODES.items())},
        averon_group=group,
        averon_map_count=sum(1 for _, mine in maps.values() if mine),
        averon_sections=[r["id"] for r in rows if r["averon_maps"]],
        upstream_only_sections=sum(1 for r in rows if not r["averon_maps"] and r["upstream_map_count"]),
        unassigned_sections=sum(1 for r in rows if not r["averon_maps"] and not r["upstream_map_count"]),
        reuse_candidates=sum(1 for r in rows if r["reuse_candidate"]),
        behaviour_bound=sum(1 for r in rows if r["behaviour_files"]),
        unknown_map_sections=unknown,
        rows=rows,
    )


def check_pins(engine, pins):
    """Errors if a pinned (saved) section value moved, or the namespace would
    reach the reserved met-location codes."""
    values = {entry["id"]: entry["value"] for entry in sections(engine)}
    errors = [f"{ident}: pinned {want}, now {values.get(ident, 'missing')}"
              for ident, want in sorted(pins.items()) if values.get(ident) != want]
    if len(values) >= FIRST_RESERVED:  # Historical implicit-only namespaces too.
        errors.append(f"MAPSEC_NONE would be {len(values)}, colliding with reserved met codes 0xFD-0xFF")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--engine", type=Path, default=Path(__file__).resolve().parents[1] / "engine")
    parser.add_argument("--group", default=DEFAULT_MAP_GROUP)
    parser.add_argument("--json", type=Path, help="write the full inventory here")
    parser.add_argument("--check-pins", type=Path, nargs="?", const=Path(__file__).with_name("averon-mapsec-pins.json"),
                        help="fail if a pinned saved section value moved (default pin file next to this script)")
    parser.add_argument("--planned-area-register", type=Path,
                        help="audit an explicit per-name planning scenario from TrackerKey/LocationOrZone CSV")
    parser.add_argument("--origin-aliases", type=Path,
                        help="optional JSON object of area key to proposed shared origin name; allocates nothing")
    parser.add_argument("--additional-origins", type=Path,
                        help="optional JSON list of extra named child origins absent from the area register")
    parser.add_argument("--origin-reserve", type=int, default=0,
                        help="reserve byte codes for other future names (Averon/children), not an allocation")
    parser.add_argument("--origin-kinds",
                        help="optional comma-separated register Kind subset, e.g. SETTLEMENT,ROUTE")
    args = parser.parse_args(argv)
    if (args.origin_aliases or args.additional_origins or args.origin_reserve
            or args.origin_kinds is not None) and not args.planned_area_register:
        parser.error("origin scenario options require --planned-area-register")
    if args.check_pins:
        errors = check_pins(args.engine, read_json(args.check_pins)["pins"])
        for error in errors:
            print("PIN ERROR: " + error)
        if errors:
            return 1
        print(f"{len(read_json(args.check_pins)['pins'])} saved section values unchanged")
    report = inventory(args.engine, args.group)
    scenario_status = 0
    if args.planned_area_register:
        from averon_origin_demand import origin_demand, read_area_register
        try:
            all_rows = read_area_register(args.planned_area_register)
            kinds = set()
            rows = all_rows
            if args.origin_kinds is not None:
                kinds = {kind.strip() for kind in args.origin_kinds.split(",") if kind.strip()}
                if not kinds or kinds - {row.get("Kind") for row in all_rows}:
                    raise ValueError("origin kinds must name existing register Kind values")
                rows = [row for row in all_rows if row.get("Kind") in kinds]
            demand = origin_demand(rows, sections(args.engine),
                                   aliases=read_json(args.origin_aliases) if args.origin_aliases else None,
                                   additional=read_json(args.additional_origins) if args.additional_origins else (),
                                   reserve=args.origin_reserve)
            demand["source_register_areas"] = len(all_rows)
            demand["selected_kinds"] = sorted(kinds)
        except (ValueError, OSError) as error:
            parser.error(str(error))
        report["planned_origin_demand"] = demand
    if args.json:
        args.json.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"{report['sections']} named sections, MAPSEC_NONE={report['mapsec_none']}, "
          f"{report['spare_codes_before_reserved']} spare codes before 0xFD")
    print(f"Averon group {report['averon_group']}: {report['averon_map_count']} maps using "
          f"{len(report['averon_sections'])} sections: {', '.join(report['averon_sections'])}")
    print(f"{report['upstream_only_sections']} sections used only by upstream maps, "
          f"{report['unassigned_sections']} by no map; {report['behaviour_bound']} named outside lookup tables; "
          f"{report['reuse_candidates']} reuse candidates (owner decision required)")
    print(f"Fly table {FLY_TABLE}: {report['fly_table_rows']} rows, ends before value {report['fly_table_end']}; "
          f"Averon sections without a Fly row: {', '.join(report['averon_without_fly']) or 'none'}")
    print(f"Averon sections on no Town Map layout: {', '.join(report['averon_off_town_map']) or 'none'}; "
          f"engine region for Averon sections: {', '.join(report['averon_engine_regions']) or 'none'}")
    print("region-conditioned evolutions: " + (", ".join(f"{k} x{v}" for k, v in
                                                      report["region_conditioned_evolutions"].items()) or "none"))
    if args.planned_area_register:
        demand = report["planned_origin_demand"]
        print(f"PLANNING SCENARIO: {demand['registered_areas']} areas / "
              f"{demand['distinct_proposed_names']} distinct names; "
              f"{demand['new_names_required']} new + {demand['other_future_reserve']} reserved vs "
              f"{demand['remaining_ordinary_codes']} available; shortfall {demand['shortfall']}")
        print("No IDs allocated; child maps and future Averon names are not a complete inventory.")
        if not demand["fits_current_byte_pool"]:
            print("PLANNING BUDGET EXCEEDED: owner origin-policy decision required, not a current ROM failure")
            scenario_status = 1
    if report["unknown_map_sections"]:
        print("maps name unknown sections: " + ", ".join(report["unknown_map_sections"]))
        return 1
    return scenario_status


if __name__ == "__main__":
    sys.exit(main())
