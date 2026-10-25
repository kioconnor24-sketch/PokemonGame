"""South reuse, bounded lower seam and append-only DEV installation regressions."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import sys
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/coronet-south-link'
s=importlib.util.spec_from_file_location('south_link',HERE/'prepare_runtime.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)

class SouthLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files,cls.receipt=m.assemble(ROOT)
        cls.old,cls.old_receipt=m.upper.assemble(ROOT)

    def test_exact_append_only_registry_and_old_indices(self):
        g=json.loads(self.files['data/maps/map_groups.json'])['gMapGroup_Sinnoh']
        prior=self.receipt['existing_map_names_preserved']
        self.assertEqual(g[:19],prior);self.assertEqual(g[19:],list(m.MAPS))
        self.assertEqual(list(self.receipt['temporary_map_slots'].values()),list(range(19,29)))
        old=json.loads(self.old[f'data/maps/{m.UPPER}/map.json'])['warp_events']
        new=json.loads(self.files[f'data/maps/{m.UPPER}/map.json'])['warp_events']
        self.assertEqual(new[:-1],old);self.assertEqual((new[-1]['x'],new[-1]['y']),(27,48))
        self.assertEqual(new[-1]['dest_warp_id'],'0')

    def test_all26_events_reciprocal_and_only_new_pair(self):
        headers=[json.loads(self.files[f'data/maps/{n}/map.json']) for n in m.MAPS]
        byid={h['id']:h for h in headers};total=0
        for h in headers:
            for i,p in enumerate(h['warp_events']):
                other=byid[p['dest_map']]['warp_events'][int(p['dest_warp_id'])]
                self.assertEqual((other['dest_map'],int(other['dest_warp_id'])),(h['id'],i));total+=1
        self.assertEqual(total,26)

    def test_reused_south_full_physics_except_eight_explicit_quarantines(self):
        source,_,_,attrs=m.reuse.south_source();before=m.words(source)
        after=m.words(self.files[f'data/layouts/{m.SOUTH}/map.bin'])
        pa=m.words(self.files['data/tilesets/primary/coronet_south_dev/metatile_attributes.bin'])
        sa=m.words(self.files['data/tilesets/secondary/coronet_south_dev/metatile_attributes.bin'])
        for i,(a,b) in enumerate(zip(before,after)):
            if i in (7*42+5,20*42+36,*[10*42+x for x in range(26,32)]):
                self.assertTrue(b&0xc00);self.assertEqual(a&0xf000,b&0xf000);self.assertEqual((pa+sa)[b&1023]&511,8);continue
            self.assertEqual(a&0xfc00,b&0xfc00)
            self.assertEqual((pa+sa)[b&1023],attrs[str(a&1023)])
        self.assertEqual(before[2*42+29],0x33a5)
        self.assertEqual((pa+sa)[after[2*42+29]&1023],0x1061)

    def test_upper_only_lower_anchor_physics_changed_and_other_eight_maps_identical(self):
        key=f'data/layouts/{m.UPPER}/map.bin'
        a=m.words(self.old[key]);b=m.words(self.files[key])
        changed=[i for i,(x,y) in enumerate(zip(a,b)) if x&0xfc00!=y&0xfc00]
        self.assertEqual(changed,[48*34+27]);self.assertEqual(b[48*34+27],0x3000|m.upper.source.LADDER)
        for name in m.upper.MAPS:
            if name==m.UPPER:continue
            for path in (f'data/layouts/{name}/map.bin',f'data/layouts/{name}/border.bin',f'data/maps/{name}/map.json'):
                self.assertEqual(self.files[path],self.old[path])

    def test_native_assets_aliased_no_global_general_cave_replacement(self):
        self.assertEqual(len(self.files),52)
        self.assertFalse(any(p.startswith(('data/tilesets/primary/general/','data/tilesets/secondary/cave/')) for p in self.files))
        self.assertFalse(any(p.endswith(('.png','.pal','.sav','.gba')) or 'region_map_sections' in p for p in self.files))
        headers=self.files['src/data/tilesets/headers.h'].decode()
        for symbol in ('CoronetSouthPrimary','CoronetSouthSecondary'):self.assertIn('gTileset_'+symbol,headers)
        layouts=json.loads(self.files['data/layouts/layouts.json'])['layouts']
        south=next(v for v in layouts if v['name']==m.SOUTH+'_Layout')
        self.assertEqual(south['primary_tileset'],'gTileset_CoronetSouthPrimary')
        self.assertEqual(south['secondary_tileset'],'gTileset_CoronetSouthSecondary')

    def test_no_story_or_extra_exits_and_old_south_source_unchanged(self):
        h=json.loads(self.files[f'data/maps/{m.SOUTH}/map.json'])
        for key in ('object_events','coord_events','bg_events','connections'):self.assertFalse(h[key])
        self.assertEqual(h['region_map_section'],'MAPSEC_ROUTE_201');self.assertEqual(len(h['warp_events']),1)
        self.assertEqual((h['warp_events'][0]['x'],h['warp_events'][0]['y']),(29,2))
        old=m.reuse.south_source()[2];self.assertEqual(old['warp_events'],[])
        for name,(w,_) in m.upper.MAPS.items():
            for x,y in json.loads((m.upper.HERE/'shell-recipe.json').read_text())['maps'][name]['sealed_external_ports']:
                if name==m.UPPER and (x,y)==(27,48):continue
                self.assertTrue(m.words(self.files[f'data/layouts/{name}/map.bin'])[y*w+x]&0xc00)

    def test_real_mapdata_parser_resolves_isolated_native_banks(self):
        sys.path.insert(0,str(ROOT/'Pokemon Game/scripts/claude_play'))
        import mapdata
        with tempfile.TemporaryDirectory() as t:
            e=Path(t)
            selected=['src/data/tilesets/headers.h','src/data/tilesets/metatiles.h',
                      'data/layouts/layouts.json',f'data/maps/{m.SOUTH}/map.json',
                      f'data/layouts/{m.SOUTH}/map.bin',f'data/layouts/{m.SOUTH}/border.bin',
                      'data/tilesets/primary/coronet_south_dev/metatile_attributes.bin',
                      'data/tilesets/secondary/coronet_south_dev/metatile_attributes.bin']
            for path in selected:
                target=e/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(self.files[path])
            (e/'data/maps/map_groups.json').write_text(json.dumps(dict(group_order=['gMapGroup_Sinnoh'],gMapGroup_Sinnoh=[m.SOUTH])))
            path=Path('include/constants/metatile_behaviors.h');(e/path).parent.mkdir(parents=True)
            (e/path).write_bytes(m.base.verified_file(ROOT,Path(m.ENGINE)/path,'HEAD'))
            info=mapdata.World(e).map('MAP_MT_CORONET_1F_SOUTH')
            self.assertEqual((info.width,info.height),(42,32))
            self.assertEqual(info.behavior(29,2),'MB_LADDER')
            for x in range(26,32):
                self.assertEqual(info.behavior(x,10),'MB_CAVE');self.assertTrue(info.collision(x,10))

    def test_corrupt_art_rejected(self):
        original=m.sha
        target=(m.HERE.parent/'coronet-upper-floors/reused-south-art/cave-family/secondary-metatiles.bin').read_bytes()
        with patch.object(m,'sha',side_effect=lambda data:'bad' if data==target else original(data)):
            with self.assertRaisesRegex(ValueError,'reused art hash'):m.assemble(ROOT)

    def test_wrong_donor_ladder_or_physics_rejected(self):
        source=m.reuse.south_source();raw=bytearray(source[0]);raw[2*(2*42+29)]^=1
        with patch.object(m.reuse,'south_source',return_value=(bytes(raw),*source[1:])):
            with self.assertRaisesRegex(ValueError,'physics|ladder'):m.assemble(ROOT)

    def test_current_baseline_changed_engine_rejected_and_non_scratch_install_refused(self):
        original=m.base.git
        def changed(repo,*args):
            if args==('rev-parse','HEAD:Pokemon Game/engine'):return b'bad\n'
            return original(repo,*args)
        with patch.object(m.base,'git',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'baseline'):m.assemble(ROOT)
        with self.assertRaisesRegex(ValueError,'marked South'):m.install(ROOT)

    def test_bespoke_fast_scope_barriers_and_final_mode_restore(self):
        sys.path.insert(0,str(ROOT/'Pokemon Game/scripts/claude_play'))
        import map_qa as qa
        spec=importlib.util.spec_from_file_location('south_qa_test',HERE/'run_runtime_qa.py')
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        old=runner.a.MAPS;original_main=qa.main;original_warp=qa.Runner.warp
        commands=[]
        def fake(args):
            self.assertEqual(runner.a.MAPS,('MAP_MT_CORONET_1F_SOUTH','MAP_SINNOH_MT_CORONET_2F'))
            return qa.main(['run'])
        with patch.object(qa,'main',side_effect=lambda args:commands.append(args) or 0),patch.object(runner.a,'run',side_effect=fake):
            self.assertEqual(runner.run(SimpleNamespace(mode='batch',affected_only=True,expect=None)),0)
        self.assertEqual(commands[0].count('--blocked'),6)
        self.assertEqual(runner.a.MAPS,old);self.assertIs(qa.main,original_main);self.assertIs(qa.Runner.warp,original_warp)
        with self.assertRaisesRegex(ValueError,'never final'):runner.run(SimpleNamespace(mode='final',affected_only=True,expect=None))
        with patch.object(runner.a,'run',side_effect=RuntimeError('probe')):
            with self.assertRaisesRegex(RuntimeError,'probe'):runner.run(SimpleNamespace(mode='batch',affected_only=True,expect=None))
        self.assertEqual(runner.a.MAPS,old);self.assertIs(qa.main,original_main);self.assertIs(qa.Runner.warp,original_warp)

    def test_baseline_guard_in_real_depth1_checkout_and_changed_engine_refused(self):
        # A tiny independent Git repository models CI with no historical BASE.
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'source';source.mkdir()
            def git(repo,*args):
                return subprocess.check_output(['git','-C',str(repo),*args],stderr=subprocess.DEVNULL).decode().strip()
            git(source,'init','-q')
            engine=source/'Pokemon Game/engine';engine.mkdir(parents=True)
            (engine/'pin.txt').write_text('original engine\n')
            git(source,'add','.')
            git(source,'-c','user.name=fixture','-c','user.email=fixture@example.invalid','commit','-qm','original')
            tree=git(source,'rev-parse','HEAD:Pokemon Game/engine')
            (source/'docs.txt').write_text('docs only\n');git(source,'add','.')
            git(source,'-c','user.name=fixture','-c','user.email=fixture@example.invalid','commit','-qm','docs')
            shallow=Path(t)/'shallow'
            subprocess.run(['git','clone','-q','--depth=1',source.as_uri(),str(shallow)],check=True,stderr=subprocess.DEVNULL)
            self.assertEqual(git(shallow,'rev-parse','--is-shallow-repository'),'true')
            self.assertNotEqual(subprocess.run(['git','-C',str(shallow),'cat-file','-e',m.BASE],stderr=subprocess.DEVNULL).returncode,0)
            with patch.object(m,'BASE_ENGINE_TREE',tree):
                m.verify_baseline_engine(shallow)
                (shallow/'Pokemon Game/engine/pin.txt').write_text('changed engine\n')
                git(shallow,'add','.')
                git(shallow,'-c','user.name=fixture','-c','user.email=fixture@example.invalid','commit','-qm','engine changed')
                with self.assertRaisesRegex(ValueError,'baseline'):
                    m.verify_baseline_engine(shallow)

    def test_deterministic_recipe_hashes(self):
        other,receipt=m.assemble(ROOT);self.assertEqual(other,self.files);self.assertEqual(receipt,self.receipt)
        for path,raw in self.files.items():self.assertEqual(m.sha(raw),self.receipt['files'][path])

if __name__=='__main__':unittest.main()
