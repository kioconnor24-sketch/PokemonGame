"""Bounded existing-scene controller checks; no memory writes, source edits, or full-world acceptance."""
import sys,json,pathlib,hashlib,shutil,time,argparse
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[4]
for name in ('coordination','claude_play'):
 sys.path.insert(0,str(ROOT/'Pokemon Game/scripts'/name))
import codex_cry_gameplay as w
import map_qa as q
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--engine',type=pathlib.Path,required=True)
parser.add_argument('--scratch',type=pathlib.Path,required=True)
parser.add_argument('--out',type=pathlib.Path,required=True)
parser.add_argument('--receipt',type=pathlib.Path,required=True)
parser.add_argument('--profile',choices=('normal','release'),required=True)
args=parser.parse_args()
profile=args.profile;engine=args.engine.resolve();scratch=args.scratch.resolve();out=args.out.resolve()
if not (engine/'.map_qa_throwaway').is_file():raise SystemExit('marked disposable scene required')
if out.exists() or out.is_relative_to(engine) or scratch.is_relative_to(engine):
 raise SystemExit('new external evidence output and external scratch required')
if not (scratch/'game.sav').is_file():raise SystemExit('provide a source-qualified private fixture flash first')
out.mkdir(parents=True)
rom_source=engine/('pokeemerald-cries-off'+('-release' if profile=='release' else '')+'.gba')
rom=scratch/'game.gba';shutil.copyfile(rom_source,rom);flash=rom.with_suffix('.sav')
recipe=json.loads(args.receipt.read_text())
if len(recipe['existing_map_names_preserved'])!=22 or len(recipe['scene'])!=44:raise SystemExit('exact22+44 scene receipt required')
for n,h in recipe['files'].items():assert hashlib.sha256((engine/n).read_bytes()).hexdigest()==h,n
result={'scope':'Bounded real controller FightArea/Gate/Campus; not full44-map acceptance','source_sha':recipe['source_sha'],'base':recipe['base'],'profile':profile,'rom_sha256':w.play.sha256(rom),'dev_entry':'existing Continue-warp fixture on fresh private original-legacy copy; no old19-slot DEV flash reused','host_probe_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'checks':[]}
fight='MAP_FIGHT_AREA';gate='MAP_SINNOH_FRONTIER_GATE';center='MAP_SINNOH_FRONTIER_CAMPUSCENTER'
def require(ok,label):
 if not ok:raise AssertionError(label)
def travel(mid):
 d.travel_to(mid);r.wait_settled();require(r.check('ordinary route reaches '+mid,d.here()[0]==mid,at=d.here()),mid);r.follower('arrival '+mid)
def warp(mid,index):
 p=next(p for p in q.map_points(world.map(mid)) if p['kind']=='warp' and p['index']==index)
 require(r.warp(mid,p),'warp '+mid)
e=None;r=None
try:
 info=w.emu.load_build_info(rom_source.with_suffix('.elf'),engine,scratch/'symbol-cache')
 info['symbols']=w.lto_aliases(info['symbols'])
 sizes=w.chunk_sizes(*w.save_struct_sizes(engine,scratch/'save-sizes','off',release=profile=='release'))
 e=w.emu.Emulator(rom,out,audio=False)
 g=w.game.Game(e,info);w.use_source_function_names(g)
 world=w.mapdata.World(engine);d=w.driver.Driver(e,g,world,out/'events.jsonl')
 d.moves=w.game.MoveTable(rom,info);g.map_names=world.by_num
 r=q.Runner(d,world,{},out)
 w.play.boot(d,False);r.wait_settled()
 require(r.check('new66-slot fixture starts FightArea',d.here()==(fight,(23,5)),at=d.here()),'initial arrival')
 r.follower('start')
 warp(fight,0)
 travel(gate);warp(gate,0)
 travel(center)
 m=world.map(center);entry=q.warp_arrive(m,*m.warps[2][:2])
 reachable=q.reach(m,[entry]) & q.reach(m,[entry],reverse=True)
 for direction in ['left','right']:
  p=next(p for p in q.map_points(m) if p['kind']=='connection' and p['direction']==direction and tuple(p['tile']) in reachable and world.map(p['dest']).walkable(*q.across(m,world.map(p['dest']),direction,p['offset'],p['tile'])) and w.mapdata.crossable(m,p['tile'],world.map(p['dest']),q.across(m,world.map(p['dest']),direction,p['offset'],p['tile'])))
  require(r.go(center,p['tile']),'reach valid seam')
  target=q.across(m,world.map(p['dest']),direction,p['offset'],p['tile'])
  d.step(direction);there=r.wait_settled();d.shot('campus-'+direction+'-arrival')
  require(r.check('actual '+direction+' campus crossing',there==(p['dest'],target),at=there),direction)
  require(r.follower('inside '+p['dest']),'follower inside')
  d.step(q.OPPOSITE[direction]);back=r.wait_settled()
  require(r.check('actual '+direction+' campus reciprocal return',back==(center,tuple(p['tile'])),at=back),direction+' return')
  require(r.follower('center after '+direction),'follower return')
 blocked=0
 for p in q.map_points(m):
  if p['kind']!='connection' or tuple(p['tile']) not in reachable:continue
  other=world.map(p['dest']);to=q.across(m,other,p['direction'],p['offset'],p['tile'])
  if other.inside(*to) and other.walkable(*to) and w.mapdata.crossable(m,p['tile'],other,to):continue
  require(r.blocked(center,*p['tile'],p['direction']),'expected source border did not block');blocked+=1
 require(r.check('all6 reachable blocked center faces exercised',blocked==6,count=blocked),'blocked face count')
 travel(gate);require(r.go(gate,(7,19)),'return save position')
 d.settle();time.sleep(.5)
 before=d.here();e.tap('START',after=1.0)
 tasks=w.active_tasks(g);count=g.gdb.read(g.sym['sNumStartMenuActions'],1)[0];cursor=g.gdb.read(g.sym['sStartMenuCursorPos'],1)[0]
 d.shot('actual-native-menu')
 require(r.check('actual native menu task and valid cursor',bool(set(tasks)&{'StartMenuTask','Task_ShowStartMenu'}) and 0<count<=9 and cursor<count,tasks=tasks,actions=count,cursor=cursor),'native menu')
 e.tap('B',after=.8);r.wait_settled()
 require(r.check('B returns to same field',d.here()==before and d.field_ready(d.state()),at=d.here()),'menu return')
 w.release_save(d,'frontier66-'+profile,sizes,flash)
 require(r.check('game-written SAVE after campus return',True,at=d.here()),'save')
except BaseException as exc:
 result['error']=repr(exc)
 if r is not None:r.check('bounded run completed',False,error=repr(exc))
finally:
 if e is not None:e.close()
 result['checks']=r.checks if r is not None else []
 result['verdict']='PASS' if result['checks'] and all(x['ok'] for x in result['checks']) and not result.get('error') else 'FAIL'
 saves=list(out.glob('saved-*.json'))
 if saves:
  result['flash_problems']=w.flash_verdict(json.loads(saves[0].read_text())['flash_before'],w.flash_slots(w.read_flash(flash),sizes),1)
  if result['flash_problems']:result['verdict']='FAIL'
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(profile,result['verdict'],sum(x['ok'] for x in result['checks']),len(result['checks']),flush=True)
if result['verdict']!='PASS':raise SystemExit(1)
