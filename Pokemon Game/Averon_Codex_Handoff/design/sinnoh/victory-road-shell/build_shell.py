#!/usr/bin/env python3
"""Author the original three-floor physical shell from explicit rooms/corridors.

Not a donor converter. Uses the existing Averon graphic renderer unchanged.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('victory_existing_art',HERE.parent/'oreburgh-donor/build_city_family.py')
art=importlib.util.module_from_spec(spec);spec.loader.exec_module(art)
base=art.accepted.base;dual=art.accepted.dual
NAMES={'1f':'SinnohVictoryRoad_1F','2f':'SinnohVictoryRoad_2F','b1f':'SinnohVictoryRoad_B1F'}
IDS={n:'MAP_SINNOH_VICTORY_ROAD_'+ref.upper() for ref,n in NAMES.items()}
FLOOR=529;WALL=513;LADDER=517
sha=lambda data:hashlib.sha256(data).hexdigest()
encode=lambda data:(json.dumps(data,indent=2)+'\n').encode()


def construct(recipe,reference):
    maps=recipe['maps'];refs=reference['files'];result={}
    if set(maps)!=set(NAMES.values()):raise ValueError('exact three core floors required')
    for name,plan in maps.items():
        w,h=plan['width'],plan['height']
        if min(w,h)<3 or (w+15)*(h+14)>10240:raise ValueError('invalid map buffer')
        grid=[WALL|0xC00]*(w*h)
        def floor(x,y):
            if not (1<=x<w-1 and 1<=y<h-1):raise ValueError('floor outside closed border')
            grid[y*w+x]=FLOOR|0x3000
        for x,y,rw,rh in plan['rooms']:
            if min(rw,rh)<1:raise ValueError('empty room')
            for yy in range(y,y+rh):
                for xx in range(x,x+rw):floor(xx,yy)
        for line in plan['corridors']:
            for (x,y),(tx,ty) in zip(line,line[1:]):
                if x!=tx and y!=ty:raise ValueError('corridors must be orthogonal')
                dx=(tx>x)-(tx<x);dy=(ty>y)-(ty<y)
                while True:
                    for xx,yy in ((x,y),(x+1,y),(x-1,y),(x,y+1),(x,y-1)):floor(xx,yy)
                    if (x,y)==(tx,ty):break
                    x+=dx;y+=dy
        source=refs[plan['reference']]['warp_events'];warps=[]
        for old in plan['interior_warp_indices']:
            v=source[old];target_ref=v['dest_header_id'].removeprefix('MAP_HEADER_VICTORY_ROAD_').lower()
            if target_ref not in NAMES:raise ValueError('external destination cannot activate')
            target=NAMES[target_ref];target_indices=maps[target]['interior_warp_indices']
            if v['dest_warp_id'] not in target_indices:raise ValueError('missing counterpart')
            x,y=v['x'],v['z'];floor(x,y);grid[y*w+x]=LADDER|0x3000
            warps.append(dict(x=x,y=y,elevation=0,dest_map=IDS[target],dest_warp_id=str(target_indices.index(v['dest_warp_id']))))
        for x,y in plan['sealed_external_ports']:
            if not (0<=x<w and 0<=y<h):raise ValueError('sealed port outside map')
            grid[y*w+x]=WALL|0xC00
        # Stock cave ceiling/side faces follow the authored room perimeter.
        # This changes only art on already solid cells, never the walk graph.
        shape=list(grid)
        for y in range(1,h-1):
            for x in range(1,w-1):
                i=y*w+x
                if not shape[i]&0xC00:continue
                tile=521 if not shape[i+w]&0xC00 else 530 if not shape[i+1]&0xC00 else 528 if not shape[i-1]&0xC00 else WALL
                grid[i]=(shape[i]&0xFC00)|tile
        header=dict(id=IDS[name],name=name,layout='LAYOUT_'+IDS[name][4:],map_type='MAP_TYPE_UNDERGROUND',requires_flash=False,
            allow_cycling=False,allow_escaping=False,allow_running=True,battle_scene='MAP_BATTLE_SCENE_NORMAL',region='REGION_SINNOH',
            region_map_section='MAPSEC_PENDING_OWNER',music='MUS_PETALBURG_WOODS',weather='WEATHER_NONE',show_map_name=True,
            connections=[],warp_events=warps,object_events=[],coord_events=[],bg_events=[])
        result[name]=(struct.pack('<%dH'%len(grid),*grid),struct.pack('<4H',*[WALL|0xC00]*4),header)
    by_id={v[2]['id']:v[2] for v in result.values()}
    for name,(_,_,header) in result.items():
        for i,p in enumerate(header['warp_events']):
            other=by_id[p['dest_map']]['warp_events'][int(p['dest_warp_id'])]
            if other['dest_map']!=header['id'] or int(other['dest_warp_id'])!=i:raise ValueError('nonreciprocal floor stair')
    return result


def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    recipe=json.loads((HERE/'shell-recipe.json').read_text());reference=json.loads((HERE/'portal-reference.json').read_text())
    result=construct(recipe,reference);root=Path(base.git(engine,'rev-parse','--show-toplevel').decode().strip());assets={}
    def read(path):
        data=base.verified_file(root,engine.relative_to(root)/path,'HEAD');assets[path]=sha(data);return data
    paths=['data/tilesets/primary/general/','data/tilesets/secondary/cave/']
    banks=[read(p+'metatiles.bin') for p in paths];attrs=[read(p+'metatile_attributes.bin') for p in paths]
    images=[dual.indexed(read(p+'tiles.png')) for p in paths];outputs={};facts={}
    for name,(raw,border,header) in result.items():
        deps=dual.closure(raw+border,banks,images);pals={i:base.palette(read(paths[i>=6]+'palettes/%02d.pal'%i)) for i in deps['palettes']}
        used={v[0]&1023 for v in struct.iter_unpack('<H',raw+border)}
        words={str(i):art.attribute(attrs[i//512],i%512) for i in sorted(used)}
        if words[str(LADDER)]&511!=0x61:raise ValueError('native ladder behavior differs')
        plan=recipe['maps'][name];preview=dual.render(raw,banks,images,pals,plan['width'],plan['height'])
        outputs[name]=(raw,border,header,words,preview)
        facts[name]=dict(dimensions=[plan['width'],plan['height']],cells=len(raw)//2,retained_technical_stairs=len(header['warp_events']),
            source_warp_indices=plan['interior_warp_indices'],sealed_external_ports=plan['sealed_external_ports'],dependencies=deps,map_sha256=sha(raw))
    out.mkdir(parents=True)
    for name,(raw,border,header,words,preview) in outputs.items():
        f=out/'staged'/name;f.mkdir(parents=True);(f/'map.bin').write_bytes(raw);(f/'border.bin').write_bytes(border)
        (f/'map.json').write_bytes(encode(header));(f/'attributes.json').write_bytes(encode(dict(used_source_attribute_words=words,source_tilesets=['gTileset_General','gTileset_Cave'])))
        preview.save(f/'averon.png')
    receipt=dict(status='ORIGINAL_SOURCE_AND_PERMITTED_ART_ONLY_NOT_RUNTIME_OR_PRODUCTION',reference_revision=reference['revision'],
        input_sha256={p:sha((HERE/p).read_bytes()) for p in ('shell-recipe.json','portal-reference.json')},existing_averon_sha256=assets,maps=facts,
        limits=recipe['limits'])
    (out/'source-receipt.json').write_bytes(encode(receipt));return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();r=build(a.engine,a.out);print(json.dumps(r['maps'],indent=2))
