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
 def test_export_does_not_require_unfetched_side_branch_baseline_object(self):
  original=m.base.git
  def shallow(repo,*args):
   if any(m.BASE in str(arg) for arg in args):raise AssertionError('BASE side-branch object unavailable in shallow CI checkout')
   return original(repo,*args)
  with patch.object(m.base,'git',shallow):
   files,r=m.assemble(ROOT)
  self.assertEqual(files,self.files);self.assertEqual(r['base_engine_tree'],m.ENGINE_TREE)
 def marked_metadata_fixture(self,path):
  engine=path/m.ENGINE
  for rel in set(self.recipe['base_input_sha256'])|set(self.recipe['native_input_sha256']):
   target=engine/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/m.ENGINE/rel).read_bytes())
  (engine/'.map_qa_throwaway').write_text('isolated unit fixture; Git state is stubbed')
  original=m.base.git
  def fixture_git(repo,*args):
   if Path(repo).resolve()==path.resolve():
    if args==('branch','--show-current'):return b'codex/battle-frontier-runtime-scratch-unit'+bytes([10])
    if args==('rev-parse','HEAD'):return (m.BASE+chr(10)).encode()
    if args and args[0]=='status':return b'?? "Pokemon Game/engine/.map_qa_throwaway"'+bytes([10])
    return original(ROOT,*args) # real immutable blobs, simulated target Git state
   return original(repo,*args)
  return engine,fixture_git
 def test_installer_filesystem_replay_with_pinned_blobs_and_stubbed_git_state(self):
  with tempfile.TemporaryDirectory() as t:
   target=Path(t);engine,git=self.marked_metadata_fixture(target)
   with patch.object(m.base,'git',git):r=m.install(target)
   self.assertEqual(r,self.recipe)
   for p,h in r['files'].items():self.assertEqual(m.base.sha((engine/p).read_bytes()),h)
   for p,h in r['native_input_sha256'].items():
    if p not in r['files']:self.assertEqual(m.base.sha((engine/p).read_bytes()),h)
 def test_installer_refuses_ignored_existing_asset_and_path_escape_before_writing(self):
  with tempfile.TemporaryDirectory() as t:
   target=Path(t);engine,git=self.marked_metadata_fixture(target)
   path=next(p for p in self.files if p.startswith('data/tilesets/secondary/') and p.endswith('/metatiles.bin'))
   asset=engine/path;asset.parent.mkdir(parents=True);asset.write_bytes(b'preexisting user asset')
   before=(engine/'data/maps/map_groups.json').read_bytes()
   with patch.object(m.base,'git',git):
    with self.assertRaisesRegex(ValueError,'existing untracked'):m.install(target)
   self.assertEqual(asset.read_bytes(),b'preexisting user asset')
   self.assertEqual((engine/'data/maps/map_groups.json').read_bytes(),before)
   outside=target/'Pokemon Game/outside.txt';outside.write_text('preserve')
   with patch.object(m.base,'git',git),patch.object(m,'assemble',return_value=({'../outside.txt':b'bad'},self.recipe)):
    with self.assertRaisesRegex(ValueError,'escapes engine'):m.install(target)
   self.assertEqual(outside.read_text(),'preserve')
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
