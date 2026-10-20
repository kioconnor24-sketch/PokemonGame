import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/jubilife-corridor'
s=importlib.util.spec_from_file_location('corridor_verify',ROOT/'verify_corridor.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
class CorridorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'staged';shutil.copytree(ROOT/'staged',self.root)
 def edit(self,relative,fn):
  p=self.root/relative;x=json.loads(p.read_text());fn(x);p.write_text(json.dumps(x))
 def test_six_real_candidates(self):self.assertEqual(v.verify(self.root)['maps'],6)
 def test_wrong_offset_fails(self):
  self.edit('Route203/map.json',lambda h:h['connections'][0].update(offset=1))
  with self.assertRaisesRegex(ValueError,'seam offset'):v.verify(self.root)
 def test_invalid_warp_fails(self):
  self.edit('Route203/map.json',lambda h:h['warp_events'][0].update(dest_warp_id=88))
  with self.assertRaisesRegex(ValueError,'warp destination index'):v.verify(self.root)
 def test_unbuilt_destination_fails(self):
  self.edit('OreburghGate_1F/map.json',lambda h:h['warp_events'][0].update(dest_map='OreburghCity'))
  with self.assertRaisesRegex(ValueError,'unbuilt warp|missing return warp'):v.verify(self.root)
 def test_false_averon_graphics_attestation_fails(self):
  self.edit('JubilifeCity/identity-remap.json',lambda h:h.update(target_primary_tileset='gTileset_General'))
  with self.assertRaisesRegex(ValueError,'donor-only'):v.verify(self.root)
 def test_inherited_story_fails(self):
  self.edit('JubilifeCity/map.json',lambda h:h['scripts'].append('OriginalStory'))
  with self.assertRaisesRegex(ValueError,'donor gameplay'):v.verify(self.root)
if __name__=='__main__':unittest.main()
