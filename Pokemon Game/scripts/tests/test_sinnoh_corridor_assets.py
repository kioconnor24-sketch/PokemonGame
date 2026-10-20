"""Used-dependency proof rejects lossy maps; unrelated sheet differences are allowed."""
import copy
import importlib.util
from pathlib import Path
import struct
import unittest
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/jubilife-corridor'
s=importlib.util.spec_from_file_location('corridor_assets',ROOT/'adapt_existing_assets.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class UsedAssetTests(unittest.TestCase):
 def setUp(self):
  def bank(word):return [struct.pack('<8H',*([word]*8)),bytes(2),Image.new('P',(128,256)),[[(i*8,0,0) for i in range(16)] for p in range(16)]]
  self.source=[bank(0),bank(512|(6<<12))];self.target=copy.deepcopy(self.source);self.raw=struct.pack('<2H',0,512)
 def test_exact_two_bank_dependency_passes(self):self.assertEqual(m.compare(self.raw,self.source,self.target)['palettes'],[0,6])
 def test_changed_metatile_fails(self):
  self.target[1][0]=bytes(16)
  with self.assertRaisesRegex(ValueError,'metatile/attribute'):m.compare(self.raw,self.source,self.target)
 def test_changed_behavior_fails(self):
  self.target[1][1]=bytes([2,0])
  with self.assertRaisesRegex(ValueError,'metatile/attribute'):m.compare(self.raw,self.source,self.target)
 def test_changed_used_indexed_pixel_fails(self):
  self.target[1][2].putpixel((0,0),1)
  with self.assertRaisesRegex(ValueError,'indexed graphic'):m.compare(self.raw,self.source,self.target)
 def test_changed_used_palette_fails(self):
  self.target[1][3][6][0]=(248,248,248)
  with self.assertRaisesRegex(ValueError,'palette mismatch'):m.compare(self.raw,self.source,self.target)
 def test_unused_palette_and_tile_do_not_disqualify(self):
  self.target[0][3][4][0]=(248,248,248);self.target[0][2].putpixel((120,248),1)
  self.assertEqual(m.compare(self.raw,self.source,self.target)['graphic_tiles'],[0,512])
 def test_missing_target_record_fails(self):
  self.target[1][0]=b''
  with self.assertRaisesRegex(ValueError,'metatile/attribute'):m.compare(self.raw,self.source,self.target)
if __name__=='__main__':unittest.main()
