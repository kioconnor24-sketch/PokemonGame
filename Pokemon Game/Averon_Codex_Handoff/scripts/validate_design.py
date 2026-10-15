#!/usr/bin/env python3
"""Static, offline lint for Pokémon Averon design CSVs.

DOES NOT compile a GBA ROM or prove map scripts work. Avoid calling this a ROM test.
"""
from pathlib import Path
from collections import defaultdict, deque
import csv, sys
ROOT=Path(__file__).resolve().parents[1]
errors=[]; warnings=[]

def read_csv(name):
    with (ROOT/'data'/name).open(newline='',encoding='utf-8') as f:
        return list(csv.DictReader(f))

places=read_csv('locations.csv'); routes=read_csv('route_network.csv')
gyms=read_csv('gyms.csv'); curve=read_csv('level_curve.csv')
legends=read_csv('legendary_quests.csv'); habitats=read_csv('habitat_examples.csv')
place_names={r['name'] for r in places}
if len(place_names)!=len(places): errors.append('Duplicate location names')
if len(routes)!=len({r['id'] for r in routes}): errors.append('Duplicate route IDs')
for r in routes:
    for key in ('from','to'):
        if r[key] not in place_names:
            errors.append(f"{r['id']}: unknown {key} '{r[key]}'")
    if r['from']==r['to']: errors.append(f"{r['id']}: self-loop")
for i,r in enumerate(gyms,1):
    if int(r['number'])!=i: errors.append('Gym order must be sequential 1..8')
    if r['city'] not in place_names: errors.append(f"Gym {i} city unknown")
    if int(r['level_cap_before_badge'])>100: errors.append(f"Gym {i} cap >100")
if len(gyms)!=8: errors.append(f'Expected 8 Averon Gyms, found {len(gyms)}')
if [r['city'] for r in gyms[5:7]]!=['Palehaven','Crownspine']:
    errors.append('Gyms 6/7 must be northern Palehaven/Crownspine')
if gyms[7]['city']!='Ashfall': errors.append('Gym 8 must be Ashfall')
if any(r['city']=='Vesper' for r in gyms): errors.append('Vesper must not have a Gym')
caps=[int(r['level_cap_before_badge']) for r in gyms]+[int(r['player_cap']) for r in curve]
if any(a>=b for a,b in zip(caps,caps[1:])): errors.append('Gym/story caps must strictly increase')
if caps[-1]!=100: errors.append('Red must be level 100 final cap')
if 'Red' not in curve[-1]['milestone']: errors.append('Final milestone must be Red')
if len(legends)<25: warnings.append('Legendary quest arcs less than 25: check if all species represented')
if len(habitats)<8: warnings.append('Habitat spreadsheet small')

# Main expected geographical traversal. These are intentional distinct connections.
main=['Saltmere','Windrow Hamlet','Alderfield','Breakwater','Coralside','Mossveil','Rillfall Outpost','Slateford','Juniper Rest','Sunscar','Vesper','Frostmere','Palehaven','Crownspine','Vesper','Gullhaven','Ashfall','Victory Isle']
edges=defaultdict(list)
for r in routes: edges[frozenset((r['from'],r['to']))].append(r)
for a,b in zip(main,main[1:]):
    if frozenset((a,b)) not in edges:
        errors.append(f'Missing mandatory contiguous main-travel edge {a} <-> {b}')

# End-to-end connectivity when all flags unlock. Every initial node should have route.
adj=defaultdict(set)
for r in routes:
    adj[r['from']].add(r['to']);adj[r['to']].add(r['from'])
seen={'Saltmere'}; queue=deque(['Saltmere'])
while queue:
    curr=queue.popleft()
    for n in adj[curr]:
        if n not in seen:
            seen.add(n);queue.append(n)
# The Red summit is in the planned SECOND region, not connected to the Averon-only CSV.
second_region_nodes={'Silverwatch Summit'}
missing=place_names-seen-second_region_nodes
if missing: errors.append(f'Locations unreachable after all Averon unlocks: {sorted(missing)}')
if not second_region_nodes <= place_names: errors.append('Sinnoh postgame summit stub missing')

# Stage availability: locked routes for future badges cannot sneak into the main path.
expected_route_unlock={'Saltmere|Windrow Hamlet':'start', 'Windrow Hamlet|Alderfield':'start',
'Alderfield|Breakwater':'badge_1','Breakwater|Coralside':'badge_2',
'Coralside|Mossveil':'badge_2', 'Mossveil|Rillfall Outpost':'badge_3',
'Rillfall Outpost|Slateford':'badge_3','Slateford|Juniper Rest':'badge_4',
'Juniper Rest|Sunscar':'badge_4','Sunscar|Vesper':'badge_5',
'Vesper|Frostmere':'badge_5','Frostmere|Palehaven':'badge_5',
'Palehaven|Crownspine':'badge_6','Crownspine|Vesper':'badge_7',
'Vesper|Gullhaven':'badge_7','Gullhaven|Ashfall':'badge_7',
'Ashfall|Victory Isle':'badge_8'}
for pair,unlock in expected_route_unlock.items():
    a,b=pair.split('|'); options=edges.get(frozenset((a,b)),[])
    if options and not any(edge['unlock']==unlock for edge in options):
        errors.append(f"Unlock mismatch {pair}: got {[r['unlock'] for r in options]}, expected {unlock}")

# Simple project-specific assertions
if not any('Jirachi' in r['species'] and 'department-store key' in r['location_and_trigger'] for r in legends):
    errors.append('Jirachi department store key quest missing')
if not any('Heatran' in r['species'] and 'Ashfall caldera' in r['location_and_trigger'] for r in legends):
    errors.append('Heatran Ashfall caldera quest missing')
if not any(r['name']=='Threshold Annex' for r in places): errors.append('Threshold Annex missing')

print('Averon static design validation')
print(f"{len(places)} named locations | {len(routes)} route edges | {len(gyms)} Gyms | {len(legends)} legendary arcs | {len(habitats)} sample habitats")
for w in warnings: print('WARNING:', w)
for e in errors: print('ERROR:',e)
if errors:
    print(f'FAILED: {len(errors)} error(s). This checks design data only.');sys.exit(1)
print('PASS: design CSV integrity and end-to-end connectivity. NOT an executable game or emulator test.')
