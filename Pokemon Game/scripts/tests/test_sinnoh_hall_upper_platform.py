"""Explicit layer selection needs full source footprint and real landing adjacency."""
import copy,importlib.util,json,struct,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/hall-upper-platform'
s=importlib.util.spec_from_file_location('hall_upper_tests',HERE/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine'
class UpperHall(unittest.TestCase):
 def setUp(self):
  self.strict=json.loads((m.STRICT/'geometry.json').read_text());self.proof=json.loads((HERE/'upper-plane-proof.json').read_text())
 def test_exact_supported_upper_layer_original_unchanged_and_closed_story_exit(self):
  g=m.upper_geometry(self.strict,self.proof)
  self.assertEqual(len(self.strict['Hall']['surfaces']),106);self.assertEqual(len(g['Hall']['surfaces']),155)
  self.assertEqual(g['Hall']['surfaces'][:106],self.strict['Hall']['surfaces'])
  raw=(HERE/'staged/Hall/map.bin').read_bytes();points={tuple(p['tile']) for p in g['Hall']['surfaces'] if p['permission']==0}
  for i,(v,) in enumerate(struct.iter_unpack('<H',raw)):self.assertEqual(not bool(v&0xc00),(i%64,i//64) in points)
  self.assertEqual(len(points),154)
  h=json.loads((HERE/'staged/Hall/map.json').read_text())
  for k in ('warp_events','connections','object_events','coord_events','bg_events'):self.assertFalse(h[k])
  r=json.loads((HERE/'receipt.json').read_text());self.assertEqual(r['maps']['Hall']['static_components'],[154])
  self.assertEqual(r['static_entry_to_platform_path'][0],[31,52]);self.assertEqual(r['static_entry_to_platform_path'][-1],[31,25])
 def test_missing_corner_wrong_layer_duplicate_or_unjoined_landing_rejected(self):
  bad=copy.deepcopy(self.proof);bad[0]['corner_heights'][0]=['48']
  with self.assertRaisesRegex(ValueError,'every corner'):m.upper_geometry(self.strict,bad)
  bad=copy.deepcopy(self.proof);bad[0]['upper_height']='48'
  with self.assertRaisesRegex(ValueError,'every corner'):m.upper_geometry(self.strict,bad)
  with self.assertRaisesRegex(ValueError,'exact supported'):m.upper_geometry(self.strict,self.proof+[self.proof[0]])
  bad=copy.deepcopy(self.strict);bad['Hall']['surfaces']=[p for p in bad['Hall']['surfaces'] if p['tile']!=[28,32]]
  with self.assertRaisesRegex(ValueError,'landing adjacency'):m.upper_geometry(bad,self.proof)
 def test_native_replay_and_output_guard(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'new';r=m.build(ENGINE,out)
   self.assertEqual(r,json.loads((HERE/'receipt.json').read_text()))
   for p,h in r['output_sha256'].items():self.assertEqual(m.existing.base.sha((out/p).read_bytes()),h)
   with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,out)
if __name__=='__main__':unittest.main()
