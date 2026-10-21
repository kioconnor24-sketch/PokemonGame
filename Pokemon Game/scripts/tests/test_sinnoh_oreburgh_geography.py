"""Isolated existing-art Cave adaptation; no production maps or saved IDs."""
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('oreburgh', ROOT /
    'Averon_Codex_Handoff/design/sinnoh/oreburgh-donor/build_oreburgh.py')
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


class CaveAdapterTest(unittest.TestCase):
    def setUp(self):
        self.records = b''.join(struct.pack('<8H', *([i] * 8)) for i in range(414))
        self.attrs = bytes(414 * 2)
        self.donor_records = self.records + bytes(26 * 16)
        self.donor_attrs = bytes(440 * 2)
        self.raw = struct.pack('<7H', 529 | 0x3000, *[i | 0x1400 for i in adapter.ENTRANCE])

    def adapt(self, **kw):
        args = dict(raw=self.raw, donor_records=self.donor_records,
                    donor_attrs=self.donor_attrs, records=self.records, attrs=self.attrs)
        args.update(kw)
        return adapter.adapt_cave(**args)

    def test_six_appended_records_preserve_complete_existing_prefix(self):
        result, attrs, used = self.adapt()
        self.assertEqual(result[:len(self.records)], self.records)
        self.assertEqual(attrs[:len(self.attrs)], self.attrs)
        self.assertEqual(len(result), 420 * 16)
        for mid, source in adapter.ENTRANCE.items():
            self.assertEqual(result[(mid-512)*16:(mid-511)*16],
                             self.records[(source-512)*16:(source-511)*16])
        self.assertEqual(used, [529, *adapter.ENTRANCE])

    def test_changed_existing_cave_record_is_rejected(self):
        changed = bytearray(self.donor_records)
        changed[(529-512)*16] ^= 1
        with self.assertRaisesRegex(ValueError, 'structural difference'):
            self.adapt(donor_records=bytes(changed))

    def test_existing_behavior_and_layer_changes_are_rejected(self):
        for value in (0x60, 0x1000):
            changed = bytearray(self.donor_attrs)
            struct.pack_into('<H', changed, (529-512)*2, value)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'behavior/layer'):
                self.adapt(donor_attrs=bytes(changed))

    def test_entrance_behavior_and_layer_changes_are_rejected(self):
        for mid in adapter.ENTRANCE:
            changed = bytearray(self.donor_attrs)
            struct.pack_into('<H', changed, (mid-512)*2, 0x60)
            with self.subTest(mid=mid), self.assertRaisesRegex(ValueError, 'replacement changes'):
                self.adapt(donor_attrs=bytes(changed))

    def test_unknown_or_missing_entrance_dependency_is_rejected(self):
        for cells in ([*adapter.ENTRANCE, 932], list(adapter.ENTRANCE)[:-1]):
            with self.subTest(cells=cells), self.assertRaisesRegex(ValueError, 'entrance dependency'):
                self.adapt(raw=struct.pack('<%dH' % len(cells), *cells))

    def test_primary_or_empty_geometry_is_rejected(self):
        for raw in (b'', self.raw + b'\x01\x00'):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, 'secondary-only'):
                self.adapt(raw=raw)

    def test_changed_prefix_size_and_truncated_donor_are_rejected(self):
        for kwargs in (dict(records=self.records[:-16]), dict(attrs=self.attrs[:-2]),
                       dict(raw=self.raw[:-1]), dict(donor_attrs=self.donor_attrs[:-1])):
            with self.subTest(kwargs=list(kwargs)), self.assertRaises(ValueError):
                self.adapt(**kwargs)

    def test_missing_source_entrance_record_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'absent donor'):
            self.adapt(donor_records=self.donor_records[:418*16], donor_attrs=self.donor_attrs[:418*2])


