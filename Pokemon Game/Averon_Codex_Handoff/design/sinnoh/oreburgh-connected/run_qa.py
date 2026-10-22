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
    for name in (('MAP_ROUTE207',) if args.upper_probe else MAPS):cmd+=['--map',name]
    if args.expect:cmd+=['--expect',str(args.expect)]
    elif not args.upper_probe:cmd+=['--save','oreburgh-corridor']
    sys.path.insert(0,str(qa.parent))
    import map_qa
    class OrdinaryFollower(map_qa.Runner):
        def follower(self,label):
            # Match the shared probe's documented plain-neighbour intent. A source
            # Muddy Slope is C0 but cannot be climbed on foot; failed input does
            # not place a follower after Continue and is not a plain walking test.
            import run as play
            mid,(x,y)=self.d.here();m=self.w.map(mid)
            for direction,(dx,dy) in map_qa.DIRS.items():
                nx,ny=x+dx,y+dy
                if (m.walkable(nx,ny) and not m.warp_at(nx,ny)
                    and 'MUDDY_SLOPE' not in m.behavior(nx,ny)
                    and (nx,ny) not in {(o[0],o[1]) for o in m.objects}):
                    if not self.d.step(direction):continue
                    self.d.step(map_qa.OPPOSITE[direction]);break
            observation=play.observe(self.d,label);follower=observation.get('follower') or {}
            return self.check('follower visible ('+label+')',bool(follower) and not follower.get('invisible'),follower=follower)
    if args.upper_probe:
        class UpperProbe(OrdinaryFollower):
            def run_map(self,map_id):
                self.go(map_id,(52,6))
                self.check('upper plateau navigation reaches exact probe',self.d.here()==(map_id,(52,6)),at=self.d.here())
                self.blocked(map_id,52,6,'up')
                self.follower('upper plateau after closed Coronet probe')
        map_qa.Runner=UpperProbe
    else:map_qa.Runner=OrdinaryFollower
    return map_qa.main(cmd[2:])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('engine','rom','scratch','out','recipe'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--profile',required=True,choices=('normal','release'));p.add_argument('--expect',type=Path);p.add_argument('--upper-probe',action='store_true')
    sys.exit(run(p.parse_args()))
