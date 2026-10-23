#!/usr/bin/env python3
"""Six connected central Sinnoh geography sources, no donor pixels or gameplay.

Reuses the same tested Eterna/Forest stager and original donor converter.
"""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('central_reuse',HERE.parent/'eterna-cycle/stage_batch.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
MAPS={'HearthomeCity': (58, 52, '914b087aaf8a239769200a32cfb01c5e80ec6a41'), 'Route208': (68, 38, 'c334b00d1a9774f588dc6dd9322d4cd0c4cc438c'), 'Route208_Access': (13, 9, 'b195400ca012d0e101f921b37bde3cafd21989dd'), 'Route209': (68, 72, '5593c5475ce0e4c9c252627c19d48bb66dc8a70f'), 'SolaceonTown': (66, 44, '858183919dcf56dac5ec35a49c69e7dfa687ae07'), 'Route210_South': (42, 94, '4175e5b76b52847e79b2223178d2b795f3dbf504'), 'Route209_Access': (13, 9, 'b195400ca012d0e101f921b37bde3cafd21989dd')}


def build(donor,out):return base.build(donor,out,maps=MAPS)


if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--donor',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
 args=p.parse_args();print(json.dumps(build(args.donor,args.out),indent=2))
