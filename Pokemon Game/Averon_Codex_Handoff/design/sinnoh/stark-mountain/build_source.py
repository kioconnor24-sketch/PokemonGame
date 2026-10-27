#!/usr/bin/env python3
"""Three source-pinned Stark physical projections using existing native art.

Technical permission/BDHC metadata only; no DS models/textures/scripts emitted.
Zero-behavior filler is conservatively sealed; slopes use an explicitly authored
native elevation-zero stair proxy, not exact DS movement or physics parity.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct
from fractions import Fraction

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('stark_existing_native',HERE.parent/'acuity-cavern/build_source.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
s=importlib.util.spec_from_file_location('stark_existing_bdhc',HERE.parent/'snowpoint-temple-height/parse_bdhc.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
base=a.base;dual=a.dual
DIMS={'Room1':(64,32),'Room2':(96,96),'Room3':(32,32)}

def extract(inputs):
    root=Path(inputs).resolve();pins=json.loads((HERE/'source-pins.json').read_text());raws={}
    for key,pin in pins['files'].items():
        path=(root/pin['private_input_name']).resolve()
        if not path.is_relative_to(root):raise ValueError('private source escapes root')
        raw=path.read_bytes()
        if len(raw)!=pin['bytes'] or base.sha(raw)!=pin['sha256']:raise ValueError('private source identity differs')
        import hashlib
        if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=pin['git_blob']:raise ValueError('private source Git identity differs')
        raws[key]=raw
    rooms={}
    for room,(w,h) in DIMS.items():
        n=int(room[-1]);matrix=json.loads(raws['matrix'+str(n)])['maps'];points=[];zero=blocked=0
        if len(matrix)*32!=h or any(len(row)*32!=w for row in matrix):raise ValueError('matrix bounds differ')
        for my,row in enumerate(matrix):
            for mx,land in enumerate(row):
                raw=raws[land];sizes=struct.unpack_from('<4I',raw)
                if sizes[0]!=2048 or sizes[1]!=0 or 16+sum(sizes)!=len(raw):raise ValueError('land section bounds differ')
                data=b.decode(raw[16+sum(sizes[:3]):])
                for i,(word,) in enumerate(struct.iter_unpack('<H',raw[16:2064])):
                    if word&0x7f00:raise ValueError('unsupported source permission flags')
                    if word&0x8000:blocked+=1;continue
                    if word&255 not in (0,8,0x6e,0x6f):raise ValueError('unsupported source behavior')
                    if word&255==0:zero+=1;continue
                    x,y=i%32,i//32;heights={v for _,v in b.tile_candidates(data,x,y)}
                    if len(heights)!=1:raise ValueError('ambiguous/missing center height')
                    height=next(iter(heights));corners=[]
                    for dx,dz in ((-8,-8),(-8,8),(8,-8),(8,8)):
                        values={v for _,v in b.candidates(data,(x-16)*b.TILE+b.TILE//2+dx*b.FX,(y-16)*b.TILE+b.TILE//2+dz*b.FX)}
                        if not values:raise ValueError('unsupported source footprint')
                        corners.append(values)
                    points.append(dict(tile=[mx*32+x,my*32+y],permission=word,
                                       height=str(height/b.FX),flat=all(height in values for values in corners)))
        events=json.loads(raws['events'+str(n)])['warp_events']
        rooms[room]=dict(dimensions=[w,h],surfaces=points,source_warps=events,
                         blocked_permission_cells=blocked,sealed_zero_behavior_cells=zero)
    return dict(source_revision=pins['revision'],rooms=rooms,
                limits=['Source cave-marked floor/door centers and four corners supported by strict BDHC',
                        'Unmarked zero-behavior filler conservatively closed, not complete DS collision parity',
                        'Native ordinal heights and wildcard slope stairs are explicit physical adaptation'])

def height_components(cells,w,h):
    """Static ordinal/wildcard graph only, excluding runtime actor semantics."""
    seen=set();sizes=[]
    for start,v in enumerate(cells):
        if v&0xc00 or start in seen:continue
        todo=[start];seen.add(start);size=0
        while todo:
            i=todo.pop();size+=1;x,y=i%w,i//w
            for xx,yy in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if not(0<=xx<w and 0<=yy<h):continue
                j=yy*w+xx;first,second=cells[i],cells[j]
                if j not in seen and not second&0xc00 and (not(first>>12) or not(second>>12) or first>>12==second>>12):
                    seen.add(j);todo.append(j)
        sizes.append(size)
    return sorted(sizes,reverse=True)


def construct(geometry):
    flat=sorted({Fraction(p['height']) for r in geometry['rooms'].values() for p in r['surfaces'] if p['flat']})
    if len(flat)>12:raise ValueError('native elevation capacity exceeded')
    elevations={v:i+3 for i,v in enumerate(flat)};result={};audit={}
    for room,(w,h) in DIMS.items():
        g=geometry['rooms'][room]
        if g['dimensions']!=[w,h]:raise ValueError('geometry dimensions differ')
        cells=[0xc00|513]*(w*h);seen=set();ramps=0
        for point in g['surfaces']:
            x,y=point['tile'];permission=point['permission']
            if not 0<=x<w or not 0<=y<h or (x,y) in seen or permission not in (8,0x6e,0x6f):raise ValueError('invalid cave surface')
            if x in (0,w-1) or y in (0,h-1):raise ValueError('unexpected open exterior boundary')
            seen.add((x,y));height=Fraction(point['height'])
            z=elevations[height] if point['flat'] else 0
            tile=529 if point['flat'] else 516
            cells[y*w+x]=z<<12|tile;ramps+=not point['flat']
        # Seal the exterior door until a supported outdoor approach exists.
        if room=='Room1':cells[29*w+20]=0xc00|513
        # Source warp index mapping after omitting Room1's exterior exit.
        targets={'Room1':[('Room2',1)],'Room2':[('Room3',0),('Room1',0)],'Room3':[('Room2',0)]}[room]
        source_warps=g['source_warps'][1:] if room=='Room1' else g['source_warps']
        if len(source_warps)!=len(targets):raise ValueError('source warp count differs')
        expected_ids={'Room1':[1],'Room2':[0,1],'Room3':[0]}[room]
        if [v['dest_warp_id'] for v in source_warps]!=expected_ids:raise ValueError('source warp identities differ')
        warps=[]
        for event,(target,index) in zip(source_warps,targets):
            x,y=event['x'],event['z']
            if (x,y) not in seen or event['dest_header_id']!='MAP_HEADER_STARK_MOUNTAIN_ROOM_'+target[-1]:raise ValueError('unverified physical warp')
            old=cells[y*w+x]
            if old&0xc00:raise ValueError('blocked physical warp')
            cells[y*w+x]=(old&0xf000)|517
            warps.append(dict(x=x,y=y,elevation=(old>>12),dest_map='MAP_SINNOH_STARK_'+target.upper(),dest_warp_id=str(index)))
        shape=list(cells)
        for y in range(1,h-1):
            for x in range(1,w-1):
                i=y*w+x
                if shape[i]&0xc00:
                    tile=521 if not shape[i+w]&0xc00 else 530 if not shape[i+1]&0xc00 else 528 if not shape[i-1]&0xc00 else 513
                    cells[i]=0xc00|tile
        header=dict(id='MAP_SINNOH_STARK_'+room.upper(),name='SinnohStark'+room,layout='LAYOUT_SINNOH_STARK_'+room.upper(),
                    map_type='MAP_TYPE_UNDERGROUND',requires_flash=False,allow_cycling=False,allow_escaping=False,allow_running=True,
                    battle_scene='MAP_BATTLE_SCENE_NORMAL',region='REGION_SINNOH',region_map_section='MAPSEC_PENDING_OWNER',
                    music='MUS_CAVE_OF_ORIGIN',weather='WEATHER_NONE',show_map_name=True,
                    connections=[],warp_events=warps,object_events=[],coord_events=[],bg_events=[])
        result[room]=(struct.pack('<%dH'%(w*h),*cells),header)
        audit[room]=dict(source_marked_surfaces=len(seen),slope_or_footprint_edge_stair_proxies=ramps,open_cells=sum(not v&0xc00 for v in cells),static_height_components=height_components(cells,w,h))
    return result,dict(rooms=audit,height_to_elevation={str(v):z for v,z in elevations.items()})

def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(base.git(engine,'rev-parse','--show-toplevel').decode().strip());assets={}
    for filename in ('geometry.json','source-pins.json'):
        verified=base.verified_file(repo,HERE.relative_to(repo)/filename,'HEAD')
        if (HERE/filename).read_bytes()!=verified:raise ValueError('dirty technical geometry dependency')
    geometry=json.loads((HERE/'geometry.json').read_bytes());result,audit=construct(geometry)
    def read(path):
        raw=base.verified_file(repo,engine.relative_to(repo)/path,'HEAD');assets[path]=base.sha(raw);return raw
    prefixes=['data/tilesets/primary/general/','data/tilesets/secondary/cave/']
    banks=[read(p+'metatiles.bin') for p in prefixes];pa=read(prefixes[0]+'metatile_attributes.bin')
    attrs=[bytearray(pa),bytearray(read(prefixes[1]+'metatile_attributes.bin'))]
    for mid in (513,516,517,521,528,529,530):struct.pack_into('<H',attrs[mid//512],2*(mid%512),0x1061 if mid==517 else 0x1000)
    secondary=sa=b'';packets={};images=[dual.indexed(read(p+'tiles.png')) for p in prefixes]
    for room,(raw,header) in result.items():
        border=struct.pack('<4H',*[0xc00|513]*4)
        desired=[a.a.words(banks[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',raw+border)]
        converted,secondary,sa=a.a.pack_art(raw+border,desired,attrs,banks[0],pa,secondary,sa)
        packets[room]=(converted[:len(raw)],converted[len(raw):],header)
    previews={};words={}
    for room,(raw,border,header) in packets.items():
        deps=dual.closure(raw+border,[banks[0],secondary],images)
        palettes={i:base.palette(read(prefixes[i>=6]+'palettes/%02d.pal'%i)) for i in deps['palettes']}
        previews[room]=dual.render(raw,[banks[0],secondary],images,palettes,*DIMS[room])
        words[room]={str(v&1023):a.a.attribute((pa,sa)[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',raw+border)}
    out.mkdir(parents=True);family=out/'cave-family';family.mkdir()
    for n,data in [('primary-metatiles',banks[0]),('primary-attributes',pa),('secondary-metatiles',secondary),('secondary-attributes',sa)]:
        (family/(n+'.bin')).write_bytes(data)
    for room,(raw,border,header) in packets.items():
        p=out/'staged'/room;p.mkdir(parents=True)
        (p/'map.bin').write_bytes(raw);(p/'border.bin').write_bytes(border)
        (p/'map.json').write_text(json.dumps(header,indent=2)+'\n');(p/'attributes.json').write_text(json.dumps(words[room],indent=2)+'\n');previews[room].save(p/'preview.png')
    receipt=dict(status='SOURCE_HEIGHT_PROJECTION_NATIVE_ART_NOT_RUNTIME_ACCEPTANCE',**audit,
                 geometry_sha256=base.sha((HERE/'geometry.json').read_bytes()),source_pins_sha256=base.sha((HERE/'source-pins.json').read_bytes()),
                 native_asset_sha256=assets,secondary_records=len(secondary)//16,
                 limits=geometry['limits']+['Exterior door sealed: Stark approach not constructed','No DS models/textures/props/story/encounters emitted','No production IDs/registry/save changes or ROM/native/mGBA/Save acceptance'])
    receipt['output_sha256']={str(p.relative_to(out)):base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--private-inputs',type=Path)
    args=p.parse_args()
    if args.private_inputs and extract(args.private_inputs)!=json.loads((HERE/'geometry.json').read_text()):raise ValueError('source extraction differs')
    print(json.dumps(build(args.engine,args.out),indent=2))
