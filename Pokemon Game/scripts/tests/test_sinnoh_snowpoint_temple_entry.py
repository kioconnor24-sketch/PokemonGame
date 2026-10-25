"""Derived city entry preserving six source-height Temple ice packets."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/snowpoint-temple-entry'
s=importlib.util.spec_from_file_location('temple_entry_tests',HERE/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine'
class TempleEntryTests(unittest.TestCase):
    def setUp(self):self.receipt=json.loads((HERE/'receipt.json').read_text())
    def test_only_native_doorsteps_change_source_borders_and_stair_prefix_unchanged(self):
        sources={'SnowpointCity':(HERE/'city-source/map.bin',34,{(17,8)}),
                 'Temple1F':(m.SOURCE/'staged/SinnohSnowpointTemple_1F/map.bin',32,{(8,13)})}
        for n,(p,w,expected) in sources.items():
            before=p.read_bytes();after=(HERE/'staged'/n/'map.bin').read_bytes()
            changed={(i%w,i//w) for i,((a,),(b,)) in enumerate(zip(struct.iter_unpack('<H',before),struct.iter_unpack('<H',after))) if a!=b}
            self.assertEqual(changed,expected)
            self.assertEqual(p.with_name('border.bin').read_bytes(),(HERE/'staged'/n/'border.bin').read_bytes())
        old=json.loads((m.SOURCE/'staged/SinnohSnowpointTemple_1F/map.json').read_text())
        new=json.loads((HERE/'staged/Temple1F/map.json').read_text())
        self.assertEqual(old['warp_events'],new['warp_events'][:-1])
    def test_338_ice_cells_unchanged_and_actual_two_way_ice_stop_routes(self):
        self.assertEqual(sum(self.receipt['ice_counts'].values()),338)
        old=struct.unpack('<1024H',(m.SOURCE/'staged/SinnohSnowpointTemple_1F/map.bin').read_bytes())
        raw=(HERE/'staged/Temple1F/map.bin').read_bytes();new=struct.unpack('<1024H',raw)
        self.assertEqual({i for i,v in enumerate(old) if v&1023==909},{i for i,v in enumerate(new) if v&1023==909})
        self.assertIn((14,3),m.t.stop_graph(raw,(8,13)))
        self.assertIn((8,13),m.t.stop_graph(raw,(14,3)))
        blocked=bytearray(raw);struct.pack_into('<H',blocked,2*(13*32+8),0x3401)
        self.assertNotIn((8,13),m.t.stop_graph(blocked,(14,3)))
    def test_native_trigger_elevations_and_city_sand_preserved(self):
        headers={}
        for n,w in [('SnowpointCity',34),('Temple1F',32)]:
            h=json.loads((HERE/'staged'/n/'map.json').read_text());headers[h['id']]=h
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
            for key in ('object_events','coord_events','bg_events'):self.assertFalse(h[key])
            e=h['warp_events'][0 if n=='SnowpointCity' else -1]
            raw=(HERE/'staged'/n/'map.bin').read_bytes();attrs=json.loads((HERE/'staged'/n/'attributes.json').read_text())
            v=struct.unpack_from('<H',raw,2*(e['y']*w+e['x']))[0]
            self.assertFalse(v&0xc00);self.assertEqual(v>>12,3);self.assertEqual(attrs[str(v&1023)]&255,0x61)
        city=headers['MAP_SNOWPOINT_CITY'];temple=headers['MAP_SINNOH_SNOWPOINT_TEMPLE_1F']
        self.assertEqual(city['warp_events'][0]['dest_warp_id'],'1')
        self.assertEqual(temple['warp_events'][1]['dest_warp_id'],'0')
        raw=(HERE/'staged/SnowpointCity/map.bin').read_bytes();attrs=json.loads((HERE/'staged/SnowpointCity/attributes.json').read_text())
        v=struct.unpack_from('<H',raw,2*(9*34+17))[0];self.assertEqual(attrs[str(v&1023)]&255,0x21)
    def test_replay_readonly_city_pins_and_native_family_prefixes(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'new';receipt=m.build(ENGINE,out);self.assertEqual(receipt,self.receipt)
            for p,h in receipt['output_sha256'].items():self.assertEqual(m.g.base.sha((out/p).read_bytes()),h);self.assertEqual((out/p).read_bytes(),(HERE/p).read_bytes())
        pins=json.loads((HERE/'city-source-pins.json').read_text())
        for p,v in pins['files'].items():self.assertEqual(m.g.base.sha((HERE/'city-source'/p).read_bytes()),v['sha256'])
        for p in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin'):
            old=(HERE/'city-source'/p).read_bytes();self.assertEqual((HERE/'families/SnowpointCity'/p).read_bytes()[:len(old)],old)
    def test_dirty_input_and_engine_output_refused_before_write(self):
        original=Path.read_bytes;target=HERE/'city-source/map.bin'
        def dirty(p):
            v=original(p);return bytes([v[0]^1])+v[1:] if p==target else v
        with tempfile.TemporaryDirectory() as t,patch.object(Path,'read_bytes',dirty):
            out=Path(t)/'never'
            with self.assertRaisesRegex(ValueError,'dirty'):m.build(ENGINE,out)
            self.assertFalse(out.exists())
        with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,ENGINE/'bad')
if __name__=='__main__':unittest.main()
