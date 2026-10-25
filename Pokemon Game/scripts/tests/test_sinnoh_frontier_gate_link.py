"""Source-stage gateway geometry/trigger/prefix proof, not emulator acceptance."""
import importlib.util,json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/frontier-gate-link'
s=importlib.util.spec_from_file_location('gate_test',HERE/'build.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
ENGINE=ROOT/'Pokemon Game/engine'
class GatewayTests(unittest.TestCase):
    def setUp(self):self.receipt=json.loads((HERE/'receipt.json').read_text())
    def test_exact_four_portal_cells_all_other_source_words_unchanged(self):
        sources={'Campus':m.F/'staged/Campus','Gate':m.C/'staged/Gate','FightArea':m.L/'staged/FightArea'}
        widths={'Campus':96,'Gate':32,'FightArea':70}
        expected={'Campus':{(48,52)},'Gate':{(7,2),(7,20)},'FightArea':{(50,9)}}
        for n,p in sources.items():
            before=(p/'map.bin').read_bytes();after=(HERE/'staged'/n/'map.bin').read_bytes();w=widths[n]
            changed={(i%w,i//w) for i,((a,),(b,)) in enumerate(zip(struct.iter_unpack('<H',before),struct.iter_unpack('<H',after))) if a!=b}
            self.assertEqual(changed,expected[n]);self.assertEqual(len(before),len(after))
            self.assertEqual((p/'border.bin').read_bytes(),(HERE/'staged'/n/'border.bin').read_bytes())
    def test_every_gateway_warp_index_reciprocal_height_and_actual_native_trigger(self):
        headers={};widths={'Campus':96,'Gate':32,'FightArea':70}
        for n in widths:
            h=json.loads((HERE/'staged'/n/'map.json').read_text());headers[h['id']]=(n,h)
        for identity,(n,h) in headers.items():
            raw=(HERE/'staged'/n/'map.bin').read_bytes();attrs=json.loads((HERE/'staged'/n/'attributes.json').read_text())
            for i,e in enumerate(h['warp_events']):
                if e['dest_map'] not in headers:continue
                _,target=headers[e['dest_map']];back=target['warp_events'][int(e['dest_warp_id'])]
                self.assertEqual((back['dest_map'],int(back['dest_warp_id'])),(identity,i))
                v=struct.unpack_from('<H',raw,2*(e['y']*widths[n]+e['x']))[0]
                self.assertFalse(v&0xc00);self.assertEqual(v>>12,e['elevation']);self.assertEqual(attrs[str(v&1023)],0x1061)
        old=json.loads((m.F/'staged/Campus/map.json').read_text())
        self.assertEqual(headers['MAP_SINNOH_FRONTIER_CAMPUS'][1]['warp_events'][:-1],old['warp_events'])
    def test_every_facility_has_nontrapping_static_approach_and_gate_returns(self):
        self.assertEqual(len(self.receipt['facility_paths']),5)
        for path in self.receipt['facility_paths'].values():
            self.assertEqual(path[0],[48,52]);self.assertGreater(len(path),2)
        self.assertEqual(self.receipt['static_paths']['Gate'][0],[7,2])
        self.assertEqual(self.receipt['static_paths']['Gate'][-1],[7,20])
        self.assertEqual(self.receipt['static_paths']['FightArea'],[[50,10],[50,9]])
        raw=(HERE/'staged/Gate/map.bin').read_bytes();attrs=json.loads((HERE/'staged/Gate/attributes.json').read_text())
        bad=bytearray(raw);struct.pack_into('<H',bad,2*(2*32+7),0x3401)
        self.assertFalse(m.a.static_path(bad,32,32,[7,2],[7,20],attrs))
    def test_original_native_family_prefix_and_full_replay(self):
        parents={'Campus':m.F/'campus-family','Gate':m.C/'native-family','FightArea':m.B/'outdoor-family'}
        for n,folder in parents.items():
            for p in ('primary-metatiles.bin','primary-attributes.bin','secondary-metatiles.bin','secondary-attributes.bin'):
                old=(folder/p).read_bytes();self.assertEqual((HERE/'families'/n/p).read_bytes()[:len(old)],old)
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'fresh';receipt=m.build(ENGINE,out);self.assertEqual(receipt,self.receipt)
            for p,h in receipt['output_sha256'].items():self.assertEqual(m.base.sha((out/p).read_bytes()),h);self.assertEqual((out/p).read_bytes(),(HERE/p).read_bytes())
    def test_dirty_source_and_unsafe_output_refused_before_write(self):
        original=Path.read_bytes;target=m.F/'staged/Campus/map.json'
        def dirty(p):
            v=original(p);return v+b' ' if p==target else v
        with tempfile.TemporaryDirectory() as t,patch.object(Path,'read_bytes',dirty):
            out=Path(t)/'never'
            with self.assertRaisesRegex(ValueError,'dirty'):m.build(ENGINE,out)
            self.assertFalse(out.exists())
        with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ENGINE,ENGINE/'bad')
if __name__=='__main__':unittest.main()
