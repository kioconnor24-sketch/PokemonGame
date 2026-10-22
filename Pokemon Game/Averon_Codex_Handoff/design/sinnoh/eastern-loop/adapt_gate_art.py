#!/usr/bin/env python3
"""Reuse the existing neutral gate packer for four source-pinned eastern gates."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('eastern_gate_reuse',HERE.parent/'hearthome-solaceon/adapt_gate_art.py')
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
MAPS={'Route212_Access':(9,11),'Route213_Access':(13,9),'Route214_Access':(9,11),'Route215_Access':(13,9)}
ANCHORS={'Route212_Access':[(4,9)],'Route213_Access':[(11,5),(1,5)],
         'Route214_Access':[(4,1),(4,9)],'Route215_Access':[(11,5),(1,5)]}


def build(engine,out):
    return shared.build(engine,out,source_root=HERE,maps=MAPS,expected_anchors=ANCHORS)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.engine,args.out),indent=2))
