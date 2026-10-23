"""Guarded four-map snow DEV recipe: identities/weather/physics and safe refusal."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/snow-corridor'
spec=importlib.util.spec_from_file_location('snow_runtime_test',HERE/'prepare_runtime.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
REPO=HERE.parents[4]

class SnowRuntimeTest(unittest.TestCase):
    def test_four_source_maps_append_after_all19_existing_names_and_keep_weather(self):
        files,r=a.assemble(REPO)
        old=json.loads(a.inputs(REPO)['data/maps/map_groups.json'])['gMapGroup_Sinnoh']
        new=json.loads(files['data/maps/map_groups.json'])['gMapGroup_Sinnoh']
        self.assertEqual(new[:19],old);self.assertEqual(new[19:],list(a.MAPS))
        self.assertEqual(r['temporary_map_slots'],{n:19+i for i,n in enumerate(a.MAPS)})
        for name in a.MAPS:
            h=json.loads(files[f'data/maps/{name}/map.json']);original=json.loads((HERE/'staged'/name/'map.json').read_text())
            original['region_map_section']='MAPSEC_ROUTE_201';self.assertEqual(h,original)
            self.assertEqual(h['weather'],'WEATHER_SNOW');self.assertFalse(h['warp_events'] or h['object_events'] or h['coord_events'] or h['bg_events'])
            self.assertEqual(files[f'data/layouts/{name}/map.bin'],(HERE/'staged'/name/'averon-map.bin').read_bytes())
            self.assertEqual(files[f'data/layouts/{name}/border.bin'],(HERE/'staged'/name/'averon-border.bin').read_bytes())

    def test_native_general_pointer_and_no_global_art_save_identity_writes(self):
        files,_=a.assemble(REPO);before=a.inputs(REPO)
        for forbidden in ('src/pokemon.c','src/save.c','include/global.h','src/data/region_map/region_map_sections.json','include/constants/region_map_sections.h'):
            self.assertNotIn(forbidden,files)
        self.assertFalse(any(p.startswith('data/tilesets/primary/') for p in files))
        layouts=json.loads(files['data/layouts/layouts.json'])['layouts'][-4:]
        self.assertTrue(all(d['primary_tileset']=='gTileset_General' for d in layouts))
        self.assertEqual(files['src/data/tilesets/headers.h'].count(b'const struct Tileset gTileset_SnowDevOutdoorSecondary'),1)
        self.assertEqual(before['data/tilesets/primary/general/metatiles.bin'],(HERE/'outdoor-family/primary-metatiles.bin').read_bytes())

    def test_repeat_recipe_hashes_exactly_describe_each_generated_file(self):
        first,r=a.assemble(REPO);second,s=a.assemble(REPO);self.assertEqual(first,second);self.assertEqual(r,s)
        self.assertEqual(r['files'],{p:a.sha(v) for p,v in sorted(first.items())})
        self.assertEqual(r['status'],'DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE')
        self.assertIn('REGISTRY_GROUP(76, gMapGroup_Sinnoh, 23, 1)',first['test/data/averon_map_registry_slots.inc'].decode())

    def test_changed_general_metadata_cannot_receive_native_pointer(self):
        before=a.inputs(REPO)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);family=root/'outdoor-family';family.mkdir()
            (family/'primary-metatiles.bin').write_bytes(b'wrong')
            with mock.patch.object(a,'inputs',return_value=before),mock.patch.object(a,'HERE',root):
                with self.assertRaisesRegex(ValueError,'General art/metadata differs'):a.assemble(REPO)

    def test_source_checkout_and_unmarked_target_refused_before_any_write(self):
        with self.assertRaisesRegex(ValueError,'explicit disposable snow'):a.install(REPO)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(Exception):a.install(Path(tmp))

if __name__=='__main__':unittest.main()
