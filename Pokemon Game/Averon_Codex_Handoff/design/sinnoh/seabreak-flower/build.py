#!/usr/bin/env python3
"""Authentic Flower/Seabreak physical segments within the existing map buffer."""
import argparse,importlib.util,json,struct,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('seabreak_existing_projection',HERE.parent/'frontier-campus/build_source.py')
existing=importlib.util.module_from_spec(s);s.loader.exec_module(existing)
existing.HERE=HERE
existing.DIMS={'FlowerParadise':(32,32),'SeabreakNorth':(32,128),'SeabreakSouth':(32,128)}
existing.OPEN_BOUNDARIES={'FlowerParadise':{'down'},'SeabreakNorth':{'up','down'},'SeabreakSouth':{'up'}}
ROOT=HERE.parents[4];BASE_WORLD='stark-world-matrix-000-PRIVATE.json'
SLICES={'FlowerParadise':(6,7),'SeabreakNorth':(7,11),'SeabreakSouth':(11,15)}
def matrix_slice(world,name):
    start,end=SLICES[name];expected='MAP_HEADER_FLOWER_PARADISE' if name=='FlowerParadise' else 'MAP_HEADER_SEABREAK_PATH'
    if any(world['headers'][y][28]!=expected for y in range(start,end)):raise ValueError('authentic world identity differs')
    return (json.dumps(dict(name='derived_'+name,headers=[],altitudes=[],maps=[[world['maps'][y][28]] for y in range(start,end)]),indent=2)+'\n').encode()
def extract(inputs):
    inputs=Path(inputs);pins=json.loads((HERE/'source-pins.json').read_text());raw=(inputs/BASE_WORLD).read_bytes()
    if existing.base.sha(raw)!=pins['world_reference']['sha256']:raise ValueError('world source differs')
    world=json.loads(raw)
    for name,pin in pins['files'].items():
        if name in SLICES and (inputs/pin['private_input_name']).read_bytes()!=matrix_slice(world,name):raise ValueError('derived source matrix differs')
    return existing.extract(inputs)
