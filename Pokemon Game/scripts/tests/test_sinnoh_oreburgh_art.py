"""Existing-art Route207 metadata: preserve behavior, layers and bank boundaries."""
import importlib.util
import json
from pathlib import Path
import struct
import unittest

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/oreburgh-donor'
spec=importlib.util.spec_from_file_location('route207_art',HERE/'adapt_route207.py')
art=importlib.util.module_from_spec(spec)
spec.loader.exec_module(art)


class ArtBankTest(unittest.TestCase):
    def setUp(self):
        self.general=b''.join(struct.pack('<8H',*([i]*8)) for i in range(512))
        self.ga=bytes(1024)
        self.rustboro=b''.join(struct.pack('<8H',*([100+i]*8)) for i in range(350))
        self.attrs=[b''.join(struct.pack('<H',0x1000+i) for i in range(512)),
                    b''.join(struct.pack('<H',0x2000+i) for i in range(440))]
        mids=[107,147,148,*art.SECONDARY]
        self.raw=struct.pack('<2048H',*(mids+[107]*(2048-len(mids))))
        self.border=bytes.fromhex('d601d701de01df01')

    def banks(self,**kw):
        args=dict(raw=self.raw,border=self.border,general=self.general,
                  general_attrs=self.ga,rustboro=self.rustboro,source_attrs=self.attrs)
        args.update(kw)
        return art.banks(**args)

    def test_complete_attributes_preserved_for_maps_and_extra_border_pieces(self):
        p,pa,s,sa=self.banks()
        used={x[0]&1023 for x in struct.iter_unpack('<H',self.raw+self.border)}
        self.assertTrue({478,479}.issubset(used))
        for mid in used:
            bank,i=divmod(mid,512)
            self.assertEqual((pa,sa)[bank][i*2:i*2+2],self.attrs[bank][i*2:i*2+2])
        self.assertEqual(len(p),8192)
        self.assertEqual(len(s)//16,357)

    def test_local_only_does_not_mutate_input_or_unused_primary_records(self):
        before=(self.general,self.ga,self.rustboro,*self.attrs)
        p,pa,_,_=self.banks()
        self.assertEqual(before,(self.general,self.ga,self.rustboro,*self.attrs))
        used={x[0]&1023 for x in struct.iter_unpack('<H',self.raw+self.border)}
        for i in set(range(512))-used:
            self.assertEqual(p[i*16:i*16+16],self.general[i*16:i*16+16])
            self.assertEqual(pa[i*2:i*2+2],self.ga[i*2:i*2+2])

    def test_stairs_use_existing_step_art_and_not_water_art(self):
        p,pa,_,_=self.banks()
        for mid in (147,148):
            self.assertEqual(p[mid*16:(mid+1)*16],self.general[175*16:176*16])
            self.assertEqual(pa[mid*2:mid*2+2],self.attrs[0][mid*2:mid*2+2])

    def test_original_tree_records_are_preserved(self):
        p,_,_,_=self.banks()
        for mid in (470,471,478,479,486,487,494,495,499):
            self.assertEqual(p[mid*16:mid*16+16],self.general[mid*16:mid*16+16])

    def test_wood_right_edge_is_mirrored_and_central_post_removed(self):
        _,_,s,_=self.banks()
        wood=art.record(self.rustboro,16)
        self.assertEqual(art.record(s,853-512),wood)
        self.assertEqual(art.record(s,855-512),[wood[i]^0x400 for i in (1,0,3,2,5,4,7,6)])
        self.assertEqual(art.record(s,850-512),[wood[i] for i in (1,1,3,3,5,5,7,7)])

    def test_unreviewed_source_dependency_or_missing_bridge_piece_rejected(self):
        for value in (901,514,0):
            changed=bytearray(self.raw);struct.pack_into('<H',changed,3*2,value)
            with self.subTest(value=value),self.assertRaisesRegex(ValueError,'dependency'):
                self.banks(raw=bytes(changed))

    def test_unknown_border_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'dependency'):
            self.banks(border=bytes(8))

    def test_bank_and_dimension_mismatch_rejected(self):
        for kwargs in (dict(raw=self.raw[:-2]),dict(border=self.border[:-2]),
                       dict(general=self.general[:-16]),dict(general_attrs=self.ga[:-2]),
                       dict(rustboro=self.rustboro[:-1]),dict(source_attrs=[self.attrs[0],b'\x00'])):
            with self.subTest(keys=list(kwargs)),self.assertRaises(ValueError):
                self.banks(**kwargs)

    def test_new_pixel_bank_or_palette_dependency_is_rejected(self):
        for word in (600,0x6001):
            changed=bytearray(self.general);struct.pack_into('<H',changed,175*16,word)
            with self.subTest(word=word),self.assertRaisesRegex(ValueError,'graphics/palette'):
                self.banks(general=bytes(changed))

    def test_truncated_source_attribute_dependency_rejected(self):
        with self.assertRaisesRegex(ValueError,'source behavior'):
            self.banks(source_attrs=[self.attrs[0],bytes(100)])

    def test_published_candidate_matches_each_recorded_source_attribute(self):
        folder=HERE/'corridor/Route207'
        receipt=json.loads((folder/'art-receipt.json').read_text())
        attrs=[(folder/'banks'/bank/'metatile_attributes.bin').read_bytes()
               for bank in ('primary','secondary')]
        for key,expected in receipt['source_attribute_words'].items():
            mid=int(key);bank,i=divmod(mid,512)
            self.assertEqual(struct.unpack_from('<H',attrs[bank],i*2)[0],expected)
        for mid,expected in ((147,0x104A),(148,0x1049),(861,0x1002)):
            self.assertEqual(receipt['source_attribute_words'][str(mid)],expected)
        self.assertEqual(receipt['geometry_sha256'],'b21dff39fc3f721a48f654d934c5eeecd952458032f95010ca9c1e4482a474e6')
        self.assertTrue(receipt['all_graphics_in_existing_general_bank'])
        self.assertFalse(receipt['secondary_callback_required'])


if __name__=='__main__':unittest.main()
