#!/usr/bin/env python3
"""Audit the atlas SOURCE layer (sinnoh-atlas.json) and print the adjacency tables used in SINNOH_ATLAS.md.

Checks: every compass link names a known area (or is reported as external); links are reciprocal
(A north->B implies B south->A); and lists areas with a single link (dead ends / spurs) and areas
known only by a location relation. --self-test drops one reciprocal side and requires it to be caught.
"""
import copy
import json
import sys
from pathlib import Path

OPP = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east',
       'northeast': 'southwest', 'southwest': 'northeast', 'northwest': 'southeast', 'southeast': 'northwest'}


def audit(atlas):
    names = {r['name']: r for r in atlas['areas']}
    alias = {'Cycling Road': 'Route 206'}   # the register's Cycling Road row is Route 206's page
    issues, external, links = [], set(), []
    for r in atlas['areas']:
        if r['name'] in alias:
            continue
        for d, targets in r.get('neighbours', {}).items():
            for t in targets:
                t = alias.get(t, t)
                links.append((r['name'], d, t))
                if t not in names:
                    external.add(t)
                    continue
                if not names[t].get('neighbours'):
                    continue   # target page has no compass fields (landmark infobox): one-sided by format
                back = names[t].get('neighbours', {}).get(OPP[d], [])
                if r['name'] not in back:
                    issues.append(f"{r['name']} {d} -> {t}, but {t} has no {OPP[d]} -> {r['name']}")
    degree = {}
    for a, _, b in links:
        degree[a] = degree.get(a, 0) + 1
    spurs = sorted(n for n, k in degree.items() if k == 1)
    only_relation = sorted(r['name'] for r in atlas['areas'] if not r.get('neighbours') and r.get('located'))
    return issues, sorted(external), spurs, only_relation, links


def main():
    atlas = json.loads(Path(__file__).with_name('sinnoh-atlas.json').read_text())
    issues, external, spurs, only_rel, links = audit(atlas)
    print(f'{len(links)} compass links; {len(issues)} non-reciprocal; {len(external)} external names')
    for i in issues:
        print('  NON-RECIPROCAL:', i)
    print('  external:', ', '.join(external))
    print('  single-link areas:', ', '.join(spurs))
    print('  relation-only areas:', len(only_rel))
    ok = True
    if '--self-test' in sys.argv:
        bad = copy.deepcopy(atlas)
        r = next(a for a in bad['areas'] if a['name'] == 'Twinleaf Town')
        r['neighbours'] = {'south': ['Route 201']}   # wrong side: Route 201 is north of Twinleaf
        caught = any('Route 201 south -> Twinleaf Town' in i for i in audit(bad)[0])
        print('mutation (Twinleaf link on the wrong side):', 'caught' if caught else 'MISSED')
        ok = caught
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
