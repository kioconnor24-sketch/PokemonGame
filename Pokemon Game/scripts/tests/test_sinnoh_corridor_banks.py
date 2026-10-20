"""Actual staged corridor bank and geography invariants, no engine map mutation."""
import json
from pathlib import Path
import struct
import unittest
ROOT=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/jubilife-corridor'
ENGINE=Path(__file__).resolve().parents[2]/'engine'
FOLDERS=('primary/general','secondary/rustboro')
class CorridorBankTests(unittest.TestCase):
 def setUp(self):
  self.p=ROOT/'corridor-banks';self.r=json.loads((self.p/'receipt.json').read_text());self.records=(self.p/'metatiles.bin').read_bytes();self.attrs=(self.p/'metatile_attributes.bin').read_bytes()
 def test_existing_secondary_ids_preserved_and_capacity_bounded(self):
  base=ENGINE/'data/tilesets/secondary/rustboro'
  self.assertEqual(self.records[:350*16],(base/'metatiles.bin').read_bytes())
  self.assertEqual(self.attrs[:350*2],(base/'metatile_attributes.bin').read_bytes())
  self.assertEqual(len(self.records)//16,369);self.assertEqual(len(self.attrs)//2,369);self.assertLessEqual(369,512)
 def test_appended_records_use_only_existing_averon_graphic_words(self):
  for entry in self.r['allocation']:
   b,i=divmod(entry['base_existing_id'],512);target=entry['target_id']-512
   original=(ENGINE/'data/tilesets'/FOLDERS[b]/'metatiles.bin').read_bytes()
   self.assertEqual(self.records[target*16:target*16+16],original[i*16:i*16+16])
   self.assertEqual(struct.unpack_from('<H',self.attrs,target*2)[0],entry['attribute_u16'])
 def test_upper_collision_and_elevation_bits_preserved(self):
  for name in ('JubilifeCity','Route203'):
   before=ROOT/('city-art-draft/map.bin' if name=='JubilifeCity' else 'staged/Route203/map.bin')
   a=struct.unpack('<'+str(before.stat().st_size//2)+'H',before.read_bytes());after=self.p/name/'map.bin';b=struct.unpack('<'+str(len(a))+'H',after.read_bytes())
   self.assertEqual([x&0xFC00 for x in a],[x&0xFC00 for x in b])
 def test_route202_streaming_strip_uses_shared_primary_only(self):
  cells=struct.unpack('<4480H',(self.p/'JubilifeCity/map.bin').read_bytes())
  self.assertTrue(all((c&1023)<512 for c in cells[57*70:]))
  self.assertEqual(self.r['primary'],'existing gTileset_General unchanged')
 def test_active_city_door_coordinates_and_collision_preserved(self):
  h=json.loads((ROOT/'staged/JubilifeCity/map.json').read_text());cells=struct.unpack('<4480H',(self.p/'JubilifeCity/map.bin').read_bytes())
  self.assertEqual([(w['x'],w['y']) for w in h['warp_events']],[(55,36),(54,26),(43,36)])
  for w in h['warp_events']:self.assertEqual((cells[w['y']*70+w['x']]>>10)&3,w['source_collision'])
 def test_all_candidate_metatiles_are_in_range(self):
  for name,w,h in [('JubilifeCity',70,64),('Route203',64,30)]:
   cells=struct.unpack('<'+str(w*h)+'H',(self.p/name/'map.bin').read_bytes())
   self.assertTrue(all((v&1023)<512+369 for v in cells))
if __name__=='__main__':unittest.main()
