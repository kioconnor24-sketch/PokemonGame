"""Validate native map links and reachable openings, using real layout bytes."""
import json, struct, re
from pathlib import Path
from collections import deque
from functools import lru_cache
root=Path(__file__).resolve().parents[1]/'engine'
groups=json.loads((root/'data/maps/map_groups.json').read_text())
layouts={l['id']:l for l in json.loads((root/'data/layouts/layouts.json').read_text())['layouts']}
names=groups['gMapGroup_AveronOpening']
maps={n:json.loads((root/f'data/maps/{n}/map.json').read_text()) for n in names}
ids={m['id']:m for m in maps.values()}
errors=[]
behavior_ids={};index=-1
for token in re.finditer(r'^\s*(MB_\w+)(?:\s*=\s*(0x[0-9A-Fa-f]+|\d+))?\s*,',
                        (root/'include/constants/metatile_behaviors.h').read_text(),re.M):
    index=int(token[2],0) if token[2] else index+1
    behavior_ids[token[1]]=index
surfable={behavior_ids[name] for name,flags in re.findall(r'\[(MB_\w+)\]\s*=\s*([^,\n]+)',
            (root/'src/metatile_behavior.c').read_text()) if 'TILE_FLAG_SURFABLE' in flags}
grids={}
for name,m in maps.items():
    l=layouts[m['layout']]
    grids[name]=(l['width'],l['height'],struct.unpack('<'+'H'*(l['width']*l['height']),(root/l['blockdata_filepath']).read_bytes()),l)
def adjacent(x,y):return ((x-1,y),(x+1,y),(x,y-1),(x,y+1))
def walk_grid(grid,x,y):
    w,h,values,layout=grid
    return (0<=x<w and 0<=y<h and ((values[y*w+x]>>10)&3)==0
            and behavior(layout,values[y*w+x]) not in surfable)
@lru_cache(None)
def attributes(symbol):
    folder=re.sub(r'(?<!^)(?=[A-Z])','_',symbol.removeprefix('gTileset_')).lower()
    path=next((root/'data/tilesets').glob('*/'+folder))/'metatile_attributes.bin'
    return [v[0]&255 for v in struct.iter_unpack('<H',path.read_bytes())]
def behavior(layout,cell):
    symbol=layout['primary_tileset'] if (cell&1023)<512 else layout['secondary_tileset']
    return attributes(symbol)[(cell&1023)%512]
for n,m in maps.items():
    l=layouts[m['layout']]; w,h=l['width'],l['height']
    data=struct.unpack('<'+'H'*(w*h),(root/l['blockdata_filepath']).read_bytes())
    def walk(x,y):return walk_grid(grids[n],x,y)
    for i,warp in enumerate(m['warp_events']):
        target=ids[warp['dest_map']]; j=int(warp['dest_warp_id'])
        if j>=len(target['warp_events']):errors.append(f'{n} warp {i}: bad destination index')
        elif target['warp_events'][j]['dest_map']!=m['id']:errors.append(f'{n} warp {i}: destination does not link back')
        # Door behavior can be entered from the tile immediately below.
        if not walk(warp['x'],warp['y']) and not walk(warp['x'],warp['y']+1):errors.append(f'{n} warp {i}: blocked door approach')
    for connection in m['connections'] or []:
        opposite={'up':'down','down':'up','left':'right','right':'left'}[connection['direction']]
        target=ids[connection['map']]
        if not any(c['map']==m['id'] and c['direction']==opposite for c in target['connections'] or []):errors.append(f'{n}: missing reverse connection')
    for npc in m['object_events']:
        if not walk(npc['x'],npc['y']):errors.append(f'{n}: NPC on collision tile at {npc["x"]},{npc["y"]}')
    # Trace real door/edge entry points. Occupied NPC tiles are not walkable.
    seeds=set()
    for warp in m['warp_events']:
        q=(warp['x'],warp['y'])
        seeds.add(q if walk(*q) else (q[0],q[1]+1))
    for c in m['connections'] or []:
        target=ids[c['map']];grid=grids[target['name']];tw,th,_,_=grid
        offset=int(c['offset']);direction=c['direction'];pairs=[]
        if direction=='up':pairs=[((x,0),(x-offset,th-1)) for x in range(w)]
        if direction=='down':pairs=[((x,h-1),(x-offset,0)) for x in range(w)]
        if direction=='left':pairs=[((0,y),(tw-1,y-offset)) for y in range(h)]
        if direction=='right':pairs=[((w-1,y),(0,y-offset)) for y in range(h)]
        crossing=[a for a,b in pairs if walk(*a) and walk_grid(grid,*b)]
        if not crossing:errors.append(f'{n}: no walkable border crossing toward {target["name"]}')
        seeds.update(crossing)
    if n=='Saltmere':seeds.add((18,18))
    occupied={(o['x'],o['y']) for o in m['object_events']}
    valid_seeds=sorted(q for q in seeds if walk(*q) and q not in occupied)
    points=set(valid_seeds[:1]);pending=deque(points)
    while pending:
        x,y=pending.popleft()
        for q in adjacent(x,y):
            if q in points or q in occupied:continue
            if walk(*q) or n=='AlderfieldGym' and q==(4,9):
                points.add(q);pending.append(q)
    for q in seeds:
        if q not in points:errors.append(f'{n}: door/border entry {q} disconnected from other entries')
    for obj in m['object_events']+m['bg_events']:
        x,y=obj['x'],obj['y'];approaches=list(adjacent(x,y))
        # Native counters allow talking across one blocked metatile.
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            cx,cy=x+dx,y+dy
            if 0<=cx<w and 0<=cy<h and behavior(l,data[cy*w+cx])==behavior_ids['MB_COUNTER']:
                approaches.append((x+dx*2,y+dy*2))
        if not any(q in points for q in approaches):
            errors.append(f'{n}: unreachable interaction {obj.get("script","?")} at {x},{y}')
    if n=='AlderfieldGym':
        blocked={(o['x'],o['y']) for o in m['object_events']}
        def reached(gate_open):
            found={(4,15)};pending=deque(found)
            while pending:
                x,y=pending.popleft()
                for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if q in found or q in blocked:continue
                    if q==(4,9) and gate_open or walk(*q):
                        found.add(q);pending.append(q)
            return found
        closed,opened=reached(False),reached(True)
        def can_talk(points,obj):
            x,y=obj['x'],obj['y']
            return any(q in points for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)))
        for obj in m['object_events']:
            if 'Sluice' in obj['script'] and not can_talk(closed,obj):
                errors.append(f'{n}: sluice unreachable before opening gate')
            if obj['script']=='Alderfield_Elio':
                if can_talk(closed,obj):errors.append(f'{n}: leader reachable through closed gate')
                if not can_talk(opened,obj):errors.append(f'{n}: leader unreachable after opening gate')
        if (5,15) not in opened:errors.append(f'{n}: second exit unreachable')
    if n=='CoastalMeadow':
        attrs=struct.unpack('<512H',(root/'data/tilesets/primary/general/metatile_attributes.bin').read_bytes())
        grass=sum(1 for v in data if (v&1023)<512 and (attrs[v&1023]&255)==2 and ((v>>10)&3)==0)
        if grass<20:errors.append(f'{n}: insufficient walkable encounter grass ({grass})')
    print(f'{n}: {w}x{h}, {len(m["warp_events"])} warps, {len(m["object_events"])} NPCs')
if errors:
    print('\n'.join(errors));raise SystemExit(1)
print('PASS: native warps/borders connect; NPC/sign interactions reachable (including counters); closed/open Gym gate checks pass. Runtime tests still required.')
