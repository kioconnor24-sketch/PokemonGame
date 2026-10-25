#!/usr/bin/env python3
"""Authored neutral gate apertures over immutable Battle Zone source packets.

No original packet, engine registry, saved identity or donor artwork is changed.
Boundary connectivity is not whole-route foot/Surf or emulator acceptance.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
from collections import deque

HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'battle-zone-north'
s=importlib.util.spec_from_file_location('battle_links_base',BASE/'adapt_art.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ROOT=HERE.parents[4]
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def load_baseline():
    plan=json.loads((HERE/'plan.json').read_text())
    for path,expected in plan['baseline_sha256'].items():
        committed=m.base.verified_file(ROOT,BASE.relative_to(ROOT)/path,'HEAD')
        if sha(committed)!=expected or (BASE/path).read_bytes()!=committed:
            raise ValueError('baseline pin/worktree mismatch: '+path)
    return plan,{n:(BASE/'staged'/n/'averon-map.bin').read_bytes() for n in m.MAPS}

def word(raw,w,x,y):return struct.unpack_from('<H',raw,2*(y*w+x))[0]

def foot_path(raw,w,h,start,end):
    # Only ordinary z3, normal-behavior cells are allowed in these small
    # authored approaches. No bridge-15, Surf, jump or controller simulation.
    pa=(BASE/'outdoor-family/primary-attributes.bin').read_bytes()
    sa=(BASE/'outdoor-family/secondary-attributes.bin').read_bytes()
    def usable(p):
        x,y=p
        if not (0<=x<w and 0<=y<h):return False
        v=word(raw,w,x,y);bank,i=divmod(v&1023,512)
        return v&0xfc00==0x3000 and m.pack.attribute((pa,sa)[bank],i)&255==0
    start,end=tuple(start),tuple(end)
    if not usable(start) or not usable(end):return []
    queue=deque([start]);prev={start:None}
    while queue:
        p=queue.popleft()
        if p==end:
            path=[]
            while p is not None:path.append(list(p));p=prev[p]
            return path[::-1]
        for dx,dy in ((0,1),(0,-1),(1,0),(-1,0)):
            q=p[0]+dx,p[1]+dy
            if q not in prev and usable(q):prev[q]=p;queue.append(q)
    return []

def construct(plan,original):
    result=dict(original);changes=[];approaches=[]
    for name,edit in plan['authored_apertures'].items():
        w,h=m.MAPS[name];raw=bytearray(original[name]);x,y,bw,bh=edit['rectangle']
        if bw<=0 or bh<=0 or min(x,y)<0 or x+bw>w or y+bh>h:raise ValueError('invalid aperture')
        for yy in range(y,y+bh):
            for xx in range(x,x+bw):
                old=word(raw,w,xx,yy)
                if not old&0xc00 and not (name=='Route225' and [xx,yy] in plan['removed_inert_behavior']['cells']):
                    raise ValueError('unexpected passable source replacement')
                new=0x3001 # native General ordinary ground; explicitly authored z3
                struct.pack_into('<H',raw,2*(yy*w+xx),new)
                changes.append(dict(map=name,cell=[xx,yy],before=old,after=new))
        result[name]=bytes(raw)
        for anchor,end in edit['foot_approaches']:
            path=foot_path(raw,w,h,anchor,end)
            if not path:raise ValueError('authored gate approach not ordinary-foot accessible')
            approaches.append(dict(map=name,anchor=anchor,boundary=end,path=path))
    # Reuse original reciprocal/elevation auditor with a private closed-list
    # override: all formerly closed seams must genuinely acquire matching lanes.
    original_closed=m.plan['closed_source_connections']
    try:
        m.plan['closed_source_connections']=[]
        seams=m.seam_audit(result)
    finally:m.plan['closed_source_connections']=original_closed
    graph={n:set() for n in m.MAPS}
    for link in seams:graph[link['source']].add(link['target'])
    seen=set();todo=[next(iter(graph))]
    while todo:
        n=todo.pop()
        if n in seen:continue
        seen.add(n);todo.extend(graph[n]-seen)
    if seen!=set(graph):raise ValueError('boundary graph remains disconnected')
    return result,dict(changed_cells=changes,ordinary_foot_approaches=approaches,seams=seams,
                      boundary_components=[sorted(seen)])

def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    plan,original=load_baseline();result,audit=construct(plan,original)
    # Render with the existing reviewed pipeline and verified native assets.
    dual=m.pack.accepted.dual
    banks=[(BASE/'outdoor-family'/n).read_bytes() for n in ('primary-metatiles.bin','secondary-metatiles.bin')]
    prefixes=('data/tilesets/primary/general/','data/tilesets/secondary/rustboro/')
    def read(path):
        raw=m.base.verified_file(ROOT,engine.relative_to(ROOT)/path,'HEAD')
        if sha(raw)!=plan['native_asset_sha256'][path]:raise ValueError('native asset identity changed')
        return raw
    images=[dual.indexed(read(p+'tiles.png')) for p in prefixes]
    previews={};attrs={}
    for n in plan['authored_apertures']:
        raw=result[n];border=(BASE/'staged'/n/'averon-border.bin').read_bytes()
        dependencies=dual.closure(raw+border,banks,images)
        palettes={i:m.base.palette(read(prefixes[i>=6]+'palettes/%02d.pal'%i)) for i in dependencies['palettes']}
        previews[n]=dual.render(raw,banks,images,palettes,*m.MAPS[n])
        pa=(BASE/'outdoor-family/primary-attributes.bin').read_bytes();sa=(BASE/'outdoor-family/secondary-attributes.bin').read_bytes()
        attrs[n]={str(v&1023):m.pack.attribute((pa,sa)[(v&1023)//512],(v&1023)%512) for (v,) in struct.iter_unpack('<H',raw+border)}
    out.mkdir(parents=True)
    for n in plan['authored_apertures']:
        p=out/'staged'/n;p.mkdir(parents=True)
        (p/'map.bin').write_bytes(result[n]);(p/'border.bin').write_bytes((BASE/'staged'/n/'averon-border.bin').read_bytes())
        # Metadata is preserved; only the physical aperture is authored.
        (p/'map.json').write_bytes((m.SOURCE/'staged'/n/'map.json').read_bytes())
        (p/'attributes.json').write_text(json.dumps(attrs[n],indent=2)+'\n')
        previews[n].save(p/'preview.png')
    receipt=dict(status='AUTHORED_BOUNDARY_SOURCE_ART_ONLY_NOT_RUNTIME_ACCEPTANCE',
                 base_pr=266,base_head=plan['base_head'],baseline_sha256=plan['baseline_sha256'],
                 plan_sha256=sha((HERE/'plan.json').read_bytes()),**audit,
                 unchanged_maps=[n for n in m.MAPS if n not in plan['authored_apertures']],
                 limits=['One boundary graph is not whole-route walking/Surf/bridge acceptance',
                         '30 cells explicitly authored; original donor pins and artifacts remain unchanged',
                         'No warps, content, permanent IDs, registry or save changes',
                         'No ROM/native-suite/mGBA/Save/Delta acceptance'])
    receipt['output_sha256']={str(p.relative_to(out)):sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    a=p.parse_args();print(json.dumps(build(a.engine,a.out),indent=2))
