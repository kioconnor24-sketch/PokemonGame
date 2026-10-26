"""Preserved Route224 terrain and bounded source-backed Room3 return."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/route224-cave-return'
s=importlib.util.spec_from_file_location('route224_tests',HERE/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine'
class RouteReturn(unittest.TestCase):
 def test_complete_original_terrain_attributes_and_only_declared_closures(self):
  original=HERE.parent/'remaining-donor/staged/Route224'
  before=(original/'map.bin').read_bytes();after=(HERE/'staged/Route224/map.bin').read_bytes()
  attrs=json.loads((original/'attributes.json').read_text())['used_source_attribute_words']
  new_attrs=json.loads((HERE/'staged/Route224/attributes.json').read_text())
  receipt=json.loads((HERE/'receipt.json').read_text());closures={tuple(e['tile']) for e in receipt['route_boundary_closures']}
  self.assertEqual(receipt['buffer_padded_cells'],8532);self.assertLessEqual(receipt['buffer_padded_cells'],10240)
  for i,((a,),(b,)) in enumerate(zip(struct.iter_unpack('<H',before),struct.iter_unpack('<H',after))):
   xy=(i%64,i//64);expected=(a&0xfc00)|0xc00 if xy in closures else a&0xfc00
   self.assertEqual(b&0xfc00,expected);self.assertEqual(new_attrs[str(b&1023)],attrs[str(a&1023)])
   if xy in closures:self.assertTrue(xy[0]==0 or xy[1]==0)
  self.assertTrue(all(v[0]&0xc00 for v in struct.iter_unpack('<H',after[:128])))
  h=json.loads((HERE/'staged/Route224/map.json').read_text());self.assertFalse(h['connections'])
 def test_reciprocal_native_door_and_one_room_cell(self):
  route=json.loads((HERE/'staged/Route224/map.json').read_text());room=json.loads((HERE/'staged/Room3/map.json').read_text())
  self.assertEqual(route['warp_events'],[dict(x=11,y=70,elevation=0,dest_map=room['id'],dest_warp_id='1')])
  self.assertEqual(room['warp_events'][1]['dest_map'],route['id']);self.assertEqual(room['warp_events'][1]['dest_warp_id'],'0')
  old=HERE.parent/'victory-road-side-rooms/staged/Room3'
  self.assertEqual(json.loads((old/'map.json').read_text())['warp_events'],room['warp_events'][:1])
  a=(old/'map.bin').read_bytes();b=(HERE/'staged/Room3/map.bin').read_bytes()
  self.assertEqual([i for i,(x,y) in enumerate(zip(struct.iter_unpack('<H',a),struct.iter_unpack('<H',b))) if x!=y],[16*32+29])
  for name,h,w,behavior in [('Route224',route,64,0x60),('Room3',room,32,0x61)]:
   p=HERE/'staged'/name;e=h['warp_events'][0 if name=='Route224' else 1]
   raw=(p/'map.bin').read_bytes();v=struct.unpack_from('<H',raw,2*(e['y']*w+e['x']))[0]
   self.assertFalse(v&0xc00);self.assertEqual(json.loads((p/'attributes.json').read_text())[str(v&1023)]&255,behavior)
   self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
 def test_replay_and_unknown_dependency_fails_before_output(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'new';r=m.build(ENGINE,out);self.assertEqual(r,json.loads((HERE/'receipt.json').read_text()))
   for p,h in r['output_sha256'].items():self.assertEqual(m.m.base.sha((out/p).read_bytes()),h)
   with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,out)
  with tempfile.TemporaryDirectory() as t,patch.dict(m.SECONDARY,{999:1}):
   out=Path(t)/'never'
   with self.assertRaisesRegex(ValueError,'unreviewed'):m.build(ENGINE,out)
   self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
