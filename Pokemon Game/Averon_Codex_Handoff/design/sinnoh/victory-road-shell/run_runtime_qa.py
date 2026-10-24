#!/usr/bin/env python3
"""Source-verified ordinary three-floor stair/follower QA; exterior remains closed."""
import argparse
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('victory_height_qa',HERE.parent/'celestic-north/run_runtime_qa.py')
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
MAPS=('MAP_SINNOH_VICTORY_ROAD_1F','MAP_SINNOH_VICTORY_ROAD_2F','MAP_SINNOH_VICTORY_ROAD_B1F')


def run(args):
    scripts=HERE.parents[3]/'scripts/claude_play';sys.path.insert(0,str(scripts))
    import driver  # bind the expected source driver before _wrapper resolves modules
    import map_qa as qa
    wrapper=qa._wrapper(args.engine)
    wrapper.emu.OFFSET_EXPRS['avatar.flags']='offsetof(struct PlayerAvatar, flags)'
    for flag in ('PLAYER_AVATAR_FLAG_SURFING','PLAYER_AVATAR_FLAG_ON_FOOT'):
        if flag not in wrapper.emu.CONSTANTS:wrapper.emu.CONSTANTS.append(flag)
    old_maps,old_check=shared.MAPS,qa.Runner.check
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
    shared.MAPS=('MAP_POKMON_LEAGUE',*MAPS) if getattr(args,'with_league',False) else MAPS
    qa.Runner.check=check
    try:return shared.run(args)
    finally:shared.MAPS=old_maps;qa.Runner.check=old_check


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('engine','rom','scratch','out','recipe'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--profile',required=True,choices=('normal','release'));p.add_argument('--expect',type=Path)
    p.add_argument('--with-league',action='store_true',help='test actual coupled League doors in the combined eight-map scene')
    sys.exit(run(p.parse_args()))
