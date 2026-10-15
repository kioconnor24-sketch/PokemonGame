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
    if n=='CoastalMeadow':
        attrs=struct.unpack('<512H',(root/'data/tilesets/primary/general/metatile_attributes.bin').read_bytes())
        grass=sum(1 for v in data if (v&1023)<512 and (attrs[v&1023]&255)==2 and ((v>>10)&3)==0)
        if grass<20:errors.append(f'{n}: insufficient walkable encounter grass ({grass})')
    print(f'{n}: {w}x{h}, {len(m["warp_events"])} warps, {len(m["object_events"])} NPCs')
if errors:
    print('\n'.join(errors));raise SystemExit(1)
print('PASS: native warp targets, reciprocal map connections, and door/NPC approach collision. Runtime tests still required.')
