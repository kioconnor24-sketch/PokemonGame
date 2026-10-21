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
