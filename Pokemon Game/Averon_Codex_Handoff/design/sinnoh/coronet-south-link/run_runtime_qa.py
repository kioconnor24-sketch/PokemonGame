#!/usr/bin/env python3
"""Ten-map Coronet QA: opt-in unique reciprocal construction traversal, full final unchanged.

The existing elevation-aware follower probes remain explicit in this bespoke
runner. Batch deduplicates only the manager helper's proven reciprocal pairs.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
s=importlib.util.spec_from_file_location('south_upper_qa',HERE.parent/'coronet-upper-floors/run_runtime_qa.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
MAPS=(*a.MAPS,'MAP_MT_CORONET_1F_SOUTH')

def run(args):
    sys.path.insert(0,str(ROOT/'Pokemon Game/scripts/claude_play'))
    import map_qa as qa
    old_maps=a.MAPS;original_warp=qa.Runner.warp;original_follower=qa.Runner.follower;original_main=qa.main
    if args.mode=='batch':
        s=importlib.util.spec_from_file_location('south_fast_qa',ROOT/'Pokemon Game/scripts/sinnoh_fast_batch_qa.py')
        fast=importlib.util.module_from_spec(s);s.loader.exec_module(fast);fast.install_batch_mode(qa)
    if getattr(args,'affected_only',False) and args.mode!='batch':
        raise ValueError('affected-only is construction QA, never final acceptance')
    a.MAPS=('MAP_MT_CORONET_1F_SOUTH','MAP_SINNOH_MT_CORONET_2F') if getattr(args,'affected_only',False) else MAPS
    def main(argv):
        argv=list(argv)
        if not args.expect:
            for x in range(26,32):argv+=['--blocked',f'MAP_MT_CORONET_1F_SOUTH,{x},9,down']
        return original_main(argv)
    qa.main=main
    try:
        code=a.run(args)
        out=getattr(args,'out',None)
        if out is not None and (Path(out)/'result.json').is_file():
            p=Path(out)/'result.json';d=json.loads(p.read_text())
            d.update(qa_mode=args.mode,construction_only=args.mode=='batch',affected_only=getattr(args,'affected_only',False),production_acceptance_claimed=False)
            p.write_text(json.dumps(d,indent=1)+'\n')
        return code
    finally:
        a.MAPS=old_maps;qa.Runner.warp=original_warp;qa.Runner.follower=original_follower;qa.main=original_main

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('engine','rom','scratch','out','recipe'):p.add_argument('--'+n,required=True,type=Path)
    p.add_argument('--profile',required=True,choices=('normal','release'))
    p.add_argument('--mode',required=True,choices=('batch','final'))
    p.add_argument('--affected-only',action='store_true',help='construction: new South warp pair and both endpoint followers; full final disallows this')
    p.add_argument('--expect',type=Path);sys.exit(run(p.parse_args()))
