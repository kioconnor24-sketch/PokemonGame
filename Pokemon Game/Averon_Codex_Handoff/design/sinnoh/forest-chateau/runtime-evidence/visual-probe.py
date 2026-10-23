#!/usr/bin/env python3
"""Read-only same-camera frame-settling diagnostic, NOT gameplay acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
from PIL import Image

p=argparse.ArgumentParser(description=__doc__)
for n in ('engine','qa-source','recipe','rom','scratch','out'):p.add_argument('--'+n,required=True,type=Path)
p.add_argument('--profile',required=True,choices=('normal','release'));a=p.parse_args()
engine=a.engine.resolve();r=json.loads(a.recipe.read_text())
assert r['status']=='DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE' and (engine/'.map_qa_throwaway').is_file()
for path,h in r['files'].items():
    f=(engine/path).resolve();assert f.is_relative_to(engine) and hashlib.sha256(f.read_bytes()).hexdigest()==h
sys.path.insert(0,str(a.qa_source.resolve()))
import driver,emu,game,mapdata,run
import map_qa
w=map_qa._wrapper(engine);assert w.driver is driver and Path(driver.__file__).resolve()==a.qa_source.resolve()/'driver.py'
a.out.mkdir(parents=True,exist_ok=False);rom=a.scratch/'game.gba';shutil.copyfile(a.rom,rom)
info=emu.load_build_info(a.rom.with_suffix('.elf'),engine,a.scratch/'symbol-cache');info['symbols']=w.lto_aliases(info['symbols'])
e=emu.Emulator(rom,a.out,audio=False);g=game.Game(e,info);w.use_source_function_names(g)
d=driver.Driver(e,g,mapdata.World(engine),a.out/'events.jsonl');d.moves=game.MoveTable(rom,info)
rows=[]
try:
    run.boot(d,False);d.settle()
    for label,delay in [('immediate',0),('settled',3)]:
        time.sleep(delay);f=d.shot('entrance-'+label)
        with Image.open(f) as image:
            count=sum(r>220 and g<50 and b>220 for r,g,b in image.convert('RGB').getdata())
        rows.append(dict(label=label,delay_seconds=delay,at=d.here(),magenta_pixels=count,image=f.name))
finally:e.close()
result=dict(status='VISUAL_PROBE_OBSERVATION_NOT_GAMEPLAY_ACCEPTANCE',profile=a.profile,
    rom_sha256=hashlib.sha256(a.rom.read_bytes()).hexdigest(),driver_sha256=hashlib.sha256(Path(driver.__file__).read_bytes()).hexdigest(),
    baseline=r['base'],observations=rows,dev_entry=True)
(a.out/'visual-probe.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
