#!/usr/bin/env python3
"""Neutral existing-Averon Eterna City art sharing the proven road-bank prefix."""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('eterna_city_cycle_art',HERE/'adapt_cycling_art.py')
cycle=importlib.util.module_from_spec(spec);spec.loader.exec_module(cycle)
pack=cycle.pack
WIDTH,HEIGHT=60,55
# Source-envelope -> existing Rustboro facade, all metatile nearest-neighbour
# with inclusive endpoints. These are cosmetics, not service/script activation.
FACADES=[((14,0,5,7),(10,24,6,7)),((26,6,4,3),(31,15,5,5)),
         ((48,3,4,7),(10,24,6,7)),((14,14,5,4),(15,35,4,4)),
         ((20,14,4,4),(31,15,5,5)),((38,19,4,4),(31,15,5,5)),
         ((18,22,4,4),(31,15,5,5)),((8,20,4,14),(10,24,6,7)),
         ((18,30,4,4),(14,42,5,4)),((23,27,5,7),(10,24,6,7)),
         ((8,36,4,9),(10,24,6,7)),((19,40,7,5),(24,15,7,5))]
ROAD={720,721,722,728,729,736,737,738,760,769,778,779,780,781,784,785}
SOIL={621,623,629,630,631}
FENCE={519:306,525:306,527:306,531:312,532:313,533:314,534:307,535:1,
       558:312,559:314,566:307,567:307,603:312,604:314,742:307,743:313,
       767:307,774:312,775:314,782:312,783:314,788:312,790:312,
       791:313,792:314,799:312,812:312,813:313,814:314}
CLIFF={515:123,516:121,517:125,523:112,524:114}


def candidate(raw,border,source,primary,pa,prior,prior_attrs,stock_banks,stock_map,warp):
    if len(raw)!=WIDTH*HEIGHT*2 or len(border)!=8 or len(stock_map)!=40*60*2:
        raise ValueError('City/facade dimensions changed')
    if len(warp)!=1 or (warp[0]['x'],warp[0]['y'],warp[0]['dest_map'],str(warp[0]['dest_warp_id']))!=(15,48,'MAP_ROUTE206_NORTH','0'):
        raise ValueError('City cycling gateway identity changed')
    source_attrs=[bytearray(1024),bytearray(1024)];desired=[]
    for mid,value in source.items():
        b,i=divmod(int(mid),512);struct.pack_into('<H',source_attrs[b],i*2,value)
    for (cell,) in struct.iter_unpack('<H',raw+border):
        mid=cell&1023
        if str(mid) not in source:raise ValueError('unknown City behavior/layer dependency')
        if mid<512:target=1 if mid in (267,268,269,418) else 175 if mid in (147,148,155,156,163,164) else mid
        elif mid in CLIFF:target=CLIFF[mid]
        elif mid in FENCE:target=FENCE[mid]
        elif mid in ROAD:target=699 # actual existing Rustboro street material
        elif mid in (750,751,758,759):target=14 if mid in (750,758) else 22
        elif mid in (819,820):target=225 # neutral existing boulder, no copied statue
        elif mid in (796,797,798,801,802,803,804):target=312 # neutral physical rail, no bike feature
        elif mid in (719,886):target=207 # conspicuous closed-door steps
        else:target=1
        b,i=divmod(target,512);words=pack.words(stock_banks[b],i)
        if mid in SOIL:words=pack.words(primary,1)
        desired.append(words)
    stock=struct.unpack('<2400H',stock_map)
    for (dx,dy,dw,dh),(sx,sy,sw,sh) in FACADES:
        if min(dx,dy,sx,sy)<0 or dx+dw>WIDTH or dy+dh>HEIGHT or sx+sw>40 or sy+sh>60:
            raise ValueError('facade envelope outside map')
        for y in range(dh):
            for x in range(dw):
                bx=sx+x*(sw-1)//max(1,dw-1);by=sy+y*(sh-1)//max(1,dh-1)
                mid=stock[by*40+bx]&1023;b,i=divmod(mid,512)
                desired[(dy+y)*WIDTH+dx+x]=pack.words(stock_banks[b],i)
    desired[48*WIDTH+15]=pack.words(primary,207)
    adapted,s,sa=pack.pack_art(raw+border,desired,source_attrs,primary,pa,prior,prior_attrs)
    if not s.startswith(prior) or not sa.startswith(prior_attrs):raise ValueError('road metadata prefix changed')
    for (old,),(new,) in zip(struct.iter_unpack('<H',raw+border),struct.iter_unpack('<H',adapted)):
        b,i=divmod(new&1023,512)
        if old&0xFC00!=new&0xFC00 or pack.attribute((pa,sa)[b],i)!=source[str(old&1023)]:
            raise ValueError('City physics/behavior/layer changed')
    return adapted[:len(raw)],adapted[len(raw):],s,sa


