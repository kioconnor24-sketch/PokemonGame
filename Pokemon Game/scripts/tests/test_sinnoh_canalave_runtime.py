"""Four-map Canalave disposable integration, immutable source and installation guards."""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/canalave-west'
spec=importlib.util.spec_from_file_location('canalave_runtime',HERE/'prepare_runtime.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)


class CanalaveRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.files,cls.receipt=runtime.assemble(ROOT)

    def test_original_nineteen_slots_preserved_and_four_appended_without_saved_ids(self):
        original=json.loads((ROOT/runtime.ENGINE/'data/maps/map_groups.json').read_text())
        groups=json.loads(self.files['data/maps/map_groups.json'])
        self.assertEqual(original['gMapGroup_Sinnoh'],groups['gMapGroup_Sinnoh'][:19])
        self.assertEqual(23,len(groups['gMapGroup_Sinnoh']))
        self.assertEqual(list(runtime.MAPS),groups['gMapGroup_Sinnoh'][19:])
        self.assertEqual([19,20,21,22],list(self.receipt['temporary_map_slots'].values()))
        self.assertFalse(any('region_map_sections' in path or 'pokemon' in path for path in self.files))

    def test_no_primary_copy_no_global_graphics_and_exact_original_map_inputs(self):
        self.assertEqual(28,len(self.files))
        self.assertEqual(4,len([p for p in self.files if p.startswith('data/tilesets/')]))
        self.assertFalse(any(p.endswith(('.png','.pal','.sav','.gba')) for p in self.files))
        layouts=json.loads(self.files['data/layouts/layouts.json'])['layouts']
        for name in runtime.MAPS:
            layout=next(l for l in layouts if l['name']==name+'_Layout')
            self.assertEqual('gTileset_Building' if name.endswith(('_East','_West')) else 'gTileset_General',layout['primary_tileset'])
            self.assertEqual('gTileset_CanalaveDevGateSecondary' if name.endswith(('_East','_West')) else 'gTileset_CanalaveDevOutdoorSecondary',layout['secondary_tileset'])
            self.assertEqual((HERE/'staged'/name/'averon-map.bin').read_bytes(),self.files['data/layouts/'+name+'/map.bin'])
            source=json.loads((HERE/'staged'/name/'map.json').read_text())
            installed=json.loads(self.files['data/maps/'+name+'/map.json'])
            source['region_map_section']='MAPSEC_ROUTE_201'
            self.assertEqual(source,installed)

    def test_recipe_matches_every_payload_and_old_donor_doors_stay_closed(self):
        self.assertEqual(runtime.BASE,self.receipt['base'])
        for path,raw in self.files.items():self.assertEqual(hashlib.sha256(raw).hexdigest(),self.receipt['files'][path])
        for name in runtime.MAPS:
            header=json.loads(self.files['data/maps/'+name+'/map.json'])
            self.assertEqual({'Route218_East':1,'Route218':2,'Route218_West':2,'CanalaveCity':1}[name],len(header['warp_events']))
            self.assertEqual(self.receipt['source_headers'][name]['connections'],header['connections'])
            self.assertTrue(all(not header[k] for k in ('object_events','coord_events','bg_events')))

    def test_production_checkout_refused_and_exact_dirty_inputs_rejected(self):
        with self.assertRaisesRegex(ValueError,'disposable Canalave branch'):runtime.install(ROOT)
        baseline=runtime.inputs(ROOT)
        corrupted=dict(baseline)
        first=next(iter(corrupted));corrupted[first]+=b'changed'
        def altered(repo,path,revision):
            return corrupted[str(path).removeprefix(runtime.ENGINE)]
        with patch.object(runtime.base,'verified_file',side_effect=altered):
            with self.assertRaisesRegex(ValueError,'baseline inputs differ'):runtime.inputs(ROOT)

    def test_wrong_base_and_escape_refused_before_any_output(self):
        with tempfile.TemporaryDirectory() as temp:
            repo=Path(temp);engine=repo/runtime.ENGINE;engine.mkdir(parents=True);(engine/'.map_qa_throwaway').touch()
            def git_wrong(repo,*args):
                if args[0]=='branch':return b'codex/canalave-runtime-scratch-fixture\n'
                return b'0'*40+b'\n'
            with patch.object(runtime.base,'git',side_effect=git_wrong):
                with self.assertRaisesRegex(ValueError,'exact production baseline'):runtime.install(repo)
            def git_clean(repo,*args):
                if args[0]=='branch':return b'codex/canalave-runtime-scratch-fixture\n'
                if args[0]=='rev-parse':return (runtime.BASE+'\n').encode()
                return b''
            with patch.object(runtime.base,'git',side_effect=git_clean),patch.object(runtime,'assemble',return_value=({'../escape':b'x'},{})):
                with self.assertRaisesRegex(ValueError,'escapes engine'):runtime.install(repo)
            self.assertEqual(['.map_qa_throwaway'],[p.name for p in engine.iterdir()])


    def test_qa_wrapper_binds_the_source_driver_and_records_foot_flags_without_writes(self):
        code=r"""
import importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
engine=Path(sys.argv[1]);path=Path(sys.argv[2])
spec=importlib.util.spec_from_file_location('qa_wrapper_probe',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
original_maps=m.shared.MAPS
# The production source-identity check used by shared.run must stay intact.
def fake_run(args):
 import driver,map_qa as qa
 wrapper=qa._wrapper(args.engine)
 assert wrapper.driver is driver
 assert Path(driver.__file__).resolve()==engine.parent/'scripts/claude_play/driver.py'
 for flags,expected in [(1,True),(9,False),(0,False)]:
  g=SimpleNamespace(sym={'gPlayerAvatar':100},off={'avatar.flags':2},c={'PLAYER_AVATAR_FLAG_SURFING':8,'PLAYER_AVATAR_FLAG_ON_FOOT':1})
  def read(addr,size):
   assert addr==102 and size==1
   return bytes([flags])
  g.gdb=SimpleNamespace(read=read)
  d=SimpleNamespace(g=g,log=lambda *a,**kw:None)
  runner=qa.Runner(d,None,None,None)
  assert runner.check('follower visible (probe)',True) is expected
  assert len(runner.checks)==2
  assert runner.checks[-1]['avatar_flags']==flags
 return 0
m.shared.run=fake_run
assert m.run(SimpleNamespace(engine=engine))==0
assert m.shared.MAPS==original_maps
"""
        result=subprocess.run([sys.executable,'-c',code,str(ROOT/'Pokemon Game/engine'),str(HERE/'run_runtime_qa.py')],capture_output=True,text=True)
        self.assertEqual(0,result.returncode,result.stdout+result.stderr)


if __name__=='__main__':unittest.main()
