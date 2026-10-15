#!/usr/bin/env python3
"""Estimate level-evolution expansion from registered Averon source encounter/gift references.

IMPORTANT: This is a source analysis, not a gameplay obtainability certificate.
It deliberately considers ONLY plain EVO_LEVEL {level, species} edges. It does
not model experience caps, preprocessor switches, hidden forms, evolution
conditions, items, map reachability, starter exclusivity, or evolution cancel.
"""
import argparse
from collections import defaultdict, Counter, deque
import importlib.util
import json
from pathlib import Path
import re

ENTRY = re.compile(r'^\s*\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*$', re.M)
PLAIN = re.compile(r'\{\s*EVO_LEVEL\s*,\s*(\d+)\s*,\s*(SPECIES_[A-Z0-9_]+)\s*\}')
METHOD = re.compile(r'\{\s*(EVO_[A-Z0-9_]+)\s*,')
GIFT = re.compile(r'^\s*givemon\s+(SPECIES_[A-Z0-9_]+)\b', re.M)


def module_from(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_species_evolutions(text):
    """Conservatively extract only straightforward level-only evolution rows."""
    entries = list(ENTRY.finditer(text))
    level_edges = set()
    methods = Counter()
    for i, match in enumerate(entries):
        body = text[match.end():entries[i + 1].start() if i + 1 < len(entries) else len(text)]
        field = body.find('.evolutions')
        if field == -1:
            continue
        # Prevent accidentally scanning another source entry with no evo field.
        field_text = body[field:]
        for found in METHOD.finditer(field_text):
            methods[found.group(1)] += 1
        for found in PLAIN.finditer(field_text):
            level = int(found.group(1))
            if 1 <= level <= 100:
                level_edges.add((match.group(1), found.group(2), level))
    return level_edges, methods


def all_evolutions(engine):
    base = engine / 'src/data/pokemon/species_info'
    all_edges = set()
    methods = Counter()
    for path in sorted(base.glob('gen_[1-9]_families.h')):
        edges, seen = parse_species_evolutions(path.read_text(encoding='utf-8'))
        all_edges.update(edges)
        methods.update(seen)
    return all_edges, methods


def gift_references(engine, map_records):
    """Recognize givemon in scripts of registered maps; event gating is unknown."""
    by_map = {}
    for entry in map_records:
        path = engine / 'data/maps' / entry['directory'] / 'scripts.inc'
        if path.exists():
            matches = set(GIFT.findall(path.read_text(encoding='utf-8')))
            if matches:
                by_map[entry['map_id']] = sorted(matches)
    return by_map


def level_closure(sources, edges):
    graph = defaultdict(list)
    for origin, evolved, level in edges:
        graph[origin].append((evolved, level))
    found = set(sources)
    derived = {}
    queue = deque(sorted(sources))
    while queue:
        parent = queue.popleft()
        for child, at_level in sorted(graph[parent]):
            if child not in found:
                found.add(child)
                derived[child] = {'from': parent, 'level': at_level}
                queue.append(child)
    return found, derived


def create_report(project):
    engine = project / 'engine'
    companion = module_from(Path(__file__).with_name('audit-averon-map-encounters.py'), 'averon_map_audit_dependency')
    map_report = companion.create_report(engine)
    wild = set()
    for entry in map_report['map_records']:
        wild.update(entry['species_slot_counts'])
    gifts = gift_references(engine, map_report['map_records'])
    direct_gifts = set().union(*(set(items) for items in gifts.values())) if gifts else set()
    edges, methods = all_evolutions(engine)
    possible, derived = level_closure(wild | direct_gifts, edges)
    return {
        'interpretation': 'Hypothetical source reference and plain level-evolution closure; NOT gameplay obtainability.',
        'registered_map_count': map_report['registered_map_count'],
        'wild_source_species_count': len(wild),
        'gift_source_species_count': len(direct_gifts),
        'gift_references_by_map': gifts,
        'direct_species_references': sorted(wild | direct_gifts),
        'plain_level_evolution_edge_count': len(edges),
        'all_evolution_method_source_references': dict(sorted(methods.items())),
        'additional_plain_level_evolution_species': len(derived),
        'hypothetical_level_closure_species_count': len(possible),
        'derived_species': dict(sorted(derived.items())),
        'limitations': [
            'Givemon in a registered map may be inaccessible or mutually exclusive.',
            'All sources are counted whether or not map travel has been unlocked.',
            'Species families can be compile-time disabled or subject to conditional evolution branches.',
            'Only simple EVO_LEVEL edges are followed; items, special cases, genders and friendship are not modeled.',
            'The full Pokédex and nonlocal regions are not evaluated.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--json-out', type=Path)
    args = parser.parse_args()
    try:
        result = create_report(args.project)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        parser.exit(2, f'Evolution source audit failed: {exc}\n')
    for key in ('wild_source_species_count', 'gift_source_species_count', 'plain_level_evolution_edge_count',
                'additional_plain_level_evolution_species', 'hypothetical_level_closure_species_count'):
        print(f'{key}: {result[key]}')
    print('SOURCE ESTIMATE ONLY: no obtainability or runtime guarantee')
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
