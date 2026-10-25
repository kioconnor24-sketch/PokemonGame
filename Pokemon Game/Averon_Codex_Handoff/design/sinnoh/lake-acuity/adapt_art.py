#!/usr/bin/env python3
"""Reuse pinned Lake Acuity geometry with isolated, permitted native proxy art."""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('acuity_existing_templates',HERE.parent/'celestic-north/adapt_outdoor_art.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t)
pack=t.pack;base=pack.accepted.base;dual=pack.accepted.dual
SOURCE=HERE.parent/'remaining-donor/staged/LakeAcuity'
SECONDARY={513:265,517:13,520:470,521:471,522:470,523:471,524:470,525:471,
 528:478,529:479,530:265,531:265,532:265,536:486,537:487,538:139,539:207,
 540:140,546:139,547:140,548:139,549:265,550:265,551:265,662:139,663:140,
 664:161,665:161,666:161,667:161,670:265,671:265,672:265,673:265,674:139,
 675:140,678:139,679:140,647:265}
# Private module instance only; shared Celestic source is untouched.
t.MAPS={'LakeAcuity':(48,52)};t.FACADES={'LakeAcuity':[]};t.PRIMARY={1:265,2:265};t.SECONDARY={'LakeAcuity':SECONDARY};t.BRIDGE=set()


def source(repo):
    repo=Path(repo).resolve();folder=SOURCE.relative_to(repo)
    data={p:base.verified_file(repo,folder/p,'HEAD') for p in ('map.bin','border.bin','map.json','attributes.json')}
    receipt=json.loads(base.verified_file(repo,HERE.parent.relative_to(repo)/'remaining-donor/source-receipt.json','HEAD'))
    pin=receipt['maps']['LakeAcuity']
    if base.sha(data['map.bin'])!=pin['staged_sha256'] or base.sha(data['border.bin'])!=pin['border_sha256']:
        raise ValueError('pinned Lake Acuity source identity differs')
    if len(data['map.bin'])!=48*52*2 or len(data['border.bin'])!=8:raise ValueError('source dimensions differ')
    header=json.loads(data['map.json']);attrs=json.loads(data['attributes.json'])['used_source_attribute_words']
    if header['region_map_section']!='MAPSEC_PENDING_OWNER' or any(header[k] for k in ('object_events','coord_events','bg_events','warp_events','connections')):
        raise ValueError('neutral disconnected source required')
    used={v[0]&1023 for v in struct.iter_unpack('<H',data['map.bin']+data['border.bin'])}
    if {int(k) for k in attrs}!=used or used&set(range(512,1024))!=set(SECONDARY):
        raise ValueError('used source attribute or secondary coverage differs')
    if any(type(v) is not int or not 0<=v<=65535 for v in attrs.values()):raise ValueError('invalid source attribute word')
    return data,header,attrs,pin


def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(base.git(engine,'rev-parse','--show-toplevel').decode().strip());data,header,attrs,pin=source(repo);assets={}
    def read(path):
        raw=base.verified_file(repo,engine.relative_to(repo)/path,'HEAD');assets[path]=base.sha(raw);return raw
    paths=['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/']
    banks=[read(p+'metatiles.bin') for p in paths];pa=read(paths[0]+'metatile_attributes.bin')
    if len(banks[0])!=8192 or len(pa)!=1024:raise ValueError('primary capacity differs')
    images=[dual.indexed(read(p+'tiles.png')) for p in paths]
    stock=struct.unpack('<2400H',read('data/layouts/RustboroCity/map.bin'))
    desired=t.desired_art('LakeAcuity',data['map.bin'],data['border.bin'],header,attrs,banks,stock)
    source_attrs=[bytearray(1024),bytearray(1024)]
    for mid,value in attrs.items():bank,i=divmod(int(mid),512);struct.pack_into('<H',source_attrs[bank],i*2,value)
    adapted,secondary,sa=pack.pack_art(data['map.bin']+data['border.bin'],desired,source_attrs,banks[0],pa,b'',b'')
    for (old,),(new,) in zip(struct.iter_unpack('<H',data['map.bin']+data['border.bin']),struct.iter_unpack('<H',adapted)):
        bank,i=divmod(new&1023,512)
        if old&0xfc00!=new&0xfc00 or pack.attribute((pa,sa)[bank],i)!=attrs[str(old&1023)]:raise ValueError('source physics/behavior/layer changed')
    final_banks=[banks[0],secondary];deps=dual.closure(adapted,final_banks,images)
    pals={i:base.palette(read(paths[i>=6]+'palettes/%02d.pal'%i)) for i in deps['palettes']}
    preview=dual.render(adapted[:4992],final_banks,images,pals,48,52)
    out.mkdir(parents=True);folder=out/'LakeAcuity';folder.mkdir();family=out/'outdoor-family';family.mkdir()
    (folder/'averon-map.bin').write_bytes(adapted[:4992]);(folder/'averon-border.bin').write_bytes(adapted[4992:]);preview.save(folder/'averon.png')
    for key,raw in [('primary-metatiles',banks[0]),('primary-attributes',pa),('secondary-metatiles',secondary),('secondary-attributes',sa)]:
        (family/(key+'.bin')).write_bytes(raw)
    receipt=dict(status='PERMITTED_NATIVE_PROXY_ART_ONLY_NO_RUNTIME_OR_PRODUCTION_ACCEPTANCE',source_revision='38228bb574a3557345852b758d5f1a65eb01bb22',source=pin,
        source_sha256={p:base.sha(v) for p,v in data.items()},native_asset_sha256=assets,dimensions=[48,52],verified_physics_behavior_cells=2500,
        primary_records=512,secondary_records=len(secondary)//16,remaining_secondary_slots=512-len(secondary)//16,
        output_sha256={str(p.relative_to(out)):base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()},dependencies=deps,secondary_remap=SECONDARY,
        limits=['Existing native General/Rustboro pixels only; pale path is winter-ground proxy, not final snow art',
                'Every source collision/elevation/full attribute/layer preserved, including water and sand',
                'Original source lacks warps/connections; no invented Lakefront seam, cave entrance or legendary content',
                'No production install, saved identity, new artwork, ROM/native/mGBA/Save acceptance'])
    (out/'art-receipt.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode());return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();print(json.dumps(build(a.engine,a.out),indent=2))
