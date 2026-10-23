#!/usr/bin/env python3
"""Disclosed Acro DEV grant + real Bag/input rail probe; never memory writes."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('eastern_common_qa',HERE/'run_runtime_qa.py')
common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common)


def validate_recipe(engine,receipt):
    grant=receipt.get('dev_fixture',{})
    if grant.get('item_grants')!=['ITEM_ACRO_BIKE'] or grant.get('flag_grants')!=[] or grant.get('map')!='Route212_South':
        raise ValueError('explicit single-Acro DEV fixture recipe required')
    common.validate_source(engine,receipt)


def bike_use(d,play):
    """Select the actual encrypted-bag Acro entry through the normal menu."""
    g=d.g;gd=g.gdb;keys=[i for i,q in g.bag_pocket('bag.keyItems','BAG_KEYITEMS_COUNT') if i and q]
    item=g.c['ITEM_ACRO_BIKE']
    if item not in keys:raise ValueError('declared DEV item grant absent')
    play.open_start_menu_action(d,2)
    pos=g.sym['gBagPosition'];pocket=g.c['POCKET_KEY_ITEMS']
    for _ in range(6):
        if gd.read(pos+g.off['bagpos.pocket'],1)[0]==pocket:break
        d.e.tap('RIGHT',after=.8)
    else:raise ValueError('Key Items pocket not reached')
    index=keys.index(item)
    for _ in range(50):
        cur=struct.unpack('<H',gd.read(pos+g.off['bagpos.cursor']+2*pocket,2))[0]
        scroll=struct.unpack('<H',gd.read(pos+g.off['bagpos.scroll']+2*pocket,2))[0]
        if cur+scroll==index:break
        d.e.tap('DOWN' if cur+scroll<index else 'UP',after=.25)
    else:raise ValueError('Acro bag cursor did not reach the item')
    d.shot('acro-key-item');d.e.tap('A',after=.7);d.e.tap('A',after=1)
    play.back_to_field(d);d.settle()


def avatar(d):
    g=d.g;a=g.sym['gPlayerAvatar'];index=g.gdb.read(a+g.off['avatar.objectEventId'],1)[0]
    raw=g.gdb.read(g.sym['gObjectEvents']+index*g.off['oe.size'],g.off['oe.size'])
    return dict(flags=g.gdb.read(a+g.off['avatar.flags'],1)[0],facing=raw[g.off['oe.directionByte']]&15,
                acro_state=g.gdb.read(a+g.off['avatar.acroState'],1)[0],elevations=common.observed_elevations(d))


def sidehop(d,direction):
    """Normal Acro sideways jump: B and perpendicular direction together."""
    key=direction.upper();before=d.here();d.log('acro-sidehop-start',direction=direction,at=before,avatar=avatar(d))
    # One X event batch: separate read-traced calls let B become a standing
    # wheelie before the perpendicular input reaches the native 4-frame window.
    from emu import KEYS
    chord=[KEYS[key],KEYS['B']]
    def send(down):
        if getattr(d.e,'trace',None):
            d.e.trace.write(json.dumps(dict(kind='controller-chord',frame=d.e.frame(),keys=[key,'B'],down=down))+'\n');d.e.trace.flush()
        subprocess.run(['xdotool','keydown' if down else 'keyup','--window',d.e.window,*chord],env=d.e.env,check=True)
    try:send(True);time.sleep(.12)
    finally:send(False)
    time.sleep(.6);d.settle();d.log('acro-sidehop-end',at=d.here(),avatar=avatar(d));return d.here()


def run(args):
    engine=args.engine.resolve();receipt=json.loads(args.recipe.read_text());validate_recipe(engine,receipt)
    scripts=HERE.parents[3]/'scripts/claude_play';sys.path.insert(0,str(scripts))
    import map_qa as qa
    w=qa._wrapper(engine);driver,emu,game,play=w.driver,w.emu,w.game,w.play
    emu.OFFSET_EXPRS.update({'bag.keyItems':'offsetof(struct Bag, keyItems)',
        'avatar.flags':'offsetof(struct PlayerAvatar, flags)',
        'avatar.acroState':'offsetof(struct PlayerAvatar, acroBikeState)',
        'avatar.objectEventId':'offsetof(struct PlayerAvatar, objectEventId)',
        'oe.elevationByte':'offsetof(struct ObjectEvent, initialCoords) - 1',
        'oe.directionByte':'offsetof(struct ObjectEvent, range) - 1'})
    for c in ('ITEM_ACRO_BIKE','PLAYER_AVATAR_FLAG_ACRO_BIKE','DIR_EAST'):
        if c not in emu.CONSTANTS:emu.CONSTANTS.append(c)
    if args.out.exists() and any(args.out.iterdir()):raise ValueError('new evidence output required')
    args.out.mkdir(parents=True,exist_ok=True);args.scratch.mkdir(parents=True,exist_ok=True)
    rom=args.scratch/'game.gba';shutil.copyfile(args.rom,rom);flash=rom.with_suffix('.sav')
    info=emu.load_build_info(args.rom.with_suffix('.elf'),engine,args.scratch/'symbol-cache');info['symbols']=w.lto_aliases(info['symbols'])
    world=qa.mapdata.World(engine);e=emu.Emulator(rom,args.out,audio=False);g=game.Game(e,info);w.use_source_function_names(g)
    d=driver.Driver(e,g,world,args.out/'events.jsonl');g.map_names=d.w.by_num;checks=[]
    result=dict(status='DECLARED_ACRO_DEV_FIXTURE_NOT_PRODUCTION_OR_NATURAL_TRAVEL',profile=args.profile,rom_sha256=play.sha256(rom),probe_sha256=play.sha256(Path(__file__)),checks=checks)
    def check(name,ok,**detail):
        checks.append(dict(name=name,ok=bool(ok),**detail));d.log('rail-check',**checks[-1])
        if not ok:raise ValueError(name)
    try:
        e.start_trace(args.out/'inputs.jsonl',g.sym['gMain']+g.off['main.vblankCounter1'])
        play.boot(d,False);d.settle()
        check('explicit Acro grant quantity exactly one',dict(g.bag_pocket('bag.keyItems','BAG_KEYITEMS_COUNT')).get(g.c['ITEM_ACRO_BIKE'])==1)
        if args.expect:
            w.check_continue(d,args.expect);check('fresh-process Continue restores actual saved state',True,at=d.here())
        else:
            check('starts at exact source-grounded rail approach',d.here()==('MAP_ROUTE212_SOUTH',(36,12)),at=d.here())
            check('ordinary foot input is blocked by the original rail',d.step('up') is None and d.here()==('MAP_ROUTE212_SOUTH',(36,12)),at=d.here())
            bike_use(d,play);check('ordinary Bag USE mounted Acro',avatar(d)['flags']&g.c['PLAYER_AVATAR_FLAG_ACRO_BIKE'],avatar=avatar(d))
            d.e.tap('RIGHT',hold=.025,after=.4);d.settle()
            check('turn-only preserves exact approach position',d.here()==('MAP_ROUTE212_SOUTH',(36,12)),at=d.here(),avatar=avatar(d))
            check('faces along horizontal rail for sideways hop',avatar(d)['facing']==g.c['DIR_EAST'],avatar=avatar(d))
            check('real sideways hop enters unchanged rail',sidehop(d,'up')==('MAP_ROUTE212_SOUTH',(36,11)),avatar=avatar(d));d.shot('acro-on-source-rail')
            check('real sideways hop exits rail onto northern ground',sidehop(d,'up')==('MAP_ROUTE212_SOUTH',(36,10)),avatar=avatar(d))
            check('return hop reenters same rail',sidehop(d,'down')==('MAP_ROUTE212_SOUTH',(36,11)),avatar=avatar(d))
            check('return hop restores original approach',sidehop(d,'down')==('MAP_ROUTE212_SOUTH',(36,12)),avatar=avatar(d))
            bike_use(d,play);check('ordinary Bag USE dismounts',not avatar(d)['flags']&g.c['PLAYER_AVATAR_FLAG_ACRO_BIKE'],avatar=avatar(d))
            common.ordinary_step(d,'right');common.ordinary_step(d,'left')
            observation=play.observe(d,'follower-after-acro');f=observation.get('follower') or {}
            check('follower visible again after ordinary dismount and foot steps',bool(f) and not f.get('invisible'),follower=f)
            sizes=w.chunk_sizes(*w.save_struct_sizes(engine,args.scratch/'save-sizes','off',release=args.profile=='release'))
            w.release_save(d,'acro-rail',sizes,flash);check('actual Save dialog succeeded',True)
        result['verdict']='PASS'
    except BaseException as exc:
        result['verdict']='FAIL';result['error']=repr(exc);d.log('rail-failure',error=repr(exc));d.shot('rail-failure')
    finally:
        e.close();(args.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['verdict'],sum(c['ok'] for c in checks),'/',len(checks));return 0 if result['verdict']=='PASS' else 1


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('engine','rom','scratch','out','recipe'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--profile',required=True,choices=('normal','release'));p.add_argument('--expect',type=Path)
    sys.exit(run(p.parse_args()))
