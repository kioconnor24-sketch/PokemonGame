"""Finished off-engine candidate boundaries; no production map mutations."""
import importlib.util
import json
from pathlib import Path
import struct
import unittest
ROOT=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/jubilife-corridor'
s=importlib.util.spec_from_file_location('overlay',ROOT/'prepare_engine_overlay.py')
o=importlib.util.module_from_spec(s);s.loader.exec_module(o)
class OverlayTests(unittest.TestCase):
 def test_gate_repairs_are_exactly_five_cells(self):
  original=(ROOT/'averon-adapted/OreburghGate_1F/map.bin').read_bytes()
  a=struct.unpack('<783H',original);b=struct.unpack('<783H',o.finish_gate(original))
  self.assertEqual({(i%29,i//29) for i in range(783) if a[i]!=b[i]}, {(19,5),(25,20),(24,21),(25,21),(26,21)})
  self.assertEqual(b[5*29+19],a[4*29+19])
  self.assertEqual(b[20*29+25],a[4*29+19])
  for x in (24,25,26):
   self.assertEqual(b[21*29+x],a[21*29+23]);self.assertEqual((b[21*29+x]>>10)&3,1)
 def test_center_escalator_removal_preserves_both_real_doors(self):
  raw=(ROOT/'averon-adapted/JubilifeCity_PokemonCenter_1F/map.bin').read_bytes();a=struct.unpack('<126H',raw);b=struct.unpack('<126H',o.finish_center(raw))
  self.assertEqual({(i%14,i//14) for i in range(126) if a[i]!=b[i]}, {(0,5),(1,5),(0,6),(1,6),(0,7),(1,7),(2,6)})
  for y in (5,6,7):
   self.assertEqual(b[y*14],a[4*14]);self.assertEqual(b[y*14+1],a[5*14+2])
  for x in (6,7):self.assertEqual(b[8*14+x],a[8*14+x])
 def test_changed_center_source_rejected(self):
  raw=bytearray((ROOT/'averon-adapted/JubilifeCity_PokemonCenter_1F/map.bin').read_bytes());raw[(6*14+1)*2]=0
  with self.assertRaisesRegex(ValueError,'source changed'):o.finish_center(raw)
 def test_committed_center_matches_generator(self):
  self.assertEqual((ROOT/'engine-overlay/data/layouts/JubilifeCity_PokemonCenter_1F/map.bin').read_bytes(),o.finish_center((ROOT/'averon-adapted/JubilifeCity_PokemonCenter_1F/map.bin').read_bytes()))
 def test_changed_gate_source_rejected(self):
  raw=bytearray((ROOT/'averon-adapted/OreburghGate_1F/map.bin').read_bytes());raw[(5*29+19)*2]=0
  with self.assertRaisesRegex(ValueError,'source changed'):o.finish_gate(raw)
 def test_committed_gate_matches_generator(self):
  self.assertEqual((ROOT/'engine-overlay/data/layouts/OreburghGate_1F/map.bin').read_bytes(),o.finish_gate((ROOT/'averon-adapted/OreburghGate_1F/map.bin').read_bytes()))
 def test_headers_have_existing_music_and_no_gameplay_events(self):
  for name,music in o.MUSIC.items():
   h=json.loads((ROOT/'engine-overlay/data/maps'/name/'map.json').read_text());self.assertEqual(h['music'],music);self.assertNotEqual(music,'MUS_DUMMY')
   for key in ('object_events','coord_events','bg_events'):self.assertEqual(h[key],[])
 def test_source_pin_and_approved_sections(self):
  f=json.loads((ROOT/'engine-overlay/registration-fragments.json').read_text())
  self.assertEqual(f['route202_header_patch']['expected_source_head'],o.ROUTE202_HEAD)
  self.assertEqual([s['value'] for s in f['append_sections']],[221,222,223])
if __name__=='__main__':unittest.main()
