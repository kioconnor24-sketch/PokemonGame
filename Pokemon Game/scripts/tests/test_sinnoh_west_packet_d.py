"""Production D: preserve installed identities, actual reused source and closed boundaries."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / 'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/west-packet-d'
spec = importlib.util.spec_from_file_location('production_d', HERE / 'install_packet_d.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def cells(raw):
    return struct.unpack('<%dH' % (len(raw) // 2), raw)


def fixture(engine):
    # The real checkout may already carry D. Reuse only the verifier's exact,
    # hash-proven original inputs instead of assuming current files are pre-D.
    before = p.baseline(p.ENGINE)
    for rel in set(p.BASE_HASHES) | set(p.ASSET_HASHES):
        path = p.target(engine, rel)
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel in before:
            path.write_bytes(before[rel])
        else:
            shutil.copy(p.target(p.ENGINE, rel), path)


class WestPacketDTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.engine = Path(self.temp.name) / 'engine'
        fixture(self.engine)

    def install(self):
        return p.install(self.engine)

    def mutate_json(self, rel, change):
        target = p.target(self.engine, rel)
        data = json.loads(target.read_text())
        change(data)
        target.write_bytes(p.encode(data))

    def test_five_slots_sections_and_layouts_extend_the_exact_installed_prefix(self):
        before_groups = json.loads(p.target(self.engine, p.GROUPS).read_text())
        before_layouts = json.loads(p.target(self.engine, p.LAYOUTS).read_text())['layouts']
        before_sections = json.loads(p.target(self.engine, p.SECTION_PATH).read_text())['map_sections']
        before_pins = json.loads(p.target(self.engine, p.PINS).read_text())['pins']
        files = self.install()
        groups = json.loads(files[p.GROUPS])
        self.assertEqual(groups['gMapGroup_Sinnoh'], before_groups['gMapGroup_Sinnoh'] + p.SLOTS)
        self.assertEqual({k: v for k, v in groups.items() if k != 'gMapGroup_Sinnoh'},
                         {k: v for k, v in before_groups.items() if k != 'gMapGroup_Sinnoh'})
        self.assertEqual(json.loads(files[p.LAYOUTS])['layouts'][:-5], before_layouts)
        self.assertEqual(json.loads(files[p.SECTION_PATH])['map_sections'], before_sections + p.SECTIONS)
        pins = json.loads(files[p.PINS])['pins']
        self.assertEqual({k: pins[k] for k in before_pins}, before_pins)
        self.assertEqual({k: v for k, v in pins.items() if k not in before_pins},
                         {s['id']: s['value'] for s in p.SECTIONS})
        self.assertEqual(p.sha(files['data/maps/MtCoronet_1F_South/map.json']),
                         'bc59c1e3599e412b57e08e304e26cc4ddd8cf0ae0023f91d9283bef6cb6a07e2')
        self.assertEqual(p.check(self.engine), [])
        with self.assertRaisesRegex(ValueError, 'production41'):
            self.install()

    def test_reuses_accepted_payloads_and_changes_only_the_unbuilt_north_door_cell(self):
        accepted = p.accepted_source()
        files = self.install()
        for name in p.SLOTS:
            for filename in ('map.bin', 'border.bin'):
                rel = f'data/layouts/{name}/{filename}'
                if name == 'Route206_North' and filename == 'map.bin':
                    a, b = cells(accepted[rel]), cells(files[rel])
                    self.assertEqual([(i, old, new) for i, (old, new) in enumerate(zip(a, b)) if old != new],
                                     [(13, 0x3323, 0x3721)])
                    self.assertEqual(b[13] & 0xF000, a[13] & 0xF000)
                    self.assertEqual(b[13] & 0x3FF, a[4] & 0x3FF)  # its own solid north wall
                else:
                    self.assertEqual(files[rel], accepted[rel], rel)
        # The removed external road connection was already blocked by its whole
        # solid roof/edge. Do not invent an additional terrain change there.
        self.assertTrue(all((word >> 10) & 3 == 1 for word in cells(files['data/layouts/Route206/map.bin'])[:28]))
        city_before = json.loads(p.baseline(p.ENGINE)[p.CITY])
        city_after = json.loads(files[p.CITY])
        city_after['connections'] = []
        self.assertEqual(city_after, city_before)

    def test_reciprocal_production_joins_preserve_installed_returns_and_no_external_targets(self):
        files = self.install()
        headers = {json.loads(raw)['id']: json.loads(raw) for rel, raw in files.items()
                   if rel.startswith('data/maps/') and rel.endswith('/map.json')}
        for mid, header in headers.items():
            for warp in header['warp_events']:
                if warp['dest_map'] in headers:
                    back = headers[warp['dest_map']]['warp_events'][int(warp['dest_warp_id'])]
                    self.assertEqual(back['dest_map'], mid, (mid, warp))
            if mid != 'MAP_OREBURGH_CITY':
                self.assertTrue(all(w['dest_map'] in headers for w in header['warp_events']))
                self.assertTrue(all(c['map'] in headers for c in header['connections']))
                for key in ('object_events', 'coord_events', 'bg_events'):
                    self.assertEqual(header[key], [])
        self.assertEqual(headers['MAP_OREBURGH_CITY']['connections'],
                         [dict(map='MAP_ROUTE207', offset=35, direction='up')])
        self.assertIn(dict(map='MAP_OREBURGH_CITY', offset=-35, direction='down'),
                      headers['MAP_ROUTE207']['connections'])
        self.assertEqual(headers['MAP_ROUTE206_NORTH']['warp_events'],
                         [dict(x=4, y=9, elevation=0, dest_map='MAP_ROUTE206', dest_warp_id='0')])
        self.assertEqual(headers['MAP_ROUTE206']['warp_events'][0]['dest_warp_id'], '0')
        south = headers['MAP_MT_CORONET_1F_SOUTH']
        self.assertEqual(south['region_map_section'], 'MAPSEC_MT_CORONET')
        self.assertEqual(south['warp_events'],
                         [dict(x=5, y=7, elevation=0, dest_map='MAP_ROUTE207', dest_warp_id='0')])

    def test_installed_externs_stay_inside_guard_and_bindings_replay_exactly(self):
        files = self.install()
        include = files['include/tilesets.h'].decode()
        before, after = include.split('#endif //GUARD_tilesets_H')
        self.assertNotIn('gTileset_', after)
        for symbol in ('AveronRoute206Primary', 'AveronRoute206Secondary',
                       'AveronRoute206GatePrimary', 'AveronRoute206GateSecondary',
                       'AveronCoronetSouthSecondary'):
            self.assertEqual(before.count(f'extern const struct Tileset gTileset_{symbol};'), 1)
        target = p.target(self.engine, 'src/data/tilesets/headers.h')
        raw = target.read_bytes()
        marker = b'const struct Tileset gTileset_AveronCoronetSouthSecondary ='
        pos = raw.index(marker)
        target.write_bytes(raw[:pos] + raw[pos:].replace(b'.callback=InitTilesetAnim_Cave', b'.callback=NULL', 1))
        self.assertNotEqual(target.read_bytes(), raw)
        with self.assertRaisesRegex(ValueError, 'baseline differs'):
            p.check(self.engine)

    def test_wrong_installed_identity_prefix_or_legacy_return_is_rejected(self):
        self.install()
        for rel, change in (
            (p.GROUPS, lambda d: d['gMapGroup_Sinnoh'].__setitem__(slice(0, 2), d['gMapGroup_Sinnoh'][1::-1])),
            (p.SECTION_PATH, lambda d: d['map_sections'][-1].__setitem__('name', 'WRONG')),
            (p.PINS, lambda d: d['pins'].__setitem__('MAPSEC_MT_CORONET', 229)),
            (p.CITY, lambda d: d['warp_events'][0].__setitem__('dest_warp_id', '0')),
        ):
            with self.subTest(rel=rel):
                target = p.target(self.engine, rel)
                original = target.read_bytes()
                self.mutate_json(rel, change)
                try:
                    with self.assertRaises(ValueError):
                        p.check(self.engine)
                finally:
                    target.write_bytes(original)

    def test_wrong_base_asset_or_preexisting_new_output_refuses_before_first_write(self):
        path = p.target(self.engine, p.CITY)
        original = path.read_bytes()
        path.write_bytes(original + b' ')
        with self.assertRaisesRegex(ValueError, 'production41'):
            self.install()
        self.assertFalse(p.target(self.engine, 'data/maps/Route207/map.json').exists())
        path.write_bytes(original)
        graphics = p.target(self.engine, 'data/tilesets/secondary/cave/tiles.png')
        good = graphics.read_bytes()
        graphics.write_bytes(good[:-1] + bytes([good[-1] ^ 1]))
        with self.assertRaisesRegex(ValueError, 'graphics/palette'):
            self.install()
        self.assertEqual(path.read_bytes(), original)
        graphics.write_bytes(good)
        other = p.target(self.engine, 'data/maps/Route207/scripts.inc')
        other.parent.mkdir(parents=True)
        other.write_text('existing work')
        with self.assertRaisesRegex(ValueError, 'existing/untracked'):
            self.install()
        self.assertEqual(other.read_text(), 'existing work')
        self.assertEqual(path.read_bytes(), original)

    def test_changed_new_payload_or_south_identity_is_reported(self):
        self.install()
        for rel, change in (
            ('data/maps/MtCoronet_1F_South/map.json', lambda raw: raw.replace(b'MAPSEC_MT_CORONET', b'MAPSEC_ROUTE_201')),
            ('data/layouts/Route207/map.bin', lambda raw: bytes([raw[0] ^ 1]) + raw[1:]),
            ('data/maps/Route207/scripts.inc', lambda raw: raw.replace(b'::', b':', 1)),
        ):
            with self.subTest(rel=rel):
                target = p.target(self.engine, rel)
                original = target.read_bytes()
                target.write_bytes(change(original))
                try:
                    self.assertIn(rel, p.check(self.engine))
                finally:
                    target.write_bytes(original)


if __name__ == '__main__':
    unittest.main()
