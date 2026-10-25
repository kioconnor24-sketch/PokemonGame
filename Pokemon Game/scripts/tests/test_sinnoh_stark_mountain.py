"""Stark physical projection: source-derived geometry, no runtime acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/stark-mountain'
s=importlib.util.spec_from_file_location('stark_test',HERE/'build_source.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class StarkSourceTests(unittest.TestCase):
    def setUp(self):self.geometry=json.loads((HERE/'geometry.json').read_text())

    def test_exact1914_supported_marked_surfaces_and_sealed_exterior(self):
        result,audit=m.construct(self.geometry)
        self.assertEqual([v['source_marked_surfaces'] for v in audit['rooms'].values()],[294,1549,71])
        self.assertEqual([v['open_cells'] for v in audit['rooms'].values()],[293,1549,71])
        self.assertEqual([v['slope_or_footprint_edge_stair_proxies'] for v in audit['rooms'].values()],[113,379,0])
        self.assertEqual([v['static_height_components'] for v in audit['rooms'].values()],[[292,1],[1487,28,20,7,7],[59,6,6]])
        self.assertEqual(len(audit['height_to_elevation']),12)
        self.assertEqual(set(audit['height_to_elevation'].values()),set(range(3,15)))
        for room,(raw,header) in result.items():
            w,h=m.DIMS[room];words=struct.unpack('<%dH'%(w*h),raw)
            source={tuple(p['tile']) for p in self.geometry['rooms'][room]['surfaces']}
            for i,v in enumerate(words):
                point=(i%w,i//w)
                expected_open=point in source and not(room=='Room1' and point==(20,29))
                self.assertEqual(not bool(v&0xc00),expected_open)
                if point[0] in (0,w-1) or point[1] in (0,h-1):self.assertTrue(v&0xc00)
                self.assertNotEqual(v>>12,15)
            self.assertEqual(header['region_map_section'],'MAPSEC_PENDING_OWNER')
            for key in ('object_events','coord_events','bg_events','connections'):self.assertFalse(header[key])

    def test_source_warps_reciprocal_and_room2_ordinary_height_graph_links_doors(self):
        result,_=m.construct(self.geometry);headers={v[1]['id']:v[1] for v in result.values()}
        self.assertEqual(sum(len(h['warp_events']) for h in headers.values()),4)
        for header in headers.values():
            for i,warp in enumerate(header['warp_events']):
                back=headers[warp['dest_map']]['warp_events'][int(warp['dest_warp_id'])]
                self.assertEqual(back['dest_map'],header['id']);self.assertEqual(int(back['dest_warp_id']),i)
        raw,h=result['Room2'];w,height=m.DIMS['Room2'];cells=struct.unpack('<%dH'%(w*height),raw)
        start,end=[v['y']*w+v['x'] for v in h['warp_events']];seen={start};todo=[start]
        while todo:
            i=todo.pop();x,y=i%w,i//w
            for xx,yy in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                if not(0<=xx<w and 0<=yy<height):continue
                j=yy*w+xx;a,b=cells[i],cells[j]
                if j not in seen and not b&0xc00 and (not(a>>12) or not(b>>12) or a>>12==b>>12):seen.add(j);todo.append(j)
        self.assertIn(end,seen)
        # Multiple disconnected source pockets remain explicitly unaccepted.
        self.assertEqual(len(seen),1487)

    def test_invalid_surface_identity_warp_and_capacity_fail_closed(self):
        bad=copy.deepcopy(self.geometry);bad['rooms']['Room1']['surfaces'][0]['tile']=[0,0]
        with self.assertRaisesRegex(ValueError,'exterior boundary'):m.construct(bad)
        bad=copy.deepcopy(self.geometry);bad['rooms']['Room1']['surfaces'][0]['permission']=0x8008
        with self.assertRaisesRegex(ValueError,'invalid cave surface'):m.construct(bad)
        bad=copy.deepcopy(self.geometry);bad['rooms']['Room2']['source_warps'][0]['dest_warp_id']=9
        with self.assertRaisesRegex(ValueError,'warp identities'):m.construct(bad)
        bad=copy.deepcopy(self.geometry);bad['rooms']['Room1']['surfaces'].append(copy.deepcopy(bad['rooms']['Room1']['surfaces'][0]))
        with self.assertRaisesRegex(ValueError,'invalid cave surface'):m.construct(bad)
        bad=copy.deepcopy(self.geometry);p=copy.deepcopy(bad['rooms']['Room1']['surfaces'][0]);p.update(flat=True,height='999');bad['rooms']['Room1']['surfaces'].append(p)
        with self.assertRaisesRegex(ValueError,'capacity'):m.construct(bad)

    def test_native_replay_preserves_geometry_and_safe_behavior(self):
        original,_=m.construct(self.geometry)
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'fresh';receipt=m.build(ROOT/'Pokemon Game/engine',out)
            self.assertEqual(receipt,json.loads((HERE/'receipt.json').read_text()))
            for path,h in receipt['output_sha256'].items():self.assertEqual(m.base.sha((out/path).read_bytes()),h);self.assertEqual((out/path).read_bytes(),(HERE/path).read_bytes())
            for room,(raw,header) in original.items():
                converted=(out/'staged'/room/'map.bin').read_bytes();attrs=json.loads((out/'staged'/room/'attributes.json').read_text());w,_=m.DIMS[room]
                warp_cells={(v['x'],v['y']) for v in header['warp_events']}
                for i,((a,),(b,)) in enumerate(zip(struct.iter_unpack('<H',raw),struct.iter_unpack('<H',converted))):
                    self.assertEqual(a&0xfc00,b&0xfc00)
                    self.assertEqual(attrs[str(b&1023)],0x1061 if (i%w,i//w) in warp_cells else 0x1000)
            self.assertIn('NOT_RUNTIME_ACCEPTANCE',receipt['status'])

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
