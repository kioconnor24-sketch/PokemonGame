"""Actual pinned upper rail cells, isolated from graphical runtime acceptance."""
import copy,importlib.util
from pathlib import Path
from unittest import mock
import unittest
# Historical DEV/source receipt replay uses its exact accepted checkout.
# Production installer tests remain bound to the current checkout.
from sinnoh_replay_fixture import post_c_source_root
ROOT = post_c_source_root(Path(__file__).resolve().parents[3])

HERE=(ROOT/'Pokemon Game')/'Averon_Codex_Handoff/design/sinnoh/eastern-loop'
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
upper=load('upper_scenario',HERE/'run_upper_rail_probe.py');a=load('upper_assembler',HERE/'prepare_runtime.py')


class UpperTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.files,_=a.assemble(ROOT);cls.md=load('upper_maps',HERE.parents[3]/'scripts/claude_play/mapdata.py')
 def world(self):
  e=ROOT/a.ENGINE;read_text=Path.read_text;read_bytes=Path.read_bytes
  def lookup(p):
   try:return self.files.get(str(p.relative_to(e)))
   except ValueError:return None
  def text(p,*args,**kwargs):
   v=lookup(p);return v.decode() if v is not None else read_text(p,*args,**kwargs)
  def binary(p):
   v=lookup(p);return v if v is not None else read_bytes(p)
  with mock.patch.object(Path,'read_text',new=text),mock.patch.object(Path,'read_bytes',new=binary):return self.md.World(e).map('MAP_ROUTE212_SOUTH')
 def test_real17_cell_track_keeps12_multilevel_cells_and_upper4_endpoints(self):
  m=self.world();p=upper.track(m);self.assertEqual((p[0],p[-1],len(p)),((43,11),(27,11),17));self.assertEqual(sum(m.elevation(*q)==15 for q in p),12);self.assertIsNotNone(upper.common.elevation_path(m,(36,12),{(43,11)},start_elevation=3));self.assertIsNotNone(upper.common.elevation_path(m,(43,11),{(36,12)},start_elevation=4))
 def test_changed_collision_height_or_behavior_is_rejected(self):
  original=self.world()
  for mode in ('collision','height','behavior'):
   m=copy.copy(original);m.blocks=list(original.blocks);m.behaviors=list(original.behaviors);i=11*m.width+36
   if mode=='collision':m.blocks[i]|=0x400
   elif mode=='height':m.blocks[i]=(m.blocks[i]&0xFFF)|0x3000
   else:m.behaviors[i]='MB_OCEAN_WATER'
   with self.subTest(mode=mode),self.assertRaisesRegex(ValueError,'track changed'):upper.track(m)
 def test_wrong_map_or_clipped_width_cannot_be_used_as_an_upper_fixture(self):
  for mode in ('map','width'):
   m=self.world()
   if mode=='map':m.id='MAP_ROUTE201'
   else:m.width=30
   with self.subTest(mode=mode),self.assertRaises(ValueError):upper.track(m)
 def test_readonly_track_validation_never_changes_source_arrays(self):
  m=self.world();before=(tuple(m.blocks),list(m.behaviors));self.assertEqual(upper.track(m),upper.track(m));self.assertEqual(before,(tuple(m.blocks),list(m.behaviors)))
if __name__=='__main__':unittest.main()
