"""Validate native map links and reachable openings, using real layout bytes."""
import json, struct
from pathlib import Path
from collections import deque
root=Path(__file__).resolve().parents[1]/'engine'
groups=json.loads((root/'data/maps/map_groups.json').read_text())
layouts={l['id']:l for l in json.loads((root/'data/layouts/layouts.json').read_text())['layouts']}
names=groups['gMapGroup_AveronOpening']
maps={n:json.loads((root/f'data/maps/{n}/map.json').read_text()) for n in names}
ids={m['id']:m for m in maps.values()}
errors=[]
for n,m in maps.items():
    l=layouts[m['layout']]; w,h=l['width'],l['height']
    data=struct.unpack('<'+'H'*(w*h),(root/l['blockdata_filepath']).read_bytes())
    def walk(x,y):return 0<=x<w and 0<=y<h and ((data[y*w+x]>>10)&3)==0
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
print('PASS: native warp targets, reciprocal connections, door/NPC collision and closed/open Gym gate reachability. Runtime tests still required.')
