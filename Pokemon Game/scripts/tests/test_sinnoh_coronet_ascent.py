"""Source-pinned upper ascent: exact portals, foot connectivity and narrow base opening."""
from collections import deque
import copy
import importlib.util
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
ROOT=Path(os.environ['AVERON_TEST_SOURCE_ROOT']) if 'AVERON_TEST_SOURCE_ROOT' in os.environ else Path(__file__).resolve().parents[3]
HERE=Path(os.environ.get('AVERON_ASCENT_INPUTS',ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/coronet-ascent'))
PACKET=Path(os.environ.get('AVERON_ASCENT_PACKET',HERE))
sp=importlib.util.spec_from_file_location('ascent',HERE/'build_ascent.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
p=HERE.parent/'victory-road-shell/build_shell.py';sp=importlib.util.spec_from_file_location('ascent_painter',p);s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s)
def words(raw):return struct.unpack('<%dH'%(len(raw)//2),raw)
class AscentTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.recipe=json.loads((HERE/'shell-recipe.json').read_text());cls.ref=json.loads((HERE/'portal-reference.json').read_text());cls.maps=s.construct(cls.recipe,cls.ref,a.NAMES,a.IDS,'MAP_HEADER_MT_CORONET_')
 def test_six_maps9524_cells18_source_pinned_reciprocal_events(self):
  self.assertEqual(len(self.maps),6);self.assertEqual(sum(len(v[0])//2 for v in self.maps.values()),9524)
  count=0;byid={v[2]['id']:v[2] for v in self.maps.values()}
  for name,(raw,border,h) in self.maps.items():
   self.assertEqual((PACKET/'staged'/name/'map.bin').read_bytes(),raw);self.assertEqual((PACKET/'staged'/name/'border.bin').read_bytes(),border)
   plan=self.recipe['maps'][name]
   for index,p in zip(plan['interior_warp_indices'],h['warp_events']):
    source=self.ref['files'][plan['reference']]['warp_events'][index];self.assertEqual((p['x'],p['y']),(source['x'],source['z']))
    other=byid[p['dest_map']]['warp_events'][int(p['dest_warp_id'])];self.assertEqual(other['dest_map'],h['id']);count+=1
   self.assertLessEqual((plan['width']+15)*(plan['height']+14),10240)
  self.assertEqual(count,18)
 def test_every_floor_cell_is_connected_through_ordinary_foot_and_real_stair_pairs(self):
  grids={n:words(v[0]) for n,v in self.maps.items()};byid={v[2]['id']:n for n,v in self.maps.items()};nodes=set();stairs={}
  for n,(raw,_,h) in self.maps.items():
   width=self.recipe['maps'][n]['width'];nodes|={(n,i%width,i//width) for i,v in enumerate(grids[n]) if not v&0xc00}
   for p in h['warp_events']:
    target=byid[p['dest_map']];dest=self.maps[target][2]['warp_events'][int(p['dest_warp_id'])];stairs[(n,p['x'],p['y'])]=(target,dest['x'],dest['y'])
  initial=(a.NAMES['2f'],8,23);seen={initial};q=deque([initial])
  while q:
   n,x,y=q.popleft();nexts=[(n,x+dx,y+dy) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))]
   if (n,x,y) in stairs:nexts.append(stairs[(n,x,y)])
   for node in nexts:
    if node in nodes and node not in seen:seen.add(node);q.append(node)
  self.assertEqual(seen,nodes)
 def test_original2f_unchanged_only3f_closed_portal_cell_opens(self):
  old=copy.deepcopy(self.recipe);old['maps']={n:old['maps'][n] for n in (a.NAMES['2f'],a.NAMES['3f'])};old['maps'][a.NAMES['3f']]['interior_warp_indices']=[0,1];old['maps'][a.NAMES['3f']]['sealed_external_ports']=[[3,29]]
  names={k:v for k,v in a.NAMES.items() if k in ('2f','3f')};ids={v:a.IDS[v] for v in names.values()};before=s.construct(old,self.ref,names,ids,'MAP_HEADER_MT_CORONET_')
  self.assertEqual(before[a.NAMES['2f']],self.maps[a.NAMES['2f']])
  n=a.NAMES['3f'];diff=[(i%28,i//28) for i,(x,y) in enumerate(zip(words(before[n][0]),words(self.maps[n][0]))) if x!=y];self.assertEqual(diff,[(3,29)]);self.assertEqual(before[n][1],self.maps[n][1]);self.assertEqual(before[n][2]['warp_events'],self.maps[n][2]['warp_events'][:2])
 def test_unbuilt_exits_borders_stay_closed_and_no_saved_identity_or_gameplay(self):
  for n,(raw,border,h) in self.maps.items():
   plan=self.recipe['maps'][n];w,ht=plan['width'],plan['height'];grid=words(raw)
   for x,y in plan['sealed_external_ports']:self.assertTrue(grid[y*w+x]&0xc00)
   self.assertTrue(all(grid[y*w+x]&0xc00 for y in range(ht) for x in range(w) if x in (0,w-1) or y in (0,ht-1)))
   self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER');self.assertFalse(h['object_events'] or h['bg_events'] or h['coord_events'] or h['connections']);self.assertFalse(h['requires_flash'])
 def test_all31_generated_outputs_repeat_and_committed_headers_only_have_disclosed_outside_type(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'packet';a.build(ROOT,HERE,out)
   expected={str(p.relative_to(out)):p.read_bytes() for p in out.rglob('*') if p.is_file()};self.assertEqual(len(expected),31)
   for path,data in expected.items():self.assertEqual((PACKET/path).read_bytes(),data,path)
  for n,(_,_,h) in self.maps.items():
   actual=json.loads((PACKET/'staged'/n/'map.json').read_text());expected=copy.deepcopy(h)
   if self.recipe['maps'][n]['reference'].startswith('outside_'):expected['map_type']='MAP_TYPE_ROUTE'
   self.assertEqual(actual,expected)
 def test_bad_foreign_topology_and_diagonal_corridor_rejected(self):
  bad=copy.deepcopy(self.ref);bad['files']['outside_south']['warp_events'][0]['dest_header_id']='MAP_HEADER_UNKNOWN_UNAPPROVED'
  with self.assertRaises((KeyError,ValueError)):s.construct(self.recipe,bad,a.NAMES,a.IDS,'MAP_HEADER_MT_CORONET_')
  bad=copy.deepcopy(self.recipe);bad['maps'][a.NAMES['outside_south']]['corridors'].append([[1,1],[3,3]])
  with self.assertRaisesRegex(ValueError,'orthogonal'):s.construct(bad,self.ref,a.NAMES,a.IDS,'MAP_HEADER_MT_CORONET_')
 def test_bare_matching_destination_suffix_cannot_impersonate_source_header(self):
  bad=copy.deepcopy(self.ref);bad['files']['2f']['warp_events'][2]['dest_header_id']='2F'
  with self.assertRaisesRegex(ValueError,'destination header prefix'):s.construct(self.recipe,bad,a.NAMES,a.IDS,'MAP_HEADER_MT_CORONET_')
if __name__=='__main__':unittest.main()
