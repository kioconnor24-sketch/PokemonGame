"""True native capacity and exact source cell/pixel/portal preservation."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/frontier-bounded-campus'
s=importlib.util.spec_from_file_location('bounded_frontier_tests',HERE/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine';OLD=HERE.parent/'frontier-gate-link'
class BoundedFrontier(unittest.TestCase):
 def test_all_global_cells_pixels_and_attributes_unchanged_and_real_buffer_fits(self):
  original=(OLD/'staged/Campus/map.bin').read_bytes()
  parts=[(HERE/'staged'/n/'map.bin').read_bytes() for n in m.PARTS]
  reconstructed=b''.join(b''.join(p[y*64:(y+1)*64] for p in parts) for y in range(96))
  self.assertEqual(original,reconstructed)
  art=Image.new('RGB',(1536,1536))
  for i,n in enumerate(m.PARTS):
   q=HERE/'staged'/n
   art.paste(Image.open(q/'preview.png').convert('RGB'),(i*512,0))
   self.assertEqual((q/'attributes.json').read_bytes(),(OLD/'staged/Campus/attributes.json').read_bytes())
   self.assertEqual((q/'border.bin').read_bytes(),(OLD/'staged/Campus/border.bin').read_bytes())
  self.assertEqual(art.tobytes(),Image.open(OLD/'staged/Campus/preview.png').convert('RGB').tobytes())
  r=json.loads((HERE/'receipt.json').read_text());self.assertEqual(r['original_padded_cells'],12210);self.assertEqual(r['buffer_cells'],10240)
  self.assertTrue(all(v<=r['buffer_cells'] for v in r['padded_cells'].values()))
  for n in m.PARTS:self.assertEqual(r['padded_cells'][n],5170)
 def test_all_six_source_portals_remapped_and_returns_have_valid_targets(self):
  r=json.loads((HERE/'receipt.json').read_text());old=json.loads((OLD/'staged/Campus/map.json').read_text())
  hs={q.name:json.loads((q/'map.json').read_text()) for q in (HERE/'staged').iterdir()}
  ids={v['id']:v for v in hs.values()}
  self.assertEqual(len(r['original_campus_portal_mapping']),6)
  for i,e in enumerate(old['warp_events']):
   target=r['original_campus_portal_mapping'][str(i)]
   new=ids[target['map']]['warp_events'][target['index']]
   self.assertEqual(new,dict(e,x=e['x']%32));self.assertEqual(target['global_tile'],[e['x'],e['y']])
  for n,h in hs.items():
   self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
   for e in h['warp_events']:
    if e['dest_map'] not in ids:
     self.assertEqual(n,'FightArea');continue # named parent town dependencies
    target=ids[e['dest_map']]['warp_events'][int(e['dest_warp_id'])]
    self.assertEqual(target['dest_map'],h['id'])
  for e in r['strip_seams']:self.assertTrue(e['ordinary_ground_rows']);self.assertEqual(e['offset'],0)
 def test_other_maps_terrain_art_and_town_gateway_unchanged(self):
  for n in ('Gate','FightArea',*m.reuse.TEMPLATES):
   source=OLD/'staged/Gate' if n=='Gate' else HERE.parent/'battle-zone-center-shells/staged/FightArea' if n=='FightArea' else HERE.parent/'frontier-facilities/staged'/n
   for f in ('map.bin','border.bin','preview.png','attributes.json'):self.assertEqual((source/f).read_bytes(),(HERE/'staged'/n/f).read_bytes())
  self.assertEqual((HERE/'staged/FightArea/map.json').read_bytes(),(HERE.parent/'battle-zone-center-shells/staged/FightArea/map.json').read_bytes())
 def test_replay_dirty_source_and_output_guard(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'fresh';r=m.build(ENGINE,out);self.assertEqual(r,json.loads((HERE/'receipt.json').read_text()))
   for p,h in r['output_sha256'].items():self.assertEqual(m.m.base.sha((out/p).read_bytes()),h)
   with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,out)
  original=Path.read_bytes;target=OLD/'staged/Campus/map.bin'
  def dirty(p):
   raw=original(p);return bytes([raw[0]^1])+raw[1:] if p==target else raw
  with tempfile.TemporaryDirectory() as t,patch.object(Path,'read_bytes',dirty):
   out=Path(t)/'never'
   with self.assertRaisesRegex(ValueError,'dirty'):m.build(ENGINE,out)
   self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
