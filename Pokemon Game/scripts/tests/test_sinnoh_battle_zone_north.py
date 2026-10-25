"""Four-map geometry/art/connection preservation; no runtime acceptance claim."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3];ENGINE=ROOT/'Pokemon Game/engine'
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/battle-zone-north'
s=importlib.util.spec_from_file_location('battle_zone_test',HERE/'adapt_art.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class NorthernArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=json.loads((HERE/'source-receipt.json').read_text())
        cls.raw={n:(m.SOURCE/'staged'/n/'map.bin').read_bytes() for n in m.MAPS}
        cls.adapted={n:(HERE/'staged'/n/'averon-map.bin').read_bytes() for n in m.MAPS}

    def test_all10128_cells_keep_collision_elevation_and_full_behavior_words(self):
        pa=(HERE/'outdoor-family/primary-attributes.bin').read_bytes();sa=(HERE/'outdoor-family/secondary-attributes.bin').read_bytes();count=0
        for n in m.MAPS:
            source=m.SOURCE/'staged'/n;target=HERE/'staged'/n
            before=self.raw[n]+(source/'border.bin').read_bytes();after=self.adapted[n]+(target/'averon-border.bin').read_bytes()
            self.assertEqual(len(before),len(after));attrs=json.loads((source/'attributes.json').read_text())['used_source_attribute_words']
            for (a,),(b,) in zip(struct.iter_unpack('<H',before),struct.iter_unpack('<H',after)):
                self.assertEqual(a&0xfc00,b&0xfc00);bank,i=divmod(b&1023,512)
                self.assertEqual(m.pack.attribute((pa,sa)[bank],i),attrs[str(a&1023)]);count+=1
        self.assertEqual(count,10128)
        self.assertEqual(self.receipt['elevation15_preserved'],dict(Route225=52,SurvivalArea=0,Route226=0,Route227=21))

    def test_all_six_reciprocal_seam_directions_and36_lanes_are_identical(self):
        before=m.seam_audit(self.raw);after=m.seam_audit(self.adapted)
        self.assertEqual(before,after);self.assertEqual(after,self.receipt['source_seams'])
        self.assertEqual([len(v['compatible_lanes']) for v in after],[3,3,5,5,10,10])
        self.assertEqual([v['offset'] for v in after],[0,0,0,0,56,-56])
        self.assertEqual(sum(len(v['compatible_lanes']) for v in after),36)

    def test_blocked_seam_and_wrong_reciprocal_offset_rejected(self):
        bad=dict(self.adapted);raw=bytearray(bad['Route225'])
        for y in range(94):
            i=2*(y*32+31);struct.pack_into('<H',raw,i,struct.unpack_from('<H',raw,i)[0]|0xc00)
        bad['Route225']=bytes(raw)
        with self.assertRaisesRegex(ValueError,'no compatible'):m.seam_audit(bad)
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for n in m.MAPS:
                p=root/'staged'/n;p.mkdir(parents=True)
                header=json.loads((m.SOURCE/'staged'/n/'map.json').read_text())
                if n=='SurvivalArea':header['connections'][0]['offset']=1
                (p/'map.json').write_text(json.dumps(header))
            with patch.object(m,'SOURCE',root):
                with self.assertRaisesRegex(ValueError,'nonreciprocal'):m.seam_audit(self.adapted)

    def test_actual_native_build_replays_every_output_and_primary_is_unchanged(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'fresh';receipt=m.build(ENGINE,out)
            self.assertEqual(json.loads(json.dumps(receipt)),self.receipt)
            for path,h in receipt['output_sha256'].items():
                raw=(out/path).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),h);self.assertEqual(raw,(HERE/path).read_bytes())
        self.assertEqual((HERE/'outdoor-family/primary-metatiles.bin').read_bytes(),(ENGINE/'data/tilesets/primary/general/metatiles.bin').read_bytes())
        self.assertEqual((HERE/'outdoor-family/primary-attributes.bin').read_bytes(),(ENGINE/'data/tilesets/primary/general/metatile_attributes.bin').read_bytes())
        self.assertEqual(self.receipt['secondary_records'],67);self.assertEqual(self.receipt['remaining_secondary_slots'],445)

    def test_corrupt_source_and_unreviewed_secondary_graphics_are_rejected(self):
        original=m.base.verified_file
        def corrupt(repo,path,rev):
            raw=original(repo,path,rev)
            if str(path).endswith('staged/Route225/map.bin'):return bytes([raw[0]^1])+raw[1:]
            return raw
        with patch.object(m.base,'verified_file',side_effect=corrupt):
            with self.assertRaisesRegex(ValueError,'pinned source'):m.verify_source(ROOT)
        bad=dict(m.existing.templates.SECONDARY['Route225']);bad.pop(next(iter(bad)))
        with tempfile.TemporaryDirectory() as t,patch.dict(m.existing.templates.SECONDARY,Route225=bad):
            out=Path(t)/'never-created'
            with self.assertRaisesRegex(ValueError,'unreviewed secondary'):m.build(ENGINE,out)
            self.assertFalse(out.exists())

    def test_no_content_ids_donor_art_or_gameplay_claim_and_correct_facade_bounds(self):
        for n in m.MAPS:
            h=json.loads((m.SOURCE/'staged'/n/'map.json').read_text())
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
            for k in ('object_events','coord_events','bg_events','warp_events'):self.assertFalse(h[k])
        self.assertIn('NOT_RUNTIME_ACCEPTANCE',self.receipt['status'])
        self.assertFalse(any(p.suffix in ('.gba','.sav','.elf') for p in HERE.rglob('*')))
        for path,h in self.receipt['existing_averon_sha256'].items():
            self.assertEqual(hashlib.sha256(m.base.verified_file(ROOT,Path('Pokemon Game/engine')/path,'HEAD')).hexdigest(),h)
            if 'tilesets/' in path:self.assertTrue('/primary/general/' in path or '/secondary/rustboro/' in path)
        self.assertIn(((15,14,5,5),(15,35,4,4)),m.existing.FACADES['SurvivalArea'])
        self.assertIn(((14,24,4,5),(31,15,5,5)),m.existing.FACADES['SurvivalArea'])

    def test_engine_output_refused_before_any_write(self):
        with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,ENGINE/'bad-output')

if __name__=='__main__':unittest.main()
