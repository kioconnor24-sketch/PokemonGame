#!/usr/bin/env python3
"""Existing graphical QA with native elevation-aware navigation/bridge probes.

The engine/map/flash is never patched. Only marked recipe-verified DEV source
is accepted; real player/follower elevation is read from matching-build offsets.
"""
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import sys

MAPS=('MAP_ETERNA_CITY','MAP_ROUTE206_NORTH','MAP_ROUTE206','MAP_ROUTE206_SOUTH','MAP_ROUTE211_WEST')
DIRS={'up':(0,-1),'down':(0,1),'left':(-1,0),'right':(1,0)}


def arrow_direction(m,tile):
    if not m.warp_at(*tile):return None
    behavior=getattr(m,'behavior',lambda x,y:'')(*tile)
    for word,direction in (('NORTH','up'),('SOUTH','down'),('WEST','left'),('EAST','right')):
        if word+'_ARROW' in behavior:return direction
    return None


def elevation_path(m,start,goals,blocked=frozenset(),allow_goal_unwalkable=True,start_elevation=0):
    """Host path planning follows IsElevationMismatchAt/ObjectEventUpdateElevation.

    Elevation0 permits transition;15 preserves the existing layer. Leaving15
    also preserves it for that step, exactly as the existing engine function.
    No pixel/collision/height or game memory is changed to obtain a route.
    """
    start=tuple(start);goals=set(goals)
    if not 0<=start_elevation<=15:raise ValueError('invalid observed elevation')
    if start in goals:return []
    initial=(*start,start_elevation);previous={initial:None};queue=deque([initial])
    while queue:
        x,y,z=queue.popleft();prior=m.elevation(x,y)
        for direction,(dx,dy) in DIRS.items():
            # The native TryArrowWarp tests the CURRENT tile. Taking its arrow
            # direction warps; it is not an ordinary step out of this square.
            if arrow_direction(m,(x,y))==direction:continue
            tile=(x+dx,y+dy)
            if tile in blocked or not m.inside(*tile):continue
            if not m.walkable(*tile) and not (allow_goal_unwalkable and tile in goals):continue
            if tile not in goals and m.warp_at(*tile):continue
            elevation=m.elevation(*tile)
            if z!=0 and elevation not in (0,15,z):continue
            nz=z if 15 in (prior,elevation) else elevation
            state=(*tile,nz)
            if state in previous:continue
            previous[state]=((x,y,z),direction)
            if tile in goals:
                result=[]
                while previous[state] is not None:
                    state,step=previous[state];result.append(step)
                return result[::-1]
            queue.append(state)
    return None


def observed_elevations(d):
    g=d.g;off=g.off;size=off['oe.size'];avatar=g.gdb.read(g.sym['gPlayerAvatar']+off['avatar.objectEventId'],1)[0]
    if avatar>=16:raise ValueError('invalid live player object index')
    raw=g.gdb.read(g.sym['gObjectEvents'],16*size)
    player=raw[avatar*size+off['oe.elevationByte']]&15;follower=None
    for i in range(16):
        rec=raw[i*size:(i+1)*size]
        if rec[0]&1 and rec[off['oe.localId']]==g.c['OBJ_EVENT_ID_FOLLOWER']:
            follower=rec[off['oe.elevationByte']]&15;break
    return dict(player=player,follower=follower)


def validate_source(engine,recipe):
    engine=Path(engine).resolve()
    if recipe['status']!='DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE' or not (engine/'.map_qa_throwaway').is_file():
        raise ValueError('marked DEV recipe required')
    for path,h in recipe['files'].items():
        target=(engine/path).resolve()
        if not target.is_relative_to(engine) or hashlib.sha256(target.read_bytes()).hexdigest()!=h:
            raise ValueError('runtime recipe source differs: '+path)


