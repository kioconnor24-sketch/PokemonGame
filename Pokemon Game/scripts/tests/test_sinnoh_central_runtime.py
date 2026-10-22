"""Seven-map current-main DEV plan reuses art and preserves production prefixes."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/hearthome-solaceon'
spec=importlib.util.spec_from_file_location('central_dev_runtime',HERE/'prepare_runtime.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ROOT=HERE.parents[4]


class RuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.files,cls.receipt=a.assemble(ROOT);cls.before=a.inputs(ROOT)

    def test_all_existing_map_layout_and_include_prefixes_survive(self):
        before=json.loads(self.before['data/maps/map_groups.json']);after=json.loads(self.files['data/maps/map_groups.json'])
        self.assertEqual(len(before['gMapGroup_Sinnoh']),19)
        for k,v in before.items():self.assertEqual(after[k][:len(v)] if k=='gMapGroup_Sinnoh' else after[k],v)
        self.assertEqual(self.receipt['temporary_map_slots'],dict(zip(a.MAPS,range(19,26))))
        before=json.loads(self.before['data/layouts/layouts.json'])['layouts'];after=json.loads(self.files['data/layouts/layouts.json'])['layouts']
        self.assertEqual(before,after[:len(before)])
        for p in ('data/event_scripts.s','include/tilesets.h','src/data/tilesets/headers.h','src/data/tilesets/metatiles.h'):
            self.assertTrue(self.files[p].startswith(self.before[p]))

    def test_installed_geometry_and_all_warp_arrays_reuse_exact_artifacts(self):
        for name in a.MAPS:
            folder=HERE/'staged'/name
            for p,suffix in [('map.bin','map'),('border.bin','border')]:
                self.assertEqual(self.files[f'data/layouts/{name}/{p}'],(folder/('border.bin' if name.endswith('_Access') and suffix=='border' else f'averon-{suffix}.bin')).read_bytes())
            source=json.loads((folder/'map.json').read_text());target=json.loads(self.files[f'data/maps/{name}/map.json'])
            self.assertEqual(source,self.receipt['source_headers'][name]);source['region_map_section']='MAPSEC_ROUTE_201';self.assertEqual(source,target)
            self.assertEqual(self.files[f'data/maps/{name}/scripts.inc'],(name+'_MapScripts::\n\t.byte 0\n').encode())

    def test_all_five_outdoors_share_one_full_tileset_pair(self):
        layouts=json.loads(self.files['data/layouts/layouts.json'])['layouts'][-7:];d={v['name']:v for v in layouts}
        for name in ('Route208','Route209','SolaceonTown','Route210_South'):
            for key in ('primary_tileset','secondary_tileset'):self.assertEqual(d[name+'_Layout'][key],d['HearthomeCity_Layout'][key])
        self.assertNotEqual(d['Route208_Access_Layout']['primary_tileset'],d['HearthomeCity_Layout']['primary_tileset'])

    def test_existing_building_asset_alias_and_animation_callback_are_reused(self):
        bindings=a.asset_bindings(self.before['src/data/tilesets/headers.h'].decode(),'Building')
        self.assertEqual(bindings,dict(tiles='gTilesetTiles_InsideBuilding',palettes='gTilesetPalettes_InsideBuilding',callback='InitTilesetAnim_Building'))
        header=self.files['src/data/tilesets/headers.h'].decode().split('const struct Tileset gTileset_CentralDevGatePrimary')[1]
        for value in bindings.values():self.assertIn(value,header)
        with self.assertRaises(ValueError):a.asset_bindings('', 'Missing')

    def test_no_save_id_general_northern_or_existing_gate_writes(self):
        self.assertEqual(len(self.files),44)
        for p in self.files:
            self.assertFalse('region_map_sections' in p or 'mapsec-pins' in p or 'pokemon.h' in p or 'global.h' in p or '/general/' in p)
            self.assertFalse(any('/'+n+'/' in p for n in self.receipt['existing_map_names_preserved']))
        self.assertTrue(all(v['region_map_section']=='MAPSEC_PENDING_OWNER' for v in self.receipt['source_headers'].values()))

    def test_plan_reproduces_without_writing_any_input(self):
        hashes={p:a.sha(d) for p,d in self.before.items()};self.assertEqual(a.assemble(ROOT),(self.files,self.receipt));self.assertEqual({p:a.sha(d) for p,d in a.inputs(ROOT).items()},hashes)

    def test_existing_qa_world_reads_every_new_tileset_and_map(self):
        # Exercise the real parser against a read-only virtual overlay. This
        # catches declaration formatting it cannot parse without rewriting it.
        path=HERE.parents[3]/'scripts/claude_play/mapdata.py'
        spec=importlib.util.spec_from_file_location('eterna_qa_mapdata',path)
        mapdata=importlib.util.module_from_spec(spec);spec.loader.exec_module(mapdata)
        engine=ROOT/a.ENGINE;read_text=Path.read_text;read_bytes=Path.read_bytes
        def lookup(path):
            try:return self.files.get(str(path.relative_to(engine)))
            except ValueError:return None
        def text(path,*args,**kwargs):
            value=lookup(path);return value.decode() if value is not None else read_text(path,*args,**kwargs)
        def binary(path):
            value=lookup(path);return value if value is not None else read_bytes(path)
        with mock.patch.object(Path,'read_text',new=text),mock.patch.object(Path,'read_bytes',new=binary):
            world=mapdata.World(engine)
            for name,(w,h) in a.MAPS.items():
                info=world.map(self.receipt['source_headers'][name]['id'])
                self.assertEqual((info.width,info.height),(w,h))
                self.assertTrue(info._primary and info._secondary)

    def test_foreign_warp_wrong_return_and_connection_offset_fail_closed(self):
        original=Path.read_text;target=HERE/'staged/Route208_Access/map.json'
        for mode in ('foreign','index','connection'):
            def read(path,*args,**kwargs):
                data=original(path,*args,**kwargs)
                if path==target and mode!='connection':
                    h=json.loads(data);h['warp_events'][0]['dest_map' if mode=='foreign' else 'dest_warp_id']='MAP_MISSING' if mode=='foreign' else '99';return json.dumps(h)
                if mode=='connection' and path==HERE/'staged/HearthomeCity/map.json':
                    h=json.loads(data);h['connections'][0]['offset']=1;return json.dumps(h)
                return data
            with self.subTest(mode=mode),mock.patch.object(Path,'read_text',new=read),self.assertRaises(ValueError):a.assemble(ROOT)

    def test_misaligned_bank_and_dirty_baseline_rejected(self):
        original=Path.read_bytes
        def read(path):
            data=original(path)
            return data[:-1] if path==HERE/'outdoor-family/secondary-metatiles.bin' else data
        with mock.patch.object(Path,'read_bytes',new=read),self.assertRaises(ValueError):a.assemble(ROOT)
        with mock.patch.object(a.base,'verified_file',return_value=b'changed'),self.assertRaises(ValueError):a.inputs(ROOT)

    def test_install_requires_marker_current_branch_head_and_clean_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp);engine=repo/a.ENGINE;engine.mkdir(parents=True)
            with mock.patch.object(a.base,'git',return_value=b'main\n'),self.assertRaises(ValueError):a.install(repo)
            (engine/'.map_qa_throwaway').touch()
            for responses in ([b'main\n'],[b'codex/central-runtime-scratch-test\n',b'wrong\n'],
                              [b'codex/central-runtime-scratch-test\n',(a.BASE+'\n').encode(),b' M source.c\n']):
                with mock.patch.object(a.base,'git',side_effect=responses),self.assertRaises(ValueError):a.install(repo)
            self.assertEqual(list(engine.iterdir()),[engine/'.map_qa_throwaway'])


if __name__=='__main__':unittest.main()
