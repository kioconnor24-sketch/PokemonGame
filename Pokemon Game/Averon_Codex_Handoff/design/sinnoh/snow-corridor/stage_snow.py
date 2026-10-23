#!/usr/bin/env python3
"""Four pinned snow-corridor maps; shared converter/stager, no donor artwork."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('snow_shared_stager',HERE.parent/'eterna-cycle/stage_batch.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
MAPS={
    'Route216':(96,40,'788e5d6785cc907b4ab478329f847e13e40d512d'),
    'Route217':(36,118,'9efd12cc02dea4dda9011a73b8555c87c00abe19'),
    'AcuityLakefront':(64,66,'276a4ad14b467abdf1d951ae17a8399d052463b0'),
    'SnowpointCity':(34,68,'1cf26ec961e985f067c9004375c44318d6aaad03'),
}


def preserve_source_weather(donor,out,receipt):
    """Shared neutral default is insufficient for the actual snow visibility.

    Re-read only already receipted header blobs. Hash and value checks prevent
    unverified weather tokens from entering staged headers. No weather engine
    or graphics change is made; actual visibility testing is a later gate.
    """
    changed={}
    for name in MAPS:
        path='data/maps/'+name+'/map.json'
        raw=subprocess.check_output(['git','-C',str(donor),'show',base.REVISION+':'+path])
        if base.sha(raw)!=receipt['donor_sha256'][path]:raise ValueError('source weather header changed')
        weather=json.loads(raw)['weather']
        if weather!='WEATHER_SNOW':raise ValueError('unexpected pinned snow weather')
        target=Path(out)/'staged'/name/'map.json';h=json.loads(target.read_text())
        changed[name]=dict(before=h['weather'],after=weather,source_header_sha256=base.sha(raw))
        h['weather']=weather;target.write_bytes(base.encode(h))
    return changed


def build(donor,out):
    receipt=base.build(donor,out,maps=MAPS)
    receipt['source_weather_restored']=preserve_source_weather(donor,out,receipt)
    receipt['limits'] += ['Source WEATHER_SNOW preserved; visibility, weather allocation and rendering not emulator-verified',
        'LakeAcuity is excluded: pinned source has no warp or connection; no invented lake entrance',
        'Original Route216 Coronet portal closed until joint source integration; no new progression or saved IDs']
    (Path(out)/'source-receipt.json').write_bytes(base.encode(receipt))
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--donor',required=True,type=Path);p.add_argument('--out',required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.donor,args.out),indent=2))
