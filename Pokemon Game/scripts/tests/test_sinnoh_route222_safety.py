import importlib.util
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(os.environ['AVERON_TEST_SOURCE_ROOT']) if 'AVERON_TEST_SOURCE_ROOT' in os.environ else Path(__file__).resolve().parents[3]
HERE=Path(os.environ.get('AVERON_SAFETY_INPUTS',ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/route222-safety'))
ORIGINAL=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/sunyshore-coast'
sp=importlib.util.spec_from_file_location('repair',HERE/'repair_route222.py');r=importlib.util.module_from_spec(sp);sp.loader.exec_module(r)
sp=importlib.util.spec_from_file_location('runtime',HERE/'prepare_runtime.py');rt=importlib.util.module_from_spec(sp);sp.loader.exec_module(rt)
class RepairTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.out=Path(cls.tmp.name)/'packet';cls.receipt=r.build(ROOT,cls.out)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_exact_two_changed_cells_preserve_all_collision_elevation_and_four_boulders(self):
  for name in r.PINS:
   old=struct.unpack('<2944H',(ORIGINAL/'staged/Route222'/name).read_bytes());new=struct.unpack('<2944H',(self.out/name).read_bytes())
   self.assertEqual([(i%92,i//92,a,b) for i,(a,b) in enumerate(zip(old,new)) if a!=b],[(36,16,0x487,0x491),(37,16,0x487,0x491)])
   self.assertTrue(all(a&0xfc00==b&0xfc00 for a,b in zip(old,new)))
   for x in (36,37):
    for y in (17,18):self.assertEqual(old[y*92+x],new[y*92+x]);self.assertTrue(new[y*92+x]&0xc00)
 def test_corrected_faces_solid_nonjumping_and_adjacent_jumps_have_safe_landings(self):
  grid=struct.unpack('<2944H',(self.out/'averon-map.bin').read_bytes());attrs=(ROOT/'Pokemon Game/engine/data/tilesets/primary/general/metatile_attributes.bin').read_bytes()
  for x in (36,37):
   word=grid[16*92+x];self.assertEqual(word&0xc00,0x400);self.assertEqual(struct.unpack_from('<H',attrs,2*(word&1023))[0]&511,0)
  for x in (34,35,38,39):
   self.assertEqual(grid[16*92+x],0x487);self.assertFalse(grid[17*92+x]&0xc00);self.assertFalse(grid[18*92+x]&0xc00)
 def test_original_inputs_pristine_no_bank_or_identity_outputs(self):
  for n,h in r.PINS.items():self.assertEqual(r.sha((ORIGINAL/'staged/Route222'/n).read_bytes()),h)
  self.assertEqual({p.name for p in self.out.iterdir()},{'map.bin','averon-map.bin','averon.png','repair-receipt.json'})
  self.assertIn('NOT_RUNTIME_ACCEPTANCE',self.receipt['status'])
 def test_repeated_outputs_exact(self):
  with tempfile.TemporaryDirectory() as t:
   other=Path(t)/'packet';r.build(ROOT,other)
   self.assertEqual({p.name:p.read_bytes() for p in self.out.iterdir()},{p.name:p.read_bytes() for p in other.iterdir()})
 def test_changed_original_or_native_semantics_refused_before_output(self):
  original=Path.read_bytes
  for suffix in ('staged/Route222/map.bin','primary/general/metatile_attributes.bin'):
   def tamper(p):
    data=original(p)
    return bytes(len(data)) if str(p).endswith(suffix) else data
   with tempfile.TemporaryDirectory() as t,patch.object(Path,'read_bytes',tamper):
    out=Path(t)/'packet'
    with self.assertRaises(ValueError):r.build(ROOT,out)
    self.assertFalse(out.exists())
 def test_existing_and_engine_output_refused(self):
  with self.assertRaises(ValueError):r.build(ROOT,self.out)
  with tempfile.TemporaryDirectory() as t:
   with self.assertRaises(ValueError):r.build(ROOT,Path(t)/'engine/packet')
class RuntimeTests(unittest.TestCase):
 def test_only_one_engine_map_diff_no_banks_ids_or_other_terrain(self):
  before,old=rt.coast.assemble(ROOT);after,receipt=rt.assemble(ROOT)
  self.assertEqual(set(after)-set(before),{'test/averon_route222_safety_runtime.c'})
  self.assertEqual({p for p in before if before[p]!=after[p]},{'data/layouts/Route222/map.bin'})
  self.assertEqual(len(after),33);self.assertEqual(receipt['base'],rt.BASE)
  self.assertEqual(receipt['existing_map_names_preserved'],old['existing_map_names_preserved'])
 def test_tampered_candidate_refused(self):
  original=Path.read_bytes
  def changed(p):
   raw=original(p)
   return bytes(len(raw)) if p==HERE/'corrected/averon-map.bin' else raw
  with patch.object(Path,'read_bytes',changed),self.assertRaisesRegex(ValueError,'tested corrected route'):rt.assemble(ROOT)
 def test_production_wrong_base_dirty_and_path_escape_refused(self):
  with self.assertRaisesRegex(ValueError,'explicit disposable'):rt.install(ROOT)
  with tempfile.TemporaryDirectory() as t:
   repo=Path(t);engine=repo/rt.ENGINE;engine.mkdir(parents=True);(engine/'.map_qa_throwaway').touch()
   def baseline(repo,*args):
    if args[0]=='branch':return b'codex/route222-safety-runtime-scratch-test\n'
    if args[0]=='rev-parse':return (rt.BASE+'\n').encode()
    return b''
   def wrong(repo,*args):return b'0'*40 if args[0]=='rev-parse' else baseline(repo,*args)
   with patch.object(rt.base,'git',side_effect=wrong),self.assertRaisesRegex(ValueError,'exact production baseline'):rt.install(repo)
   def dirty(repo,*args):return b' M engine/src/save.c\n' if args[0]=='status' else baseline(repo,*args)
   with patch.object(rt.base,'git',side_effect=dirty),self.assertRaisesRegex(ValueError,'dirty runtime source'):rt.install(repo)
   with patch.object(rt.base,'git',side_effect=baseline),patch.object(rt,'assemble',return_value=({'../escape':b'x'},{})),self.assertRaisesRegex(ValueError,'escapes engine'):rt.install(repo)
   self.assertEqual([p.name for p in engine.iterdir()],['.map_qa_throwaway'])
if __name__=='__main__':unittest.main()

