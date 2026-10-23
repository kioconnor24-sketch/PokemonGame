"""Current-main reconciliation preserves existing runtime slots and source bytes."""
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

HERE = Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/oreburgh-connected'
spec = importlib.util.spec_from_file_location('oreburgh_current',HERE/'prepare_current.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
ROOT = HERE.parents[4]


class CurrentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = a.current_inputs()
        cls.old = {p:a.frozen.blob(ROOT,a.frozen.BASE,a.ENGINE+p) for p in cls.before}
        cls.frozen, _ = a.frozen.assemble(ROOT)
        cls.files,cls.receipt = a.assemble(ROOT)

    def test_northern_slots_and_all_other_groups_preserved(self):
        before = json.loads(self.before['data/maps/map_groups.json'])
        after = json.loads(self.files['data/maps/map_groups.json'])
        self.assertEqual(len(before['gMapGroup_Sinnoh']),19)
        self.assertEqual(before['gMapGroup_Sinnoh'][13:],['Route204','RavagedPath','FloaromaTown','FloaromaMeadow','Route205_South','Route205_North'])
        for k,v in before.items():
            self.assertEqual(after[k][:len(v)] if k=='gMapGroup_Sinnoh' else after[k],v)
        self.assertEqual(self.receipt['temporary_map_slots'],dict(zip(a.frozen.MAPS,range(19,23))))

    def test_layouts_and_text_prefixes_retain_every_current_byte(self):
        before = json.loads(self.before['data/layouts/layouts.json'])['layouts']
        after = json.loads(self.files['data/layouts/layouts.json'])['layouts']
        self.assertEqual(after[:len(before)],before)
        for p in ('data/event_scripts.s','include/tilesets.h','src/data/tilesets/headers.h','src/data/tilesets/metatiles.h'):
            self.assertTrue(self.files[p].startswith(self.before[p]))
        old = self.before['test/data/averon_map_registry_slots.inc'].decode().splitlines()
        new = self.files['test/data/averon_map_registry_slots.inc'].decode().splitlines()
        self.assertEqual([x for x in old if not x.startswith('REGISTRY_GROUP(76,')],
                         [x for x in new[:len(old)] if not x.startswith('REGISTRY_GROUP(76,')])

    def test_proven_geography_art_events_and_fixture_bytes_reused(self):
        for p,data in self.files.items():
            if p not in self.before:
                self.assertEqual(data,self.frozen[p],p)
        a.frozen.validate_links(self.receipt['source_headers'],json.loads(self.files['data/maps/OreburghGate_1F/map.json']))
        self.assertEqual(self.files['data/layouts/OreburghGate_1F/map.bin'],self.frozen['data/layouts/OreburghGate_1F/map.bin'])

    def test_no_permanent_origins_save_schema_or_northern_map_writes(self):
        self.assertFalse(any(p.endswith('.pal') or p.endswith('.png') or 'region_map_sections' in p or 'pokemon.h' in p or 'global.h' in p for p in self.files))
        for name in self.receipt['existing_map_names_preserved'][13:]:
            self.assertFalse(any('/'+name+'/' in p for p in self.files))
        for name in a.frozen.MAPS:
            self.assertEqual(json.loads(self.files['data/maps/'+name+'/map.json'])['region_map_section'],'MAPSEC_ROUTE_201')
            self.assertEqual(self.receipt['source_headers'][name]['region_map_section'],'MAPSEC_PENDING_OWNER')

    def test_offline_empty_checkout_replay_and_inputs_immutable(self):
        original = copy.deepcopy(self.before)
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(a.frozen,'git',side_effect=AssertionError('history fetch')):
            self.assertEqual(a.assemble(Path(tmp)),(self.files,self.receipt))
        self.assertEqual(self.before,original)

    def mutated(self,path,fn):
        result = dict(self.before)
        data = json.loads(result[path]);fn(data)
        result[path] = a.frozen.encode(data)
        return result

    def test_overwritten_northern_prefix_duplicate_map_and_group_order_rejected(self):
        path='data/maps/map_groups.json'
        for fn in (lambda d:d['gMapGroup_Sinnoh'].__setitem__(0,'Wrong'),
                   lambda d:d['gMapGroup_Sinnoh'].append('OreburghCity'),
                   lambda d:d['gMapGroup_Sinnoh'].append('Route204'),
                   lambda d:d['group_order'].reverse()):
            with self.subTest(fn=fn),self.assertRaises(ValueError):
                a.reconcile(self.frozen,self.mutated(path,fn),self.old)

    def test_duplicate_layout_and_changed_old_layout_rejected(self):
        path='data/layouts/layouts.json'
        for fn in (lambda d:d['layouts'].append(copy.deepcopy(d['layouts'][0])),
                   lambda d:d['layouts'][0].__setitem__('width',999)):
            with self.assertRaises(ValueError):a.reconcile(self.frozen,self.mutated(path,fn),self.old)

    def test_stale_golden_count_slot_or_changed_gate_rejected(self):
        p='test/data/averon_map_registry_slots.inc'
        for old,new in ((b'gMapGroup_Sinnoh, 19,',b'gMapGroup_Sinnoh, 13,'),(b', Route204, 1)',b', Wrong, 1)')):
            bad=dict(self.before);self.assertIn(old,bad[p]);bad[p]=bad[p].replace(old,new)
            with self.assertRaises(ValueError):a.reconcile(self.frozen,bad,self.old)
        for p in ('data/maps/OreburghGate_1F/map.json','data/layouts/OreburghGate_1F/map.bin'):
            bad=dict(self.before);bad[p]+=b'x'
            with self.assertRaisesRegex(ValueError,'Gate changed'):a.reconcile(self.frozen,bad,self.old)

    def test_non_append_only_frozen_overlay_and_duplicate_declarations_rejected(self):
        p='include/tilesets.h';bad=dict(self.frozen);bad[p]=b'wrong'
        with self.assertRaises(ValueError):a.reconcile(bad,self.before,self.old)
        bad=dict(self.before);bad[p]+=b'OreburghCity'
        with self.assertRaises(ValueError):a.reconcile(self.frozen,bad,self.old)

    def test_cache_tamper_or_extra_paths_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            here=Path(tmp);(here/'current-base-input-hashes.json').write_bytes((HERE/'current-base-input-hashes.json').read_bytes())
            for extra in (False,True):
                b=io.BytesIO()
                with zipfile.ZipFile(b,'w') as z:
                    for p,v in self.before.items():z.writestr(p,v+(b'x' if not extra else b''))
                    if extra:z.writestr('extra',b'x')
                (here/'current-base-inputs.zip').write_bytes(b.getvalue())
                with mock.patch.object(a,'HERE',here),self.assertRaises(ValueError):a.current_inputs()

    def test_install_refuses_missing_marker_wrong_branch_head_and_dirty_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp);engine=repo/a.ENGINE;engine.mkdir(parents=True)
            with mock.patch.object(a.frozen,'git',return_value=b'main\n'),self.assertRaises(ValueError):a.install(repo)
            (engine/'.map_qa_throwaway').touch()
            for responses in ([b'main\n'],[b'codex/oreburgh-current-runtime-scratch-test\n',b'wrong\n'],
                              [b'codex/oreburgh-current-runtime-scratch-test\n',(a.EXACT_BASE+'\n').encode(),b' M source.c\n']):
                with mock.patch.object(a.frozen,'git',side_effect=responses),self.assertRaises(ValueError):a.install(repo)
            self.assertEqual(list(engine.iterdir()),[engine/'.map_qa_throwaway'])


if __name__=='__main__':unittest.main()
