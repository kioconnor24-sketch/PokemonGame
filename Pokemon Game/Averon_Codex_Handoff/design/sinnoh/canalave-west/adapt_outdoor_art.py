#!/usr/bin/env python3
"""Permitted Averon art over pinned Canalave/218 geometry; no donor pixels.

Reuses the reviewed pack_art and Celestic facade/source guards. The source maps
and complete collision/elevation/behavior/layer words are immutable. This is an
isolated art candidate, not an engine installation or Surf/bridge acceptance.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('canalave_art_templates',HERE.parent/'celestic-north/adapt_outdoor_art.py')
templates=importlib.util.module_from_spec(spec);spec.loader.exec_module(templates)
pack=templates.pack
MAPS={'Route218':(64,32),'CanalaveCity':(38,64)}
HOUSE=(31,15,5,5);CENTER=(15,35,4,4)
FACADES={'Route218':[((0,17,4,4),HOUSE),((60,21,4,4),HOUSE)], 'CanalaveCity':[
    ((5,12,5,6),HOUSE),((27,10,4,4),HOUSE),((26,19,5,4),CENTER),
    ((6,27,7,5),HOUSE),((23,28,4,4),HOUSE),((23,36,4,4),HOUSE),
    ((7,36,4,4),HOUSE),((8,43,4,3),HOUSE),((23,43,4,3),HOUSE),
    ((34,47,4,4),HOUSE)]}
# Enumerated source dependencies, independently pinned by source(). Unknown
# donor IDs fail closed rather than silently rendering a generic ground tile.
SECONDARY={
 'Route218':{829:1,832:13,862:1,863:1,864:1,867:1,
              872:434,873:435,874:436,875:440,876:441,877:442,878:443,879:444,887:453},
 'CanalaveCity':dict.fromkeys((512,513,517,518,519,520,521,522,525,526,527,531,532,533,
  536,537,538,539,540,541,544,545,546,547,548,549,550,552,553,554,555,556,557,558,559,
  560,561,562,563,564,565,566,567,568,569,570,571,572,573,574,575,576,577,578,579,
  580,581,582,583,588,589,590,592,593,594,595,596,597,599,604,605,606,607,608,609,610,
  611,612,613,614,615,616,617,618,619,620,621,624,625,626,627,628,629,630,632,
  633,634,635,636,637,638,639,640,641,642,643,644,645,646,647,648,649,651,652,
  653,654,655,656,657,658,660,662,663,664,668),699)}
SECONDARY['CanalaveCity'].update({517:93,518:94,519:95,525:93,526:95,527:94,
    531:93,532:94,533:95,563:21,564:22,565:23,588:434,589:435,590:436,
    647:207,648:207,649:207,651:207,652:207,657:368,658:368,662:368,663:368})
# No water/bridge flattening: existing General records remain available verbatim.
PRIMARY={}
templates.HERE=HERE;templates.MAPS=MAPS;templates.FACADES=FACADES
templates.SECONDARY=SECONDARY;templates.PRIMARY=PRIMARY;templates.BRIDGE=set()
source=templates.source
BRIDGES={'Route218':{872,873,874,875,876,877,878,879,887},
         'CanalaveCity':{637,638,639,645,646,647,653,654,655,656,660,664,668}}


def desired_art(name,raw,border,header,attrs,banks,stock):
    desired=templates.desired_art(name,raw,border,header,attrs,banks,stock)
    # One existing wood plank record, preserving each original attribute word.
    # Repeated walkways must not accidentally become a resampled house facade.
    plank=pack.words(banks[1],528-512)
    wood=tuple(plank[i] for i in (1,1,3,3,5,5,7,7))
    for i,(cell,) in enumerate(struct.iter_unpack('<H',raw+border)):
        if cell&1023 in BRIDGES[name]:desired[i]=wood
    return desired


def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    base=pack.accepted.base;dual=pack.accepted.dual
    root=Path(base.git(engine,'rev-parse','--show-toplevel').decode().strip());rev=base.git(engine,'rev-parse','HEAD').decode().strip();assets={}
    def read(path):
        data=base.verified_file(root,engine.relative_to(root)/path,rev);assets[path]=base.sha(data);return data
    paths=['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/']
    stock_banks=[read(p+'metatiles.bin') for p in paths];pa=read(paths[0]+'metatile_attributes.bin')
    if len(stock_banks[0])!=8192 or len(pa)!=1024:raise ValueError('primary capacity contract changed')
    stock=struct.unpack('<2400H',read('data/layouts/RustboroCity/map.bin'))
    images=[dual.indexed(read(p+'tiles.png')) for p in paths]
    secondary=sa=b'';result={};hashes={};verified=0;heights={}
    for name,(w,h) in MAPS.items():
        raw,border,header,attrs=source(name)
        hashes[name]={p:base.sha((HERE/'staged'/name/p).read_bytes()) for p in ('map.bin','border.bin','map.json','attributes.json')}
        source_attrs=[bytearray(1024),bytearray(1024)]
        for mid,value in attrs.items():b,i=divmod(int(mid),512);struct.pack_into('<H',source_attrs[b],i*2,value)
        wanted=desired_art(name,raw,border,header,attrs,stock_banks,stock)
        adapted,secondary,sa=pack.pack_art(raw+border,wanted,source_attrs,stock_banks[0],pa,secondary,sa)
        for (old,),(new,) in zip(struct.iter_unpack('<H',raw+border),struct.iter_unpack('<H',adapted)):
            b,i=divmod(new&1023,512)
            if old&0xFC00!=new&0xFC00 or pack.attribute((pa,sa)[b],i)!=attrs[str(old&1023)]:
                raise ValueError('source physics/full behavior/layer changed')
            verified+=1
        heights[name]=sum(c[0]>>12==15 for c in struct.iter_unpack('<H',raw))
        result[name]=(adapted[:len(raw)],adapted[len(raw):])
    banks=[stock_banks[0],secondary];dependencies={};previews={}
    for name,(raw,border) in result.items():
        dependencies[name]=dual.closure(raw+border,banks,images)
        palettes={i:base.palette(read(paths[i>=6]+'palettes/%02d.pal'%i)) for i in dependencies[name]['palettes']}
        previews[name]=dual.render(raw,banks,images,palettes,*MAPS[name])
    out.mkdir(parents=True);(out/'outdoor-family').mkdir()
    for name,(raw,border) in result.items():
        folder=out/name;folder.mkdir();(folder/'averon-map.bin').write_bytes(raw);(folder/'averon-border.bin').write_bytes(border);previews[name].save(folder/'averon.png')
    for name,data in [('primary-metatiles',banks[0]),('primary-attributes',pa),('secondary-metatiles',secondary),('secondary-attributes',sa)]:
        (out/'outdoor-family'/(name+'.bin')).write_bytes(data)
    receipt=dict(status='EXISTING_AVERON_CANALAVE_ART_NOT_RUNTIME_ACCEPTANCE',engine_source=rev,
        existing_averon_sha256=assets,source_sha256=hashes,source_headers_unchanged=True,
        verified_physics_behavior_cells=verified,elevation15_preserved=heights,primary_records=512,
        secondary_records=len(secondary)//16,remaining_secondary_slots=512-len(secondary)//16,
        dependencies=dependencies,facades=FACADES,secondary_remap=SECONDARY,primary_remap=PRIMARY,wood_bridge_ids={n:sorted(v) for n,v in BRIDGES.items()},
        limits=['Only existing Averon General/Rustboro pixels/palettes; donor artwork not read or distributed',
          'Source building envelopes use neutral closed facades; no library/Gym/shop/services or dialogue added',
          'Canal/bridge collision, elevation and complete behaviors retained, not ROM animation or traversal acceptance',
          'Original Route218 water barrier retained: no Surf/ferry/grant/natural foot arrival or saved-origin acceptance',
          'Original blocked metadata-only city/route boundary remains blocked; travel uses paired west gateway',
          'Source art candidate only: no engine install, ROM/native/mGBA/Delta or production acceptance'])
    (out/'outdoor-art-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('engine','out'):p.add_argument('--'+n,required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.engine,args.out),indent=2))
