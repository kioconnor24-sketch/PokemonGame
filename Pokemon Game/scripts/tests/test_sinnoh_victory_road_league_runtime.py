"""Combined DEV source matches both scenes and the actual sixteen portal events."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(os.environ.get('AVERON_TEST_SOURCE_ROOT',Path(__file__).resolve().parents[3]))
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/victory-road-shell'
TOOL=Path(os.environ.get('AVERON_COMBINED_FIXTURE',HERE))
spec=importlib.util.spec_from_file_location('combined_scene_test',TOOL/'prepare_league_runtime.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class CombinedSceneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.files,cls.receipt=r.assemble(ROOT)

    def test_actual45_file_payload_appends_eight_after_original19_without_origins(self):
        old=json.loads((ROOT/r.ENGINE/'data/maps/map_groups.json').read_text());g=json.loads(self.files['data/maps/map_groups.json'])
        self.assertEqual(g['gMapGroup_Sinnoh'][:19],old['gMapGroup_Sinnoh']);self.assertEqual(len(g['gMapGroup_Sinnoh']),27)
        self.assertEqual(list(self.receipt['temporary_map_slots'].values()),list(range(19,27)))
        self.assertEqual(len(self.files),45)
        self.assertFalse(any('pokemon' in p or 'region_map_sections' in p or p.endswith(('.png','.pal','.sav','.gba')) for p in self.files))
        self.assertEqual(len([p for p in self.files if p.startswith('data/tilesets/')]),4)
        for p,v in self.files.items():self.assertEqual(r.sha(v),self.receipt['files'][p])

    def test_source_coast_terrain_unchanged_and_connected_doors_exact(self):
        coast=r.load(ROOT,'combined_before_probe',r.PREFIX+'sunyshore-coast/prepare_runtime.py');before,_=coast.assemble(ROOT)
        for n in coast.MAPS:
            for f in ('map.bin','border.bin'):self.assertEqual(before['data/layouts/'+n+'/'+f],self.files['data/layouts/'+n+'/'+f])
        for n in ('PokmonLeague','SinnohVictoryRoad_1F','SinnohVictoryRoad_2F','SinnohVictoryRoad_B1F'):
            for f in ('map.bin','border.bin'):self.assertEqual((HERE/'connected'/n/f).read_bytes(),self.files['data/layouts/'+n+'/'+f])
            h=json.loads((HERE/'connected'/n/'map.json').read_text());h['region_map_section']='MAPSEC_ROUTE_201'
            self.assertEqual(h,json.loads(self.files['data/maps/'+n+'/map.json']))

    def test_native_expectations_follow_actual_slots_and_events_not_old_scene_counts(self):
        groups=json.loads(self.files['data/maps/map_groups.json'])['gMapGroup_Sinnoh'];headers={n:json.loads(self.files['data/maps/'+n+'/map.json']) for n in groups[19:]}
        self.assertEqual(groups.index('SinnohVictoryRoad_1F'),24);self.assertEqual(groups.index('PokmonLeague'),22)
        self.assertEqual([len(headers[n]['warp_events']) for n in groups[24:]],[8,3,3])
        self.assertEqual(len(headers['PokmonLeague']['warp_events']),2)
        native=self.files['test/averon_victory_runtime.c'].decode();self.assertIn('counts[]={8,3,3}',native);self.assertIn('24+i',native)
        self.assertIn('EXPECT_EQ(total,14)',native);self.assertIn('MAP_NUM(MAP_POKMON_LEAGUE)',native)
        self.assertIn('warps[]={1,1,0,2,2}',self.files['test/averon_sunyshore_runtime.c'].decode())
        byid={h['id']:h for h in headers.values()}
        for n in ('PokmonLeague',*groups[24:]):
            for i,p in enumerate(headers[n]['warp_events']):
                back=byid[p['dest_map']]['warp_events'][int(p['dest_warp_id'])]
                self.assertEqual((back['dest_map'],int(back['dest_warp_id'])),(headers[n]['id'],i))
        # Original source fixtures and goldens remain unchanged; only new DEV
        # payload test expectations are derived for the eight-map arrangement.
        self.assertIn('EXPECT_EQ(total,12)',(HERE/'native-runtime.c').read_text())
        self.assertFalse(any(p.startswith('test/data/') and p!='test/data/averon_map_registry_slots.inc' for p in self.files))

    def test_prior_event_prefix_layouts_and_no_duplicate_names_or_symbols(self):
        layouts=json.loads(self.files['data/layouts/layouts.json'])['layouts'];ids=[v['id'] for v in layouts]
        self.assertEqual(len(ids),len(set(ids)))
        events=self.files['data/event_scripts.s'].decode()
        for n in self.receipt['temporary_map_slots']:self.assertEqual(events.count('data/maps/'+n+'/scripts.inc'),1)
        original=(ROOT/r.ENGINE/'data/event_scripts.s').read_text();self.assertTrue(events.startswith(original))

    def test_connected_packet_tamper_and_changed_native_template_refused(self):
        original=Path.read_bytes
        def changed(p):
            data=original(p)
            return data+b'changed' if str(p).endswith('/connected/SinnohVictoryRoad_1F/map.bin') else data
        with patch.object(Path,'read_bytes',changed),self.assertRaisesRegex(ValueError,'packet hash'):r.assemble(ROOT)
        with self.assertRaisesRegex(ValueError,'fixture contract'):r.replace_once(b'unexpected','missing','new')

    def test_main_checkout_and_wrong_base_refused_before_output(self):
        with self.assertRaisesRegex(ValueError,'marked disposable'):r.install(ROOT)
        base=r.load(ROOT,'combined_guard_probe',r.PREFIX+'sunyshore-coast/prepare_runtime.py').base
        with tempfile.TemporaryDirectory() as t:
            repo=Path(t);e=repo/r.ENGINE;e.mkdir(parents=True);(e/'.map_qa_throwaway').touch()
            def wrong(repo,*args):return b'codex/victory-league-runtime-scratch-test\n' if args[0]=='branch' else b'0'*40+b'\n'
            # Reuse the actual source guard with a fixture-only repository.
            with patch.object(r,'load',return_value=type('Guard',(),{'base':base})()),patch.object(base,'git',side_effect=wrong),self.assertRaisesRegex(ValueError,'exact production baseline'):r.install(repo)
            self.assertEqual([p.name for p in e.iterdir()],['.map_qa_throwaway'])

    def test_separate_baseline_only_target_does_not_need_unmerged_source_tools(self):
        # The real target is a clean main checkout, which cannot contain the
        # unmerged scene tools. Keep source and destination roles independent.
        pins=json.loads((ROOT/r.PREFIX/'sunyshore-coast/runtime-base-input-hashes.json').read_text())
        assets=json.loads((HERE/'source-receipt.json').read_text())['existing_averon_sha256']
        paths=sorted(set(pins)|set(assets))
        with tempfile.TemporaryDirectory() as t:
            target=Path(t)
            subprocess.run(['git','init','-q',str(target)],check=True)
            for name in paths:
                p=target/r.ENGINE/name;p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(subprocess.check_output(['git','-C',str(ROOT),'show','HEAD:'+r.ENGINE+name]))
            subprocess.run(['git','-C',str(target),'add','--',*[r.ENGINE+p for p in paths]],check=True)
            subprocess.run(['git','-C',str(target),'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-q','-m','Baseline-only test fixture'],check=True)
            self.assertFalse((target/r.PREFIX).exists())
            actual,receipt=r.assemble(target)
            self.assertEqual(actual,self.files)
            self.assertEqual(receipt['files'],self.receipt['files'])

    def test_qa_scope_includes_both_league_doors_only_when_explicitly_requested(self):
        script=r'''
import importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
p=Path(sys.argv[1]);sp=importlib.util.spec_from_file_location('four_map_qa_probe',p)
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);old=m.shared.MAPS
def fake(args):
 import driver,map_qa as q
 w=q._wrapper(args.engine)
 assert w.driver is driver
 assert m.shared.MAPS==(('MAP_POKMON_LEAGUE',*m.MAPS) if args.with_league else m.MAPS)
 return 0
m.shared.run=fake
for value in (False,True):
 assert m.run(SimpleNamespace(engine=Path(sys.argv[2]),with_league=value))==0
 assert m.shared.MAPS==old
'''
        result=subprocess.run([sys.executable,'-c',script,str(HERE/'run_runtime_qa.py'),str(ROOT/r.ENGINE)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
