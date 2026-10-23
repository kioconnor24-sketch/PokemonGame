#!/usr/bin/env python3
"""Neutral shared stock interior test art over pinned donor floor plans.

Reuses the merged central packer. No map conversion or donor asset ingestion.
Stairs/portals use stock mats; neutral counters/walls are not final room art.
"""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('remaining_interior_shared',HERE.parent/'hearthome-solaceon/adapt_gate_art.py')
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
MAPS={'Route222_Access': (13, 9),
 'ValleyWindoworks_Indoor': (22, 16),
 'TwinleafTown_MainHouse_1F': (11, 9),
 'TwinleafTown_MainHouse_2F': (9, 8),
 'Twinleaf_Town_RivalsHouse_F1': (11, 9),
 'Twinleaf_Town_RivalsHouse_F2': (9, 8),
 'SandgemTown_RivalHouse_F1': (11, 9),
 'SandgemTown_RivalHouse_F2': (9, 8),
 'JubilifeCity_JubilifeTV_F1': (16, 10),
 'JubilifeCity_JubilifeTV_F2': (16, 10),
 'JubilifeCity_JubilifeTV_F3': (16, 10),
 'JubilifeCity_JubilifeTV_F4': (16, 10),
 'JubilifeCity_PoketchCompany_F1': (19, 9),
 'JubilifeCity_PoketchCompany_F2': (19, 9),
 'JubilifeCity_PoketchCompany_F3': (19, 9),
 'JubilifeCity_Flat1_F1': (14, 9),
 'JubilifeCity_Flat1_F2': (14, 9),
 'JubilifeCity_Flat1_F3': (14, 9),
 'JubilifeCity_Flat2_F1': (14, 9),
 'JubilifeCity_Flat2_F2': (14, 9),
 'JubilifeCity_Flat2_F3': (14, 9),
 'JubilifeCity_Flat3_F1': (14, 9),
 'JubilifeCity_Flat3_F2': (14, 9),
 'JubilifeCity_Flat3_F3': (14, 9),
 'OreburghCity_Flat1_F1': (14, 8),
 'OreburghCity_Flat1_F2': (14, 8),
 'OreburghCity_Flat2_F1': (14, 8),
 'OreburghCity_Flat2_F2': (14, 8),
 'OreburghCity_PokemonCenter_1F': (14, 9),
 'OreburghCity_PokemonCenter_2F': (14, 10),
 'FloaromaTown_PokemonCenter_1F': (14, 9),
 'FloaromaTwon_PokemonCenter_2F': (14, 10),
 'EternaCity_Flat1_F1': (14, 8),
 'EternaCity_Flat1_F2': (14, 8),
 'EternaCity_Flat1_F3': (14, 8),
 'EternaCity_PokemonCenter_F1': (14, 9),
 'EternaCity_PokemonCenter_F2': (14, 10),
 'EternaCity_GalacticBuilding_1F': (16, 12),
 'EternaCity_GalacticBuilding_2F': (16, 12),
 'EternaCity_GalacticBuilding_3F': (16, 12),
 'EternaCity_GalacticBuilding_4F': (16, 12),
 'EternaCity_GalacticBuilding_B1F': (16, 12)}
ANCHORS={'Route222_Access': [(1, 5), (11, 5)],
 'ValleyWindoworks_Indoor': [(10, 15), (11, 15)],
 'TwinleafTown_MainHouse_1F': [(8, 2)],
 'TwinleafTown_MainHouse_2F': [(7, 1)],
 'Twinleaf_Town_RivalsHouse_F1': [(2, 2)],
 'Twinleaf_Town_RivalsHouse_F2': [(1, 1)],
 'SandgemTown_RivalHouse_F1': [(2, 2)],
 'SandgemTown_RivalHouse_F2': [(1, 1)],
 'JubilifeCity_JubilifeTV_F1': [(1, 2)],
 'JubilifeCity_JubilifeTV_F2': [(1, 2), (4, 2)],
 'JubilifeCity_JubilifeTV_F3': [(4, 2), (1, 2)],
 'JubilifeCity_JubilifeTV_F4': [(1, 2)],
 'JubilifeCity_PoketchCompany_F1': [(14, 1)],
 'JubilifeCity_PoketchCompany_F2': [(14, 1), (2, 1)],
 'JubilifeCity_PoketchCompany_F3': [(2, 1)],
 'JubilifeCity_Flat1_F1': [(3, 1)],
 'JubilifeCity_Flat1_F2': [(3, 1), (1, 1)],
 'JubilifeCity_Flat1_F3': [(1, 1)],
 'JubilifeCity_Flat2_F1': [(3, 1)],
 'JubilifeCity_Flat2_F2': [(3, 1), (1, 1)],
 'JubilifeCity_Flat2_F3': [(1, 1)],
 'JubilifeCity_Flat3_F1': [(3, 1)],
 'JubilifeCity_Flat3_F2': [(3, 1), (1, 1)],
 'JubilifeCity_Flat3_F3': [(1, 1)],
 'OreburghCity_Flat1_F1': [(2, 1)],
 'OreburghCity_Flat1_F2': [(2, 1)],
 'OreburghCity_Flat2_F1': [(2, 1)],
 'OreburghCity_Flat2_F2': [(2, 1)],
 'OreburghCity_PokemonCenter_1F': [(1, 6)],
 'OreburghCity_PokemonCenter_2F': [(1, 6)],
 'FloaromaTown_PokemonCenter_1F': [(1, 6)],
 'FloaromaTwon_PokemonCenter_2F': [(1, 6)],
 'EternaCity_Flat1_F1': [(1, 1)],
 'EternaCity_Flat1_F2': [(1, 1), (4, 1)],
 'EternaCity_Flat1_F3': [(4, 1)],
 'EternaCity_PokemonCenter_F1': [(1, 6)],
 'EternaCity_PokemonCenter_F2': [(1, 6)],
 'EternaCity_GalacticBuilding_1F': [(12, 1), (3, 1)],
 'EternaCity_GalacticBuilding_2F': [(12, 1), (3, 1)],
 'EternaCity_GalacticBuilding_3F': [(12, 1), (3, 1)],
 'EternaCity_GalacticBuilding_4F': [(12, 1)],
 'EternaCity_GalacticBuilding_B1F': [(3, 1)]}


def build(engine,out):
    receipt=shared.build(engine,out,source_root=HERE,maps=MAPS,expected_anchors=ANCHORS)
    receipt['status']='NEUTRAL_SHARED_AVERON_INTERIOR_TEST_ART_NOT_FINAL_OR_RUNTIME_ACCEPTANCE'
    receipt['limits'] += ['Shared stock floor/wall/counter/mat adaptation, not final donor appearance',
        'Every retained stair/door portal uses a mat; labels/services/story remain absent',
        'Closed exterior exits remain collision barriers; no natural accessibility claimed']
    (Path(out)/'gate-art-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    args=p.parse_args();r=build(args.engine,args.out)
    print(json.dumps(dict(maps=len(MAPS),cells=r['verified_physics_behavior_cells'],secondary_records=r['secondary_records']),indent=2))
