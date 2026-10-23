#!/usr/bin/env python3
"""Reconcile the proven Oreburgh DEV overlay with a pinned production baseline.

Only a marked disposable checkout at EXACT_BASE can receive temporary maps.
This does not authorize permanent saved origins or production registration.
"""
import argparse
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import zipfile

HERE = Path(__file__).resolve().parent
EXACT_BASE = 'c6ac2f967b02473741791eb24b5cc9b11bda3904'
ENGINE = 'Pokemon Game/engine/'
SPEC = importlib.util.spec_from_file_location('oreburgh_frozen_recipe', HERE/'prepare_candidate.py')
frozen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(frozen)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def current_inputs():
    """Pinned cache permits offline/shallow replay, never arbitrary local reads."""
    pins = json.loads((HERE/'current-base-input-hashes.json').read_text())
    with zipfile.ZipFile(io.BytesIO((HERE/'current-base-inputs.zip').read_bytes())) as archive:
        if len(archive.namelist()) != len(pins) or set(archive.namelist()) != set(pins):
            raise ValueError('current baseline cache paths changed')
        result = {p: archive.read(p) for p in pins}
    for path, data in result.items():
        if sha(data) != pins[path]:
            raise ValueError('current baseline cache hash changed: '+path)
    return result


def reconcile(files, before, old_before):
    """Append only to the supplied current prefix; reject collisions before writes."""
    files = dict(files)
    group_name = 'gMapGroup_Sinnoh'
    groups = json.loads(before['data/maps/map_groups.json'])
    layouts = json.loads(before['data/layouts/layouts.json'])
    old_groups = json.loads(old_before['data/maps/map_groups.json'])
    old_layouts = json.loads(old_before['data/layouts/layouts.json'])
    additions = json.loads(files['data/layouts/layouts.json'])['layouts'][len(old_layouts['layouts']):]
    names = groups[group_name]
    if (len(names) != len(set(names)) or groups['group_order'] != old_groups['group_order']
            or names[:len(old_groups[group_name])] != old_groups[group_name]):
        raise ValueError('existing map identities/order changed')
    if set(frozen.MAPS) & {n for k,v in groups.items() if k != 'group_order' for n in v}:
        raise ValueError('target map already registered')
    for key in ('id', 'name'):
        existing = [x[key] for x in layouts['layouts']]
        if len(existing) != len(set(existing)) or set(existing) & {x[key] for x in additions}:
            raise ValueError('duplicate or already registered layout '+key)
    if layouts['layouts'][:len(old_layouts['layouts'])] != old_layouts['layouts']:
        raise ValueError('existing layout prefix changed')
    group = groups['group_order'].index(group_name)
    count = len(names)
    if count+len(frozen.MAPS) > 256:
        raise ValueError('map slot byte capacity exceeded')
    pins = before['test/data/averon_map_registry_slots.inc'].decode()
    marker = f'REGISTRY_GROUP({group}, {group_name}, {count}, 1)'
    if pins.count(marker) != 1:
        raise ValueError('current registry count differs')
    for slot, name in enumerate(names):
        # Require every literal existing golden slot to agree with current groups.
        if not any(line.startswith(f'REGISTRY_SLOT({group}, {slot}, ')
                   and line.endswith(f', {name}, 1)') for line in pins.splitlines()):
            raise ValueError('current registry slot differs: '+name)
    pins = pins.replace(marker, f'REGISTRY_GROUP({group}, {group_name}, {count+len(frozen.MAPS)}, 1)')
    for slot,name in enumerate(frozen.MAPS, count):
        pins += f'REGISTRY_SLOT({group}, {slot}, {frozen.IDS[name]}, {name}, 1)\n'
    groups[group_name] += list(frozen.MAPS)
    layouts['layouts'] += additions
    files['data/maps/map_groups.json'] = frozen.encode(groups)
    files['data/layouts/layouts.json'] = frozen.encode(layouts)
    files['test/data/averon_map_registry_slots.inc'] = pins.encode()
    for path in ('data/event_scripts.s', 'include/tilesets.h',
                 'src/data/tilesets/headers.h', 'src/data/tilesets/metatiles.h'):
        if not files[path].startswith(old_before[path]):
            raise ValueError('frozen overlay is not append-only: '+path)
        extra = files[path][len(old_before[path]):]
        if extra in before[path] or any(name.encode() in before[path] for name in frozen.MAPS):
            raise ValueError('target declarations already present: '+path)
        files[path] = before[path]+extra
    for path in ('data/maps/OreburghGate_1F/map.json', 'data/layouts/OreburghGate_1F/map.bin'):
        if before[path] != old_before[path]:
            raise ValueError('Gate changed since proven source: '+path)
    return files, {name: count+i for i,name in enumerate(frozen.MAPS)}


def assemble(repo):
    files, receipt = frozen.assemble(repo)
    before = current_inputs()
    old = {p: frozen.blob(repo, frozen.BASE, ENGINE+p) for p in before}
    files,slots = reconcile(files,before,old)
    receipt = copy.deepcopy(receipt)
    receipt.update(base=EXACT_BASE, frozen_source_base=frozen.BASE,
                   existing_map_names_preserved=json.loads(before['data/maps/map_groups.json'])['gMapGroup_Sinnoh'],
                   temporary_map_slots=slots, files={p:sha(v) for p,v in sorted(files.items())},
                   baseline_files={p:sha(v) for p,v in sorted(before.items())})
    return files,receipt


def install(repo):
    repo = Path(repo).resolve()
    branch = frozen.git(repo,'branch','--show-current').decode().strip()
    engine = repo/ENGINE
    if not branch.startswith('codex/oreburgh-current-runtime-scratch-') or not (engine/'.map_qa_throwaway').is_file():
        raise ValueError('explicit current disposable branch and marker required')
    if frozen.git(repo,'rev-parse','HEAD').decode().strip() != EXACT_BASE:
        raise ValueError('scratch must start at exact current baseline')
    if frozen.git(repo,'status','--porcelain','--untracked-files=normal','--',ENGINE).decode().splitlines() not in ([], ['?? "Pokemon Game/engine/.map_qa_throwaway"']):
        raise ValueError('refusing dirty or untracked runtime source')
    files, receipt = assemble(repo)
    for path,data in current_inputs().items():
        tracked = frozen.git(repo,'show','HEAD:'+ENGINE+path)
        if tracked != data or (engine/path).read_bytes() != tracked:
            raise ValueError('current runtime source differs from pinned baseline: '+path)
    for path in files:
        target = engine/path
        if not target.resolve().is_relative_to(engine.resolve()):
            raise ValueError('overlay escapes engine')
        try:
            frozen.git(repo,'cat-file','-e','HEAD:'+ENGINE+path)
        except subprocess.CalledProcessError:
            if target.exists():
                raise ValueError('untracked overlay target exists: '+path)
    for path,data in files.items():
        target = engine/path
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--install',action='store_true')
    args = parser.parse_args()
    print(json.dumps(install(args.repo) if args.install else assemble(args.repo)[1],indent=2))
