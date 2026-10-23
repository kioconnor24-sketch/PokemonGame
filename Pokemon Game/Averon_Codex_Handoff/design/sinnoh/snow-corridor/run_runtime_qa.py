#!/usr/bin/env python3
"""Existing height-aware runner over four source-pinned snow DEV maps.

No emulator, converter, save formatter or planner is reimplemented. The reused
runner's internal save label remains coronet-six; this is disclosed test naming,
not a claim this is the Coronet scene. Recipe/hash checks identify actual source.
"""
import argparse
import json
import re
import subprocess
import importlib.util
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('snow_height_qa',HERE.parent/'celestic-north/run_runtime_qa.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
qa.MAPS=('MAP_ROUTE216','MAP_ROUTE217','MAP_ACUITY_LAKEFRONT','MAP_SNOWPOINT_CITY')

def weather_offsets(engine,out):
    """Read-only ABI diagnostics, using the existing emu probe's GCC/nm method."""
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    fields={'current':'offsetof(struct Weather, currWeather)',
            'loaded':'offsetof(struct Weather, weatherGfxLoaded)',
            'count':'offsetof(struct Weather, snowflakeSpriteCount)',
            'target':'offsetof(struct Weather, targetSnowflakeSpriteCount)',
            'snow':'WEATHER_SNOW','expected':'NUM_SNOWFLAKE_SPRITES'}
    src=out/'weather-probe.c';obj=out/'weather-probe.o'
    lines=['#include "global.h"','#include "field_weather.h"',
           '#define P(n,v) asm volatile(".globl SNOWPROBE_" #n "\\n.equ SNOWPROBE_" #n ", %c0" :: "i"(v))',
           'void SnowProbe(void) {']
    lines += ['P('+name+','+expr+');' for name,expr in fields.items()];lines += ['}']
    src.write_text('\n'.join(lines)+'\n')
    subprocess.run(['arm-none-eabi-gcc','-mthumb','-mthumb-interwork','-O2','-mabi=apcs-gnu',
        '-mtune=arm7tdmi','-march=armv4t','-std=gnu17','-iquote','include','-I','tools/agbcc/include',
        '-DMODERN=1','-DTESTING=0','-DEMERALD','-c',str(src),'-o',str(obj)],cwd=engine,check=True)
    values={}
    for line in subprocess.check_output(['arm-none-eabi-nm',str(obj)],text=True).splitlines():
        match=re.fullmatch(r'([0-9a-f]+) A SNOWPROBE_(\w+)',line)
        if match:values[match[2]]=int(match[1],16)
    if set(values)!=set(fields):raise ValueError('incomplete compiler-derived weather probe')
    (out/'weather-offsets.json').write_text(json.dumps(values,indent=2)+'\n');return values


def run(args):
    scripts=HERE.parents[3]/'scripts/claude_play';sys.path.insert(0,str(scripts))
    import map_qa
    offsets=weather_offsets(args.engine,args.scratch/'weather-probe')
    if args.bridge_probe:qa.MAPS=('MAP_ROUTE216',)
    original=map_qa.Runner
    class WeatherRunner(original):
        def check(self,name,ok,**details):
            result=super().check(name,ok,**details)
            if args.bridge_probe and args.expect and name=='follower visible (start)':
                live=self.d.g.live_blocks(96,40)
                source=self.w.map('MAP_ROUTE216').blocks
                differences=None if live is None else [(x,y,hex(live[y*96+x]),hex(source[y*96+x]))
                    for y in range(18,34) for x in (47,48) if live[y*96+x]!=source[y*96+x]]
                super().check('all actual bridge grid cells equal ROM after Continue',
                    live is not None and not differences,differences=differences)
            return result
        def run_map(self,map_id):
            if args.bridge_probe:
                self.check('bridge probe starts on original Route216',self.d.here()[0]==map_id,at=self.d.here())
                for tile in ((47,18),(47,23),(47,25),(47,28),(47,32),(47,28),(47,25),(47,23),(47,18)):
                    ok=self.go(map_id,tile)
                    self.check('upper bridge foot travel '+str(tile),ok,at=self.d.here())
                    z=qa.observed_elevations(self.d)
                    self.check('upper player and follower remain4 '+str(tile),z==dict(player=4,follower=4),elevations=z)
                    if tile==(47,25):
                        live=self.d.live_map(map_id);source=self.w.map(map_id)
                        point=25*live.width+47
                        self.check('live upper bridge cell equals ROM source',live.blocks[point]==source.blocks[point],
                            live=hex(live.blocks[point]),source=hex(source.blocks[point]))
                        self.d.shot('upper-bridge')
                self.check('original stairs reach lower3',self.go(map_id,(46,25)),at=self.d.here())
                self.check('lower approach player3',qa.observed_elevations(self.d)['player']==3)
                for direction,tile in (('right',(47,25)),('right',(48,25)),('right',(49,25)),
                                       ('left',(48,25)),('left',(47,25)),('left',(46,25))):
                    state=qa.ordinary_step(self.d,direction)
                    ok=state is not None and self.d.field_ready(state) and self.d.here(state)==(map_id,tile)
                    self.check('ordinary lower underpass '+str(tile),ok,at=self.d.here())
                    z=qa.observed_elevations(self.d)
                    self.check('lower player and follower remain3 '+str(tile),z==dict(player=3,follower=3),elevations=z)
                    if tile==(47,25):
                        live=self.d.live_map(map_id);source=self.w.map(map_id);point=25*live.width+47
                        self.check('live lower bridge cell equals ROM source',live.blocks[point]==source.blocks[point],
                            live=hex(live.blocks[point]),source=hex(source.blocks[point]))
                        self.d.shot('lower-underpass')
            else:super().run_map(map_id)
            self.d.settle();g=self.d.g;address=g.sym['gWeather']
            observed={name:g.gdb.read(address+offsets[name],1)[0] for name in ('current','loaded','count','target')}
            self.check('actual initialized snow sprites '+map_id,
                observed['current']==offsets['snow'] and observed['loaded']==1
                and observed['count']==observed['target']==offsets['expected'],weather=observed,compiled=offsets)
            self.d.shot('snow-'+map_id)
    map_qa.Runner=WeatherRunner
    try:return qa.run(args)
    finally:map_qa.Runner=original


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('engine','rom','scratch','out','recipe'):p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--profile',required=True,choices=('normal','release'));p.add_argument('--expect',type=Path)
    p.add_argument('--bridge-probe',action='store_true',help='Focused original stairs/upper4/lower3 foot test, same verified ROM')
    sys.exit(run(p.parse_args()))
