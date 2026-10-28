"""Immutable coast packet, exact reuse and bounded reciprocal geographic seams."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/sunyshore-coast'
spec=importlib.util.spec_from_file_location('coast_stage',HERE/'stage_cluster.py')
stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)


def sha(raw):return hashlib.sha256(raw).hexdigest()
def words(raw):return [v[0] for v in struct.iter_unpack('<H',raw)]


class CoastSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pins=json.loads((HERE/'source-input-hashes.json').read_text())
        # Frozen branch fixtures are validated against immutable-parent pins;
        # production CLI reads git objects, not these mutable test fixtures.
        cls.files={path:(ROOT/path).read_bytes() for path in cls.pins}
        cls.staged,cls.borders,cls.attrs,cls.receipt=stage.bound(cls.files,cls.pins)

    def test_all_five_maps_and14034_source_cells_match_exact_committed_candidates(self):
        self.assertEqual(5,len(stage.MAPS));self.assertEqual(14034,sum(w*h for w,h in stage.MAPS.values()))
        self.assertEqual(json.loads(stage.encode(self.receipt)),json.loads((HERE/'source-receipt.json').read_text()))
        for name,(raw,h) in self.staged.items():
            folder=HERE/'staged'/name
            self.assertEqual(raw,(folder/'map.bin').read_bytes());self.assertEqual(h,json.loads((folder/'map.json').read_text()))
            self.assertEqual(self.borders[name],(folder/'border.bin').read_bytes())
            self.assertEqual(self.attrs[name],json.loads((folder/'attributes.json').read_text()))
            self.assertTrue((folder/'collision.png').is_file())
        self.assertIn('PokmonLeague',self.staged);self.assertNotIn('PokemonLeague',self.staged)

    def test_only21_route224_edge_cells_close_with_all_other_bits_and_source_attrs_preserved(self):
        self.assertEqual({'SunyshoreCity':0,'Route222':0,'Route223':0,'PokmonLeague':21,'Route222_Access':0},
                         {n:len(c) for n,c in self.receipt['closure_changes'].items()})
        for name,(raw,_) in self.staged.items():
            w,h=stage.MAPS[name];restored=words(raw)
            for c in reversed(self.receipt['closure_changes'][name]):
                index=c['y']*w+c['x'];self.assertEqual(c['after'],restored[index]);self.assertEqual(0,(c['before']^c['after'])&~0xC00)
                restored[index]=c['before']
            original=self.files[stage.SOURCE+'staged/'+name+'/map.bin']
            self.assertEqual(original,struct.pack('<%dH'%len(restored),*restored))
            for value in words(raw+self.borders[name]):self.assertIn(str(value&1023),self.attrs[name]['used_source_attribute_words'])
            header=self.staged[name][1];self.assertEqual('MAPSEC_PENDING_OWNER',header['region_map_section'])
            self.assertTrue(all(not header[k] for k in ('object_events','coord_events','bg_events')))
        self.assertFalse(any(c['map']=='MAP_ROUTE224' for _,h in self.staged.values() for c in h['connections']))

    def test_real_gate_pairs_remain_source_exact_and_all_internal_warps_have_valid_destinations(self):
        ids={h['id']:n for n,(_,h) in self.staged.items()}
        gate=self.staged['Route222_Access'][1]
        self.assertEqual([(1,5),(11,5)],[(e['x'],e['y']) for e in gate['warp_events']])
        for name,(raw,h) in self.staged.items():
            for event in h['warp_events']:
                self.assertIn(event['dest_map'],ids)
                target=self.staged[ids[event['dest_map']]][1]
                self.assertTrue(0<=int(event['dest_warp_id'])<len(target['warp_events']))
        self.assertEqual(['MAP_ROUTE222','MAP_SUNYSHORE_CITY'],[e['dest_map'] for e in gate['warp_events']])

    def test_connections_are_reciprocal_and_no_final_open_boundary_points_at_closed_or_outside_cell(self):
        ids={h['id']:n for n,(_,h) in self.staged.items()};opp={'up':'down','down':'up','left':'right','right':'left'}
        for name,(raw,h) in self.staged.items():
            w,ht=stage.MAPS[name];cells=words(raw)
            for c in h['connections']:
                target=ids[c['map']];tw,th=stage.MAPS[target];other,header=self.staged[target]
                self.assertEqual(1,len([v for v in header['connections'] if v['map']==h['id'] and v['direction']==opp[c['direction']] and v['offset']==-c['offset']]))
                points=([(x,0 if c['direction']=='up' else ht-1) for x in range(w)] if c['direction'] in ('up','down') else [(0 if c['direction']=='left' else w-1,y) for y in range(ht)])
                for x,y in points:
                    if cells[y*w+x]&0xC00:continue
                    tx,ty=stage.base.destination((x,y),c['direction'],c['offset'],tw,th)
                    self.assertTrue(0<=tx<tw and 0<=ty<th)
                    self.assertEqual(0,words(other)[ty*tw+tx]&0xC00)

    def test_all20_source_packets_reject_bit_flips_and_missing_or_extra_sources(self):
        self.assertEqual(20,len(self.files))
        for path in self.files:
            changed=dict(self.files);changed[path]=changed[path]+b'changed'
            with self.assertRaisesRegex(ValueError,'hash changed'):stage.bound(changed,self.pins)
        for missing in (True,False):
            files=dict(self.files)
            if missing:files.pop(next(iter(files)))
            else:files['unknown']=b'x'
            with self.assertRaisesRegex(ValueError,'exact five-map'):stage.bound(files,self.pins)

    def test_gate_art_is_exact_reuse_with_real_bank_capacity_and_unchanged_source(self):
        reuse=json.loads((HERE/'gate-art-reuse.json').read_text());self.assertEqual(stage.GATE_REV,reuse['source_revision'])
        self.assertEqual(6,len(reuse['copied_sha256']))
        for path,expected in reuse['copied_sha256'].items():self.assertEqual(expected,sha((HERE/path).read_bytes()))
        raw=(HERE/'staged/Route222_Access/averon-map.bin').read_bytes();old=self.staged['Route222_Access'][0]
        pa=(HERE/'gate-art/primary-attributes.bin').read_bytes();sa=(HERE/'gate-art/secondary-attributes.bin').read_bytes();attrs=self.attrs['Route222_Access']['used_source_attribute_words']
        self.assertEqual(331,len((HERE/'gate-art/secondary-metatiles.bin').read_bytes())//16)
        for a,b in zip(words(old),words(raw)):
            self.assertEqual(a&0xFC00,b&0xFC00);bank,index=divmod(b&1023,512)
            self.assertEqual(attrs[str(a&1023)],struct.unpack_from('<H',(pa,sa)[bank],index*2)[0])

    def test_production_or_existing_output_refused_before_any_git_read(self):
        with self.assertRaisesRegex(ValueError,'off-engine'):stage.build(ROOT,ROOT/'Pokemon Game/engine/new-map')
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,'off-engine'):stage.build(ROOT,Path(temp))
            self.assertEqual([],list(Path(temp).iterdir()))


if __name__=='__main__':unittest.main()
