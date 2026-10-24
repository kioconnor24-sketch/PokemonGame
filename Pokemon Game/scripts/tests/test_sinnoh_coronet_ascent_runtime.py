"""Original Coronet six-map DEV install cannot affect production or external geography."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/coronet-ascent'
spec=importlib.util.spec_from_file_location('victory_scene_test',HERE/'prepare_runtime.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)

class CoronetAscentRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.files,cls.receipt=r.assemble(ROOT)

    def test_original19_prefix_and_only_six_temporary_maps_no_origins_or_graphics(self):
        groups=json.loads(self.files['data/maps/map_groups.json']);old=json.loads((ROOT/r.ENGINE/'data/maps/map_groups.json').read_text())
        self.assertEqual(groups['gMapGroup_Sinnoh'][:19],old['gMapGroup_Sinnoh'])
        self.assertEqual(groups['gMapGroup_Sinnoh'][19:],list(r.MAPS));self.assertEqual(len(groups['gMapGroup_Sinnoh']),25)
        self.assertEqual(list(self.receipt['temporary_map_slots'].values()),[19,20,21,22,23,24])
        self.assertEqual(len(self.files),29)
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

    def test_same_floor_pair_distinct_and_all_external_anchors_still_solid(self):
        import struct
        names=list(r.MAPS);h=json.loads(self.files[f'data/maps/{names[0]}/map.json'])
        a,b=h['warp_events'][:2]
        self.assertEqual((a['x'],a['y'],b['x'],b['y']),(7,23,7,12))
        self.assertEqual((a['dest_map'],b['dest_map']),(h['id'],h['id']))
        self.assertEqual((a['dest_warp_id'],b['dest_warp_id']),('1','0'))
        recipe=json.loads((HERE/'shell-recipe.json').read_text())
        for name,(w,_) in r.MAPS.items():
            raw=self.files[f'data/layouts/{name}/map.bin']
            for x,y in recipe['maps'][name]['sealed_external_ports']:
                self.assertTrue(struct.unpack_from('<H',raw,2*(y*w+x))[0]&0xc00)

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
                p=d/'staged/SinnohMtCoronet_2F'/filename
                if filename=='map.json':
                    h=json.loads(p.read_text());h['warp_events'][0]['x']+=1;p.write_text(json.dumps(h))
                else:
                    raw=bytearray(p.read_bytes());raw[0]^=1;p.write_bytes(raw)
                with patch.object(r,'HERE',d),self.assertRaisesRegex(ValueError,'tested original packet'):r.assemble(ROOT)

    def test_qa_scope_and_hook_restoration(self):
        script=r"""
import importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
p=Path(sys.argv[1]);sp=importlib.util.spec_from_file_location('upper_qa_probe',p)
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);old=m.shared.MAPS
def fake(args):
 import driver,map_qa as q
 assert q._wrapper(args.engine).driver is driver
 assert m.shared.MAPS==('MAP_SINNOH_MT_CORONET_2F', 'MAP_SINNOH_MT_CORONET_3F', 'MAP_SINNOH_MT_CORONET_OUTSIDE_SOUTH', 'MAP_SINNOH_MT_CORONET_OUTSIDE_NORTH', 'MAP_SINNOH_MT_CORONET_4F_ROOMS_1_AND_2', 'MAP_SINNOH_MT_CORONET_4F_ROOM_3')
 return 0
m.shared.run=fake
assert m.run(SimpleNamespace(engine=Path(sys.argv[2])))==0
assert m.shared.MAPS==old
"""
        result=subprocess.run([sys.executable,'-c',script,str(HERE/'run_runtime_qa.py'),str(ROOT/r.ENGINE)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_main_checkout_wrong_base_dirty_or_path_escape_refused(self):
        with self.assertRaisesRegex(ValueError,'marked disposable'):r.install(ROOT)
        with tempfile.TemporaryDirectory() as temp:
            repo=Path(temp);e=repo/r.ENGINE;e.mkdir(parents=True);(e/'.map_qa_throwaway').touch()
            def wrong(repo,*args):return b'codex/coronet-ascent-runtime-scratch-test\n' if args[0]=='branch' else b'0'*40+b'\n'
            with patch.object(r.base,'git',side_effect=wrong),self.assertRaisesRegex(ValueError,'exact production baseline'):r.install(repo)
            def clean(repo,*args):
                if args[0]=='branch':return b'codex/coronet-ascent-runtime-scratch-test\n'
                if args[0]=='rev-parse':return (r.BASE+'\n').encode()
                return b''
            with patch.object(r.base,'git',side_effect=clean),patch.object(r,'assemble',return_value=({'../escape':b'x'},{})),self.assertRaisesRegex(ValueError,'escapes engine'):r.install(repo)
            def dirty(repo,*args):
                return b' M Pokemon Game/engine/src/save.c\n' if args[0]=='status' else clean(repo,*args)
            with patch.object(r.base,'git',side_effect=dirty),self.assertRaisesRegex(ValueError,'dirty runtime source'):r.install(repo)
            self.assertEqual([p.name for p in e.iterdir()],['.map_qa_throwaway'])

if __name__=='__main__':unittest.main()
