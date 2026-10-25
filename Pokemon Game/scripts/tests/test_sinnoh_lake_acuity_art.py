"""Reused Lake Acuity geography, complete physics and native-art closure tests."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/lake-acuity'
s=importlib.util.spec_from_file_location('acuity_art_test',HERE/'adapt_art.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class LakeAcuityArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data,cls.header,cls.attrs,cls.pin=m.source(ROOT)
        cls.receipt=json.loads((HERE/'art-receipt.json').read_text())

    def test_exact_original_geography_and_every_full_attribute_survives(self):
        self.assertEqual(hashlib.sha256(self.data['map.bin']).hexdigest(),'f1a7e4890fc4d0d846960645a07df4f48748abc5204794fbc715f447dd69df68')
        before=self.data['map.bin']+self.data['border.bin']
        after=(HERE/'LakeAcuity/averon-map.bin').read_bytes()+(HERE/'LakeAcuity/averon-border.bin').read_bytes()
        pa=(HERE/'outdoor-family/primary-attributes.bin').read_bytes();sa=(HERE/'outdoor-family/secondary-attributes.bin').read_bytes()
        count=0
        for (old,),(new,) in zip(struct.iter_unpack('<H',before),struct.iter_unpack('<H',after)):
            self.assertEqual(old&0xfc00,new&0xfc00)
            bank,i=divmod(new&1023,512)
            self.assertEqual(m.pack.attribute((pa,sa)[bank],i),self.attrs[str(old&1023)]);count+=1
        self.assertEqual(count,2500);self.assertEqual(len(before),len(after))

    def test_source_stays_disconnected_no_ids_story_or_runtime_claim(self):
        self.assertEqual(self.header['region_map_section'],'MAPSEC_PENDING_OWNER')
        for k in ('object_events','coord_events','bg_events','warp_events','connections'):self.assertFalse(self.header[k])
        self.assertIn('NO_RUNTIME_OR_PRODUCTION_ACCEPTANCE',self.receipt['status'])
        self.assertFalse(any(p.suffix in ('.gba','.sav','.elf') for p in HERE.rglob('*')))
        self.assertEqual(self.receipt['secondary_records'],9);self.assertEqual(self.receipt['remaining_secondary_slots'],503)

    def test_water_layer_words_and_sand_are_preserved_not_just_low_behavior(self):
        source_words={self.attrs[str(v[0]&1023)] for v in struct.iter_unpack('<H',self.data['map.bin'])}
        self.assertTrue({0x1010,0x2010,0x21}<=source_words)
        pa=(HERE/'outdoor-family/primary-attributes.bin').read_bytes();sa=(HERE/'outdoor-family/secondary-attributes.bin').read_bytes()
        target_words={m.pack.attribute((pa,sa)[v[0]&1023>=512],v[0]%512) for v in struct.iter_unpack('<H',(HERE/'LakeAcuity/averon-map.bin').read_bytes())}
        self.assertEqual(source_words,target_words)

    def test_real_native_build_replays_outputs_and_all_assets_are_pinned(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'new'
            receipt=m.build(ROOT/'Pokemon Game/engine',out)
            self.assertEqual(json.loads(json.dumps(receipt)),self.receipt)
            for path,h in receipt['output_sha256'].items():
                raw=(out/path).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),h);self.assertEqual(raw,(HERE/path).read_bytes())
        for path,h in self.receipt['native_asset_sha256'].items():
            self.assertEqual(hashlib.sha256(m.base.verified_file(ROOT,Path('Pokemon Game/engine')/path,'HEAD')).hexdigest(),h)

    def test_corrupt_source_or_uncovered_attribute_and_in_engine_output_refused(self):
        original=m.base.verified_file
        def corrupt(repo,path,rev):
            raw=original(repo,path,rev)
            if str(path).endswith('remaining-donor/staged/LakeAcuity/map.bin'):return bytes([raw[0]^1])+raw[1:]
            return raw
        with patch.object(m.base,'verified_file',side_effect=corrupt):
            with self.assertRaisesRegex(ValueError,'identity'):m.source(ROOT)
        def uncovered(repo,path,rev):
            raw=original(repo,path,rev)
            if str(path).endswith('remaining-donor/staged/LakeAcuity/attributes.json'):
                d=json.loads(raw);d['used_source_attribute_words'].pop('513');return json.dumps(d).encode()
            return raw
        with patch.object(m.base,'verified_file',side_effect=uncovered):
            with self.assertRaisesRegex(ValueError,'coverage'):m.source(ROOT)
        with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ROOT/'Pokemon Game/engine',ROOT/'Pokemon Game/engine/bad-output')

if __name__=='__main__':unittest.main()
