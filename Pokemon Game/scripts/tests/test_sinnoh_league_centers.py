"""Native neutral League rooms preserve exterior and omit online services."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
# Historical DEV/source receipt replay uses its exact accepted checkout.
# Production installer tests remain bound to the current checkout.
from sinnoh_replay_fixture import post_c_source_root
ROOT = post_c_source_root(Path(__file__).resolve().parents[3])

ROOT=post_c_source_root(Path(__file__).resolve().parents[3]);HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/league-neutral-centers'
s=importlib.util.spec_from_file_location('league_centers_tests',HERE/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine'


class LeagueCenters(unittest.TestCase):
 def test_unchanged_exterior_prefix_and_native_door_approaches(self):
  old=HERE.parent/'victory-road-shell/connected/PokmonLeague';new=HERE/'staged/League'
  for n in ('map.bin','border.bin','averon.png','attributes.json'):self.assertEqual((old/n).read_bytes(),(new/n).read_bytes())
  oldh=json.loads((old/'map.json').read_text());h=json.loads((new/'map.json').read_text())
  self.assertEqual(h['warp_events'][:2],oldh['warp_events']);self.assertEqual(h['connections'],oldh['connections'])
  words=json.loads((new/'attributes.json').read_text())['used_source_attribute_words']
  for e in h['warp_events'][2:]:
   v=struct.unpack_from('<H',(new/'map.bin').read_bytes(),2*(e['y']*33+e['x']))[0]
   self.assertEqual(words[str(v&1023)]&255,0x69)
   below=struct.unpack_from('<H',(new/'map.bin').read_bytes(),2*((e['y']+1)*33+e['x']))[0];self.assertFalse(below&0xc00)
 def test_four_rooms_clear_service_free_reciprocal_stairs_and_closed_online(self):
  layouts={x['id']:x for x in json.loads((ENGINE/'data/layouts/layouts.json').read_text())['layouts']}
  for side in m.PORTS:
   for floor in (1,2):
    p=HERE/'staged'/(side+str(floor));h=json.loads((p/'map.json').read_text())
    original=json.loads((ENGINE/('data/maps/PetalburgCity_PokemonCenter_%dF/map.json'%floor)).read_text());l=layouts[original['layout']]
    expected=bytearray((ENGINE/l['blockdata_filepath']).read_bytes())
    self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
    for k in ('object_events','coord_events','bg_events'):self.assertFalse(h[k])
    if floor==2:
     for e in original['warp_events'][1:]:
      i=2*(e['y']*l['width']+e['x']);v=struct.unpack_from('<H',expected,i)[0];struct.pack_into('<H',expected,i,v|0xc00)
     self.assertEqual(len(h['warp_events']),1)
     self.assertEqual(h['warp_events'][0]['dest_warp_id'],'2')
    else:
     self.assertEqual(len(h['warp_events']),3)
     self.assertEqual(h['warp_events'][2]['dest_warp_id'],'0')
     self.assertEqual(h['warp_events'][0]['dest_map'],'MAP_POKMON_LEAGUE')
     self.assertEqual(h['warp_events'][1]['dest_map'],'MAP_POKMON_LEAGUE')
    self.assertEqual(bytes(expected),(p/'map.bin').read_bytes())
    self.assertEqual((ENGINE/l['border_filepath']).read_bytes(),(p/'border.bin').read_bytes())
 def test_replay_dirty_source_and_existing_output_negative(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'fresh';r=m.build(ENGINE,out);self.assertEqual(r,json.loads((HERE/'receipt.json').read_text()))
   for p,h in r['output_sha256'].items():self.assertEqual(m.m.base.sha((out/p).read_bytes()),h)
   with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,out)
  target=HERE.parent/'victory-road-shell/connected/PokmonLeague/map.bin';original=Path.read_bytes
  def dirty(p):
   raw=original(p);return bytes([raw[0]^1])+raw[1:] if p==target else raw
  with tempfile.TemporaryDirectory() as t,patch.object(Path,'read_bytes',dirty):
   out=Path(t)/'never'
   with self.assertRaisesRegex(ValueError,'dirty'):m.build(ENGINE,out)
   self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
