import importlib.util,json,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parents[3]/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/coast-coronet-combined/prepare_runtime.py'
s=importlib.util.spec_from_file_location('combined',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Combined(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.files,cls.receipt=m.assemble(m.SOURCE_ROOT)
 def test_original19_and_all14_appended_only(self):
  g=json.loads(self.files['data/maps/map_groups.json'])['gMapGroup_Sinnoh']
  self.assertEqual(len(g),33);self.assertEqual(g[:19],self.receipt['existing_map_names_preserved']);self.assertEqual(len(set(g)),33)
  self.assertEqual(list(self.receipt['temporary_map_slots'].values()),list(range(19,33)))
 def test_exact_published_repair_and_every_other_terrain_unchanged(self):
  for path,h in self.receipt['source_league_files'].items():
   if path.startswith('data/layouts/') and path.endswith('.bin') and path!='data/layouts/Route222/map.bin':self.assertEqual(m.load('coast_hash','coronet-ascent/prepare_runtime.py').sha(self.files[path]),h)
  self.assertEqual(self.receipt['repair_changed_cells'],[1508,1509])
  self.assertEqual(m.load('ascent_hash','coronet-ascent/prepare_runtime.py').sha(self.files['data/layouts/Route222/map.bin']),'d72e2575f7503746f8ba2e404696b217ee9f66e60d1995dc6a26e22fc22d7d36')
 def test_every_ascent_payload_unchanged_except_fixture_indices(self):
  helper=m.load('ascent_hash','coronet-ascent/prepare_runtime.py')
  for path,h in self.receipt['source_ascent_files'].items():
   if path.startswith(('data/maps/Sinnoh','data/layouts/Sinnoh')):self.assertEqual(helper.sha(self.files[path]),h)
  self.assertIn(b'MAP_NUM(maps[i]),27+i',self.files['test/averon_coronet_ascent_runtime.c'])
  self.assertNotIn(b'p->mapNum>=19',self.files['test/averon_coronet_ascent_runtime.c'])
 def test_all_warps_reciprocal_and_no_invented_cross_cluster_links(self):
  headers=[json.loads(raw) for p,raw in self.files.items() if p.startswith('data/maps/') and p.endswith('/map.json')]
  byid={h['id']:h for h in headers};count=0
  for h in headers:
   self.assertEqual(h['region_map_section'],'MAPSEC_ROUTE_201')
   for key in ('object_events','coord_events','bg_events'):self.assertEqual(h[key],[])
   for i,p in enumerate(h['warp_events']):
    other=byid[p['dest_map']]['warp_events'][int(p['dest_warp_id'])]
    self.assertEqual((other['dest_map'],int(other['dest_warp_id'])),(h['id'],i));count+=1
    if 'CORONET' in h['id']:self.assertIn('CORONET',p['dest_map'])
  self.assertEqual(count,38) # coast6 + connected Victory14 + Coronet18
 def test_fixture_counts_scripts_layouts_and_no_saved_encoding(self):
  layouts=json.loads(self.files['data/layouts/layouts.json'])['layouts'];self.assertEqual(len({x['id'] for x in layouts}),len(layouts))
  script=self.files['data/event_scripts.s']
  for n in self.receipt['temporary_map_slots']:self.assertEqual(script.count(('"data/maps/'+n+'/scripts.inc"').encode()),1)
  self.assertFalse(any(p.startswith(('src/save','include/constants/region_map_sections')) or p.endswith(('.sav','.gba','.elf')) for p in self.files))
 def test_unknown_original_repair_input_rejected(self):
  load=m.load
  def corrupt(name,path):
   module=load(name,path)
   if name=='combined_league':
    old=module.assemble
    def altered(repo):
     files,receipt=old(repo);p='data/layouts/Route222/map.bin';raw=bytearray(files[p]);raw[0]^=1;files[p]=bytes(raw);return files,receipt
    module.assemble=altered
   return module
  with patch.object(m,'load',side_effect=corrupt),self.assertRaisesRegex(ValueError,'exact two published'):m.assemble(m.SOURCE_ROOT)
 def test_shallow_source_replay_needs_no_historical_base_or_repair_objects(self):
  load=m.load;guards=[]
  def current_only(name,path):
   module=load(name,path)
   if name=='combined_ascent':
    old=module.base.git;guards.append((module.base,old))
    def git(repo,*args):
     self.assertFalse(any(m.BASE+':' in str(a) or m.REPAIR+':' in str(a) for a in args))
     return old(repo,*args)
    module.base.git=git
   return module
  try:
   with patch.object(m,'load',side_effect=current_only):files,receipt=m.assemble(m.SOURCE_ROOT)
   self.assertEqual(files,self.files)
  finally:
   for guard,old in guards:guard.git=old
 def test_install_refuses_public_wrong_base_dirty_and_path_escape_before_writes(self):
  import tempfile
  from types import SimpleNamespace
  with self.assertRaisesRegex(ValueError,'marked disposable'):m.install(m.SOURCE_ROOT)
  with tempfile.TemporaryDirectory() as temp:
   repo=Path(temp);engine=repo/m.ENGINE;engine.mkdir(parents=True);(engine/'.map_qa_throwaway').touch()
   def clean(repo,*args):
    if args[0]=='branch':return b'codex/coast-coronet-runtime-scratch-test\n'
    if args[0]=='rev-parse':return (m.BASE+'\n').encode()
    return b''
   for mode,message in [('base','exact production'),('dirty','dirty runtime'),('escape','escapes engine')]:
    def git(repo,*args):
     if mode=='base' and args[0]=='rev-parse':return b'0'*40+b'\n'
     if mode=='dirty' and args[0]=='status':return b' M Pokemon Game/engine/src/save.c\n'
     return clean(repo,*args)
    guard=SimpleNamespace(base=SimpleNamespace(git=git))
    with patch.object(m,'load',return_value=guard),patch.object(m,'assemble',return_value=({'../escape':b'x'},{})),self.assertRaisesRegex(ValueError,message):m.install(repo)
   self.assertEqual([p.name for p in engine.iterdir()],['.map_qa_throwaway'])
if __name__=='__main__':unittest.main()
