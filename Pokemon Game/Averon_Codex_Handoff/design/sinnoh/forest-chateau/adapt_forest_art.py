#!/usr/bin/env python3
"""Existing-Averon woodland and neutral Chateau facade over pinned geography.

An explicit material adaptation, not matching ordinal/structural records as
proof of donor visual equivalence. No donor pixels or palette are consumed.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('forest_accepted_pack',HERE.parent/'oreburgh-donor/build_city_family.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
WIDTH,HEIGHT=82,84
# Reviewed source/current atlases: corresponding ordinary terrain silhouettes,
# different existing Averon colors/leaf texture/sign. Explicit whitelist prevents
# silently interpreting another source metatile as the same-numbered artwork.
PRIMARY=(1,2,3,13,104,105,106,107,108,109,112,114,115,116,117,120,121,122,
         123,124,125,137,224,280,281,282,288,289,290,296,297,298,306,307,
         312,313,314,320,321,322,328,329,330,454,455,462,463,470,471,478,
         479,486,487,488,489,494,495,508,509)
# Valor canopy variants become the corresponding existing General tree pieces.
# Dark shadow ground variants deliberately become ordinary grass; the tree/cliff
# geometry and full source behavior/layer word are still retained independently.
SECONDARY={658:470,659:471,662:478,663:479,666:486,667:487,
           730:489,731:488,732:2,733:2,734:486,735:487,736:478,
           737:479,738:1,739:471,740:470,741:137}
FACADE={724,744,745,746,752,753,754,755,760,761,762,763,
        768,769,770,771,772,773,776,777,778,779,780,781,786,788}


def candidate(raw,border,source_attrs,primary,pa,secondary,sa,stock,warps):
    if len(raw)!=WIDTH*HEIGHT*2 or len(border)!=8 or len(stock)!=40*60*2:
        raise ValueError('source forest/border/facade dimensions changed')
    if len(warps)!=1 or (warps[0]['x'],warps[0]['y'],warps[0]['dest_map'],str(warps[0]['dest_warp_id']))!=(59,7,'MAP_OLD_CHATEAU_ENTRANCE','0'):
        raise ValueError('paired Chateau entrance changed')
    used={v[0]&1023 for v in struct.iter_unpack('<H',raw+border)}
    if used!=set(PRIMARY)|set(SECONDARY)|FACADE:
        raise ValueError('unreviewed forest metatile dependency')
    banks=(primary,secondary);stock=struct.unpack('<2400H',stock)
    desired=[]
    for i,(cell,) in enumerate(struct.iter_unpack('<H',raw+border)):
        mid=cell&1023
        if mid in FACADE:
            x,y=i%WIDTH,i//WIDTH
            if i>=WIDTH*HEIGHT or not (54<=x<=64 and 2<=y<=7):
                raise ValueError('Chateau facade escaped reviewed envelope')
            # End-point resampling retains the actual bottom doorway, unlike
            # floor(y*source_height/height), which skips the last source row.
            sx=6+(x-54)*11//10;sy=7+(y-2)*8//5
            target=stock[sy*40+sx]&1023
            if mid==724:target=stock[15*40+11]&1023
        else:target=mid if mid in PRIMARY else SECONDARY[mid]
        bank,index=divmod(target,512)
        desired.append(pack.words(banks[bank],index))
    adapted,secondary,sa=pack.pack_art(raw+border,desired,source_attrs,primary,pa,secondary,sa)
    count=WIDTH*HEIGHT*2
    return adapted[:count],adapted[count:],secondary,sa


def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:
        raise ValueError('new off-engine output required')
    base=pack.accepted.base;dual=pack.accepted.dual
    root=Path(base.git(engine,'rev-parse','--show-toplevel').decode().strip())
    rev=base.git(engine,'rev-parse','HEAD').decode().strip();assets={}
    def read(path):
        raw=base.verified_file(root,engine.relative_to(root)/path,rev);assets[path]=base.sha(raw);return raw
    folders=['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/']
    banks=[read(f+'metatiles.bin') for f in folders];attrs=[read(f+'metatile_attributes.bin') for f in folders]
    images=[dual.indexed(read(f+'tiles.png')) for f in folders]
    folder=HERE/'staged/EternaForest';raw=(folder/'map.bin').read_bytes();border=(folder/'border.bin').read_bytes()
    header=json.loads((folder/'map.json').read_text());source=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
    if header['region_map_section']!='MAPSEC_PENDING_OWNER' or any(header[k] for k in ('object_events','coord_events','bg_events')):
        raise ValueError('neutral source stage required')
    source_attrs=[bytearray(1024),bytearray(1024)]
    for mid,value in source.items():
        bank,index=divmod(int(mid),512);struct.pack_into('<H',source_attrs[bank],index*2,value)
    adapted,adapted_border,secondary,sa=candidate(raw,border,source_attrs,*[banks[0],attrs[0],banks[1],attrs[1]],
        read('data/layouts/RustboroCity/map.bin'),header['warp_events'])
    result_banks=[banks[0],secondary];result_attrs=[attrs[0],sa]
    for (before,),(after,) in zip(struct.iter_unpack('<H',raw+border),struct.iter_unpack('<H',adapted+adapted_border)):
        if before&0xFC00!=after&0xFC00:raise ValueError('source collision/elevation changed')
        sb,si=divmod(before&1023,512);db,di=divmod(after&1023,512)
        if str(before&1023) not in source or pack.attribute(result_attrs[db],di)!=source[str(before&1023)]:
            raise ValueError('source behavior/layer changed')
    deps=dual.closure(adapted+adapted_border,result_banks,images)
    palettes={i:base.palette(read(folders[i>=6]+'palettes/%02d.pal'%i)) for i in deps['palettes']}
    out.mkdir(parents=True)
    for name,data in [('averon-map.bin',adapted),('averon-border.bin',adapted_border),
                      ('primary-metatiles.bin',banks[0]),('primary-attributes.bin',attrs[0]),
                      ('secondary-metatiles.bin',secondary),('secondary-attributes.bin',sa)]:
        (out/name).write_bytes(data)
    dual.render(adapted,result_banks,images,palettes,WIDTH,HEIGHT).save(out/'averon.png')
    receipt=dict(status='EXISTING_AVERON_MATERIAL_ADAPTATION_NOT_DONOR_VISUAL_OR_RUNTIME_ACCEPTANCE',
        engine_source=rev,existing_averon_sha256=assets,
        source_sha256={p:base.sha((folder/p).read_bytes()) for p in ('map.bin','border.bin','map.json','attributes.json')},
        source_primary_to_existing={str(i):i for i in PRIMARY},source_secondary_to_existing=SECONDARY,
        facade=dict(envelope=[54,2,11,6],existing_source='RustboroCity Devon facade [6,7,12,9]',
                    doorway=[59,7],resampling='endpoint preserving; exact stock door at11,15'),
        verified_physics_behavior_cells=WIDTH*HEIGHT+4,primary_records=len(banks[0])//16,
        secondary_records=len(secondary)//16,remaining_secondary_slots=512-len(secondary)//16,
        dependencies=deps,source_warps_headers_unchanged=True,
        limits=['Different current Averon leaves/colors/sign and neutral resampled facade; not donor visual equivalence',
                'Valor shadow variants deliberately use ordinary grass/tree silhouettes',
                'No donor pixels/palettes, shared General edits, permanent IDs or production registration',
                'No native/build/mGBA/animation/follower/warp/save acceptance for Forest'])
    (out/'forest-art-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('engine','out'):parser.add_argument('--'+name,required=True,type=Path)
    args=parser.parse_args();print(json.dumps(build(args.engine,args.out),indent=2))
