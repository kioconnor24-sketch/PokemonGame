"""Existing donor South geometry must be reused, not reauthored or silently reskinned."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/coronet-upper-floors'
s=importlib.util.spec_from_file_location('south_art_reuse',HERE/'reuse_south_art.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def words(raw):return struct.unpack('<%dH'%(len(raw)//2),raw)
class SouthArtReuseTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.out=Path(cls.temp.name)/'art';cls.receipt=m.build(ROOT/'Pokemon Game/engine',cls.out)
  cls.raw,cls.border,cls.header,cls.attrs=m.south_source()
 @classmethod
 def tearDownClass(cls):cls.temp.cleanup()
 def test_all1348_source_collision_elevation_and_full_attribute_words_preserved(self):
  a=m.load_packer();p=self.out/m.SOUTH;raw=(p/'averon-map.bin').read_bytes()+(p/'averon-border.bin').read_bytes()
  attrs=[(self.out/'cave-family/primary-attributes.bin').read_bytes(),(self.out/'cave-family/secondary-attributes.bin').read_bytes()]
  self.assertEqual(len(raw),1348*2)
  for old,new in zip(words(self.raw+self.border),words(raw)):
   self.assertEqual(old&0xfc00,new&0xfc00);bank,index=divmod(new&1023,512);self.assertEqual(a.pack.attribute(attrs[bank],index),self.attrs[str(old&1023)])
 def test_existing_three_cave_outputs_and_full_bank_prefix_remain_identical(self):
  old=HERE.parent/'celestic-north'
  for name in m.load_packer().MAPS:
   for file in ('averon-map.bin','averon-border.bin'):self.assertEqual((self.out/name/file).read_bytes(),(old/'staged'/name/file).read_bytes())
  for file in ('primary-metatiles.bin','primary-attributes.bin'):self.assertEqual((self.out/'cave-family'/file).read_bytes(),(old/'cave-family'/file).read_bytes())
  for file in ('secondary-metatiles.bin','secondary-attributes.bin'):self.assertTrue((self.out/'cave-family'/file).read_bytes().startswith((old/'cave-family'/file).read_bytes()))
  self.assertEqual(self.receipt['secondary_records'],38);self.assertEqual(self.receipt['remaining_secondary_slots'],474)
 def test_existing_ladder_and_quarantined_header_not_replaced_with_platinum_coordinates(self):
  raw=words((self.out/m.SOUTH/'averon-map.bin').read_bytes());word=raw[2*42+29];bank,index=divmod(word&1023,512)
  p=self.out/'cave-family'/('primary-attributes.bin' if bank==0 else 'secondary-attributes.bin')
  self.assertEqual(struct.unpack_from('<H',p.read_bytes(),index*2)[0],0x1061)
  self.assertEqual(word&0xfc00,0x3000);self.assertEqual(self.header['warp_events'],[])
  self.assertFalse((self.out/m.SOUTH/'map.json').exists());self.assertEqual(self.receipt['south_existing_stair'],[29,2])
  for path,h in json.loads((HERE/'reuse-existing-south.json').read_text())['staged_files_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),h)
 def test_only_reviewed_ocean_role_can_extend_existing_packer(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);facts=json.loads((HERE/'reuse-existing-south.json').read_text())
   for path in facts['staged_files_sha256']:
    dest=root/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,dest)
   rel=next(p for p in facts['staged_files_sha256'] if p.endswith('/attributes.json'));p=root/rel;attrs=json.loads(p.read_text());attrs['used_source_attribute_words']['649']=0x1000;p.write_text(json.dumps(attrs));facts['staged_files_sha256'][rel]=hashlib.sha256(p.read_bytes()).hexdigest()
   fixture=root/'inputs';fixture.mkdir();(fixture/'reuse-existing-south.json').write_text(json.dumps(facts))
   with patch.object(m,'HERE',fixture),self.assertRaisesRegex(ValueError,'unreviewed South water'):m.south_source(root)
 def test_changed_existing_geography_rejected_before_art_build(self):
  facts=copy.deepcopy(json.loads((HERE/'reuse-existing-south.json').read_text()));key=next(p for p in facts['staged_files_sha256'] if p.endswith('/map.bin'));facts['staged_files_sha256'][key]='0'*64
  with tempfile.TemporaryDirectory() as temp:
   folder=Path(temp);(folder/'reuse-existing-south.json').write_text(json.dumps(facts))
   with patch.object(m,'HERE',folder),self.assertRaisesRegex(ValueError,'South source hash'):m.south_source()
if __name__=='__main__':unittest.main()
