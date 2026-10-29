"""Six-map DEV assembler: unchanged source/art and exact legacy registry prefix."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import sys
import types
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/forest-chateau'
spec=importlib.util.spec_from_file_location('forest_dev_runtime',HERE/'prepare_runtime.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ROOT=HERE.parents[4]


class ForestRuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.files,cls.receipt=a.assemble(ROOT);cls.before=a.inputs(ROOT)

    def test_all_existing_map_layout_and_include_prefixes_survive(self):
        before=json.loads(self.before['data/maps/map_groups.json']);after=json.loads(self.files['data/maps/map_groups.json'])
        self.assertEqual(len(before['gMapGroup_Sinnoh']),41)
        for k,v in before.items():self.assertEqual(after[k][:len(v)] if k=='gMapGroup_Sinnoh' else after[k],v)
        self.assertEqual(self.receipt['temporary_map_slots'],dict(zip(a.MAPS,range(41,47))))
        before=json.loads(self.before['data/layouts/layouts.json'])['layouts'];after=json.loads(self.files['data/layouts/layouts.json'])['layouts']
        self.assertEqual(before,after[:len(before)])
        for p in ('data/event_scripts.s','include/tilesets.h','src/data/tilesets/headers.h','src/data/tilesets/metatiles.h'):
            self.assertTrue(self.files[p].startswith(self.before[p]))

    def test_installed_source_warps_and_all_geometry_reuse_exact_accepted_art(self):
        count=0;self_map=0
        for name in a.MAPS:
            folder=HERE/'staged'/name
            for p in ('map.bin','border.bin'):
                self.assertEqual(self.files[f'data/layouts/{name}/{p}'],(folder/('averon-'+p if name=='EternaForest' else p)).read_bytes())
            h=json.loads((folder/'map.json').read_text());self.assertEqual(h,self.receipt['source_headers'][name])
            count+=len(h['warp_events']);self_map+=sum(w['dest_map']==h['id'] for w in h['warp_events'])
            h['region_map_section']='MAPSEC_ROUTE_201';self.assertEqual(h,json.loads(self.files[f'data/maps/{name}/map.json']))
            self.assertEqual(self.files[f'data/maps/{name}/scripts.inc'],(name+'_MapScripts::\n\t.byte 0\n').encode())
        self.assertEqual((count,self_map),(31,15))

    def test_all_interiors_share_building_with_distinct_museum_and_generic_metadata(self):
        d={v['name']:v for v in json.loads(self.files['data/layouts/layouts.json'])['layouts'][-6:]}
        entrance=d['OldChateau_Entrance_Layout'];other=d['OldChateau_2F_Layout']
        self.assertEqual(entrance['primary_tileset'],other['primary_tileset'])
        self.assertNotEqual(entrance['secondary_tileset'],other['secondary_tileset'])
        for name in ('OldChateau_DiningRoom','OldChateau_SideRoom_1','OldChateau_SideRoom_2'):
            for key in ('primary_tileset','secondary_tileset'):self.assertEqual(d[name+'_Layout'][key],other[key])

    def test_actual_building_alias_and_all_existing_animation_bindings_are_preserved(self):
        old=self.before['src/data/tilesets/headers.h'].decode();new=self.files['src/data/tilesets/headers.h'].decode()[len(old):]
        for graphics in ('General','Rustboro','Building','LilycoveMuseum','GenericBuilding'):
            for v in a.asset_bindings(old,graphics).values():self.assertIn(v,new)
        self.assertEqual(a.asset_bindings(old,'Building')['tiles'],'gTilesetTiles_InsideBuilding')
        with self.assertRaises(ValueError):a.asset_bindings('', 'Missing')

    def test_no_save_id_global_art_northern_or_existing_production_map_writes(self):
        self.assertEqual(len(self.files),42)
        for p in self.files:
            self.assertFalse(any(s in p for s in ('region_map_sections','mapsec-pins','pokemon.h','global.h','/general/')))
            self.assertFalse(any('/'+n+'/' in p for n in self.receipt['existing_map_names_preserved']))
        self.assertTrue(all(v['region_map_section']=='MAPSEC_PENDING_OWNER' for v in self.receipt['source_headers'].values()))

    def test_all_six_tilesets_and_maps_parse_in_real_qa_world(self):
        path=HERE.parents[3]/'scripts/claude_play/mapdata.py'
        spec=importlib.util.spec_from_file_location('forest_real_world',path)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
        engine=ROOT/a.ENGINE;read_text=Path.read_text;read_bytes=Path.read_bytes
        def lookup(path):
            try:return self.files.get(str(path.relative_to(engine)))
            except ValueError:return None
        def text(path,*args,**kwargs):
            v=lookup(path);return v.decode() if v is not None else read_text(path,*args,**kwargs)
        def binary(path):
            v=lookup(path);return v if v is not None else read_bytes(path)
        with mock.patch.object(Path,'read_text',new=text),mock.patch.object(Path,'read_bytes',new=binary):
            w=m.World(engine)
            for name,(width,height) in a.MAPS.items():
                info=w.map(self.receipt['source_headers'][name]['id'])
                self.assertEqual((info.width,info.height),(width,height));self.assertTrue(info._primary and info._secondary)

    def test_follower_returns_after_a_real_falsey_state_snapshot(self):
        self.follower_fixture(False)

    def test_follower_does_not_send_a_return_for_a_failed_step(self):
        self.follower_fixture(True)

    def follower_fixture(self,fail):
        scripts=ROOT/'Pokemon Game/scripts/claude_play';sys.path.insert(0,str(scripts))
        import map_qa as qa
        import game
        d=types.SimpleNamespace(position=('MAP_TEST',(1,1)),steps=[])
        d.here=lambda:d.position;d.log=lambda *args,**kwargs:None
        d.live_map=lambda mid:types.SimpleNamespace(walkable=lambda x,y:True,warp_at=lambda x,y:None,objects=[])
        def step(direction):
            d.steps.append(direction)
            if fail:return None
            mid,(x,y)=d.position;dx,dy=qa.DIRS[direction];d.position=(mid,(x+dx,y+dy))
            state=game.State();state.cb2='CB2_Overworld';state.x=x+dx;state.y=y+dy
            self.assertFalse(bool(state));return state
        d.step=step
        runner=qa.Runner(d,types.SimpleNamespace(map=d.live_map),{},None)
        play=types.SimpleNamespace(observe=lambda driver,label:dict(follower=dict(invisible=False)))
        with mock.patch.dict(sys.modules,{'run':play}):self.assertTrue(runner.follower('actual State fixture'))
        self.assertEqual(d.steps,['up'] if fail else ['up','down']);self.assertEqual(d.position,('MAP_TEST',(1,1)))

    def test_runtime_floor_repair_is_opaque_and_preserves_source_attributes(self):
        import struct
        records=(HERE/'entrance-metatiles.bin').read_bytes()
        self.assertEqual(records[(660-512)*16:(661-512)*16],records[(649-512)*16:(650-512)*16])
        source=json.loads((HERE/'staged/OldChateau_Entrance/attributes.json').read_text())['used_source_attribute_words']
        self.assertEqual(struct.unpack_from('<H',(HERE/'entrance-attributes.bin').read_bytes(),(660-512)*2)[0],source['660'])
        images=[a.art.pack.accepted.dual.indexed((ROOT/a.ENGINE/('data/tilesets/'+p+'/tiles.png')).read_bytes()) for p in ('primary/building','secondary/lilycove_museum')]
        # Every pixel in the repaired lower layer must cover the GBA backdrop;
        # transparent color0 is valid in the upper layer only.
        for word in struct.unpack_from('<8H',records,(660-512)*16)[:4]:
            bank,tile=divmod(word&1023,512)
            pixels=images[bank].crop((tile%16*8,tile//16*8,tile%16*8+8,tile//16*8+8))
            self.assertNotIn(0,set(pixels.getdata()))

    def test_plan_reproduces_without_writing_any_input(self):
        self.assertEqual(a.assemble(ROOT),(self.files,self.receipt))
        self.assertEqual(a.inputs(ROOT),self.before)

    def test_runtime_launcher_refuses_unmarked_changed_or_escaping_source(self):
        spec=importlib.util.spec_from_file_location('forest_actual_driver_launcher',HERE/'run_runtime_qa.py')
        launcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(launcher)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);recipe=dict(status='DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE',files={})
            with self.assertRaises(ValueError):launcher.validate_source(root,recipe)
            (root/'.map_qa_throwaway').touch();recipe['files']={'../outside':'bad'}
            with self.assertRaises(ValueError):launcher.validate_source(root,recipe)
            (root/'inside').write_bytes(b'actual');recipe['files']={'inside':a.sha(b'wrong')}
            with self.assertRaises(ValueError):launcher.validate_source(root,recipe)
            recipe['files']={'inside':a.sha(b'actual')};launcher.validate_source(root,recipe)

    def test_foreign_or_invalid_self_warp_rejected_before_writing(self):
        read_text=Path.read_text;target=HERE/'staged/OldChateau_2F/map.json'
        for key,value in [('dest_map','MAP_MISSING'),('dest_warp_id','99')]:
            def text(path,*args,**kwargs):
                raw=read_text(path,*args,**kwargs)
                if path==target:
                    h=json.loads(raw);h['warp_events'][2][key]=value;return json.dumps(h)
                return raw
            with self.subTest(key=key),mock.patch.object(Path,'read_text',new=text),self.assertRaises(ValueError):a.assemble(ROOT)

    def test_misaligned_bank_dirty_baseline_and_unmarked_install_rejected(self):
        read=Path.read_bytes;target=HERE/'generic-metatiles.bin'
        with mock.patch.object(Path,'read_bytes',new=lambda p:read(p)[:-1] if p==target else read(p)),self.assertRaises(ValueError):a.assemble(ROOT)
        with mock.patch.object(a.base,'verified_file',return_value=b'changed'),self.assertRaises(ValueError):a.inputs(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);engine=root/a.ENGINE;engine.mkdir(parents=True)
            with mock.patch.object(a.base,'git',return_value=b'main\n'),self.assertRaises(ValueError):a.install(root)
            (engine/'.map_qa_throwaway').touch()
            for replies in ([b'main\n'],[b'codex/forest-runtime-scratch-test\n',b'wrong\n'],
                            [b'codex/forest-runtime-scratch-test\n',(a.BASE+'\n').encode(),b' M source.c\n']):
                with mock.patch.object(a.base,'git',side_effect=replies),self.assertRaises(ValueError):a.install(root)
            self.assertEqual(list(engine.iterdir()),[engine/'.map_qa_throwaway'])


if __name__=='__main__':unittest.main()
