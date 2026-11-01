#!/usr/bin/env python3
"""Bulk remaining registered geography through the merged stager/converter."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('remaining_shared_stager',HERE.parent/'eterna-cycle/stage_batch.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)


DUPLICATED_ROUTE221=[{'map':'MAP_ROUTE220','offset':4,'direction':'left'}]*2


def corrected_headers(headers):
    result=copy.deepcopy(headers)
    if 'Route221' in result:
        if result['Route221'].get('connections')!=DUPLICATED_ROUTE221:
            raise ValueError('pinned duplicate Route221 connection changed')
        result['Route221']['connections']=copy.deepcopy(DUPLICATED_ROUTE221[:1])
    return result


def build(donor,out,selection=None):
    selection=json.loads((HERE/'selection.json').read_text()) if selection is None else selection
    if selection['donor_revision']!=base.REVISION:
        raise ValueError('wrong source selection revision')
    maps={x['name']:(*x['dimensions'],x['map_blob']) for x in selection['maps']}
    if len(maps)!=len(selection['maps']) or not maps:
        raise ValueError('duplicate or empty source selection')
    # No geometry conversion/sanitization implementation here: same tested
    # fixed-point closure, converter and full attribute recording as prior batches.
    sanitize=base.sanitize
    def checked(headers,layouts,raws):
        return sanitize(corrected_headers(headers),layouts,raws)
    base.sanitize=checked
    try:
        receipt=base.build(donor,out,maps=maps,border_overrides=selection.get('border_repairs',{}))
    finally:
        base.sanitize=sanitize
    if 'Route221' in maps:
        receipt['neutral_header_corrections']=[dict(map='Route221',field='connections',
            before=DUPLICATED_ROUTE221,after=DUPLICATED_ROUTE221[:1],
            reason='Remove exact duplicate; source Route220 has one reciprocal right offset -4')]
    receipt['limits'] += ['Bulk source-only staging, not art/ROM/runtime/production acceptance',
        'Closed external connections/doors remain unbuilt; no lost map omitted from selection silently']
    (Path(out)/'source-receipt.json').write_bytes(base.encode(receipt))
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--donor',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    args=p.parse_args();r=build(args.donor,args.out)
    print(json.dumps({'maps':len(r['maps']),'status':r['status']},indent=2))
