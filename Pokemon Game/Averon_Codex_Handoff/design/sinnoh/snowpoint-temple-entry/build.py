#!/usr/bin/env python3
"""Explicit native city doorstep/Temple entry over existing verified ice floors."""
import argparse,importlib.util,json,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('temple_gateway_reuse',HERE.parent/'frontier-gate-link/build.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
s=importlib.util.spec_from_file_location('temple_existing_height',HERE.parent/'snowpoint-temple-height/build_geometry.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t)
ROOT=HERE.parents[4];SOURCE=HERE.parent/'snowpoint-temple-height';CITY=HERE/'city-source'
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(g.base.git(engine,'rev-parse','--show-toplevel').decode().strip());pins={}
    def read(path):
        v=g.base.verified_file(repo,path.relative_to(repo),'HEAD');pins[str(path.relative_to(repo))]=g.base.sha(v);return v
    city_pins=json.loads(read(HERE/'city-source-pins.json'))
    for n,pin in city_pins['files'].items():
        if g.base.sha(read(CITY/n))!=pin['sha256']:raise ValueError('pinned readonly city input differs')
    audit=json.loads(read(SOURCE/'geometry-audit.json'))
    if not any(p['tile']==[8,13] and p['height_candidates']==['16'] for p in audit['floors']['1f']['walkable_center_samples']):raise ValueError('unsupported Temple source entry')
    city_header=json.loads(read(CITY/'map.json'))
    p=SOURCE/'staged/SinnohSnowpointTemple_1F';temple_header=json.loads(read(p/'map.json'))
    if city_header['warp_events'] or len(temple_header['warp_events'])!=1:raise ValueError('source doorway prefixes differ')
    city=read(CITY/'map.bin');city_border=read(CITY/'border.bin')
    primary,pa,sec,sa=[read(CITY/n) for n in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin')]
    v=struct.unpack_from('<H',city,2*(8*34+17))[0]
    if v&0xfc00!=0x3000:raise ValueError('city doorway not supported ordinary native ground')
    mid=v&1023;art=g.pack.words((primary,sec)[mid//512],mid%512)
    city,city_border,sec,sa,changes=g.add_portals(city,city_border,primary,pa,sec,sa,[(17,8,34,3)],art)
    temple=bytearray(read(p/'map.bin'));temple_border=read(p/'border.bin');old=struct.unpack_from('<H',temple,2*(13*32+8))[0]
    if not old&0xc00:raise ValueError('Temple exterior already open')
    struct.pack_into('<H',temple,2*(13*32+8),0x3000|517)
    # Keep existing stair0 unchanged; B1F still returns to the same source index.
    city_header['warp_events']=[dict(x=17,y=8,elevation=3,dest_map=temple_header['id'],dest_warp_id='1')]
    temple_header['warp_events'].append(dict(x=8,y=13,elevation=3,dest_map=city_header['id'],dest_warp_id='0'))
    native_prefixes=['data/tilesets/primary/general/','data/tilesets/secondary/cave/']
    native_banks=[read(engine/n/'metatiles.bin') for n in native_prefixes];native_attrs=[read(engine/n/'metatile_attributes.bin') for n in native_prefixes]
    if g.pack.attribute(native_attrs[1],517-512)&255!=0x61:raise ValueError('native Temple ladder semantics changed')
    paths={}
    first=t.stop_graph(temple,(8,13));back=t.stop_graph(temple,(14,3))
    if (14,3) not in first or (8,13) not in back:raise ValueError('Temple ice does not permit two-way entry return')
    paths['temple_entry_stoppable_count']=len(first);paths['temple_stair_stoppable_count']=len(back)
    city_attrs={str(v&1023):g.pack.attribute((pa,sa)[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',city+city_border)}
    # Existing city pale ground retains native MB_SAND; it is ordinary foot
    # terrain, unlike the frontier-only helper's narrower normal/ladder set.
    # Normalize only this read-only host model; emitted attributes stay intact.
    foot_attrs={mid:(word&~255 if word&255==0x21 else word) for mid,word in city_attrs.items()}
    ordinary=g.a.static_path(city,34,68,[17,9],[17,8],foot_attrs)
    if not ordinary:raise ValueError('city entrance approach inaccessible')
    paths['city_approach']=ordinary;paths['city_ground_behavior']='MB_SAND preserved, ordinary-foot host classification only'
    maps={'SnowpointCity':(city,city_border,city_header,(primary,sec),(pa,sa),(34,68),'rustboro'),
          'Temple1F':(bytes(temple),temple_border,temple_header,native_banks,native_attrs,(32,32),'cave')}
    previews={};attrs={}
    for name,(raw,border,h,banks,attributes,dims,secondary) in maps.items():
        prefixes=['data/tilesets/primary/general/','data/tilesets/secondary/'+secondary+'/']
        images=[g.dual.indexed(read(engine/p/'tiles.png')) for p in prefixes];deps=g.dual.closure(raw,banks,images)
        palettes={i:g.base.palette(read(engine/prefixes[i>=6]/('palettes/%02d.pal'%i))) for i in deps['palettes']}
        previews[name]=g.dual.render(raw,banks,images,palettes,*dims)
        attrs[name]={str(v&1023):g.pack.attribute(attributes[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',raw+border)}
    # All prior six-floor ice markers are immutable and counted from actual bytes.
    ice={}
    for name in audit['floors']:
        actual={'1f':'1F','b1f':'B1F','b2f':'B2F','b3f':'B3F','b4f':'B4F','b5f':'B5F'}[name]
        data=bytes(temple) if name=='1f' else read(SOURCE/'staged'/('SinnohSnowpointTemple_'+actual)/'map.bin')
        ice[actual]=sum((v&1023)==909 for (v,) in struct.iter_unpack('<H',data))
    if sum(ice.values())!=338:raise ValueError('original338 ice markers changed')
    out.mkdir(parents=True)
    for name,(raw,border,h,banks,attributes,dims,secondary) in maps.items():
        folder=out/'staged'/name;folder.mkdir(parents=True)
        (folder/'map.bin').write_bytes(raw);(folder/'border.bin').write_bytes(border);(folder/'map.json').write_text(json.dumps(h,indent=2)+'\n')
        (folder/'attributes.json').write_text(json.dumps(attrs[name],indent=2)+'\n');previews[name].save(folder/'preview.png')
        family=out/'families'/name;family.mkdir(parents=True)
        for n,v in zip(('primary-metatiles','primary-attributes','secondary-metatiles','secondary-attributes'),(banks[0],attributes[0],banks[1],attributes[1])):(family/(n+'.bin')).write_bytes(v)
    receipt=dict(status='EXPLICIT_CITY_TEMPLE_ENTRY_SOURCE_NOT_RUNTIME_ACCEPTANCE',source_sha256=pins,city_changes=changes,
        temple_change=dict(cell=[8,13],before=old,after=0x3000|517),paths=paths,ice_counts=ice,
        limits=['City17,8 is explicit native northern-hall doorstep adaptation, not blindly copied DS global coordinates',
                'Readonly235 city copies only; original snow bridge and six source-height floors untouched except derived1F door',
                'Host ice-stop model is not GBA/DS physics or canonical-puzzle acceptance',
                'No legendary/story/permanent IDs/production registry/save changes or runtime proof'])
    receipt['output_sha256']={str(p.relative_to(out)):g.base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();print(json.dumps(build(a.engine,a.out),indent=2))
