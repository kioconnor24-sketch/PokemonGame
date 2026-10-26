#!/usr/bin/env python3
"""Bounded authentic Underground corridor sector; no multiplayer/game systems."""
import argparse,importlib.util,json,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('underground_existing_projection',HERE.parent/'frontier-campus/build_source.py')
existing=importlib.util.module_from_spec(s);s.loader.exec_module(existing)
existing.HERE=HERE;existing.DIMS={n:(64,64) for n in ('NW','NE','SW','SE')}
existing.SOURCE_BEHAVIORS=existing.SOURCE_BEHAVIORS+(12,)
existing.OPEN_BOUNDARIES={'NW':{'right','down'},'NE':{'left','down'},'SW':{'right','up'},'SE':{'left','up'}}
SLICES={'NW':(6,3),'NE':(8,3),'SW':(6,5),'SE':(8,5)}
LINKS=[('NW','NE','right','left'),('SW','SE','right','left'),('NW','SW','down','up'),('NE','SE','down','up')]
def matrix_slice(world,name):
    x,y=SLICES[name]
    return (json.dumps(dict(name='derived_underground_'+name,headers=[],altitudes=[],maps=[row[x:x+2] for row in world['maps'][y:y+2]]),indent=2)+chr(10)).encode()
def extract(inputs):
    inputs=Path(inputs);pins=json.loads((HERE/'source-pins.json').read_text())
    raw=(inputs/'underground-matrix-002-PRIVATE.json').read_bytes()
    if existing.base.sha(raw)!=pins['world_reference']['sha256']:raise ValueError('original matrix differs')
    world=json.loads(raw)
    for n in SLICES:
        if (inputs/pins['files'][n]['private_input_name']).read_bytes()!=matrix_slice(world,n):raise ValueError('derived source slice differs')
    return existing.extract(inputs)
base_construct=existing.construct
def construct(geometry):
    if any(p['permission']!=12 or not p['flat'] for g in geometry.values() for p in g['surfaces']):raise ValueError('ordinary source corridor floor required')
    adjusted={n:dict(g,surfaces=[dict(p,permission=0) for p in g['surfaces']]) for n,g in geometry.items()}
    result=base_construct(adjusted)
    for n,(raw,h,audit) in result.items():
        h.update(id='MAP_SINNOH_UNDERGROUND_SECTOR_'+n,name='SinnohUndergroundSector'+n,layout='LAYOUT_SINNOH_UNDERGROUND_SECTOR_'+n,
            map_type='MAP_TYPE_UNDERGROUND',music='MUS_GRANITE_CAVE',connections=[])
    for a,b,forward,back in LINKS:
        result[a][1]['connections'].append(dict(map=result[b][1]['id'],direction=forward,offset=0))
        result[b][1]['connections'].append(dict(map=result[a][1]['id'],direction=back,offset=0))
    return result
existing.construct=construct
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(existing.base.git(engine,'rev-parse','--show-toplevel').decode().strip())
    pins=existing.base.verified_file(repo,(HERE/'source-pins.json').relative_to(repo),'HEAD')
    spec=importlib.util.spec_from_file_location('underground_native_limits',HERE.parents[4]/'Pokemon Game/scripts/audit-averon-map-readiness.py')
    capacity=importlib.util.module_from_spec(spec);spec.loader.exec_module(capacity)
    limits=capacity.source_limits(existing.base.verified_file(repo,(engine/'include/fieldmap.h').relative_to(repo),'HEAD').decode(),
        existing.base.verified_file(repo,(engine/'include/global.fieldmap.h').relative_to(repo),'HEAD').decode())
    padded=(64+limits['pad_w'])*(64+limits['pad_h'])
    if padded>limits['cells']:raise ValueError('native sector capacity exceeded')
    receipt=existing.build(engine,out);seams=[]
    maps={n:struct.unpack('<4096H',(out/'staged'/n/'map.bin').read_bytes()) for n in SLICES}
    for a,b,d,_ in LINKS:
        lanes=[]
        for i in range(64):
            p,q=((63,i),(0,i)) if d=='right' else ((i,63),(i,0))
            v,w=maps[a][p[1]*64+p[0]],maps[b][q[1]*64+q[0]]
            if not(v&0xc00 or w&0xc00) and v>>12==w>>12:lanes.append(i)
        if len(lanes)!=20:raise ValueError('authentic corridor seam differs')
        seams.append(dict(source=a,target=b,direction=d,offset=0,lanes=lanes))
    receipt.update(status='BOUNDED_UNDERGROUND_CORRIDORS_NOT_FULL_UNDERGROUND_OR_RUNTIME_ACCEPTANCE',world_chunk_origin=[6,3],global_tile_origin=[192,96],
        source_pins_sha256=existing.base.sha(pins),padded_map_cells=padded,buffer_cells=limits['cells'],seams=seams,
        limits=['Authentic128x128 corridor sector split into four64x64 maps, not full480x480 world',
                'Source floor0x0C is ordinary mountain-floor walking, normalized to native normal floor without encounters',
                'No dynamic MAP649 secret-base slots, multiplayer/mining/traps/spheres/base mechanics or surface transport',
                'Outer sector cuts sealed; all internal source centers/corners/heights preserved',
                'Existing native Cave artwork only; no DS models/pixels/music/story/IDs/registry/schema',
                'No NORMAL/RELEASE/native-game-suite/mGBA/Save/Delta acceptance'])
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+chr(10));return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--private-inputs',type=Path);a=p.parse_args()
    if a.private_inputs:(HERE/'geometry.json').write_text(json.dumps(extract(a.private_inputs),indent=2)+chr(10))
    else:print(json.dumps(build(a.engine,a.out),indent=2))
