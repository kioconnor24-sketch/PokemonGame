"""Thirteen-map current-main DEV plan reuses art and preserves production prefixes."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/eastern-loop'
spec=importlib.util.spec_from_file_location('eastern_dev_runtime',HERE/'prepare_runtime.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ROOT=HERE.parents[4]


class RuntimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.files,cls.receipt=a.assemble(ROOT);cls.before=a.inputs(ROOT)

    def test_all_existing_map_layout_and_include_prefixes_survive(self):
        before=json.loads(self.before['data/maps/map_groups.json']);after=json.loads(self.files['data/maps/map_groups.json'])
        self.assertEqual(len(before['gMapGroup_Sinnoh']),41)
        for k,v in before.items():self.assertEqual(after[k][:len(v)] if k=='gMapGroup_Sinnoh' else after[k],v)
        self.assertEqual(self.receipt['temporary_map_slots'],dict(zip(a.MAPS,range(41,54))))
        before=json.loads(self.before['data/layouts/layouts.json'])['layouts'];after=json.loads(self.files['data/layouts/layouts.json'])['layouts']
        self.assertEqual(before,after[:len(before)])
        for p in ('data/event_scripts.s','include/tilesets.h','src/data/tilesets/headers.h','src/data/tilesets/metatiles.h'):
            self.assertTrue(self.files[p].startswith(self.before[p]))

    def test_installed_geometry_and_all_warp_arrays_reuse_exact_artifacts(self):
        for name in a.MAPS:
            folder=(HERE/'hotel-link/staged'/name) if name=='HotelGrandLake' else (HERE/'staged'/name)
            for p,suffix in [('map.bin','map'),('border.bin','border')]:
                self.assertEqual(self.files[f'data/layouts/{name}/{p}'],(a.crossing.patch((folder/'averon-map.bin').read_bytes()) if p=='map.bin' and name=='Route212_South' else (HERE/'hotel-link/valor-map.bin' if p=='map.bin' and name=='ValorLakefront' else HERE/'hotel-link/route213-map.bin' if p=='map.bin' and name=='Route213' else folder/('border.bin' if p=='border.bin' and (name.endswith('_Access') or name=='HotelGrandLake') else f'averon-{suffix}.bin')).read_bytes()))
            source=json.loads((HERE/'hotel-link/route213-map.json' if name=='Route213' else folder/'map.json').read_text());target=json.loads(self.files[f'data/maps/{name}/map.json'])
            self.assertEqual(source,self.receipt['source_headers'][name]);source['region_map_section']='MAPSEC_ROUTE_201'
            self.assertEqual(source,target)
            self.assertEqual(self.files[f'data/maps/{name}/scripts.inc'],(name+'_MapScripts::\n\t.byte 0\n').encode())

    def test_all_eight_outdoors_and_five_gate_families_are_separate_and_coherent(self):
        layouts=json.loads(self.files['data/layouts/layouts.json'])['layouts'][-13:];d={v['name']:v for v in layouts}
        groups=([n for n in a.MAPS if not n.endswith('_Access') and n!='HotelGrandLake'],[n for n in a.MAPS if n.endswith('_Access') or n=='HotelGrandLake'])
        self.assertEqual(tuple(map(len,groups)),(8,5))
        for names in groups:
            for name in names:
                for key in ('primary_tileset','secondary_tileset'):
                    self.assertEqual(d[name+'_Layout'][key],d[names[0]+'_Layout'][key])
        self.assertEqual(d['Route213_Layout']['primary_tileset'],'gTileset_General')
        self.assertNotEqual(d['VeilstoneCity_Layout']['secondary_tileset'],d['Route215_Access_Layout']['secondary_tileset'])
        for name in ('General','Rustboro','Building','Shop'):
            for value in a.asset_bindings(self.before['src/data/tilesets/headers.h'].decode(),name).values():
                self.assertIn(value,self.files['src/data/tilesets/headers.h'].decode())
        self.assertEqual(len(self.files['data/tilesets/primary/eastern_dev_gateprimary/metatiles.bin']),8*16)

    def test_no_save_id_general_northern_or_existing_gate_writes(self):
        self.assertEqual(len(self.files),66)
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
        original=Path.read_text;target=HERE/'staged/Route213_Access/map.json'
        for mode in ('foreign','index','connection'):
            def read(path,*args,**kwargs):
                data=original(path,*args,**kwargs)
                if path==target and mode!='connection':
                    h=json.loads(data);h['warp_events'][0]['dest_map' if mode=='foreign' else 'dest_warp_id']='MAP_MISSING' if mode=='foreign' else '99';return json.dumps(h)
                if mode=='connection' and path==HERE/'hotel-link/route213-map.json':
                    h=json.loads(data);h['connections'][0]['offset']=1;return json.dumps(h)
                return data
            with self.subTest(mode=mode),mock.patch.object(Path,'read_text',new=read),self.assertRaises(ValueError):a.assemble(ROOT)

    def test_misaligned_bank_and_dirty_baseline_rejected(self):
        original=Path.read_bytes
        def read(path):
            data=original(path)
            return data[:-1] if path==HERE/'hotel-link/outdoor-family/secondary-metatiles.bin' else data
        with mock.patch.object(Path,'read_bytes',new=read),self.assertRaises(ValueError):a.assemble(ROOT)
        with mock.patch.object(a.base,'verified_file',return_value=b'changed'),self.assertRaises(ValueError):a.inputs(ROOT)

    def test_native_general_reuse_rejects_either_changed_primary_metadata_array(self):
        original=Path.read_bytes
        for filename in ('primary-metatiles.bin','primary-attributes.bin'):
            target=HERE/'hotel-link/outdoor-family'/filename
            def read(path):
                data=original(path)
                return bytes([data[0]^1])+data[1:] if path==target else data
            with self.subTest(filename=filename),mock.patch.object(Path,'read_bytes',new=read),self.assertRaisesRegex(ValueError,'native General primary metadata'):
                a.assemble(ROOT)

    def test_remaining_route212_rails_block_feet_and_single_ground_crossing_connects(self):
        path=HERE/'run_runtime_qa.py'
        spec=importlib.util.spec_from_file_location('eastern_foot_qa',path)
        qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
        path=HERE.parents[3]/'scripts/claude_play/mapdata.py'
        spec=importlib.util.spec_from_file_location('eastern_foot_maps',path)
        md=importlib.util.module_from_spec(spec);spec.loader.exec_module(md)
        engine=ROOT/a.ENGINE;read_text=Path.read_text;read_bytes=Path.read_bytes
        def lookup(path):
            try:return self.files.get(str(path.relative_to(engine)))
            except ValueError:return None
        def text(path,*args,**kwargs):
            value=lookup(path);return value.decode() if value is not None else read_text(path,*args,**kwargs)
        def binary(path):
            value=lookup(path);return value if value is not None else read_bytes(path)
        with mock.patch.object(Path,'read_text',new=text),mock.patch.object(Path,'read_bytes',new=binary):
            m=md.World(engine).map('MAP_ROUTE212_SOUTH')
            for x in range(36,41):
                self.assertEqual((m.collision(x,11),m.elevation(x,11),m.behavior(x,11)),(0,15,'MB_NORMAL' if x==38 else 'MB_HORIZONTAL_RAIL'))
                self.assertEqual(qa.foot_walkable(m,x,11),x==38)
            # Original runtime failure is preserved by negative source fixtures;
            # the sole new ground cell now allows an ordinary foot route.
            self.assertIsNotNone(qa.elevation_path(m,(36,12),{(10,0)},start_elevation=3))
            self.assertIsNone(qa.elevation_path(m,(36,12),{(36,11)},start_elevation=3))
            self.assertIsNotNone(qa.elevation_path(m,(36,12),{(37,12)},start_elevation=3))
            self.assertNotIn(('up',(36,11)),list(qa.follower_neighbors(m,(36,12))))
            plan=qa.acro_crossing_plan(m,(129,15),(10,0),3)
            self.assertIsNone(plan)  # ordinary ground crossing makes Acro unnecessary
            self.assertIsNone(qa.acro_crossing_plan(m,(10,0),(129,15),3))
            self.assertIsNone(qa.acro_crossing_plan(m,(36,12),(37,12),3))
            changed=list(m.blocks);changed[11*m.width+36]^=0x1000
            with self.assertRaisesRegex(ValueError,'rail portal changed'):
                qa.acro_crossing_plan(m.with_live_blocks(changed),(129,15),(10,0),3)


    def test_subset_evidence_cannot_silently_replace_full_corridor_scope(self):
        spec=importlib.util.spec_from_file_location('eastern_scope_qa',HERE/'run_runtime_qa.py')
        qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
        self.assertEqual(qa.select_scope(),(qa.MAPS,'eastern-thirteen'))
        self.assertEqual(qa.select_scope(['MAP_ROUTE212_NORTH'],'north'),(('MAP_ROUTE212_NORTH',),'eastern-subset-north'))
        for maps,label in ((['MAP_ROUTE212_NORTH'],None),(None,'north'),([], 'north'),
                           (['MAP_ROUTE212_NORTH']*2,'north'),(['MAP_INVALID'],'bad'),
                           (['MAP_ROUTE212_NORTH'],'../full')):
            with self.subTest(maps=maps,label=label),self.assertRaises(ValueError):qa.select_scope(maps,label)

    def test_explicit_acro_fixture_reuses_existing_grant_without_geometry_or_default_changes(self):
        before={p:bytes(d) for p,d in self.files.items()};files,receipt=a.assemble(ROOT,acro_fixture=True)
        changed=[p for p in files if files[p]!=before[p]]
        self.assertEqual(changed,['data/maps/Route212_South/scripts.inc'])
        script=files[changed[0]].decode()
        self.assertEqual(script.count('additem ITEM_ACRO_BIKE'),1)
        self.assertIn('checkitem ITEM_ACRO_BIKE',script)
        self.assertNotIn('setflag',script)
        self.assertIn('TEST-ONLY map_qa fixture grant',script)
        self.assertEqual(receipt['dev_fixture']['item_grants'],['ITEM_ACRO_BIKE'])
        self.assertEqual(receipt['dev_fixture']['flag_grants'],[])
        self.assertEqual(set(files),set(before));self.assertEqual(len(files),66)
        self.assertEqual(a.assemble(ROOT),(self.files,self.receipt))
        published=json.loads((HERE/'runtime-recipe-west41.json').read_text())
        self.assertEqual(self.receipt,published)  # separate source-pinned41-slot no-grant contract; 19/22/30-slot recipes retained
        self.assertNotIn('dev_fixture',self.receipt)
        for bad in (1,'yes',None):
            with self.subTest(value=bad),self.assertRaises(ValueError):a.assemble(ROOT,acro_fixture=bad)

    def test_install_requires_marker_current_branch_head_and_clean_engine(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp);engine=repo/a.ENGINE;engine.mkdir(parents=True)
            with mock.patch.object(a.base,'git',return_value=b'main\n'),self.assertRaises(ValueError):a.install(repo)
            (engine/'.map_qa_throwaway').touch()
            for responses in ([b'main\n'],[b'codex/eastern-runtime-scratch-test\n',b'wrong\n'],
                              [b'codex/eastern-runtime-scratch-test\n',(a.BASE+'\n').encode(),b' M source.c\n']):
                with mock.patch.object(a.base,'git',side_effect=responses),self.assertRaises(ValueError):a.install(repo)
            self.assertEqual(list(engine.iterdir()),[engine/'.map_qa_throwaway'])


if __name__=='__main__':unittest.main()
