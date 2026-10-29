"""Sinnoh placeholder art tool: PNG I/O, the Emerald-build catalogue, plan
composition with exact stamps, and the manifest check. Reads the real engine;
writes only to temporary directories."""
import csv
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

SCRIPT = Path(__file__).resolve().parents[1] / 'sinnoh-placeholder-art.py'
DESIGN = SCRIPT.parents[1] / 'Averon_Codex_Handoff/design/sinnoh'
SPEC = importlib.util.spec_from_file_location('sinnoh_placeholder_art', SCRIPT)
art = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(art)


def indexed_png(width, height, pixels, depth=4):
    """A minimal non-interlaced indexed PNG using filter type 1 (sub) on every row."""
    rows = b''
    for row in pixels:
        if depth == 4:
            packed = bytes((row[x] << 4) | row[x + 1] for x in range(0, width, 2))
        else:
            packed = bytes(row)
        subbed = bytes((packed[i] - (packed[i - 1] if i else 0)) & 0xFF for i in range(len(packed)))
        rows += b'\x01' + subbed

    def chunk(kind, body):
        return struct.pack('>I', len(body)) + kind + body + struct.pack('>I', zlib.crc32(kind + body) & 0xFFFFFFFF)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, depth, 3, 0, 0, 0))
            + chunk(b'PLTE', bytes(48)) + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


