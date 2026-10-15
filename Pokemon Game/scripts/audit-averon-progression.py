#!/usr/bin/env python3
"""Validate planned Averon routes, optional loops and badge-order access.

DESIGN-ONLY: the CSV route graph is a plan, not evidence of native map warps,
collision, cutscene triggers or in-game story gates. Traversal assumes paths
are bidirectional, except inaccessible edges gated by scenario conditions.
"""
import argparse
import csv
import json
from collections import deque
from pathlib import Path
import re

LOCKS = {'start', 'field_cut', 'water_gear', 'postleague', 'postcoup', 'story_finale'}
BADGE = re.compile(r'badge_([1-8])\Z')


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def validate(location_rows, route_rows, gym_rows):
    errors = []
    locations = [r['name'].strip() for r in location_rows]
    locset = set(locations)
    if len(locset) != len(locations):
        errors.append('Duplicate location name')
    identifiers = [r['id'] for r in route_rows]
    if len(set(identifiers)) != len(identifiers):
        errors.append('Duplicate route ID')
    for route in route_rows:
        if not route['id'].startswith('R') or not route['id'][1:].isdigit():
            errors.append('Invalid route ID: ' + route['id'])
        for side in ('from', 'to'):
            if route[side] not in locset:
                errors.append(f'{route["id"]}: unknown {side} endpoint {route[side]!r}')
        lock = route['unlock'].strip()
        if lock not in LOCKS and not BADGE.fullmatch(lock):
            errors.append(f'{route["id"]}: unrecognized unlock condition {lock!r}')
    numbers = []
    for gym in gym_rows:
        try:
            number = int(gym['number'])
        except ValueError:
            errors.append('Invalid Gym number: ' + gym['number'])
            continue
        numbers.append(number)
        if gym['city'] not in locset:
            errors.append(f'Gym {number}: missing city {gym["city"]!r}')
    if sorted(numbers) != list(range(1, 9)):
        errors.append('Expected exactly eight numbered Gyms (1–8)')
    if not any(r['name'] == 'Victory Isle' for r in location_rows):
        errors.append('Missing League location: Victory Isle')
    return errors


def is_open(unlock, badge_count, enabled):
    lock = BADGE.fullmatch(unlock)
    return badge_count >= int(lock.group(1)) if lock else unlock == 'start' or unlock in enabled


def walk(route_rows, badge_count=0, enabled=(), start='Saltmere'):
    """Reachable *design locations* and path records under one scenario."""
    if not 0 <= badge_count <= 8:
        raise ValueError('badge_count must be 0..8')
    enabled = set(enabled)
    unknown = enabled - LOCKS
    if unknown:
        raise ValueError('Unknown scenario abilities: ' + ', '.join(sorted(unknown)))
    neighbors = {}
    for route in route_rows:
        if is_open(route['unlock'], badge_count, enabled):
            neighbors.setdefault(route['from'], []).append((route['to'], route['id']))
            neighbors.setdefault(route['to'], []).append((route['from'], route['id']))
    queue = deque([start])
    visited = {start}
    via = {}
    while queue:
        current = queue.popleft()
        for destination, route_id in neighbors.get(current, []):
            if destination not in visited:
                visited.add(destination)
                via[destination] = {'from': current, 'route': route_id}
                queue.append(destination)
    return visited, via


def create_report(locations, routes, gyms):
    errors = validate(locations, routes, gyms)
    if errors:
        raise ValueError('\n'.join(errors))
    checkpoints = []
    gym_by_number = {int(g['number']): g for g in gyms}
    for badge_count in range(0, 9):
        reachable, via = walk(routes, badge_count)
        # Gym N must be visitable BEFORE obtaining badge N. Badge 1 at state 0.
        next_gym = gym_by_number.get(badge_count + 1)
        should_reach = next_gym['city'] if next_gym else 'Victory Isle'
        checkpoints.append({
            'badges': badge_count,
            'reachable_count': len(reachable),
            'reachable': sorted(reachable),
            'next_objective': should_reach,
            'next_objective_reachable': should_reach in reachable,
            'next_objective_path': reconstruct(via, should_reach) if should_reach in reachable else [],
        })
    extras = []
    for scenario, enabled in [
        ('cut', {'field_cut'}), ('water', {'water_gear'}),
        ('postcoup', {'postcoup'}), ('finale', {'story_finale'}),
        ('postgame', {'field_cut', 'water_gear', 'postleague', 'postcoup', 'story_finale'}),
    ]:
        visited, via = walk(routes, 8, enabled)
        extras.append({'scenario': scenario, 'reachable': sorted(visited), 'reachable_count': len(visited)})
    errors = [f'Before Badge {n+1}: cannot reach {row["next_objective"]}' for n, row in enumerate(checkpoints[:8]) if not row['next_objective_reachable']]
    if not checkpoints[8]['next_objective_reachable']:
        errors.append('After Badge 8: cannot reach Victory Isle')
    intended = {r['name'] for r in locations if r['name'] != 'Silverwatch Summit'}
    available_post = set(extras[-1]['reachable'])
    missing_post = sorted(intended - available_post)
    if missing_post:
        errors.append('Fully unlocked route graph misses: ' + ', '.join(missing_post))
    return {
        'status': 'PASS' if not errors else 'FAILED DESIGN GRAPH',
        'scope': 'design-only CSV graph, not implemented native world maps',
        'route_count': len(routes), 'location_count': len(locations),
        'badge_checkpoints': checkpoints,
        'extra_scenarios': extras,
        'planned_unreachable_locations': missing_post,
        'issues': errors,
        'exceptions': ['Silverwatch Summit is a separate Sinnoh Red endpoint, not connected by the Averon route table'],
    }


def reconstruct(via, dest):
    parts = []
    while dest in via:
        edge = via[dest]
        parts.append({'route': edge['route'], 'from': edge['from'], 'to': dest})
        dest = edge['from']
    return list(reversed(parts))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--json-out', type=Path)
    args = parser.parse_args(argv)
    data = args.project / 'Averon_Codex_Handoff/data'
    try:
        report = create_report(rows(data / 'locations.csv'), rows(data / 'route_network.csv'), rows(data / 'gyms.csv'))
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f'Invalid region progression data: {exc}\n')
    print(f"{report['status']}: {report['location_count']} locations, {report['route_count']} routes")
    for record in report['badge_checkpoints']:
        print(f"  Badge {record['badges']}: {record['reachable_count']} reachable; next {record['next_objective']}: {'YES' if record['next_objective_reachable'] else 'NO'}")
    for problem in report['issues']:
        print('ERROR:', problem)
    print('These results verify the design graph only, not playable map links.')
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return 0 if not report['issues'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