def construct(geometry):
    # Use only real ground for the shared ordinal-land projection. Water
    # is restored separately as actual native ocean, never ordinary floor.
    for name,g in geometry.items():
        seen=set();w,h=existing.DIMS[name]
        for p in g['surfaces']:
            xy=tuple(p['tile'])
            if len(xy)!=2 or xy in seen or not (0<=xy[0]<w and 0<=xy[1]<h) or p['permission'] not in (0,0x15):
                raise ValueError('invalid or duplicate supported source surface')
            seen.add(xy)
    ground={n:dict(g,surfaces=[p for p in g['surfaces'] if p['permission']==0]) for n,g in geometry.items()}
    result=existing.construct(ground);audit={}
    for name,(raw,h,facts) in result.items():
        w,height=existing.DIMS[name];cells=list(struct.unpack('<%dH'%(w*height),raw));points={tuple(p['tile']):p for p in geometry[name]['surfaces']}
        for (x,y),p in points.items():
            if p['permission']==0x15:
                # Keep exterior sides and unbuilt southern join safely closed.
                edge=(x in (0,w-1)) or (y==0 and 'up' not in existing.OPEN_BOUNDARIES[name]) or (y==height-1 and 'down' not in existing.OPEN_BOUNDARIES[name])
                cells[y*w+x]=0x1000|368|(0xc00 if edge else 0)
            elif p['permission']==0:
                v=cells[y*w+x]
                if not v&0xc00:
                    cells[y*w+x]=(v&0xfc00)|(4 if name=='FlowerParadise' and not(14<=x<=16) else 265)
        # Unsupported/permission-blocked land stays visibly bounded grass.
        for i,v in enumerate(cells):
            if v&0xc00 and ((i%w,i//w) not in points or (v&1023)>=512):cells[i]=(v&0xfc00)|1
        h.update(id='MAP_SINNOH_'+('FLOWER_PARADISE' if name=='FlowerParadise' else 'SEABREAK_NORTH' if name=='SeabreakNorth' else 'SEABREAK_SOUTH'),
                 name='Sinnoh'+name,layout='LAYOUT_SINNOH_'+name.upper(),map_type='MAP_TYPE_ROUTE',allow_cycling=True)
        h['connections']=[]
        audit[name]=dict(source_supported=len(points),source_ground=sum(p['permission']==0 for p in points.values()),source_sea=sum(p['permission']==0x15 for p in points.values()))
        result[name]=(struct.pack('<%dH'%(w*height),*cells),h)
    headers={n:v[1] for n,v in result.items()}
    for north,south in [('FlowerParadise','SeabreakNorth'),('SeabreakNorth','SeabreakSouth')]:
        headers[north]['connections'].append(dict(map=headers[south]['id'],direction='down',offset=0))
        headers[south]['connections'].append(dict(map=headers[north]['id'],direction='up',offset=0))
    return result,audit
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(existing.base.git(engine,'rev-parse','--show-toplevel').decode().strip());pins={}
    def read(path):
        raw=existing.base.verified_file(repo,path.relative_to(repo),'HEAD');pins[str(path.relative_to(repo))]=existing.base.sha(raw);return raw
    geometry=json.loads(read(HERE/'geometry.json'));result,audit=construct(geometry)
    spec=importlib.util.spec_from_file_location('existing_readiness',ROOT/'Pokemon Game/scripts/audit-averon-map-readiness.py')
    readiness=importlib.util.module_from_spec(spec);spec.loader.exec_module(readiness)
    limits=readiness.source_limits(read(engine/'include/fieldmap.h').decode(),read(engine/'include/global.fieldmap.h').decode())
    capacity={}
    for name,(w,h) in existing.DIMS.items():
        padded=(w+limits['pad_w'])*(h+limits['pad_h'])
        if padded>limits['cells']:raise ValueError('native padded-map capacity exceeded')
        capacity[name]=padded
    prefixes=['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/']
    primary=read(engine/prefixes[0]/'metatiles.bin');pa=read(engine/prefixes[0]/'metatile_attributes.bin');source_attrs=[bytearray(pa),bytearray(1024)]
    for mid in (1,4,265):struct.pack_into('<H',source_attrs[0],2*mid,0x1000)
    if existing.packer.attribute(pa,368)!=0x1015:raise ValueError('native ocean semantics differ')
    sec=sa=b'';packets={}
    for name,(raw,h) in result.items():
        border=struct.pack('<4H',*[0x1c00|368]*4);desired=[existing.packer.words(primary,v&1023) for (v,) in struct.iter_unpack('<H',raw+border)]
        data,sec,sa=existing.packer.pack_art(raw+border,desired,source_attrs,primary,pa,sec,sa)
        packets[name]=(data[:len(raw)],data[len(raw):],h)
    images=[existing.dual.indexed(read(engine/p/'tiles.png')) for p in prefixes];previews={};attrs={}
    for name,(raw,border,h) in packets.items():
        deps=existing.dual.closure(raw,[primary,sec],images);palettes={i:existing.base.palette(read(engine/prefixes[i>=6]/('palettes/%02d.pal'%i))) for i in deps['palettes']}
        previews[name]=existing.dual.render(raw,[primary,sec],images,palettes,*existing.DIMS[name])
        attrs[name]={str(v&1023):existing.packer.attribute((pa,sa)[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',raw+border)}
    seams=[]
    for north,south in [('FlowerParadise','SeabreakNorth'),('SeabreakNorth','SeabreakSouth')]:
        nw,nh=existing.DIMS[north];sw,sh=existing.DIMS[south]
        a=struct.unpack('<%dH'%(nw*nh),packets[north][0]);b=struct.unpack('<%dH'%(sw*sh),packets[south][0]);lanes=[]
        for x in range(32):
            first,second=a[(nh-1)*nw+x],b[x]
            if first&0xc00 or second&0xc00:continue
            if attrs[north][str(first&1023)]&255 or attrs[south][str(second&1023)]&255:continue
            z,zz=first>>12,second>>12
            if z and zz and z!=zz:raise ValueError('ground seam elevation differs')
            lanes.append(x)
        if lanes!=[14,15,16]:raise ValueError('authentic ground seam differs')
        seams.append(dict(north=north,south=south,ground_lanes=lanes))
    out.mkdir(parents=True);family=out/'native-family';family.mkdir()
    for n,v in [('primary-metatiles',primary),('primary-attributes',pa),('secondary-metatiles',sec),('secondary-attributes',sa)]:(family/(n+'.bin')).write_bytes(v)
    for name,(raw,border,h) in packets.items():
        p=out/'staged'/name;p.mkdir(parents=True);(p/'map.bin').write_bytes(raw);(p/'border.bin').write_bytes(border);(p/'map.json').write_text(json.dumps(h,indent=2)+'\n');(p/'attributes.json').write_text(json.dumps(attrs[name],indent=2)+'\n');previews[name].save(p/'preview.png')
    receipt=dict(status='SOURCE_FLOWER_SEABREAK_SEGMENTS_NOT_STORY_OR_RUNTIME_ACCEPTANCE',source_sha256=pins,source_geometry=audit,
        buffer_capacity=limits['cells'],padded_cells=capacity,unsplit_padded_cells=(32+limits['pad_w'])*(256+limits['pad_h']),seams=seams,
        limits=['Split authentic256-row road into128-row segments for existing fixed buffer, no engine change',
                'Sea0x15 mapped explicitly to native0x1015 ocean/Surf semantics; not ordinary ground',
                'Source south Route224 entrance closed until coherent authorized physical/story integration',
                'Existing native flower/pale-road art only, no DS textures/props/story/encounters or Shaymin',
                'No permanent IDs/registry/save changes or ROM/native/mGBA/Save acceptance'])
    receipt['output_sha256']={str(p.relative_to(out)):existing.base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--private-inputs',type=Path);a=p.parse_args()
    if a.private_inputs and extract(a.private_inputs)!=json.loads((HERE/'geometry.json').read_text()):raise ValueError('source extraction differs')
    print(json.dumps(build(a.engine,a.out),indent=2))
