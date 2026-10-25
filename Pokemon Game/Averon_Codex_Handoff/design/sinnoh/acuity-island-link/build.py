#!/usr/bin/env python3
"""Pair the existing Lake Acuity island door with a supported neutral cavern exit.

Water is immutable and Surf access is not asserted. No Lakefront path is invented.
"""
import argparse,importlib.util,json,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('acuity_gate_reuse',HERE.parent/'frontier-gate-link/build.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
ROOT=HERE.parents[4];LAKE=HERE.parent/'lake-acuity';CAVE=HERE.parent/'acuity-cavern'
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(g.base.git(engine,'rev-parse','--show-toplevel').decode().strip());pins={}
    def read(path):
        v=g.base.verified_file(repo,path.relative_to(repo),'HEAD');pins[str(path.relative_to(repo))]=g.base.sha(v);return v
    lake=read(LAKE/'LakeAcuity/averon-map.bin');lb=read(LAKE/'LakeAcuity/averon-border.bin')
    lh=json.loads(read(HERE.parent/'remaining-donor/staged/LakeAcuity/map.json'))
    cave=read(CAVE/'staged/map.bin');cb=read(CAVE/'staged/border.bin');ch=json.loads(read(CAVE/'staged/map.json'))
    if lh['warp_events'] or ch['warp_events']:raise ValueError('source events differ')
    geometry=json.loads(read(CAVE/'geometry.json'))
    if not any(p['tile']==[14,29] for p in geometry['walkable']) or geometry['height']!=16:raise ValueError('unsupported cavern exit')
    def family(folder):return [read(folder/p) for p in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin')]
    lp,lpa,ls,lsa=family(LAKE/'outdoor-family');cp,cpa,cs,csa=family(CAVE/'cave-family')
    old=struct.unpack_from('<H',lake,2*(29*48+23))[0];mid=old&1023
    if old&0xfc00!=0x3000 or g.pack.attribute((lpa,lsa)[mid//512],mid%512)&255!=0x60:raise ValueError('existing native island doorway differs')
    art=g.pack.words(read(engine/'data/tilesets/secondary/cave/metatiles.bin'),517-512)
    cave,cb,cs,csa,changes=g.add_portals(cave,cb,cp,cpa,cs,csa,[(14,29,32,3)],art)
    lh['warp_events']=[dict(x=23,y=29,elevation=3,dest_map=ch['id'],dest_warp_id='0')]
    ch['warp_events']=[dict(x=14,y=29,elevation=3,dest_map=lh['id'],dest_warp_id='0')]
    maps={'LakeAcuity':(lake,lb,lh,(lp,lpa,ls,lsa),(48,52),'rustboro'),
          'AcuityCavern':(cave,cb,ch,(cp,cpa,cs,csa),(32,32),'cave')}
    previews={};attrs={};paths={}
    for name,(raw,border,h,fam,dims,secondary) in maps.items():
        primary,pa,sec,sa=fam
        attr={str(v&1023):g.pack.attribute((pa,sa)[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',raw+border)};attrs[name]=attr
        foot={mid:(word&~255 if word&255 in (0x21,0x2b) else (word&~255)|0x61 if word&255==0x60 else word) for mid,word in attr.items()}
        start,end=([23,31],[23,29]) if name=='LakeAcuity' else ([14,29],[14,28])
        path=g.a.static_path(raw,*dims,start,end,foot)
        if not path:raise ValueError('local island/cavern approach inaccessible')
        paths[name]=path
        prefixes=['data/tilesets/primary/general/','data/tilesets/secondary/'+secondary+'/']
        images=[g.dual.indexed(read(engine/p/'tiles.png')) for p in prefixes];deps=g.dual.closure(raw,[primary,sec],images)
        palettes={i:g.base.palette(read(engine/prefixes[i>=6]/('palettes/%02d.pal'%i))) for i in deps['palettes']}
        previews[name]=g.dual.render(raw,[primary,sec],images,palettes,*dims)
    original=read(CAVE/'staged/map.bin')
    oldattrs=json.loads(read(CAVE/'staged/attributes.json'))
    old_reflective={i for i,(v,) in enumerate(struct.iter_unpack('<H',original)) if oldattrs[str(v&1023)]&255==0x2b}
    new_reflective={i for i,(v,) in enumerate(struct.iter_unpack('<H',cave)) if attrs['AcuityCavern'][str(v&1023)]&255==0x2b}
    if len(old_reflective)!=182 or old_reflective!=new_reflective:raise ValueError('reflective no-Surf terrain changed')
    out.mkdir(parents=True)
    for name,(raw,border,h,fam,dims,secondary) in maps.items():
        p=out/'staged'/name;p.mkdir(parents=True);(p/'map.bin').write_bytes(raw);(p/'border.bin').write_bytes(border)
        (p/'map.json').write_text(json.dumps(h,indent=2)+'\n');(p/'attributes.json').write_text(json.dumps(attrs[name],indent=2)+'\n');previews[name].save(p/'preview.png')
        f=out/'families'/name;f.mkdir(parents=True)
        for n,v in zip(('primary-metatiles','primary-attributes','secondary-metatiles','secondary-attributes'),fam):(f/(n+'.bin')).write_bytes(v)
    receipt=dict(status='NEUTRAL_ISLAND_CAVERN_SOURCE_LINK_NOT_RUNTIME_ACCEPTANCE',source_sha256=pins,cavern_changes=changes,
        lake_map_sha256=g.base.sha(lake),preserved_reflective_cells=len(old_reflective),local_paths=paths,
        limits=['Lake geometry/water/shore unchanged; Surf access and Lakefront arrival NOT established',
                'Existing native island23,29 door paired to supported cavern14,29; DS missing warp1 not copied',
                '182 reflective cells retain exact no-Surf behavior; no water-to-land flattening',
                'No legendary/story/IDs/registry/save/engine changes or ROM/native/mGBA/Save acceptance'])
    receipt['output_sha256']={str(p.relative_to(out)):g.base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();print(json.dumps(build(a.engine,a.out),indent=2))
