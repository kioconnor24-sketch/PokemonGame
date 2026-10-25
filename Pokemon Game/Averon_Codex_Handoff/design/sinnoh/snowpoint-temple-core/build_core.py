#!/usr/bin/env python3
"""Original neutral northern stair chambers via existing painter; no puzzle acceptance."""
import argparse
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('temple_existing_cave',HERE.parent/'victory-road-shell/build_shell.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
NAMES={f:'SinnohSnowpointTemple_'+f.upper() for f in ('1f','b1f','b2f','b3f','b4f','b5f')}
ORIGINAL_CONSTRUCT=a.construct
IDS={n:'MAP_SINNOH_SNOWPOINT_TEMPLE_'+f.upper() for f,n in NAMES.items()}

def construct(recipe,reference):
    return ORIGINAL_CONSTRUCT(recipe,reference,NAMES,IDS,'MAP_HEADER_SNOWPOINT_TEMPLE_')

def build(engine,out):
    # Own module instance; shared painter source is unchanged.
    original=a.construct;a.construct=construct;a.HERE=HERE
    try:return a.build(engine,out)
    finally:a.construct=original

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);args=p.parse_args();build(args.engine,args.out)
