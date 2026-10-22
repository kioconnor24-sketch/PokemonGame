#!/usr/bin/env python3
"""Drive the existing map_qa runner on the verified disposable Oreburgh assembly.

All movement/warp/follower/save assertions remain in the existing shared runner.
Requires an already prepared DEV flash fixture; no gameplay memory is edited.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

MAPS=('MAP_ROUTE203','MAP_OREBURGH_GATE_1F','MAP_OREBURGH_CITY','MAP_ROUTE207',
      'MAP_OREBURGH_MINE_B1F','MAP_OREBURGH_MINE_B2F')


def validate_source(engine,recipe):
    if recipe['status']!='DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE':
        raise ValueError('explicit DEV recipe required')
    if not (engine/'.map_qa_throwaway').is_file():raise ValueError('disposable marker required')
    for path,expected in recipe['files'].items():
        target=(engine/path).resolve()
        if not target.is_relative_to(engine.resolve()):raise ValueError('recipe escapes engine')
        if hashlib.sha256(target.read_bytes()).hexdigest()!=expected:
            raise ValueError('source differs from the tested recipe: '+path)


def run(args):
    engine=args.engine.resolve();recipe=json.loads(args.recipe.read_text());validate_source(engine,recipe)
    qa=engine.parent/'scripts/claude_play/map_qa.py'
    cmd=[sys.executable,str(qa),'run','--engine',str(engine),'--rom',str(args.rom),
         '--scratch',str(args.scratch),'--out',str(args.out),'--build',args.profile]
    for name in MAPS:cmd+=['--map',name]
    if args.expect:cmd+=['--expect',str(args.expect)]
    else:cmd+=['--save','oreburgh-corridor','--blocked','MAP_ROUTE207,52,6,up']
    return subprocess.call(cmd)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('engine','rom','scratch','out','recipe'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--profile',required=True,choices=('normal','release'));p.add_argument('--expect',type=Path)
    sys.exit(run(p.parse_args()))
