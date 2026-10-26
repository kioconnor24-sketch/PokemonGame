"""Bounded Hall technical geometry cannot imply legendary/DS scene acceptance."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/hall-origin-footprint'
s=importlib.util.spec_from_file_location('hall_tests',HERE/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine'
class HallTests(unittest.TestCase):
 def test_supported_only_closed_exit_and_no_story(self):
  g=json.loads((HERE/'geometry.json').read_text())['Hall'];self.assertEqual(len(g['surfaces']),106)
  self.assertEqual(g['rejected_permission_clear'],dict(missing_or_ambiguous_center=49))
  points={tuple(p['tile']):p for p in g['surfaces']}
  raw=(HERE/'staged/Hall/map.bin').read_bytes();open_count=0
  for i,(v,) in enumerate(struct.iter_unpack('<H',raw)):
   if not v&0xc00:
    open_count+=1;self.assertIn((i%64,i//64),points);self.assertEqual(points[(i%64,i//64)]['permission'],0)
  self.assertEqual(open_count,105)
  h=json.loads((HERE/'staged/Hall/map.json').read_text())
  self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
  for k in ('warp_events','connections','object_events','coord_events','bg_events'):self.assertFalse(h[k])
  self.assertTrue(struct.unpack_from('<H',raw,2*(53*64+31))[0]&0xc00)
 def test_full_replay_and_output_safety(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'fresh';r=m.build(ENGINE,out);self.assertEqual(r,json.loads((HERE/'receipt.json').read_text()))
   for p,h in r['output_sha256'].items():self.assertEqual(m.existing.base.sha((out/p).read_bytes()),h)
   with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,out)
 def test_source_default_unchanged_and_duplicate_rejected(self):
  g=json.loads((HERE/'geometry.json').read_text());g['Hall']['surfaces'].append(g['Hall']['surfaces'][0])
  with self.assertRaisesRegex(ValueError,'invalid|duplicate'):m.construct(g)
if __name__=='__main__':unittest.main()
