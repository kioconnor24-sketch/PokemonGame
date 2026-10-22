"""Central Sinnoh real-source fixtures; geometry only, not art/ROM acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import unittest

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/hearthome-solaceon'
spec=importlib.util.spec_from_file_location('central_stage',HERE/'stage_central.py');stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)


class CentralTest(unittest.TestCase):
    def setUp(self):
        self.receipt=json.loads((HERE/'source-receipt.json').read_text());self.headers=copy.deepcopy(self.receipt['source_geometry_headers'])
        self.layouts={n:dict(width=v[0],height=v[1]) for n,v in stage.MAPS.items()};self.raws={}
        for n in stage.MAPS:
            raw=bytearray((HERE/'staged'/n/'map.bin').read_bytes());w=stage.MAPS[n][0]
            for c in self.receipt['closure_changes'][n]:struct.pack_into('<H',raw,(w*c['y']+c['x'])*2,c['before'])
            self.raws[n]=bytes(raw)

    def build(self):return stage.base.sanitize(self.headers,self.layouts,self.raws)

    def test_all_seven_real_maps_replay_and_keep_every_original_id_and_elevation(self):
        staged,closures,_=self.build();count=0
        for n,(raw,h) in staged.items():
            self.assertEqual(raw,(HERE/'staged'/n/'map.bin').read_bytes());self.assertEqual(h,json.loads((HERE/'staged'/n/'map.json').read_text()))
            self.assertEqual(closures[n],self.receipt['closure_changes'][n]);self.assertEqual(stage.base.sha(self.raws[n]),self.receipt['maps'][n]['source_sha256'])
            for (old,),(new,) in zip(struct.iter_unpack('<H',self.raws[n]),struct.iter_unpack('<H',raw)):
                self.assertEqual(old&0xF3FF,new&0xF3FF);count+=1
        self.assertEqual(count,17582)

    def test_all_reciprocal_offsets_are_source_exact(self):
        staged,_,_=self.build();actual={n:[(c['map'],c['direction'],c['offset']) for c in h['connections']] for n,(_,h) in staged.items()}
        self.assertIn(('MAP_ROUTE208','left',21),actual['HearthomeCity']);self.assertIn(('MAP_HEARTHOME_CITY','right',-21),actual['Route208'])
        self.assertIn(('MAP_ROUTE209','right',-17),actual['HearthomeCity']);self.assertIn(('MAP_HEARTHOME_CITY','left',17),actual['Route209'])
        self.assertIn(('MAP_SOLACEON_TOWN','up',34),actual['Route209']);self.assertIn(('MAP_ROUTE209','down',-34),actual['SolaceonTown'])
        self.assertIn(('MAP_ROUTE210_SOUTH','up',-6),actual['SolaceonTown']);self.assertIn(('MAP_SOLACEON_TOWN','down',6),actual['Route210_South'])

    def test_both_city_gateways_keep_coupled_source_return_indices(self):
        staged,_,tr=self.build()
        self.assertEqual(tr['HearthomeCity'],{0:0,1:1})
        self.assertEqual([w['dest_warp_id'] for w in staged['HearthomeCity'][1]['warp_events']],['1','0'])
        self.assertEqual([w['dest_warp_id'] for w in staged['Route208_Access'][1]['warp_events']],['0','0'])
        self.assertEqual([w['dest_warp_id'] for w in staged['Route209_Access'][1]['warp_events']],['1','0'])
        self.assertEqual(staged['Route209'][1]['warp_events'][0]['dest_warp_id'],'1')

    def test_wrong_offset_removed_return_and_duplicate_source_warp_rejected(self):
        original=copy.deepcopy(self.headers);self.headers['Route208']['connections'][0]['offset']=-20
        with self.assertRaises(ValueError):self.build()
        self.headers=copy.deepcopy(original);self.headers['Route208_Access']['warp_events'][0]['dest_warp_id']='99'
        with self.assertRaises(ValueError):self.build()
        self.headers=copy.deepcopy(original);self.headers['Route208']['warp_events'].append(copy.deepcopy(self.headers['Route208']['warp_events'][0]))
        with self.assertRaises(ValueError):self.build()

    def test_no_foreign_warps_or_external_open_edges_and_no_gameplay(self):
        staged,_,_=self.build();ids={h['id']:n for n,(_,h) in staged.items()}
        for n,(raw,h) in staged.items():
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER');self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])
            for w in h['warp_events']:
                self.assertIn(w['dest_map'],ids);target=staged[ids[w['dest_map']]][1];self.assertLess(int(w['dest_warp_id']),len(target['warp_events']))
            self.assertTrue(all(c['map'] in ids for c in h['connections']))

    def test_no_field_buffer_overflow_or_missing_source_attribute(self):
        for n,(w,h,_) in stage.MAPS.items():
            self.assertLessEqual((w+15)*(h+14),10240)
            folder=HERE/'staged'/n;attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
            self.assertEqual({int(x) for x in attrs},{x[0]&1023 for x in struct.iter_unpack('<H',(folder/'map.bin').read_bytes()+(folder/'border.bin').read_bytes())})

    def test_walkable_connected_boundary_never_faces_solid_or_missing_source_cell(self):
        staged,_,_=self.build();ids={h['id']:n for n,(_,h) in staged.items()}
        for n,(raw,h) in staged.items():
            w,height=stage.MAPS[n][:2];data=stage.base.cells(raw,w,height)
            for c in h['connections']:
                target=ids[c['map']];tw,th=stage.MAPS[target][:2];dest=stage.base.cells(staged[target][0],tw,th)
                points=([(x,0 if c['direction']=='up' else height-1) for x in range(w)] if c['direction'] in ('up','down') else [(0 if c['direction']=='left' else w-1,y) for y in range(height)])
                for x,y in points:
                    if (data[y*w+x]>>10)&3:continue
                    tx,ty=stage.base.destination((x,y),c['direction'],c['offset'],tw,th)
                    self.assertTrue(0<=tx<tw and 0<=ty<th);self.assertEqual((dest[ty*tw+tx]>>10)&3,0)

    def test_invalid_duplicate_id_and_source_dimensions_rejected(self):
        self.headers['Route208']['id']=self.headers['HearthomeCity']['id']
        with self.assertRaises(ValueError):self.build()
        with self.assertRaises(ValueError):stage.base.cells(b'',0,1)

    def test_no_mutation_and_deterministic_recipe(self):
        before=copy.deepcopy((self.headers,self.layouts,self.raws));self.assertEqual(self.build(),self.build());self.assertEqual(before,(self.headers,self.layouts,self.raws))

if __name__=='__main__':unittest.main()
