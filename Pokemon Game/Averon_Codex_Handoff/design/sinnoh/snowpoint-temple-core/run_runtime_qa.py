#!/usr/bin/env python3
"""Partial Temple stair QA; opt-in construction dedup, unchanged full final traversal."""
import argparse
import importlib.util
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
a=load('temple_height_qa',HERE.parent/'coronet-ascent/run_runtime_qa.py')
MAPS=tuple('MAP_SINNOH_SNOWPOINT_TEMPLE_'+f for f in ('1F','B1F','B2F','B3F','B4F','B5F'))
def run(args):
    sys.path.insert(0,str(ROOT/'Pokemon Game/scripts/claude_play'))
    import map_qa as qa
    old_maps=a.MAPS;old_warp=qa.Runner.warp;old_follower=qa.Runner.follower;old_main=qa.main
    if args.mode=='batch':load('temple_fast_qa',ROOT/'Pokemon Game/scripts/sinnoh_fast_batch_qa.py').install_batch_mode(qa)
    def main(argv):
        argv=list(argv)
        if '--save' in argv:argv[argv.index('--save')+1]='temple-core'
        return old_main(argv)
    qa.main=main;a.MAPS=MAPS
    try:return a.run(args)
    finally:a.MAPS=old_maps;qa.Runner.warp=old_warp;qa.Runner.follower=old_follower;qa.main=old_main
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('engine','rom','scratch','out','recipe'):p.add_argument('--'+n,required=True,type=Path)
    p.add_argument('--profile',required=True,choices=('normal','release'));p.add_argument('--mode',required=True,choices=('batch','final'));p.add_argument('--expect',type=Path);sys.exit(run(p.parse_args()))
