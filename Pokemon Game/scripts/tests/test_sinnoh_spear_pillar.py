"""Actual supported normal-summit footprint and bounded physical6F return."""
import copy,importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/spear-pillar'
s=importlib.util.spec_from_file_location('summit_tests',HERE/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine';UPPER=HERE.parent/'coronet-upper-floors'
class SummitTests(unittest.TestCase):
    def setUp(self):self.r=json.loads((HERE/'receipt.json').read_text());self.geometry=json.loads((HERE/'geometry.json').read_text())
    def test_actual484_supported_cells_only_and_one6F_change(self):
        raw=(HERE/'staged/Summit/map.bin').read_bytes();points={tuple(p['tile']) for p in self.geometry['Summit']['surfaces']}
        self.assertEqual(len(points),484);self.assertEqual(self.r['current_open_cells']['Summit'],484)
        for i,(v,) in enumerate(struct.iter_unpack('<H',raw)):self.assertEqual(not bool(v&0xc00),(i%64,i//64) in points)
        before=(UPPER/'staged/SinnohMtCoronet_6F/map.bin').read_bytes();after=(HERE/'staged/Coronet6F/map.bin').read_bytes()
        diff={(i%14,i//14) for i,((a,),(b,)) in enumerate(zip(struct.iter_unpack('<H',before),struct.iter_unpack('<H',after))) if a!=b}
        self.assertEqual(diff,{(7,5)})
        self.assertEqual((UPPER/'staged/SinnohMtCoronet_6F/border.bin').read_bytes(),(HERE/'staged/Coronet6F/border.bin').read_bytes())
    def test_normal_only_reciprocal_source_indices_trigger_elevation_and_old_stair_prefix(self):
        headers={}
        for n,w in [('Summit',64),('Coronet6F',14)]:
            h=json.loads((HERE/'staged'/n/'map.json').read_text());headers[h['id']]=h
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
            for k in ('object_events','coord_events','bg_events'):self.assertFalse(h[k])
            e=h['warp_events'][0 if n=='Summit' else -1];raw=(HERE/'staged'/n/'map.bin').read_bytes();attrs=json.loads((HERE/'staged'/n/'attributes.json').read_text())
            v=struct.unpack_from('<H',raw,2*(e['y']*w+e['x']))[0];self.assertEqual(v>>12,3);self.assertFalse(v&0xc00);self.assertEqual(attrs[str(v&1023)]&255,0x61)
        summit=headers['MAP_SINNOH_SPEAR_PILLAR'];six=headers['MAP_SINNOH_MT_CORONET_6F']
        self.assertEqual((summit['warp_events'][0]['dest_map'],summit['warp_events'][0]['dest_warp_id']),(six['id'],'1'))
        self.assertEqual((six['warp_events'][1]['dest_map'],six['warp_events'][1]['dest_warp_id']),(summit['id'],'0'))
        old=json.loads((UPPER/'staged/SinnohMtCoronet_6F/map.json').read_text());self.assertEqual(old['warp_events'],six['warp_events'][:-1])
        self.assertNotIn('DISTORTED',json.dumps(headers));self.assertNotIn('DIALGA',json.dumps(headers));self.assertNotIn('PALKIA',json.dumps(headers))
    def test_ground_paths_overlook_and_downstairs_are_actual_and_invalid_surfaces_rejected(self):
        path=self.r['local_paths']['Summit'];self.assertEqual(path[0],[31,53]);self.assertEqual(path[-1],[31,13]);self.assertEqual(len(path),41)
        self.assertEqual(self.r['local_paths']['Coronet6F'][0],[7,5]);self.assertEqual(self.r['local_paths']['Coronet6F'][-1],[10,24])
        bad=copy.deepcopy(self.geometry);bad['Summit']['surfaces'].append(copy.deepcopy(bad['Summit']['surfaces'][0]))
        with self.assertRaisesRegex(ValueError,'invalid|duplicate'):m.construct(bad)
        bad=copy.deepcopy(self.geometry);bad['Summit']['surfaces'][0]['permission']=0xffff
        with self.assertRaisesRegex(ValueError,'invalid'):m.construct(bad)
        spec=importlib.util.spec_from_file_location('frontier_default_unchanged',HERE.parent/'frontier-campus/build_source.py')
        default=importlib.util.module_from_spec(spec);spec.loader.exec_module(default)
        self.assertNotIn(0x6f,default.SOURCE_BEHAVIORS);self.assertIn(0x6f,m.existing.SOURCE_BEHAVIORS)
    def test_full_native_replay_and_source_metadata_pins(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'new';r=m.build(ENGINE,out);self.assertEqual(r,self.r)
            for p,h in r['output_sha256'].items():self.assertEqual(m.existing.base.sha((out/p).read_bytes()),h);self.assertEqual((out/p).read_bytes(),(HERE/p).read_bytes())
        self.assertEqual(self.r['baseline_projection']['Summit']['supported'],484)
    def test_dirty_existing_map_and_engine_output_rejected_before_write(self):
        original=Path.read_bytes;target=UPPER/'staged/SinnohMtCoronet_6F/map.bin'
        def dirty(p):
            v=original(p);return bytes([v[0]^1])+v[1:] if p==target else v
        with tempfile.TemporaryDirectory() as t,patch.object(Path,'read_bytes',dirty):
            out=Path(t)/'never'
            with self.assertRaisesRegex(ValueError,'dirty'):m.build(ENGINE,out)
            self.assertFalse(out.exists())
        with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,ENGINE/'bad')
if __name__=='__main__':unittest.main()
