"""Original core-floor DEV install cannot affect production or external geography."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/victory-road-shell'
spec=importlib.util.spec_from_file_location('victory_scene_test',HERE/'prepare_runtime.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class VictoryRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.files,cls.receipt=r.assemble(ROOT)

    def test_original19_prefix_and_only_three_temporary_maps_no_origins_or_graphics(self):
        groups=json.loads(self.files['data/maps/map_groups.json']);old=json.loads((ROOT/r.ENGINE/'data/maps/map_groups.json').read_text())
        self.assertEqual(groups['gMapGroup_Sinnoh'][:19],old['gMapGroup_Sinnoh'])
        self.assertEqual(groups['gMapGroup_Sinnoh'][19:],list(r.MAPS));self.assertEqual(len(groups['gMapGroup_Sinnoh']),22)
        self.assertEqual(list(self.receipt['temporary_map_slots'].values()),[19,20,21])
        self.assertEqual(len(self.files),17)
        self.assertFalse(any('tileset' in p or 'pokemon' in p or 'region_map_sections' in p or p.endswith(('.png','.pal','.sav','.gba')) for p in self.files))

    def test_every_packet_and_full_stair_order_exact_only_section_surrogate_changes(self):
        layouts=json.loads(self.files['data/layouts/layouts.json'])['layouts']
        for name in r.MAPS:
            f=HERE/'staged'/name;h=json.loads((f/'map.json').read_text());h['region_map_section']='MAPSEC_ROUTE_201'
            self.assertEqual(h,json.loads(self.files[f'data/maps/{name}/map.json']))
            for p in ('map.bin','border.bin'):self.assertEqual((f/p).read_bytes(),self.files[f'data/layouts/{name}/{p}'])
            layout=next(v for v in layouts if v['name']==name+'_Layout')
            self.assertEqual(layout['primary_tileset'],'gTileset_General');self.assertEqual(layout['secondary_tileset'],'gTileset_Cave')
            self.assertEqual(self.files[f'data/maps/{name}/scripts.inc'],(name+'_MapScripts::\n\t.byte 0\n').encode())
        self.assertEqual(self.receipt['base'],r.BASE)
        for p,raw in self.files.items():self.assertEqual(r.sha(raw),self.receipt['files'][p])

    def test_modified_native_cave_graphics_rejected(self):
        original=r.base.verified_file
        def changed(repo,path,rev):
            data=original(repo,path,rev)
            return data+b'changed' if str(path).endswith('secondary/cave/tiles.png') else data
        with patch.object(r.base,'verified_file',side_effect=changed),self.assertRaisesRegex(ValueError,'native cave asset'):r.assemble(ROOT)

    def test_source_border_or_header_tamper_rejected_before_engine_output(self):
        for filename in ('border.bin','map.json','map.bin'):
            with self.subTest(filename=filename),tempfile.TemporaryDirectory() as temp:
                d=Path(temp)/'candidate';shutil.copytree(HERE,d)
                p=d/'staged/SinnohVictoryRoad_1F'/filename
                if filename=='map.json':
                    h=json.loads(p.read_text());h['warp_events'][0]['x']+=1;p.write_text(json.dumps(h))
                else:
                    raw=bytearray(p.read_bytes());raw[0]^=1;p.write_bytes(raw)
                with patch.object(r,'HERE',d),self.assertRaisesRegex(ValueError,'tested original packet'):r.assemble(ROOT)

    def test_main_checkout_wrong_base_dirty_or_path_escape_refused(self):
        with self.assertRaisesRegex(ValueError,'marked disposable'):r.install(ROOT)
        with tempfile.TemporaryDirectory() as temp:
            repo=Path(temp);e=repo/r.ENGINE;e.mkdir(parents=True);(e/'.map_qa_throwaway').touch()
            def wrong(repo,*args):return b'codex/victory-runtime-scratch-test\n' if args[0]=='branch' else b'0'*40+b'\n'
            with patch.object(r.base,'git',side_effect=wrong),self.assertRaisesRegex(ValueError,'exact production baseline'):r.install(repo)
            def clean(repo,*args):
                if args[0]=='branch':return b'codex/victory-runtime-scratch-test\n'
                if args[0]=='rev-parse':return (r.BASE+'\n').encode()
                return b''
            with patch.object(r.base,'git',side_effect=clean),patch.object(r,'assemble',return_value=({'../escape':b'x'},{})),self.assertRaisesRegex(ValueError,'escapes engine'):r.install(repo)
            def dirty(repo,*args):
                return b' M Pokemon Game/engine/src/save.c\n' if args[0]=='status' else clean(repo,*args)
            with patch.object(r.base,'git',side_effect=dirty),self.assertRaisesRegex(ValueError,'dirty runtime source'):r.install(repo)
            self.assertEqual([p.name for p in e.iterdir()],['.map_qa_throwaway'])

if __name__=='__main__':unittest.main()
