"""Conservative source-surface construction, no Frontier game mechanics."""
import copy,importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/frontier-campus'
s=importlib.util.spec_from_file_location('frontier_test',HERE/'build_source.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class FrontierTests(unittest.TestCase):
    def setUp(self):self.g=json.loads((HERE/'geometry.json').read_text())
    def test_supported_surfaces_only_and_all_doors_boundaries_closed(self):
        result=m.construct(self.g)
        self.assertEqual([v[2]['supported'] for v in result.values()],[172,1263])
        self.assertEqual(self.g['Gate']['rejected_permission_clear'],{'missing_or_ambiguous_center':722})
        self.assertEqual(sum(self.g['Campus']['rejected_permission_clear'].values()),448)
        for n,(raw,header,audit) in result.items():
            w,h=m.DIMS[n];source={tuple(p['tile']):p for p in self.g[n]['surfaces']}
            for i,(v,) in enumerate(struct.iter_unpack('<H',raw)):
                x,y=i%w,i//w;point=source.get((x,y))
                expected=bool(point and point['permission']==0 and x not in (0,w-1) and y not in (0,h-1))
                self.assertEqual(not bool(v&0xc00),expected);self.assertNotEqual(v>>12,15)
            self.assertEqual(header['region_map_section'],'MAPSEC_PENDING_OWNER')
            for key in ('connections','warp_events','object_events','coord_events','bg_events'):self.assertFalse(header[key])
    def test_duplicate_bad_bounds_unknown_behavior_and_height_capacity_refused(self):
        for kind in ('duplicate','bounds','behavior','height'):
            bad=copy.deepcopy(self.g);p=bad['Gate']['surfaces'][0]
            if kind=='duplicate':bad['Gate']['surfaces'].append(copy.deepcopy(p))
            if kind=='bounds':p['tile']=[100,100]
            if kind=='behavior':p['permission']=0xffff
            if kind=='height':
                bad['Gate']['surfaces']=[dict(tile=[i+1,4],permission=0,height=str(i),flat=True) for i in range(13)]
            with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'invalid|capacity'):m.construct(bad)
    def test_actual_native_replay_and_unchanged_collision_elevation(self):
        before=m.construct(self.g)
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'fresh';receipt=m.build(ROOT/'Pokemon Game/engine',out)
            self.assertEqual(receipt,json.loads((HERE/'receipt.json').read_text()))
            for p,h in receipt['output_sha256'].items():self.assertEqual(m.base.sha((out/p).read_bytes()),h);self.assertEqual((out/p).read_bytes(),(HERE/p).read_bytes())
            pa=(out/'native-family/primary-attributes.bin').read_bytes();sa=(out/'native-family/secondary-attributes.bin').read_bytes()
            for n,(raw,_,_) in before.items():
                after=(out/'staged'/n/'map.bin').read_bytes()
                for (a,),(b,) in zip(struct.iter_unpack('<H',raw),struct.iter_unpack('<H',after)):
                    self.assertEqual(a&0xfc00,b&0xfc00)
                    self.assertEqual(m.packer.attribute((pa,sa)[(b&1023)//512],b%512),0x1000)
            self.assertIn('NOT_RUNTIME_ACCEPTANCE',receipt['status'])
    def test_unfinished_civic_candidate_replays_and_preserves_all_source_physics(self):
        spec=importlib.util.spec_from_file_location('civic_test',HERE/'adapt_civic.py')
        civic=importlib.util.module_from_spec(spec);spec.loader.exec_module(civic)
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'new';receipt=civic.build(ROOT/'Pokemon Game/engine',out)
            self.assertEqual(receipt,json.loads((HERE/'civic-candidate/receipt.json').read_text()))
            for path,h in receipt['output_sha256'].items():self.assertEqual(m.base.sha((out/path).read_bytes()),h)
            old=(HERE/'staged/Campus/map.bin').read_bytes();new=(out/'map.bin').read_bytes()
            self.assertEqual(len(old),len(new))
            for (a,),(b,) in zip(struct.iter_unpack('<H',old),struct.iter_unpack('<H',new)):self.assertEqual(a&0xfc00,b&0xfc00)
            self.assertEqual(receipt['source_cells'],9220)
            self.assertEqual(receipt['secondary_records'],20)
        with self.assertRaisesRegex(ValueError,'off-engine'):civic.build(ROOT/'Pokemon Game/engine',ROOT/'Pokemon Game/engine/bad')

    def test_dirty_geometry_and_engine_output_refused_before_write(self):
        original=Path.read_bytes
        def dirty(p):
            raw=original(p);return raw+b' ' if p==HERE/'geometry.json' else raw
        with tempfile.TemporaryDirectory() as t,patch.object(Path,'read_bytes',dirty):
            out=Path(t)/'never'
            with self.assertRaisesRegex(ValueError,'dirty'):m.build(ROOT/'Pokemon Game/engine',out)
            self.assertFalse(out.exists())
        with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ROOT/'Pokemon Game/engine',ROOT/'Pokemon Game/engine/bad')
if __name__=='__main__':unittest.main()
