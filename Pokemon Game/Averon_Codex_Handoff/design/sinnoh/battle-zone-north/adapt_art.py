#!/usr/bin/env python3
"""Reuse the existing packer for nine pinned northern maps, no donor art import."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import struct

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('battle_existing_packer',HERE.parent/'canalave-west/adapt_outdoor_art.py')
existing=importlib.util.module_from_spec(s);s.loader.exec_module(existing)
pack=existing.pack;base=pack.accepted.base
SOURCE=HERE.parent/'remaining-donor';ROOT=HERE.parents[4]
MAPS={'Route225':(32,94),'SurvivalArea':(32,32),'Route226':(100,32),'Route227':(48,60),'FightArea':(70,37),'Route228':(32,94),'Route229':(64,30),'ResortArea':(36,30),'Route230':(96,34)}
plan=json.loads((HERE/'art-plan.json').read_text())
if set(plan['maps'])!=set(MAPS):raise ValueError('exact northern cluster required')
for n,d in MAPS.items():
    if plan['maps'][n]['dimensions']!=list(d):raise ValueError('planned source dimensions differ')
existing.HERE=SOURCE;existing.MAPS=MAPS
existing.SECONDARY={n:{int(k):v for k,v in plan['maps'][n]['secondary_remap'].items()} for n in MAPS}
existing.FACADES={n:[(tuple(a),tuple(b)) for a,b in plan['maps'][n]['facades']] for n in MAPS}
existing.BRIDGES={n:set(plan['maps'][n]['wood_walkway_ids']) for n in MAPS}
existing.templates.HERE=SOURCE;existing.templates.MAPS=MAPS;existing.templates.SECONDARY=existing.SECONDARY
existing.templates.FACADES=existing.FACADES;existing.templates.PRIMARY={};existing.templates.BRIDGE=set()
# This private template instance uses full source-envelope resampling instead
# of its4x4 Center special case, which would leave an old roof strip here.
existing.templates.CENTER=(-1,-1,0,0)


original_desired_art=existing.desired_art
def desired_art(name,*args):
    old=existing.templates.PRIMARY
    existing.templates.PRIMARY={int(k):v for k,v in plan['maps'][name].get('primary_remap',{}).items()}
    try:return original_desired_art(name,*args)
    finally:existing.templates.PRIMARY=old
existing.desired_art=desired_art


def verify_source(repo):
    repo=Path(repo).resolve();receipt=json.loads(base.verified_file(repo,SOURCE.relative_to(repo)/'source-receipt.json','HEAD'));pins={}
    for name,(w,h) in MAPS.items():
        files={p:base.verified_file(repo,SOURCE.relative_to(repo)/'staged'/name/p,'HEAD') for p in ('map.bin','border.bin','map.json','attributes.json')}
        old=receipt['maps'][name]
        if len(files['map.bin'])!=2*w*h or base.sha(files['map.bin'])!=old['staged_sha256'] or base.sha(files['border.bin'])!=old['border_sha256']:
            raise ValueError('pinned source geometry differs')
        header=json.loads(files['map.json'])
        if header['region_map_section']!='MAPSEC_PENDING_OWNER' or any(header[k] for k in ('object_events','coord_events','bg_events','warp_events')):raise ValueError('neutral source packet required')
        # The inherited converter and seam auditor consume these worktree files.
        # A committed pin alone does not authenticate their actual input bytes.
        for filename, verified in files.items():
            if (SOURCE/'staged'/name/filename).read_bytes()!=verified:
                raise ValueError('worktree source differs from committed pin: '+name+'/'+filename)
        pins[name]={p:base.sha(v) for p,v in files.items()}
    return pins


def seam_audit(files):
    """Only source C/E seam support, not Surf/foot/gameplay acceptance."""
    headers={n:json.loads((SOURCE/'staged'/n/'map.json').read_text()) for n in MAPS}
    names={v['id']:n for n,v in headers.items()};result=[]
    for name,(w,h) in MAPS.items():
        cells=struct.unpack('<%dH'%(w*h),files[name])
        for link in headers[name]['connections']:
            if link['map'] not in names:continue
            target=names[link['map']];dw,dh=MAPS[target];destcells=struct.unpack('<%dH'%(dw*dh),files[target])
            direction=link['direction'];off=link['offset'];opposite={'up':'down','down':'up','left':'right','right':'left'}
            if dict(map=headers[name]['id'],direction=opposite[direction],offset=-off) not in headers[target]['connections']:
                raise ValueError('nonreciprocal source connection')
            usable=[]
            for i in range(w if direction in ('up','down') else h):
                a=(i,0 if direction=='up' else h-1) if direction in ('up','down') else (0 if direction=='left' else w-1,i)
                b=(i-off,dh-1 if direction=='up' else 0) if direction in ('up','down') else (dw-1 if direction=='left' else 0,i-off)
                if not 0<=b[0]<dw or not 0<=b[1]<dh:continue
                first=cells[a[1]*w+a[0]];second=destcells[b[1]*dw+b[0]]
                if first&0xc00 or second&0xc00:continue
                z,zz=first>>12,second>>12
                if z not in (0,15) and zz not in (0,15,z):continue
                usable.append(dict(source=list(a),target=list(b),elevations=[z,zz]))
            identity=dict(source=name,target=target,direction=direction,offset=off)
            closed=identity in plan.get('closed_source_connections',[])
            if not usable and not closed:raise ValueError('source connection has no compatible seam lane: '+name+' '+direction+' -> '+target)
            if usable and closed:raise ValueError('closed source gate unexpectedly opened')
            result.append(dict(**identity,state='CLOSED_SOURCE_METADATA_ONLY' if closed else 'COMPATIBLE_GEOMETRY_ONLY',compatible_lanes=usable))
    return result


def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    repo=Path(base.git(engine,'rev-parse','--show-toplevel').decode().strip());pins=verify_source(repo)
    before=seam_audit({n:(SOURCE/'staged'/n/'map.bin').read_bytes() for n in MAPS})
    receipt=existing.build(engine,out)
    # The immutable engine tree identifies source independent of docs-only heads.
    del receipt['engine_source'];receipt['engine_tree']=base.git(repo,'rev-parse','HEAD:Pokemon Game/engine').decode().strip()
    staged=out/'staged';staged.mkdir()
    for name in MAPS:shutil.move(str(out/name),staged/name)
    after=seam_audit({n:(staged/n/'averon-map.bin').read_bytes() for n in MAPS})
    if after!=before:raise ValueError('source seam lanes changed during art conversion')
    for path,expected in plan['preserved_first_four_outputs'].items():
        if base.sha((out/path).read_bytes())!=expected:raise ValueError('accepted first-four art packet changed')
    for path,pin in plan['preserved_secondary_prefix'].items():
        if base.sha((out/path).read_bytes()[:pin['bytes']])!=pin['sha256']:raise ValueError('first-four metadata prefix changed')
    (out/'outdoor-art-receipt.json').unlink()  # own freshly generated intermediate
    receipt.update(status='NINE_MAP_NATIVE_ART_SOURCE_ONLY_NOT_RUNTIME_ACCEPTANCE',source_pins=pins,art_plan_sha256=base.sha((HERE/'art-plan.json').read_bytes()),
        source_revision='38228bb574a3557345852b758d5f1a65eb01bb22',source_seams=after,
        output_sha256={str(p.relative_to(out)):base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()},
        limits=['Only existing native General/Rustboro pixels/palettes are emitted; no donor artwork',
                'Actual donor art inspected privately for facade/terrain roles; native proxies are not pixel-identical final art',
                'All source C/E/full behavior/layer words and existing connection headers preserved',
                'Route225 bridge priority, Route226 Surf and Route227 Acro rails remain runtime integration requirements',
                'Original staged closed house doors/external boundaries remain closed; no services, content or permanent IDs',
                'No engine installation, ROM/native-suite/mGBA/Save or production acceptance'])
    (out/'source-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();print(json.dumps(build(a.engine,a.out),indent=2))
