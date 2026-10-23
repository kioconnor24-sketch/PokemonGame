#!/usr/bin/env python3
"""Permitted Averon winter test proxy over pinned snow geography; no donor pixels.

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
spec=importlib.util.spec_from_file_location('snow_art_templates',HERE.parent/'celestic-north/adapt_outdoor_art.py')
templates=importlib.util.module_from_spec(spec);spec.loader.exec_module(templates)
pack=templates.pack
MAPS={'Route216': (96, 40), 'Route217': (36, 118), 'AcuityLakefront': (64, 66), 'SnowpointCity': (34, 68)}
HOUSE=(31,15,5,5);CENTER=(15,35,4,4)
FACADES={'Route216':[((14,19,4,4),HOUSE)],
 'Route217':[((6,51,4,4),HOUSE),((29,26,4,4),HOUSE)],'AcuityLakefront':[],
 'SnowpointCity':[((12,1,10,6),HOUSE),((2,17,4,4),HOUSE),((28,17,4,4),HOUSE),
                 ((14,29,7,5),HOUSE),((2,40,4,4),HOUSE),((27,41,5,4),CENTER)]}
USED_SECONDARY={'Route216': (513, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525, 528, 529, 530, 531, 536, 537, 538, 539, 540, 544, 545, 546, 547, 548, 600, 601, 602, 603, 608, 609, 610, 616, 617, 619, 620, 624, 627, 628, 648, 649, 651, 652, 653, 655, 656, 658), 'Route217': (513, 516, 517, 520, 521, 522, 523, 524, 525, 528, 529, 530, 531, 536, 537, 538, 608, 609, 610, 616, 617, 619, 620, 624, 627, 628, 659, 660, 661), 'AcuityLakefront': (513, 514, 517, 518, 519, 520, 521, 522, 523, 524, 525, 528, 529, 530, 531, 532, 536, 537, 538, 540, 544, 545, 546, 547, 548, 651, 652, 656, 657, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 674, 675, 676, 677, 678, 679), 'SnowpointCity': (513, 515, 518, 519, 520, 521, 522, 523, 528, 529, 533, 534, 535, 536, 537, 538, 540, 541, 542, 543, 546, 547, 548, 552, 553, 554, 555, 556, 557, 558, 560, 561, 562, 563, 564, 565, 566, 568, 569, 570, 572, 573, 575, 577, 578, 580, 581, 582, 583, 584, 586, 587, 588, 591, 592, 594, 596, 597, 598, 599, 600, 601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 612, 613, 615, 616, 617, 619, 620, 621, 622, 623, 624, 627, 628, 629, 630, 631, 632, 633, 634, 635, 636, 637, 638, 639, 640, 641, 642, 643, 644, 645, 646)}
# Existing pale General path is a neutral snow-ground proxy; conifers retain
# current green Averon art. No invented snow pixels/palette or donor art import.
REMAP={513:265,514:207,515:3,516:13,517:13,518:139,519:140,
 520:470,521:471,522:470,523:471,524:470,525:471,528:478,529:479,
 530:265,531:265,532:265,533:265,534:265,535:265,536:486,537:487,
 538:139,539:207,540:140,541:265,542:265,543:265,544:139,545:140,
 546:139,547:140,548:139,651:470,652:471,656:265,657:140,658:265,
 659:265,660:265,661:265,662:139,663:140,664:161,665:161,666:161,
 667:161,668:139,669:140,670:265,671:265,674:139,675:140,676:139,
 677:140,678:139,679:140,584:265,592:265,577:265,578:265,586:265,594:265}
SECONDARY={n:{mid:REMAP.get(mid,265) for mid in used} for n,used in USED_SECONDARY.items()}
PRIMARY={1:265,2:265}
templates.HERE=HERE;templates.MAPS=MAPS;templates.FACADES=FACADES
templates.SECONDARY=SECONDARY;templates.PRIMARY=PRIMARY;templates.BRIDGE=set()
BRIDGES={'Route216':{648,649,653,655,155},'Route217':set(),'AcuityLakefront':set(),'SnowpointCity':set()}


def source(name):
    result=templates.source(name)
    if result[2]['weather']!='WEATHER_SNOW':raise ValueError('source snow weather changed')
    return result


def desired_art(name,raw,border,header,attrs,banks,stock):
    if header['weather']!='WEATHER_SNOW':raise ValueError('source snow weather changed')
    desired=templates.desired_art(name,raw,border,header,attrs,banks,stock)
    plank=pack.words(banks[1],528-512)
    wood=tuple(plank[i] for i in (1,1,3,3,5,5,7,7))
    for i,(cell,) in enumerate(struct.iter_unpack('<H',raw+border)):
        mid=cell&1023
        if mid in BRIDGES[name]:desired[i]=wood

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
    receipt=dict(status='EXISTING_AVERON_SNOW_PROXY_ART_NOT_RUNTIME_ACCEPTANCE',engine_source=rev,
        existing_averon_sha256=assets,source_sha256=hashes,source_headers_unchanged=True,
        verified_physics_behavior_cells=verified,elevation15_preserved=heights,primary_records=512,
        secondary_records=len(secondary)//16,remaining_secondary_slots=512-len(secondary)//16,
        dependencies=dependencies,facades=FACADES,secondary_remap=SECONDARY,primary_remap=PRIMARY,wood_bridge_ids={n:sorted(v) for n,v in BRIDGES.items()},
        weather={n:'WEATHER_SNOW' for n in MAPS},snow_covered_art=False,
        limits=['Only existing Averon General/Rustboro pixels/palettes; no donor art/palettes/music',
          'Pale existing path is a snow-ground PROXY, with green conifers and neutral facades; NOT snow-covered art approval',
          'Exact source WEATHER_SNOW headers retained, but snowflake rendering/sprite budget/native footprints not runtime-tested',
          'Original24 elevation15 cells and full bridge/terrain behaviors retained; no bridge runtime acceptance',
          'LakeAcuity/source Coronet exits remain closed; no invented lake entry, Surf, story or progression',
          'No production install, ROM/native/mGBA/Delta/save-origin or natural-arrival acceptance'])
    (out/'outdoor-art-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('engine','out'):p.add_argument('--'+n,required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.engine,args.out),indent=2))
