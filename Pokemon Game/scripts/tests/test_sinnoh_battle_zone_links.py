"""Authored gate apertures: immutable donor baseline and local foot geometry."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/battle-zone-links'
s=importlib.util.spec_from_file_location('battle_links_test',HERE/'build.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class PhysicalLinksTests(unittest.TestCase):
    def setUp(self):self.plan,self.original=m.load_baseline()

    def test_exact30_authored_cells_preserve_every_other_original_cell(self):
        result,audit=m.construct(self.plan,self.original)
        changes={(v['map'],*v['cell']) for v in audit['changed_cells']}
        self.assertEqual(len(changes),30)
        for name,raw in self.original.items():
            w,h=m.m.MAPS[name]
            for i,((a,),(b,)) in enumerate(zip(struct.iter_unpack('<H',raw),struct.iter_unpack('<H',result[name]))):
                if a!=b:self.assertIn((name,i%w,i//w),changes);self.assertEqual(b,0x3001)
                else:self.assertNotIn((name,i%w,i//w),changes)
        self.assertEqual(len(audit['ordinary_foot_approaches']),8)
        self.assertEqual(audit['boundary_components'],[sorted(m.m.MAPS)])
        self.assertEqual(len(audit['seams']),18)
        self.assertEqual(sum(len(v['compatible_lanes']) for v in audit['seams']),128)

    def test_all_other_boundary_cells_stay_closed_or_identical(self):
        result,_=m.construct(self.plan,self.original)
        for name,(w,h) in m.m.MAPS.items():
            allowed=self.plan['authored_apertures'].get(name,{}).get('rectangle',[0,0,0,0]);x,y,bw,bh=allowed
            for xx,yy in {(i,0) for i in range(w)}|{(i,h-1) for i in range(w)}|{(0,i) for i in range(h)}|{(w-1,i) for i in range(h)}:
                if not (x<=xx<x+bw and y<=yy<y+bh):
                    self.assertEqual(m.word(result[name],w,xx,yy),m.word(self.original[name],w,xx,yy))

    def test_blocked_or_wrong_height_approach_is_not_foot_proof(self):
        result,_=m.construct(self.plan,self.original)
        for value in (0x3401,0x4001,0xf001,0x300d):
            raw=bytearray(result['Route225']);struct.pack_into('<H',raw,2*(89*32+22),value)
            self.assertFalse(m.foot_path(raw,32,94,[22,89],[22,93]))
        self.assertFalse(m.foot_path(result['Route225'],32,94,[-1,89],[22,93]))

    def test_missing_gate_or_unexpected_edit_refused(self):
        for name in self.plan['authored_apertures']:
            bad=copy.deepcopy(self.plan);del bad['authored_apertures'][name]
            with self.assertRaisesRegex(ValueError,'no compatible'):m.construct(bad,self.original)
        bad=copy.deepcopy(self.plan);bad['authored_apertures']['Route225']['rectangle']=[22,89,2,5]
        with self.assertRaisesRegex(ValueError,'unexpected passable'):m.construct(bad,self.original)

    def test_nonreciprocal_offsets_fail_even_with_open_geometry(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)
            for name in m.m.MAPS:
                dest=root/'staged'/name;dest.mkdir(parents=True)
                header=json.loads((m.m.SOURCE/'staged'/name/'map.json').read_text())
                if name=='FightArea':
                    for link in header['connections']:
                        if link['map']=='MAP_ROUTE225':link['offset']=1
                (dest/'map.json').write_text(json.dumps(header))
            with patch.object(m.m,'SOURCE',root):
                with self.assertRaisesRegex(ValueError,'nonreciprocal'):m.construct(self.plan,self.original)

    def test_replay_and_no_new_warps_ids_or_content(self):
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/'fresh';receipt=m.build(ROOT/'Pokemon Game/engine',out)
            expected=json.loads((HERE/'receipt.json').read_text())
            self.assertEqual(receipt,expected)
            for p,h in receipt['output_sha256'].items():
                self.assertEqual(m.sha((out/p).read_bytes()),h)
                self.assertEqual((out/p).read_bytes(),(HERE/p).read_bytes())
            for n in self.plan['authored_apertures']:
                header=json.loads((out/'staged'/n/'map.json').read_text())
                self.assertEqual(header['region_map_section'],'MAPSEC_PENDING_OWNER')
                self.assertEqual((out/'staged'/n/'map.json').read_bytes(),(m.m.SOURCE/'staged'/n/'map.json').read_bytes())
                for k in ('warp_events','object_events','coord_events','bg_events'):self.assertFalse(header[k])
            self.assertIn('NOT_RUNTIME_ACCEPTANCE',receipt['status'])

    def test_dirty_baseline_and_engine_output_refused_before_write(self):
        original=Path.read_bytes
        target=m.BASE/'staged/Route225/averon-map.bin'
        def dirty(path):
            raw=original(path)
            return bytes([raw[0]^1])+raw[1:] if path==target else raw
        with tempfile.TemporaryDirectory() as t,patch.object(Path,'read_bytes',dirty):
            out=Path(t)/'never'
            with self.assertRaisesRegex(ValueError,'baseline pin/worktree|dirty donor dependency'):m.build(ROOT/'Pokemon Game/engine',out)
            self.assertFalse(out.exists())
        with self.assertRaisesRegex(ValueError,'off-engine'):m.build(ROOT/'Pokemon Game/engine',ROOT/'Pokemon Game/engine/bad')

if __name__=='__main__':unittest.main()
