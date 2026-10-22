"""Pinned connected Celestic/northern Coronet geometry, without gameplay/art."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import unittest

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/celestic-north'
spec=importlib.util.spec_from_file_location('celestic_source',HERE/'stage_celestic.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)


class CelesticTest(unittest.TestCase):
    def setUp(self):
        self.receipt=json.loads((HERE/'source-receipt.json').read_text());self.headers=copy.deepcopy(self.receipt['source_geometry_headers'])
        self.layouts={n:dict(width=v[0],height=v[1]) for n,v in s.MAPS.items()};self.raws={}
        for n,(w,h,_) in s.MAPS.items():
            raw=bytearray((HERE/'staged'/n/'map.bin').read_bytes())
            for c in self.receipt['closure_changes'][n]:struct.pack_into('<H',raw,2*(c['y']*w+c['x']),c['before'])
            self.raws[n]=bytes(raw)

    def stage(self):return s.base.sanitize(self.headers,self.layouts,self.raws)

    def test_every_original_blob_cell_and_published_header_replays_exactly(self):
        result,closures,_=self.stage();count=0
        for n,(raw,h) in result.items():
            source=self.raws[n];blob=hashlib.sha1(('blob '+str(len(source))+'\0').encode()+source).hexdigest()
            self.assertEqual(blob,s.MAPS[n][2]);self.assertEqual(s.base.sha(source),self.receipt['maps'][n]['source_sha256'])
            self.assertEqual(raw,(HERE/'staged'/n/'map.bin').read_bytes());self.assertEqual(h,json.loads((HERE/'staged'/n/'map.json').read_text()))
            self.assertEqual(closures[n],self.receipt['closure_changes'][n])
            for (old,),(new,) in zip(struct.iter_unpack('<H',source),struct.iter_unpack('<H',raw)):
                self.assertEqual(old&0xF3FF,new&0xF3FF);count+=1
        self.assertEqual(count,9445)

    def test_cave_compaction_translates_both_route_and_basement_returns(self):
        result,_,tr=self.stage()
        self.assertEqual(tr['MtCoronet_1F_North_Room1'],{1:0,2:1})
        self.assertEqual(tr['MtCoronet_1F_North_Room2'],{0:0})
        self.assertEqual(result['Route211_East'][1]['warp_events'][0]['dest_warp_id'],'0')
        self.assertEqual(result['MtCoronet_B1F'][1]['warp_events'][0]['dest_warp_id'],'1')
        self.assertEqual(sum(len(h['warp_events']) for _,h in result.values()),6)

    def test_reciprocal_source_connections_and_unbuilt_edges_are_preserved_or_closed(self):
        result,closures,_=self.stage()
        self.assertEqual(result['Route210_North'][1]['connections'],[dict(map='MAP_CELESTIC_TOWN',offset=-6,direction='left')])
        self.assertIn(dict(map='MAP_ROUTE210_NORTH',offset=6,direction='right'),result['CelesticTown'][1]['connections'])
        self.assertIn(dict(map='MAP_ROUTE211_EAST',offset=3,direction='left'),result['CelesticTown'][1]['connections'])
        self.assertEqual(result['Route211_East'][1]['connections'],[dict(map='MAP_CELESTIC_TOWN',offset=-3,direction='right')])
        self.assertEqual(sum(len(v) for v in closures.values()),8)
        ids={h['id'] for _,h in result.values()}
        for raw,h in result.values():
            self.assertTrue(all(w['dest_map'] in ids for w in h['warp_events']))
            self.assertTrue(all(c['map'] in ids for c in h['connections']))

    def test_all48_bridge_elevation15_cells_and_hardware_footprints_remain(self):
        result,_,_=self.stage();count=0
        for n,(raw,h) in result.items():
            w,height=s.MAPS[n][:2];self.assertLessEqual((w+15)*(height+14),10240)
            count+=sum(c[0]>>12==15 for c in struct.iter_unpack('<H',raw))
        self.assertEqual(count,48)

    def test_all_map_border_attributes_are_present_without_gameplay_or_saved_ids(self):
        for n in s.MAPS:
            folder=HERE/'staged'/n;h=json.loads((folder/'map.json').read_text());attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
            self.assertEqual(set(map(int,attrs)),{v[0]&1023 for v in struct.iter_unpack('<H',(folder/'map.bin').read_bytes()+(folder/'border.bin').read_bytes())})
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER');self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])

    def test_bad_connection_index_or_removed_return_is_rejected(self):
        saved=copy.deepcopy(self.headers)
        self.headers['CelesticTown']['connections'][0]['offset']=7
        with self.assertRaises(ValueError):self.stage()
        self.headers=copy.deepcopy(saved);self.headers['MtCoronet_B1F']['warp_events'][0]['dest_warp_id']='0'
        with self.assertRaises(ValueError):self.stage() # source0 is the unbuilt west exit
        self.headers=copy.deepcopy(saved);self.headers['Route211_East']['warp_events'][0]['dest_warp_id']='99'
        with self.assertRaises(ValueError):self.stage()

    def test_duplicate_anchor_and_invalid_dimensions_are_rejected(self):
        self.headers['Route211_East']['warp_events']*=2
        with self.assertRaises(ValueError):self.stage()
        with self.assertRaises(ValueError):s.base.cells(b'bad',1,1)

    def test_input_immutable_and_pure_stage_deterministic(self):
        before=copy.deepcopy((self.headers,self.layouts,self.raws));self.assertEqual(self.stage(),self.stage());self.assertEqual(before,(self.headers,self.layouts,self.raws))


if __name__=='__main__':unittest.main()