def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    base=pack.accepted.base;dual=pack.accepted.dual
    root=Path(base.git(engine,'rev-parse','--show-toplevel').decode().strip());rev=base.git(engine,'rev-parse','HEAD').decode().strip();assets={}
    def read(path):
        raw=base.verified_file(root,engine.relative_to(root)/path,rev);assets[path]=base.sha(raw);return raw
    paths=['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/']
    stock_banks=[read(p+'metatiles.bin') for p in paths];pa=read(paths[0]+'metatile_attributes.bin')
    prior=(HERE/'cycling-art/secondary-metatiles.bin').read_bytes();prior_attrs=(HERE/'cycling-art/secondary-attributes.bin').read_bytes()
    if stock_banks[0]!=(HERE/'cycling-art/primary-metatiles.bin').read_bytes() or pa!=(HERE/'cycling-art/primary-attributes.bin').read_bytes():
        raise ValueError('shared primary bank differs from road family')
    folder=HERE/'staged/EternaCity';raw=(folder/'map.bin').read_bytes();border=(folder/'border.bin').read_bytes();header=json.loads((folder/'map.json').read_text())
    source=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
    if header['region_map_section']!='MAPSEC_PENDING_OWNER' or any(header[k] for k in ('object_events','coord_events','bg_events')):
        raise ValueError('neutral staged City required')
    adapted,border2,s,sa=candidate(raw,border,source,stock_banks[0],pa,prior,prior_attrs,stock_banks,read('data/layouts/RustboroCity/map.bin'),header['warp_events'])
    banks=[stock_banks[0],s];images=[dual.indexed(read(p+'tiles.png')) for p in paths]
    dependencies={};previews={}
    for name,data,w,h in [('EternaCity',adapted,60,55),('Route206',(HERE/'staged/Route206/averon-map.bin').read_bytes(),28,120),
                          ('Route211_West',(HERE/'staged/Route211_West/averon-map.bin').read_bytes(),36,28)]:
        b=border2 if name=='EternaCity' else (HERE/'staged'/name/'averon-border.bin').read_bytes()
        dependencies[name]=dual.closure(data+b,banks,images)
        palettes={i:base.palette(read(paths[i>=6]+'palettes/%02d.pal'%i)) for i in dependencies[name]['palettes']}
        image=dual.render(data,banks,images,palettes,w,h);previews[name]=image
        if name!='EternaCity':
            with dual.Image.open(HERE/'staged'/name/'averon.png') as old:
                if image.tobytes()!=old.convert('RGB').tobytes():raise ValueError('streamed neighbour appearance changed: '+name)
    out.mkdir(parents=True)
    for name,data in [('averon-map.bin',adapted),('averon-border.bin',border2),
                      ('primary-metatiles.bin',banks[0]),('primary-attributes.bin',pa),
                      ('secondary-metatiles.bin',s),('secondary-attributes.bin',sa)]:
        (out/name).write_bytes(data)
    previews['EternaCity'].save(out/'averon.png')
    receipt=dict(status='SHARED_EXISTING_AVERON_ETERNA_CITY_ART_NOT_RUNTIME_ACCEPTANCE',engine_source=rev,
        existing_averon_sha256=assets,source_sha256={p:base.sha((folder/p).read_bytes()) for p in ('map.bin','border.bin','map.json','attributes.json')},
        prior_secondary_sha256=base.sha(prior),prior_secondary_attributes_sha256=base.sha(prior_attrs),prior_secondary_records=len(prior)//16,
        primary_records=len(banks[0])//16,secondary_records=len(s)//16,remaining_secondary_slots=512-len(s)//16,
        verified_physics_behavior_cells=WIDTH*HEIGHT+4,neighbour_rgb_unchanged=['Route206','Route211_West'],
        dependencies=dependencies,facades=FACADES,
        limits=['Existing facades resampled within source envelopes; neutral rock replaces donor statue; rail replaces bike props',
                'Brown soil becomes grass and streets use existing Rustboro paving; original collision/height/layer/warps survive',
                'No services/story/scripts/encounters, donor pixels/colors, production registrars or permanent origins',
                'Static neighbour RGB equality does not prove runtime streaming, bridge priority or genuine gameplay acceptance'])
    (out/'city-art-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('engine','out'):p.add_argument('--'+n,required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.engine,args.out),indent=2))
