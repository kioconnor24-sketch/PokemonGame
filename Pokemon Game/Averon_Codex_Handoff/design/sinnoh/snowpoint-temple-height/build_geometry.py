#!/usr/bin/env python3
"""Provisional native-art Temple geometry from verified BDHC/permission metadata.

A conservative source conversion, not DS puzzle/gameplay acceptance. No private
model/texture/props or engine files are emitted. City access remains sealed.
"""
import argparse
from collections import deque
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'snowpoint-temple-core'
s=importlib.util.spec_from_file_location('height_existing_core',SOURCE/'build_core.py')
core=importlib.util.module_from_spec(s);s.loader.exec_module(core)
FLOOR,WALL,LADDER,ICE=529,513,517,909
sha=core.a.sha;encode=core.a.encode


def construct(audit,reference):
    if audit['revision']!=reference['revision'] or audit['total_ice_tiles']!=338:
        raise ValueError('pinned source revision or ice count differs')
    recipe=json.loads((SOURCE/'shell-recipe.json').read_text())
    headers={n:packet[2] for n,packet in core.construct(recipe,reference).items()}
    result={}
    for floor,name in core.NAMES.items():
        info=audit['floors'][floor];cells=[WALL|0xc00]*1024;seen=set();ice=set()
        for point in info['walkable_center_samples']:
            x,y=point['tile']
            if not 0<x<31 or not 0<y<31 or (x,y) in seen:
                raise ValueError('duplicate or outside supported surface')
            if point['height_candidates']!=['16']:
                raise ValueError('nonflat or ambiguous walkable height requires separate conversion')
            behavior=point['source_behavior']
            if behavior not in (0,8,32,0x5e,0x5f,0x65,0x6f):
                raise ValueError('unsupported source behavior')
            seen.add((x,y));cells[y*32+x]=(ICE if behavior==32 else FLOOR)|0x3000
            if behavior==32:ice.add((x,y))
        if ice!={tuple(v['tile']) for v in info['ice']} or any(v['collision_bit'] or not v['height_candidates'] for v in info['ice']):
            raise ValueError('ice surface or permission differs')
        header=headers[name]
        for p in header['warp_events']:
            x,y=p['x'],p['y']
            if (x,y) not in seen or (x,y) in ice:
                raise ValueError('source stair unsupported or on ice')
            cells[y*32+x]=LADDER|0x3000
        # Same bounded DEV-only city closure as the existing neutral core.
        for x,y in recipe['maps'][name]['sealed_external_ports']:
            cells[y*32+x]=WALL|0xc00
        shape=list(cells)
        for y in range(1,31):
            for x in range(1,31):
                i=y*32+x
                if shape[i]&0xc00:
                    tile=521 if not shape[i+32]&0xc00 else 530 if not shape[i+1]&0xc00 else 528 if not shape[i-1]&0xc00 else WALL
                    cells[i]=(shape[i]&0xfc00)|tile
        result[name]=(struct.pack('<1024H',*cells),struct.pack('<4H',*[WALL|0xc00]*4),header)
    return result


def stop_graph(raw,start):
    """Host-only orthogonal ice sliding model; not a DS/GBA runtime assertion."""
    cells=struct.unpack('<1024H',raw);seen={tuple(start)};queue=deque(seen)
    while queue:
        x,y=queue.popleft()
        for dx,dy in ((0,-1),(0,1),(-1,0),(1,0)):
            xx,yy=x+dx,y+dy
            if not 0<=xx<32 or not 0<=yy<32 or cells[yy*32+xx]&0xc00:continue
            for _ in range(32):
                if cells[yy*32+xx]&1023!=ICE:break
                nx,ny=xx+dx,yy+dy
                if not 0<=nx<32 or not 0<=ny<32 or cells[ny*32+nx]&0xc00:break
                xx,yy=nx,ny
            if (xx,yy) not in seen:seen.add((xx,yy));queue.append((xx,yy))
    return seen


def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:
        raise ValueError('new off-engine output required')
    audit=json.loads((HERE/'geometry-audit.json').read_text());reference=json.loads((SOURCE/'portal-reference.json').read_text())
    maps=construct(audit,reference);a=core.a;assets={}
    root=Path(a.base.git(engine,'rev-parse','--show-toplevel').decode().strip())
    def read(path):
        data=a.base.verified_file(root,engine.relative_to(root)/path,'HEAD');assets[path]=sha(data);return data
    paths=['data/tilesets/primary/general/','data/tilesets/secondary/cave/']
    banks=[read(p+'metatiles.bin') for p in paths];attrs=[read(p+'metatile_attributes.bin') for p in paths]
    images=[a.dual.indexed(read(p+'tiles.png')) for p in paths]
    for tile,behavior in ((LADDER,0x61),(ICE,0x20)):
        if a.art.attribute(attrs[tile//512],tile%512)&511!=behavior:
            raise ValueError('native ladder or ice behavior differs')
    out.mkdir(parents=True);facts={}
    for name,(raw,border,header) in maps.items():
        deps=a.dual.closure(raw+border,banks,images)
        pals={i:a.base.palette(read(paths[i>=6]+'palettes/%02d.pal'%i)) for i in deps['palettes']}
        preview=a.dual.render(raw,banks,images,pals,32,32)
        used={w[0]&1023 for w in struct.iter_unpack('<H',raw+border)}
        words={str(i):a.art.attribute(attrs[i//512],i%512) for i in sorted(used)}
        folder=out/'staged'/name;folder.mkdir(parents=True)
        for path,data in [('map.bin',raw),('border.bin',border),('map.json',encode(header)),('attributes.json',encode(dict(used_source_attribute_words=words,source_tilesets=['gTileset_General','gTileset_Cave'])))]:
            (folder/path).write_bytes(data)
        preview.save(folder/'averon.png')
        reachable=stop_graph(raw,(header['warp_events'][0]['x'],header['warp_events'][0]['y']))
        stairs={(p['x'],p['y']) for p in header['warp_events']}
        if not stairs<=reachable:raise ValueError('source stairs disconnected under host ice model')
        facts[name]=dict(dimensions=[32,32],map_sha256=sha(raw),ice_tiles=sum((w[0]&1023)==ICE for w in struct.iter_unpack('<H',raw)),
            host_stoppable_cells=len(reachable),all_stairs_host_reachable=True,dependencies=deps)
    receipt=dict(status='PROVISIONAL_SOURCE_GEOMETRY_AND_NATIVE_ART_NOT_RUNTIME_ACCEPTED',source_revision=audit['revision'],
        input_sha256={'geometry-audit.json':sha((HERE/'geometry-audit.json').read_bytes()),'portal-reference.json':sha((SOURCE/'portal-reference.json').read_bytes())},
        native_asset_sha256=assets,maps=facts,limitations=['Tile-center surfaces and permissions are verified, not DS movement/edge/model parity',
        'All source permission-clear supported centers are flat16; native elevation3 is a provisional single-layer adaptation',
        'Ice stopping and stair access are host-only; genuine paired ROM/native/mGBA/Save acceptance is still required',
        'City door sealed; no story, legendary, encounters, permanent IDs or production registry'])
    (out/'source-receipt.json').write_bytes(encode(receipt));return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();print(json.dumps(build(a.engine,a.out),indent=2))
