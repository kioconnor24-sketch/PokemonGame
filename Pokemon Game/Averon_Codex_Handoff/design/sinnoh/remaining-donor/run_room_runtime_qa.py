#!/usr/bin/env python3
"""Two separate real stair pairs, reusing merged source-verified height-aware QA.

The two houses are intentionally disconnected; separate fixture entries do not
pretend that their closed exterior doors are naturally accessible from town.
"""
import argparse
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('room_height_qa',HERE.parent/'celestic-north/run_runtime_qa.py')
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
PAIRS={'main':('MAP_TWINLEAF_TOWN_MAIN_HOUSE_1F','MAP_TWINLEAF_TOWN_MAIN_HOUSE_2F'),
       'rival':('MAP_TWINLEAF_TOWN_RIVALS_HOUSE_F1','MAP_TWINLEAF_TOWN_RIVALS_HOUSE_F2')}


def run(args):
    previous=shared.MAPS;shared.MAPS=PAIRS[args.pair]
    try:return shared.run(args)
    finally:shared.MAPS=previous


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('engine','rom','scratch','out','recipe'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--profile',required=True,choices=('normal','release'))
    p.add_argument('--pair',required=True,choices=tuple(PAIRS));p.add_argument('--expect',type=Path)
    sys.exit(run(p.parse_args()))
