#!/usr/bin/env python3
"""Six real Forest/Chateau geography sources; neutral, source-only and art-free.

Reuses the existing connected-cluster stage and merged donor converter.
No story scripts, ghost events, NPCs, donor pixels or encounters are imported.
"""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('forest_reuse',HERE.parent/'eterna-cycle/stage_batch.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
MAPS={'EternaForest': (82, 84, '828c593d96ab44bea1362d6ae74cb601d16b98ba'), 'OldChateau_Entrance': (19, 17, 'b2b9df5c563591c49f503e76e6d86070de1a380e'), 'OldChateau_DiningRoom': (40, 10, '312060ed0a5009dd002dfa98d58c4f171ba0c487'), 'OldChateau_2F': (38, 14, '6838b9e34ed395577c8dab346d1c67422dae51c8'), 'OldChateau_SideRoom_1': (10, 10, 'd3881b97e1fd899bbed143f15bdba2223f7a12fb'), 'OldChateau_SideRoom_2': (10, 10, 'd3881b97e1fd899bbed143f15bdba2223f7a12fb')}


def build(donor,out):
    return base.build(donor,out,maps=MAPS,border_overrides={'OldChateau_SideRoom_2':dict(expected_sha256='aa298641e3346d9c7ac51454222ff057768946e61980fd82e4db65912df412fe',replacement_source_path='data/layouts/OldChateau_SideRoom_1/border.bin',reason='source SideRoom2 erroneously uses General trees468/469/476/477 beyond its 8-record Building primary; identical SideRoom1 geometry supplies the valid Building border')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--donor',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.donor,args.out),indent=2))
