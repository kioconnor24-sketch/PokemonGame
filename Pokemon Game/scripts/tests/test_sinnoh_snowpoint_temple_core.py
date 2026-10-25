"""Original six-floor neutral core, source-pinned stairs, no puzzle/production claim."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import sys
from unittest.mock import patch
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/snowpoint-temple-core'
s=importlib.util.spec_from_file_location('temple_core',HERE/'build_core.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class TempleCoreTests(unittest.TestCase):
    def setUp(self):
        self.recipe=json.loads((HERE/'shell-recipe.json').read_text())
        self.reference=json.loads((HERE/'portal-reference.json').read_text())
        self.maps=m.construct(self.recipe,self.reference)

    def test_six_committed_real_maps_repeat(self):
        self.assertEqual(len(self.maps),6)
        for name,(raw,border,header) in self.maps.items():
            folder=HERE/'staged'/name
            self.assertEqual(raw,(folder/'map.bin').read_bytes());self.assertEqual(border,(folder/'border.bin').read_bytes())
            self.assertEqual(header,json.loads((folder/'map.json').read_text()))
            self.assertEqual(len(raw),800)

    def test_all10_source_stairs_exact_and_reciprocal(self):
        byid={v[2]['id']:v[2] for v in self.maps.values()};count=0
        for name,(_,_,header) in self.maps.items():
            plan=self.recipe['maps'][name];ref=self.reference['files'][plan['reference']]['warp_events']
            for i,(p,old) in enumerate(zip(header['warp_events'],plan['interior_warp_indices'])):
                self.assertEqual((p['x'],p['y']),(ref[old]['x'],ref[old]['z']))
                other=byid[p['dest_map']]['warp_events'][int(p['dest_warp_id'])]
                self.assertEqual((other['dest_map'],int(other['dest_warp_id'])),(header['id'],i));count+=1
        self.assertEqual(count,10)

    def test_city_exit_closed_and_no_content_or_identity(self):
        for name,(raw,_,h) in self.maps.items():
            self.assertEqual(h['region_map_section'],'MAPSEC_PENDING_OWNER')
            for key in ('object_events','coord_events','bg_events','connections'):self.assertFalse(h[key])
            for x,y in self.recipe['maps'][name]['sealed_external_ports']:
                self.assertTrue(struct.unpack_from('<H',raw,2*(y*20+x))[0]&0xc00)
        self.assertTrue(all(p['dest_map']!='MAP_SNOWPOINT_CITY' for _,_,h in self.maps.values() for p in h['warp_events']))

    def test_stairs_reachable_on_neutral_floor_without_ice_claim(self):
        for name,(raw,_,h) in self.maps.items():
            cells=struct.unpack('<400H',raw);points=[(p['x'],p['y']) for p in h['warp_events']]
            todo=[points[0]];seen=set(todo)
            while todo:
                x,y=todo.pop()
                for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if 0<=xx<20 and 0<=yy<20 and (xx,yy) not in seen and not cells[yy*20+xx]&0xc00:
                        seen.add((xx,yy));todo.append((xx,yy))
            self.assertTrue(set(points)<=seen)
        self.assertIn('not canonical DS ice geometry',str(self.recipe['limits']))

    def test_bad_bare_prefix_or_outside_stair_refused(self):
        d=copy.deepcopy(self.reference);d['files']['b1f']['warp_events'][1]['dest_header_id']='B2F'
        with self.assertRaisesRegex(ValueError,'prefix'):m.construct(self.recipe,d)
        d=copy.deepcopy(self.reference);d['files']['b2f']['warp_events'][1]['x']=40
        with self.assertRaisesRegex(ValueError,'outside'):m.construct(self.recipe,d)

    def test_missing_return_or_oversized_map_refused(self):
        r=copy.deepcopy(self.recipe);r['maps'][m.NAMES['b1f']]['interior_warp_indices']=[1]
        with self.assertRaisesRegex(ValueError,'counterpart'):m.construct(r,self.reference)
        r=copy.deepcopy(self.recipe);r['maps'][m.NAMES['1f']]['width']=10240
        with self.assertRaisesRegex(ValueError,'buffer'):m.construct(r,self.reference)

    def test_source_reference_and_existing_native_art_pinned(self):
        receipt=json.loads((HERE/'source-receipt.json').read_text())
        self.assertEqual(receipt['reference_revision'],'6dc1499e3127176d4cb34f41c01ee62e1d98808a')
        for name,h in receipt['input_sha256'].items():self.assertEqual(m.a.sha((HERE/name).read_bytes()),h)
        for path,h in receipt['existing_averon_sha256'].items():
            self.assertEqual(m.a.sha(m.a.base.verified_file(ROOT,Path('Pokemon Game/engine')/path,'HEAD')),h)
        self.assertFalse(any(p.suffix in ('.sav','.gba') for p in HERE.rglob('*')))

class TempleRuntimePreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('temple_prepare_test',HERE/'prepare_runtime.py')
        cls.m=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.m)
        cls.files,cls.receipt=cls.m.assemble(ROOT)

    def test_guarded29_file_scene_preserves_original_prefix_and_six_source_packets(self):
        self.assertEqual(len(self.files),29)
        groups=json.loads(self.files['data/maps/map_groups.json'])['gMapGroup_Sinnoh']
        self.assertEqual(groups[:19],self.receipt['existing_map_names_preserved'])
        self.assertEqual(groups[19:],list(self.m.MAPS))
        self.assertEqual(list(self.receipt['temporary_map_slots'].values()),list(range(19,25)))
        for n in self.m.MAPS:
            self.assertEqual(self.files[f'data/layouts/{n}/map.bin'],(HERE/'staged'/n/'map.bin').read_bytes())
            h=json.loads(self.files[f'data/maps/{n}/map.json']);old=json.loads((HERE/'staged'/n/'map.json').read_text())
            old['region_map_section']='MAPSEC_ROUTE_201';self.assertEqual(h,old)
        self.assertFalse(any('tileset' in p or p.endswith(('.png','.pal','.sav','.gba')) or 'region_map_sections' in p for p in self.files))

    def test_source_art_or_baseline_mismatch_and_production_install_refused(self):
        original=self.m.sha
        target=(HERE/'shell-recipe.json').read_bytes()
        with patch.object(self.m,'sha',side_effect=lambda data:'bad' if data==target else original(data)):
            with self.assertRaisesRegex(ValueError,'Temple source'):self.m.assemble(ROOT)
        git=self.m.base.git
        with patch.object(self.m.base,'git',side_effect=lambda repo,*args:b'bad' if args==('rev-parse','HEAD:Pokemon Game/engine') else git(repo,*args)):
            with self.assertRaisesRegex(ValueError,'baseline engine'):self.m.assemble(ROOT)
        with self.assertRaisesRegex(ValueError,'marked Temple'):self.m.install(ROOT)

    def test_baseline_guard_in_real_depth1_checkout_and_changed_engine_refused(self):
        # A tiny independent Git repository models CI with no historical BASE.
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'source';source.mkdir()
            def git(repo,*args):
                return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL).decode().strip()
            git(source,'init','-q')
            engine=source/'Pokemon Game/engine';engine.mkdir(parents=True)
            (engine/'pin.txt').write_text('original engine\n')
            git(source,'add','.')
            git(source,'-c','user.name=fixture','-c','user.email=fixture@example.invalid','commit','-qm','original')
            tree=git(source,'rev-parse','HEAD:Pokemon Game/engine')
            (source/'docs.txt').write_text('docs only\n');git(source,'add','.')
            git(source,'-c','user.name=fixture','-c','user.email=fixture@example.invalid','commit','-qm','docs')
            shallow=Path(t)/'shallow'
            subprocess.run(['git','clone','-q','--depth=1',source.as_uri(),str(shallow)],check=True,stderr=subprocess.DEVNULL)
            self.assertEqual(git(shallow,'rev-parse','--is-shallow-repository'),'true')
            self.assertNotEqual(subprocess.run(['git','-C',str(shallow),'cat-file','-e',self.m.BASE],stderr=subprocess.DEVNULL).returncode,0)
            with patch.object(self.m,'BASE_ENGINE_TREE',tree):
                self.m.verify_baseline_engine(shallow)
                (shallow/'Pokemon Game/engine/pin.txt').write_text('changed engine\n')
                git(shallow,'add','.')
                git(shallow,'-c','user.name=fixture','-c','user.email=fixture@example.invalid','commit','-qm','engine changed')
                with self.assertRaisesRegex(ValueError,'baseline engine'):
                    self.m.verify_baseline_engine(shallow)

    def test_construction_and_final_runner_restore_original_shared_qa(self):
        sys.path.insert(0,str(ROOT/'Pokemon Game/scripts/claude_play'))
        import map_qa as qa
        spec=importlib.util.spec_from_file_location('temple_run_test',HERE/'run_runtime_qa.py')
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        old=runner.a.MAPS;warp=qa.Runner.warp;main=qa.main
        for mode in ('batch','final'):
            commands=[]
            def probe(args):
                self.assertEqual(runner.a.MAPS,runner.MAPS)
                return qa.main(['run','--save','coronet-six'])
            with patch.object(qa,'main',side_effect=lambda args:commands.append(args) or 0),patch.object(runner.a,'run',side_effect=probe):
                self.assertEqual(runner.run(SimpleNamespace(mode=mode)),0)
            self.assertEqual(commands,[['run','--save','temple-core','--blocked','MAP_SINNOH_SNOWPOINT_TEMPLE_1F,8,12,down']]);self.assertEqual(runner.a.MAPS,old)
            self.assertIs(qa.Runner.warp,warp);self.assertIs(qa.main,main)
        with patch.object(runner.a,'run',side_effect=RuntimeError('fixture')):
            with self.assertRaises(RuntimeError):runner.run(SimpleNamespace(mode='batch'))
        self.assertIs(qa.Runner.warp,warp);self.assertIs(qa.main,main);self.assertEqual(runner.a.MAPS,old)

if __name__=='__main__':unittest.main()
