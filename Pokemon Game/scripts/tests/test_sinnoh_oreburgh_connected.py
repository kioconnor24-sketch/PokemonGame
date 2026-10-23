"""Pinned four-area assembly, not production or graphical acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parents[2]/'Averon_Codex_Handoff/design/sinnoh/oreburgh-connected'
spec=importlib.util.spec_from_file_location('oreburgh_connected',HERE/'prepare_candidate.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
ROOT=HERE.parents[4]


class AssemblyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.files,cls.receipt=a.assemble(ROOT)

    def gate(self):return json.loads(self.files['data/maps/OreburghGate_1F/map.json'])

    def test_reuses_pinned_art_and_mine_bytes_without_reconversion(self):
        for n in a.MAPS:
            path=a.SOURCE+('staged/'+n+'.bin' if n.startswith('OreburghMine') else 'city-family/'+n+'/map.bin')
            source=a.blob(ROOT,a.BASE if n.startswith('OreburghMine') else a.ART,path)
            if n=='Route207':source=a.close_unmatched_seam(source)
            self.assertEqual(source,self.files['data/layouts/'+n+'/map.bin'])

    def test_original_group_prefix_and_registry_slots_preserved(self):
        before=json.loads(a.blob(ROOT,a.BASE,a.ENGINE+'data/maps/map_groups.json'))
        after=json.loads(self.files['data/maps/map_groups.json'])
        for group,items in before.items():
            self.assertEqual(items,after[group][:len(items)] if group=='gMapGroup_Sinnoh' else after[group])
        self.assertEqual(after['gMapGroup_Sinnoh'][-4:],list(a.MAPS))

    def test_existing_layouts_and_shared_general_assets_untouched(self):
        before=json.loads(a.blob(ROOT,a.BASE,a.ENGINE+'data/layouts/layouts.json'))['layouts']
        after=json.loads(self.files['data/layouts/layouts.json'])['layouts']
        self.assertEqual(before,after[:len(before)])
        self.assertFalse(any(p.startswith('data/tilesets/primary/general/') for p in self.files))
        self.assertFalse(any(p.endswith('tiles.png') or p.endswith('.pal') for p in self.files))

    def test_no_saved_identity_save_format_or_story_writes(self):
        self.assertNotIn('src/data/region_map/region_map_sections.json',self.files)
        self.assertNotIn('../scripts/averon-mapsec-pins.json',self.files)
        for name in a.MAPS:
            h=json.loads(self.files['data/maps/'+name+'/map.json'])
            self.assertEqual(h['region_map_section'],'MAPSEC_ROUTE_201')
            self.assertEqual(self.receipt['source_headers'][name]['region_map_section'],'MAPSEC_PENDING_OWNER')
            self.assertFalse(h['object_events'] or h['coord_events'] or h['bg_events'])

    def test_gate_opens_four_exact_source_cells_and_retains_every_other_cell(self):
        before=a.blob(ROOT,a.BASE,a.ENGINE+'data/layouts/OreburghGate_1F/map.bin')
        after=self.files['data/layouts/OreburghGate_1F/map.bin']
        changed=[i for i,(x,y) in enumerate(zip(struct.iter_unpack('<H',before),struct.iter_unpack('<H',after))) if x!=y]
        self.assertEqual(changed,[20*29+25,21*29+24,21*29+25,21*29+26])
        self.assertEqual(self.gate()['warp_events'][0],json.loads(a.blob(ROOT,a.BASE,a.ENGINE+'data/maps/OreburghGate_1F/map.json'))['warp_events'][0])

    def test_gate_wrong_precondition_and_dimensions_rejected(self):
        before=bytearray(a.blob(ROOT,a.BASE,a.ENGINE+'data/layouts/OreburghGate_1F/map.bin'))
        with self.assertRaises(ValueError):a.open_gate(before[:-1])
        before[2*(20*29+25)]=0
        with self.assertRaises(ValueError):a.open_gate(before)

    def test_complete_warp_cluster_validates(self):a.validate_links(self.receipt['source_headers'],self.gate())

    def test_offset_mutation_rejected(self):
        h=copy.deepcopy(self.receipt['source_headers']);h['Route207']['connections'][0]['offset']=-34
        with self.assertRaisesRegex(ValueError,'offset'):a.validate_links(h,self.gate())

    def test_losing_any_individual_b1_event_rejected(self):
        for i in range(6):
            h=copy.deepcopy(self.receipt['source_headers']);h['OreburghMine_B1F']['warp_events'].pop(i)
            with self.subTest(event=i),self.assertRaises(ValueError):a.validate_links(h,self.gate())

    def test_wrong_sparse_city_return_and_b2_canonical_return_rejected(self):
        for name,i in [('OreburghMine_B1F',0),('OreburghMine_B2F',0)]:
            h=copy.deepcopy(self.receipt['source_headers']);h[name]['warp_events'][i]['dest_warp_id']='3'
            with self.subTest(map=name),self.assertRaises(ValueError):a.validate_links(h,self.gate())

    def test_wrong_city_anchor_and_foreign_museum_target_rejected(self):
        for key,value in [('x',49),('dest_map','MAP_LILYCOVE_CITY_LILYCOVE_MUSEUM_1F')]:
            h=copy.deepcopy(self.receipt['source_headers']);h['OreburghCity']['warp_events'][1][key]=value
            with self.assertRaises(ValueError):a.validate_links(h,self.gate())

    def test_unbuilt_coronet_event_and_gameplay_objects_rejected(self):
        for key,value in [('object_events',[{'local_id':1}]),('warp_events',[dict(x=52,y=5,elevation=0,dest_map='MAP_MT_CORONET_1F_SOUTH',dest_warp_id='0')])]:
            h=copy.deepcopy(self.receipt['source_headers']);h['Route207'][key]=value
            with self.assertRaises(ValueError):a.validate_links(h,self.gate())

    def test_unmatched_edge_closure_changes_only_one_collision_pair(self):
        path=a.SOURCE+'city-family/Route207/map.bin';raw=a.blob(ROOT,a.ART,path)
        out=a.close_unmatched_seam(raw)
        changes=[(i,x[0]^y[0]) for i,(x,y) in enumerate(zip(struct.iter_unpack('<H',raw),struct.iter_unpack('<H',out))) if x!=y]
        self.assertEqual(changes,[(31*64+13,0x400)])
        with self.assertRaises(ValueError):a.close_unmatched_seam(out)

    def test_read_only_shallow_checkout_needs_no_sibling_or_base_git_fetch(self):
        with mock.patch.object(a,'git',side_effect=AssertionError('unexpected history dependency')):
            self.assertEqual((self.files,self.receipt),a.assemble(ROOT))

    def test_tampered_art_cache_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp)/'city-art-inputs.zip').write_bytes(b'changed')
            with mock.patch.object(a,'HERE',Path(temp)),self.assertRaisesRegex(ValueError,'cache changed'):
                a.blob(ROOT,a.ART,a.SOURCE+'city-family/warp-plan.json')

    def test_frozen_candidate_replays_after_production_base_advances(self):
        # A later main may have extra maps. This fixture remains explicitly bound
        # to BASE, not a claim of runtime acceptance on that newer production tree.
        with tempfile.TemporaryDirectory() as temp, mock.patch.object(a,'git',side_effect=AssertionError('unexpected history fetch')):
            self.assertEqual((self.files,self.receipt),a.assemble(temp))

    def test_corrupted_pinned_base_cache_rejected(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as repo:
            folder=Path(temp);(folder/'base-inputs.zip').write_bytes(b'changed')
            (folder/'base-input-hashes.json').write_bytes((a.HERE/'base-input-hashes.json').read_bytes())
            path=next(iter(json.loads((folder/'base-input-hashes.json').read_text())))
            with mock.patch.object(a,'HERE',folder),self.assertRaisesRegex(ValueError,'base cache changed'):
                a.blob(repo,a.BASE,path)

    def test_source_assembly_is_deterministic(self):self.assertEqual((self.files,self.receipt),a.assemble(ROOT))

    def test_install_refuses_unmarked_checkout_before_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            subprocess.check_call(['git','init','-q',temp])
            subprocess.check_call(['git','-C',temp,'symbolic-ref','HEAD','refs/heads/codex/oreburgh-runtime-scratch-test'])
            with self.assertRaisesRegex(ValueError,'marker'):a.install(temp)
            self.assertFalse((Path(temp)/'Pokemon Game').exists())

if __name__=='__main__':unittest.main()
