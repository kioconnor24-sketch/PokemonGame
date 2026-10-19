"""Actual temporary Git snapshots and indexed graphics; no production maps/assets."""
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from PIL import Image

spec = importlib.util.spec_from_file_location('isolated', Path(__file__).resolve().parents[1] / 'sinnoh-isolated-tileset.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class IsolatedFamilyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name); self.root = self.base / 'donor'; self.root.mkdir()
        self.engine = self.base / 'destination'; self.engine.mkdir()
        self.output = self.base / 'scratch'
        self.bank = self.root / m.FAMILY; self.bank.mkdir(parents=True)
        self.run_git('init', '-q')
        for rel in m.CONTRACTS:
            for root in (self.root, self.engine):
                p = root / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('contract\n')
        self.layout = {'id': 'LAYOUT_ROUTE202', 'width': 2, 'height': 1,
                       'primary_tileset': 'gTileset_General', 'secondary_tileset': 'gTileset_Petalburg',
                       'border_filepath': 'data/layouts/Route202/border.bin',
                       'blockdata_filepath': 'data/layouts/Route202/map.bin'}
        p = self.root / 'data/maps/Route202/map.json'; p.parent.mkdir(parents=True)
        p.write_text(json.dumps({'id': 'MAP_ROUTE202', 'layout': 'LAYOUT_ROUTE202',
                                'object_events': [{'script': 'NEVER_IMPORT'}]}))
        self.table = self.root / 'data/layouts/layouts.json'; self.table.parent.mkdir(parents=True)
        self.table.write_text(json.dumps({'layouts': [self.layout]}))
        p = self.root / self.layout['blockdata_filepath']; p.parent.mkdir(parents=True)
        p.write_bytes(struct.pack('<2H', 0x1400, 0xFC00))
        (self.root / self.layout['border_filepath']).write_bytes(bytes(8))
        (self.bank / 'metatiles.bin').write_bytes(bytes(16))
        (self.bank / 'metatile_attributes.bin').write_bytes(bytes(2))
        im = Image.new('P', (128, 8)); im.putpalette([v for i in range(256) for v in (i, i, i)])
        im.save(self.bank / 'tiles.png')
        for i in range(16):
            p = self.bank / ('palettes/%02d.pal' % i); p.parent.mkdir(exist_ok=True)
            p.write_text('JASC-PAL\n0100\n16\n' + '255 128 0\n'*16)
        self.commit()

    def run_git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.PIPE)

    def commit(self):
        self.run_git('add', '.')
        self.run_git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
        self.rev = self.run_git('rev-parse', 'HEAD').decode().strip()

    def stage(self):
        return m.stage(self.root, self.engine, self.rev, 'Route202', self.output)

    def test_real_snapshot_stages_exact_assets_and_collision(self):
        result = self.stage()
        self.assertTrue(result['staged_pixels_equal_source'])
        self.assertEqual(result['dependencies'], {'metatiles': [0], 'graphic_tiles': [0], 'palettes': [0]})
        self.assertEqual((self.output / 'map.bin').read_bytes(), struct.pack('<2H', 0x1400, 0xFC00))
        self.assertEqual(len(list((self.output / 'SinnohGeneralStatic').rglob('*.pal'))), 16)
        self.assertFalse(any('map.json' == p.name for p in self.output.rglob('*')))
        self.assertNotIn('NEVER_IMPORT', (self.output / 'receipt.json').read_text())
        source = (self.output/'sinnoh_general_static.c').read_text()
        self.assertIn('const struct Tileset gTileset_SinnohGeneralStatic', source)
        self.assertIn('.callback = NULL', source)
        self.assertNotIn('gTileset_General =', source)

    def test_border_dependency_is_validated(self):
        (self.root / self.layout['border_filepath']).write_bytes(struct.pack('<4H', 512, 0, 0, 0)); self.commit()
        with self.assertRaisesRegex(ValueError, 'secondary metatiles'): self.stage()

    def test_border_length_refused(self):
        (self.root / self.layout['border_filepath']).write_bytes(bytes(6)); self.commit()
        with self.assertRaisesRegex(ValueError, 'border dimensions'): self.stage()

    def test_git_declared_crlf_checkout_is_not_dirty(self):
        (self.root/'.gitattributes').write_text('*.pal text eol=crlf\n'); self.commit()
        p = self.bank/'palettes/00.pal'; p.write_bytes(p.read_bytes().replace(b'\n', b'\r\n'))
        self.assertTrue(self.stage()['staged_pixels_equal_source'])

    def test_wrong_head(self):
        self.rev = 'a'*40
        with self.assertRaisesRegex(ValueError, 'HEAD'): self.stage()

    def test_dirty_graphic_dependency(self):
        (self.bank / 'tiles.png').write_bytes(b'not original')
        with self.assertRaisesRegex(ValueError, 'dirty'): self.stage()
        self.assertFalse(self.output.exists())

    def test_dirty_map_dependency(self):
        (self.root / self.layout['blockdata_filepath']).write_bytes(bytes(4))
        with self.assertRaisesRegex(ValueError, 'dirty'): self.stage()

    def test_contract_mismatch(self):
        (self.engine / m.CONTRACTS[0]).write_text('different engine')
        with self.assertRaisesRegex(ValueError, 'contract mismatch'): self.stage()

    def test_existing_output_not_overwritten(self):
        self.stage()
        with self.assertRaisesRegex(ValueError, 'NEW'): self.stage()

    def test_donor_and_engine_outputs_rejected(self):
        for p in (self.root/'scratch', self.engine/'scratch', self.base/'engine'/'scratch'):
            self.output = p
            with self.assertRaisesRegex(ValueError, 'off-engine'): self.stage()

    def test_symlink_source_refused(self):
        p = self.bank / 'metatiles.bin'; p.unlink(); p.symlink_to('metatile_attributes.bin'); self.commit()
        with self.assertRaisesRegex(ValueError, 'regular tracked'): self.stage()

    def test_secondary_metatile_refused(self):
        (self.root / self.layout['blockdata_filepath']).write_bytes(struct.pack('<2H', 512, 0)); self.commit()
        with self.assertRaisesRegex(ValueError, 'secondary metatiles'): self.stage()

    def test_animation_dependency_refused(self):
        (self.bank / 'metatiles.bin').write_bytes(struct.pack('<8H', *([432]*8))); self.commit()
        with self.assertRaisesRegex(ValueError, 'callback adapter'): self.stage()

    def test_secondary_palette_refused(self):
        (self.bank / 'metatiles.bin').write_bytes(struct.pack('<8H', *([6<<12]*8))); self.commit()
        with self.assertRaisesRegex(ValueError, 'palette dependency'): self.stage()

    def test_attribute_count_refused(self):
        (self.bank / 'metatile_attributes.bin').write_bytes(bytes(4)); self.commit()
        with self.assertRaisesRegex(ValueError, 'attribute count'): self.stage()

    def test_absent_graphic_tile_refused(self):
        (self.bank / 'metatiles.bin').write_bytes(struct.pack('<8H', *([100]*8))); self.commit()
        with self.assertRaisesRegex(ValueError, 'absent source graphic'): self.stage()

    def test_non_4bpp_pixels_refused(self):
        im = Image.open(self.bank / 'tiles.png'); im.putpixel((0, 0), 16); im.save(self.bank / 'tiles.png'); self.commit()
        with self.assertRaisesRegex(ValueError, '4bpp'): self.stage()

    def test_palette_quantization_and_flips(self):
        self.assertEqual(m.palette((self.bank/'palettes/00.pal').read_bytes())[0], (248, 128, 0))
        im = Image.new('P', (128, 8)); im.putpixel((0, 0), 1)
        records = struct.pack('<8H', *([0x400]*4 + [0]*4))
        pals = {0: [(0,0,0), (248,0,0)]}
        preview = m.render(bytes(2), records, im, pals, 1, 1)
        self.assertEqual(preview.getpixel((7, 0)), (248,0,0))
        self.assertEqual(preview.getpixel((0, 0)), (248,0,0)) # top-layer nonzero
        self.assertEqual(preview.getpixel((1, 0)), (0,0,0))

    def test_unsupported_layer_refused(self):
        (self.bank/'metatile_attributes.bin').write_bytes(struct.pack('<H', 0x2000)); self.commit()
        with self.assertRaisesRegex(ValueError, 'layer type'): self.stage()


if __name__ == '__main__': unittest.main()
