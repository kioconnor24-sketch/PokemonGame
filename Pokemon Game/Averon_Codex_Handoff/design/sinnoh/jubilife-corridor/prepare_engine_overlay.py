#!/usr/bin/env python3
"""Materialize six neutral engine-shaped map candidates without editing the engine.

Registrar fragments are deliberately NOT applied while #181/Verity own shared
registries. Protected integration and actual gameplay acceptance are separate.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import struct
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('corridor',HERE/'build_corridor.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
SECTIONS={'JubilifeCity':('MAPSEC_JUBILIFE_CITY',221,'JUBILIFE CITY'),'Route203':('MAPSEC_ROUTE_203',222,'ROUTE 203'),'OreburghGate_1F':('MAPSEC_OREBURGH_GATE',223,'OREBURGH GATE')}

ROUTE202_HEAD='b4c1d39f0476b004f772506abd1b378e055ad03e'
MUSIC={'JubilifeCity':'MUS_RUSTBORO','Route203':'MUS_ROUTE104',
       'OreburghGate_1F':'MUS_PETALBURG_WOODS',
       'JubilifeCity_PokemonCenter_1F':'MUS_POKE_CENTER',
       'JubilifeCity_Mart':'MUS_POKE_MART','JubilifeCity_PokemonSchool':'MUS_SCHOOL'}

def finish_gate(raw):
 """Remove the unused ladder and seal the unbuilt exit with existing cave art.

 Input is the immutable staged candidate; reject moved/changed source cells.
 The south-facing mouth is replaced with the adjacent continuous cave wall.
 No new warp, destination, art or saved identity is introduced.
 """
 cells=list(struct.unpack('<783H',raw))
 expected={(19,5):575,(25,20):519,(24,21):600,(25,21):601,(26,21):602}
 for (x,y),mid in expected.items():
  if cells[y*29+x]&1023!=mid:raise ValueError('Gate closure source changed')
 floor=cells[4*29+19];wall=cells[21*29+23]
 if floor!=0x3201 or wall!=0x0609:raise ValueError('Gate reference terrain changed')
 cells[5*29+19]=floor;cells[20*29+25]=floor
 for x in (24,25,26):cells[21*29+x]=wall
 return struct.pack('<783H',*cells)

def finish_center(raw):
 """Replace the unused escalator to an unbuilt floor with a continuous wall.

 Both real outside doors are unchanged. Reuse the adjacent wall/floor cells;
 restore the old escalator approach's transition elevation to ordinary floor.
 """
 cells=list(struct.unpack('<126H',raw))
 expected={(0,5):0x280,(1,5):0x281,(0,6):0x288,(1,6):0x289,(0,7):0x290,(1,7):0x291,(2,6):0x202}
 for (x,y),mid in expected.items():
  if cells[y*14+x]&1023!=mid:raise ValueError('Center closure source changed')
 wall=cells[4*14];floor=cells[5*14+2]
 if wall!=0x3620 or floor!=0x3202:raise ValueError('Center reference terrain changed')
 if cells[6*14+2]>>12!=0:raise ValueError('Center approach source changed')
 for y in (5,6,7):cells[y*14]=wall;cells[y*14+1]=floor
 cells[6*14+2]=floor
 return struct.pack('<126H',*cells)

def prepare(donor,root,output):
 donor,root,output=map(Path,(donor,root,output))
 if output.exists() or 'engine' in output.resolve().parts:raise ValueError('new off-engine output required')
 spec=json.loads((root/'corridor-spec.json').read_text());revision=spec['donor_revision']
 if b.static.git(donor,'rev-parse','HEAD').decode().strip()!=revision:raise ValueError('wrong pinned donor')
 ids={};layouts=[];includes=[]
 for name in spec['maps']:
  ids[name]=json.loads(b.static.verified_file(donor,'data/maps/'+name+'/map.json',revision))['id']
 output.mkdir(parents=True)
 for name,config in spec['maps'].items():
  stage=json.loads((root/'staged'/name/'map.json').read_text());parent=config['parent'];section=SECTIONS[parent][0]
  city=name=='JubilifeCity';route=name=='Route203';cave=name=='OreburghGate_1F';inside=not(city or route or cave)
  selected=(root/'corridor-banks'/name) if city or route else (root/'averon-adapted'/name)
  raw=(selected/'map.bin').read_bytes();w,h=config['dimensions']
  if cave:raw=finish_gate(raw)
  if name=='JubilifeCity_PokemonCenter_1F':raw=finish_center(raw)
  if len(raw)!=w*h*2:raise ValueError('invalid map length')
  layout_id='LAYOUT_'+ids[name].removeprefix('MAP_')
  target_tilesets=['gTileset_General','gTileset_AveronCorridorRustboro'] if city or route else stage['source_tilesets']
  layouts.append({'id':layout_id,'name':name+'_Layout','width':w,'height':h,'primary_tileset':target_tilesets[0],'secondary_tileset':target_tilesets[1],
                  'border_filepath':'data/layouts/'+name+'/border.bin','blockdata_filepath':'data/layouts/'+name+'/map.bin','layout_version':'emerald'})
  warp_events=[{k:v for k,v in warp.items() if k in ('x','y','elevation','dest_warp_id')}|{'dest_map':ids[warp['dest_map']],'dest_warp_id':str(warp['dest_warp_id'])} for warp in stage['warp_events']]
  header={'id':ids[name],'name':name,'layout':layout_id,'music':MUSIC[name],'region':'REGION_SINNOH','region_map_section':section,
          'weather':'WEATHER_SUNNY','map_type':'MAP_TYPE_CITY' if city else 'MAP_TYPE_ROUTE' if route else 'MAP_TYPE_UNDERGROUND' if cave else 'MAP_TYPE_INDOOR',
          'allow_cycling':city or route,'allow_escaping':cave,'allow_running':True,'show_map_name':True,'requires_flash':False,'battle_scene':'MAP_BATTLE_SCENE_NORMAL',
          'connections':[{'map':ids[c['to']],'direction':c['direction'],'offset':c['offset']} for c in stage['connections']],
          'object_events':[],'coord_events':[],'bg_events':[],'warp_events':warp_events}
  # Concrete candidate only, depends on actual Route202 protected integration.
  if city:header['connections'].append({'map':'MAP_ROUTE202','direction':'down','offset':38})
  md=output/'data/maps'/name;ld=output/'data/layouts'/name;md.mkdir(parents=True);ld.mkdir(parents=True)
  b.dump(md/'map.json',header);(md/'scripts.inc').write_text(name+'_MapScripts::\n\t.byte 0\n')
  (ld/'map.bin').write_bytes(raw);shutil.copy(root/'staged'/name/'border.bin',ld/'border.bin')
  includes.append('\t.include "data/maps/'+name+'/scripts.inc"')
 bank=output/'data/tilesets/secondary/averon_corridor_rustboro';bank.mkdir(parents=True)
 for name in ('metatiles.bin','metatile_attributes.bin'):shutil.copy(root/'corridor-banks'/name,bank/name)
 (output/'averon_corridor_tileset.c').write_text((root/'corridor-banks/tileset.c').read_text())
 fragment={'status':'UNAPPLIED_REGISTRAR_FRAGMENTS_NOT_PRODUCTION_ACCEPTANCE','required_upstream':'PR181 Route202 integration; serialize globals with ClaudeVerity',
           'append_map_names':list(spec['maps']),'append_layouts':layouts,'append_event_includes':includes,
           'append_sections':[{'id':symbol,'value':value,'name':label,'region':'REGION_SINNOH'} for symbol,value,label in SECTIONS.values()],
           'tileset_symbol':'gTileset_AveronCorridorRustboro',
           'route202_header_patch':{'expected_source_head':ROUTE202_HEAD,'append_connection':{'map':ids['JubilifeCity'],'direction':'up','offset':-38},'preserve_all_existing_connections':True},
           'deferred':['actual map-group indices depend on current main; append only','section221/222/223 approved; preserve legacy/sentinel/special codes','source/pins/required protected-path authorization','paired ROM/native and genuine graphical/save acceptance','no healer/services/encounters introduced; existing Averon music reused']}
 b.dump(output/'registration-fragments.json',fragment)
 return fragment

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('donor','root','output'):p.add_argument('--'+n,required=True)
 v=p.parse_args();print(json.dumps(prepare(v.donor,v.root,v.output),indent=2))