class PngTests(unittest.TestCase):
    def test_indexed_reader_undoes_filters_and_unpacks_nibbles(self):
        pixels = [[(x + y) % 16 for x in range(8)] for y in range(3)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'p.png'
            path.write_bytes(indexed_png(8, 3, pixels))
            self.assertEqual(art.read_indexed_png(path), (8, 3, pixels))

    def test_rgb_writer_produces_a_valid_png(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'o.png'
            art.write_rgb_png(path, 2, 1, [[(255, 0, 0), (0, 0, 255)]])
            data = path.read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            body = data[8 + 8 + 13 + 4:]
            length = struct.unpack('>I', body[:4])[0]
            self.assertEqual(zlib.decompress(body[8:8 + length]), b'\x00\xff\x00\x00\x00\x00\xff')


class CatalogueTests(unittest.TestCase):
    def test_frlg_branches_are_dropped(self):
        text = '\n'.join(['A', '#if !IS_FRLG', 'B', '#else', 'C', '#endif', '#if IS_FRLG', 'D', '#endif', 'E'])
        self.assertEqual(art.emerald_text(text).split(), ['A', 'B', 'E'])

    def test_real_engine_catalogue_is_emerald_only(self):
        cat = art.tileset_catalogue()
        stock = ['gTileset_Building', 'gTileset_General', 'gTileset_SecretBase']
        primaries = sorted(k for k, v in cat.items() if not v['secondary'])
        self.assertEqual([k for k in primaries if not k.startswith('gTileset_Averon')], stock)
        for name in primaries:                      # Averon primaries reuse a stock Emerald primary's tiles
            self.assertIn(cat[name]['tiles'], {cat[k]['tiles'] for k in stock}, name)
        self.assertFalse([k for k in cat if k.endswith('Frlg')])
        self.assertIn('gTileset_Dewford', cat)
        self.assertTrue(cat['gTileset_General']['tiles'].endswith('primary/general/tiles.png'))

    def test_behavior_names_follow_the_enum(self):
        names = art.behavior_names()
        self.assertEqual(names[:3], ['MB_NORMAL', 'MB_SECRET_BASE_WALL', 'MB_TALL_GRASS'])
        self.assertIn('MB_ANIMATED_DOOR', names)

    def test_pair_resolves_primary_and_secondary_metatiles(self):
        pair = art.Pair('gTileset_General', 'gTileset_Dewford')
        names = art.behavior_names()
        self.assertEqual(names[pair.metatile(97)[1] & 0xFF], 'MB_ANIMATED_DOOR')    # primary
        self.assertEqual(names[pair.metatile(292)[1] & 0xFF], 'MB_SAND')            # primary
        self.assertEqual(len(pair.render(549)), 16)                                  # secondary
        with self.assertRaises(KeyError):
            art.Pair('gTileset_General_Frlg', 'gTileset_Dewford')


class PlanTests(unittest.TestCase):
    def plan(self, **changes):
        plan = {'primary': 'gTileset_General', 'secondary': 'gTileset_Dewford', 'width': 6, 'height': 5,
                'legend': {'.': {'metatile': 292, 'elevation': 3}, 'T': {'metatile': 579, 'collision': 1,
                                                                         'elevation': 0}},
                'rows': ['TTTTTT', 'T....T', 'T....T', 'T....T', 'TTTTTT'], 'stamps': []}
        plan.update(changes)
        return plan

    def test_legend_cells_pack_metatile_collision_and_elevation(self):
        grid = art.compose_plan(self.plan())
        self.assertEqual(grid[0][0], 579 | (1 << 10))
        self.assertEqual(grid[2][2], 292 | (3 << 12))

    def test_stamp_copies_exact_blocks_from_a_layout(self):
        stamp = {'from': 'LAYOUT_DEWFORD_TOWN', 'src': [1, 7, 4, 4], 'at': [1, 1]}
        grid = art.compose_plan(self.plan(width=6, height=6, rows=['......'] * 6, stamps=[stamp]))
        source = art.read_blocks(art.ENGINE, art.layout_entry(art.ENGINE, 'LAYOUT_DEWFORD_TOWN'))
        self.assertEqual([row[1:5] for row in grid[1:5]], [row[1:5] for row in source[7:11]])
        self.assertEqual(grid[4][2] & 0x3FF, 97)          # the Pokemon Center door
        self.assertTrue(grid[4][2] & 0x0C00)              # doors are solid; stepping in warps

    def test_other_secondary_only_for_primary_art(self):
        mart = {'from': 'LAYOUT_MAUVILLE_CITY', 'src': [22, 12, 4, 3], 'at': [1, 1]}
        art.compose_plan(self.plan(stamps=[mart]))          # primary-only Mart rows: accepted
        house = {'from': 'LAYOUT_MAUVILLE_CITY', 'src': [18, 11, 4, 4], 'at': [1, 1]}
        with self.assertRaisesRegex(ValueError, 'gTileset_Mauville metatiles'):
            art.compose_plan(self.plan(width=6, height=6, rows=['......'] * 6, stamps=[house]))

    def test_bad_plans_are_refused(self):
        with self.assertRaisesRegex(ValueError, 'legend has no entry'):
            art.compose_plan(self.plan(rows=['TTTTTT', 'T..x.T', 'T....T', 'T....T', 'TTTTTT']))
        with self.assertRaisesRegex(ValueError, 'rows must be'):
            art.compose_plan(self.plan(rows=['TTTTT'] * 5))
        with self.assertRaisesRegex(ValueError, 'lands outside'):
            art.compose_plan(self.plan(stamps=[{'from': 'LAYOUT_DEWFORD_TOWN', 'src': [1, 7, 4, 4],
                                                'at': [4, 3]}]))

    def test_sandgem_candidate_composes_and_writes_blockdata(self):
        path = DESIGN / 'sandgem/sandgem-town-candidate.json'
        plan = json.loads(path.read_text())
        grid = art.compose_plan(plan)
        self.assertEqual((len(grid[0]), len(grid)), (plan['width'], plan['height']))
        names = art.behavior_names()
        pair = art.Pair(plan['primary'], plan['secondary'])
        for mark in plan['marks']:
            x, y = mark['at']
            if mark['kind'] == 'warp':                       # every marked door is a real door ...
                self.assertEqual(names[pair.metatile(grid[y][x] & 0x3FF)[1] & 0xFF], 'MB_ANIMATED_DOOR', mark)
                self.assertFalse(grid[y + 1][x] & 0x0C00, mark)  # ... with a walkable tile below it
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'map.bin'
            self.assertEqual(art.main(['plan', str(path), '--out', str(Path(tmp) / 'p.png'),
                                       '--blockdata', str(out)]), 0)
            self.assertEqual(out.stat().st_size, plan['width'] * plan['height'] * 2)


class ManifestTests(unittest.TestCase):
    def write(self, tmp, rows):
        path = Path(tmp) / 'm.csv'
        with open(path, 'w', newline='') as handle:
            out = csv.DictWriter(handle, fieldnames=art.MANIFEST_COLUMNS)
            out.writeheader()
            for row in rows:
                out.writerow({c: row.get(c, '') for c in art.MANIFEST_COLUMNS})
        return path

    def good(self, **changes):
        row = dict(token='T1', role='r', biome='b', primary='gTileset_General', secondary='gTileset_Dewford',
                   metatiles='292 97', behaviors='MB_SAND MB_ANIMATED_DOOR', source='in-repo',
                   license='upstream', replace_when='owner', status='USABLE')
        row.update(changes)
        return row

    def test_committed_manifest_matches_the_engine(self):
        self.assertEqual(art.check_manifest(DESIGN / 'SINNOH_PLACEHOLDER_MANIFEST.csv'), [])

    def test_each_kind_of_drift_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(art.check_manifest(self.write(tmp, [self.good()])), [])
            cases = {
                'not an Emerald-build tileset': self.good(secondary='gTileset_PalletTown_Frlg'),
                'is a secondary tileset': self.good(primary='gTileset_Dewford'),
                'behaves as MB_SAND': self.good(behaviors='MB_NORMAL MB_ANIMATED_DOOR'),
                'outside 0..': self.good(metatiles='292 4000'),
                'not an object event graphics id': self.good(object_graphics='OBJ_EVENT_GFX_NOPE'),
                'license is empty': self.good(license=''),
                'FRLG art is not linked': self.good(source='FRLG port'),
                'duplicate token': None,
            }
            for expected, row in cases.items():
                rows = [self.good(), self.good()] if row is None else [row]
                with self.subTest(expected):
                    problems = art.check_manifest(self.write(tmp, rows))
                    self.assertTrue(any(expected in p for p in problems), problems)


if __name__ == '__main__':
    unittest.main()
