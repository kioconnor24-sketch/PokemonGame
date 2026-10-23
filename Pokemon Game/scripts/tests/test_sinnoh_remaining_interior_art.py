"""Shared permitted indoor candidate physics, assets, rendering and fail-closed anchors."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/remaining-donor'
ENGINE=ROOT/'Pokemon Game/engine'
spec=importlib.util.spec_from_file_location('remaining_indoor_art',HERE/'adapt_interior_art.py')
art=importlib.util.module_from_spec(spec);spec.loader.exec_module(art)


def sha(raw):return hashlib.sha256(raw).hexdigest()
def words(raw):return [x[0] for x in struct.iter_unpack('<H',raw)]


class RemainingInteriorArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=json.loads((HERE/'interior-art/gate-art-receipt.json').read_text())
        cls.primary=(HERE/'interior-art/primary-metatiles.bin').read_bytes()
        cls.pa=(HERE/'interior-art/primary-attributes.bin').read_bytes()
        cls.secondary=(HERE/'interior-art/secondary-metatiles.bin').read_bytes()
        cls.sa=(HERE/'interior-art/secondary-attributes.bin').read_bytes()

    def test_all_42_maps_5811_cells_keep_full_source_attributes_physics_and_source_files(self):
        self.assertEqual(42,len(art.MAPS));count=0
        for name,(w,h) in art.MAPS.items():
            folder=HERE/'staged'/name;raw=(folder/'map.bin').read_bytes();adapted=(folder/'averon-map.bin').read_bytes()
            self.assertEqual(w*h*2,len(adapted))
            self.assertEqual(self.receipt['source_map_sha256'][name],sha(raw))
            attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
            header=json.loads((folder/'map.json').read_text())
            self.assertEqual(art.ANCHORS[name],[(e['x'],e['y']) for e in header['warp_events']])
            for old,new in zip(words(raw),words(adapted)):
                self.assertEqual(old&0xFC00,new&0xFC00)
                bank,idx=divmod(new&1023,512)
                self.assertEqual(attrs[str(old&1023)],struct.unpack_from('<H',(self.pa,self.sa)[bank],idx*2)[0])
            count+=w*h
        self.assertEqual(5811,count)

    def test_real_building_prefix_shop_prefix_and_secondary_headroom(self):
        self.assertEqual(self.primary,(ENGINE/'data/tilesets/primary/building/metatiles.bin').read_bytes())
        self.assertEqual(self.pa,(ENGINE/'data/tilesets/primary/building/metatile_attributes.bin').read_bytes())
        prefix=(ENGINE/'data/tilesets/secondary/shop/metatiles.bin').read_bytes()
        attrs=(ENGINE/'data/tilesets/secondary/shop/metatile_attributes.bin').read_bytes()
        self.assertTrue(self.secondary.startswith(prefix));self.assertTrue(self.sa.startswith(attrs))
        self.assertEqual(8,len(self.primary)//16);self.assertEqual(331,len(self.secondary)//16)
        self.assertEqual(181,self.receipt['remaining_secondary_slots'])

    def test_every_asset_input_is_existing_stock_building_shop_or_stock_gate(self):
        used=self.receipt['existing_averon_sha256'];self.assertGreater(len(used),10)
        for path,expected in used.items():
            self.assertTrue(path.startswith(('data/tilesets/primary/building/','data/tilesets/secondary/shop/')) or path=='data/layouts/Route110_SeasideCyclingRoadEntrance/map.bin')
            canonical=art.shared.pack.accepted.base.verified_file(ROOT,ENGINE.relative_to(ROOT)/path,'HEAD')
            self.assertEqual(expected,sha(canonical))
        self.assertIn('NOT_FINAL_OR_RUNTIME_ACCEPTANCE',self.receipt['status'])

    def test_exact_rendered_pixels_and_graphic_palette_dependencies_for_all_maps(self):
        base=art.shared.pack.accepted.base;dual=art.shared.pack.accepted.dual
        pp='data/tilesets/primary/building/';sp='data/tilesets/secondary/shop/'
        images=[dual.indexed((ENGINE/(p+'tiles.png')).read_bytes()) for p in (pp,sp)]
        palettes={i:base.palette((ENGINE/((pp if i<6 else sp)+'palettes/%02d.pal'%i)).read_bytes()) for i in range(16)}
        for name,(w,h) in art.MAPS.items():
            folder=HERE/'staged'/name;raw=(folder/'averon-map.bin').read_bytes()
            dual.closure(raw+(folder/'border.bin').read_bytes(),[self.primary,self.secondary],images)
            expected=dual.render(raw,[self.primary,self.secondary],images,palettes,w,h)
            with Image.open(folder/'averon.png') as actual:
                self.assertEqual((w*16,h*16),actual.size)
                self.assertEqual(expected.tobytes(),actual.convert(expected.mode).tobytes())

    def test_changed_portal_or_non_neutral_fixture_refused_before_any_output(self):
        name='Route222_Access'
        for mutation in ('missing','reordered','outside','scripted'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory() as temp:
                source=Path(temp)/'source';folder=source/'staged'/name;folder.mkdir(parents=True)
                for filename in ('map.bin','border.bin','map.json','attributes.json'):
                    shutil.copyfile(HERE/'staged'/name/filename,folder/filename)
                h=json.loads((folder/'map.json').read_text())
                if mutation=='missing':h['warp_events']=[]
                if mutation=='reordered':h['warp_events'].reverse()
                if mutation=='outside':h['warp_events'][0]['x']=999
                if mutation=='scripted':h['object_events']=[{'script':'not_allowed'}]
                (folder/'map.json').write_text(json.dumps(h))
                out=Path(temp)/'out'
                with self.assertRaises(ValueError):
                    art.shared.build(ENGINE,out,source_root=source,maps={name:art.MAPS[name]},expected_anchors={name:art.ANCHORS[name]})
                self.assertFalse(out.exists())


if __name__=='__main__':unittest.main()
