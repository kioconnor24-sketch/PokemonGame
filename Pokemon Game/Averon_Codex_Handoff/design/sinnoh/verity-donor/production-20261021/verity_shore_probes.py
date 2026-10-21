"""Run only two previously accepted lake shore probes using unchanged map_qa APIs."""
import json, pathlib, shutil, sys
root=pathlib.Path('/workspace/averon-verity-production/Pokemon Game')
sys.path.insert(0,str(root/'scripts/claude_play'))
import map_qa as qa
engine=root/'engine'; profile=sys.argv[1]; attempt=sys.argv[2] if len(sys.argv)>2 else 'initial'
scratch=pathlib.Path('/workspace/scratch')/('verity-shore-'+profile+'-'+attempt);scratch.mkdir(exist_ok=True)
out=pathlib.Path('/workspace/averon-session-evidence')/('verity-shore-'+profile+'-'+attempt);out.mkdir(exist_ok=True)
source=engine/('pokeemerald-release.gba' if profile=='release' else 'pokeemerald.gba')
rom=scratch/'game.gba';shutil.copyfile(source,rom)
shutil.copyfile(pathlib.Path('/workspace/scratch')/('verity-production-'+profile)/'game.sav',scratch/'game.sav')
w=qa._wrapper(engine)
from codex_cry_gameplay import driver, emu, game, play
info=emu.load_build_info(source.with_suffix('.elf'),engine,scratch/'symbol-cache')
info['symbols']=w.lto_aliases(info['symbols'])
world=qa.mapdata.World(engine);_,plan=qa.static_audit(world,['MAP_LAKE_VERITY'])
e=emu.Emulator(rom,out,audio=False,display=83);g=game.Game(e,info);w.use_source_function_names(g)
d=driver.Driver(e,g,world,out/'events.jsonl');d.moves=game.MoveTable(rom,info);g.map_names=d.w.by_num
r=qa.Runner(d,world,plan,out)
error=None
try:
 play.boot(d,False);r.wait_settled()
 r.blocked('MAP_LAKE_VERITY',42,27,'left')
 r.blocked('MAP_LAKE_VERITY',34,37,'left')
except BaseException as exc:
 error=repr(exc)
finally:
 e.close()
 result=dict(profile=profile,rom_sha256=play.sha256(rom),checks=r.checks,error=error,
  scope='supplementary shore probes only; unchanged Runner.blocked, graphical input/read-only observation')
 result['verdict']='PASS' if error is None and len(r.checks)==2 and all(c['ok'] for c in r.checks) else 'FAIL'
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 print(result['verdict'],sum(c['ok'] for c in r.checks),'/',len(r.checks))
 sys.exit(0 if result['verdict']=='PASS' else 1)
