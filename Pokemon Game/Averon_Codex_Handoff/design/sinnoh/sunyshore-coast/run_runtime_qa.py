#!/usr/bin/env python3
"""Source-verified coast dry-map input QA; no Surf/Waterfall grant.

Water maps remain compiled/native-tested but excluded from this foot-only plan.
Their presence is not natural water-route traversal acceptance.
"""
import argparse
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('sunyshore_height_qa',HERE.parent/'celestic-north/run_runtime_qa.py')
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
MAPS=('MAP_ROUTE222','MAP_ROUTE222_ACCESS','MAP_SUNYSHORE_CITY')


def run(args):
    scripts=HERE.parents[3]/'scripts/claude_play';sys.path.insert(0,str(scripts))
    import driver  # bind the expected source driver before _wrapper resolves modules
    import map_qa as qa
    wrapper=qa._wrapper(args.engine)
    wrapper.emu.OFFSET_EXPRS['avatar.flags']='offsetof(struct PlayerAvatar, flags)'
    for flag in ('PLAYER_AVATAR_FLAG_SURFING','PLAYER_AVATAR_FLAG_ON_FOOT'):
        if flag not in wrapper.emu.CONSTANTS:wrapper.emu.CONSTANTS.append(flag)
    old_maps,old_check,old_runner=shared.MAPS,qa.Runner.check,qa.Runner
    class CoastRunner(old_runner):
        def run_map(self,map_id):
            if getattr(args,'ledge_x',None) is not None:
                x=args.ledge_x
                ok=self.go(map_id,(x,15))
                self.check('reached source ledge approach',ok,at=self.d.here())
                if ok:
                    self.d.shot('source-ledge-before')
                    self.press('down',hold=.35,after=1.0)
                    here=self.wait_settled()
                    self.d.shot('source-ledge-after')
                    # A real source defect is a FAIL, even when other paths
                    # pass. Read-only source facts; no collision/game edits.
                    landed=here==(map_id,(x,17))
                    m=self.w.map(map_id)
                    self.check('source ledge does not land inside solid terrain',not (landed and m.collision(x,17)!=0),
                               at=here,landing_collision=m.collision(x,17),source_ledge=(x,16))
                return
            super().run_map(map_id)
            if map_id=='MAP_SUNYSHORE_CITY':
                # Four source-pinned spans, not a claim all68 tiles or both
                # render planes have been accepted from static packing alone.
                for x,y in ((28,11),(25,33),(23,44),(30,45)):
                    ok=self.go(map_id,(x,y))
                    self.check('source elevated walkway reached '+str((x,y)),ok,at=self.d.here(),elevations=shared.observed_elevations(self.d))
                    self.d.shot('sunyshore-elevated-%d-%d'%(x,y))
                    if ok:self.follower('elevated '+str((x,y)))
    def check(self,name,ok,**details):
        result=old_check(self,name,ok,**details)
        if name.startswith('follower visible'):
            g=self.d.g
            flags=g.gdb.read(g.sym['gPlayerAvatar']+g.off['avatar.flags'],1)[0]
            mask=g.c['PLAYER_AVATAR_FLAG_SURFING']
            foot=g.c['PLAYER_AVATAR_FLAG_ON_FOOT']
            ordinary=old_check(self,'ordinary foot/no Surf at '+name,bool(flags&foot) and not (flags&mask),avatar_flags=flags,foot_mask=foot,surf_mask=mask)
            return bool(result and ordinary)
        return result
    shared.MAPS=('MAP_ROUTE222',) if getattr(args,'ledge_x',None) is not None else MAPS
    qa.Runner.check=check;qa.Runner=CoastRunner
    try:return shared.run(args)
    finally:shared.MAPS=old_maps;qa.Runner.check=old_check;qa.Runner=old_runner


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('engine','rom','scratch','out','recipe'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--profile',required=True,choices=('normal','release'));p.add_argument('--expect',type=Path)
    p.add_argument('--ledge-x',type=int,choices=(36,37),help='independent actual source-ledge negative, DEV flash copy only')
    sys.exit(run(p.parse_args()))
