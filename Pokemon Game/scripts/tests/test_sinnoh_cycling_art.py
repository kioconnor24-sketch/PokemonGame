"""Cycling Road art keeps all elevations, layer behaviors and original portals."""
import importlib.util
import json
from pathlib import Path
import struct
import unittest
from PIL import Image

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/eterna-cycle'
spec=importlib.util.spec_from_file_location('cycling_materials',HERE/'adapt_cycling_art.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ENGINE=HERE.parents[3]/'engine'


class CyclingArtTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.receipt=json.loads((HERE/'cycling-art-receipt.json').read_text())

    def family(self,name):
        family='cycling' if name in a.OUTDOORS else 'gate';folder=HERE/(family+'-art')
        banks=[(folder/(b+'-metatiles.bin')).read_bytes() for b in ('primary','secondary')]
        attrs=[(folder/(b+'-attributes.bin')).read_bytes() for b in ('primary','secondary')]
        return banks,attrs

    def test_all_cells_retain_collision_elevation_and_full_source_attributes(self):
        count=0
        for name in a.MAPS:
            raw,border,header,source=a.source_data(name);banks,attrs=self.family(name);folder=HERE/'staged'/name
            adapted=(folder/'averon-map.bin').read_bytes()+(folder/'averon-border.bin').read_bytes()
            self.assertEqual(len(adapted),len(raw+border))
            for (old,),(new,) in zip(struct.iter_unpack('<H',raw+border),struct.iter_unpack('<H',adapted)):
                self.assertEqual(old&0xFC00,new&0xFC00);b,i=divmod(new&1023,512)
                self.assertEqual(a.pack.attribute(attrs[b],i),source[str(old&1023)]);count+=1
        self.assertEqual(count,self.receipt['verified_physics_behavior_cells'])

    def test_all_271_elevation15_positions_and_other_height_pairs_unchanged(self):
        raw,*_=a.source_data('Route206');dst=(HERE/'staged/Route206/averon-map.bin').read_bytes()
        heights=lambda data:[c[0]>>12 for c in struct.iter_unpack('<H',data)]
        self.assertEqual(heights(raw),heights(dst));self.assertEqual(heights(raw).count(15),271)
        self.assertEqual(self.receipt['route206_elevation15_preserved'],271)
        raw,*_=a.source_data('Route211_West');dst=(HERE/'staged/Route211_West/averon-map.bin').read_bytes()
        self.assertEqual(heights(raw),heights(dst));self.assertEqual(heights(raw).count(15),19)

    def test_two_families_have_correct_palette_graphics_closure_and_actual_rgb_previews(self):
        dual=a.pack.accepted.dual;base=a.pack.accepted.base
        for name,(w,h) in a.MAPS.items():
            folders=('primary/general','secondary/mauville') if name in a.OUTDOORS else ('primary/building','secondary/shop')
            images=[dual.indexed((ENGINE/('data/tilesets/'+f+'/tiles.png')).read_bytes()) for f in folders]
            banks,attrs=self.family(name);folder=HERE/'staged'/name;raw=(folder/'averon-map.bin').read_bytes();border=(folder/'averon-border.bin').read_bytes()
            deps=dual.closure(raw+border,banks,images);self.assertEqual(deps,self.receipt['dependencies'][name])
            palettes={i:base.palette((ENGINE/('data/tilesets/'+folders[i>=6]+'/palettes/%02d.pal'%i)).read_bytes()) for i in deps['palettes']}
            image=dual.render(raw,banks,images,palettes,w,h)
            with Image.open(folder/'averon.png') as published:self.assertEqual(image.tobytes(),published.convert('RGB').tobytes())

    def test_real_primary_sizes_and_bank_capacity_no_stock_mauville_overwrite(self):
        for name,primary in [('Route206','general'),('Route206_North','building')]:
            banks,attrs=self.family(name);p=ENGINE/('data/tilesets/primary/'+primary)
            self.assertEqual(banks[0],(p/'metatiles.bin').read_bytes());self.assertEqual(attrs[0],(p/'metatile_attributes.bin').read_bytes())
            self.assertLessEqual(len(banks[1]),8192);self.assertEqual(len(banks[1]),len(attrs[1])*8)
        self.assertLess(self.receipt['family_records']['cycling'][1],64)
        self.assertEqual(self.receipt['family_records']['gate'],[8,295])
        self.assertEqual((ENGINE/'data/tilesets/secondary/mauville/metatiles.bin').stat().st_size,510*16)

    def test_both_outdoors_use_only_shared_general_graphics_and_palettes(self):
        # They can later share an Eterna City secondary graphics family, provided
        # that integration retains the same accumulated metadata IDs/prefix.
        for name in a.OUTDOORS:
            deps=self.receipt['dependencies'][name]
            self.assertTrue(all(t<512 for t in deps['graphic_tiles']))
            self.assertTrue(all(p<6 for p in deps['palettes']))

    def test_source_geometry_header_warp_and_current_asset_hashes_remain_exact(self):
        base=a.pack.accepted.base;root=Path(base.git(ENGINE,'rev-parse','--show-toplevel').decode().strip())
        for name,files in self.receipt['source_sha256'].items():
            for p,h in files.items():self.assertEqual(base.sha((HERE/'staged'/name/p).read_bytes()),h)
        for p,h in self.receipt['existing_averon_sha256'].items():
            self.assertEqual(base.sha(base.verified_file(root,ENGINE.relative_to(root)/p,'HEAD')),h)
        raw,border,header,attrs=a.source_data('Route206')
        self.assertEqual([(w['dest_map'],str(w['dest_warp_id'])) for w in header['warp_events']],
                         [('MAP_ROUTE206_NORTH','1'),('MAP_ROUTE206_SOUTH','0'),('MAP_ROUTE206_SOUTH','0'),('MAP_ROUTE206_SOUTH','1'),('MAP_ROUTE206_SOUTH','1')])

    def test_malformed_dimensions_unknown_primary_secondary_and_missing_semantics_rejected(self):
        raw,border,h,attrs=a.source_data('Route206');banks,_=self.family('Route206')
        for mode in ('dimensions','primary','secondary','missing_attribute'):
            r=raw;source=dict(attrs)
            if mode=='dimensions':r=raw[:-1]
            elif mode=='missing_attribute':source.pop(str(struct.unpack_from('<H',raw)[0]&1023))
            else:
                r=bytearray(raw);struct.pack_into('<H',r,0,500 if mode=='primary' else 1023)
            with self.subTest(mode=mode),self.assertRaises(ValueError):a.desired_art('Route206',r,border,h,banks,source)

    def test_bad_gateway_anchors_rejected_and_original_input_immutable(self):
        raw,border,h,attrs=a.source_data('Route206_North');banks,_=self.family('Route206_North')
        expected=json.dumps(h,sort_keys=True);wanted=a.desired_art('Route206_North',raw,border,h,banks,attrs)
        self.assertEqual(len(wanted),(len(raw)+len(border))//2);self.assertEqual(json.dumps(h,sort_keys=True),expected)
        h['warp_events'][1]['y']=8
        with self.assertRaises(ValueError):a.desired_art('Route206_North',raw,border,h,banks,attrs)


if __name__=='__main__':unittest.main()
