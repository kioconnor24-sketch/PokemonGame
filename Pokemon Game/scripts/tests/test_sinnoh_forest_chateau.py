"""Real six-map source fixtures, edge warps and the malformed donor border."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import unittest

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/forest-chateau'
spec=importlib.util.spec_from_file_location('forest_stage',HERE/'stage_forest.py');stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)


class ForestTest(unittest.TestCase):
    def setUp(self):
        self.receipt=json.loads((HERE/'source-receipt.json').read_text())
        self.headers=copy.deepcopy(self.receipt['source_geometry_headers'])
        self.layouts={n:dict(width=v[0],height=v[1]) for n,v in stage.MAPS.items()}
        self.raws={}
        for name in stage.MAPS:
            b=bytearray((HERE/'staged'/name/'map.bin').read_bytes());w=stage.MAPS[name][0]
            for c in self.receipt['closure_changes'][name]:struct.pack_into('<H',b,(w*c['y']+c['x'])*2,c['before'])
            self.raws[name]=bytes(b)

    def build(self):return stage.base.sanitize(self.headers,self.layouts,self.raws)

    def test_every_published_cell_header_and_closure_reproduces(self):
        staged,closures,_=self.build();count=0
        for name,(raw,h) in staged.items():
            self.assertEqual(raw,(HERE/'staged'/name/'map.bin').read_bytes())
            self.assertEqual(h,json.loads((HERE/'staged'/name/'map.json').read_text()))
            self.assertEqual(closures[name],self.receipt['closure_changes'][name])
            self.assertEqual(stage.base.sha(self.raws[name]),self.receipt['maps'][name]['source_sha256'])
            for (old,),(new,) in zip(struct.iter_unpack('<H',self.raws[name]),struct.iter_unpack('<H',raw)):
                self.assertEqual(old&0xF3FF,new&0xF3FF);count+=1
        self.assertEqual(count,8343)

    def test_boundary_warps_are_retained_without_closing_their_source_cells(self):
        staged,_,_=self.build();count=0
        for name,(raw,h) in staged.items():
            w,height=stage.MAPS[name][:2]
            for e in h['warp_events']:
                if e['x'] in (0,w-1) or e['y'] in (0,height-1):
                    i=(e['y']*w+e['x'])*2;self.assertEqual(raw[i:i+2],self.raws[name][i:i+2]);count+=1
        self.assertEqual(count,11)

    def test_forest4_compacts_to0_with_three_entrance_returns(self):
        staged,_,tr=self.build();self.assertEqual(tr['EternaForest'],{4:0})
        self.assertEqual(staged['EternaForest'][1]['warp_events'][0]['dest_warp_id'],'0')
        self.assertEqual([e['dest_warp_id'] for e in staged['OldChateau_Entrance'][1]['warp_events'][:3]],['0']*3)
        self.assertEqual(sum(len(h['warp_events']) for _,h in staged.values()),31)

    def test_all_seventeen_upstairs_room_warps_keep_individual_indices(self):
        staged,_,tr=self.build();name='OldChateau_2F'
        self.assertEqual(tr[name],{i:i for i in range(17)})
        self.assertEqual(staged[name][1]['warp_events'],self.headers[name]['warp_events'])

    def test_external205_mouths_closed_and_gameplay_absent(self):
        staged,_,_=self.build();raw,h=staged['EternaForest'];w=stage.MAPS['EternaForest'][0]
        for e in self.headers['EternaForest']['warp_events'][:4]:self.assertEqual((struct.unpack_from('<H',raw,(e['y']*w+e['x'])*2)[0]>>10)&3,1)
        for _,h in staged.values():
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER');self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])

    def test_broken_pair_missing_return_and_duplicate_edge_anchor_rejected(self):
        original=copy.deepcopy(self.headers)
        for target,index,key,value in [('OldChateau_Entrance',0,'dest_warp_id','0'),('OldChateau_2F',2,'dest_warp_id','99'),('OldChateau_Entrance',1,'x',9)]:
            self.headers=copy.deepcopy(original);self.headers[target]['warp_events'][index][key]=value
            with self.subTest(change=(target,index,key)),self.assertRaises(ValueError):self.build()

    def test_every_source_attribute_used_by_map_and_repaired_border_exists(self):
        for name in stage.MAPS:
            folder=HERE/'staged'/name;attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
            used={c[0]&1023 for c in struct.iter_unpack('<H',(folder/'map.bin').read_bytes()+(folder/'border.bin').read_bytes())}
            self.assertEqual(used,{int(x) for x in attrs})

    def test_bad_outdoor_border_is_replaced_only_for_the_identical_room_geometry(self):
        a=HERE/'staged/OldChateau_SideRoom_1';b=HERE/'staged/OldChateau_SideRoom_2'
        self.assertEqual(self.raws['OldChateau_SideRoom_1'],self.raws['OldChateau_SideRoom_2'])
        self.assertEqual((a/'border.bin').read_bytes(),(b/'border.bin').read_bytes())
        spec=self.receipt['border_substitutions']['OldChateau_SideRoom_2'];original=bytes.fromhex('d401d501dc01dd01')
        self.assertEqual(stage.base.sha(original),spec['expected_sha256'])
        self.assertEqual(stage.base.repair_border(original,spec,(a/'border.bin').read_bytes()),bytes.fromhex('0100010001000100'))
        with self.assertRaises(ValueError):stage.base.repair_border(original[:-1],spec,(a/'border.bin').read_bytes())
        with self.assertRaises(ValueError):stage.base.repair_border(original,spec,b'')

    def test_no_source_mutation_and_deterministic_pure_replay(self):
        before=copy.deepcopy((self.headers,self.layouts,self.raws));self.assertEqual(self.build(),self.build());self.assertEqual(before,(self.headers,self.layouts,self.raws))

class ExistingArtTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('forest_render',HERE/'render_existing.py')
        cls.art=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.art)

    def test_published_metadata_keeps_every_used_source_attribute_word(self):
        from hashlib import sha256
        receipt=json.loads((HERE/'graphics-compatibility.json').read_text())
        engine=HERE.parents[3]/'engine'
        for path,expected in receipt['existing_averon_sha256'].items():
            # Receipt hashes are committed blob bytes; declared PAL CRLF checkout
            # normalization is already enforced by the shared verified_file helper.
            raw=(engine/path).read_bytes()
            if path.endswith('.pal'):raw=raw.replace(b'\r\n',b'\n')
            self.assertEqual(sha256(raw).hexdigest(),expected)
        banks=[(engine/'data/tilesets/primary/building/metatile_attributes.bin').read_bytes(),(HERE/'generic-attributes.bin').read_bytes()]
        for name in self.art.MAPS:
            folder=HERE/'staged'/name;attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
            for mid,value in attrs.items():
                b,i=divmod(int(mid),512);self.assertEqual(struct.unpack_from('<H',banks[b],i*2)[0],value)
        self.assertTrue(receipt['primary_pixels_byte_identical'] and receipt['secondary_pixels_byte_identical'] and receipt['all_used_palette_colors_equal'])

    def test_published_four_renders_use_only_existing_averon_pixels_and_colors(self):
        from PIL import Image
        engine=HERE.parents[3]/'engine';d=self.art.dual
        families=['data/tilesets/primary/building/','data/tilesets/secondary/generic_building/']
        images=[d.indexed((engine/f/'tiles.png').read_bytes()) for f in families]
        banks=[(engine/families[0]/'metatiles.bin').read_bytes(),(HERE/'generic-metatiles.bin').read_bytes()]
        receipt=json.loads((HERE/'graphics-compatibility.json').read_text());palettes={i:d.base.palette((engine/families[0 if i<6 else 1]/('palettes/%02d.pal'%i)).read_bytes()) for i in receipt['used_palette_ids']}
        for name,(w,h) in self.art.MAPS.items():
            raw=(HERE/'staged'/name/'map.bin').read_bytes();image=d.render(raw,banks,images,palettes,w,h)
            with Image.open(HERE/'staged'/name/'averon.png') as published:self.assertEqual(published.convert('RGB').tobytes(),image.convert('RGB').tobytes())


if __name__=='__main__':unittest.main()
