"""Original missing upper floors: frozen portals and real component connectivity."""
from collections import deque
import copy
import importlib.util
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest

ROOT=Path(os.environ.get('AVERON_TEST_SOURCE_ROOT',Path(__file__).resolve().parents[3]))
HERE=Path(os.environ.get('AVERON_UPPER_INPUTS',ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/coronet-upper'))
PACKET=Path(os.environ.get('AVERON_UPPER_PACKET',HERE))
p=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/victory-road-shell/build_shell.py'
sp=importlib.util.spec_from_file_location('upper_source_painter_test',p);s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s)
names={'2f':'SinnohMtCoronet_2F','3f':'SinnohMtCoronet_3F'};ids={n:'MAP_SINNOH_MT_CORONET_'+k.upper() for k,n in names.items()}
def cells(raw):return struct.unpack('<%dH'%(len(raw)//2),raw)
def reach(grid,w,h,start):
 seen={start};q=deque([start])
 while q:
  x,y=q.popleft()
  for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=nx<w and 0<=ny<h and (nx,ny) not in seen and not grid[ny*w+nx]&0xC00:seen.add((nx,ny));q.append((nx,ny))
 return seen

class UpperSourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.recipe=json.loads((HERE/'shell-recipe.json').read_text());cls.ref=json.loads((HERE/'portal-reference.json').read_text())
  cls.out=s.construct(cls.recipe,cls.ref,names,ids,'MAP_HEADER_MT_CORONET_')
  cls.receipt=json.loads((PACKET/'source-receipt.json').read_text())
 def test_actual_two_maps3128_cells_and_all_six_frozen_portal_coordinates(self):
  total=warps=0;byid={h['id']:h for _,_,h in self.out.values()}
  for n,(raw,border,h) in self.out.items():
   p=self.recipe['maps'][n];total+=len(raw)//2
   self.assertEqual((PACKET/'staged'/n/'map.bin').read_bytes(),raw);self.assertEqual((PACKET/'staged'/n/'border.bin').read_bytes(),border)
   self.assertEqual(json.loads((PACKET/'staged'/n/'map.json').read_text()),h)
   for old,v in zip(p['interior_warp_indices'],h['warp_events']):
    src=self.ref['files'][p['reference']]['warp_events'][old];self.assertEqual((src['x'],src['z']),(v['x'],v['y']))
    back=byid[v['dest_map']]['warp_events'][int(v['dest_warp_id'])];self.assertEqual(back['dest_map'],h['id']);warps+=1
   self.assertLessEqual((p['width']+15)*(p['height']+14),10240)
  self.assertEqual((total,warps),(3128,6))
 def test_2f_two_physical_components_join_only_via_its_actual_self_stairs(self):
  n=names['2f'];raw,_,h=self.out[n];grid=cells(raw);p=self.recipe['maps'][n];w,ht=p['width'],p['height']
  lower=reach(grid,w,ht,(7,23));upper=reach(grid,w,ht,(7,12));self.assertFalse(lower&upper)
  floor={(x,y) for y in range(ht) for x in range(w) if not grid[y*w+x]&0xC00};self.assertEqual(lower|upper,floor)
  self.assertEqual([(v['dest_map'],v['dest_warp_id']) for v in h['warp_events'][:2]],[(ids[n],'1'),(ids[n],'0')])
  third=self.out[names['3f']];r=cells(third[0]);self.assertEqual(len(reach(r,28,34,(14,26))),sum(not v&0xC00 for v in r))
 def test_external_1f_route207_outside_anchors_stay_closed_no_ids_or_story(self):
  for n,(raw,border,h) in self.out.items():
   p=self.recipe['maps'][n];grid=cells(raw);w,ht=p['width'],p['height']
   self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER');self.assertFalse(h['connections'] or h['object_events'] or h['bg_events'] or h['coord_events'])
   for x,y in p['sealed_external_ports']:self.assertTrue(grid[y*w+x]&0xC00)
   self.assertTrue(all(grid[y*w+x]&0xC00 for y in range(ht) for x in range(w) if x in (0,w-1) or y in (0,ht-1)))
   self.assertTrue(all(p['dest_map'] in ids.values() for p in h['warp_events']))
 def test_exact_permitted_asset_hashes_and_all_preview_pixels_and_native_attributes(self):
  engine=ROOT/'Pokemon Game/engine';paths=['data/tilesets/primary/general/','data/tilesets/secondary/cave/'];banks=[(engine/(p+'metatiles.bin')).read_bytes() for p in paths];attrs=[(engine/(p+'metatile_attributes.bin')).read_bytes() for p in paths];images=[s.dual.indexed((engine/(p+'tiles.png')).read_bytes()) for p in paths]
  for p,h in self.receipt['existing_averon_sha256'].items():self.assertEqual(s.sha(s.base.verified_file(ROOT,Path('Pokemon Game/engine')/p,'HEAD')),h)
  for n,(raw,border,h) in self.out.items():
   deps=s.dual.closure(raw+border,banks,images);self.assertEqual(deps,self.receipt['maps'][n]['dependencies']);pals={i:s.base.palette((engine/(paths[i>=6]+'palettes/%02d.pal'%i)).read_bytes()) for i in deps['palettes']};p=self.recipe['maps'][n]
   im=s.dual.render(raw,banks,images,pals,p['width'],p['height'])
   with s.dual.Image.open(PACKET/'staged'/n/'averon.png') as got:self.assertEqual(im.tobytes(),got.convert('RGB').tobytes())
   for v in h['warp_events']:
    val=cells(raw)[v['y']*p['width']+v['x']];self.assertEqual(s.art.attribute(attrs[(val&1023)//512],(val&1023)%512)&511,0x61)
 def test_namespace_mismatch_external_target_diagonal_and_buffer_overflow_rejected(self):
  with self.assertRaises(ValueError):s.construct(self.recipe,self.ref)
  for kind in ('external','diagonal','buffer'):
   r=copy.deepcopy(self.recipe);ref=copy.deepcopy(self.ref)
   if kind=='external':ref['files']['2f']['warp_events'][2]['dest_header_id']='MAP_HEADER_MT_CORONET_OUTSIDE_SOUTH'
   elif kind=='diagonal':r['maps'][names['2f']]['corridors'][0]=[[3,3],[5,5]]
   else:r['maps'][names['3f']]['height']=1000
   with self.subTest(kind=kind),self.assertRaises(ValueError):s.construct(r,ref,names,ids,'MAP_HEADER_MT_CORONET_')

if __name__=='__main__':unittest.main()
