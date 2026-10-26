#!/usr/bin/env python3
"""Capacity-safe Frontier campus strips; no original terrain/art/engine changes."""
import argparse,importlib.util,io,json,struct
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('bounded_frontier_reuse',HERE.parent/'frontier-facilities/build.py')
reuse=importlib.util.module_from_spec(s);s.loader.exec_module(reuse)
m=reuse.m
PARTS=('CampusWest','CampusCenter','CampusEast')
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(m.base.git(engine,'rev-parse','--show-toplevel').decode().strip());pins={}
    def read(p):
        raw=m.base.verified_file(repo,p.relative_to(repo),'HEAD');pins[str(p.relative_to(repo))]=m.base.sha(raw);return raw
    source=HERE.parent/'frontier-gate-link';facilities=HERE.parent/'frontier-facilities'
    source_header=json.loads(read(source/'staged/Campus/map.json'));raw=read(source/'staged/Campus/map.bin')
    border=read(source/'staged/Campus/border.bin');attrs=read(source/'staged/Campus/attributes.json')
    art=Image.open(io.BytesIO(read(source/'staged/Campus/preview.png')));art.load()
    if len(raw)!=96*96*2 or art.size!=(1536,1536) or len(source_header['warp_events'])!=6:raise ValueError('source campus differs')
    root=HERE.parents[4];sp=importlib.util.spec_from_file_location('bounded_actual_limits',root/'Pokemon Game/scripts/audit-averon-map-readiness.py')
    limits_module=importlib.util.module_from_spec(sp);sp.loader.exec_module(limits_module)
    limits=limits_module.source_limits(read(engine/'include/fieldmap.h').decode(),read(engine/'include/global.fieldmap.h').decode())
    old_padded=(96+limits['pad_w'])*(96+limits['pad_h']);new_padded=(32+limits['pad_w'])*(96+limits['pad_h'])
    if old_padded<=limits['cells'] or new_padded>limits['cells']:raise ValueError('capacity premise differs')
    headers={};packets={};sizes={};mapping={}
    for col,name in enumerate(PARTS):
        data=b''.join(raw[(y*96+col*32)*2:(y*96+(col+1)*32)*2] for y in range(96))
        h=json.loads(json.dumps(source_header))
        h.update(id='MAP_SINNOH_FRONTIER_'+name.upper(),name='SinnohFrontier'+name,layout='LAYOUT_SINNOH_FRONTIER_'+name.upper(),warp_events=[],connections=[])
        if col:h['connections'].append(dict(map='MAP_SINNOH_FRONTIER_'+PARTS[col-1].upper(),direction='left',offset=0))
        if col<2:h['connections'].append(dict(map='MAP_SINNOH_FRONTIER_'+PARTS[col+1].upper(),direction='right',offset=0))
        for index,e in enumerate(source_header['warp_events']):
            if e['x']//32!=col:continue
            event=dict(e,x=e['x']-col*32)
            mapping[str(index)]=dict(map=h['id'],index=len(h['warp_events']),global_tile=[e['x'],e['y']],local_tile=[event['x'],event['y']])
            h['warp_events'].append(event)
        buf=io.BytesIO();art.crop((col*512,0,(col+1)*512,1536)).save(buf,format='PNG')
        headers[name]=h;packets[name]={'map.bin':data,'border.bin':border,'attributes.json':attrs,'preview.png':buf.getvalue()};sizes[name]=[32,96]
    def add_source(name,folder,preview='preview.png'):
        packets[name]={n:read(folder/n) for n in ('map.bin','border.bin','attributes.json')}
        packets[name]['preview.png']=read(folder/preview)
        headers[name]=json.loads(read(folder/'map.json'))
    add_source('Gate',source/'staged/Gate')
    add_source('FightArea',HERE.parent/'battle-zone-center-shells/staged/FightArea')
    sizes.update(Gate=[32,32],FightArea=[70,37])
    for name in reuse.TEMPLATES:
        add_source(name,facilities/'staged'/name)
        layout=json.loads(read(facilities/'staged'/name/'layout.json'))
        sizes[name]=[layout['width'],layout['height']]
        packets[name]['layout.json']=(json.dumps(layout,indent=2)+chr(10)).encode()
    changed=[]
    for name,h in headers.items():
        for index,e in enumerate(h['warp_events']):
            if e['dest_map']!=source_header['id']:continue
            old=dict(e);new=mapping[e['dest_warp_id']]
            e.update(dest_map=new['map'],dest_warp_id=str(new['index']))
            changed.append(dict(map=name,event=index,before=old,after=dict(e)))
    # The retained current town events require the existing town packet.
    external={'MAP_SINNOH_FIGHTAREA_CENTER_1F','MAP_SINNOH_FIGHTAREAHOUSE1','MAP_SINNOH_FIGHTAREAHOUSE2'}
    by_id={h['id']:h for h in headers.values()}
    for name,h in headers.items():
        for e in h['warp_events']:
            if e['dest_map'] in external:continue
            if e['dest_map'] not in by_id:raise ValueError('unresolved internal destination')
            other=by_id[e['dest_map']]
            if not 0<=int(e['dest_warp_id'])<len(other['warp_events']):raise ValueError('invalid remapped portal index')
    cells=struct.unpack('<9216H',raw);words=json.loads(attrs);seams=[]
    for col in (0,1):
        lanes=[]
        for y in range(96):
            a,b=cells[y*96+(col+1)*32-1],cells[y*96+(col+1)*32]
            if a&0xc00 or b&0xc00 or words[str(a&1023)]&255 or words[str(b&1023)]&255:continue
            if a>>12 and b>>12 and a>>12!=b>>12:continue
            lanes.append(y)
        if not lanes:raise ValueError('strip seam has no ordinary-ground crossing')
        seams.append(dict(west=PARTS[col],east=PARTS[col+1],offset=0,ordinary_ground_rows=lanes))
    capacity={n:(w+limits['pad_w'])*(h+limits['pad_h']) for n,(w,h) in sizes.items()}
    if any(v>limits['cells'] for v in capacity.values()):raise ValueError('derived packet exceeds native capacity')
    out.mkdir(parents=True)
    for name,data in packets.items():
        p=out/'staged'/name;p.mkdir(parents=True)
        for n,v in data.items():(p/n).write_bytes(v)
        (p/'map.json').write_text(json.dumps(headers[name],indent=2)+chr(10))
    receipt=dict(status='BOUNDED_FRONTIER_SOURCE_PACKET_NOT_RUNTIME_ACCEPTANCE',input_sha256=pins,
        original_padded_cells=old_padded,buffer_cells=limits['cells'],padded_cells=capacity,dimensions=sizes,
        original_campus_portal_mapping=mapping,remapped_return_events=changed,strip_seams=seams,
        family_dependencies={'campus':str((source/'families/Campus').relative_to(repo)),'gate':str((source/'families/Gate').relative_to(repo)),'fight':str((source/'families/FightArea').relative_to(repo)),'facilities':'original frontier-facilities/layout.json native dependencies'},
        limits=['Three exact32x96 source strips replace oversized96x96 proposal; global terrain/C/E/art unchanged',
                'This is an alternative bounded campus proposal, not duplicate registration of old96x96 header',
                'Existing facility/gate IDs retained, six campus portals and returns mechanically remapped',
                'Current Fight Area center/house external events require #295; regional source dependencies retained',
                'No engine buffer expansion, permanent savedIDs/registry/schema/story or ROM/native/mGBA/Save acceptance'])
    receipt['output_sha256']={str(p.relative_to(out)):m.base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+chr(10));return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(build(a.engine,a.out),indent=2))
