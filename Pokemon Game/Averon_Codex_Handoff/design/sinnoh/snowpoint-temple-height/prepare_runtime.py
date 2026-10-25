#!/usr/bin/env python3
"""Assemble/guard a separate source-height Temple DEV scene; never production."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent

def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

core=load('temple_height_existing_prepare',HERE.parent/'snowpoint-temple-core/prepare_runtime.py')
geometry=load('temple_height_geometry',HERE/'build_geometry.py')
base=core.base;sha=core.sha;encode=core.encode;ENGINE=core.ENGINE;BASE=core.BASE


def assemble(repo):
    repo=Path(repo).resolve();files,receipt=core.assemble(repo)
    pin=json.loads((HERE/'source-receipt.json').read_text())
    for path,h in pin['input_sha256'].items():
        folder=HERE.parent/'snowpoint-temple-core' if path=='portal-reference.json' else HERE
        if sha((folder/path).read_bytes())!=h:raise ValueError('height source input differs')
    for path,h in pin['native_asset_sha256'].items():
        if sha(base.verified_file(repo,Path(ENGINE)/path,'HEAD'))!=h:raise ValueError('height native art differs')
    expected=geometry.construct(json.loads((HERE/'geometry-audit.json').read_text()),json.loads((HERE.parent/'snowpoint-temple-core/portal-reference.json').read_text()))
    layouts=json.loads(files['data/layouts/layouts.json'])
    for name,(raw,border,header) in expected.items():
        f=HERE/'staged'/name
        if raw!=(f/'map.bin').read_bytes() or border!=(f/'border.bin').read_bytes() or header!=json.loads((f/'map.json').read_text()):
            raise ValueError('height geometry packet differs')
        header['region_map_section']='MAPSEC_ROUTE_201'
        files[f'data/maps/{name}/map.json']=encode(header)
        files[f'data/layouts/{name}/map.bin']=raw;files[f'data/layouts/{name}/border.bin']=border
        layout=next(v for v in layouts['layouts'] if v['id']==header['layout'])
        if layout['width']!=20 or layout['height']!=20:raise ValueError('unexpected inherited geometry')
        layout.update(width=32,height=32)
    files['data/layouts/layouts.json']=encode(layouts)
    del files['test/averon_temple_core_runtime.c']
    files['test/averon_temple_height_runtime.c']=(HERE/'native-runtime.c').read_bytes()
    receipt.update(physical_scope='provisional source-height/ice geometry; no runtime acceptance',files={p:sha(v) for p,v in sorted(files.items())})
    return files,receipt


def install(repo):
    repo=Path(repo).resolve();engine=repo/ENGINE
    if not base.git(repo,'branch','--show-current').decode().strip().startswith('codex/temple-height-runtime-') or not (engine/'.map_qa_throwaway').is_file():
        raise ValueError('marked height disposable branch required')
    if base.git(repo,'rev-parse','HEAD').decode().strip()!=BASE:raise ValueError('exact base required')
    if base.git(repo,'status','--porcelain','--untracked-files=normal','--',ENGINE).decode().splitlines() not in ([],['?? "Pokemon Game/engine/.map_qa_throwaway"']):
        raise ValueError('dirty engine refused')
    files,r=assemble(repo)
    for p in files:
        target=(engine/p).resolve()
        if not target.is_relative_to(engine.resolve()):raise ValueError('output escapes engine')
        try:base.git(repo,'cat-file','-e','HEAD:'+ENGINE+p)
        except subprocess.CalledProcessError:
            if target.exists():raise ValueError('untracked output exists')
    for p,data in files.items():
        target=engine/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return r

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',required=True,type=Path);p.add_argument('--install',action='store_true');a=p.parse_args()
    print(json.dumps(install(a.repo) if a.install else assemble(a.repo)[1],indent=2))
