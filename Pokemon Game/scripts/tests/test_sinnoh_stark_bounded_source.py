"""Exact source Stark capacity repair, pending origins and unchanged native art."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from PIL import Image
# Historical DEV/source receipt replay uses its exact accepted checkout.
# Production installer tests remain bound to the current checkout.
from sinnoh_replay_fixture import post_c_source_root
ROOT = post_c_source_root(Path(__file__).resolve().parents[3])

ROOT=post_c_source_root(Path(__file__).resolve().parents[3]);HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/stark-bounded-source'
s=importlib.util.spec_from_file_location('stark_bounded_tests',HERE/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine'


class BoundedStark(unittest.TestCase):
 def test_original_room2_cells_and_all_rgba_pixels_reassemble_exactly(self):
  old=HERE.parent/'stark-mountain/staged/Room2'
  parts=[(HERE/'staged'/('StarkRoom2'+p)/'map.bin').read_bytes() for p in ('West','Center','East')]
  self.assertEqual(b''.join(b''.join(p[y*64:(y+1)*64] for p in parts) for y in range(96)),(old/'map.bin').read_bytes())
  canvas=Image.new('RGBA',(1536,1536))
  for i,p in enumerate(('West','Center','East')):canvas.paste(Image.open(HERE/'staged'/('StarkRoom2'+p)/'preview.png').convert('RGBA'),(512*i,0))
  self.assertEqual(canvas.tobytes(),Image.open(old/'preview.png').convert('RGBA').tobytes())
 def test_other_geometry_art_and_native_bank_prefixes_unchanged(self):
  for key,folder in [('Route227','stark-approach/staged/Route227'),('StarkOutside','stark-approach/staged/Outside'),('StarkRoom1','stark-approach/staged/Room1'),('StarkRoom3','stark-mountain/staged/Room3')]:
   for n in ('map.bin','border.bin','preview.png'):self.assertEqual((HERE/'staged'/key/n).read_bytes(),(HERE.parent/folder/n).read_bytes())
  for n in ('secondary-metatiles.bin','secondary-attributes.bin'):
   self.assertTrue((HERE/'families/Cave'/n).read_bytes().startswith((HERE.parent/'stark-mountain/cave-family'/n).read_bytes()))
 def test_source_sections_capacity_and_internal_returns(self):
  r=json.loads((HERE/'receipt.json').read_text());heads={}
  for key in m.KEYS:
   h=json.loads((HERE/'staged'/key/'map.json').read_text());heads[h['id']]=h
   self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER');self.assertFalse(h['name'].startswith('Dev'))
   self.assertLessEqual(r['padded_cells'][key],10240)
   for field in ('object_events','coord_events','bg_events'):self.assertFalse(h[field])
  self.assertNotIn('MAP_SINNOH_STARK_ROOM2',heads)
  for key in ('StarkRoom2West','StarkRoom2Center','StarkRoom2East'):self.assertEqual(r['padded_cells'][key],5170)
  for h in heads.values():
   for e in h['warp_events']:
    self.assertIn(e['dest_map'],heads)
    self.assertEqual(heads[e['dest_map']]['warp_events'][int(e['dest_warp_id'])]['dest_map'],h['id'])
   for e in h['connections']:
    if e['map'] not in heads:self.assertEqual(e['map'],'MAP_ROUTE226')
  for e in r['split_seams']:self.assertTrue(e['ordinary_ground_rows'])
 def test_full_replay_stable_artifacts_and_unsafe_output_refused(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'new';r=m.build(ENGINE,out)
   self.assertEqual(r['output_sha256'],json.loads((HERE/'receipt.json').read_text())['output_sha256'])
   for p,h in r['output_sha256'].items():self.assertEqual(m.scene.base.sha((out/p).read_bytes()),h)
   with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,out)
  with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,ENGINE/'bad')
if __name__=='__main__':unittest.main()
