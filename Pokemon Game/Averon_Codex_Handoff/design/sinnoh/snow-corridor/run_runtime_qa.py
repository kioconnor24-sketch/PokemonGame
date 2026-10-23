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
    offsets=weather_offsets(args.engine,args.out/'weather-probe')
    original=map_qa.Runner
    class WeatherRunner(original):
        def run_map(self,map_id):
            super().run_map(map_id)
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
    sys.exit(run(p.parse_args()))
