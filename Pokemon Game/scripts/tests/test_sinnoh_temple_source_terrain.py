"""Strict DS metadata bounds/identity tests; no models or game acceptance."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
HERE=Path(__file__).resolve().parents[3]/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/snowpoint-temple-core'
s=importlib.util.spec_from_file_location('temple_terrain',HERE/'read_source_terrain.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

def fixture(words=None):
    words=[0]*1024 if words is None else words
    return struct.pack('<4I',2048,4,5,3)+struct.pack('<1024H',*words)+b'PROP'+b'MODEL'+b'XYZ'

class SourceTerrainTests(unittest.TestCase):
    def test_little_endian_flags_ice_and_opaque_sections(self):
        data=[0]*1024;data[35]=0x8020;data[100]=8
        words,d=m.decode(fixture(data));self.assertEqual(words[35],0x8020)
        self.assertEqual(d['ice_coordinates'],[[3,1]]);self.assertEqual(d['collision_bit_tiles'],1)
        self.assertEqual(d['opaque_section_bytes'],dict(props=4,model=5,bdhc=3));self.assertFalse(d['models_or_textures_emitted']);self.assertFalse(d['full_walkability_accepted'])

    def test_truncated_header_sections_or_trailing_data_rejected(self):
        raw=fixture()
        for candidate in (raw[:12],raw[:-1],raw+b'X'):
            with self.assertRaisesRegex(ValueError,'header|length'):m.decode(candidate)

    def test_wrong_grid_or_missing_opaque_section_rejected(self):
        raw=fixture()
        for header in ((1024,4,5,3),(2048,4,0,8),(2048,4,8,0)):
            with self.assertRaisesRegex(ValueError,'terrain|absent'):m.decode(struct.pack('<4I',*header)+raw[16:])

    def test_unreviewed_flags_and_behavior_fail_closed(self):
        for value in (0x0100,0xfe):
            cells=[0]*1024;cells[500]=value
            with self.assertRaisesRegex(ValueError,'flag|behavior'):m.decode(fixture(cells))

    def test_identity_blob_and_input_escape_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);raw=fixture();(root/'input.bin').write_bytes(raw)
            identity=dict(private_input_name='input.bin',bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),git_blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest())
            manifest=dict(revision='fixture',floors={'floor':identity})
            self.assertEqual(m.audit(root,manifest)['total_terrain_words'],1024)
            for field,value,error in [('bytes',1,'identity'),('git_blob','bad','blob'),('private_input_name','../outside','escapes')]:
                broken=copy.deepcopy(manifest);broken['floors']['floor'][field]=value
                with self.assertRaisesRegex(ValueError,error):m.audit(root,broken)

    def test_actual_checked_audit_is_source_only_and_pins_all_six_floors(self):
        d=json.loads((HERE/'terrain-audit.json').read_text());pins=json.loads((HERE/'terrain-source-identities.json').read_text())
        self.assertEqual(d['total_terrain_words'],6144);self.assertEqual(d['total_ice_tiles'],338)
        self.assertEqual([len(v['ice_coordinates']) for v in d['floors'].values()],[7,14,2,106,1,208])
        self.assertEqual([v['matrix'] for v in pins['floors'].values()],list(range(68,74)))
        for floor,v in d['floors'].items():self.assertFalse(v['full_walkability_accepted']);self.assertEqual(v['source_identity'],pins['floors'][floor])

if __name__=='__main__':unittest.main()
