"""Structural comparisons remain distinct from visual and gameplay acceptance."""
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/'sinnoh-donor-bank-audit.py'
spec=importlib.util.spec_from_file_location('bank_audit',SCRIPT)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class BankAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.donor=self.root/'donor';self.engine=self.root/'destination'
        layouts=[]
        for name in ('Route202','VerityLakefront','LakeVerity'):
            p=self.donor/'data/layouts'/name/'map.bin';p.parent.mkdir(parents=True)
            p.write_bytes(struct.pack('<3H',0x1400,0x2401,0x3400|512))
            h=self.donor/'data/maps'/name/'map.json';h.parent.mkdir(parents=True)
            h.write_text(json.dumps({'id':'MAP_'+name.upper(),'layout':'LAYOUT_CUSTOM_'+name.upper()}))
            layouts.append({'id':'LAYOUT_CUSTOM_'+name.upper(),'blockdata_filepath':'data/layouts/'+name+'/map.bin','width':3,'height':1,
                            'primary_tileset':'gTileset_General','secondary_tileset':'gTileset_Petalburg'})
        (self.donor/'data/layouts/layouts.json').write_text(json.dumps({'layouts':layouts}))
        for root in (self.donor,self.engine):
            for group,count in [('primary/general',2),('secondary/petalburg',1),('secondary/dewford',1)]:
                p=root/'data/tilesets'/group;p.mkdir(parents=True)
                (p/'metatiles.bin').write_bytes(bytes(16*count))
                (p/'metatile_attributes.bin').write_bytes(bytes(2*count))
                (p/'tiles.png').write_bytes(b'donor' if root==self.donor else b'different destination')

    def test_all_three_maps_and_per_record_cells(self):
        for name in ('Route202','VerityLakefront','LakeVerity'):
            r=m.audit(self.donor,self.engine,name)
            self.assertEqual((r['primary_cells'],r['secondary_cells']),(2,1))
            self.assertEqual([v['id'] for v in r['used_records']],[0,1,512])
            self.assertTrue(all(v['cells']==1 for v in r['used_records']))
            self.assertFalse(r['banks'][0]['graphics_png_sha256_equal'])
            self.assertTrue(r['used_records'][2]['same_index_record_and_attribute'])

    def test_dewford_option_compares_requested_destination(self):
        p=self.engine/'data/tilesets/secondary/dewford/metatile_attributes.bin';p.write_bytes(struct.pack('<H',2))
        r=m.audit(self.donor,self.engine,'LakeVerity','dewford')
        self.assertEqual(r['banks'][1]['destination_family'],'secondary/dewford')
        self.assertEqual(r['used_records'][2]['matching_destination_ids'],[])
        self.assertTrue(m.audit(self.donor,self.engine,'LakeVerity')['used_records'][2]['same_index_record_and_attribute'])

    def test_unavailable_target_index_reported(self):
        p=self.engine/'data/tilesets/secondary/petalburg';(p/'metatiles.bin').write_bytes(b'');(p/'metatile_attributes.bin').write_bytes(b'')
        r=m.audit(self.donor,self.engine,'VerityLakefront')
        self.assertEqual(r['banks'][1]['out_of_destination_range'],1)
        self.assertFalse(r['used_records'][2]['destination_index_available'])

    def test_cli_verity_is_supported(self):
        for name in ('VerityLakefront','LakeVerity'):
            r=subprocess.run([sys.executable,str(SCRIPT),'--donor-root',str(self.donor),'--engine-root',str(self.engine),'--map',name],capture_output=True,text=True,check=True)
            self.assertEqual(json.loads(r.stdout)['source_map'],name)

    def test_unsupported_paths_and_family_rejected(self):
        for name,family in [('../escape','petalburg'),('LakeVerity','../escape')]:
            with self.assertRaisesRegex(ValueError,'unsupported'):m.audit(self.donor,self.engine,name,family)

    def test_missing_source_record_refused(self):
        p=self.donor/'data/layouts/LakeVerity/map.bin';p.write_bytes(struct.pack('<3H',0,1,513))
        with self.assertRaisesRegex(ValueError,'absent donor metatile'):m.audit(self.donor,self.engine,'LakeVerity')

    def test_malformed_bank_refused(self):
        p=self.donor/'data/tilesets/primary/general/metatiles.bin';p.write_bytes(bytes(17))
        with self.assertRaisesRegex(ValueError,'invalid metatile bank'):m.audit(self.donor,self.engine,'LakeVerity')

if __name__=='__main__':unittest.main()
