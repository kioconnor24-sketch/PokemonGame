#!/usr/bin/env python3
"""Original neutral Hotel connector; reuse stager/packer, preserve accepted12-map inputs."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

stage=module('hotel_stage',HERE.parent/'eterna-cycle/stage_batch.py')
gate=module('hotel_gate',HERE/'adapt_gate_art.py')
pack=gate.shared.pack
BLOB='4ffd2c9d215171d44aa4396ccd93d76b7026ff85'
MAP='HotelGrandLake'
ANCHORS=[(7,1),(7,10)]


def build(donor,engine,out):
    donor,engine,out=map(lambda p:Path(p).resolve(),(donor,engine,out))
    # Existing identity converter validates just this180-cell source. The
    # generic single-map stage closes foreign exits; restore the exact pinned
    # original pair only after verifying the known Route213 context below.
    receipt=stage.build(donor,out,maps={MAP:(15,12,BLOB)})
    original=receipt['source_geometry_headers'][MAP]
    if [(w['x'],w['y'],w['dest_map'],int(w['dest_warp_id'])) for w in original['warp_events']]!=[(7,1,'MAP_ROUTE213',2),(7,10,'MAP_ROUTE213',1)]:
        raise ValueError('original Hotel pair changed')
    folder=out/'staged'/MAP
    raw=stage.subprocess.check_output(['git','-C',str(donor),'show',stage.REVISION+':data/layouts/HotelGrandLake/map.bin'])
    if len(raw)!=360 or stage.sha(raw)!=receipt['maps'][MAP]['source_sha256']:raise ValueError('Hotel source identity mismatch')
    header=json.loads((folder/'map.json').read_text());header['warp_events']=copy.deepcopy(original['warp_events'])
    (folder/'map.bin').write_bytes(raw);(folder/'map.json').write_bytes(stage.encode(header));stage.schematic(raw,15,12).save(folder/'collision.png')
    receipt.update(status='NEUTRAL_ORIGINAL_HOTEL_CONNECTOR_NOT_PRODUCTION',closure_changes={MAP:[]},warp_index_translation={MAP:{0:0,1:1}})
    receipt['maps'][MAP].update(staged_sha256=stage.sha(raw),closed_cells=0,warp_count=2)
    (out/'source-receipt.json').write_bytes(stage.encode(receipt))
    root=Path(pack.accepted.base.git(engine,'rev-parse','--show-toplevel').decode().strip());rev=pack.accepted.base.git(engine,'rev-parse','HEAD').decode().strip();assets={}
    def read(path):
        data=pack.accepted.base.verified_file(root,engine.relative_to(root)/path,rev);assets[path]=stage.sha(data);return data
    primary=(HERE/'gate-art/primary-metatiles.bin').read_bytes();pa=(HERE/'gate-art/primary-attributes.bin').read_bytes()
    secondary=(HERE/'gate-art/secondary-metatiles.bin').read_bytes();sa=(HERE/'gate-art/secondary-attributes.bin').read_bytes();old_secondary=secondary;old_sa=sa
    attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words'];source_attrs=[bytearray(1024),bytearray(1024)]
    for mid,value in attrs.items():b,i=divmod(int(mid),512);struct.pack_into('<H',source_attrs[b],2*i,value)
    adapted,secondary,sa=gate.shared.candidate(raw,15,12,header['warp_events'],source_attrs,primary+bytes(8192-len(primary)),pa+bytes(1024-len(pa)),secondary,sa,expected_anchors=ANCHORS)
    if not secondary.startswith(old_secondary) or not sa.startswith(old_sa):raise ValueError('existing four gateway records changed')
    for (old,),(new,) in zip(struct.iter_unpack('<H',raw),struct.iter_unpack('<H',adapted)):
        b,i=divmod(new&1023,512)
        if old&0xFC00!=new&0xFC00 or pack.attribute((pa,sa)[b],i)!=attrs[str(old&1023)]:raise ValueError('Hotel physics/attrs changed')
    (folder/'averon-map.bin').write_bytes(adapted)
    # Restore only original Route213 records. An animated door remains C1;
    # native TryDoorWarp handles it. The north arrow alone was artificially C1.
    context=json.loads((HERE/'source-receipt.json').read_text());route_header=json.loads((HERE/'staged/Route213/map.json').read_text())
    events=context['source_geometry_headers']['Route213']['warp_events']
    if len(events)!=3 or route_header['warp_events']!=events[:1]:raise ValueError('accepted Route213 prefix changed')
    route_header['warp_events']=copy.deepcopy(events)
    if [(w['x'],w['y']) for w in events[1:]]!=[(68,16),(68,11)]:raise ValueError('Hotel source doors changed')
    closures=[c for c in context['closure_changes']['Route213'] if (c['x'],c['y']) in [(68,11),(68,16)]]
    if len(closures)!=1 or (closures[0]['x'],closures[0]['y'])!=(68,11):raise ValueError('expected one north-arrow closure')
    src=(HERE/'staged/Route213/map.bin').read_bytes();route=bytearray((HERE/'staged/Route213/averon-map.bin').read_bytes());w=100
    for c in closures:
        i=c['y']*w+c['x'];old=struct.unpack_from('<H',src,2*i)[0]
        if old!=c['after'] or (c['before']^old)!=0x400:raise ValueError('source closure is not the recorded collision bit')
        value=struct.unpack_from('<H',route,2*i)[0];struct.pack_into('<H',route,2*i,(value&0x3FF)|(c['before']&0xFC00))
    op=(HERE/'outdoor-family/primary-metatiles.bin').read_bytes();opa=(HERE/'outdoor-family/primary-attributes.bin').read_bytes();os=(HERE/'outdoor-family/secondary-metatiles.bin').read_bytes();osa=(HERE/'outdoor-family/secondary-attributes.bin').read_bytes()
    desired=[pack.words((op,os)[(v[0]&1023)//512],v[0]&511) for v in struct.iter_unpack('<H',route)]
    general=read('data/tilesets/primary/general/metatiles.bin')
    desired[11*w+68]=pack.words(general,207);desired[16*w+68]=pack.words(general,33)
    new_route,ns,nsa=pack.pack_art(bytes(route),desired,(opa,osa),op,opa,os,osa)
    if not ns.startswith(os) or not nsa.startswith(osa):raise ValueError('accepted eight-map metadata prefix changed')
    # Four mutually matched seam cells form a4-cell component with no path
    # into either map interior. Cap only those technical ghost endpoints.
    frontier=[];valor=(HERE/'staged/ValorLakefront/averon-map.bin').read_bytes()
    maps_to_cap=[('Route213',new_route,100,[(82,0),(83,0)]),
                 ('ValorLakefront',valor,56,[(42,65),(43,65)])]
    capped={}
    for name,geometry,width,points in maps_to_cap:
        edited=bytearray(geometry)
        wanted=[pack.words((op,ns)[(v[0]&1023)//512],v[0]&511) for v in struct.iter_unpack('<H',geometry)]
        for x,y in points:
            i=y*width+x;value=struct.unpack_from('<H',edited,2*i)[0]
            if value&0xC00:raise ValueError('ghost cap no longer points at original passable cell')
            struct.pack_into('<H',edited,2*i,value|0x400);wanted[i]=pack.words(general,225)
            frontier.append(dict(map=name,x=x,y=y,before_runtime=value,after_collision=value|0x400,
                                 reason='isolated four-cell mutually matched border component'))
        adapted_cap,ns,nsa=pack.pack_art(bytes(edited),wanted,(opa,nsa),op,opa,ns,nsa)
        capped[name]=adapted_cap
    new_route=capped['Route213'];valor=capped['ValorLakefront']
    (out/'frontier-closures.json').write_bytes(stage.encode(dict(status='FOUR_GHOST_ENDPOINT_CAPS_NOT_GEOGRAPHIC_REDESIGN',cells=frontier,all_elevations_attributes_and_mainland_preserved=True,remaining_runtime_closures_vs_donor=343)))
    for name,banks in [('gate-art',(primary,pa,secondary,sa)),('outdoor-family',(op,opa,ns,nsa))]:
        d=out/name;d.mkdir()
        for filename,data in zip(('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin'),banks):(d/filename).write_bytes(data)
    dependencies={}
    for name,geometry,border,records,paths,dims,target in [(MAP,adapted,(folder/'border.bin').read_bytes(),(primary,secondary),('data/tilesets/primary/building/','data/tilesets/secondary/shop/'),(15,12),folder/'averon.png'),('Route213',new_route,(HERE/'staged/Route213/averon-border.bin').read_bytes(),(op,ns),('data/tilesets/primary/general/','data/tilesets/secondary/rustboro/'),(100,60),out/'route213-preview.png'),('ValorLakefront',valor,(HERE/'staged/ValorLakefront/averon-border.bin').read_bytes(),(op,ns),('data/tilesets/primary/general/','data/tilesets/secondary/rustboro/'),(56,66),out/'valor-preview.png')]:
        images=[pack.accepted.dual.indexed(read(p+'tiles.png')) for p in paths];dep=pack.accepted.dual.closure(geometry+border,records,images);dependencies[name]=dep
        palettes={i:pack.accepted.base.palette(read(paths[i>=6]+'palettes/%02d.pal'%i)) for i in dep['palettes']};pack.accepted.dual.render(geometry,records,images,palettes,*dims).save(target)
    (out/'valor-map.bin').write_bytes(valor);(out/'route213-map.bin').write_bytes(new_route);(out/'route213-map.json').write_bytes(stage.encode(route_header))
    plan=dict(status='EXACT_ORIGINAL_CONNECTOR_RESTORATION_DEV_ONLY',source_stage_sha256=stage.sha((HERE/'source-receipt.json').read_bytes()),closure_restorations=closures,existing_route213_warp_prefix=events[:1],append_original_warps=events[1:],all_existing17_event_indices_preserved=True,new_total_warp_events=21,temporary_hotel_slot=31,source_staged_files_unmodified=True,ghost_endpoint_caps=4,remaining_runtime_closures_vs_donor=343,limits=['Only one original north collision reopened; south animated door stays original C1','No permanent section/map IDs or production save migration','Four isolated ghost endpoints capped; whole-cluster audit still required'])
    (out/'restoration-plan.json').write_bytes(stage.encode(plan));(out/'art-receipt.json').write_bytes(stage.encode(dict(status='EXISTING_AVERON_HOTEL_CONNECTOR_ART_NOT_RUNTIME_ACCEPTANCE',engine_source=rev,verified_hotel_cells=180,gate_secondary_records=len(secondary)//16,outdoor_secondary_records=len(ns)//16,existing_averon_sha256=assets,dependencies=dependencies,route213_sha256=stage.sha(new_route))))
    return plan


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('donor','engine','out'):p.add_argument('--'+n,required=True,type=Path)
    a=p.parse_args();print(json.dumps(build(a.donor,a.engine,a.out),indent=2))
