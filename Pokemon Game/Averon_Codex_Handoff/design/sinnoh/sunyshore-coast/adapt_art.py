#!/usr/bin/env python3
"""Configure the existing guarded outdoor packer for the bounded coast source.

Reads permitted Averon graphics only. No converter, donor art or engine install.
"""
import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('sunyshore_existing_art', HERE.parent/'canalave-west/adapt_outdoor_art.py')
existing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(existing)
pack = existing.pack
MAPS = {'SunyshoreCity': (70,64), 'Route222': (92,32),
        'Route223': (34,124), 'PokmonLeague': (33,69)}
roles = json.loads((HERE/'art-map-roles.json').read_text())['maps']
if set(roles) != set(MAPS):
    raise ValueError('exact four-map art role set required')
FACADES = {n: [(tuple(a),tuple(b)) for a,b in roles[n]['facades']] for n in MAPS}
SECONDARY = {n: {int(k):v for k,v in roles[n]['secondary_remap'].items()} for n in MAPS}
BRIDGES = {n: set(roles[n]['wood_walkway_ids']) for n in MAPS}
existing.HERE = HERE
existing.MAPS = MAPS
existing.FACADES = FACADES
existing.SECONDARY = SECONDARY
existing.BRIDGES = BRIDGES
existing.templates.HERE = HERE
existing.templates.MAPS = MAPS
existing.templates.FACADES = FACADES
existing.templates.SECONDARY = SECONDARY
source = existing.source
desired_art = existing.desired_art


def build(engine, out):
    receipt = existing.build(engine, out)
    if receipt['elevation15_preserved'] != dict(SunyshoreCity=68, Route222=0, Route223=0, PokmonLeague=0):
        raise ValueError('source elevated walkway contract changed')
    receipt['status'] = 'EXISTING_AVERON_SUNYSHORE_ART_NOT_RUNTIME_ACCEPTANCE'
    receipt['art_roles_sha256'] = pack.accepted.base.sha((HERE/'art-map-roles.json').read_bytes())
    receipt['limits'] = [
        'Existing Averon General/Rustboro pixels and palettes only; no donor images/music',
        'Neutral stock facades/wood replace source buildings/solar walkways; not final visual equivalence',
        'All68 elevated cells, collision/elevation and complete behavior/layer words preserved',
        'No ocean foot traversal, Surf unlock, waterfall permission or natural League arrival claimed',
        'Unbuilt Route224 edge stays closed; no cave portal/story/services/encounters invented',
        'Off-engine art only: no ROM/native/mGBA/save/bridge priority or production acceptance']
    (Path(out)/'outdoor-art-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    result = build(args.engine, args.out)
    print(json.dumps({k: result[k] for k in ('verified_physics_behavior_cells','secondary_records','remaining_secondary_slots','elevation15_preserved')}, indent=2))
