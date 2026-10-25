#!/usr/bin/env python3
"""Source-derived Stark outside with an explicit authored Route227 seam.

Copies, never rewrites, the original three-room and Route227 packets. Native
ordinal/stair projection and static paths are not emulator acceptance.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct
from fractions import Fraction
from collections import deque

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'stark-mountain'
ROUTE=HERE.parent/'battle-zone-north'
s=importlib.util.spec_from_file_location('approach_existing_stark',BASE/'build_source.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ROOT=HERE.parents[4]
base=m.base;dual=m.dual;packer=m.a.a

def extract(inputs):
    pins=json.loads((BASE/'NEXT_APPROACH_SOURCE.json').read_text());raws={}
    for path,pin in pins['files'].items():
        raw=(Path(inputs)/pin['private_input_name']).read_bytes()
        import hashlib
        if len(raw)!=pin['bytes'] or base.sha(raw)!=pin['sha256'] or hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=pin['git_blob']:
            raise ValueError('outside source identity differs')
        raws[path]=raw
    matrix=json.loads(raws['res/field/matrices/map_matrix_000.json'])
    if matrix['headers'][7][23]!='MAP_HEADER_STARK_MOUNTAIN_OUTSIDE' or matrix['maps'][7][23]!='MAP_172' or matrix['headers'][8][23]!='MAP_HEADER_ROUTE_227':
        raise ValueError('outside source adjacency differs')
    events=json.loads(raws['res/field/events/events_stark_mountain_outside.json'])['warp_events']
    if events!=[dict(x=750,z=231,dest_header_id='MAP_HEADER_STARK_MOUNTAIN_ROOM_1',dest_warp_id=0)]:raise ValueError('outside source door differs')
    raw=raws['res/field/maps/data/map_data_172.bin'];sizes=struct.unpack_from('<4I',raw)
    if sizes!=(2048,144,56140,1624) or 16+sum(sizes)!=len(raw):raise ValueError('outside section bounds differ')
    data=m.b.decode(raw[16+sum(sizes[:3]):]);points=[];blocked=0
    for i,(word,) in enumerate(struct.iter_unpack('<H',raw[16:2064])):
        if word&0x7f00:raise ValueError('unknown permission flags')
        if word&0x8000:blocked+=1;continue
        if word not in (0,2,0x6e):raise ValueError('unknown passable terrain')
        x,y=i%32,i//32;heights={v for _,v in m.b.tile_candidates(data,x,y)}
        if len(heights)!=1:raise ValueError('ambiguous outside height')
        height=next(iter(heights));flat=True
        for dx,dz in ((-8,-8),(-8,8),(8,-8),(8,8)):
            values={v for _,v in m.b.candidates(data,(x-16)*m.b.TILE+m.b.TILE//2+dx*m.b.FX,(y-16)*m.b.TILE+m.b.TILE//2+dz*m.b.FX)}
            if not values:raise ValueError('unsupported outside footprint')
            flat &= height in values
        points.append(dict(tile=[x,y],permission=word,height=str(height/m.b.FX),flat=flat))
    return dict(dimensions=[32,32],world_cell=[23,7],source_door=[14,7],surfaces=points,blocked_permission_cells=blocked,
                source_revision=pins['revision'],props_or_model_emitted=False)

def load():
    plan=json.loads((HERE/'plan.json').read_text())
    for path,h in plan['baseline_sha256'].items():
        committed=base.verified_file(ROOT,HERE.parent.relative_to(ROOT)/path,'HEAD')
        if base.sha(committed)!=h or (HERE.parent/path).read_bytes()!=committed:raise ValueError('baseline pin differs')
    for filename in ('geometry.json','plan.json'):
        committed=base.verified_file(ROOT,HERE.relative_to(ROOT)/filename,'HEAD')
        if (HERE/filename).read_bytes()!=committed:raise ValueError('dirty approach source')
    return json.loads((HERE/'geometry.json').read_text()),plan

def construct(geometry,route,room,room_header):
    flats=sorted({Fraction(p['height']) for p in geometry['surfaces'] if p['flat']})
    if len(flats)>12:raise ValueError('outside height capacity')
    zmap={v:i+3 for i,v in enumerate(flats)};cells=[0xc00|513]*1024;seen=set()
    for p in geometry['surfaces']:
        x,y=p['tile']
        if not 0<=x<32 or not 0<=y<32 or (x,y) in seen or p['permission'] not in (0,2,0x6e):raise ValueError('invalid outside surface')
        seen.add((x,y))
        # All unmatched outer edges closed; only the authored two-lane seam.
        if x in (0,31) or y in (0,31):
            if not(y==31 and x in (28,29)):continue
        z=zmap[Fraction(p['height'])] if p['flat'] else 0
        cells[y*32+x]=(z<<12)|(13 if p['permission']==2 else 529 if p['flat'] else 516)
    for x in (28,29):
        if cells[31*32+x]&0xfc00!=0x3000:raise ValueError('south source seam height differs')
    if (14,7) not in seen:raise ValueError('missing outside door')
    cells[7*32+14]=(cells[7*32+14]&0xf000)|517
    route=bytearray(route);changes=[]
    for x in (28,29):
        old=struct.unpack_from('<H',route,2*x)[0]
        if not old&0xc00:raise ValueError('unexpected open Route227 source boundary')
        struct.pack_into('<H',route,2*x,0x3001);changes.append(dict(cell=[x,0],before=old,after=0x3001))
    # Reuse the accepted Room1 ladder metatile, preserving its family IDs.
    header=json.loads(json.dumps(room_header));old_warps=json.loads(json.dumps(header['warp_events']))
    if len(old_warps)!=1 or old_warps[0]['dest_map']!='MAP_SINNOH_STARK_ROOM2':raise ValueError('Room1 source warp prefix differs')
    room=bytearray(room);ladder=struct.unpack_from('<H',room,2*(2*64+17))[0]&1023
    old=struct.unpack_from('<H',room,2*(29*64+20))[0]
    if not old&0xc00:raise ValueError('Room1 exterior already open')
    struct.pack_into('<H',room,2*(29*64+20),0x3000|ladder)
    header['warp_events'].append(dict(x=20,y=29,elevation=3,dest_map='MAP_SINNOH_STARK_OUTSIDE',dest_warp_id='0'))
    outside=dict(id='MAP_SINNOH_STARK_OUTSIDE',name='SinnohStarkOutside',layout='LAYOUT_SINNOH_STARK_OUTSIDE',
                 map_type='MAP_TYPE_ROUTE',requires_flash=False,allow_cycling=False,allow_escaping=False,allow_running=True,
                 battle_scene='MAP_BATTLE_SCENE_NORMAL',region='REGION_SINNOH',region_map_section='MAPSEC_PENDING_OWNER',
                 music='MUS_ROUTE110',weather='WEATHER_NONE',show_map_name=True,
                 connections=[dict(map='MAP_ROUTE227',direction='down',offset=0)],
                 warp_events=[dict(x=14,y=7,elevation=cells[7*32+14]>>12,dest_map=header['id'],dest_warp_id='1')],
                 object_events=[],coord_events=[],bg_events=[])
    return struct.pack('<1024H',*cells),bytes(route),bytes(room),outside,header,dict(route_changes=changes,room1_changed_cell=[20,29],
               source_marked_surfaces=len(seen),outside_open_cells=sum(not v&0xc00 for v in cells),
               closed_unmatched_boundary_cells=sum(p['tile'][0] in (0,31) or p['tile'][1] in (0,31) for p in geometry['surfaces'])-2,
               height_to_elevation={str(v):z for v,z in zmap.items()},source_warp_prefix_preserved=header['warp_events'][:-1]==old_warps)

def static_path(raw,w,h,start,end,attributes):
    cells=struct.unpack('<%dH'%(w*h),raw);start,end=tuple(start),tuple(end)
    def valid(p):
        x,y=p
        return 0<=x<w and 0<=y<h and not cells[y*w+x]&0xc00 and attributes[str(cells[y*w+x]&1023)]&255 in (0,0x61)
    if not valid(start) or not valid(end):return []
    todo=deque([start]);prev={start:None}
    while todo:
        p=todo.popleft()
        if p==end:
            path=[]
            while p is not None:path.append(list(p));p=prev[p]
            return path[::-1]
        a=cells[p[1]*w+p[0]]>>12
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            q=p[0]+dx,p[1]+dy
            if q in prev or not valid(q):continue
            b=cells[q[1]*w+q[0]]>>12
            if a and b and a!=b:continue
            prev[q]=p;todo.append(q)
    return []

def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    geometry,plan=load();route=(ROUTE/'staged/Route227/averon-map.bin').read_bytes()
    room=(BASE/'staged/Room1/map.bin').read_bytes();header=json.loads((BASE/'staged/Room1/map.json').read_text())
    raw,route,room,outside,header,audit=construct(geometry,route,room,header)
    route_header=json.loads((m.HERE.parent/'remaining-donor/staged/Route227/map.json').read_text())
    route_header['connections'].append(dict(map=outside['id'],direction='up',offset=0))
    prefixes=['data/tilesets/primary/general/','data/tilesets/secondary/cave/'];assets={}
    def read(path):
        v=base.verified_file(ROOT,engine.relative_to(ROOT)/path,'HEAD');assets[path]=base.sha(v);return v
    stock=[read(p+'metatiles.bin') for p in prefixes];pa=read(prefixes[0]+'metatile_attributes.bin')
    attrs=[bytearray(pa),bytearray(read(prefixes[1]+'metatile_attributes.bin'))]
    for mid in (13,513,516,517,529):struct.pack_into('<H',attrs[mid//512],2*(mid%512),0x1061 if mid==517 else 0x1000)
    border=struct.pack('<4H',*[0xc00|513]*4)
    desired=[packer.words(stock[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',raw+border)]
    sec=(BASE/'cave-family/secondary-metatiles.bin').read_bytes();sa=(BASE/'cave-family/secondary-attributes.bin').read_bytes()
    converted,sec,sa=packer.pack_art(raw+border,desired,attrs,stock[0],pa,sec,sa)
    def attributes(data,banks):return {str(v&1023):packer.attribute(banks[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',data)}
    outside_attrs=attributes(converted,(pa,sa));room_attrs=attributes(room,(pa,sa))
    paths=[]
    for x in (28,29):
        path=static_path(converted[:2048],32,32,[x,31],[14,7],outside_attrs)
        if not path:raise ValueError('outside seam cannot reach cave door')
        paths.append(path)
    # Ordinary local Route227 and Room1 approaches must remain accessible.
    route_attrs=attributes(route,[(ROUTE/'outdoor-family/primary-attributes.bin').read_bytes(),(ROUTE/'outdoor-family/secondary-attributes.bin').read_bytes()])
    if not static_path(route,48,60,[28,1],[28,0],route_attrs):raise ValueError('Route227 approach inaccessible')
    room_path=static_path(room,64,32,[20,29],[17,2],room_attrs)
    if not room_path:raise ValueError('Room1 entry cannot reach internal stair')
    images=[dual.indexed(read(p+'tiles.png')) for p in prefixes]
    previews={}
    for n,data,w,h in [('Outside',converted[:2048],32,32),('Room1',room,64,32)]:
        deps=dual.closure(data,[stock[0],sec],images)
        palettes={i:base.palette(read(prefixes[i>=6]+'palettes/%02d.pal'%i)) for i in deps['palettes']}
        previews[n]=dual.render(data,[stock[0],sec],images,palettes,w,h)
    out.mkdir(parents=True);family=out/'cave-family';family.mkdir()
    for n,v in [('primary-metatiles',stock[0]),('primary-attributes',pa),('secondary-metatiles',sec),('secondary-attributes',sa)]:(family/(n+'.bin')).write_bytes(v)
    packets={'Outside':(converted[:2048],converted[2048:],outside,outside_attrs),
             'Room1':(room,(BASE/'staged/Room1/border.bin').read_bytes(),header,room_attrs),
             'Route227':(route,(ROUTE/'staged/Route227/averon-border.bin').read_bytes(),route_header,route_attrs)}
    for n,(data,border,h,attr) in packets.items():
        p=out/'staged'/n;p.mkdir(parents=True);(p/'map.bin').write_bytes(data);(p/'border.bin').write_bytes(border)
        (p/'map.json').write_text(json.dumps(h,indent=2)+'\n');(p/'attributes.json').write_text(json.dumps(attr,indent=2)+'\n')
        if n in previews:previews[n].save(p/'preview.png')
    receipt=dict(status='AUTHORED_SOURCE_HEIGHT_APPROACH_NOT_RUNTIME_ACCEPTANCE',**audit,
                 geometry_sha256=base.sha((HERE/'geometry.json').read_bytes()),plan_sha256=base.sha((HERE/'plan.json').read_bytes()),
                 baseline_sha256=plan['baseline_sha256'],native_asset_sha256=assets,secondary_records=len(sec)//16,
                 outside_paths=paths,room1_entry_path=room_path,
                 limits=['Source outside permission/heights with ordinal/wildcard native physical adaptation',
                         'Two Route227 boundary cells and one Room1 cell explicitly authored; original packets immutable',
                         'Seam offset0/0 is authored width adaptation, not donor original',
                         'Grass renders without encounters; ashfall/props/models not copied',
                         'No permanent IDs/registry/save changes or ROM/native/mGBA/Save acceptance'])
    receipt['output_sha256']={str(p.relative_to(out)):base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--private-inputs',type=Path)
    args=p.parse_args()
    if args.private_inputs and extract(args.private_inputs)!=json.loads((HERE/'geometry.json').read_text()):raise ValueError('outside extraction differs')
    print(json.dumps(build(args.engine,args.out),indent=2))
