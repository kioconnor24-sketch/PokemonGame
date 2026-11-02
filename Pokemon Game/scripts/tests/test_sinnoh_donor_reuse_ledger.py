"""Reproducible inventory, coverage and fail-closed source-evidence tests."""
import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
SCRIPTS=ROOT/'Pokemon Game/scripts'
DEV=ROOT/'Pokemon Game/Averon_Codex_Handoff/development'
spec=importlib.util.spec_from_file_location('reuse_ledger',SCRIPTS/'build_sinnoh_donor_reuse_ledger.py')
ledger=importlib.util.module_from_spec(spec);spec.loader.exec_module(ledger)


class ReuseLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((DEV/'SINNOH_DONOR_REUSE_INPUTS.json').read_text())

    def test_committed_ledger_reproduces_without_git_history_or_network(self):
        self.assertEqual(ledger.render(self.data),(DEV/'SINNOH_DONOR_REUSE_LEDGER.csv').read_text())

    def test_159_sources_once_and_all_87_sites_covered(self):
        rows=ledger.rows(self.data)
        sources=[r for r in rows if r['row_kind']=='SOURCE_MAP']
        self.assertEqual(159,len(sources))
        self.assertEqual(159,len({r['donor_map_name'] for r in sources}))
        self.assertEqual(87,len(set('|'.join(r['covered_sites'] for r in rows).split('|'))-{''}))
        self.assertEqual(len(rows),len({r['site_or_child_key'] for r in rows}))

    def test_missing_source_targets_are_not_claimed_constructed(self):
        targets=[r for r in ledger.rows(self.data) if r['row_kind']=='BUILD_TARGET']
        self.assertTrue(any(r['covered_sites']=='SN-L29' for r in targets))
        self.assertTrue(any(r['site_or_child_key']=='target:SN-T12:uncovered-interiors' for r in targets))
        self.assertTrue(all(r['actual_runtime_QA_status']=='NOT_TESTED' for r in targets))

    def test_real_source_typos_are_preserved_and_site_aliases_are_explicit(self):
        rows={r['donor_map_name']:r for r in ledger.rows(self.data)}
        self.assertEqual('SN-T15',rows['PokmonLeague']['covered_sites'])
        self.assertEqual('SN-T05',rows['FloaromaTwon_PokemonCenter_2F']['covered_sites'])
        self.assertEqual('SN-L13',rows['ValleyWindoworks_Indoor']['covered_sites'])
        self.assertIn('PokmonLeague',self.data['donor']['registered'])
        self.assertNotIn('PokemonLeague',self.data['donor']['registered'])

    def test_no_story_or_trainer_events_published_in_source_snapshot(self):
        for f in self.data['donor']['maps']:
            for field in ('object_events','coord_events','bg_events','scripts'):
                self.assertNotIn(field,f['header'])

    def test_duplicate_source_or_target_missing_site_and_wrong_revision_refused(self):
        for mutation in ('duplicate','missing','revision','bad_hash','duplicate_site'):
            with self.subTest(mutation=mutation):
                data=copy.deepcopy(self.data)
                if mutation=='duplicate':data['donor']['registered'][-1]=data['donor']['registered'][0]
                if mutation=='missing':data['donor']['maps'].pop()
                if mutation=='revision':data['donor']['revision']='0'*40
                if mutation=='bad_hash':data['donor']['maps'][0]['map_sha256']='bad'
                if mutation=='duplicate_site':data['sites'][-1]=data['sites'][0]
                with self.assertRaises(ValueError):ledger.rows(data)

    def test_unknown_source_name_is_not_silently_assigned(self):
        with self.assertRaisesRegex(ValueError,'unmapped source'):
            ledger.sites_for('UnknownMap',self.data['sites'])

    def test_stage_does_not_imply_production_or_runtime_acceptance(self):
        rows={r['donor_map_name']:r for r in ledger.rows(self.data)}
        self.assertEqual('REGISTERED_ON_MAIN',rows['SandgemTown']['production_registry_status'])
        self.assertEqual('NOT_REGISTERED_ON_MAIN',rows['CanalaveCity']['production_registry_status'])
        self.assertIn('UNKNOWN',rows['CanalaveCity']['actual_runtime_QA_status'])
        self.assertIn('unresolved',rows['Route216']['actual_runtime_QA_status'])
        self.assertEqual([],next(f for f in self.data['donor']['maps'] if f['name']=='LakeAcuity')['header']['warp_events'])

    def test_declared_fuego_layout_has_no_blob_and_is_not_marked_usable(self):
        l=next(l for l in self.data['donor']['unregistered_layouts'] if l['id']=='LAYOUT_FUEGO_IRONWORKS')
        self.assertIsNone(l['blockdata_git_blob'])
        row=next(r for r in ledger.rows(self.data) if r['site_or_child_key']=='target:SN-L16:geography')
        self.assertIn('"blob":null',row['known_repair'])
        self.assertEqual('NOT_TESTED',row['actual_runtime_QA_status'])

    def test_missing_upper_floors_and_roadmap_underground_are_explicit_targets(self):
        keys={r['site_or_child_key'] for r in ledger.rows(self.data)}
        self.assertIn('target:SN-L07:remaining-upper-coronet',keys)
        self.assertIn('target:SN-L09:basement',keys)
        self.assertIn('target:ROADMAP-W8:underground',keys)

    def test_reproduced_source_repairs_are_visible_in_flat_ledger_rows(self):
        rows={r['donor_map_name']:r for r in ledger.rows(self.data)}
        self.assertIn('HASH_GUARDED_BORDER_REPAIR',rows['Route205_House']['known_repair'])
        self.assertIn('468',rows['Route205_House']['known_repair'])
        self.assertIn('PINNED_HEADER_REPAIR',rows['Route221']['known_repair'])

    def test_stale_receipt_hash_is_rejected(self):
        facts={'registered':['Route202'],'maps':[dict(name='Route202',header={'id':'MAP_ROUTE202'},
            map_sha256='a'*64,layout={'blockdata_filepath':'data/layouts/Route202/map.bin'})]}
        doc={'maps':{'Route202':{}},'donor_sha256':{'data/layouts/Route202/map.bin':'b'*64}}
        path=ledger.DESIGN+'fake/source-receipt.json'
        def fake_git(repo,*args):
            return (('1'*40+'\n') if args[0]=='rev-parse' else path+'\n').encode()
        with patch.object(ledger,'git',side_effect=fake_git),patch.object(ledger,'read',return_value=json.dumps(doc).encode()):
            with self.assertRaisesRegex(ValueError,'stale receipt source hash'):
                ledger.evidence_snapshot('.',{'main':'HEAD'},facts)


if __name__=='__main__':unittest.main()
