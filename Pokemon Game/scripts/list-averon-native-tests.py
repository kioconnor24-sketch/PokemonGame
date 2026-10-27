"""List compiled native test identities from an ARM ELF; this does not execute tests.

Complements check-averon-native-baseline.py without changing its completion or
expected-failure rules. Supports the current ARM32 struct Test ABI (20 bytes,
name/filename pointers at offsets 0/4 and sourceLine at 16). Unknown formats
fail closed. No third-party ELF package or emulator is needed.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct


def inventory(blob, prefix='Averon'):
    if len(blob) < 52 or blob[:7] != b'\x7fELF\x01\x01\x01':
        raise ValueError('expected complete little-endian ELF32')
    h = struct.unpack_from('<16sHHIIIIIHHHHHH', blob)
    if h[1:4] != (2, 40, 1) or h[8] != 52 or h[11] != 40 or not 0 < h[12] <= 4096:
        raise ValueError('unsupported ARM executable/section ABI')

    def region(offset, size):
        if offset < 0 or size < 0 or offset > len(blob) or size > len(blob) - offset:
            raise ValueError('truncated ELF region')
        return memoryview(blob)[offset:offset + size]

    region(h[6], h[11] * h[12])
    sections = [struct.unpack_from('<10I', blob, h[6] + 40 * i) for i in range(h[12])]
    for s in sections:
        if s[1] != 8:  # SHT_NOBITS has no file payload.
            region(s[4], s[5])
    tables = [s for s in sections if s[1] == 2]
    if len(tables) != 1:
        raise ValueError('one unstripped symbol table required')
    symbols = tables[0]
    if symbols[9] != 16 or symbols[5] % 16 or symbols[5] // 16 > 1_000_000:
        raise ValueError('unsupported symbol table')
    if symbols[6] >= len(sections) or sections[symbols[6]][1] != 3:
        raise ValueError('invalid symbol string table')
    strings = bytes(region(sections[symbols[6]][4], sections[symbols[6]][5]))

    def cstring(data, offset, limit=None):
        limit = len(data) if limit is None else limit
        if not 0 <= offset < limit:
            raise ValueError('string pointer outside section')
        end = data.find(b'\0', offset, limit)
        if end < 0:
            raise ValueError('unterminated string')
        try:
            return data[offset:end].decode('utf-8')
        except UnicodeDecodeError as error:
            raise ValueError('invalid UTF-8 identity') from error

    bounds = {}
    for offset in range(symbols[4], symbols[4] + symbols[5], 16):
        name, address = struct.unpack_from('<II', blob, offset)
        name = cstring(strings, name)
        if name in ('__start_tests', '__stop_tests'):
            if name in bounds:
                raise ValueError('duplicate test boundary symbol')
            bounds[name] = address
    if len(bounds) != 2:
        raise ValueError('missing compiled test boundaries')
    start, stop = bounds['__start_tests'], bounds['__stop_tests']
    if start % 4 or stop <= start or (stop - start) % 20 or (stop - start) // 20 > 65536:
        raise ValueError('unsupported test descriptor span/ABI')
    # Keep section ranges, not payload copies (which may overlap in malformed input).
    backed = [(s[3], s[3] + s[5], s[4], s[5]) for s in sections if s[1] == 1]

    def mapped(address, size=1):
        matches = [(file_offset + address - low, file_offset + size_on_disk)
                   for low, high, file_offset, size_on_disk in backed if low <= address and address + size <= high]
        if len(matches) != 1:
            raise ValueError('unmapped or ambiguous test pointer')
        return matches[0]

    base, _ = mapped(start, stop - start)
    tests = []
    for offset in range(base, base + stop - start, 20):
        name_ptr, filename_ptr = struct.unpack_from('<II', blob, offset)
        index, limit = mapped(name_ptr)
        name = cstring(blob, index, limit)
        if not name.startswith(prefix):
            continue
        index, limit = mapped(filename_ptr)
        tests.append(dict(name=name, filename=cstring(blob, index, limit),
                          line=struct.unpack_from('<H', blob, offset + 16)[0]))
    if not tests:
        raise ValueError('no compiled tests match prefix')
    duplicates = sorted(name for name, count in Counter(t['name'] for t in tests).items() if count > 1)
    return dict(scope='Compiled identity inventory only; no execution or acceptance claim',
                elf_sha256=hashlib.sha256(blob).hexdigest(), prefix=prefix, count=len(tests),
                ambiguous_log_names=duplicates, tests=tests)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('elf', type=Path)
    p.add_argument('--prefix', default='Averon')
    args = p.parse_args()
    if args.elf.stat().st_size > 64 * 1024 * 1024:
        p.error('ELF exceeds 64 MiB inventory limit')
    try:
        with args.elf.open('rb') as stream:
            blob = stream.read(64 * 1024 * 1024 + 1)
        if len(blob) > 64 * 1024 * 1024:
            p.error('ELF exceeds 64 MiB inventory limit')
        print(json.dumps(inventory(blob, args.prefix), indent=2))
    except ValueError as error:
        p.error(str(error))


if __name__ == '__main__':
    main()
