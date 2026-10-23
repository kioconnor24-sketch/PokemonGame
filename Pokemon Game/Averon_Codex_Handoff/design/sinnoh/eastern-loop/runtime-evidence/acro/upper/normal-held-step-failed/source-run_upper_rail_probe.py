#!/usr/bin/env python3
"""One scoped upper-layer case, reusing the existing QA/Acro controllers."""
import argparse
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
common=module('upper_common',HERE/'run_runtime_qa.py')
acro=module('upper_existing_acro',HERE/'run_rail_probe.py')


def track(m):
    if m.id!='MAP_ROUTE212_SOUTH':raise ValueError('exact Route212South required')
    cells=[(x,11) for x in range(43,26,-1)]
    for x,y in cells:
        if (not m.inside(x,y) or m.collision(x,y)!=0 or m.elevation(x,y) not in (4,15)
                or m.behavior(x,y) not in ('MB_NORMAL','MB_HORIZONTAL_RAIL')):
            raise ValueError('upper source track changed')
    if m.elevation(*cells[0])!=4 or m.elevation(*cells[-1])!=4 or not any(m.elevation(*p)==15 for p in cells):
        raise ValueError('upper source elevation endpoints changed')
    return cells


def run(args):
    scripts=HERE.parents[3]/'scripts/claude_play';sys.path.insert(0,str(scripts));import map_qa as qa
    original=qa.Runner
    class UpperRunner(original):
        def require(self,name,ok,**detail):
            if not self.check(name,ok,**detail):raise ValueError(name)
        def run_map(self,mid):
            d=self.d;g=d.g;cells=track(d.live_map(mid));w=qa._wrapper(args.engine)
            self.require('starts on genuine lower ground3 approach',d.here()==(mid,(36,12)) and common.observed_elevations(d)['player']==3,at=d.here(),elevations=common.observed_elevations(d))
            self.require('explicit fixture grants exactly one Acro',dict(g.bag_pocket('bag.keyItems','BAG_KEYITEMS_COUNT')).get(g.c['ITEM_ACRO_BIKE'])==1)
            d.walk_path(mid,{cells[0]});d.settle()
            self.require('ordinary foot route reaches upper layer4',d.here()==(mid,cells[0]) and common.observed_elevations(d)['player']==4,at=d.here(),elevations=common.observed_elevations(d))
            acro.bike_use(d,w.play);self.require('upper bridge mounted through ordinary Bag USE',acro.avatar(d)['flags']&g.c['PLAYER_AVATAR_FLAG_ACRO_BIKE'])
            for direction,points in (('left',cells[1:]),('right',list(reversed(cells[:-1])))):
                for point in points:
                    common.ordinary_step(d,direction)
                    self.require('upper '+direction+' '+str(point),d.here()==(mid,point) and common.observed_elevations(d)['player']==4,at=d.here(),source_elevation=d.live_map(mid).elevation(*point),elevations=common.observed_elevations(d))
                d.shot('upper-'+direction+'-endpoint')
            acro.bike_use(d,w.play);self.require('upper ordinary Bag USE dismounts',not acro.avatar(d)['flags']&g.c['PLAYER_AVATAR_FLAG_ACRO_BIKE'])
            self.follower('upper bridge returned',expected_layer=4)
            self.require('upper player and follower retain native layer4 after dismount',common.observed_elevations(d)==dict(player=4,follower=4),elevations=common.observed_elevations(d))
            for label,tile,layer in (('back to lower',(36,12),3),('back to upper',cells[0],4)):
                d.walk_path(mid,{tile});d.settle();self.follower(label,expected_layer=layer)
                self.require(label+' foot transition preserves both actors',d.here()==(mid,tile) and common.observed_elevations(d)==dict(player=layer,follower=layer),at=d.here(),elevations=common.observed_elevations(d))
    # One scenario, not a substitute for the normal thirteen-map traversal.
    args.map=['MAP_ROUTE212_SOUTH'];args.subset_label='upper-rail';args.acro_route=True
    qa.Runner=UpperRunner
    try:return common.run(args)
    finally:qa.Runner=original

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('engine','rom','scratch','out','recipe'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--profile',required=True,choices=('normal','release'));p.add_argument('--expect',type=Path)
    sys.exit(run(p.parse_args()))
