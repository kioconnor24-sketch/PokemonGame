#!/usr/bin/env python3
"""Pinned westward geography; existing converter/stager, no donor pixels/gameplay."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('canalave_shared_stager',HERE.parent/'eterna-cycle/stage_batch.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
MAPS={
    'Route218_East':(13,9,'b195400ca012d0e101f921b37bde3cafd21989dd'),
    'Route218':(64,32,'51b70abe19c57b3d60d79ef2064c8dadb9d70f60'),
    'Route218_West':(13,9,'feab6a93f800e642ee42c0c229b4db7302835a6f'),
    'CanalaveCity':(38,64,'bc3131fae6aa9a366de8e910c2293b177460a1a5'),
}
BAD={'x':59,'y':24,'elevation':0,'dest_map':'MAP_ROUTE211_EAST','dest_warp_id':'1'}
GOOD={**BAD,'dest_map':'MAP_ROUTE218_EAST'}
RETURN={'x':1,'y':5,'elevation':0,'dest_map':'MAP_ROUTE218','dest_warp_id':'0'}


def corrected_headers(headers):
    """Source return proves a mistyped map name, not a new geography decision.

    Fail closed if either pinned endpoint changes; never mutate donor/inputs or
    silently reinterpret a later donor revision. Original source is receipted.
    """
    if headers['Route218']['warp_events'][0]!=BAD or headers['Route218_East']['warp_events'][1]!=RETURN:
        raise ValueError('pinned Route218 east portal correction no longer applies')
    result=copy.deepcopy(headers)
    result['Route218']['warp_events'][0]=copy.deepcopy(GOOD)
    return result


def build(donor,out):
    sanitize=base.sanitize
    def with_verified_portal(headers,layouts,raws):
        return sanitize(corrected_headers(headers),layouts,raws)
    base.sanitize=with_verified_portal
    try:receipt=base.build(donor,out,maps=MAPS)
    finally:base.sanitize=sanitize
    receipt['neutral_header_corrections']=[dict(map='Route218',original_warp_index=0,
        before=BAD,after=GOOD,reciprocal_source_map='Route218_East',reciprocal_source_warp_index=1,
        reason='Original source return targets Route218/0; original outward map name instead targets unrelated Route211East')]
    receipt['limits'] += ['Route218 water is preserved; no Surf grant, unlock or ordinary foot through-route acceptance',
        'Jubilife exit is closed until a separately verified integration; ferry/transfer/gameplay content excluded',
        'Donor metatile identities/attributes only; Pasos/Jubilife/Canalave artwork is NOT distributed or verified as Averon art']
    (Path(out)/'source-receipt.json').write_bytes(base.encode(receipt))
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--donor',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.donor,args.out),indent=2))
