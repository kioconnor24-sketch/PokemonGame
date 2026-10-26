#!/usr/bin/env python3
"""Nine-map neutral Battle Zone center packet; existing exterior bytes retained."""
import argparse,importlib.util,json,struct
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('battle_native_rooms',HERE.parent/'frontier-facilities/build.py')
reuse=importlib.util.module_from_spec(spec);spec.loader.exec_module(reuse)
m=reuse.m
AREAS={'FightArea':dict(width=70,height=37,door=[39,14]),'SurvivalArea':dict(width=32,height=32,door=[17,18]),'ResortArea':dict(width=36,height=30,door=[9,10])}
def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    repo=Path(m.base.git(engine,'rev-parse','--show-toplevel').decode().strip());pins={}
    def read(p):
        data=m.base.verified_file(repo,p.relative_to(repo),'HEAD');pins[str(p.relative_to(repo))]=m.base.sha(data);return data
    def eng(p):return read(engine/p)
    layouts={x['id']:x for x in json.loads(eng('data/layouts/layouts.json'))['layouts']}
    packets={};room_data={};closures=[];exterior_prefix={}
    base=HERE.parent/'battle-zone-north'
    for area,cfg in AREAS.items():
        # Fight includes the separately completed boundary aperture and Frontier gateway.
        if area=='FightArea':
            folder=HERE.parent/'frontier-gate-link/staged/FightArea'
            data={n:read(folder/n) for n in ('map.bin','border.bin','map.json','attributes.json','preview.png')}
            words=json.loads(data['attributes.json'])
        else:
            folder=base/'staged'/area
            data={n:read(folder/old) for n,old in [('map.bin','averon-map.bin'),('border.bin','averon-border.bin'),('preview.png','averon.png')]}
            data['map.json']=read(HERE.parent/'remaining-donor/staged'/area/'map.json')
            family=[read(base/'outdoor-family'/(n+'-attributes.bin')) for n in ('primary','secondary')]
            words={str(v&1023):m.packer.attribute(family[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',data['map.bin']+data['border.bin'])}
            data['attributes.json']=(json.dumps(words,indent=2)+chr(10)).encode()
        w,h=cfg['width'],cfg['height'];x,y=cfg['door']
        if len(data['map.bin'])!=2*w*h:raise ValueError('exterior bounds differ')
        header=json.loads(data['map.json']);prefix=json.loads(json.dumps(header['warp_events']))
        if len(prefix)!=(1 if area=='FightArea' else 0):raise ValueError('existing gateway prefix differs')
        v=struct.unpack_from('<H',data['map.bin'],2*(y*w+x))[0]
        below=struct.unpack_from('<H',data['map.bin'],2*((y+1)*w+x))[0]
        if words[str(v&1023)]&255!=0x69 or below&0xc00:raise ValueError('center anchor or doorstep differs')
        index=len(prefix);root_id='MAP_SINNOH_'+area.upper()+'_CENTER_1F'
        header['warp_events'].append(dict(x=x,y=y,elevation=0,dest_map=root_id,dest_warp_id='0'))
        data['map.json']=(json.dumps(header,indent=2)+chr(10)).encode();packets[area]=data;exterior_prefix[area]=prefix
        for floor in (1,2):
            name=area+'Center'+str(floor)
            original=json.loads(eng('data/maps/PetalburgCity_PokemonCenter_%dF/map.json'%floor))
            layout=layouts[original['layout']];width,height=layout['width'],layout['height']
            raw=bytearray(eng(layout['blockdata_filepath']));border=eng(layout['border_filepath'])
            rh=dict(original);rh.update(id='MAP_SINNOH_'+area.upper()+'_CENTER_'+str(floor)+'F',name='Sinnoh'+name,
                layout='LAYOUT_SINNOH_'+name.upper(),region='REGION_SINNOH',region_map_section='MAPSEC_PENDING_OWNER',
                connections=[],object_events=[],coord_events=[],bg_events=[])
            events=[]
            for i,event in enumerate(original['warp_events']):
                event=dict(event)
                if floor==1:
                    event.update(dest_map=header['id'] if i<2 else 'MAP_SINNOH_'+area.upper()+'_CENTER_2F',
                                 dest_warp_id=str(index) if i<2 else '0');events.append(event)
                elif i==0:
                    event.update(dest_map=root_id,dest_warp_id='2');events.append(event)
                else:
                    off=2*(event['y']*width+event['x']);before=struct.unpack_from('<H',raw,off)[0]
                    struct.pack_into('<H',raw,off,before|0xc00)
                    closures.append(dict(map=name,tile=[event['x'],event['y']],before=before,after=before|0xc00))
            rh['warp_events']=events
            paths=['data/tilesets/primary/'+reuse.folder(layout['primary_tileset'])+'/',
                   'data/tilesets/secondary/'+reuse.folder(layout['secondary_tileset'])+'/']
            banks=[eng(p+'metatiles.bin') for p in paths];attrs=[eng(p+'metatile_attributes.bin') for p in paths]
            images=[m.dual.indexed(eng(p+'tiles.png')) for p in paths];deps=m.dual.closure(raw,banks,images)
            palettes={i:m.base.palette(eng(paths[i>=6]+'palettes/%02d.pal'%i)) for i in deps['palettes']}
            preview=m.dual.render(raw,banks,images,palettes,width,height)
            words={str(v&1023):m.packer.attribute(attrs[(v&1023)//512],v%512) for (v,) in struct.iter_unpack('<H',raw+border)}
            l=dict(layout);l.update(id=rh['layout'],name=rh['name']+'_Layout',blockdata_filepath='staged/'+name+'/map.bin',border_filepath='staged/'+name+'/border.bin')
            room_data[name]=(raw,border,rh,l,words,preview)
    out.mkdir(parents=True)
    for name,data in packets.items():
        p=out/'staged'/name;p.mkdir(parents=True)
        for n,v in data.items():(p/n).write_bytes(v)
    for name,(raw,border,h,l,words,preview) in room_data.items():
        p=out/'staged'/name;p.mkdir(parents=True)
        for n,v in [('map.bin',raw),('border.bin',border),('map.json',(json.dumps(h,indent=2)+chr(10)).encode()),('layout.json',(json.dumps(l,indent=2)+chr(10)).encode()),('attributes.json',(json.dumps(words,indent=2)+chr(10)).encode())]:(p/n).write_bytes(v)
        preview.save(p/'preview.png')
    receipt=dict(status='NINE_MAP_NEUTRAL_CENTER_PACKET_NOT_SERVICES_OR_RUNTIME_ACCEPTANCE',input_sha256=pins,areas=AREAS,
       preserved_exterior_warp_prefix=exterior_prefix,closed_online_door_cells=closures,
       limits=['Six native GBA template room adaptations, not copied donor interiors or gameplay services',
               'Exterior map/border/art, existing Frontier gateway and regional connections unchanged',
               'No nurse/healer/respawn/link registrations, saved IDs/registry/schema/story or encounters',
               'Generic PC/door/escalator behavior needs actual runtime acceptance',
               'Original source Surf/rail/rock-climb restrictions remain, no whole-region foot acceptance',
               'No NORMAL/RELEASE/native-game-suite/mGBA/Save acceptance borrowed'])
    receipt['output_sha256']={str(p.relative_to(out)):m.base.sha(p.read_bytes()) for p in out.rglob('*') if p.is_file()}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+chr(10));return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--engine',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(build(a.engine,a.out),indent=2))
