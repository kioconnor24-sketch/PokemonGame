#!/usr/bin/env python3
"""Reuse Route224 geometry with isolated native art and Room3 return."""
import argparse,importlib.util,json,struct
from pathlib import Path
from fractions import Fraction
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('route224_existing_art',HERE.parent/'frontier-campus/build_source.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
SECONDARY={686:4,687:4,646:4,647:4,638:4,639:4,680:368,630:4,645:4,684:368,682:368,685:368}
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(m.base.git(engine,'rev-parse','--show-toplevel').decode().strip());pins={}
    def read(p):
        raw=m.base.verified_file(repo,p.relative_to(repo),'HEAD');pins[str(p.relative_to(repo))]=m.base.sha(raw);return raw
    original=HERE.parent/'remaining-donor/staged/Route224'
    raw=read(original/'map.bin');border=read(original/'border.bin');header=json.loads(read(original/'map.json'))
    attrs=json.loads(read(original/'attributes.json'))['used_source_attribute_words']
    if len(raw)!=64*94*2 or header['warp_events']:raise ValueError('immutable source identity differs')
    used={v&1023 for (v,) in struct.iter_unpack('<H',raw+border)}
    if used!={int(v) for v in attrs} or {v for v in used if v>=512}!=set(SECONDARY):raise ValueError('unreviewed metatile dependency')
    prefixes=['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/']
    primary=read(engine/prefixes[0]/'metatiles.bin');pa=read(engine/prefixes[0]/'metatile_attributes.bin')
    source_attrs=[bytearray(1024),bytearray(1024)]
    for mid,value in attrs.items():struct.pack_into('<H',source_attrs[int(mid)//512],2*(int(mid)%512),value)
    wanted=[m.packer.words(primary,SECONDARY.get(v&1023,v&1023)) for (v,) in struct.iter_unpack('<H',raw+border)]
    packed,sec,sa=m.packer.pack_art(raw+border,wanted,source_attrs,primary,pa,b'',b'')
    for (old,),(new,) in zip(struct.iter_unpack('<H',raw+border),struct.iter_unpack('<H',packed)):
        if old&0xfc00!=new&0xfc00 or m.packer.attribute((pa,sa)[(new&1023)//512],new%512)!=attrs[str(old&1023)]:raise ValueError('source physics or full attribute differs')
    cells=bytearray(packed[:len(raw)]);closures=[]
    # Direct League shortcut and story bridge are outside this bounded source packet.
    for x,y in sorted({(0,y) for y in range(94)}|{(x,0) for x in range(64)}):
        off=2*(y*64+x);v=struct.unpack_from('<H',cells,off)[0]
        if not v&0xc00:
            struct.pack_into('<H',cells,off,v|0xc00);closures.append(dict(tile=[x,y],before=v,after=v|0xc00))
    x,y=11,70;door=struct.unpack_from('<H',cells,2*(y*64+x))[0]
    if door&0xc00 or m.packer.attribute((pa,sa)[(door&1023)//512],door%512)&255!=0x60:raise ValueError('native source cave anchor differs')
    if struct.unpack_from('<H',cells,2*((y+1)*64+x))[0]&0xc00:raise ValueError('route door approach blocked')
    side=HERE.parent/'victory-road-side-rooms'
    room=bytearray(read(side/'staged/Room3/map.bin'));room_border=read(side/'staged/Room3/border.bin')
    rh=json.loads(read(side/'staged/Room3/map.json'))
    geometry=json.loads(read(side/'geometry.json'))['Room3']['surfaces']
    e=json.loads(read(side/'source-pins.json'))['technical_portals']['Room3']['warps'][1]
    if e!=dict(x=29,z=16,dest_header_id='MAP_HEADER_ROUTE_224',dest_warp_id=0) or len(rh['warp_events'])!=1:raise ValueError('source room exit differs')
    p=next(p for p in geometry if p['tile']==[29,16])
    levels=sorted({Fraction(p['height']) for p in geometry if p['flat']});z=levels.index(Fraction(p['height']))+3
    source_event=rh['warp_events'][0];trigger=struct.unpack_from('<H',room,2*(source_event['y']*32+source_event['x']))[0]&1023
    off=2*(16*32+29);old=struct.unpack_from('<H',room,off)[0]
    if not old&0xc00:raise ValueError('room original exit already open')
    struct.pack_into('<H',room,off,z<<12|trigger)
    rh['warp_events'].append(dict(x=29,y=16,elevation=z,dest_map=header['id'],dest_warp_id='0'))
    header.update(connections=[],warp_events=[dict(x=11,y=70,elevation=0,dest_map=rh['id'],dest_warp_id='1')])
    images=[m.dual.indexed(read(engine/q/'tiles.png')) for q in prefixes]
    deps=m.dual.closure(cells,[primary,sec],images)
    palettes={i:m.base.palette(read(engine/prefixes[i>=6]/('palettes/%02d.pal'%i))) for i in deps['palettes']}
    preview=m.dual.render(cells,[primary,sec],images,palettes,64,94)
    # Preserve the separate Room3 bank and original presentation inputs.
    family={n:read(side/'native-family'/n) for n in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin')}
    room_images=[images[0],m.dual.indexed(read(engine/'data/tilesets/secondary/cave/tiles.png'))]
    room_banks=[family['primary-metatiles.bin'],family['secondary-metatiles.bin']]
    room_deps=m.dual.closure(room,room_banks,room_images)
    room_palettes={i:m.base.palette(read(engine/('data/tilesets/primary/general/' if i<6 else 'data/tilesets/secondary/cave/')/('palettes/%02d.pal'%i))) for i in room_deps['palettes']}
    room_preview=m.dual.render(room,room_banks,room_images,room_palettes,32,32)
    out.mkdir(parents=True);bank=out/'route-family';bank.mkdir()
    for n,v in [('primary-metatiles.bin',primary),('primary-attributes.bin',pa),('secondary-metatiles.bin',sec),('secondary-attributes.bin',sa)]:(bank/n).write_bytes(v)
    rp=out/'staged/Route224';rp.mkdir(parents=True)
    route_attrs={str(v&1023):m.packer.attribute((pa,sa)[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',cells+packed[len(raw):])}
    room_attrs={str(v&1023):m.packer.attribute((family['primary-attributes.bin'],family['secondary-attributes.bin'])[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',room+room_border)}
    for name,data,bd,h,a in [('Route224',cells,packed[len(raw):],header,route_attrs),('Room3',room,room_border,rh,room_attrs)]:
        q=out/'staged'/name;q.mkdir(parents=True,exist_ok=True)
        for n,v in [('map.bin',data),('border.bin',bd),('map.json',(json.dumps(h,indent=2)+chr(10)).encode()),('attributes.json',(json.dumps(a,indent=2)+chr(10)).encode())]:(q/n).write_bytes(v)
    preview.save(rp/'preview.png');room_preview.save(out/'staged/Room3/preview.png')
    receipt=dict(status='SOURCE_ROUTE224_CAVE_RETURN_NOT_STORY_OR_RUNTIME_ACCEPTANCE',input_sha256=pins,secondary_art_remap={str(k):v for k,v in SECONDARY.items()},
       route_boundary_closures=closures,room_one_change=dict(tile=[29,16],before=old,after=z<<12|trigger),
       buffer_padded_cells=(64+15)*(94+14),secondary_records=len(sec)//16,
       limits=['Original donor technical map reused, native General art with secondary native flowers/ocean adaptation',
               'Full original attributes/layers and C/E preserved except explicit north/left collision closures and one room door',
               'Existing direct League connection removed; Seabreak/story path north closed',
               'Separate original Room3 bank required; no DS pixels, IDs, encounters/story or save changes',
               'No ROM/native/mGBA/Save/animated water or natural Surf acceptance'])
    receipt['output_sha256']={str(p.relative_to(out)):m.base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+chr(10));return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    print(json.dumps(build(a.engine,a.out),indent=2))
