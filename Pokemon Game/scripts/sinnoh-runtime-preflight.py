#!/usr/bin/env python3
"""Read-only archived DEV-batch identity checks before serial emulator testing.

This verifies consistency of listed, locally recorded inputs, not independent
build provenance or runtime acceptance. Unlisted engine changes need a separate
whole-tree audit. It never installs maps, changes saves, or authorizes IDs.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def inside(root, relative):
    p = Path(relative)
    target = (root / p).resolve()
    if p.is_absolute() or not target.is_relative_to(root.resolve()):
        raise ValueError('path escapes input root: ' + str(relative))
    return target


def verify_engine_changes(repo, engine, recipe):
    """Reject unlisted tracked or untracked source changes without modifying Git."""
    repo, engine = Path(repo).resolve(), Path(engine).resolve()
    relative = engine.relative_to(repo).as_posix()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args])
    if git('rev-parse', 'HEAD').decode().strip() != recipe['base']:
        raise ValueError('scratch HEAD differs from recipe base')
    baseline = json.loads(git('show', 'HEAD:' + relative + '/data/maps/map_groups.json'))
    if baseline['gMapGroup_Sinnoh'] != recipe['existing_map_names_preserved']:
        raise ValueError('original Sinnoh prefix differs from base HEAD')
    tracked = git('diff', '--name-only', '-z', 'HEAD', '--', relative)
    untracked = git('ls-files', '--others', '--exclude-standard', '-z', '--', relative)
    paths = {v.decode() for v in (tracked + untracked).split(b'\0') if v}
    allowed = {relative + '/' + name for name in recipe['files']}
    allowed.add(relative + '/.map_qa_throwaway')
    unexpected = sorted(paths - allowed)
    if unexpected:
        raise ValueError('unlisted engine changes: ' + repr(unexpected))
    return dict(base=recipe['base'], changed_paths=len(paths), unexpected_engine_paths=[])


def verify(engine, archive, recipe_name, identity_name, profile, repo=None):
    if profile not in ('normal', 'release'):
        raise ValueError('unknown profile')
    engine, archive = Path(engine).resolve(), Path(archive).resolve()
    manifest = json.loads((archive / 'archive.json').read_text())
    stem = 'pokeemerald-release' if profile == 'release' else 'pokeemerald'
    names = [recipe_name, identity_name, stem + '.gba', stem + '.elf']
    for name in names:
        p = inside(archive, name)
        expected = manifest[name]
        if p.stat().st_size != expected['bytes'] or digest(p) != expected['sha256']:
            raise ValueError('archive identity differs: ' + name)
    recipe_path = inside(archive, recipe_name)
    recipe = json.loads(recipe_path.read_text())
    identity = json.loads(inside(archive, identity_name).read_text())
    if recipe['status'] != 'DEV_ONLY_NOT_PRODUCTION_OR_SAVED_ORIGIN_ACCEPTANCE':
        raise ValueError('DEV-only recipe required')
    if not (engine / '.map_qa_throwaway').is_file():
        raise ValueError('marked scratch required')
    if (identity['base'] != recipe['base'] or identity['files'] != recipe['files']
            or identity['recipe_sha256'] != digest(recipe_path)):
        raise ValueError('source identity and recipe differ')
    for name, expected in recipe['files'].items():
        if digest(inside(engine, name)) != expected:
            raise ValueError('engine source differs: ' + name)
    groups = json.loads((engine / 'data/maps/map_groups.json').read_text())
    prior = recipe['existing_map_names_preserved']
    slots = recipe['temporary_map_slots']
    names = list(groups['gMapGroup_Sinnoh'])
    if (len(set(names)) != len(names) or len(set(prior)) != len(prior)
            or names != prior + list(slots)
            or list(slots.values()) != list(range(len(prior), len(names)))):
        raise ValueError('temporary registry is not an exact append-only prefix')
    audit = verify_engine_changes(repo, engine, recipe) if repo is not None else None
    return dict(whole_engine_audit=audit, status='CONSISTENT_DEV_INPUTS_NOT_RUNTIME_ACCEPTANCE', profile=profile,
                base=recipe['base'], engine_tree=identity['engine_tree'],
                source_files=len(recipe['files']), coverage='listed file hashes plus whole-engine Git audit' if audit is not None else 'listed recipe files only; audit unlisted engine changes separately',
                prior_maps=len(prior),
                temporary_maps=len(slots), rom_sha256=digest(archive / (stem + '.gba')),
                elf_sha256=digest(archive / (stem + '.elf')))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--engine', required=True, type=Path)
    p.add_argument('--archive', required=True, type=Path)
    p.add_argument('--recipe', required=True, help='relative archived recipe filename')
    p.add_argument('--identity', required=True, help='relative archived identity filename')
    p.add_argument('--repo', required=True, type=Path, help='scratch repository for whole-engine change audit')
    p.add_argument('--profile', required=True, choices=('normal', 'release'))
    a = p.parse_args()
    print(json.dumps(verify(a.engine, a.archive, a.recipe, a.identity, a.profile, a.repo), indent=2))
