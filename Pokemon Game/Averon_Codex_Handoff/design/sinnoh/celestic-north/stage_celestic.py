#!/usr/bin/env python3
"""Six connected Celestic/northern ridge/cave sources, no donor pixels/gameplay."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('celestic_reused_stager',HERE.parent/'eterna-cycle/stage_batch.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
MAPS={
    'Route210_North':(99,29,'60d9586757efe560c5808418d05c4c91e53ea258'),
    'CelesticTown':(38,35,'510a7a21efed727805bb7db13f5cbca5c34e7dd3'),
    'Route211_East':(32,32,'fe18fa5a0c1bceff72658bbde3414361ac503382'),
    'MtCoronet_1F_North_Room1':(36,51,'077741fab7d11819896b5a49a7c3b12d311e0f5d'),
    'MtCoronet_1F_North_Room2':(19,16,'f2c39cf2d36185beb1bec3caec4a79fe2a96382a'),
    'MtCoronet_B1F':(32,65,'33dea8eb454992463d78b2f90692ba2993bbbe78'),
}


def build(donor,out):return base.build(donor,out,maps=MAPS)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--donor',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.donor,args.out),indent=2))
