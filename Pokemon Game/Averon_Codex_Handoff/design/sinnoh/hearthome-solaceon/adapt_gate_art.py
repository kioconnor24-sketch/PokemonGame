#!/usr/bin/env python3
"""Neutral current-Averon gate art over source geography; no donor pixels.

Reuses accepted pack_art. Adapted metatile IDs live in separate candidate maps;
source map.bin/header/warp data are never overwritten or registered.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('central_gate_pack',HERE.parent/'oreburgh-donor/build_city_family.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
MAPS={'Route208_Access':(13,9),'Route209_Access':(13,9)}
FLOOR=616;WALL_TOP=648;WALL_FACE=656;COUNTER=680;MAT=534


def candidate(raw,width,height,warps,source_attrs,primary,primary_attrs,secondary,secondary_attrs,*,expected_anchors=None):
    if len(raw)!=width*height*2 or width<3 or height<3:raise ValueError('invalid gate dimensions')
    expected=[(1,5),(11,5)] if expected_anchors is None else list(expected_anchors)
    if not expected or len(set(expected))!=len(expected) or [(w['x'],w['y']) for w in warps]!=expected:raise ValueError('source gate anchors changed')
    for w in warps:
        if not 0<=w['x']<width or not 0<=w['y']<height:raise ValueError('warp outside gate')
    desired=[];anchors={(w['x'],w['y']) for w in warps}
    def art(mid):return pack.words(primary if mid<512 else secondary,mid%512)
    for i,(cell,) in enumerate(struct.iter_unpack('<H',raw)):
        x,y=i%width,i//width
        if (x,y) in anchors:template=MAT
        elif (cell>>10)&3:
            template=WALL_TOP if y==0 else WALL_FACE if y==1 or x in (0,width-1) or y==height-1 else COUNTER
        else:template=FLOOR
        desired.append(art(template))
    result,records,attrs=pack.pack_art(raw,desired,source_attrs,primary,primary_attrs,secondary,secondary_attrs)
    for (old,),(new,) in zip(struct.iter_unpack('<H',raw),struct.iter_unpack('<H',result)):
        if old&0xFC00!=new&0xFC00:raise ValueError('physics changed')
        sb,si=divmod(old&1023,512);db,di=divmod(new&1023,512)
        if pack.attribute(source_attrs[sb],si)!=pack.attribute((primary_attrs,attrs)[db],di):raise ValueError('source behavior/layer changed')
    return result,records,attrs


def build(engine,out,*,source_root=None,maps=None,expected_anchors=None):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    base=pack.accepted.base;dual=pack.accepted.dual
    root=Path(base.git(engine,'rev-parse','--show-toplevel').decode().strip());rev=base.git(engine,'rev-parse','HEAD').decode().strip();used={}
    def read(path):
        raw=base.verified_file(root,engine.relative_to(root)/path,rev);used[path]=base.sha(raw);return raw
    ppath='data/tilesets/primary/building/';spath='data/tilesets/secondary/shop/'
    original_primary=read(ppath+'metatiles.bin');original_pa=read(ppath+'metatile_attributes.bin')
    primary=original_primary+bytes(8192-len(original_primary));pa=original_pa+bytes(1024-len(original_pa))
    secondary=read(spath+'metatiles.bin');sa=read(spath+'metatile_attributes.bin')
    stock=read('data/layouts/Route110_SeasideCyclingRoadEntrance/map.bin')
    if len(stock)!=15*6*2:raise ValueError('stock gate footprint changed')
    if not {FLOOR,WALL_TOP,WALL_FACE,COUNTER,MAT}<={v[0]&1023 for v in struct.iter_unpack('<H',stock)}:raise ValueError('stock gate template disappeared')
    images=[dual.indexed(read(f+'tiles.png')) for f in (ppath,spath)]
    palettes={i:base.palette(read((ppath if i<6 else spath)+'palettes/%02d.pal'%i)) for i in range(16)}
    source_root=HERE if source_root is None else Path(source_root)
    dimensions=MAPS if maps is None else maps
    maps={};source_sha={};verified=0
    for name,(w,h) in dimensions.items():
        folder=source_root/'staged'/name;raw=(folder/'map.bin').read_bytes();header=json.loads((folder/'map.json').read_text());source_sha[name]=base.sha(raw)
        if header['region_map_section']!='MAPSEC_PENDING_OWNER' or header['object_events']:raise ValueError('not a neutral source stage')
        source=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words'];source_attrs=[bytearray(1024),bytearray(1024)]
        for mid,value in source.items():
            b,i=divmod(int(mid),512);struct.pack_into('<H',source_attrs[b],i*2,value)
        anchors=None if expected_anchors is None else expected_anchors[name]
        adapted,secondary,sa=candidate(raw,w,h,header['warp_events'],source_attrs,primary,pa,secondary,sa,expected_anchors=anchors)
        maps[name]=adapted;verified+=w*h
    # pack_art accepts a512-record working primary. Its unused zero padding
    # is not an asset: retain only the real Building prefix in published output.
    primary,pa=original_primary,original_pa
    out.mkdir(parents=True)
    dependencies={}
    for name,raw in maps.items():
        w,h=dimensions[name];border=(source_root/'staged'/name/'border.bin').read_bytes();dependencies[name]=dual.closure(raw+border,[primary,secondary],images)
        (out/(name+'.bin')).write_bytes(raw);dual.render(raw,[primary,secondary],images,palettes,w,h).save(out/(name+'.png'))
    for name,data in [('primary-metatiles.bin',primary),('primary-attributes.bin',pa),('secondary-metatiles.bin',secondary),('secondary-attributes.bin',sa)]:
        (out/name).write_bytes(data)
    receipt=dict(status='NEUTRAL_EXISTING_AVERON_GATE_ADAPTATION_NOT_DONOR_VISUAL_OR_RUNTIME_ACCEPTANCE',engine_source=rev,existing_averon_sha256=used,source_map_sha256=source_sha,verified_physics_behavior_cells=verified,
        primary_records=len(primary)//16,packing_padding_removed_bytes=(8192-len(original_primary))+(1024-len(original_pa)),secondary_records=len(secondary)//16,remaining_secondary_slots=512-len(secondary)//16,source_maps_headers_warps_unchanged=True,templates=dict(floor=FLOOR,wall_top=WALL_TOP,wall_face=WALL_FACE,counter=COUNTER,exit_mat=MAT),dependencies=dependencies,
        limits=['Only existing Building/Shop/Route110 gate art; no donor pixels or colors imported','No engine install, saved identity, ROM or genuine gameplay acceptance','Source Pasos visual appearance intentionally replaced by neutral Averon gate art'])
    (out/'gate-art-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();print(json.dumps(build(a.engine,a.out),indent=2))
