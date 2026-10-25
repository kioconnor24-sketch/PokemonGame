#!/usr/bin/env python3
"""Explicit reversible source-stage Frontier gateway; original packets immutable."""
import argparse,importlib.util,json,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('gate_existing',HERE.parent/'stark-approach/build_source.py')
a=importlib.util.module_from_spec(s);s.loader.exec_module(a)
base=a.base;dual=a.dual;pack=a.packer
ROOT=HERE.parents[4]
F=HERE.parent/'frontier-facilities';C=HERE.parent/'frontier-campus';B=HERE.parent/'battle-zone-north';L=HERE.parent/'battle-zone-links'

def add_portals(raw,border,primary,pa,sec,sa,points,art):
    cells=bytearray(raw);placeholder=512+len(sec)//16;changes=[]
    for x,y,w,z in points:
        i=2*(y*w+x);old=struct.unpack_from('<H',cells,i)[0]
        struct.pack_into('<H',cells,i,z<<12|placeholder);changes.append(dict(cell=[x,y],before=old))
    attrs=[pa,sa+struct.pack('<H',0x1061)];wanted=[]
    for (v,) in struct.iter_unpack('<H',cells+border):
        mid=v&1023
        wanted.append(art if mid==placeholder else pack.words((primary,sec)[mid//512],mid%512))
    converted,newsec,newsa=pack.pack_art(cells+border,wanted,attrs,primary,pa,sec,sa)
    if newsec[:len(sec)]!=sec or newsa[:len(sa)]!=sa:raise ValueError('source metadata prefix changed')
    for p in changes:
        x,y=p['cell'];w=points[0][2];p['after']=struct.unpack_from('<H',converted,2*(y*w+x))[0]
    return converted[:len(raw)],converted[len(raw):],newsec,newsa,changes

def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(base.git(engine,'rev-parse','--show-toplevel').decode().strip());pins={}
    def read(path):
        v=base.verified_file(repo,path.relative_to(repo),'HEAD');pins[str(path.relative_to(repo))]=base.sha(v);return v
    headers={n:json.loads(read(p)) for n,p in [('Campus',F/'staged/Campus/map.json'),('Gate',C/'staged/Gate/map.json'),('FightArea',L/'staged/FightArea/map.json')]}
    if len(headers['Campus']['warp_events'])!=5 or headers['Gate']['warp_events'] or headers['FightArea']['warp_events']:raise ValueError('source warp prefix differs')
    # Native gate door points are actual supported source0-height footprints.
    geometry=json.loads(read(C/'geometry.json'))
    for n,points in [('Gate',[(7,2),(7,20)]),('Campus',[(48,52)])]:
        supported={tuple(p['tile']):p for p in geometry[n]['surfaces']}
        if any(p not in supported for p in points):raise ValueError('unsupported source gate')
        expected='0' if n=='Gate' else '16'
        if any(supported[p]['height']!=expected or not supported[p]['flat'] for p in points):raise ValueError('source gate height differs')
    specs={
        'Campus':dict(folder=F/'staged/Campus',family=F/'campus-family',dims=(96,96),points=[(48,52,96,3)],secondary='rustboro'),
        'Gate':dict(folder=C/'staged/Gate',family=C/'native-family',dims=(32,32),points=[(7,2,32,3),(7,20,32,3)],secondary='cave'),
        'FightArea':dict(folder=L/'staged/FightArea',family=B/'outdoor-family',dims=(70,37),points=[(50,9,70,3)],secondary='rustboro')}
    packets={};changes={};families={}
    for name,spec in specs.items():
        p=spec['folder'];raw=read(p/'map.bin');border=read(p/'border.bin')
        family=spec['family'];primary,pa,sec,sa=[read(family/v) for v in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin')]
        if name=='Gate':art=pack.words(read(engine/'data/tilesets/secondary/cave/metatiles.bin'),516-512)
        else:art=pack.words(primary,265)
        data,border,newsec,newsa,delta=add_portals(raw,border,primary,pa,sec,sa,spec['points'],art)
        packets[name]=(data,border);families[name]=(primary,pa,newsec,newsa);changes[name]=delta
    campus,gate,fight=[headers[n] for n in ('Campus','Gate','FightArea')]
    campus['warp_events'].append(dict(x=48,y=52,elevation=3,dest_map=gate['id'],dest_warp_id='0'))
    gate['warp_events']=[dict(x=7,y=2,elevation=3,dest_map=campus['id'],dest_warp_id='5'),dict(x=7,y=20,elevation=3,dest_map=fight['id'],dest_warp_id='0')]
    fight['warp_events']=[dict(x=50,y=9,elevation=3,dest_map=gate['id'],dest_warp_id='1')]
    paths={};previews={};attributes={}
    for name,(raw,border) in packets.items():
        primary,pa,sec,sa=families[name];w,h=specs[name]['dims']
        attrs={str(v&1023):pack.attribute((pa,sa)[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',raw+border)};attributes[name]=attrs
        if name=='Gate':path=a.static_path(raw,w,h,[7,2],[7,20],attrs)
        elif name=='Campus':path=a.static_path(raw,w,h,[48,51],[48,52],attrs)
        else:path=a.static_path(raw,w,h,[50,10],[50,9],attrs)
        if not path:raise ValueError('gateway approach not statically accessible: '+name)
        paths[name]=path
        prefixes=['data/tilesets/primary/general/','data/tilesets/secondary/'+specs[name]['secondary']+'/']
        images=[dual.indexed(read(engine/p/'tiles.png')) for p in prefixes];deps=dual.closure(raw,[primary,sec],images)
        palettes={i:base.palette(read(engine/prefixes[i>=6]/('palettes/%02d.pal'%i))) for i in deps['palettes']}
        previews[name]=dual.render(raw,[primary,sec],images,palettes,w,h)
    facility_paths={}
    campus_raw=packets['Campus'][0];campus_attrs=attributes['Campus']
    for target in campus['warp_events'][:-1]:
        # Do not route through another active portal while proving this approach.
        data=bytearray(campus_raw)
        for event in campus['warp_events'][:-1]:
            if event is target:continue
            i=2*(event['y']*96+event['x']);v=struct.unpack_from('<H',data,i)[0];struct.pack_into('<H',data,i,v|0xc00)
        path=a.static_path(data,96,96,[48,52],[target['x'],target['y']],campus_attrs)
        if not path:raise ValueError('campus facility cannot reach gate without another portal')
        facility_paths[target['dest_map']]=path
    out.mkdir(parents=True)
    for name,(raw,border) in packets.items():
        p=out/'staged'/name;p.mkdir(parents=True);(p/'map.bin').write_bytes(raw);(p/'border.bin').write_bytes(border)
        (p/'map.json').write_text(json.dumps(headers[name],indent=2)+'\n')
        (p/'attributes.json').write_text(json.dumps(attributes[name],indent=2)+'\n');previews[name].save(p/'preview.png')
        family=out/'families'/name;family.mkdir(parents=True)
        for n,v in zip(('primary-metatiles','primary-attributes','secondary-metatiles','secondary-attributes'),families[name]):(family/(n+'.bin')).write_bytes(v)
    receipt=dict(status='EXPLICIT_NATIVE_GATEWAY_SOURCE_NOT_RUNTIME_ACCEPTANCE',source_sha256=pins,changes=changes,static_paths=paths,facility_paths=facility_paths,
        family_secondary_records={n:len(v[2])//16 for n,v in families.items()},
        limits=['FightArea50,9 threshold explicitly authored, not DS source warp2','Original map packets/IDs/old campus warp prefix unchanged','No story/transport/progression/competitive mechanics','Static ordinary approaches only; not full town/Surf/rail/gameplay acceptance','No production registry/save changes/ROM/native-suite/mGBA/Save proof'])
    receipt['output_sha256']={str(p.relative_to(out)):base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);v=p.parse_args();print(json.dumps(build(v.engine,v.out),indent=2))
