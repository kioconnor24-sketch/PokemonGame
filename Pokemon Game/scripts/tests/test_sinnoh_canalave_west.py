"""Pinned west branch geometry; no Averon art, Surf or runtime acceptance."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import unittest

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/canalave-west'
spec=importlib.util.spec_from_file_location('canalave_stage',HERE/'stage_canalave.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class CanalaveTest(unittest.TestCase):
    def setUp(self):
        self.r=json.loads((HERE/'source-receipt.json').read_text())
        self.headers=copy.deepcopy(self.r['source_geometry_headers'])
        self.layouts={n:dict(width=d[0],height=d[1]) for n,d in a.MAPS.items()}
        self.raw={}
        for n,(w,h,_) in a.MAPS.items():
            raw=bytearray((HERE/'staged'/n/'map.bin').read_bytes())
            for c in self.r['closure_changes'][n]:struct.pack_into('<H',raw,2*(c['y']*w+c['x']),c['before'])
            self.raw[n]=bytes(raw)

    def build(self,correct=True):
        return a.base.sanitize(a.corrected_headers(self.headers) if correct else self.headers,self.layouts,self.raw)

    def test_real_original_typo_fails_unmodified_and_only_exact_pair_is_corrected(self):
        with self.assertRaisesRegex(ValueError,'return warp'):self.build(False)
        before=copy.deepcopy(self.headers);fixed=a.corrected_headers(self.headers)
        self.assertEqual(self.headers,before)
        self.assertEqual(self.headers['Route218']['warp_events'][0],a.BAD)
        self.assertEqual(fixed['Route218']['warp_events'][0],a.GOOD)
        before['Route218']['warp_events'][0]=copy.deepcopy(a.GOOD);self.assertEqual(fixed,before)
        self.assertEqual(self.r['neutral_header_corrections'][0]['before'],a.BAD)
        self.assertEqual(self.r['neutral_header_corrections'][0]['after'],a.GOOD)

    def test_changed_pinned_endpoints_cannot_silently_receive_old_correction(self):
        old=copy.deepcopy(self.headers)
        for name,index,key,value in [('Route218',0,'x',58),('Route218',0,'dest_warp_id','0'),
              ('Route218_East',1,'dest_map','MAP_ROUTE211_EAST'),('Route218_East',1,'dest_warp_id','1')]:
            self.headers=copy.deepcopy(old);self.headers[name]['warp_events'][index][key]=value
            with self.subTest(name=name,key=key),self.assertRaisesRegex(ValueError,'no longer applies'):self.build()

    def test_all_four_outputs_and_original_git_blobs_replay_without_checkout(self):
        staged,closures,trans=self.build();self.assertEqual(sum(len(v)//2 for v in self.raw.values()),4714)
        self.assertEqual(trans,{n:{int(k):v for k,v in d.items()} for n,d in self.r['warp_index_translation'].items()})
        for n,(raw,h) in staged.items():
            original=self.raw[n];blob=hashlib.sha1(b'blob '+str(len(original)).encode()+b'\0'+original).hexdigest()
            self.assertEqual(blob,a.MAPS[n][2]);self.assertEqual(a.base.sha(original),self.r['maps'][n]['source_sha256'])
            self.assertEqual(raw,(HERE/'staged'/n/'map.bin').read_bytes())
            self.assertEqual(h,json.loads((HERE/'staged'/n/'map.json').read_text()))
            self.assertEqual(closures[n],self.r['closure_changes'][n])

    def test_source_collision_elevation_and_ids_change_only_journaled_closures(self):
        staged,_,_=self.build();self.assertEqual(sum(len(c) for c in self.r['closure_changes'].values()),133)
        for n,(raw,h) in staged.items():
            w,height,_=a.MAPS[n];closed={c['y']*w+c['x'] for c in self.r['closure_changes'][n]}
            self.assertLessEqual((w+15)*(height+14),10240)
            for i,((old,),(new,)) in enumerate(zip(struct.iter_unpack('<H',self.raw[n]),struct.iter_unpack('<H',raw))):
                self.assertEqual(old&0xF3FF,new&0xF3FF)
                if i in closed:self.assertEqual((new>>10)&3,1)
                else:self.assertEqual(old,new)

    def test_three_real_warp_pairs_survive_exact_destination_and_return_coordinates(self):
        staged,_,trans=self.build();ids={h['id']:n for n,(_,h) in staged.items()};total=0
        for n,(_,h) in staged.items():
            for w in h['warp_events']:
                total+=1;target=ids[w['dest_map']];back=staged[target][1]['warp_events'][int(w['dest_warp_id'])]
                self.assertEqual(back['dest_map'],h['id'])
                self.assertEqual(h['warp_events'][int(back['dest_warp_id'])],w)
        self.assertEqual(total,6)
        self.assertEqual(trans['Route218_East'],{1:0})
        self.assertEqual(staged['Route218'][1]['warp_events'][0]['dest_warp_id'],'0')
        self.assertEqual(staged['Route218_East'][1]['warp_events'][0]['dest_warp_id'],'0')

    def test_canalave_route_border_offsets_and_every_passable_endpoint_are_reciprocal(self):
        staged,_,_=self.build()
        self.assertEqual(staged['Route218'][1]['connections'],[dict(map='MAP_CANALAVE_CITY',offset=-30,direction='left')])
        self.assertEqual(staged['CanalaveCity'][1]['connections'],[dict(map='MAP_ROUTE218',offset=30,direction='right')])
        count=0
        for n,target,x,dx,offset in [('Route218','CanalaveCity',0,37,-30),('CanalaveCity','Route218',37,0,30)]:
            width,height,_=a.MAPS[n];tw,th,_=a.MAPS[target];raw=a.base.cells(staged[n][0],width,height);dest=a.base.cells(staged[target][0],tw,th)
            for y in range(height):
                if (raw[y*width+x]>>10)&3:continue
                dy=y-offset;self.assertTrue(0<=dy<th);self.assertEqual((dest[dy*tw+dx]>>10)&3,0);count+=1
        # Donor connection metadata is real, but neither source edge has
        # an overlapping open endpoint. Travel uses the paired west gateway.
        self.assertEqual(count,0)

    def test_source_attribute_dependencies_cover_every_map_and_border_cell(self):
        for n in a.MAPS:
            p=HERE/'staged'/n;d=json.loads((p/'attributes.json').read_text())
            used={v[0]&1023 for v in struct.iter_unpack('<H',(p/'map.bin').read_bytes()+(p/'border.bin').read_bytes())}
            self.assertEqual(used,{int(k) for k in d['used_source_attribute_words']})
            self.assertEqual(d['averon_art_compatibility'],'UNVERIFIED')
            self.assertTrue(all(type(v) is int and 0<=v<=65535 for v in d['used_source_attribute_words'].values()))

    def test_unbuilt_jubilife_gameplay_and_saved_identifiers_stay_excluded(self):
        staged,_,_=self.build();ids={h['id'] for _,h in staged.values()}
        for n,(raw,h) in staged.items():
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
            self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])
            self.assertTrue(all(w['dest_map'] in ids for w in h['warp_events']))
            self.assertTrue(all(c['map'] in ids for c in h['connections']))
        w=a.MAPS['Route218_East'][0];raw=a.base.cells(staged['Route218_East'][0],w,9)
        self.assertEqual((raw[5*w+11]>>10)&3,1)

    def test_later_warp_and_offset_corruption_fail_closed(self):
        self.headers['Route218_West']['warp_events'][0]['dest_warp_id']='99'
        with self.assertRaisesRegex(ValueError,'return warp'):self.build()
        self.setUp();self.headers['CanalaveCity']['connections'][0]['offset']=29
        with self.assertRaisesRegex(ValueError,'nonreciprocal'):self.build()

    def test_deterministic_replay_never_mutates_inputs(self):
        before=copy.deepcopy((self.headers,self.layouts,self.raw));self.assertEqual(self.build(),self.build())
        self.assertEqual(before,(self.headers,self.layouts,self.raw))

if __name__=='__main__':unittest.main()
