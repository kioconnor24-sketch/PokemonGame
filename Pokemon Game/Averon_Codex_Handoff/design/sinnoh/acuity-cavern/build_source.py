#!/usr/bin/env python3
"""Native-art Acuity Cavern from pinned supported surface metadata, no content."""
import argparse
import importlib.util
import json
import hashlib
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('acuity_cavern_native',HERE.parent/'oreburgh-donor/build_city_family.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
base=a.accepted.base;dual=a.accepted.dual
FLOOR,WALL,REFLECTIVE=529,513,161


def read_source(inputs):
    root=Path(inputs).resolve();pins=json.loads((HERE/'source-pins.json').read_text());raws={}
    for key,pin in pins['files'].items():
        relative=Path(pin['private_input_name']);p=(root/relative).resolve()
        if relative.is_absolute() or not p.is_relative_to(root):raise ValueError('private input escapes root')
        raw=p.read_bytes()
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if len(raw)!=pin['bytes'] or base.sha(raw)!=pin['sha256'] or blob!=pin['git_blob']:raise ValueError('source identity differs')
        raws[key]=raw
    if json.loads(raws['matrix'])['maps']!=[['MAP_561']]:raise ValueError('source matrix differs')
    events=json.loads(raws['events'])['warp_events']
    if events!=[dict(x=14,z=29,dest_header_id='MAP_HEADER_LAKE_ACUITY',dest_warp_id=1)]:raise ValueError('source warp differs')
    raw=raws['land_data'];sizes=struct.unpack_from('<4I',raw)
    if sizes!=(2048,0,46912,198) or 16+sum(sizes)!=len(raw):raise ValueError('source section bounds differ')
    spec=importlib.util.spec_from_file_location('acuity_existing_bdhc',HERE.parent/'snowpoint-temple-height/parse_bdhc.py')
    b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
    data=b.decode(raw[16+sum(sizes[:3]):]);words=struct.unpack_from('<1024H',raw,16);points=[]
    for i,word in enumerate(words):
        if word&0x7f00 or word&255 not in (0,0x1d,0x65,0x6f):raise ValueError('unsupported source permission')
        if word&0x8000:continue
        x,y=i%32,i//32
        if [v for _,v in b.tile_candidates(data,x,y)]!=[16*b.FX]:raise ValueError('nonflat source surface')
        for dx,dz in ((-8,-8),(-8,8),(8,-8),(8,8)):
            if not any(v==16*b.FX for _,v in b.candidates(data,(x-16)*b.TILE+b.TILE//2+dx*b.FX,(y-16)*b.TILE+b.TILE//2+dz*b.FX)):
                raise ValueError('unsupported source footprint')
        points.append(dict(tile=[x,y],source_behavior=word&255))
    return dict(dimensions=[32,32],height=16,flat_footprint_samples=len(points)*4,walkable=points,sealed_source_exit=[14,29],technical_warp=events[0],runtime_accepted=False)


def construct(geometry):
    if geometry['dimensions']!=[32,32] or geometry['height']!=16 or geometry['flat_footprint_samples']!=1548:
        raise ValueError('verified flat geometry required')
    cells=[WALL|0xc00]*1024;seen=set();reflection=0
    for p in geometry['walkable']:
        x,y=p['tile'];behavior=p['source_behavior']
        if not 0<x<31 or not 0<y<31 or (x,y) in seen:raise ValueError('duplicate or outside surface')
        if behavior not in (0,0x1d,0x6f):raise ValueError('unreviewed source behavior')
        seen.add((x,y));cells[y*32+x]=(REFLECTIVE if behavior==0x1d else FLOOR)|0x3000
        reflection+=behavior==0x1d
    if len(seen)!=387 or reflection!=182:raise ValueError('source surface or reflective count differs')
    if geometry['sealed_source_exit']!=[14,29] or geometry['technical_warp']!=dict(x=14,z=29,dest_header_id='MAP_HEADER_LAKE_ACUITY',dest_warp_id=1):
        raise ValueError('unverified source exit')
    cells[29*32+14]=WALL|0xc00
    shape=list(cells)
    for y in range(1,31):
        for x in range(1,31):
            i=y*32+x
            if shape[i]&0xc00:
                tile=521 if not shape[i+32]&0xc00 else 530 if not shape[i+1]&0xc00 else 528 if not shape[i-1]&0xc00 else WALL
                cells[i]=(shape[i]&0xfc00)|tile
    header=dict(id='MAP_SINNOH_ACUITY_CAVERN',name='SinnohAcuityCavern',layout='LAYOUT_SINNOH_ACUITY_CAVERN',map_type='MAP_TYPE_UNDERGROUND',requires_flash=False,
        allow_cycling=False,allow_escaping=False,allow_running=True,battle_scene='MAP_BATTLE_SCENE_NORMAL',region='REGION_SINNOH',region_map_section='MAPSEC_PENDING_OWNER',
        music='MUS_CAVE_OF_ORIGIN',weather='WEATHER_NONE',show_map_name=True,connections=[],warp_events=[],object_events=[],coord_events=[],bg_events=[])
    return struct.pack('<1024H',*cells),struct.pack('<4H',*[WALL|0xc00]*4),header


def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    geometry=json.loads((HERE/'geometry.json').read_text());raw,border,header=construct(geometry)
    repo=Path(base.git(engine,'rev-parse','--show-toplevel').decode().strip());assets={}
    def read(path):
        data=base.verified_file(repo,engine.relative_to(repo)/path,'HEAD');assets[path]=base.sha(data);return data
    paths=['data/tilesets/primary/general/','data/tilesets/secondary/cave/']
    banks=[read(p+'metatiles.bin') for p in paths];pa=read(paths[0]+'metatile_attributes.bin');original_attrs=[pa,read(paths[1]+'metatile_attributes.bin')]
    source_attrs=[bytearray(v) for v in original_attrs]
    used={v[0]&1023 for v in struct.iter_unpack('<H',raw+border)}
    for tile in used:
        bank,index=divmod(tile,512)
        # Explicit semantic conversion: DS0x1D no-splash reflective floor to
        # existing native MB_REFLECTION_UNDER_BRIDGE, never surfable water.
        struct.pack_into('<H',source_attrs[bank],index*2,0x102b if tile==REFLECTIVE else 0x1000)
    desired=[a.words(banks[tile//512],tile%512) for (v,) in struct.iter_unpack('<H',raw+border) for tile in [v&1023]]
    converted,secondary,sa=a.pack_art(raw+border,desired,source_attrs,banks[0],pa,b'',b'')
    for (old,),(new,) in zip(struct.iter_unpack('<H',raw+border),struct.iter_unpack('<H',converted)):
        bank,index=divmod(new&1023,512)
        if old&0xfc00!=new&0xfc00 or a.attribute((pa,sa)[bank],index)!=a.attribute(source_attrs[(old&1023)//512],old%512):raise ValueError('native semantic conversion differs')
    images=[dual.indexed(read(p+'tiles.png')) for p in paths];deps=dual.closure(converted,[banks[0],secondary],images)
    palettes={i:base.palette(read(paths[i>=6]+'palettes/%02d.pal'%i)) for i in deps['palettes']}
    preview=dual.render(converted[:2048],[banks[0],secondary],images,palettes,32,32)
    out.mkdir(parents=True);staged=out/'staged';staged.mkdir();family=out/'cave-family';family.mkdir()
    for name,data in [('map.bin',converted[:2048]),('border.bin',converted[2048:]),('map.json',(json.dumps(header,indent=2)+'\n').encode())]:
        (staged/name).write_bytes(data)
    words={str(v[0]&1023):a.attribute((pa,sa)[(v[0]&1023)//512],v[0]%512) for v in struct.iter_unpack('<H',converted)}
    (staged/'attributes.json').write_text(json.dumps(words,indent=2)+'\n');preview.save(staged/'averon.png')
    for name,data in [('primary-metatiles',banks[0]),('primary-attributes',pa),('secondary-metatiles',secondary),('secondary-attributes',sa)]:
        (family/(name+'.bin')).write_bytes(data)
    receipt=dict(status='SOURCE_GEOMETRY_NATIVE_ART_ONLY_NO_RUNTIME_ACCEPTANCE',source_pins_sha256=base.sha((HERE/'source-pins.json').read_bytes()),geometry_sha256=base.sha((HERE/'geometry.json').read_bytes()),
        native_asset_sha256=assets,dimensions=[32,32],open_cells=386,reflective_no_surf_no_splash_cells=182,secondary_records=len(secondary)//16,dependencies=deps,
        output_sha256={str(p.relative_to(out)):base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()},
        limits=['Exact semantic mapping is explicit, not preservation of DS numeric behavior IDs','No DS model/texture/props/story/legendary/encounter data emitted',
        'Source door14,29 sealed: GBA lake has no reciprocal warp1','Tile centers/corners are source-supported flat16; native elevation3/proxy art still need runtime proof',
        'No production IDs, registry, engine or gameplay acceptance'])
    (out/'source-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--private-inputs',type=Path)
    args=p.parse_args()
    if args.private_inputs is not None and read_source(args.private_inputs)!=json.loads((HERE/'geometry.json').read_text()):raise ValueError('committed geometry differs from source')
    print(json.dumps(build(args.engine,args.out),indent=2))
