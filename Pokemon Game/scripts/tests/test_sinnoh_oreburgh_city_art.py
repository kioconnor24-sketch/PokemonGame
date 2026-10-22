"""Off-engine shared art and coupled sparse warp indices; no runtime claims."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import unittest

HERE = Path(__file__).resolve().parents[2] / 'Averon_Codex_Handoff/design/sinnoh/oreburgh-donor'
spec = importlib.util.spec_from_file_location('oreburgh_city_art', HERE / 'build_city_family.py')
art = importlib.util.module_from_spec(spec)
spec.loader.exec_module(art)


def cells(values):
    return struct.pack('<%dH' % len(values), *values)


class PackingTest(unittest.TestCase):
    def setUp(self):
        self.primary = b''.join(cells([i] * 8) for i in range(512))
        self.pa = cells([0] * 512)
        self.source = [cells([0x1000 + i for i in range(512)]), cells([0x2000 + i for i in range(512)])]

    def pack(self, raw=None, desired=None, **kw):
        args = dict(raw=cells([0xAC01, 0xFC01]), desired=[(7,) * 8] * 2,
                    source_attrs=self.source, primary=self.primary, primary_attrs=self.pa,
                    secondary=b'', secondary_attrs=b'')
        if raw is not None: args['raw'] = raw
        if desired is not None: args['desired'] = desired
        args.update(kw)
        return art.pack_art(**args)

    def test_deduplicates_complete_art_and_attribute_pair(self):
        raw, records, attrs = self.pack()
        self.assertEqual(cells([0xAE00, 0xFE00]), raw)
        self.assertEqual(records, cells([7] * 8))
        self.assertEqual(attrs, cells([0x1001]))

    def test_every_collision_and_elevation_combination_preserved(self):
        original = [((i << 10) | 1) for i in range(64)]
        out, _, _ = self.pack(cells(original), [(7,) * 8] * 64)
        self.assertEqual([v & 0xFC00 for v in original], [v[0] & 0xFC00 for v in struct.iter_unpack('<H', out)])

    def test_same_art_with_different_full_layer_word_is_distinct(self):
        _, records, attrs = self.pack(cells([1, 513]), [(7,) * 8] * 2)
        self.assertEqual(len(records), 32)
        self.assertEqual(attrs, cells([0x1001, 0x2001]))

    def test_reuses_matching_primary_record_without_secondary_allocation(self):
        source = [self.pa, self.source[1]]
        out, records, _ = self.pack(cells([7]), [(7,) * 8], source_attrs=source)
        self.assertEqual(out, cells([7])); self.assertEqual(records, b'')

    def test_capacity_exhaustion_rejected(self):
        with self.assertRaisesRegex(ValueError, 'capacity'):
            self.pack(secondary=self.primary, secondary_attrs=self.pa)

    def test_malformed_dimensions_rejected(self):
        for kw in (dict(raw=b'\x00'), dict(desired=[]), dict(primary=b''),
                   dict(primary_attrs=b''), dict(secondary=b'\0'),
                   dict(secondary=bytes(16), secondary_attrs=b''),
                   dict(secondary=bytes(513*16), secondary_attrs=bytes(513*2))):
            with self.subTest(kw=list(kw)), self.assertRaises(ValueError): self.pack(**kw)

    def test_invalid_art_words_and_truncated_source_attributes_rejected(self):
        for record in ((1,) * 7, (65536,) * 8, (-1,) * 8, (True,) * 8):
            with self.subTest(record=record), self.assertRaises(ValueError): self.pack(desired=[record] * 2)
        with self.assertRaises(ValueError): self.pack(source_attrs=[b'', b''])

    def test_input_banks_remain_unmodified_and_existing_prefix_preserved(self):
        secondary = bytearray(cells([4] * 8)); attrs = bytearray(cells([0]))
        before = (bytes(secondary), bytes(attrs), self.primary, self.pa, tuple(self.source))
        _, result, result_attrs = self.pack(secondary=secondary, secondary_attrs=attrs)
        self.assertEqual(result[:16], secondary); self.assertEqual(result_attrs[:2], attrs)
        self.assertEqual(before, (bytes(secondary), bytes(attrs), self.primary, self.pa, tuple(self.source)))


class WarpPlanTest(unittest.TestCase):
    def setUp(self):
        data = json.loads((HERE / 'source-inspection.json').read_text())
        self.city = data['OreburghCity']['warp_geometry']
        self.b1 = [dict(x=x, y=y, elevation=0, dest_map=dest, dest_warp_id=str(w))
                   for x,y,dest,w in [(11,1,'MAP_OREBURGH_CITY',11), (12,1,'MAP_OREBURGH_CITY',14),
                       (11,21,'MAP_OREBURGH_MINE_B2F',0), (12,21,'MAP_OREBURGH_MINE_B2F',0),
                       (10,21,'MAP_OREBURGH_MINE_B2F',0), (13,21,'MAP_OREBURGH_MINE_B2F',0)]]
        self.b2 = [dict(x=15,y=1,elevation=0,dest_map='MAP_OREBURGH_MINE_B1F',dest_warp_id='2')]
        self.gate = [dict(x=5,y=14,elevation=0,dest_map='MAP_ROUTE203',dest_warp_id='0'),dict(x=25,y=20,elevation=0,dest_map='MAP_OREBURGH_CITY',dest_warp_id='0')]
        self.args = [self.city,self.b1,self.b2,self.gate]

    def test_sparse_city_returns_compact_as_one_coupled_plan(self):
        before = copy.deepcopy(self.args)
        plan = art.compact_warps(*self.args)
        self.assertEqual(plan['city_source_to_candidate'], {0:0,11:1,12:2,13:3,14:4})
        events = plan['events']
        self.assertEqual([w['dest_warp_id'] for w in events['MAP_OREBURGH_MINE_B1F'][:2]], ['1','4'])
        self.assertEqual(events['MAP_OREBURGH_MINE_B1F'][2:], self.b1[2:])
        self.assertEqual(events['MAP_OREBURGH_MINE_B2F'], self.b2)
        self.assertEqual(self.args, before)

    def test_missing_reordered_or_shifted_city_mine_anchor_rejected(self):
        for mutate in (lambda c:c.pop(), lambda c:c[11].update(x=49),
                       lambda c:c[12].update(elevation=1), lambda c:c.reverse()):
            args = copy.deepcopy(self.args); mutate(args[0])
            with self.assertRaises(ValueError): art.compact_warps(*args)

    def test_invalid_gate_or_city_destination_rejected(self):
        for group,index,key,value in ((3,1,'dest_warp_id','1'),(3,1,'x',24),
                (0,0,'dest_warp_id','0'),(0,11,'dest_warp_id','6'),
                (0,14,'dest_map','MAP_OTHER')):
            args=copy.deepcopy(self.args);args[group][index][key]=value
            with self.subTest(change=(group,index,key)),self.assertRaises(ValueError):art.compact_warps(*args)

    def test_all_source_mine_events_and_canonical_b2_return_required(self):
        for mutate in (lambda a:a[1].pop(), lambda a:a[1][4].update(x=9),
                       lambda a:a[2][0].update(dest_warp_id='3'), lambda a:a[1][0].update(dest_warp_id='12')):
            args=copy.deepcopy(self.args);mutate(args)
            with self.assertRaises(ValueError):art.compact_warps(*args)


class PublishedFamilyTest(unittest.TestCase):
    def test_published_cells_preserve_geometry_and_used_source_attributes(self):
        folder=HERE/'city-family'
        receipt=json.loads((folder/'receipt.json').read_text())
        bank=[(folder/'banks'/b/'metatiles.bin').read_bytes() for b in ('primary','secondary')]
        attrs=[(folder/'banks'/b/'metatile_attributes.bin').read_bytes() for b in ('primary','secondary')]
        self.assertEqual([len(x)//16 for x in bank],[512,receipt['shared_bank_records']])
        source=json.loads((HERE/'source-inspection.json').read_text())
        count=0
        for name in ('OreburghCity','Route207'):
            before=(HERE/'corridor'/name/'map.bin').read_bytes()
            after=(folder/name/'map.bin').read_bytes()
            self.assertEqual(len(before),len(after))
            # The pinned source receipt records every consumed behavior/layer word.
            expected=receipt['source_used_attributes'][name]
            for (old,), (new,) in zip(struct.iter_unpack('<H',before),struct.iter_unpack('<H',after)):
                self.assertEqual(old&0xFC00,new&0xFC00)
                b,i=divmod(new&1023,512)
                self.assertEqual(art.attribute(attrs[b],i),int(expected[str(old&1023)]))
                art.words(bank[b],i);count+=1
        self.assertEqual(count,6178)
        self.assertEqual(count,receipt['verified_cells'])


if __name__ == '__main__': unittest.main()
