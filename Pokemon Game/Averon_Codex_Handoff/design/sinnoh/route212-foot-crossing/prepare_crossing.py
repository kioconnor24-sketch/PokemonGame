#!/usr/bin/env python3
"""Compose one reversible DEV foot crossing onto the existing eastern scene.

No installer: callers receive the ordinary eastern overlay dictionary and receipt.
Production source, donor geometry and the original eastern packet stay immutable.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
SOURCE_SHA256 = '33ca15c567c5a28eec9cae20589db3bf94fe07e6b5ef372913eeee23af7a7d97'
PATH = 'data/layouts/Route212_South/map.bin'
CELL = (38, 11)
WIDTH, HEIGHT = 130, 34
OLD, NEW = 0xF24C, 0xF001


def sha(data):
    return hashlib.sha256(data).hexdigest()


def patch(raw):
    if len(raw) != WIDTH * HEIGHT * 2 or sha(raw) != SOURCE_SHA256:
        raise ValueError('exact original eastern Route212 South required')
    offset = 2 * (CELL[1] * WIDTH + CELL[0])
    if struct.unpack_from('<H', raw, offset)[0] != OLD:
        raise ValueError('source rail word changed')
    result = bytearray(raw)
    struct.pack_into('<H', result, offset, NEW)
    return bytes(result)


def eastern():
    spec = importlib.util.spec_from_file_location('crossing_existing_eastern', HERE.parent / 'eastern-loop/prepare_runtime.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compose(files, receipt):
    """Fail closed before returning a copied overlay; preserve collision/elevation."""
    original = files[PATH]
    replacement = patch(original)
    # Both records use the existing primary General bank. Verify semantics,
    # not just the selected raw word, before composing a usable scene.
    primary = HERE.parent / 'eastern-loop/hotel-link/outdoor-family/primary-attributes.bin'
    secondary = HERE.parent / 'eastern-loop/hotel-link/outdoor-family/secondary-attributes.bin'
    if struct.unpack_from('<H', primary.read_bytes(), 2)[0] != 0:
        raise ValueError('existing plain-ground full attribute changed')
    if struct.unpack_from('<H', secondary.read_bytes(), (0x24C - 512) * 2)[0] != 0xD6:
        raise ValueError('existing rail full attribute changed')
    result = dict(files)
    result[PATH] = replacement
    evidence = copy.deepcopy(receipt)
    evidence['foot_crossing'] = dict(status='SOURCE_DEV_ONLY_NOT_RUNTIME_ACCEPTANCE',
        contract_pr=291, contract_head='0089e5ff88ab3d511975fe37f23ca176127e01a3',
        path=PATH, cell=list(CELL), before_word=OLD, after_word=NEW,
        before_sha256=sha(original), after_sha256=sha(replacement),
        changed_cells=1, collision=0, elevation=15,
        graphics='Existing General metatile1; no bank or asset modification',
        remaining_rails='Every other original rail is byte-identical')
    return result, evidence


def assemble(repo, acro_fixture=False):
    return compose(*eastern().assemble(repo, acro_fixture=acro_fixture))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True,
        help='new off-engine output directory; never installs into engine')
    args = parser.parse_args()
    repo = args.repo.resolve()
    out = args.out.resolve()
    engine = repo / 'Pokemon Game/engine'
    if out.is_relative_to(engine) or out.exists():
        raise ValueError('new off-engine output directory required')
    files, receipt = assemble(repo)
    out.mkdir(parents=True)
    (out / 'route212-south-map.bin').write_bytes(files[PATH])
    (out / 'receipt.json').write_text(json.dumps(receipt['foot_crossing'], indent=2) + '\n')
    print(json.dumps(receipt['foot_crossing'], indent=2))


if __name__ == '__main__':
    main()
