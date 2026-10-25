"""Source-derived exterior, authored seam, and save-neutral staging guards."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/stark-approach'
s=importlib.util.spec_from_file_location('approach_tests',HERE/'build_source.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class ApproachTests(unittest.TestCase):
    def setUp(self):
        self.geometry,self.plan=m.load()
        self.route=(m.ROUTE/'staged/Route227/averon-map.bin').read_bytes()
        self.room=(m.BASE/'staged/Room1/map.bin').read_bytes()
        self.header=json.loads((m.BASE/'staged/Room1/map.json').read_text())

    def candidate(self):return m.construct(self.geometry,self.route,self.room,self.header)

    def test_only_two_route_cells_and_one_room_cell_changed(self):
        outside,route,room,oh,rh,a=self.candidate()
        for before,after,w,expected in [(self.route,route,48,{(28,0),(29,0)}),(self.room,room,64,{(20,29)})]:
            changed={(i%w,i//w) for i,((x,),(y,)) in enumerate(zip(struct.iter_unpack('<H',before),struct.iter_unpack('<H',after))) if x!=y}
            self.assertEqual(changed,expected)
        self.assertEqual(a['source_marked_surfaces'],249)
        self.assertTrue(a['source_warp_prefix_preserved'])
        self.assertEqual(rh['warp_events'][:-1],self.header['warp_events'])
        self.assertEqual(rh['warp_events'][-1]['elevation'],10)
        self.assertEqual(struct.unpack_from('<H',room,2*(29*64+20))[0]>>12,10)

    def test_every_unmatched_outside_boundary_is_closed(self):
        raw,*_=self.candidate();words=struct.unpack('<1024H',raw)
        expected={(28,31),(29,31)}
        opened={(x,y) for x,y in {(i,0) for i in range(32)}|{(i,31) for i in range(32)}|{(0,i) for i in range(32)}|{(31,i) for i in range(32)} if not words[y*32+x]&0xc00}
        self.assertEqual(opened,expected)
        self.assertFalse(any(v>>12==15 for v in words))
        self.assertEqual(self.geometry['props_or_model_emitted'],False)

    def test_reciprocal_seam_negative_offset_blocked_elevation_and_extra_lane(self):
        out,route,room,oh,rh,a=self.candidate()
        rh=dict(connections=[dict(map='MAP_SINNOH_STARK_OUTSIDE',direction='up',offset=0)])
        self.assertEqual(m.validate_seam(out,route,oh,rh),[28,29])
        bad=copy.deepcopy(rh);bad['connections'][0]['offset']=1
        with self.assertRaisesRegex(ValueError,'reciprocal'):m.validate_seam(out,route,oh,bad)
        for v,error in [(0x3401,'lanes'),(0x4001,'elevation')]:
            changed=bytearray(route);struct.pack_into('<H',changed,2*28,v)
            with self.assertRaisesRegex(ValueError,error):m.validate_seam(out,changed,oh,rh)
        extra=bytearray(out);rr=bytearray(route)
        struct.pack_into('<H',extra,2*(31*32+27),0x3001);struct.pack_into('<H',rr,2*27,0x3001)
        with self.assertRaisesRegex(ValueError,'lanes'):m.validate_seam(extra,rr,oh,rh)

    def test_actual_render_replay_paths_and_parent_family_prefix(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'new';receipt=m.build(ROOT/'Pokemon Game/engine',out)
            self.assertEqual(receipt,json.loads((HERE/'receipt.json').read_text()))
            for path,h in receipt['output_sha256'].items():self.assertEqual(m.base.sha((out/path).read_bytes()),h);self.assertEqual((out/path).read_bytes(),(HERE/path).read_bytes())
            for name in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin'):
                old=(m.BASE/'cave-family'/name).read_bytes();self.assertEqual((out/'cave-family'/name).read_bytes()[:len(old)],old)
            attrs=json.loads((out/'staged/Outside/attributes.json').read_text());raw=(out/'staged/Outside/map.bin').read_bytes()
            for x in (28,29):self.assertTrue(m.static_path(raw,32,32,[x,31],[14,7],attrs))
            # The rejected initial proposal genuinely points into a closed pocket.
            self.assertFalse(m.static_path(raw,32,32,[4,31],[14,7],attrs))
            for name in ('Outside','Room1','Route227'):
                h=json.loads((out/'staged'/name/'map.json').read_text())
                self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
                for key in ('object_events','coord_events','bg_events'):self.assertFalse(h[key])
            self.assertIn('NOT_RUNTIME_ACCEPTANCE',receipt['status'])

    def test_invalid_source_duplicates_and_reopening_source_are_rejected(self):
        bad=copy.deepcopy(self.geometry);bad['surfaces'].append(copy.deepcopy(bad['surfaces'][0]))
        with self.assertRaisesRegex(ValueError,'invalid outside'):m.construct(bad,self.route,self.room,self.header)
        bad=copy.deepcopy(self.geometry);bad['surfaces'][0]['permission']=0x8002
        with self.assertRaisesRegex(ValueError,'invalid outside'):m.construct(bad,self.route,self.room,self.header)
        route=bytearray(self.route);struct.pack_into('<H',route,2*28,0x3001)
        with self.assertRaisesRegex(ValueError,'unexpected open'):m.construct(self.geometry,route,self.room,self.header)
        room=bytearray(self.room);struct.pack_into('<H',room,2*(29*64+20),0x3001)
        with self.assertRaisesRegex(ValueError,'already open'):m.construct(self.geometry,self.route,room,self.header)

    def test_dirty_geometry_and_unsafe_output_refused_before_write(self):
        original=Path.read_bytes
        def dirty(path):
            raw=original(path)
            return raw+b' ' if path==HERE/'geometry.json' else raw
        with tempfile.TemporaryDirectory() as t,patch.object(Path,'read_bytes',dirty):
            out=Path(t)/'never'
            with self.assertRaisesRegex(ValueError,'dirty'):m.build(ROOT/'Pokemon Game/engine',out)
            self.assertFalse(out.exists())
        with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ROOT/'Pokemon Game/engine',ROOT/'Pokemon Game/engine/bad')

if __name__=='__main__':unittest.main()