def run(args):
    engine=args.engine.resolve();validate_source(engine,json.loads(args.recipe.read_text()))
    sys.path.insert(0,str(engine.parent/'scripts/claude_play'))
    import map_qa as qa
    w=qa._wrapper(engine)
    if w.driver.mapdata is not qa.mapdata:raise ValueError('shared driver planner module differs')
    w.emu.OFFSET_EXPRS['avatar.objectEventId']='offsetof(struct PlayerAvatar, objectEventId)'
    # On this actual GCC/GBA ABI, the current/previous elevation byte is the
    # byte immediately before initialCoords; its offset is compiler-derived.
    w.emu.OFFSET_EXPRS['oe.elevationByte']='offsetof(struct ObjectEvent, initialCoords) - 1'
    original_bfs=qa.mapdata.bfs;original_runner=qa.Runner;active=[None]
    def bfs(m,start,goals,blocked=frozenset(),allow_goal_unwalkable=True):
        if active[0] is None:return original_bfs(m,start,goals,blocked,allow_goal_unwalkable)
        z=observed_elevations(active[0])['player']
        return elevation_path(m,start,goals,blocked,allow_goal_unwalkable,z)

    class HeightRunner(original_runner):
        def __init__(self,*values):
            super().__init__(*values);active[0]=self.d

        def path(self,map_id,tile,z=None,start=None):
            here=self.d.here()
            return elevation_path(self.d.live_map(map_id),start or here[1],{tuple(tile)},
                                  start_elevation=observed_elevations(self.d)['player'] if z is None else z)

        def go(self,map_id,tile,_depth=0):
            from driver import Stuck
            tile=tuple(tile)
            if self.d.here()[0]==map_id and self.path(map_id,tile) is None and _depth<2:
                self.enter_region(map_id,tile,_depth)
            try:self.d.walk_path(map_id,{tile})
            except Stuck as exc:
                self.d.log('unreachable',map=map_id,tile=tile,reason=str(exc));return False
            return self.d.here()==(map_id,tile)

        def enter_region(self,map_id,tile,depth):
            target=self.w.map(map_id)
            for src in self.plan:
                for p in self.plan[src]['points']:
                    if p['kind']!='warp' or p['dest']!=map_id or p['dest_warp']>=len(target.warps):continue
                    arrive=qa.warp_arrive(target,*target.warps[p['dest_warp']][:2]);z=target.elevation(*arrive)
                    if z==15 or elevation_path(target,arrive,{tuple(tile)},start_elevation=z) is None:continue
                    self.d.log('enter-region',map=map_id,tile=tile,via=(src,p['tile']),destinationElevation=z)
                    if self.d.here()[0]!=src:self.d.travel_to(src)
                    if not self.go(src,p['tile'],depth+1):continue
                    for _ in range(4):
                        self.press(p['push'],hold=.3,after=1.2)
                        if self.d.here()[0]!=src or self.d.here()==(map_id,arrive):break
                    there=self.wait_settled()
                    if there[0]==map_id and self.path(map_id,tile) is not None:return True
            return False

        def follower(self,label):
            mid,(x,y)=self.d.here();m=self.d.live_map(mid)
            for direction,(dx,dy) in qa.DIRS.items():
                tile=(x+dx,y+dy)
                if (not m.walkable(*tile) or m.warp_at(*tile)
                    or tile in {(o[0],o[1]) for o in m.objects}):continue
                path=self.path(mid,tile)
                if path!=[direction]:continue
                moved=self.d.step(direction)
                if not moved:continue
                if not self.d.field_ready(moved) or self.d.here(moved)!=(mid,tile):
                    return self.check('follower visible ('+label+')',False,reason='ordinary foot probe unexpectedly left its map/tile',at=self.d.here(moved))
                returned=self.d.step(qa.OPPOSITE[direction])
                if not returned or not self.d.field_ready(returned) or self.d.here(returned)!=(mid,(x,y)):
                    return self.check('follower visible ('+label+')',False,reason='ordinary foot probe did not return to the exact source tile',at=self.d.here())
                break
            observation=w.play.observe(self.d,label);follower=observation.get('follower') or {}
            return self.check('follower visible ('+label+')',bool(follower) and not follower.get('invisible'),follower=follower,elevations=observed_elevations(self.d))

        def can_leave(self,label):
            mid,pos=self.d.here();m=self.d.live_map(mid)
            exits={tuple(p['tile']) for p in qa.map_points(m)}
            path=elevation_path(m,pos,exits,start_elevation=observed_elevations(self.d)['player'])
            return self.check('an exit is reachable after '+label,path is not None,at=(mid,pos),elevations=observed_elevations(self.d))

        def run_map(self,map_id):
            if not args.bridge_probe:return super().run_map(map_id)
            upper=args.bridge_probe=='upper';entry=(10,15) if upper else (20,70);z=4 if upper else 3
            if not self.check('explicit '+args.bridge_probe+' DEV entry',self.d.here()==(map_id,entry),at=self.d.here()):return
            directions=[('down',70),('up',70)] if upper else [('left',16),('right',16)]
            for direction,count in directions:
                for index in range(count):
                    before=self.d.here()[1];dx,dy=qa.DIRS[direction];expected=(before[0]+dx,before[1]+dy)
                    moved=self.d.step(direction);at=self.d.here();elev=observed_elevations(self.d)
                    if not self.check(args.bridge_probe+' '+direction+' step '+str(index+1),bool(moved) and at==(map_id,expected) and elev['player']==z,at=at,expected=expected,elevations=elev):
                        self.d.shot('failed-'+args.bridge_probe+'-step');return
                self.follower(args.bridge_probe+' after '+direction)
                elev=observed_elevations(self.d)
                self.check(args.bridge_probe+' player and follower layer',elev['player']==z and elev['follower']==z,elevations=elev)
                self.d.shot(args.bridge_probe+'-'+direction+'-layer')

    cmd=['run','--engine',str(engine),'--rom',str(args.rom),'--scratch',str(args.scratch),'--out',str(args.out),'--build',args.profile]
    for mid in (('MAP_ROUTE206',) if args.bridge_probe else MAPS):cmd+=['--map',mid]
    if args.expect:cmd+=['--expect',str(args.expect)]
    elif not args.bridge_probe:cmd+=['--save','eterna-cycle']
    qa.mapdata.bfs=bfs;qa.Runner=HeightRunner
    try:return qa.main(cmd)
    finally:qa.mapdata.bfs=original_bfs;qa.Runner=original_runner


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('engine','rom','scratch','out','recipe'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--profile',required=True,choices=('normal','release'));p.add_argument('--expect',type=Path);p.add_argument('--bridge-probe',choices=('upper','lower'))
    sys.exit(run(p.parse_args()))
