#!/usr/bin/env python3
"""Permitted wooden Cycling Road and two neutral gateway art candidates.

Existing pack_art preserves source physics/full attributes. Source maps and
warp arrays remain immutable; nothing is installed into the production engine.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('cycling_art_pack',HERE.parent/'oreburgh-donor/build_city_family.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
MAPS={'Route206':(28,120),'Route206_North':(9,11),'Route206_South':(9,11),'Route211_West':(36,28)}
OUTDOORS=('Route206','Route211_West')
RIDGE_SECONDARY={515:123,516:121,517:125,521:289,523:112,524:114,
                 536:225,841:435,848:435,856:435,861:13}
RIDGE_PRIMARY=(1,3,105,107,108,109,113,114,115,116,117,121,123,124,125,
               136,137,138,147,155,163,167,169,267,268,368,376,400,402)
SECONDARY={607:124,615:125,672:13,673:306,674:427,675:428,676:428,677:307,
           680:434,681:435,682:436,683:435,684:1,685:434,686:435,687:436,
           688:435,689:435,692:1,696:307,697:427,698:428,699:428,700:440,
           701:441,702:435,703:435,704:1,706:436,707:105,708:434,
           709:435,710:435,711:435,712:440,713:441,714:443,715:112,716:436}
PRIMARY=(1, 2, 3, 5, 6, 13, 35, 42, 61, 62, 63, 69, 70, 71, 77, 78, 79, 85, 86, 87, 104, 105, 106, 107, 108, 109, 112, 113, 114, 115, 116, 117, 120, 121, 122, 123, 125, 137, 167, 171, 172, 180, 181, 182, 183, 199, 225, 227, 228, 281, 282, 288, 289, 290, 296, 297, 298, 302, 303, 306, 307, 309, 312, 313, 314, 320, 321, 322, 368, 393, 454, 455, 462, 463, 470, 471, 478, 479, 483, 484, 485, 486, 487, 488, 489, 498)
PRIMARY_ART={199:61,183:42,483:85,484:207,485:87}


def source_data(name):
    folder=HERE/'staged'/name;w,h=MAPS[name]
    raw=(folder/'map.bin').read_bytes();border=(folder/'border.bin').read_bytes()
    header=json.loads((folder/'map.json').read_text())
    attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
    if len(raw)!=w*h*2 or len(border)%2 or not border:raise ValueError('map/border dimensions changed')
    if header['region_map_section']!='MAPSEC_PENDING_OWNER' or any(header[k] for k in ('object_events','coord_events','bg_events')):
        raise ValueError('neutral source stage required')
    return raw,border,header,attrs


def desired_art(name,raw,border,header,records,source_attrs):
    w,h=MAPS[name]
    if len(raw)!=w*h*2 or not border or len(border)%2:raise ValueError('source dimensions changed')
    cells=list(struct.iter_unpack('<H',raw+border));desired=[]
    if name not in OUTDOORS and [(v['x'],v['y']) for v in header['warp_events']]!=[(4,1),(4,9)]:
        raise ValueError('paired north/south gate anchors changed')
    if name=='Route206':
        used={v[0]&1023 for v in cells}
        if used!=set(SECONDARY)|set(PRIMARY):raise ValueError('unreviewed Cycling Road secondary artwork')
    elif name=='Route211_West':
        if {v[0]&1023 for v in cells}!=set(RIDGE_SECONDARY)|set(RIDGE_PRIMARY):
            raise ValueError('unreviewed ridge artwork')
    anchors={(v['x'],v['y']) for v in header['warp_events']}
    for i,(cell,) in enumerate(cells):
        mid=cell&1023
        if str(mid) not in source_attrs:raise ValueError('missing source behavior/layer')
        if name=='Route206':target=PRIMARY_ART.get(mid,mid) if mid<512 else SECONDARY[mid]
        elif name=='Route211_West':
            target=175 if mid in (147,155,163) else 225 if mid==268 else mid if mid<512 else RIDGE_SECONDARY[mid]
        elif i>=w*h:target=1 # original neutral Building border
        elif (i%w,i//w) in anchors:target=534
        elif cell&0xC00:target=648 if i//w==0 else 656 if i%w in (0,w-1) or i//w==h-1 else 680
        else:target=616
        bank,index=divmod(target,512);words=pack.words(records[bank],index)
        if name=='Route211_West' and mid in (521,267):
            words=tuple((v&0xFFF)|0x3000 for v in pack.words(records[0],289))
        desired.append(words)
    return desired


def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    base=pack.accepted.base;dual=pack.accepted.dual
    root=Path(base.git(engine,'rev-parse','--show-toplevel').decode().strip());rev=base.git(engine,'rev-parse','HEAD').decode().strip();assets={}
    def read(path):
        raw=base.verified_file(root,engine.relative_to(root)/path,rev);assets[path]=base.sha(raw);return raw
    result={};families={};dependencies={};source_hashes={};verified=0;elevation15=0
    for family,names,folders in [('cycling',OUTDOORS,('primary/general','secondary/mauville')),
                                 ('gate',('Route206_North','Route206_South'),('primary/building','secondary/shop'))]:
        paths=['data/tilesets/'+f+'/' for f in folders]
        banks=[read(p+'metatiles.bin') for p in paths];attrs=[read(p+'metatile_attributes.bin') for p in paths]
        # Stock Mauville consumes510/512 slots, insufficient for the required
        # art/source-attribute variants. Reuse its real graphics
        # and palettes, but pack a NEW isolated metadata family containing only
        # the needed art/source-attribute pairs; never overwrite the stock bank.
        if family=='cycling':banks[1],attrs[1]=b'',b''
        original=banks[0],attrs[0];banks[0]+=bytes(8192-len(banks[0]));attrs[0]+=bytes(1024-len(attrs[0]))
        images=[dual.indexed(read(p+'tiles.png')) for p in paths]
        for name in names:
            raw,border,header,source=source_data(name);source_hashes[name]={p:base.sha((HERE/'staged'/name/p).read_bytes()) for p in ('map.bin','border.bin','map.json','attributes.json')}
            source_attrs=[bytearray(1024),bytearray(1024)]
            for mid,value in source.items():
                b,i=divmod(int(mid),512);struct.pack_into('<H',source_attrs[b],i*2,value)
            wanted=desired_art(name,raw,border,header,banks,source)
            adapted,banks[1],attrs[1]=pack.pack_art(raw+border,wanted,source_attrs,banks[0],attrs[0],banks[1],attrs[1])
            for (old,),(new,) in zip(struct.iter_unpack('<H',raw+border),struct.iter_unpack('<H',adapted)):
                b,i=divmod(new&1023,512)
                if old&0xFC00!=new&0xFC00 or pack.attribute(attrs[b],i)!=source[str(old&1023)]:raise ValueError('physics or behavior/layer changed')
                verified+=1
            if name=='Route206':elevation15=sum((v[0]>>12)==15 for v in struct.iter_unpack('<H',raw))
            if name=='Route211_West' and sum((v[0]>>12)==15 for v in struct.iter_unpack('<H',raw))!=19:
                raise ValueError('ridge elevation15 contract changed')
            result[name]=(adapted[:len(raw)],adapted[len(raw):])
        banks[0],attrs[0]=original
        families[family]=(banks,attrs,images,paths,names)
    if elevation15!=271:raise ValueError('source elevation15 bridge/underpass contract changed')
    out.mkdir(parents=True)
    for family,(banks,attrs,images,paths,names) in families.items():
        (out/(family+'-art')).mkdir()
        for label,blobs in [('metatiles',banks),('attributes',attrs)]:
            for bank,data in zip(('primary','secondary'),blobs):(out/(family+'-art')/(bank+'-'+label+'.bin')).write_bytes(data)
        for name in names:
            raw,border=result[name];w,h=MAPS[name];folder=out/name;folder.mkdir()
            dependencies[name]=dual.closure(raw+border,banks,images)
            palettes={i:base.palette(read(paths[i>=6]+'palettes/%02d.pal'%i)) for i in dependencies[name]['palettes']}
            (folder/'averon-map.bin').write_bytes(raw);(folder/'averon-border.bin').write_bytes(border)
            dual.render(raw,banks,images,palettes,w,h).save(folder/'averon.png')
    receipt=dict(status='EXISTING_AVERON_CYCLING_MATERIAL_ADAPTATION_NOT_RUNTIME_ACCEPTANCE',engine_source=rev,
        existing_averon_sha256=assets,source_sha256=source_hashes,source_secondary_to_existing=SECONDARY,
        explicit_primary_adaptations=PRIMARY_ART,
        ridge_secondary_to_existing=RIDGE_SECONDARY,route211_elevation15_preserved=19,
        verified_physics_behavior_cells=verified,route206_elevation15_preserved=elevation15,
        family_records={f:[len(b)//16 for b in v[0]] for f,v in families.items()},dependencies=dependencies,
        source_headers_warps_unchanged=True,
        limits=['Existing wooden deck replaces donor blue metal; canopy/cliff/sign colors differ',
                'Neutral Building/Shop interiors replace donor gateway decoration',
                'All source elevations, including271 elevation15 cells, and full source behavior/layer words survive',
                'Bridge lower/upper traversal and sprite priority still need actual runtime QA',
                'No donor pixels/palettes/music, global General modification, permanent IDs or production install'])
    (out/'cycling-art-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('engine','out'):p.add_argument('--'+n,required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.engine,args.out),indent=2))
