#!/usr/bin/env python3
"""Normal Spear Pillar supported footprint, existing native art, no plot."""
import argparse,importlib.util,json,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('summit_existing_projection',HERE.parent/'frontier-campus/build_source.py')
existing=importlib.util.module_from_spec(s);s.loader.exec_module(existing)
existing.HERE=HERE;existing.DIMS={'Summit':(64,64)}
# Narrow private-instance extension: actual source south-door0x6F. Other callers'
# defaults and original map data remain unchanged; all source doors stay sealed.
existing.SOURCE_BEHAVIORS=existing.SOURCE_BEHAVIORS+(0x6f,)
original_construct=existing.construct
def construct(geometry):
    maps=original_construct(geometry)
    for name,(raw,h,audit) in maps.items():
        h.update(id='MAP_SINNOH_SPEAR_PILLAR',name='SinnohSpearPillar',layout='LAYOUT_SINNOH_SPEAR_PILLAR',map_type='MAP_TYPE_ROUTE',allow_cycling=False,music='MUS_PETALBURG_WOODS')
    return maps
existing.construct=construct
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(existing.base.git(engine,'rev-parse','--show-toplevel').decode().strip());pins={}
    def read(path):
        data=existing.base.verified_file(repo,path.relative_to(repo),'HEAD');pins[str(path.relative_to(repo))]=existing.base.sha(data);return data
    upper=HERE.parent/'coronet-upper-floors';source=upper/'staged/SinnohMtCoronet_6F'
    six=bytearray(read(source/'map.bin'));border=read(source/'border.bin');six_h=json.loads(read(source/'map.json'))
    if len(six_h['warp_events'])!=1:raise ValueError('existing6F source prefix differs')
    normal=json.loads(read(upper/'portal-reference.json'))['files']['6f']['warp_events'][1]
    if normal!=dict(x=7,z=5,dest_header_id='MAP_HEADER_SPEAR_PILLAR',dest_warp_id=0):raise ValueError('normal6F source route differs')
    geometry=json.loads(read(HERE/'geometry.json'))
    if not any(p['tile']==[31,53] and p['permission']==0x6f and p['height']=='16' and p['flat'] for p in geometry['Summit']['surfaces']):raise ValueError('unsupported source summit exit')
    source_pins=json.loads(read(HERE/'source-pins.json'))
    if source_pins['technical_exit']['warps']!=[dict(x=31,z=53,dest_header_id='MAP_HEADER_MT_CORONET_6F',dest_warp_id=1)]:raise ValueError('normal summit source return differs')
    core=existing.build(engine,out)
    summit=bytearray((out/'staged/Summit/map.bin').read_bytes());summit_h=json.loads((out/'staged/Summit/map.json').read_text())
    family=out/'native-family';primary=(family/'primary-metatiles.bin').read_bytes();pa=(family/'primary-attributes.bin').read_bytes();sec=(family/'secondary-metatiles.bin').read_bytes();sa=(family/'secondary-attributes.bin').read_bytes()
    spec=importlib.util.spec_from_file_location('summit_existing_portal',HERE.parent/'frontier-gate-link/build.py')
    gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
    stock=read(engine/'data/tilesets/secondary/cave/metatiles.bin');art=existing.packer.words(stock,517-512)
    summit,sb,sec,sa,changes=gate.add_portals(summit,(out/'staged/Summit/border.bin').read_bytes(),primary,pa,sec,sa,[(31,53,64,3)],art)
    old=struct.unpack_from('<H',six,2*(5*14+7))[0]
    if not old&0xc00:raise ValueError('6F normal summit door already open')
    struct.pack_into('<H',six,2*(5*14+7),0x3000|517)
    summit_h['warp_events']=[dict(x=31,y=53,elevation=3,dest_map=six_h['id'],dest_warp_id='1')]
    six_h['warp_events'].append(dict(x=7,y=5,elevation=3,dest_map=summit_h['id'],dest_warp_id='0'))
    cp=read(engine/'data/tilesets/primary/general/metatiles.bin');cpa=read(engine/'data/tilesets/primary/general/metatile_attributes.bin');csa=read(engine/'data/tilesets/secondary/cave/metatile_attributes.bin')
    packets={'Summit':(summit,sb,summit_h,(primary,pa,sec,sa),(64,64)),
             'Coronet6F':(bytes(six),border,six_h,(cp,cpa,stock,csa),(14,28))}
    paths={}
    for name,(raw,border,h,fam,dims) in packets.items():
        p=out/'staged'/name;p.mkdir(parents=True,exist_ok=True)
        attrs={str(v&1023):existing.packer.attribute((fam[1],fam[3])[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',raw+border)}
        foot={mid:(v&~255 if v&255==8 else v) for mid,v in attrs.items()}
        start,end=([31,53],[31,13]) if name=='Summit' else ([7,5],[10,24])
        path=gate.a.static_path(raw,*dims,start,end,foot)
        if not path:raise ValueError('source summit/6F ordinary approach disconnected')
        paths[name]=path
        prefixes=['data/tilesets/primary/general/','data/tilesets/secondary/cave/']
        images=[existing.dual.indexed(read(engine/q/'tiles.png')) for q in prefixes]
        deps=existing.dual.closure(raw,[fam[0],fam[2]],images)
        palettes={i:existing.base.palette(read(engine/prefixes[i>=6]/('palettes/%02d.pal'%i))) for i in deps['palettes']}
        preview=existing.dual.render(raw,[fam[0],fam[2]],images,palettes,*dims)
        (p/'map.bin').write_bytes(raw);(p/'border.bin').write_bytes(border);(p/'map.json').write_text(json.dumps(h,indent=2)+'\n')
        (p/'attributes.json').write_text(json.dumps(attrs,indent=2)+'\n');preview.save(p/'preview.png')
        (p/'preview.png').stat()
        f=out/'families'/name;f.mkdir(parents=True)
        for n,v in zip(('primary-metatiles','primary-attributes','secondary-metatiles','secondary-attributes'),fam):(f/(n+'.bin')).write_bytes(v)
    # Remove only own freshly generated intermediate/duplicate native output.
    import shutil
    shutil.rmtree(out/'native-family')
    (out/'staged/Summit/preview.png').stat()
    receipt=dict(status='NORMAL_SUMMIT_SOURCE_GEOMETRY_NOT_STORY_OR_RUNTIME_ACCEPTANCE',baseline_projection=core['maps'],current_open_cells={n:sum(not v&0xc00 for (v,) in struct.iter_unpack('<H',d[0])) for n,d in packets.items()},source_sha256=pins,
        summit_changes=changes,sixf_change=dict(cell=[7,5],before=old,after=0x3000|517),local_paths=paths,
        native_assets=core['native_assets'],limits=['Actual normal matrix022 footprint, no DS models/props/art/story emitted',
        '484 supported source cells, ordinary native ordinal projection not DS movement parity',
        'Normal physical return only; original6F conditional variants/source packets untouched, no7F invented',
        'No production story unlock, IDs/registry/save changes or ROM/native/mGBA/Save proof'])
    receipt['output_sha256']={str(q.relative_to(out)):existing.base.sha(q.read_bytes()) for q in out.rglob('*') if q.is_file() and q.name!='receipt.json'}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--private-inputs',type=Path);a=p.parse_args()
    if a.private_inputs and existing.extract(a.private_inputs)!=json.loads((HERE/'geometry.json').read_text()):raise ValueError('source extraction differs')
    print(json.dumps(build(a.engine,a.out),indent=2))
