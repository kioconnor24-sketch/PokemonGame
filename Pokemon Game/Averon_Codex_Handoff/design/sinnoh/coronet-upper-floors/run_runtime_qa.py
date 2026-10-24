#!/usr/bin/env python3
"""Reuse the tested short-pulse Coronet runner for ten source-verified DEV maps."""
import argparse
import importlib.util
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('upper_existing_qa',HERE.parent/'coronet-ascent/run_runtime_qa.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
MAPS=('MAP_SINNOH_MT_CORONET_2F', 'MAP_SINNOH_MT_CORONET_3F', 'MAP_SINNOH_MT_CORONET_OUTSIDE_SOUTH', 'MAP_SINNOH_MT_CORONET_OUTSIDE_NORTH', 'MAP_SINNOH_MT_CORONET_4F_ROOMS_1_AND_2', 'MAP_SINNOH_MT_CORONET_4F_ROOM_3', 'MAP_SINNOH_MT_CORONET_5F', 'MAP_SINNOH_MT_CORONET_6F', 'MAP_SINNOH_MT_CORONET_1F_SOUTH', 'MAP_SINNOH_MT_CORONET_1F_TUNNEL_ROOM')
def run(args):
    old=a.MAPS;a.MAPS=MAPS
    try:return a.run(args)
    finally:a.MAPS=old
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('engine','rom','scratch','out','recipe'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--profile',required=True,choices=('normal','release'));p.add_argument('--expect',type=Path)
    sys.exit(run(p.parse_args()))
