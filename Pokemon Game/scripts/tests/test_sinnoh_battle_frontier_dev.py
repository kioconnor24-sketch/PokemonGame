"""Exact-source disposable scene assembly, preserving real legacy metadata."""
import copy,importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/battle-frontier-dev'
s=importlib.util.spec_from_file_location('battle_dev_tests',HERE/'prepare_scene.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class BattleFrontierDEV(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.files,cls.recipe=m.assemble(ROOT);cls.before=m.reuse.inputs(ROOT)
 def test_original_groups_layouts_disabled_entries_and_registry_slots_preserved(self):
  before=json.loads(self.before['data/maps/map_groups.json']);after=json.loads(self.files['data/maps/map_groups.json'])
  self.assertEqual(before['group_order'],after['group_order'])
  for k,v in before.items():
   if k!='gMapGroup_Sinnoh':self.assertEqual(v,after[k])
  self.assertEqual(after['gMapGroup_Sinnoh'][:19],before['gMapGroup_Sinnoh']);self.assertEqual(len(after['gMapGroup_Sinnoh']),63)
  old=json.loads(self.before['data/layouts/layouts.json'])['layouts'];new=json.loads(self.files['data/layouts/layouts.json'])['layouts']
  self.assertEqual(new[:len(old)],old);self.assertEqual(len(new),len(old)+44)
  oldslots=[x for x in self.before['test/data/averon_map_registry_slots.inc'].decode().splitlines() if x.startswith('REGISTRY_SLOT(')]
  slots=[x for x in self.files['test/data/averon_map_registry_slots.inc'].decode().splitlines() if x.startswith('REGISTRY_SLOT(')]
  self.assertEqual(slots[:len(oldslots)],oldslots);self.assertEqual(len(slots),len(oldslots)+44)
  for path in ('include/tilesets.h','src/data/tilesets/headers.h','src/data/tilesets/metatiles.h','data/event_scripts.s'):
   self.assertTrue(self.files[path].startswith(self.before[path]))
 def test_actual_room2_strip_recomposition_source_ids_unmodified_and_all_maps_fit(self):
  scene=self.recipe['scene'];self.assertEqual(len(scene),44)
  pieces=[self.files['data/layouts/'+scene['StarkRoom2'+p]['name']+'/map.bin'] for p in ('West','Center','East')]
  reconstructed=b''.join(b''.join(p[y*64:(y+1)*64] for p in pieces) for y in range(96))
  original=HERE.parent/'stark-mountain/staged/Room2/map.bin';self.assertEqual(reconstructed,original.read_bytes())
  ids={}
  for key,item in scene.items():
   h=json.loads(self.files['data/maps/'+item['name']+'/map.json']);ids[h['id']]=h
   w,height=item['dimensions'];self.assertLessEqual((w+15)*(height+14),10240)
   self.assertEqual(h['region_map_section'],'MAPSEC_ROUTE_201')
   self.assertEqual(item['source_section'],'MAPSEC_PENDING_OWNER')
  self.assertEqual(scene['StarkRoom1']['dimensions'],[64,32])
  for h in ids.values():
   for e in h['warp_events']:
    other=ids[e['dest_map']]['warp_events'][int(e['dest_warp_id'])]
    self.assertEqual(other['dest_map'],h['id'])
  self.assertNotIn('MAP_SINNOH_STARK_ROOM2',ids)
 def test_safe_family_prefix_sharing_and_unlinked_metadata_accounting(self):
  self.assertLess(self.recipe['secondary_metadata_bytes_after'],self.recipe['secondary_metadata_bytes_before'])
  for name,target in self.recipe['family_aliases'].items():
   source,graphics=m.FAMILIES[name];chosen,g2=m.FAMILIES[target];self.assertEqual(graphics,g2)
   for f in ('secondary-metatiles.bin','secondary-attributes.bin'):
    self.assertTrue((HERE.parent/chosen/f).read_bytes().startswith((HERE.parent/source/f).read_bytes()))
  self.assertGreater(self.recipe['verified_native_attribute_cells'],40000)
 def test_assembled_header_graph_is_one_component_without_foreign_links(self):
  heads={json.loads(v)['id']:json.loads(v) for p,v in self.files.items() if p.startswith('data/maps/') and p.endswith('/map.json')}
  self.assertEqual(len(heads),44)
  edges={k:{e['dest_map'] for e in h['warp_events']}|{e['map'] for e in h['connections'] or []} for k,h in heads.items()}
  todo=[next(iter(heads))];seen=set()
  for n in todo:
   if n in seen:continue
   seen.add(n)
   for other in edges[n]:
    self.assertIn(other,heads)
    if other not in seen:todo.append(other)
  self.assertEqual(seen,set(heads)) # header connectivity only, not Surf/foot acceptance
 def test_export_replays_and_existing_or_engine_outputs_refused(self):
  with tempfile.TemporaryDirectory() as t:
   out=Path(t)/'new';r=m.export(ROOT,out);self.assertEqual(r,self.recipe)
   for p,h in r['files'].items():self.assertEqual(m.base.sha((out/'overlay'/p).read_bytes()),h)
   with self.assertRaisesRegex(ValueError,'off-engine'):m.export(ROOT,out)
  with self.assertRaisesRegex(ValueError,'off-engine'):m.export(ROOT,ROOT/m.ENGINE/'bad')
 def test_dirty_source_and_non_disposable_install_refused_without_writes(self):
  original=Path.read_bytes;target=HERE.parent/'stark-mountain/staged/Room2/map.bin'
  def dirty(p):
   raw=original(p);return bytes([raw[0]^1])+raw[1:] if p==target else raw
  with tempfile.TemporaryDirectory() as t,patch.object(Path,'read_bytes',dirty):
   out=Path(t)/'never'
   with self.assertRaisesRegex(ValueError,'dirty'):m.export(ROOT,out)
   self.assertFalse(out.exists())
  with self.assertRaisesRegex(ValueError,'disposable'):m.install(ROOT)
if __name__=='__main__':unittest.main()
