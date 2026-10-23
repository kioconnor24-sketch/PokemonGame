#!/usr/bin/env python3
"""Use the merged neutral gateway packer for the actual Route218 anchor sets."""
import argparse
import importlib.util
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('canalave_gate_reuse',HERE.parent/'hearthome-solaceon/adapt_gate_art.py')
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
MAPS={'Route218_East':(13,9),'Route218_West':(13,9)}
ANCHORS={'Route218_East':[(1,5)],'Route218_West':[(11,5),(1,5)]}


def build(engine,out):
    return shared.build(engine,out,source_root=HERE,maps=MAPS,expected_anchors=ANCHORS)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.engine,args.out),indent=2))
