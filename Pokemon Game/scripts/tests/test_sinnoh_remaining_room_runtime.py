"""Four-floor disposable integration, immutable source and installation guards."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/remaining-donor'
spec=importlib.util.spec_from_file_location('room_runtime',HERE/'prepare_room_runtime.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)


class RoomRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.files,cls.receipt=runtime.assemble(ROOT)

    def test_original_nineteen_slots_preserved_and_four_appended_without_saved_ids(self):
        original=json.loads((ROOT/runtime.ENGINE/'data/maps/map_groups.json').read_text())
        groups=json.loads(self.files['data/maps/map_groups.json'])
        self.assertEqual(original['gMapGroup_Sinnoh'],groups['gMapGroup_Sinnoh'][:19])
        self.assertEqual(23,len(groups['gMapGroup_Sinnoh']))
        self.assertEqual(list(runtime.MAPS),groups['gMapGroup_Sinnoh'][19:])
        self.assertEqual([19,20,21,22],list(self.receipt['temporary_map_slots'].values()))
        self.assertFalse(any('region_map_sections' in path or 'pokemon' in path for path in self.files))

    def test_no_primary_copy_no_global_graphics_and_exact_original_room_inputs(self):
        self.assertEqual(26,len(self.files))
        self.assertEqual(2,len([p for p in self.files if p.startswith('data/tilesets/')]))
        self.assertFalse(any(p.endswith(('.png','.pal','.sav','.gba')) for p in self.files))
        layouts=json.loads(self.files['data/layouts/layouts.json'])['layouts']
        for name in runtime.MAPS:
            layout=next(l for l in layouts if l['name']==name+'_Layout')
            self.assertEqual('gTileset_Building',layout['primary_tileset'])
            self.assertEqual('gTileset_RoomsDevSecondary',layout['secondary_tileset'])
            self.assertEqual((HERE/'staged'/name/'averon-map.bin').read_bytes(),self.files['data/layouts/'+name+'/map.bin'])
            source=json.loads((HERE/'staged'/name/'map.json').read_text())
            installed=json.loads(self.files['data/maps/'+name+'/map.json'])
            source['region_map_section']='MAPSEC_ROUTE_201'
            self.assertEqual(source,installed)

    def test_recipe_matches_every_payload_and_old_donor_doors_stay_closed(self):
        self.assertEqual(runtime.BASE,self.receipt['base'])
        for path,raw in self.files.items():self.assertEqual(hashlib.sha256(raw).hexdigest(),self.receipt['files'][path])
        for name in runtime.MAPS:
            header=json.loads(self.files['data/maps/'+name+'/map.json'])
            self.assertEqual(1,len(header['warp_events']))
            self.assertEqual([],header['connections'])
            self.assertTrue(all(not header[k] for k in ('object_events','coord_events','bg_events')))

    def test_production_checkout_refused_and_exact_dirty_inputs_rejected(self):
        with self.assertRaisesRegex(ValueError,'disposable rooms branch'):runtime.install(ROOT)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(Exception):runtime.inputs(Path(temp))
            self.assertEqual([],list(Path(temp).iterdir()))

    def test_wrong_base_and_escape_refused_before_any_output(self):
        with tempfile.TemporaryDirectory() as temp:
            repo=Path(temp);engine=repo/runtime.ENGINE;engine.mkdir(parents=True);(engine/'.map_qa_throwaway').touch()
            def git_wrong(repo,*args):
                if args[0]=='branch':return b'codex/rooms-runtime-scratch-fixture\n'
                return b'0'*40+b'\n'
            with patch.object(runtime.base,'git',side_effect=git_wrong):
                with self.assertRaisesRegex(ValueError,'exact production baseline'):runtime.install(repo)
            def git_clean(repo,*args):
                if args[0]=='branch':return b'codex/rooms-runtime-scratch-fixture\n'
                if args[0]=='rev-parse':return (runtime.BASE+'\n').encode()
                return b''
            with patch.object(runtime.base,'git',side_effect=git_clean),patch.object(runtime,'assemble',return_value=({'../escape':b'x'},{})):
                with self.assertRaisesRegex(ValueError,'escapes engine'):runtime.install(repo)
            self.assertEqual(['.map_qa_throwaway'],[p.name for p in engine.iterdir()])


if __name__=='__main__':unittest.main()
