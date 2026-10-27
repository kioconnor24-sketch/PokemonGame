"""Nine-map Battle Zone center construction without service/identity changes."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/battle-zone-center-shells'
s=importlib.util.spec_from_file_location('battle_center_tests',HERE/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine'
class BattleCenters(unittest.TestCase):
 def test_all_four_exteriors_immutable_geometry_and_existing_gateway_prefix(self):
  for name,cfg in m.AREAS.items():
   q=HERE/'staged'/name
   if name=='FightArea':
    parent=HERE.parent/'frontier-gate-link/staged/FightArea'
    for n in ('map.bin','border.bin','preview.png','attributes.json'):self.assertEqual((parent/n).read_bytes(),(q/n).read_bytes())
    original=json.loads((parent/'map.json').read_text())
   elif name=='Route228':
    parent=HERE.parent/'battle-zone-links/staged/Route228'
    for n in ('map.bin','border.bin','preview.png'):self.assertEqual((parent/n).read_bytes(),(q/n).read_bytes())
    original=json.loads((parent/'map.json').read_text())
   else:
    parent=HERE.parent/'battle-zone-north/staged'/name
    for a,b in [('map.bin','averon-map.bin'),('border.bin','averon-border.bin'),('preview.png','averon.png')]:self.assertEqual((parent/b).read_bytes(),(q/a).read_bytes())
    original=json.loads((HERE.parent/'remaining-donor/staged'/name/'map.json').read_text())
   h=json.loads((q/'map.json').read_text());self.assertEqual(h['warp_events'][:len(original['warp_events'])],original['warp_events'])
   self.assertEqual(h['connections'],original['connections'])
   e=h['warp_events'][len(original['warp_events'])];self.assertEqual([e['x'],e['y']],cfg['door']);self.assertEqual(e['dest_warp_id'],'0')
   v=struct.unpack_from('<H',(q/'map.bin').read_bytes(),2*(e['y']*cfg['width']+e['x']))[0]
   self.assertEqual(json.loads((q/'attributes.json').read_text())[str(v&1023)]&255,0x69)
 def test_six_rooms_reciprocal_stairs_return_aliases_and_only_online_closures(self):
  layouts={v['id']:v for v in json.loads((ENGINE/'data/layouts/layouts.json').read_text())['layouts']}
  for area,cfg in m.AREAS.items():
   if not cfg.get('center',True):continue
   exterior=json.loads((HERE/'staged'/area/'map.json').read_text())
   for floor in (1,2):
    p=HERE/'staged'/(area+'Center'+str(floor));h=json.loads((p/'map.json').read_text())
    source=json.loads((ENGINE/('data/maps/PetalburgCity_PokemonCenter_%dF/map.json'%floor)).read_text())
    l=layouts[source['layout']];raw=bytearray((ENGINE/l['blockdata_filepath']).read_bytes())
    self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
    for k in ('object_events','coord_events','bg_events'):self.assertFalse(h[k])
    if floor==2:
     for e in source['warp_events'][1:]:
      off=2*(e['y']*l['width']+e['x']);v=struct.unpack_from('<H',raw,off)[0];struct.pack_into('<H',raw,off,v|0xc00)
     self.assertEqual(len(h['warp_events']),1)
     self.assertEqual(h['warp_events'][0]['dest_warp_id'],'2')
    else:
     self.assertEqual(len(h['warp_events']),3)
     for e in h['warp_events'][:2]:
      self.assertEqual(e['dest_map'],exterior['id'])
      self.assertEqual(exterior['warp_events'][int(e['dest_warp_id'])]['dest_map'],h['id'])
     self.assertEqual(h['warp_events'][2]['dest_warp_id'],'0')
    self.assertEqual((p/'map.bin').read_bytes(),bytes(raw))
    self.assertEqual((p/'border.bin').read_bytes(),(ENGINE/l['border_filepath']).read_bytes())
 def test_nine_house_shells_preserve_templates_and_both_return_aliases(self):
  layouts={v['id']:v for v in json.loads((ENGINE/'data/layouts/layouts.json').read_text())['layouts']}
  for name,(area,x,y,template) in m.HOUSES.items():
   p=HERE/'staged'/name;h=json.loads((p/'map.json').read_text())
   original=json.loads((ENGINE/('data/maps/'+template+'/map.json')).read_text());l=layouts[original['layout']]
   self.assertEqual((p/'map.bin').read_bytes(),(ENGINE/l['blockdata_filepath']).read_bytes())
   self.assertEqual((p/'border.bin').read_bytes(),(ENGINE/l['border_filepath']).read_bytes())
   self.assertEqual(len(h['warp_events']),2)
   self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
   for k in ('object_events','coord_events','bg_events'):self.assertFalse(h[k])
   parent=json.loads((HERE/'staged'/area/'map.json').read_text())
   for e in h['warp_events']:
    self.assertEqual(e['dest_map'],parent['id'])
    back=parent['warp_events'][int(e['dest_warp_id'])]
    self.assertEqual(back['dest_map'],h['id']);self.assertEqual((back['x'],back['y']),(x,y))
 def test_replay_dirty_source_and_unsafe_output_negatives(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'new';r=m.build(ENGINE,out);self.assertEqual(r,json.loads((HERE/'receipt.json').read_text()))
   for p,h in r['output_sha256'].items():self.assertEqual(m.m.base.sha((out/p).read_bytes()),h)
   with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,out)
  original=Path.read_bytes;target=HERE.parent/'frontier-gate-link/staged/FightArea/map.bin'
  def dirty(p):
   raw=original(p);return bytes([raw[0]^1])+raw[1:] if p==target else raw
  with tempfile.TemporaryDirectory() as t,patch.object(Path,'read_bytes',dirty):
   out=Path(t)/'never'
   with self.assertRaisesRegex(ValueError,'dirty'):m.build(ENGINE,out)
   self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
