#!/usr/bin/env python3
"""Native neutral League center shells, existing exterior art/physics unchanged."""
import argparse,importlib.util,json,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('league_native_templates',HERE.parent/'frontier-facilities/build.py')
reuse=importlib.util.module_from_spec(s);s.loader.exec_module(reuse)
m=reuse.m
PORTS={'South':(11,58),'North':(16,13)}
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(m.base.git(engine,'rev-parse','--show-toplevel').decode().strip());pins={}
    def read(p):
        raw=m.base.verified_file(repo,p.relative_to(repo),'HEAD');pins[str(p.relative_to(repo))]=m.base.sha(raw);return raw
    def eng(p):return read(engine/p)
    layouts={v['id']:v for v in json.loads(eng('data/layouts/layouts.json'))['layouts']}
    core=HERE.parent/'victory-road-shell/connected/PokmonLeague'
    outdoor={n:read(core/n) for n in ('map.bin','border.bin','map.json','attributes.json','averon.png')}
    exterior=json.loads(outdoor['map.json'])
    if len(exterior['warp_events'])!=2:raise ValueError('existing exterior event prefix differs')
    attrs=json.loads(outdoor['attributes.json'])['used_source_attribute_words']
    packets={};closures=[]
    for side,(x,y) in PORTS.items():
        v=struct.unpack_from('<H',outdoor['map.bin'],2*(y*33+x))[0]
        if attrs[str(v&1023)]&255!=0x69:raise ValueError('existing animated-door anchor differs')
        below=struct.unpack_from('<H',outdoor['map.bin'],2*((y+1)*33+x))[0]
        if below&0xc00:raise ValueError('existing doorstep blocked')
        exterior_index=len(exterior['warp_events'])
        exterior['warp_events'].append(dict(x=x,y=y,elevation=0,dest_map='MAP_SINNOH_LEAGUE_'+side.upper()+'_1F',dest_warp_id='0'))
        for floor in (1,2):
            name=side+str(floor);original=json.loads(eng('data/maps/PetalburgCity_PokemonCenter_%dF/map.json'%floor))
            layout=layouts[original['layout']];w,h=layout['width'],layout['height']
            raw=bytearray(eng(layout['blockdata_filepath']));border=eng(layout['border_filepath'])
            header=dict(original);header.update(id='MAP_SINNOH_LEAGUE_'+side.upper()+'_'+str(floor)+'F',name='SinnohLeague'+name,
                layout='LAYOUT_SINNOH_LEAGUE_'+name.upper(),region='REGION_SINNOH',region_map_section='MAPSEC_PENDING_OWNER',
                connections=[],object_events=[],coord_events=[],bg_events=[])
            events=[]
            for i,source in enumerate(original['warp_events']):
                e=dict(source)
                if floor==1:
                    if i<2:e.update(dest_map=exterior['id'],dest_warp_id=str(exterior_index))
                    else:e.update(dest_map='MAP_SINNOH_LEAGUE_'+side.upper()+'_2F',dest_warp_id='0')
                    events.append(e)
                elif i==0:
                    e.update(dest_map='MAP_SINNOH_LEAGUE_'+side.upper()+'_1F',dest_warp_id='2');events.append(e)
                else:
                    off=2*(e['y']*w+e['x']);v=struct.unpack_from('<H',raw,off)[0]
                    struct.pack_into('<H',raw,off,v|0xc00);closures.append(dict(map=name,tile=[e['x'],e['y']],before=v,after=v|0xc00,reason='online/link room absent'))
            header['warp_events']=events
            prefixes=['data/tilesets/primary/'+reuse.folder(layout['primary_tileset'])+'/',
                      'data/tilesets/secondary/'+reuse.folder(layout['secondary_tileset'])+'/']
            banks=[eng(q+'metatiles.bin') for q in prefixes];attribute_banks=[eng(q+'metatile_attributes.bin') for q in prefixes]
            images=[m.dual.indexed(eng(q+'tiles.png')) for q in prefixes]
            deps=m.dual.closure(raw,banks,images)
            palettes={i:m.base.palette(eng(prefixes[i>=6]+'palettes/%02d.pal'%i)) for i in deps['palettes']}
            preview=m.dual.render(raw,banks,images,palettes,w,h)
            used={str(v&1023):m.packer.attribute(attribute_banks[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',raw+border)}
            layout=dict(layout);layout.update(id=header['layout'],name=header['name']+'_Layout',blockdata_filepath='staged/'+name+'/map.bin',border_filepath='staged/'+name+'/border.bin')
            packets[name]=(raw,border,header,layout,used,preview)
    # Only after validated source/assets and complete rendering create outputs.
    out.mkdir(parents=True)
    for name,(raw,border,h,l,words,preview) in packets.items():
        p=out/'staged'/name;p.mkdir(parents=True)
        for filename,data in [('map.bin',raw),('border.bin',border),('map.json',(json.dumps(h,indent=2)+chr(10)).encode()),('layout.json',(json.dumps(l,indent=2)+chr(10)).encode()),('attributes.json',(json.dumps(words,indent=2)+chr(10)).encode())]:(p/filename).write_bytes(data)
        preview.save(p/'preview.png')
    p=out/'staged/League';p.mkdir()
    for n,v in outdoor.items():
        if n=='map.json':v=(json.dumps(exterior,indent=2)+chr(10)).encode()
        (p/n).write_bytes(v)
    receipt=dict(status='NATIVE_NEUTRAL_CENTER_GEOGRAPHY_NOT_HEALING_OR_RUNTIME_ACCEPTANCE',input_sha256=pins,portals={n:list(v) for n,v in PORTS.items()},
        closures=closures,exterior_binary_border_art_unchanged=True,
        limits=['Explicit native GBA room adaptation, not DS room geometry or functional service implementation',
                'No nurse/healer/respawn registration, encounters/story, save IDs/schema or production installation',
                'Generic PC/metatile behavior and door animation need runtime acceptance; not claimed',
                'Original exterior two cave events preserved; Route223 Surf and side-room/League dependencies remain',
                'No NORMAL/RELEASE/native-game-suite/mGBA/Save evidence borrowed from earlier packets'])
    receipt['output_sha256']={str(p.relative_to(out)):m.base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+chr(10));return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(build(a.engine,a.out),indent=2))
