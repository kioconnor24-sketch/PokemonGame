"""Real reused-source joins and fail-closed packet-D fixture boundaries."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import tempfile
import sys
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/west-packet-d'
spec = importlib.util.spec_from_file_location('packet_d_test', HERE/'prepare_runtime.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PacketD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.receipt = p.assemble(ROOT)
        w25 = p.module('packet_d_test_w25', HERE.parent/'cycling-road-join/prepare_current_runtime.py')
        cls.before, _ = w25.compose(ROOT)
        cls.data, cls.pins = p.south_inputs(ROOT)
        cls.bindings = {k:dict(tiles='existing',palettes='existing',callback='existing') for k in ('primary','secondary')}

    def test_real_composition_keeps_all_49_registry_and_layout_entries(self):
        old = json.loads(self.before['data/maps/map_groups.json'])
        new = json.loads(self.files['data/maps/map_groups.json'])
        self.assertEqual(new['gMapGroup_Sinnoh'], old['gMapGroup_Sinnoh']+[p.NAME])
        self.assertEqual({k:v for k,v in old.items() if k!='gMapGroup_Sinnoh'}, {k:v for k,v in new.items() if k!='gMapGroup_Sinnoh'})
        a=json.loads(self.before['data/layouts/layouts.json'])['layouts'];b=json.loads(self.files['data/layouts/layouts.json'])['layouts']
        self.assertEqual(b[:-1],a);self.assertEqual((b[-1]['width'],b[-1]['height']),(42,32))
        self.assertEqual(len(self.files),70)
        self.assertEqual(self.receipt['files'],{x:hashlib.sha256(y).hexdigest() for x,y in self.files.items()})

    def test_only_the_proven_port_cells_change(self):
        path='data/layouts/Route207/map.bin';a=p.words(self.before[path]);b=p.words(self.files[path])
        self.assertEqual([(i,x,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y],[(372,0x4A7,0xA7)])
        a=p.words(self.data['averon-map.bin']);b=p.words(self.files['data/layouts/'+p.NAME+'/map.bin'])
        self.assertEqual([(i,x,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y],[(113,0x3222,0x3604),(299,0x361A,0x321A),(876,0x361A,0x3604)])
        self.assertEqual(self.files['data/layouts/'+p.NAME+'/border.bin'],self.data['averon-border.bin'])
        for path,raw in self.before.items():
            if path.startswith(('data/layouts/','data/maps/')) and path not in {'data/layouts/layouts.json','data/maps/map_groups.json','data/layouts/Route207/map.bin','data/maps/Route207/map.json'}:
                self.assertEqual(self.files[path],raw,path)

    def test_reciprocal_warps_and_no_gameplay_events(self):
        a=json.loads(self.files['data/maps/Route207/map.json']);b=json.loads(self.files['data/maps/'+p.NAME+'/map.json'])
        self.assertEqual(a['warp_events'],[dict(x=52,y=5,elevation=0,dest_map=p.MAP_ID,dest_warp_id='0')])
        self.assertEqual(b['warp_events'],[dict(x=5,y=7,elevation=0,dest_map='MAP_ROUTE207',dest_warp_id='0')])
        self.assertEqual(b['region_map_section'],'MAPSEC_ROUTE_201')
        for key in ('connections','object_events','coord_events','bg_events'):self.assertFalse(b[key])
        self.assertIn('MAPSEC_COUNT == 228',self.files['test/averon_packet_d.c'].decode())
        self.assertFalse(any('region_map_sections' in x or 'healing' in x for x in self.files))

    def test_actual_native_behaviors_allow_west_return_and_keep_mud_and_unbuilt_ports_closed(self):
        sys.path.insert(0,str(ROOT/'Pokemon Game/scripts/claude_play'))
        import mapdata
        with tempfile.TemporaryDirectory() as temp:
            e=Path(temp)
            layouts=json.loads(self.files['data/layouts/layouts.json'])
            layouts['layouts']=[x for x in layouts['layouts'] if x.get('name') in {'Route207_Layout',p.NAME+'_Layout'}]
            payload={'data/maps/map_groups.json':p.encode(dict(group_order=['gMapGroup_Sinnoh'],gMapGroup_Sinnoh=['Route207',p.NAME])),
                     'data/layouts/layouts.json':p.encode(layouts),
                     'include/constants/metatile_behaviors.h':(ROOT/'Pokemon Game/engine/include/constants/metatile_behaviors.h').read_bytes()}
            for path,raw in self.files.items():
                if (path.startswith(('data/maps/Route207/','data/maps/'+p.NAME+'/',
                        'data/layouts/Route207/','data/layouts/'+p.NAME+'/',
                        'src/data/tilesets/')) or path.startswith('data/tilesets/') and path.endswith('metatile_attributes.bin')):
                    payload[path]=raw
            for path,raw in payload.items():
                target=e/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            world=mapdata.World(e);south=world.map(p.MAP_ID);route=world.map('MAP_ROUTE207')
            self.assertEqual(south.behavior(5,7),'MB_SOUTH_ARROW_WARP')
            reachable=mapdata.reach_states(south,(5,6))
            self.assertTrue(south.walkable(5,7));self.assertIn((5,7),reachable)
            self.assertIn((36,19),reachable)  # real west-to-east passage approach for later packet E
            for tile in ((36,20),(29,2)):
                self.assertEqual(south.behavior(*tile),'MB_NORMAL');self.assertFalse(south.walkable(*tile))
            self.assertEqual(route.behavior(52,5),'MB_NON_ANIMATED_DOOR')
            self.assertIn((52,5),mapdata.reach_states(route,(15,2)))
            self.assertNotIn((52,5),mapdata.reach_states(route,(9,31)))

    def test_rejects_wrong_prefix_duplicate_and_changed_doorway(self):
        for kind in ('prefix','duplicate','door','warp','layout','registry'):
            files=dict(self.before)
            if kind in ('prefix','duplicate'):
                v=json.loads(files['data/maps/map_groups.json']);v['gMapGroup_Sinnoh'].append(p.NAME if kind=='duplicate' else 'Unexpected');files['data/maps/map_groups.json']=p.encode(v)
            elif kind=='door':
                raw=bytearray(files['data/layouts/Route207/map.bin']);struct.pack_into('<H',raw,744,0xA7);files['data/layouts/Route207/map.bin']=bytes(raw)
            elif kind=='warp':
                v=json.loads(files['data/maps/Route207/map.json']);v['warp_events']=[{}];files['data/maps/Route207/map.json']=p.encode(v)
            elif kind=='layout':
                v=json.loads(files['data/layouts/layouts.json']);v['layouts'].append(dict(id='LAYOUT_MT_CORONET_1F_SOUTH'));files['data/layouts/layouts.json']=p.encode(v)
            else:files['test/data/averon_map_registry_slots.inc']=b'wrong'
            with self.subTest(kind=kind),self.assertRaises(ValueError):p.extend(files,self.data,self.pins,self.bindings)

    def test_rejects_changed_donor_return_and_foreign_gameplay(self):
        pins=copy.deepcopy(self.pins);pins['donor_headers']['data/maps/MtCoronet_1F_South/map.json']['warp_events'][0]['dest_warp_id']='1'
        with self.assertRaises(ValueError):p.extend(self.before,self.data,pins,self.bindings)
        data=dict(self.data);v=json.loads(data['source-header.json']);v['object_events']=[{}];data['source-header.json']=p.encode(v)
        with self.assertRaises(ValueError):p.extend(self.before,data,self.pins,self.bindings)

    def test_source_hash_and_full_semantics_are_enforced(self):
        for repin in (False,True):
            with tempfile.TemporaryDirectory() as temp:
                view=Path(temp);shutil.copytree(HERE/'inputs',view/'inputs');shutil.copyfile(HERE/'source-pins.json',view/'source-pins.json')
                f=view/'inputs/averon-map.bin';raw=bytearray(f.read_bytes());raw[1]^=4;f.write_bytes(raw)
                if repin:
                    pins=json.loads((view/'source-pins.json').read_text());pins['files']['averon-map.bin']['sha256']=p.sha(raw);(view/'source-pins.json').write_text(json.dumps(pins))
                with patch.object(p,'HERE',view),self.assertRaises(ValueError):p.south_inputs(ROOT)

    def test_real_preprocessor_and_linker_require_the_emitted_global_script_table(self):
        # Double-colon exports are processed by the real engine tool. Both GNU
        # ARM and host binutils can verify this architecture-independent ABI.
        assembler=shutil.which('arm-none-eabi-as') or shutil.which('as')
        self.assertIsNotNone(assembler)
        linker=shutil.which('arm-none-eabi-ld') if 'arm-none-eabi' in assembler else shutil.which('ld')
        self.assertIsNotNone(linker)
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);tool=root/'tools/preproc'
            shutil.copytree(ROOT/'Pokemon Game/engine/tools/preproc',tool,ignore=shutil.ignore_patterns('preproc','preproc.exe'))
            chars=root/'include/constants/characters.h';chars.parent.mkdir(parents=True);shutil.copyfile(ROOT/'Pokemon Game/engine/include/constants/characters.h',chars)
            built=subprocess.run(['make','-C',str(tool)],capture_output=True,text=True)
            self.assertEqual(built.returncode,0,built.stderr)
            reference=root/'reference.s';reference.write_text('.global _start\n_start:\n.long MtCoronet_1F_South_MapScripts\n')
            subprocess.run([assembler,str(reference),'-o',str(root/'reference.o')],check=True,capture_output=True)
            table=self.files['data/maps/'+p.NAME+'/scripts.inc']
            outcomes=[]
            for label,raw in [('generated',table),('local-regression',table.replace(b'::',b':'))]:
                script=root/(label+'.s');script.write_bytes(raw)
                processed=subprocess.run([str(tool/'preproc'),'-ie',str(script),str(ROOT/'Pokemon Game/engine/charmap.txt')],input=raw,capture_output=True,check=True).stdout
                output=root/(label+'-processed.s');output.write_bytes(processed)
                obj=root/(label+'.o');subprocess.run([assembler,str(output),'-o',str(obj)],capture_output=True,check=True)
                linked=subprocess.run([linker,'--no-undefined','-e','_start','-Ttext=0x08000000',str(root/'reference.o'),str(obj),'-o',str(root/(label+'.elf'))],capture_output=True,text=True)
                outcomes.append(linked)
            self.assertEqual(outcomes[0].returncode,0,outcomes[0].stderr)
            self.assertNotEqual(outcomes[1].returncode,0)
            self.assertIn('undefined reference',outcomes[1].stderr)

    def test_palette_checkout_crlf_is_not_a_color_waiver(self):
        original=Path.read_bytes
        def changed(path):
            raw=original(path)
            if str(path).endswith('engine/data/tilesets/primary/general/palettes/00.pal'):return raw.replace(b'24 41 82',b'25 41 82')
            return raw
        with patch.object(Path,'read_bytes',changed),self.assertRaisesRegex(ValueError,'graphics dependency'):p.south_inputs(ROOT)


if __name__=='__main__':unittest.main()
