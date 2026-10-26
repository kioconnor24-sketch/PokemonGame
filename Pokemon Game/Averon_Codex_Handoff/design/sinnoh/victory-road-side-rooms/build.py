#!/usr/bin/env python3
"""Source-backed Victory Road side rooms, native cave art; no story."""
import argparse,importlib.util,json,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('victory_side_projection',HERE.parent/'frontier-campus/build_source.py')
existing=importlib.util.module_from_spec(s);s.loader.exec_module(existing)
existing.HERE=HERE;existing.DIMS={'Room1':(32,32),'Room2':(64,64),'Room3':(32,32)}
# Actual source door codes; defaults remain unchanged for other callers.
existing.SOURCE_BEHAVIORS=existing.SOURCE_BEHAVIORS+(8,0x6f,0x70)
original_construct=existing.construct
def construct(geometry):
    adjusted={}
    for n,g in geometry.items():
        adjusted[n]=dict(g,surfaces=[dict(p,permission=0 if p['permission']==8 else p['permission']) for p in g['surfaces']])
    result=original_construct(adjusted)
    pins=json.loads((HERE/'source-pins.json').read_text())
    from fractions import Fraction
    for n,(raw,h,audit) in result.items():
        w,height=existing.DIMS[n];cells=list(struct.unpack('<%dH'%(w*height),raw))
        levels=sorted({Fraction(p['height']) for p in geometry[n]['surfaces'] if p['flat']})
        zmap={v:i+3 for i,v in enumerate(levels)}
        for p in geometry[n]['surfaces']:
            x,y=p['tile']
            if p['permission']==0x15:
                cells[y*w+x]=0x1000|368
        h.update(id='MAP_SINNOH_VICTORY_SIDE_'+n.upper(),name='SinnohVictorySide'+n,layout='LAYOUT_SINNOH_VICTORY_SIDE_'+n.upper(),map_type='MAP_TYPE_UNDERGROUND',music='MUS_GRANITE_CAVE')
        for i,e in enumerate(pins['technical_portals'][n]['warps']):
            if n=='Room3' and i==1:continue # Route224 outside this bounded group
            x,y=e['x'],e['z']
            p=next((p for p in geometry[n]['surfaces'] if p['tile']==[x,y]),None)
            if not p or not p['flat'] or p['permission'] not in (0x6c,0x6d):raise ValueError('unsupported source portal')
            z=zmap[Fraction(p['height'])];cells[y*w+x]=z<<12|517
            target=e['dest_header_id'].removeprefix('MAP_HEADER_VICTORY_ROAD_1F_ROOM_')
            dest='MAP_SINNOH_VICTORY_SIDE_ROOM'+target if target.isdigit() else 'MAP_SINNOH_VICTORY_ROAD_1F'
            h['warp_events'].append(dict(x=x,y=y,elevation=z,dest_map=dest,dest_warp_id=str(e['dest_warp_id']) if target.isdigit() else '8'))
        result[n]=(struct.pack('<%dH'%(w*height),*cells),h,audit)
    return result
existing.construct=construct
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    # Existing generator performs all output-safety, source and asset checks.
    result=existing.build(engine,out)
    core=HERE.parent/'victory-road-shell/connected/SinnohVictoryRoad_1F'
    repo=Path(existing.base.git(engine,'rev-parse','--show-toplevel').decode().strip())
    def read(p):return existing.base.verified_file(repo,p.relative_to(repo),'HEAD')
    raw=bytearray(read(core/'map.bin'));h=json.loads(read(core/'map.json'));border=read(core/'border.bin')
    if len(h['warp_events'])!=8:raise ValueError('core prefix differs')
    before=struct.unpack_from('<H',raw,2*(33*52+45))[0]
    if before!=0xe09:raise ValueError('core side door differs')
    struct.pack_into('<H',raw,2*(33*52+45),0x3000|517)
    h['warp_events'].append(dict(x=45,y=33,elevation=3,dest_map='MAP_SINNOH_VICTORY_SIDE_ROOM1',dest_warp_id='0'))
    p=out/'staged/Core1F';p.mkdir()
    for name,data in [('map.bin',raw),('border.bin',border),('map.json',(json.dumps(h,indent=2)+'\n').encode())]:(p/name).write_bytes(data)
    # Side-room family is distinct from the immutable stock Cave core family.
    fam=out/'native-family';pa=(fam/'primary-attributes.bin').read_bytes();sa=(fam/'secondary-attributes.bin').read_bytes()
    for n in existing.DIMS:
        p=out/'staged'/n;data=(p/'map.bin').read_bytes()
        attrs={str(v&1023):existing.packer.attribute((pa,sa)[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',data)}
        (p/'attributes.json').write_text(json.dumps(attrs,indent=2)+'\n')
    result.update(status='SOURCE_VICTORY_SIDE_ROOMS_NOT_SURF_OR_RUNTIME_ACCEPTANCE',core_single_cell_change=dict(tile=[45,33],before=before,after=0x3000|517),
        limits=['Three actual source rooms with native cave/step proxies, not full DS 3D puzzle parity',
                'Room2 actual sea0x15 remains native ocean0x1015 and requires Surf; no capability grant',
                'Room3 Route224 exit sealed; existing core eight event prefix retained',
                'Separate side-room and stock core art families required; no production registry or saved IDs',
                'No DS art, NPC, boulder, Defog, encounter/story or ROM/native/mGBA/Save acceptance'])
    result['output_sha256']={str(p.relative_to(out)):existing.base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file() and p.name!='receipt.json'}
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--private-inputs',type=Path);a=p.parse_args()
    if a.private_inputs:
        geometry=existing.extract(a.private_inputs)
        (HERE/'geometry.json').write_text(json.dumps(geometry,indent=2)+'\n')
    else:print(json.dumps(build(a.engine,a.out),indent=2))
