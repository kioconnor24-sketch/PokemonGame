#!/usr/bin/env python3
"""Read-only source graph audit of13 staged maps, not a runtime installer."""
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('scene_approach',HERE/'build_source.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def load_scene():
    def read(path):return m.base.verified_file(m.ROOT,path.relative_to(m.ROOT),'HEAD')
    scene={}
    for name,definition in json.loads(read(m.ROUTE/'art-plan.json'))['maps'].items():
        w,h=definition['dimensions']
        link=HERE.parent/'battle-zone-links/staged'/name
        if name=='Route227':folder=HERE/'staged'/name
        elif link.exists():folder=link
        else:folder=None
        header=json.loads(read(folder/'map.json' if folder else HERE.parent/'remaining-donor/staged'/name/'map.json'))
        raw=read(folder/'map.bin' if folder else m.ROUTE/'staged'/name/'averon-map.bin')
        family=m.ROUTE/'outdoor-family'
        scene[header['id']]=dict(name=name,width=w,height=h,header=header,raw=raw,
            attrs=[read(family/p) for p in ('primary-attributes.bin','secondary-attributes.bin')])
    for name in ('Outside','Room1','Room2','Room3'):
        folder=(HERE if name in ('Outside','Room1') else m.BASE)/'staged'/name
        w,h=(32,32) if name=='Outside' else m.m.DIMS[name]
        header=json.loads(read(folder/'map.json'))
        family=HERE/'cave-family'
        scene[header['id']]=dict(name=name,width=w,height=h,header=header,raw=read(folder/'map.bin'),
            attrs=[read(family/p) for p in ('primary-attributes.bin','secondary-attributes.bin')])
    return scene

def audit(scene):
    if len(scene)!=13:raise ValueError('exact13-map scene required')
    graph={name:set() for name in scene};warps=0;connections=0
    for identity,item in scene.items():
        h=item['header'];w,height=item['width'],item['height']
        if len(item['raw'])!=2*w*height:raise ValueError('map bounds differ')
        if h['region_map_section']!='MAPSEC_PENDING_OWNER':raise ValueError('unapproved source section')
        for (v,) in struct.iter_unpack('<H',item['raw']):
            mid=v&1023
            if len(item['attrs'][mid//512])<2*(mid%512+1):raise ValueError('unresolved attribute record')
        for link in h['connections']:
            target=link['map']
            if target not in scene:raise ValueError('unresolved connection')
            opposite={'up':'down','down':'up','left':'right','right':'left'}
            expected=dict(map=identity,direction=opposite[link['direction']],offset=-link['offset'])
            if expected not in scene[target]['header']['connections']:raise ValueError('nonreciprocal connection')
            graph[identity].add(target);connections+=1
        for i,event in enumerate(h['warp_events']):
            target=event['dest_map'];index=int(event['dest_warp_id'])
            if target not in scene or not 0<=index<len(scene[target]['header']['warp_events']):raise ValueError('unresolved warp')
            back=scene[target]['header']['warp_events'][index]
            if back['dest_map']!=identity or int(back['dest_warp_id'])!=i:raise ValueError('nonreciprocal warp index')
            x,y=event['x'],event['y']
            if not(0<=x<w and 0<=y<height):raise ValueError('warp outside map')
            v=struct.unpack_from('<H',item['raw'],2*(y*w+x))[0];mid=v&1023
            behavior=struct.unpack_from('<H',item['attrs'][mid//512],2*(mid%512))[0]&255
            if v&0xc00 or v>>12!=event['elevation'] or behavior!=0x61:raise ValueError('blocked/height/behavior warp')
            graph[identity].add(target);warps+=1
    seen=set();todo=[next(iter(graph))]
    while todo:
        n=todo.pop()
        if n in seen:continue
        seen.add(n);todo.extend(graph[n]-seen)
    if len(seen)!=13:raise ValueError('disconnected scene headers')
    return dict(status='SOURCE_HEADER_GRAPH_NOT_RUNTIME_ACCEPTANCE',maps=13,directed_connections=connections,
                directed_warps=warps,header_components=1,
                maps_sha256={v['name']:m.base.sha(v['raw']) for v in scene.values()},
                limits=['Header graph is not full walking/Surf/rail/bridge reachability','No ROM, engine installation, saved identity or runtime acceptance'])

if __name__=='__main__':print(json.dumps(audit(load_scene()),indent=2))
