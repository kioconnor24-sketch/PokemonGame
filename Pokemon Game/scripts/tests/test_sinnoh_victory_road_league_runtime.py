"""Combined DEV source matches both scenes and the actual sixteen portal events."""
import importlib.util
import json
import os
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

if __name__=='__main__':unittest.main()
