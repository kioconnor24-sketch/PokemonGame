#!/usr/bin/env python3
"""Twelve source-verified eastern/southern geography maps, no donor art/gameplay.

Reuses the accepted cluster stager and original donor converter unchanged.
"""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('eastern_reuse',HERE.parent/'eterna-cycle/stage_batch.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
MAPS={'Route212_Access': (9, 11, '38af8d53086c00edfee9778c2b17a9d5a12c1872'), 'Route212_North': (34, 100, '95da4bb2ec84b4d54a42e346871c229727d6f5b8'), 'Route212_South': (130, 34, '32c3fabe6f2af6fc5a7577081934de489486a39c'), 'Route213': (100, 60, 'a8e56eafb005d94cbe3248a56a6e18763e460b97'), 'Route213_Access': (13, 9, 'b195400ca012d0e101f921b37bde3cafd21989dd'), 'Route214': (44, 91, 'cb6faa3d4729bef5a43775dee3acb03e1ca148c2'), 'Route214_Access': (9, 11, '38af8d53086c00edfee9778c2b17a9d5a12c1872'), 'Route215': (100, 42, '9986f98b26c78b38ec4628c9c4230783756730bb'), 'Route215_Access': (13, 9, 'feab6a93f800e642ee42c0c229b4db7302835a6f'), 'ValorLakefront': (56, 66, '972daf04538e3ef85fba0c8784e943179491c890'), 'VeilstoneCity': (66, 68, 'cf156106b37670e558c401dcf577a599f3a6059f'), 'PastoriaCity': (68, 60, '2daf5ede287de06223c1ff2063e4dfd885eda450')}


def build(donor,out):return base.build(donor,out,maps=MAPS)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--donor',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.donor,args.out),indent=2))
