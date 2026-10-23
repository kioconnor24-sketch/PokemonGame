"""Neutral permitted-art adaptation; source physics and source files stay fixed."""
import importlib.util
import json
from pathlib import Path
import struct
import unittest

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/hearthome-solaceon'
spec=importlib.util.spec_from_file_location('central_gate_art',HERE/'adapt_gate_art.py');art=importlib.util.module_from_spec(spec);spec.loader.exec_module(art)
ENGINE=HERE.parents[3]/'engine'


class GateArtTest(unittest.TestCase):
    def setUp(self):
        self.banks=[(HERE/'gate-art'/p).read_bytes() for p in ['primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin']]
        self.receipt=json.loads((HERE/'gate-art-receipt.json').read_text())

    def test_all234_cells_preserve_physics_and_complete_source_behavior_layer(self):
        count=0
        for name in art.MAPS:
            folder=HERE/'staged'/name;raw=(folder/'map.bin').read_bytes();new=(folder/'averon-map.bin').read_bytes()
            self.assertEqual(art.pack.accepted.base.sha(raw),self.receipt['source_map_sha256'][name])
            source=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
            self.assertEqual(len(raw),len(new))
            for (old,),(adapted,) in zip(struct.iter_unpack('<H',raw),struct.iter_unpack('<H',new)):
                self.assertEqual(old&0xFC00,adapted&0xFC00);bank,i=divmod(adapted&1023,512)
                self.assertEqual(art.pack.attribute((self.banks[1],self.banks[3])[bank],i),source[str(old&1023)]);count+=1
        self.assertEqual(count,234)

    def test_current_shop_prefix_and_building_prefix_unmodified(self):
        for bank,name in [('primary','building'),('secondary','shop')]:
            for filename in ['metatiles.bin','metatile_attributes.bin']:
                raw=(ENGINE/'data/tilesets'/bank/name/filename).read_bytes();candidate=(HERE/'gate-art'/((bank+'-metatiles.bin') if filename=='metatiles.bin' else bank+'-attributes.bin')).read_bytes()
                self.assertEqual(candidate[:len(raw)],raw)
        self.assertLessEqual(self.receipt['secondary_records'],512)

    def test_published_images_reproduce_with_existing_pixels_and_palettes(self):
        from PIL import Image
        d=art.pack.accepted.dual;base=d.base;primary='data/tilesets/primary/building/';secondary='data/tilesets/secondary/shop/'
        images=[d.indexed((ENGINE/p/'tiles.png').read_bytes()) for p in (primary,secondary)]
        palettes={i:base.palette((ENGINE/(primary if i<6 else secondary)/('palettes/%02d.pal'%i)).read_bytes()) for i in range(16)}
        for name,(w,h) in art.MAPS.items():
            raw=(HERE/'staged'/name/'averon-map.bin').read_bytes();image=d.render(raw,[self.banks[0],self.banks[2]],images,palettes,w,h)
            with Image.open(HERE/'staged'/name/'averon.png') as published:self.assertEqual(image.tobytes(),published.tobytes())

    def test_source_header_warps_remain_unallocated_and_unmodified(self):
        receipt=json.loads((HERE/'source-receipt.json').read_text())
        for name in art.MAPS:
            header=json.loads((HERE/'staged'/name/'map.json').read_text())
            self.assertEqual(header['region_map_section'],'MAPSEC_PENDING_OWNER');self.assertEqual([(w['x'],w['y']) for w in header['warp_events']],[(1,5),(11,5)])
            self.assertEqual(art.pack.accepted.base.sha((HERE/'staged'/name/'map.bin').read_bytes()),receipt['maps'][name]['staged_sha256'])

    def test_wrong_source_anchor_dimension_or_missing_template_rejected(self):
        raw=bytes(13*9*2);source_attrs=[bytes(1024),bytes(1024)]
        for w,h,warps in [(13,9,[]),(0,9,[{'x':1,'y':5},{'x':11,'y':5}]),(13,9,[{'x':1,'y':4},{'x':11,'y':5}])]:
            with self.subTest(width=w,height=h),self.assertRaises(ValueError):art.candidate(raw,w,h,warps,source_attrs,*self.banks)
        with self.assertRaises(ValueError):art.candidate(raw,13,9,[{'x':1,'y':5},{'x':11,'y':5}],source_attrs,bytes(8192),bytes(1024),b'',b'')

if __name__=='__main__':unittest.main()
