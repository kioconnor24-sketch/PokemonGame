#!/usr/bin/env python3
"""Chateau entrance: current Averon Museum art, with four explicit substitutions.

All other used graphic patterns and all used GBA palette colors must match the
pinned source. Source pictures/colors are read for comparison, never published.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct
import io
from PIL import Image

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('entrance_reuse',HERE/'render_existing.py')
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
CHANGED={916,917,932,933}


def build(donor,engine,out):
    donor,engine,out=map(lambda p:Path(p).resolve(),(donor,engine,out))
    if out.exists() or out.is_relative_to(engine) or out.is_relative_to(donor) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    d=shared.dual;b=d.base
    if b.git(donor,'rev-parse','HEAD').decode().strip()!=shared.REVISION:raise ValueError('wrong donor revision')
    root=Path(b.git(engine,'rev-parse','--show-toplevel').decode().strip());rev=b.git(engine,'rev-parse','HEAD').decode().strip()
    source_hash={};current_hash={}
    def source(path):
        raw=b.git(donor,'show',shared.REVISION+':'+path);source_hash[path]=b.sha(raw);return raw
    def current(path):
        raw=b.verified_file(root,engine.relative_to(root)/path,rev);current_hash[path]=b.sha(raw);return raw
    primary='data/tilesets/primary/building/';secondary='data/tilesets/secondary/lilycove_museum/'
    pictures=[current(f+'tiles.png') for f in (primary,secondary)];source_pictures=[source(f+'tiles.png') for f in (primary,secondary)]
    if pictures[0]!=source_pictures[0]:raise ValueError('Building pixels changed')
    images=[d.indexed(x) for x in pictures];source_images=[d.indexed(x) for x in source_pictures]
    p=current(primary+'metatiles.bin');pa=current(primary+'metatile_attributes.bin')
    if p!=source(primary+'metatiles.bin') or pa!=source(primary+'metatile_attributes.bin'):raise ValueError('primary source contract changed')
    source_records=source(secondary+'metatiles.bin');source_attrs=source(secondary+'metatile_attributes.bin')
    folder=HERE/'staged/OldChateau_Entrance';raw=(folder/'map.bin').read_bytes();border=(folder/'border.bin').read_bytes()
    if len(raw)!=19*17*2:raise ValueError('Entrance geometry changed')
    mids={v[0]&1023 for v in struct.iter_unpack('<H',raw+border)};count=max(mids)-511
    records=bytearray(count*16);attrs=bytearray(count*2)
    for mid in mids:
        if mid<512:continue
        i=mid-512
        if len(source_records)<(i+1)*16 or len(source_attrs)<(i+1)*2:raise ValueError('source metadata out of bounds')
        records[i*16:(i+1)*16]=source_records[i*16:(i+1)*16];attrs[i*2:(i+1)*2]=source_attrs[i*2:(i+1)*2]
    deps=d.closure(raw+border,[p,records],images);palettes={};source_palettes={}
    for i in deps['palettes']:
        path=(primary if i<6 else secondary)+'palettes/%02d.pal'%i
        palettes[i]=b.palette(current(path));source_palettes[i]=b.palette(source(path))
        if palettes[i]!=source_palettes[i]:raise ValueError('used source palette differs')
    different=[]
    for tile in deps['graphic_tiles']:
        bank,i=divmod(tile,512);box=(i%16*8,i//16*8,i%16*8+8,i//16*8+8)
        if images[bank].crop(box).tobytes()!=source_images[bank].crop(box).tobytes():different.append(tile)
    if set(different)!=CHANGED:raise ValueError('unreviewed Museum pixel mismatch: '+str(different))
    affected=[(i%19,i//19) for i,(v,) in enumerate(struct.iter_unpack('<H',raw)) if (v&1023)==660]
    if len(affected)!=12:raise ValueError('substitution footprint changed')
    for mid in mids:
        bank,i=divmod(mid,512)
        words=struct.unpack_from('<8H',(p,records)[bank],i*16)
        if any((word&1023) in CHANGED for word in words) and mid!=660:raise ValueError('unexpected substituted cell type')
    # The four current Museum replacement patterns are transparent placeholders.
    # Static RGB compositing hid the backdrop leak, but settled real GBA frames
    # show a magenta tile. Reuse an already verified opaque floor record; keep
    # every source cell and its complete660 behavior/layer attribute unchanged.
    records[(660-512)*16:(661-512)*16]=records[(649-512)*16:(650-512)*16]
    deps=d.closure(raw+border,[p,records],images)
    image=d.render(raw,[p,records],images,palettes,19,17)
    reference=d.render(raw,[p,source_records],source_images,source_palettes,19,17)
    left,right=image.tobytes(),reference.tobytes();stride=len(image.getbands())
    different_pixels=sum(left[i:i+stride]!=right[i:i+stride] for i in range(0,len(left),stride))
    out.mkdir(parents=True);image.save(out/'averon.png');(out/'entrance-metatiles.bin').write_bytes(records);(out/'entrance-attributes.bin').write_bytes(attrs)
    receipt=dict(status='EXISTING_AVERON_ENTRANCE_WITH_EXPLICIT_LIMITED_ART_SUBSTITUTION_NOT_RUNTIME_ACCEPTANCE',donor_revision=shared.REVISION,engine_source=rev,
        source_sha256=source_hash,existing_averon_sha256=current_hash,geometry_sha256=b.sha(raw),source_physics_and_attributes_unchanged=True,
        dependencies=deps,substituted_graphic_tile_ids=sorted(CHANGED),substituted_metatile=660,affected_cells=affected,changed_render_pixels=different_pixels,
        all_other_used_patterns_identical=True,all_used_palette_colors_equal=True,secondary_records=count,
        runtime_opaque_floor_repair=dict(metatile=660,existing_floor_template=649,affected_cells=len(affected),source_attribute_preserved=True),
        limits=['Metatile660 uses accepted opaque Museum floor649 to replace four transparent placeholder patterns; not source RGB equivalence','No donor PNG/palette written or imported, no story/objects/encounters','Static art only; exact repaired ROM/native/mGBA evidence is separate from pre-repair functional runs'])
    (out/'entrance-graphics-compatibility.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('donor','engine','out'):p.add_argument('--'+n,required=True,type=Path)
    a=p.parse_args();print(json.dumps(build(a.donor,a.engine,a.out),indent=2))
