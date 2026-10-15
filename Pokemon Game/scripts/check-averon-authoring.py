"""Verify regeneration does not keep changing native source or map/save IDs."""
from pathlib import Path
import hashlib, json, subprocess, sys
root=Path(__file__).resolve().parents[1]
author=root/'scripts/build-averon-coast.py'
def generate():subprocess.run([sys.executable,str(author)],check=True,capture_output=True)
def snapshot():
    engine=root/'engine'
    groups=json.loads((engine/'data/maps/map_groups.json').read_text())
    names=groups['gMapGroup_AveronOpening']
    paths=[engine/p for p in ('data/maps/map_groups.json','data/layouts/layouts.json',
        'src/data/trainers.party','src/data/wild_encounters.json','src/data/heal_locations.json',
        'src/data/region_map/region_map_sections.json','data/specials.inc',
        'src/new_game.c','src/battle_main.c','src/pokemon.c','include/constants/vars.h',
        'data/event_scripts.s','data/averon_optional_sidequests.inc',
        'data/scripts/debug.inc',
        'include/constants/flags.h','include/constants/opponents.h','include/config/battle.h')]
    for name in names:
        paths.extend([engine/f'data/maps/{name}/map.json',engine/f'data/maps/{name}/scripts.inc'])
        layout=engine/f'data/layouts/{name}'
        if layout.is_dir():paths.extend(layout.glob('*.bin'))
    return {str(p.relative_to(engine)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
generate();first=snapshot()
generate();second=snapshot()
changed=[p for p in first if first[p]!=second[p]]
if changed:raise SystemExit('FAIL: regeneration changes '+', '.join(changed))
print(f'PASS: {len(first)} authored source/map files stable across repeated regeneration.')
