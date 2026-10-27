"""Five-map current-main DEV plan reuses art and preserves production prefixes."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/eterna-cycle'
spec=importlib.util.spec_from_file_location('eterna_dev_runtime',HERE/'prepare_runtime.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ROOT=HERE.parents[4]


class RuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.files,cls.receipt=a.assemble(ROOT);cls.before=a.inputs(ROOT)

    def test_all_existing_map_layout_and_include_prefixes_survive(self):
        before=json.loads(self.before['data/maps/map_groups.json']);after=json.loads(self.files['data/maps/map_groups.json'])
        self.assertEqual(len(before['gMapGroup_Sinnoh']),30)
        for k,v in before.items():self.assertEqual(after[k][:len(v)] if k=='gMapGroup_Sinnoh' else after[k],v)
        self.assertEqual(self.receipt['temporary_map_slots'],dict(zip(a.MAPS,range(30,35))))
        before=json.loads(self.before['data/layouts/layouts.json'])['layouts'];after=json.loads(self.files['data/layouts/layouts.json'])['layouts']
        self.assertEqual(before,after[:len(before)])
        for p in ('data/event_scripts.s','include/tilesets.h','src/data/tilesets/headers.h','src/data/tilesets/metatiles.h'):
            self.assertTrue(self.files[p].startswith(self.before[p]))

    def test_installed_geometry_and_all_warp_arrays_reuse_exact_artifacts(self):
        for name in a.MAPS:
            folder=HERE/'staged'/name
            for p,suffix in [('map.bin','map'),('border.bin','border')]:
                self.assertEqual(self.files[f'data/layouts/{name}/{p}'],(folder/f'averon-{suffix}.bin').read_bytes())
            source=json.loads((folder/'map.json').read_text());target=json.loads(self.files[f'data/maps/{name}/map.json'])
            self.assertEqual(source,self.receipt['source_headers'][name]);source['region_map_section']='MAPSEC_ROUTE_201';self.assertEqual(source,target)
            self.assertEqual(self.files[f'data/maps/{name}/scripts.inc'],(name+'_MapScripts::\n\t.byte 0\n').encode())

    def test_city_and_both_roads_share_one_full_tileset_pair(self):
        layouts=json.loads(self.files['data/layouts/layouts.json'])['layouts'][-5:];d={v['name']:v for v in layouts}
        for name in ('Route206','Route211_West'):
            for key in ('primary_tileset','secondary_tileset'):self.assertEqual(d[name+'_Layout'][key],d['EternaCity_Layout'][key])
        self.assertNotEqual(d['Route206_North_Layout']['primary_tileset'],d['EternaCity_Layout']['primary_tileset'])

    def test_existing_building_asset_alias_and_animation_callback_are_reused(self):
        bindings=a.asset_bindings(self.before['src/data/tilesets/headers.h'].decode(),'Building')
        self.assertEqual(bindings,dict(tiles='gTilesetTiles_InsideBuilding',palettes='gTilesetPalettes_InsideBuilding',callback='InitTilesetAnim_Building'))
        header=self.files['src/data/tilesets/headers.h'].decode().split('const struct Tileset gTileset_EternaDevGatePrimary')[1]
        for value in bindings.values():self.assertIn(value,header)
        with self.assertRaises(ValueError):a.asset_bindings('', 'Missing')

    def test_no_save_id_general_northern_or_existing_gate_writes(self):
        self.assertEqual(len(self.files),36)
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
        original=Path.read_text;target=HERE/'staged/Route206_North/map.json'
        for mode in ('foreign','index','connection'):
            def read(path,*args,**kwargs):
                data=original(path,*args,**kwargs)
                if path==target and mode!='connection':
                    h=json.loads(data);h['warp_events'][0]['dest_map' if mode=='foreign' else 'dest_warp_id']='MAP_MISSING' if mode=='foreign' else '99';return json.dumps(h)
                if mode=='connection' and path==HERE/'staged/EternaCity/map.json':
                    h=json.loads(data);h['connections'][0]['offset']=1;return json.dumps(h)
                return data
            with self.subTest(mode=mode),mock.patch.object(Path,'read_text',new=read),self.assertRaises(ValueError):a.assemble(ROOT)

    def test_misaligned_bank_and_dirty_baseline_rejected(self):
        original=Path.read_bytes
        def read(path):
            data=original(path)
            return data[:-1] if path==HERE/'city-family/secondary-metatiles.bin' else data
        with mock.patch.object(Path,'read_bytes',new=read),self.assertRaises(ValueError):a.assemble(ROOT)
        with mock.patch.object(a.base,'verified_file',return_value=b'changed'),self.assertRaises(ValueError):a.inputs(ROOT)

    def test_install_requires_marker_current_branch_head_and_clean_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp);engine=repo/a.ENGINE;engine.mkdir(parents=True)
            with mock.patch.object(a.base,'git',return_value=b'main\n'),self.assertRaises(ValueError):a.install(repo)
            (engine/'.map_qa_throwaway').touch()
            for responses in ([b'main\n'],[b'codex/eterna-runtime-scratch-test\n',b'wrong\n'],
                              [b'codex/eterna-runtime-scratch-test\n',(a.BASE+'\n').encode(),b' M source.c\n']):
                with mock.patch.object(a.base,'git',side_effect=responses),self.assertRaises(ValueError):a.install(repo)
            self.assertEqual(list(engine.iterdir()),[engine/'.map_qa_throwaway'])


class ElevationNavigationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec=importlib.util.spec_from_file_location('eterna_height_navigation',HERE/'run_runtime_qa.py')
        cls.q=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.q)

    def grid(self,rows,solids=(),warps=()):
        return types.SimpleNamespace(
            inside=lambda x,y:0<=y<len(rows) and 0<=x<len(rows[0]),
            walkable=lambda x,y:0<=y<len(rows) and 0<=x<len(rows[0]) and (x,y) not in solids,
            elevation=lambda x,y:rows[y][x],warp_at=lambda x,y:(x,y) if (x,y) in warps else None)

    def test_bridge_does_not_allow_deck4_to_ground3_shortcut(self):
        m=self.grid([[4,15,3]])
        self.assertIsNone(self.q.elevation_path(m,(0,0),{(2,0)},start_elevation=4))
        self.assertEqual(self.q.elevation_path(m,(2,0),{(1,0)},start_elevation=3),['left'])

    def test_transition0_allows_a_real_change_between_layers(self):
        m=self.grid([[3,0,4]])
        self.assertEqual(self.q.elevation_path(m,(0,0),{(2,0)},start_elevation=3),['right','right'])

    def test_leaving15_preserves_layer_for_that_step_like_native_update(self):
        m=self.grid([[3,15,0,4]])
        self.assertIsNone(self.q.elevation_path(m,(0,0),{(3,0)},start_elevation=3))
        m=self.grid([[3,15,0,0,4]])
        self.assertEqual(self.q.elevation_path(m,(0,0),{(4,0)},start_elevation=3),['right']*4)

    def test_path_search_keeps_same_coordinate_on_different_layers_distinct(self):
        m=self.grid([[3,15,4],[0,0,4]])
        path=self.q.elevation_path(m,(0,0),{(2,0)},start_elevation=3)
        self.assertIsNotNone(path);self.assertEqual(len(path),4);self.assertEqual(path[0],'down')
        self.assertEqual(tuple(sum(self.q.DIRS[d][i] for d in path) for i in (0,1)),(2,0))

    def test_solids_warps_and_invalid_elevation_still_refuse_bad_paths(self):
        self.assertIsNone(self.q.elevation_path(self.grid([[3,3,3]],solids={(1,0)}),(0,0),{(2,0)},start_elevation=3))
        self.assertIsNone(self.q.elevation_path(self.grid([[3,3,3]],warps={(1,0)}),(0,0),{(2,0)},start_elevation=3))
        with self.assertRaises(ValueError):self.q.elevation_path(self.grid([[3]]),(0,0),{(0,0)},start_elevation=16)

    def test_arrow_warp_at_current_tile_cannot_be_used_as_an_ordinary_footstep(self):
        m=self.grid([[3],[3],[3]],warps={(0,1)});m.behavior=lambda x,y:'MB_NORTH_ARROW_WARP' if (x,y)==(0,1) else 'MB_NORMAL'
        self.assertIsNone(self.q.elevation_path(m,(0,1),{(0,0)},start_elevation=3))
        self.assertEqual(self.q.elevation_path(m,(0,1),{(0,2)},start_elevation=3),['down'])

    def test_read_only_observation_uses_compiled_offsets_and_actual_object_ids(self):
        raw=bytearray(16*16);raw[2*16+11]=0xA4;raw[5*16]=1;raw[5*16+8]=123;raw[5*16+11]=0xB3
        calls=[]
        def read(address,size):
            calls.append((address,size))
            return b'\x02' if address==103 else bytes(raw)
        g=types.SimpleNamespace(off={'oe.size':16,'avatar.objectEventId':3,'oe.elevationByte':11,'oe.localId':8},
            sym={'gPlayerAvatar':100,'gObjectEvents':200},c={'OBJ_EVENT_ID_FOLLOWER':123},gdb=types.SimpleNamespace(read=read))
        self.assertEqual(self.q.observed_elevations(types.SimpleNamespace(g=g)),dict(player=4,follower=3))
        self.assertEqual(calls,[(103,1),(200,256)])

    def test_driver_state_is_falsey_even_when_it_contains_live_attributes(self):
        # Real game.State inherits dict but stores snapshots as attributes.
        # A successful Driver.step therefore returns an empty/falsey dict.
        path=ROOT/'Pokemon Game/scripts/claude_play/game.py'
        spec=importlib.util.spec_from_file_location('eterna_actual_state',path)
        game=importlib.util.module_from_spec(spec);spec.loader.exec_module(game)
        state=game.State();state.cb2='CB2_Overworld';state.x=10;state.y=16
        self.assertFalse(bool(state));self.assertIsNotNone(state)
        launcher=(HERE/'run_runtime_qa.py').read_text()
        self.assertIn('moved is not None and at==',launcher)
        self.assertIn('if moved is None:continue',launcher)
        self.assertIn('if returned is None or not self.d.field_ready(returned)',launcher)

    def test_source_guard_rejects_unmarked_changed_and_escaping_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);recipe=dict(status='DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE',files={})
            with self.assertRaises(ValueError):self.q.validate_source(root,recipe)
            (root/'.map_qa_throwaway').touch();recipe['files']={'../outside':'bad'}
            with self.assertRaises(ValueError):self.q.validate_source(root,recipe)
            (root/'inside').write_bytes(b'good');recipe['files']={'inside':a.sha(b'bad')}
            with self.assertRaises(ValueError):self.q.validate_source(root,recipe)
            recipe['files']={'inside':a.sha(b'good')};self.q.validate_source(root,recipe)


if __name__=='__main__':unittest.main()
