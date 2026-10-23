#!/usr/bin/env python3
"""One isolated existing-Averon art family for the three staged northern Coronet caves.

Reuses pack_art; source cells, headers, full behavior/layer words and elevations
are immutable. Donor pixels/palettes are neither read nor emitted by this tool.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('coronet_cave_pack',HERE.parent/'oreburgh-donor/build_city_family.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
MAPS={'MtCoronet_1F_North_Room1':(36,51),'MtCoronet_1F_North_Room2':(19,16),'MtCoronet_B1F':(32,65)}
# Explicit source-used roles, not pixel equivalence inferred from numeric IDs.
USED={513,514,515,519,575,588,589,593,676,741,742,743,744,745,746,747,748,749,750,
752,753,754,760,761,762,766,767,770,771,774,775,779,782,786,787,790,922,
932,933,934,935,936,937,938,939,940,941,942,944,945,946,947,948,949}
REPLACEMENTS={922:513,932:741,933:575,**dict.fromkeys(range(934,943),161),
              **dict.fromkeys(range(944,950),207)}
PRIMARY={171:175,172:207}


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


def desired_art(name,raw,border,header,attrs,banks,stock=None):
    w,h=MAPS[name]
    if len(raw)!=w*h*2 or len(border)!=8:raise ValueError('source dimensions changed')
    used={c[0]&1023 for c in struct.iter_unpack('<H',raw+border)}
    if set(map(int,attrs))!=used or not {i for i in used if i>=512}<=USED:
        raise ValueError('unreviewed cave dependency')
    result=[]
    for (cell,) in struct.iter_unpack('<H',raw+border):
        mid=cell&1023
        target=PRIMARY.get(mid,mid) if mid<512 else REPLACEMENTS.get(mid,mid)
        bank,index=divmod(target,512)
        result.append(pack.words(banks[bank],index))
    return result


def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    base=pack.accepted.base;dual=pack.accepted.dual
    root=Path(base.git(engine,'rev-parse','--show-toplevel').decode().strip());rev=base.git(engine,'rev-parse','HEAD').decode().strip();assets={}
    def read(path):
        data=base.verified_file(root,engine.relative_to(root)/path,rev);assets[path]=base.sha(data);return data
    paths=['data/tilesets/primary/general/','data/tilesets/secondary/cave/']
    stock_banks=[read(p+'metatiles.bin') for p in paths];pa=read(paths[0]+'metatile_attributes.bin')
    if len(stock_banks[0])!=8192 or len(pa)!=1024:raise ValueError('primary capacity contract changed')
    stock=None
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
    if any(heights.values()):raise ValueError('unexpected cave bridge dependency')
    # Validate every final shared-bank dependency before creating any output.
    banks=[stock_banks[0],secondary];dependencies={};previews={}
    for name,(raw,border) in result.items():
        dependencies[name]=dual.closure(raw+border,banks,images)
        palettes={i:base.palette(read(paths[i>=6]+'palettes/%02d.pal'%i)) for i in dependencies[name]['palettes']}
        previews[name]=dual.render(raw,banks,images,palettes,*MAPS[name])
    out.mkdir(parents=True);(out/'cave-family').mkdir()
    for name,(raw,border) in result.items():
        folder=out/name;folder.mkdir();(folder/'averon-map.bin').write_bytes(raw);(folder/'averon-border.bin').write_bytes(border);previews[name].save(folder/'averon.png')
    for name,data in [('primary-metatiles',banks[0]),('primary-attributes',pa),('secondary-metatiles',secondary),('secondary-attributes',sa)]:
        (out/'cave-family'/(name+'.bin')).write_bytes(data)
    receipt=dict(status='EXISTING_AVERON_CORONET_CAVE_ART_NOT_RUNTIME_ACCEPTANCE',engine_source=rev,
        existing_averon_sha256=assets,source_sha256=hashes,source_headers_and_outdoor_art_unchanged=True,
        verified_physics_behavior_cells=verified,elevation15_preserved=heights,primary_records=512,
        secondary_records=len(secondary)//16,remaining_secondary_slots=512-len(secondary)//16,
        dependencies=dependencies,explicit_role_remap=REPLACEMENTS,primary_remap=PRIMARY,
        limits=['Only existing Averon General/Cave pixels and palettes; no donor pixels distributed',
                'Floor922 uses stock cave513; ladder933 stock575; blocked cap932 stock741',
                'Pond934-942 uses existing General161 water with source full attrs and original shoreline geometry',
                'Walkable transition strips944-949 use stock207 stairs, not a new Rock Climb mechanic',
                'Other source-used cave roles use current Cave art, never donor graphics',
                'No native/build/animation/gameplay/save/production acceptance inferred from static art'])

    (out/'cave-art-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('engine','out'):p.add_argument('--'+n,required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.engine,args.out),indent=2))
