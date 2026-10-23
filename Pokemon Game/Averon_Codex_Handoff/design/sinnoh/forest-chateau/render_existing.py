#!/usr/bin/env python3
"""Render four Chateau interiors using byte-proven existing Averon pixels only.

No donor image/palette is published. All palette/graphic dependencies actually
used by these layouts must match; metadata is isolated rather than global.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import io
from PIL import Image

HERE=Path(__file__).resolve().parent
SCRIPTS=HERE.parents[3]/'scripts'
spec=importlib.util.spec_from_file_location('chateau_dual',SCRIPTS/'sinnoh-dual-bank-family.py')
dual=importlib.util.module_from_spec(spec);spec.loader.exec_module(dual)
REVISION='38228bb574a3557345852b758d5f1a65eb01bb22'
MAPS={'OldChateau_DiningRoom':(40,10),'OldChateau_2F':(38,14),
      'OldChateau_SideRoom_1':(10,10),'OldChateau_SideRoom_2':(10,10)}


def build(donor,engine,out):
    donor,engine,out=map(lambda p:Path(p).resolve(),(donor,engine,out))
    if out.exists() or out.is_relative_to(donor) or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    if dual.base.git(donor,'rev-parse','HEAD').decode().strip()!=REVISION:raise ValueError('wrong donor revision')
    consumed={};current={};root=Path(dual.base.git(engine,'rev-parse','--show-toplevel').decode().strip());rev=dual.base.git(engine,'rev-parse','HEAD').decode().strip()
    def source(path):
        value=dual.base.git(donor,'show',REVISION+':'+path);consumed[path]=dual.base.sha(value);return value
    def existing(path):
        value=dual.base.verified_file(root,engine.relative_to(root)/path,rev);current[path]=dual.base.sha(value);return value
    primary='data/tilesets/primary/building/';secondary='data/tilesets/secondary/generic_building/'
    raw_images=[existing(f+'tiles.png') for f in (primary,secondary)]
    for f,raw in zip((primary,secondary),raw_images):
        if source(f+'tiles.png')!=raw:raise ValueError('pixels are not the proven current Averon sheets')
    images=[dual.indexed(raw) for raw in raw_images]
    p=existing(primary+'metatiles.bin');pa=existing(primary+'metatile_attributes.bin')
    if p!=source(primary+'metatiles.bin') or pa!=source(primary+'metatile_attributes.bin'):raise ValueError('Building metadata mismatch')
    records=source(secondary+'metatiles.bin');attrs=source(secondary+'metatile_attributes.bin')
    needed=set();maps={}
    for name,(w,h) in MAPS.items():
        folder=HERE/'staged'/name;raw=(folder/'map.bin').read_bytes();border=(folder/'border.bin').read_bytes()
        if len(raw)!=w*h*2:raise ValueError('map dimensions changed')
        maps[name]=(raw,border)
        needed|={v[0]&1023 for v in struct.iter_unpack('<H',raw+border) if v[0]&1023>=512}
    size=max(needed)-511;s=bytearray(size*16);sa=bytearray(size*2)
    for mid in needed:
        i=mid-512
        if len(records)<(i+1)*16 or len(attrs)<(i+1)*2:raise ValueError('source metatile missing')
        s[i*16:(i+1)*16]=records[i*16:(i+1)*16];sa[i*2:(i+1)*2]=attrs[i*2:(i+1)*2]
    deps={n:dual.closure(raw+border,[p,s],images) for n,(raw,border) in maps.items()}
    palette_ids=sorted({i for d in deps.values() for i in d['palettes']})
    palettes={};donor_palettes={}
    for i in palette_ids:
        f=(primary if i<6 else secondary)+'palettes/%02d.pal'%i
        palettes[i]=dual.base.palette(existing(f));donor_palettes[i]=dual.base.palette(source(f))
        if palettes[i]!=donor_palettes[i]:raise ValueError('used palette differs from source: '+str(i))
    out.mkdir(parents=True)
    for name,(raw,_) in maps.items():
        w,h=MAPS[name];current_render=dual.render(raw,[p,s],images,palettes,w,h)
        # Pixel sheets are byte-identical; independently render full source metadata
        # and source parsed colors in memory. Never write the donor rendering.
        donor_render=dual.render(raw,[p,records],images,donor_palettes,w,h)
        if current_render.tobytes()!=donor_render.tobytes():raise ValueError('rendered pixels differ')
        current_render.save(out/(name+'.png'))
    (out/'generic-metatiles.bin').write_bytes(s);(out/'generic-attributes.bin').write_bytes(sa)
    receipt=dict(status='EXISTING_AVERON_RENDER_ONLY_NOT_RUNTIME_ACCEPTANCE',donor_revision=REVISION,engine_source=rev,
        source_sha256=consumed,existing_averon_sha256=current,used_secondary_ids=sorted(needed),secondary_records=size,
        primary_pixels_byte_identical=True,secondary_pixels_byte_identical=True,all_used_palette_colors_equal=True,
        rendered_rgb_equal_source=True,used_palette_ids=palette_ids,dependencies=deps,
        limits=['Only four GenericBuilding interiors verified; Forest Valor and Entrance Museum remain unadapted','No production save identity, ROM, warp/follower or emulator acceptance'])
    (out/'graphics-compatibility.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('donor','engine','out'):p.add_argument('--'+n,required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.donor,args.engine,args.out),indent=2))