class MinePairTest(unittest.TestCase):
    def setUp(self):
        self.primary = b''.join(struct.pack('<8H', *([i] * 8)) for i in range(512))
        self.pa = bytearray(1024)
        self.source_pa = bytearray(1024)
        struct.pack_into('<H', self.source_pa, 484*2, 0x64)
        self.cave = bytes(420*16)
        self.ca = bytes(420*2)
        self.jubilife = bytes(440*16)
        self.ja = bytearray(440*2)
        for mid in (896, 899, 900):
            struct.pack_into('<H', self.ja, (mid-512)*2, 0x65)
        self.cells = [113 | 0x3000] * 624
        for index, mid in enumerate(adapter.B1_SECONDARY):
            self.cells[index] = mid | 0x3000
        for x, mid in ((10, 899), (11, 896), (12, 896), (13, 900)):
            self.cells[21*24+x] = mid
        self.raw = struct.pack('<624H', *self.cells)

    def banks(self, **kw):
        args = dict(raw=self.raw, primary=self.primary, primary_attrs=bytes(self.pa),
                    source_primary_attrs=bytes(self.source_pa), cave=self.cave,
                    cave_attrs=self.ca, jubilife=self.jubilife, jubilife_attrs=bytes(self.ja))
        args.update(kw)
        return adapter.mine_banks(**args)

    @staticmethod
    def warps():
        def warp(x, y, target, dest):
            return dict(x=x, y=y, elevation=0, dest_map=target, dest_warp_id=str(dest))
        city='MAP_OREBURGH_CITY';bottom='MAP_OREBURGH_MINE_B2F'
        return ([warp(11,1,city,11), warp(12,1,city,14), warp(11,21,bottom,0),
                 warp(12,21,bottom,0), warp(10,21,bottom,0), warp(13,21,bottom,0)],
                [warp(15,1,'MAP_OREBURGH_MINE_B1F',2)])

    def test_isolated_primary_and_cave_prefixes_preserved(self):
        primary, pa, cave, ca, remap = self.banks()
        changed = [i for i in range(512) if primary[i*16:i*16+16] != self.primary[i*16:i*16+16]]
        self.assertEqual(changed, [483,484,485])
        self.assertEqual(struct.unpack_from('<H', pa, 484*2)[0], 0x64)
        self.assertEqual(cave[:len(self.cave)], self.cave)
        self.assertEqual(ca[:len(self.ca)], self.ca)
        self.assertEqual(len(cave)//16,442)
        self.assertEqual(set(remap.values()),set(range(932,954)))
        for mid,target in remap.items():
            self.assertEqual(ca[(target-512)*2:(target-511)*2],self.ja[(mid-512)*2:(mid-511)*2])

    def test_all_wide_entrances_and_canonical_return_preserved(self):
        b1,b2=self.warps();first,second=adapter.mine_warps(b1,b2)
        self.assertEqual(first,b1);self.assertEqual(second,b2)
        self.assertEqual(first[2]['dest_warp_id'],'0')
        self.assertEqual(second[0]['dest_warp_id'],'2')
        self.assertEqual(len(b1),6)  # Inputs are not mutated.
        first[0]['x']=99
        self.assertEqual(b1[0]['x'],11)

    def test_changed_source_warp_identity_or_elevation_rejected(self):
        for key,value in [('x',10),('elevation',3),('dest_warp_id','1')]:
            b1,b2=self.warps();b2[0][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'warp contract'):
                adapter.mine_warps(b1,b2)
        b1,b2=self.warps()
        with self.assertRaisesRegex(ValueError,'warp contract'):
            adapter.mine_warps(b1[:-1],b2)

    def test_every_forward_warp_resolves_and_return_lands_on_the_source_canonical_entrance(self):
        b1,b2=self.warps();first,second=adapter.mine_warps(b1,b2)
        for entrance in first[2:]:
            target=second[int(entrance['dest_warp_id'])]
            self.assertEqual((target['x'],target['y']),(15,1))
            back=first[int(target['dest_warp_id'])]
            self.assertEqual((back['x'],back['y']),(11,21))
            self.assertEqual(back['dest_map'],'MAP_OREBURGH_MINE_B2F')
        self.assertEqual(len(first[2:]),4)

    def test_all_entrance_behavior_and_layer_words_survive_remapping(self):
        _,_,_,attrs,remap=self.banks()
        for source in (896,899,900):
            self.assertEqual(struct.unpack_from('<H',attrs,(remap[source]-512)*2)[0],0x65)
        self.assertEqual({v&0xFC00 for v in self.cells},{0,0x3000})

    def test_changed_behavior_layer_or_city_warp_is_rejected(self):
        ja=bytearray(self.ja);struct.pack_into('<H',ja,(869-512)*2,0x1000)
        with self.assertRaisesRegex(ValueError,'secondary behavior/layer'):
            self.banks(jubilife_attrs=bytes(ja))
        pa=bytearray(self.source_pa);struct.pack_into('<H',pa,113*2,0x10)
        with self.assertRaisesRegex(ValueError,'primary behavior/layer'):
            self.banks(source_primary_attrs=bytes(pa))
        pa=bytearray(self.source_pa);struct.pack_into('<H',pa,484*2,0)
        with self.assertRaisesRegex(ValueError,'north-arrow warp'):
            self.banks(source_primary_attrs=bytes(pa))

    def test_unknown_secondary_or_graphics_dependency_is_rejected(self):
        raw=bytearray(self.raw);struct.pack_into('<H',raw,100*2,901)
        with self.assertRaisesRegex(ValueError,'secondary dependency'):
            self.banks(raw=bytes(raw))
        records=bytearray(self.jubilife);struct.pack_into('<H',records,(687-512)*16,700)
        with self.assertRaisesRegex(ValueError,'unmapped donor support'):
            self.banks(jubilife=bytes(records))

    def test_wrong_dimensions_or_bank_size_is_rejected(self):
        for change in [dict(raw=self.raw[:-2]),dict(primary=self.primary[:-16]),
                       dict(cave=self.cave[:-16]),dict(jubilife_attrs=bytes(self.ja[:-1]))]:
            with self.subTest(change=list(change)),self.assertRaisesRegex(ValueError,'bank/dimension'):
                self.banks(**change)


if __name__ == '__main__':
    unittest.main()
