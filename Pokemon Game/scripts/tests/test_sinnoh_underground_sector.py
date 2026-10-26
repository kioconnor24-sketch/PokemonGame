"""Real bounded Underground corridors; no fabricated base/multiplayer systems."""
import copy,importlib.util,json,struct,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/underground-physical-sector'
s=importlib.util.spec_from_file_location('underground_sector_tests',HERE/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine'
class UndergroundSector(unittest.TestCase):
 def test_genuine_source_floors_only_and_bounded_outer_cuts(self):
  g=json.loads((HERE/'geometry.json').read_text());self.assertEqual(sum(len(v['surfaces']) for v in g.values()),5850)
  self.assertNotIn('MAP_649',json.loads((HERE/'source-pins.json').read_text())['files'])
  for n,data in g.items():
   self.assertFalse(data['rejected_permission_clear']);points={tuple(p['tile']) for p in data['surfaces']}
   self.assertTrue(all(p['permission']==12 and p['flat'] for p in data['surfaces']))
   for i,(v,) in enumerate(struct.iter_unpack('<H',(HERE/'staged'/n/'map.bin').read_bytes())):
    x,y=i%64,i//64
    blocked_edge=x==0 and 'left' not in m.existing.OPEN_BOUNDARIES[n] or x==63 and 'right' not in m.existing.OPEN_BOUNDARIES[n] or y==0 and 'up' not in m.existing.OPEN_BOUNDARIES[n] or y==63 and 'down' not in m.existing.OPEN_BOUNDARIES[n]
    self.assertEqual(not bool(v&0xc00),(x,y) in points and not blocked_edge)
 def test_native_capacity_reciprocal_seams_and_true_components(self):
  r=json.loads((HERE/'receipt.json').read_text());self.assertEqual(r['padded_map_cells'],6162);self.assertEqual(r['buffer_cells'],10240)
  self.assertEqual([len(e['lanes']) for e in r['seams']],[20]*4)
  self.assertEqual([c['cells'] for c in r['static_global_components']],[3180,1040,910,460,160])
  self.assertEqual(r['static_global_components'][0]['sectors'],['NE','NW','SE','SW'])
  hs=[json.loads((HERE/'staged'/n/'map.json').read_text()) for n in m.SLICES];ids={h['id']:h for h in hs}
  for h in hs:
   self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
   for k in ('warp_events','object_events','coord_events','bg_events'):self.assertFalse(h[k])
   for e in h['connections']:
    other=ids[e['map']];reverse=dict(right='left',left='right',up='down',down='up')[e['direction']]
    self.assertIn(dict(map=h['id'],direction=reverse,offset=0),other['connections'])
 def test_invalid_capability_surface_and_duplicate_rejected(self):
  g=json.loads((HERE/'geometry.json').read_text());g['NW']['surfaces'][0]['permission']=0x65
  with self.assertRaisesRegex(ValueError,'ordinary source'):m.construct(g)
  g=json.loads((HERE/'geometry.json').read_text());g['NW']['surfaces'].append(copy.deepcopy(g['NW']['surfaces'][0]))
  with self.assertRaisesRegex(ValueError,'invalid|duplicate'):m.construct(g)
 def test_full_replay_and_existing_output_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'fresh';r=m.build(ENGINE,out);self.assertEqual(r,json.loads((HERE/'receipt.json').read_text()))
   for p,h in r['output_sha256'].items():self.assertEqual(m.existing.base.sha((out/p).read_bytes()),h)
   with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,out)
if __name__=='__main__':unittest.main()
