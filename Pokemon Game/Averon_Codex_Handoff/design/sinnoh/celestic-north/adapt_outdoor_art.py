#!/usr/bin/env python3
"""One isolated existing-Averon art family for the three staged Celestic outdoors.

Reuses pack_art; source cells, headers, full behavior/layer words and elevations
are immutable. Donor pixels/palettes are neither read nor emitted by this tool.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('celestic_outdoor_pack',HERE.parent/'oreburgh-donor/build_city_family.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
MAPS={'Route210_North':(99,29),'CelesticTown':(38,35),'Route211_East':(32,32)}
HOUSE=(31,15,5,5);CENTER=(15,35,4,4)
FACADES={
 'Route210_North':[((83,0,4,4),HOUSE)],
 'CelesticTown':[((4,4,4,4),HOUSE),((27,4,4,4),HOUSE),((8,23,4,4),HOUSE),
                  ((15,3,7,5),HOUSE),((25,20,5,8),CENTER)],
 'Route211_East':[]}
# Explicit complete secondary dependencies from the pinned Celestic bank.
SOIL={548,549,550,551,557,558,559}
BRIDGE={612,613,615,628}
SECONDARY={
 'Route210_North':{544:1,545:1,546:1,520:1,521:1,522:1,528:1,523:1,529:1,
  530:1,536:1,531:1,539:1,540:1,557:1,559:1,621:240,622:242,612:1,
  629:312,630:312,628:1,613:1,615:1,558:1,549:1,551:1,548:1,550:1,
  646:225,623:312,631:312,639:312},
 'Route211_East':{558:1,559:1,557:1,548:1,549:1,550:1,551:1},
 'CelesticTown':dict.fromkeys((552,553,554,555,556,544,545,546,560,561,562,563,564,
  520,521,522,528,523,529,530,568,569,547,570,571,572,536,531,539,540,576,577,
  580,584,585,586,587,588,589,592,593,594,595,596,597,600,601,602,603,604,
  605,608,609,610,616,617,618,625,512,513,514,532,533,524,525,526),1)}
# Neutral stone features reuse existing rocks instead of foreign landmark art.
for mid in (584,585,586,587,588,589,592,593,594,595,596,597,600,601,602,603,604,605,
            608,609,610,616,617,618,625):
    SECONDARY['CelesticTown'][mid]=225
PRIMARY={}


def source(name):
    folder=HERE/'staged'/name;w,h=MAPS[name]
    raw=(folder/'map.bin').read_bytes();border=(folder/'border.bin').read_bytes()
    header=json.loads((folder/'map.json').read_text())
    attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
    if len(raw)!=w*h*2 or len(border)!=8:raise ValueError('source dimensions changed')
    if header['region_map_section']!='MAPSEC_PENDING_OWNER' or any(header[k] for k in ('object_events','coord_events','bg_events')):
        raise ValueError('neutral off-engine stage required')
    if any(not 0<=int(mid)<1024 or type(value) is not int or not 0<=value<=65535 for mid,value in attrs.items()):
        raise ValueError('invalid full source attribute word')
    return raw,border,header,attrs


def desired_art(name,raw,border,header,attrs,banks,stock):
    w,h=MAPS[name]
    if len(raw)!=w*h*2 or len(border)!=8 or len(stock)!=2400:raise ValueError('art dimensions changed')
    desired=[]
    used={cell[0]&1023 for cell in struct.iter_unpack('<H',raw+border)}
    if set(map(int,attrs))!=used:raise ValueError('source used attribute coverage changed')
    if name in SECONDARY and {mid for mid in used if mid>=512}!=set(SECONDARY[name]):
        raise ValueError('unreviewed secondary dependency')
    for (cell,) in struct.iter_unpack('<H',raw+border):
        mid=cell&1023
        target=PRIMARY.get(mid,mid) if mid<512 else SECONDARY[name][mid]
        b,i=divmod(target,512);art=pack.words(banks[b],i)
        if mid in BRIDGE:
            wood=pack.words(banks[1],528-512)
            art=tuple(wood[i] for i in (1,1,3,3,5,5,7,7))
        desired.append(art)
    for (dx,dy,dw,dh),(sx,sy,sw,sh) in FACADES[name]:
        if min(dx,dy,sx,sy)<0 or min(dw,dh,sw,sh)<1 or dx+dw>w or dy+dh>h or sx+sw>40 or sy+sh>60:
            raise ValueError('facade outside source footprint')
        if (sx,sy,sw,sh)==CENTER:
            # Preserve the real 4x4 Center facade instead of duplicating its
            # curved roof row when fitting the donor's 5x5 envelope.
            for yy in range(dy,dy+dh):
                for xx in range(dx,dx+dw):
                    cell=struct.unpack_from('<H',raw,(yy*w+xx)*2)[0]
                    desired[yy*w+xx]=pack.words(banks[0],225 if cell&0xC00 else 1)
            dx+=(dw-sw)//2;dy+=dh-sh;dw=sw;dh=sh
        for y in range(dh):
            for x in range(dw):
                mid=stock[(sy+y*(sh-1)//max(1,dh-1))*40+sx+x*(sw-1)//max(1,dw-1)]&1023
                b,i=divmod(mid,512);desired[(dy+y)*w+dx+x]=pack.words(banks[b],i)
    # Retained gateways are visibly marked exactly at their source anchors;
    # unavailable building doors remain collision-closed in the original data.
    for warp in header['warp_events']:
        x,y=warp['x'],warp['y']
        if not (0<=x<w and 0<=y<h):raise ValueError('gateway outside source footprint')
        desired[y*w+x]=pack.words(banks[0],207)
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
        heights[name]=sum(cell[0]>>12==15 for cell in struct.iter_unpack('<H',raw))
        result[name]=(adapted[:len(raw)],adapted[len(raw):])
    if heights['Route210_North']!=48:raise ValueError('source bridge elevation15 changed')
    # Validate every final shared-bank dependency before creating any output.
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
    receipt=dict(status='EXISTING_AVERON_CELESTIC_OUTDOOR_ART_NOT_RUNTIME_ACCEPTANCE',engine_source=rev,
        existing_averon_sha256=assets,source_sha256=hashes,source_headers_and_cave_sources_unchanged=True,
        verified_physics_behavior_cells=verified,elevation15_preserved=heights,primary_records=512,
        secondary_records=len(secondary)//16,remaining_secondary_slots=512-len(secondary)//16,
        dependencies=dependencies,facades=FACADES,secondary_remap=SECONDARY,primary_remap=PRIMARY,
        limits=['Existing Rustboro facades resampled into source envelopes; no donor pixels/palettes/music',
               'Closed neutral house/Center facades and stone features replace foreign Celestic art; no services or landmark lore',
               'Existing wood/General rail art replaces foreign bridges/rails; every original full attribute and all48 bridge15 cells survive',
               'Native General terrain retained; neutral rock clusters replace foreign landmark art; no new lore',
               'Source art only: no ROM/native/mGBA/bridge sprite-priority/production/save acceptance or permanent origins'])
    (out/'outdoor-art-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('engine','out'):p.add_argument('--'+n,required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.engine,args.out),indent=2))
