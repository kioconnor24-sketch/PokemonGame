#!/usr/bin/env python3
"""Prove four complete source candidates against EXISTING Averon map assets.

No approximate or guessed remaps: referenced records, attributes, indexed tiles
and actual selected palettes must agree before the existing converter is called.
Unreferenced palette/sheet differences do not count as used dependency failures.
"""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
from PIL import Image

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('corridor_builder',HERE/'build_corridor.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
FOLDERS={'gTileset_General':'primary/general','gTileset_Building':'primary/building','gTileset_Cave':'secondary/cave','gTileset_PokemonCenter':'secondary/pokemon_center','gTileset_Shop':'secondary/shop','gTileset_PokemonSchool':'secondary/pokemon_school'}
MAPS=('OreburghGate_1F','JubilifeCity_PokemonCenter_1F','JubilifeCity_Mart','JubilifeCity_PokemonSchool')

def tile(image,index):
 columns=image.width//8;x=(index%columns)*8;y=(index//columns)*8
 if x+8>image.width or y+8>image.height:raise ValueError('graphic out of range')
 return image.crop((x,y,x+8,y+8)).tobytes()

def compare(raw,source,target):
 records=[p[0] for p in source];images=[p[2] for p in source]
 deps=b.dual.closure(raw,records,images)
 for mid in deps['metatiles']:
  bank,index=divmod(mid,512)
  for component,size in ((0,16),(1,2)):
   if source[bank][component][index*size:(index+1)*size]!=target[bank][component][index*size:(index+1)*size]:raise ValueError('metatile/attribute mismatch: '+str(mid))
 for tid in deps['graphic_tiles']:
  bank,index=divmod(tid,512)
  if tile(source[bank][2],index)!=tile(target[bank][2],index):raise ValueError('indexed graphic mismatch: '+str(tid))
 for pal in deps['palettes']:
  bank=0 if pal<6 else 1
  if source[bank][3][pal]!=target[bank][3][pal]:raise ValueError('palette mismatch: '+str(pal))
 return deps

def read_target(engine,folder):
 p=Path(engine)/'data/tilesets'/folder
 return ((p/'metatiles.bin').read_bytes(),(p/'metatile_attributes.bin').read_bytes(),Image.open(p/'tiles.png'),[b.static.palette((p/('palettes/%02d.pal'%i)).read_bytes()) for i in range(16)])

def adapt(donor,engine,staged,output):
 donor,engine,staged,output=map(Path,(donor,engine,staged,output))
 if output.exists() or 'engine' in output.resolve().parts:raise ValueError('new off-engine output required')
 spec=json.loads((HERE/'corridor-spec.json').read_text());revision=spec['donor_revision']
 if b.static.git(donor,'rev-parse','HEAD').decode().strip()!=revision:raise ValueError('wrong source revision')
 # Runtime enums/scheduling are engine source, not guessed from graphic names.
 for rel in b.static.CONTRACTS:
  if b.static.verified_file(donor,rel,revision)!=(engine/rel).read_bytes():raise ValueError('runtime contract mismatch')
 pending=[]
 for name in MAPS:
  h=json.loads((staged/name/'map.json').read_text());raw=(staged/name/'source.bin').read_bytes();border=(staged/name/'border.bin').read_bytes()
  source=[b.bank(donor,FOLDERS[s],revision) for s in h['source_tilesets']]
  target=[read_target(engine,FOLDERS[s]) for s in h['source_tilesets']]
  deps=compare(raw+border,source,target)
  widths=h['dimensions'];pals={i:target[0 if i<6 else 1][3][i] for i in range(16)}
  final=(staged/name/'map.bin').read_bytes()
  preview=b.dual.render(final,[x[0] for x in target],[x[2] for x in target],pals,*widths)
  manifest=b.pilot.draft_manifest(b.pilot.analyze(donor,name,revision))
  manifest.update(target_map_id='UNREGISTERED_'+name,target_primary_tileset=h['source_tilesets'][0],target_secondary_tileset=h['source_tilesets'][1])
  for key,value in manifest['metatiles'].items():value.update(target=int(key),graphics_verified=True,behavior_verified=True)
  pending.append((name,manifest,preview,deps,final,target))
 output.mkdir(parents=True)
 report={'status':'FOUR_AVERON_ASSET_CANDIDATES_HOST_VERIFIED_NOT_GAMEPLAY','donor_revision':revision,'maps':{}}
 for name,manifest,preview,deps,final,target in pending:
  p=output/name;p.mkdir();b.dump(p/'averon-remap.json',manifest)
  receipt=b.pilot.convert(donor,name,manifest,p/'averon-converted.bin')
  if (p/'averon-converted.bin').read_bytes()!=(staged/name/'source.bin').read_bytes():raise ValueError('identity conversion failed')
  (p/'map.bin').write_bytes(final);preview.save(p/'averon-render.png')
  report['maps'][name]={'dimensions':json.loads((staged/name/'map.json').read_text())['dimensions'],
   'dependencies':deps,'source_sha256':receipt['source_sha256'],'candidate_sha256':b.digest(final),
   'rgb_sha256':b.digest(preview.tobytes()),'tilesets':[manifest['target_primary_tileset'],manifest['target_secondary_tileset']],
   'scope':'Used static indexed pixels/palettes/records/attributes exact; no engine registration, doors/services or gameplay acceptance'}
 b.dump(output/'receipt.json',report)
 return report

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for a in ('donor','engine','staged','output'):p.add_argument('--'+a,required=True)
 a=p.parse_args();print(json.dumps(adapt(a.donor,a.engine,a.staged,a.output),indent=2))
