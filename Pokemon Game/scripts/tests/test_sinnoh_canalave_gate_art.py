"""Route218's single/reversed portals retain exact physics and neutral art."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from unittest import mock
HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/canalave-west'
spec=importlib.util.spec_from_file_location('canalave_gate_test',HERE/'adapt_gate_art.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ENGINE=HERE.parents[3]/'engine'

class CanalaveGateArtTest(unittest.TestCase):
    def setUp(self):
        self.b=[(HERE/'gate-art'/p).read_bytes() for p in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin')]
        self.r=json.loads((HERE/'gate-art-receipt.json').read_text())

    def test_all234_cells_keep_original_collision_elevation_and_full_attributes(self):
        count=0
        for name in a.MAPS:
            folder=HERE/'staged'/name;raw=(folder/'map.bin').read_bytes();new=(folder/'averon-map.bin').read_bytes()
            self.assertEqual(len(raw),len(new));attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
            self.assertEqual(a.shared.pack.accepted.base.sha(raw),self.r['source_map_sha256'][name])
            for (old,),(v,) in zip(struct.iter_unpack('<H',raw),struct.iter_unpack('<H',new)):
                self.assertEqual(old&0xFC00,v&0xFC00);b,i=divmod(v&1023,512)
                self.assertEqual(a.shared.pack.attribute((self.b[1],self.b[3])[b],i),attrs[str(old&1023)]);count+=1
        self.assertEqual(count,234)
        self.assertEqual(self.r['verified_physics_behavior_cells'],234)

    def test_existing_building_shop_prefix_and_hardware_budgets_are_preserved(self):
        for bank,name,indices in [('primary','building',(0,1)),('secondary','shop',(2,3))]:
            for idx,filename in zip(indices,('metatiles.bin','metatile_attributes.bin')):
                raw=(ENGINE/'data/tilesets'/bank/name/filename).read_bytes();self.assertEqual(self.b[idx][:len(raw)],raw)
        self.assertEqual(self.r['primary_records'],8);self.assertEqual(self.r['secondary_records'],295)
        self.assertEqual(len(self.b[2]),len(self.b[3])*8);self.assertLessEqual(len(self.b[2]),8192)
        self.assertEqual(self.r['remaining_secondary_slots'],217)

    def test_real_current_dependency_closure_and_both_rendered_previews(self):
        dual=a.shared.pack.accepted.dual;base=dual.base;paths=['data/tilesets/primary/building/','data/tilesets/secondary/shop/']
        images=[dual.indexed((ENGINE/(p+'tiles.png')).read_bytes()) for p in paths]
        palettes={i:base.palette((ENGINE/(paths[i>=6]+'palettes/%02d.pal'%i)).read_bytes()) for i in range(16)}
        for name,(w,h) in a.MAPS.items():
            folder=HERE/'staged'/name;raw=(folder/'averon-map.bin').read_bytes();border=(folder/'border.bin').read_bytes()
            self.assertEqual(dual.closure(raw+border,[self.b[0],self.b[2]],images),self.r['dependencies'][name])
            actual=dual.render(raw,[self.b[0],self.b[2]],images,palettes,w,h)
            with dual.Image.open(folder/'averon.png') as im:self.assertEqual(actual.tobytes(),im.convert('RGB').tobytes())

    def test_closed_jubilife_gate_is_visibly_blocked_and_no_original_portal_reordered(self):
        for name in a.MAPS:
            h=json.loads((HERE/'staged'/name/'map.json').read_text())
            self.assertEqual([(w['x'],w['y']) for w in h['warp_events']],a.ANCHORS[name])
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
            self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])
        f=HERE/'staged/Route218_East';old=struct.unpack('<117H',(f/'map.bin').read_bytes());new=struct.unpack('<117H',(f/'averon-map.bin').read_bytes())
        self.assertEqual(old[5*13+11]>>10&3,1);self.assertEqual(new[5*13+11]>>10&3,1)
        bank,mid=divmod(new[5*13+11]&1023,512)
        stock=(ENGINE/'data/tilesets/secondary/shop/metatiles.bin').read_bytes()
        self.assertEqual(a.shared.pack.words((self.b[0],self.b[2])[bank],mid),a.shared.pack.words(stock,a.shared.COUNTER-512))
        self.assertEqual(a.ANCHORS,{'Route218_East':[(1,5)],'Route218_West':[(11,5),(1,5)]})

    def test_wrong_single_exit_missing_return_and_reordered_west_are_rejected_before_output(self):
        for wrong in ({'Route218_East':[(11,5)],'Route218_West':a.ANCHORS['Route218_West']},
                      {'Route218_East':[(1,5)],'Route218_West':[(1,5),(11,5)]},
                      {'Route218_East':[],'Route218_West':a.ANCHORS['Route218_West']}):
            with tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp)/'out'
                with mock.patch.object(a,'ANCHORS',wrong),self.assertRaisesRegex(ValueError,'source gate anchors changed'):a.build(ENGINE,out)
                self.assertFalse(out.exists())

if __name__=='__main__':unittest.main()
