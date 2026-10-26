#!/usr/bin/env python3
"""Explicit upper-plane Hall prototype; original strict projection unchanged."""
import argparse,copy,hashlib,importlib.util,json,struct
from fractions import Fraction
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('hall_strict_source',HERE.parent/'hall-origin-footprint/build.py')
old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
existing=old.existing
STRICT=HERE.parent/'hall-origin-footprint'
def extract(inputs):
    inputs=Path(inputs);pins=json.loads((STRICT/'source-pins.json').read_text())
    strict=existing.extract(inputs);b=existing.m.b;proof=[]
    for xx,yy,land in [(0,0,576),(1,0,577),(0,1,578),(1,1,579)]:
        pin=pins['files']['MAP_%d'%land];raw=(inputs/pin['private_input_name']).read_bytes()
        if existing.base.sha(raw)!=pin['sha256'] or hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=pin['git_blob']:raise ValueError('source identity differs')
        sizes=struct.unpack_from('<4I',raw);data=b.decode(raw[16+sum(sizes[:3]):])
        for i,(word,) in enumerate(struct.iter_unpack('<H',raw[16:2064])):
            if word&0x8000:continue
            x,y=i%32,i//32;values=sorted({v for _,v in b.tile_candidates(data,x,y)})
            if len(values)!=2:continue
            corners=[]
            for dx,dz in ((-8,-8),(-8,8),(8,-8),(8,8)):
                corners.append(sorted({str(v/b.FX) for _,v in b.candidates(data,(x-16)*b.TILE+b.TILE//2+dx*b.FX,(y-16)*b.TILE+b.TILE//2+dz*b.FX)}))
            proof.append(dict(tile=[xx*32+x,yy*32+y],center_heights=[str(v/b.FX) for v in values],corner_heights=corners,upper_height='256',permission=word&255))
    return strict,proof
def upper_geometry(strict,proof):
    expected={(x,y) for y in range(25,32) for x in range(28,35)}
    if len(proof)!=49 or {tuple(p['tile']) for p in proof}!=expected:raise ValueError('exact supported upper footprint required')
    result=copy.deepcopy(strict)
    for p in proof:
        if p['center_heights']!=['48','256'] or p['upper_height']!='256' or p['permission']!=0 or len(p['corner_heights'])!=4 or not all('256' in c for c in p['corner_heights']):raise ValueError('upper plane must cover every corner')
        result['Hall']['surfaces'].append(dict(tile=p['tile'],permission=0,height='256',flat=True))
    # The whole lower arena boundary meets an already unique256-unit landing.
    for x in range(28,35):
        if not any(p==dict(tile=[x,32],permission=0,height='256',flat=True) for p in strict['Hall']['surfaces']):raise ValueError('authentic upper landing adjacency differs')
    result['Hall']['rejected_permission_clear']={}
    return result
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(existing.base.git(engine,'rev-parse','--show-toplevel').decode().strip());pins={}
    def read(p):
        raw=existing.base.verified_file(repo,p.relative_to(repo),'HEAD');pins[str(p.relative_to(repo))]=existing.base.sha(raw);return raw
    strict=json.loads(read(STRICT/'geometry.json'));proof=json.loads(read(HERE/'upper-plane-proof.json'))
    geometry=json.loads(read(HERE/'geometry.json'))
    if upper_geometry(strict,proof)!=geometry:raise ValueError('derived upper geometry differs')
    read(STRICT/'source-pins.json')
    old_here=existing.HERE
    try:
        existing.HERE=HERE
        receipt=old.build(engine,out)
    finally:existing.HERE=old_here
    spec=importlib.util.spec_from_file_location('hall_path_reuse',HERE.parent/'frontier-gate-link/build.py')
    gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
    family=out/'native-family';pa=(family/'primary-attributes.bin').read_bytes();sa=(family/'secondary-attributes.bin').read_bytes()
    raw=(out/'staged/Hall/map.bin').read_bytes()
    attrs={str(v&1023):existing.packer.attribute((pa,sa)[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',raw)}
    path=gate.a.static_path(raw,64,64,[31,52],[31,25],attrs)
    if not path:raise ValueError('bounded upper ramp path disconnected')
    receipt.update(status='EXPLICIT_UPPER_PLANE_HALL_PROTOTYPE_NOT_DUAL_PLANE_OR_RUNTIME_ACCEPTANCE',projection_input_sha256=pins,
        upper_selected_cells=49,lower_plane_not_represented='48',upper_plane='256',static_entry_to_platform_path=path,
        limits=['49 centers have actual overlapping48/256 planes; all four corners support256',
                'Select explicit upper256 plane contiguous with existing unique256 landing, not generic highest-plane fallback',
                'Lower48 plane under this platform intentionally not represented by this one-layer GBA projection',
                'Original strict106-cell prototype unchanged; no DS camera/dual-plane/script parity claimed',
                'Original source exit remains sealed; no flute/legendary/story/IDs/registry/ROM/native/mGBA/Save acceptance'])
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+chr(10));return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--private-inputs',type=Path);a=p.parse_args()
    if a.private_inputs:
        strict,proof=extract(a.private_inputs)
        (HERE/'upper-plane-proof.json').write_text(json.dumps(proof,indent=2)+chr(10))
        (HERE/'geometry.json').write_text(json.dumps(upper_geometry(strict,proof),indent=2)+chr(10))
    else:print(json.dumps(build(a.engine,a.out),indent=2))
