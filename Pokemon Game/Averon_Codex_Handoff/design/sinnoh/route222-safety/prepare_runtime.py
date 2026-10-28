#!/usr/bin/env python3
"""Apply the reviewed two-cell candidate over the existing coast DEV assembler."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('route222_original_scene',HERE.parent/'sunyshore-coast/prepare_runtime.py')
coast=importlib.util.module_from_spec(sp);sp.loader.exec_module(coast)
BASE='871c46b6fc8b4fdaae9e2bef04543c649987542a'
ENGINE=coast.ENGINE;base=coast.base;sha=coast.sha


def assemble(repo):
    files,receipt=coast.assemble(repo)
    repair=json.loads((HERE/'corrected/repair-receipt.json').read_text())
    # Both original packets remain pinned by the source correction and the
    # engine candidate must be the exact separately reviewed corrected bytes.
    before=files['data/layouts/Route222/map.bin']
    if sha(before)!=repair['original_sha256']['averon-map.bin']:raise ValueError('original runtime route changed')
    raw=(HERE/'corrected/averon-map.bin').read_bytes()
    if sha(raw)!=repair['output_sha256']['averon-map.bin']:raise ValueError('tested corrected route differs')
    import struct
    changes=[(i,a,b) for i,(a,b) in enumerate(zip(struct.unpack('<2944H',before),struct.unpack('<2944H',raw))) if a!=b]
    if changes!=[(16*92+36,0x487,0x491),(16*92+37,0x487,0x491)]:raise ValueError('exact two cliff corrections required')
    files['data/layouts/Route222/map.bin']=raw
    files['test/averon_route222_safety_runtime.c']=(HERE/'native-runtime.c').read_bytes()
    receipt.update(base=BASE,correction=repair,files={p:sha(v) for p,v in sorted(files.items())})
    return files,receipt


def install(repo):
    repo=Path(repo).resolve();engine=repo/ENGINE
    if not base.git(repo,'branch','--show-current').decode().strip().startswith('codex/route222-safety-runtime-scratch-') or not (engine/'.map_qa_throwaway').is_file():
        raise ValueError('explicit disposable Route222 safety branch and marker required')
    if base.git(repo,'rev-parse','HEAD').decode().strip()!=BASE:raise ValueError('exact production baseline required')
    status=base.git(repo,'status','--porcelain','--untracked-files=normal','--',ENGINE).decode().splitlines()
    if status not in ([],['?? "Pokemon Game/engine/.map_qa_throwaway"']):raise ValueError('refusing dirty runtime source')
    files,receipt=assemble(repo)
    for path in files:
        target=(engine/path).resolve()
        if not target.is_relative_to(engine.resolve()):raise ValueError('output path escapes engine')
        try:base.git(repo,'cat-file','-e','HEAD:'+ENGINE+path)
        except subprocess.CalledProcessError:
            if target.exists():raise ValueError('untracked output exists')
    for path,data in files.items():
        target=engine/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',required=True,type=Path);p.add_argument('--install',action='store_true');a=p.parse_args()
    print(json.dumps(install(a.repo) if a.install else assemble(a.repo)[1],indent=2))
