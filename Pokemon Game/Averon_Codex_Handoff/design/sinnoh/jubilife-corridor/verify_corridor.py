#!/usr/bin/env python3
"""Strict OFF-ENGINE candidate checks; not ROM/gameplay acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

OPPOSITE={'left':'right','right':'left','up':'down','down':'up'}
def verify(root):
 root=Path(root);receipt=json.loads((root/'receipt.json').read_text());maps={n:json.loads((root/n/'map.json').read_text()) for n in receipt['maps']}
 for name,h in maps.items():
  w,ht=h['dimensions'];raw=(root/name/'source.bin').read_bytes();candidate=(root/name/'map.bin').read_bytes();m=receipt['maps'][name]
  if len(raw)!=2*w*ht or len(candidate)!=len(raw):raise ValueError('invalid geometry length')
  if hashlib.sha256(raw).hexdigest()!=m['source_sha256'] or hashlib.sha256(candidate).hexdigest()!=m['candidate_sha256']:raise ValueError('geometry hash mismatch')
  before=struct.unpack('<'+str(w*ht)+'H',raw);after=struct.unpack('<'+str(w*ht)+'H',candidate)
  changes={c['y']*w+c['x']:c for c in h['collision_closures']}
  for i,(a,b) in enumerate(zip(before,after)):
   if (a^b)&~0xC00:raise ValueError('metatile or elevation changed')
   if a!=b and (i not in changes or changes[i]['before']!=a or changes[i]['after']!=b):raise ValueError('undeclared collision edit')
  if h['section'] is not None:raise ValueError('candidate section must remain unregistered')
  for key in ('object_events','coord_events','bg_events','scripts','encounters','services'):
   if h[key]:raise ValueError('forbidden donor gameplay')
  manifest=json.loads((root/name/'identity-remap.json').read_text())
  if not all(str(manifest[k]).startswith('DONOR_ONLY_') for k in ('target_primary_tileset','target_secondary_tileset')):raise ValueError('identity proof is donor-only')
  for source,v in manifest['metatiles'].items():
   if v['target']!=int(source):raise ValueError('identity mapping changed')
  for c in h['connections']:
   if c['to'] not in maps:raise ValueError('unbuilt connection')
   if not any(v['to']==name and v['direction']==OPPOSITE[c['direction']] and v['offset']==-c['offset'] for v in maps[c['to']]['connections']):raise ValueError('nonreciprocal seam offset')
  for warp in h['warp_events']:
   if warp['dest_map'] not in maps:raise ValueError('unbuilt warp destination')
   target=maps[warp['dest_map']];index=warp['dest_warp_id']
   if type(index)is not int or not 0<=index<len(target['warp_events']):raise ValueError('invalid warp destination index')
   if target['warp_events'][index]['dest_map']!=name:raise ValueError('missing return warp')
   x,y=warp['x'],warp['y']
   if not 0<=x<w or not 0<=y<ht or ((after[y*w+x]>>10)&3)!=warp['source_collision']:raise ValueError('warp is blocked/out of bounds')
 return {'maps':len(maps),'cells':sum(v['source_cells'] for v in receipt['maps'].values()),'warps':sum(len(v['warp_events']) for v in maps.values()),'connections':sum(len(v['connections']) for v in maps.values()),'status':'HOST_VALIDATED_NOT_INTEGRATED_OR_PLAYTESTED'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('root');a=p.parse_args();print(json.dumps(verify(a.root),indent=2))
