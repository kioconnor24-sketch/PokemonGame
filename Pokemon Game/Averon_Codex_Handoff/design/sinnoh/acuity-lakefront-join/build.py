#!/usr/bin/env python3
"""Source-grounded Lakefront cliff-mouth/land-shore pair; Surf is not bypassed."""
import argparse,importlib.util,json,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('lakefront_gate_reuse',HERE.parent/'frontier-gate-link/build.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
ROOT=HERE.parents[4];ISLAND=HERE.parent/'acuity-island-link';CITY=HERE.parent/'snowpoint-temple-entry/city-source'
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(g.base.git(engine,'rev-parse','--show-toplevel').decode().strip());pins={}
    def read(p):
        raw=g.base.verified_file(repo,p.relative_to(repo),'HEAD');pins[str(p.relative_to(repo))]=g.base.sha(raw);return raw
    reference=json.loads(read(HERE/'source-pins.json'))
    for name,pin in reference['files'].items():
        if g.base.sha(read(HERE/'lakefront-source'/name))!=pin['sha256']:raise ValueError('readonly Lakefront source differs')
    front=read(HERE/'lakefront-source/map.bin');fb=read(HERE/'lakefront-source/border.bin');fh=json.loads(read(HERE/'lakefront-source/map.json'))
    lake=read(ISLAND/'staged/LakeAcuity/map.bin');lb=read(ISLAND/'staged/LakeAcuity/border.bin');lh=json.loads(read(ISLAND/'staged/LakeAcuity/map.json'))
    if fh['warp_events'] or len(lh['warp_events'])!=1:raise ValueError('existing portal prefix differs')
    specs={'AcuityLakefront':(front,fb,fh,CITY,64,66,[(20,39,64,3),(21,39,64,3)]),
           'LakeAcuity':(lake,lb,lh,ISLAND/'families/LakeAcuity',48,52,[(6,48,48,3),(7,48,48,3)])}
    packets={};families={};changes={};attrs={};paths={};previews={}
    for name,(raw,border,h,folder,w,height,points) in specs.items():
        primary,pa,sec,sa=[read(folder/p) for p in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin')]
        words=[struct.unpack_from('<H',raw,2*(y*w+x))[0] for x,y,_,_ in points]
        if len(set(words))!=1 or words[0]&0xfc00!=0x3000:raise ValueError('existing ground mouth/shore differs')
        mid=words[0]&1023;behavior=g.pack.attribute((pa,sa)[mid//512],mid%512)&255
        if behavior not in (0,0x21):raise ValueError('cannot turn water/hazard into entry ground')
        art=g.pack.words((primary,sec)[mid//512],mid%512)
        data,border,sec,sa,delta=g.add_portals(raw,border,primary,pa,sec,sa,points,art)
        packets[name]=(data,border,h,w,height);families[name]=(primary,pa,sec,sa);changes[name]=delta
        attrs[name]={str(v&1023):g.pack.attribute((pa,sa)[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',data+border)}
        foot={mid:(v&~255 if v&255==0x21 else v) for mid,v in attrs[name].items()}
        local=[]
        for x,y,_,_ in points:
            start=[x,y+1] if name=='AcuityLakefront' else [x,y-1]
            path=g.a.static_path(data,w,height,start,[x,y],foot)
            if not path:raise ValueError('source ground doorway not accessible')
            local.append(path)
        paths[name]=local
        prefixes=['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/']
        images=[g.dual.indexed(read(engine/p/'tiles.png')) for p in prefixes];deps=g.dual.closure(data,[primary,sec],images)
        palettes={i:g.base.palette(read(engine/prefixes[i>=6]/('palettes/%02d.pal'%i))) for i in deps['palettes']}
        previews[name]=g.dual.render(data,[primary,sec],images,palettes,w,height)
    fh['warp_events']=[dict(x=20,y=39,elevation=3,dest_map=lh['id'],dest_warp_id='1'),dict(x=21,y=39,elevation=3,dest_map=lh['id'],dest_warp_id='2')]
    lh['warp_events']+= [dict(x=6,y=48,elevation=3,dest_map=fh['id'],dest_warp_id='0'),dict(x=7,y=48,elevation=3,dest_map=fh['id'],dest_warp_id='1')]
    # Source water remains byte/attribute-identical even when C/E permits movement.
    water={}
    for name,(data,border,h,w,height) in packets.items():
        old=specs[name][0];folder=specs[name][3]
        opa=read(folder/'primary-attributes.bin');osa=read(folder/'secondary-attributes.bin');count=0
        for (a,),(b,) in zip(struct.iter_unpack('<H',old),struct.iter_unpack('<H',data)):
            word=g.pack.attribute((opa,osa)[(a&1023)//512],a%512)
            if word&255==0x10:
                if a!=b or attrs[name][str(b&1023)]!=word:raise ValueError('water or layer semantics changed')
                count+=1
        water[name]=count
    out.mkdir(parents=True)
    for name,(raw,border,h,w,height) in packets.items():
        p=out/'staged'/name;p.mkdir(parents=True);(p/'map.bin').write_bytes(raw);(p/'border.bin').write_bytes(border)
        (p/'map.json').write_text(json.dumps(h,indent=2)+'\n');(p/'attributes.json').write_text(json.dumps(attrs[name],indent=2)+'\n');previews[name].save(p/'preview.png')
        f=out/'families'/name;f.mkdir(parents=True)
        for n,v in zip(('primary-metatiles','primary-attributes','secondary-metatiles','secondary-attributes'),families[name]):(f/(n+'.bin')).write_bytes(v)
    receipt=dict(status='SOURCE_GROUNDED_CLIFF_SHORE_JOIN_NOT_RUNTIME_ACCEPTANCE',source_sha256=pins,changes=changes,
        preserved_water_cells=water,local_ground_paths=paths,
        limits=['Existing cliff mouth20/21,39 matches pinned DS entry after native+2row adaptation',
                'Lake shore6/7,48 explicitly adapted to existing land, no DS indices blindly copied',
                'Original island/cavern event0 and regional connections preserved; every water/layer word unchanged',
                'No new trail/tree cuts/footbridge/Surf grant/story/low-water variant/IDs/registry/save changes',
                'Static local ground checks are not natural arrival or Surf/runtime/Save acceptance'])
    receipt['output_sha256']={str(p.relative_to(out)):g.base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();print(json.dumps(build(a.engine,a.out),indent=2))
