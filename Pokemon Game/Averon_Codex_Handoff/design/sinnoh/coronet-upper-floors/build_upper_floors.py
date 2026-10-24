#!/usr/bin/env python3
"""Extend the existing original-room authoring config; summit remains closed."""
import argparse
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('upper_floors_existing_ascent',HERE.parent/'coronet-ascent/build_ascent.py')
a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
NAMES=dict(a.NAMES,**{'5f':'SinnohMtCoronet_5F','6f':'SinnohMtCoronet_6F','1f_tunnel_room':'SinnohMtCoronet_1F_Tunnel_Room'})
IDS={n:'MAP_SINNOH_MT_CORONET_'+k.upper() for k,n in NAMES.items()}
def build(repo,inputs,out):
    a.NAMES=NAMES;a.IDS=IDS
    return a.build(repo,inputs,out)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('repo','inputs','out'):p.add_argument('--'+n,required=True,type=Path)
    args=p.parse_args();build(args.repo,args.inputs,args.out)
