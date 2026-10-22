"""Four existing-art gates reuse the default-compatible central packer."""
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/eastern-loop'
spec=importlib.util.spec_from_file_location('eastern_gate_art_test',HERE/'adapt_gate_art.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ENGINE=HERE.parents[3]/'engine'


class EasternGateTest(unittest.TestCase):
    def setUp(self):
        self.banks=[(HERE/'gate-art'/p).read_bytes() for p in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin')]
        self.receipt=json.loads((HERE/'gate-art-receipt.json').read_text())

    def test_all432_cells_keep_complete_source_attributes_collision_and_elevation(self):
        count=0
        for name in a.MAPS:
            folder=HERE/'staged'/name;raw=(folder/'map.bin').read_bytes();new=(folder/'averon-map.bin').read_bytes()
            self.assertEqual(len(raw),len(new));source=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
            self.assertEqual(a.shared.pack.accepted.base.sha(raw),self.receipt['source_map_sha256'][name])
            for (old,),(adapted,) in zip(struct.iter_unpack('<H',raw),struct.iter_unpack('<H',new)):
                self.assertEqual(old&0xFC00,adapted&0xFC00);b,i=divmod(adapted&1023,512)
                self.assertEqual(a.shared.pack.attribute((self.banks[1],self.banks[3])[b],i),source[str(old&1023)]);count+=1
        self.assertEqual(count,432)

    def test_only_real_primary_and_original_shop_prefix_within_budget(self):
        self.assertEqual(self.receipt['primary_records'],8)
        for bank,name,indices in [('primary','building',(0,1)),('secondary','shop',(2,3))]:
            for idx,filename in zip(indices,('metatiles.bin','metatile_attributes.bin')):
                original=(ENGINE/'data/tilesets'/bank/name/filename).read_bytes()
                self.assertEqual(self.banks[idx][:len(original)],original)
        self.assertEqual(self.receipt['secondary_records'],298)
        self.assertEqual(self.receipt['remaining_secondary_slots'],214)

    def test_every_preview_is_rendered_from_actual_current_averon_dependencies(self):
        dual=a.shared.pack.accepted.dual;base=dual.base
        paths=['data/tilesets/primary/building/','data/tilesets/secondary/shop/']
        images=[dual.indexed((ENGINE/(p+'tiles.png')).read_bytes()) for p in paths]
        palettes={i:base.palette((ENGINE/(paths[i>=6]+'palettes/%02d.pal'%i)).read_bytes()) for i in range(16)}
        for name,(w,h) in a.MAPS.items():
            folder=HERE/'staged'/name;raw=(folder/'averon-map.bin').read_bytes();border=(folder/'border.bin').read_bytes()
            self.assertEqual(dual.closure(raw+border,[self.banks[0],self.banks[2]],images),self.receipt['dependencies'][name])
            rendered=dual.render(raw,[self.banks[0],self.banks[2]],images,palettes,w,h)
            with dual.Image.open(folder/'averon.png') as published:self.assertEqual(rendered.tobytes(),published.convert('RGB').tobytes())

    def test_exact_anchor_order_single_retained_exit_and_bad_inputs(self):
        for name in a.MAPS:
            h=json.loads((HERE/'staged'/name/'map.json').read_text())
            self.assertEqual([(w['x'],w['y']) for w in h['warp_events']],a.ANCHORS[name])
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
        self.assertEqual(a.ANCHORS['Route212_Access'],[(4,9)])
        primary=self.banks[0]+bytes(8192-len(self.banks[0]));pa=self.banks[1]+bytes(1024-len(self.banks[1]))
        for anchors,warps in [([],[]),([(4,9),(4,9)],[dict(x=4,y=9)]),([(4,1)],[dict(x=4,y=9)]),([(99,99)],[dict(x=99,y=99)])]:
            with self.subTest(anchors=anchors),self.assertRaises(ValueError):
                a.shared.candidate(bytes(9*11*2),9,11,warps,[bytes(1024),bytes(1024)],primary,pa,self.banks[2],self.banks[3],expected_anchors=anchors)

    def test_original_central_defaults_reproduce_every_existing_art_byte(self):
        central=HERE.parent/'hearthome-solaceon'
        self.assertEqual(a.shared.MAPS,{'Route208_Access':(13,9),'Route209_Access':(13,9)})
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'out';a.shared.build(ENGINE,out);count=0
            for name in a.shared.MAPS:
                for suffix,target in [('.bin','averon-map.bin'),('.png','averon.png')]:
                    self.assertEqual((out/(name+suffix)).read_bytes(),(central/'staged'/name/target).read_bytes());count+=1
            for p in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin'):
                self.assertEqual((out/p).read_bytes(),(central/'gate-art'/p).read_bytes());count+=1
            self.assertEqual(count,8)


if __name__=='__main__':unittest.main()
