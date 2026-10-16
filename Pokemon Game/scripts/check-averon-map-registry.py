#!/usr/bin/env python3
"""Check existing saved map IDs and capacities without writing any map files."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import struct

GROUP = re.compile(r'REGISTRY_GROUP\((\d+), (\w+), (\d+), ([01])\)')
SLOT = re.compile(r'REGISTRY_SLOT\((\d+), (\d+), (MAP_\w+), (\w+), ([01])\)')
EVENTS = {'object_events': 255, 'warp_events': 128,
          'coord_events': 255, 'bg_events': 255}


def read_pins(path):
    groups, slots = [], []
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith('//'):
            continue
        if match := GROUP.fullmatch(line):
            index, name, count, linked = match.groups()
            groups.append((int(index), name, int(count), int(linked)))
        elif match := SLOT.fullmatch(line):
            group, index, constant, name, linked = match.groups()
            slots.append((int(group), int(index), constant, name, int(linked)))
        else:
            raise ValueError(f'Unrecognized pinned registry line: {line}')
    if not groups or not slots:
        raise ValueError('Pinned registry must contain positive group and map counts')
    return groups, slots


def validate(groups, maps, pins):
    errors = []

    def fail(code, detail):
        errors.append({'code': code, 'detail': detail})

    order = groups.get('group_order')
    if not isinstance(order, list) or not order or not all(isinstance(x, str) for x in order):
        return [{'code': 'group-order', 'detail': 'Expected nonempty string array'}]
    if len(order) > 128:
        fail('group-capacity', f'{len(order)} groups exceed signed-byte indexing')
    if len(order) != len(set(order)):
        fail('duplicate-group', 'group_order contains duplicate entries')
    if set(groups) - {'group_order'} != set(order):
        fail('group-membership', 'Group definitions differ from group_order')
    seen_names, seen_ids = set(), set()
    actual_groups, actual_slots = [], []
    for group_index, name in enumerate(order):
        names = groups.get(name)
        if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
            fail('group-definition', name)
            continue
        if len(names) > 128:
            fail('map-capacity', f'{name} has {len(names)} entries')
        linked = []
        for index, symbol in enumerate(names):
            if symbol in seen_names:
                fail('duplicate-map', symbol)
            seen_names.add(symbol)
            data = maps.get(symbol)
            if not isinstance(data, dict):
                fail('missing-map', symbol)
                continue
            constant = data.get('id')
            if not isinstance(constant, str) or not re.fullmatch(r'MAP_\w+', constant):
                fail('map-id', symbol)
                continue
            if constant in seen_ids:
                fail('duplicate-id', constant)
            seen_ids.add(constant)
            if data.get('name') != symbol:
                fail('map-symbol', symbol)
            if (group_index, index) == (127, 127):
                fail('reserved-id', f'{symbol} occupies MAP_DYNAMIC')
            region = data.get('region', 'REGION_HOENN')
            if region not in ('REGION_HOENN', 'REGION_KANTO'):
                fail('unsupported-region', f'{symbol}: {region}')
            active = int(region == 'REGION_HOENN')
            linked.append(active)
            actual_slots.append((group_index, index, constant, symbol, active))
            for event, capacity in EVENTS.items():
                entries = data.get(event, [])
                if entries is None:
                    entries = []
                if not isinstance(entries, list):
                    fail('event-array', f'{symbol}.{event}')
                elif len(entries) > capacity:
                    fail('event-capacity', f'{symbol}.{event}: {len(entries)} > {capacity}')
        # mapjson compacts filtered entries but constants and MAP_GROUP_COUNT
        # retain source positions/counts. A mixed group would desynchronize them.
        if len(set(linked)) > 1:
            fail('mixed-region-group', name)
        actual_groups.append((group_index, name, len(names), int(any(linked))))
    if actual_groups != pins[0]:
        fail('pinned-groups', 'Existing ordered groups/counts/link state changed')
    if actual_slots != pins[1]:
        fail('pinned-slots', 'Existing saved map IDs/order/symbols/link state changed')
    return errors


def mutations(groups, maps, pins):
    cases = {}
    first, second = groups['group_order'][:2]
    symbol, other = groups[first][:2]
    for name in ('group-reorder', 'map-reorder', 'duplicate-id', 'missing-map',
                 'symbol-mismatch', 'mixed-region', 'group-overflow',
                 'map-overflow', 'event-overflow', 'warp-index-overflow'):
        g, m = deepcopy(groups), deepcopy(maps)
        if name == 'group-reorder':
            g['group_order'][:2] = [second, first]
            expected = 'pinned-groups'
        elif name == 'map-reorder':
            g[first][:2] = [other, symbol]
            expected = 'pinned-slots'
        elif name == 'duplicate-id':
            m[other]['id'] = m[symbol]['id']
            expected = 'duplicate-id'
        elif name == 'missing-map':
            del m[symbol]
            expected = 'missing-map'
        elif name == 'symbol-mismatch':
            m[symbol]['name'] = 'MUTATED_IN_MEMORY'
            expected = 'map-symbol'
        elif name == 'mixed-region':
            m[symbol]['region'] = 'REGION_KANTO'
            expected = 'mixed-region-group'
        elif name == 'group-overflow':
            for i in range(129 - len(g['group_order'])):
                key = f'gMapGroup_InMemoryMutation{i}'
                g['group_order'].append(key)
                g[key] = []
            expected = 'group-capacity'
        elif name == 'map-overflow':
            g[first] = [symbol] * 129
            expected = 'map-capacity'
        elif name == 'event-overflow':
            m[symbol]['object_events'] = [{}] * 256
            expected = 'event-capacity'
        elif name == 'warp-index-overflow':
            m[symbol]['warp_events'] = [{}] * 129
            expected = 'event-capacity'
        errors = validate(g, m, pins)
        if expected not in {e['code'] for e in errors}:
            raise AssertionError(f'Undetected {name}: expected {expected}, got {errors}')
        cases[name] = 'DETECTED'
    # Prove the capacities accept their last representable values. These
    # in-memory arrays do not author maps or validate their gameplay contents.
    boundary = deepcopy(maps)
    for field, capacity in EVENTS.items():
        boundary[symbol][field] = [{}] * capacity
    if validate(groups, boundary, pins):
        raise AssertionError('Valid event-capacity boundary was rejected')
    return cases


class ArmElf:
    """Read allocated ARM ELF bytes and local symbols; no external packages."""
    def __init__(self, data):
        self.data = data
        if data[:7] != b'\x7fELF\x01\x01\x01':
            raise ValueError('Expected a little-endian ELF32 build')
        header = struct.unpack_from('<HHIIIIIHHHHHH', data, 16)
        if header[0] != 2 or header[1] != 40 or header[10] != 40:
            raise ValueError('Expected executable ARM ELF with ELF32 section headers')
        self.sections = [struct.unpack_from('<10I', data, header[5] + i * 40)
                         for i in range(header[11])]
        self.symbols = {}
        for section in self.sections:
            if section[1] != 2:  # SHT_SYMTAB, including assembler-local labels.
                continue
            if section[9] != 16:
                raise ValueError('Unexpected ELF32 symbol size')
            strings = self.sections[section[6]]
            text = data[strings[4]:strings[4] + strings[5]]
            for offset in range(section[4], section[4] + section[5], 16):
                name, value, size, info, other, index = struct.unpack_from('<IIIBBH', data, offset)
                if index == 0:
                    continue
                end = text.find(b'\0', name)
                if end < name:
                    raise ValueError('Unterminated ELF symbol')
                name = text[name:end].decode('utf-8', errors='replace')
                self.symbols.setdefault(name, []).append(value)

    def symbol(self, name):
        values = self.symbols.get(name, [])
        if len(values) != 1:
            raise ValueError(f'Expected one defined ELF symbol {name}, found {len(values)}')
        return values[0]

    def offset(self, address):
        for section in self.sections:
            if section[1] != 8 and section[2] & 2 and section[3] <= address and address + 4 <= section[3] + section[5]:
                offset = section[4] + address - section[3]
                if offset + 4 > len(self.data):
                    raise ValueError('ELF section extends past file')
                return offset
        raise ValueError(f'Address 0x{address:x} has no allocated ELF bytes')

    def word(self, address):
        return struct.unpack_from('<I', self.data, self.offset(address))[0]


def validate_elf(data, pins):
    elf, errors = ArmElf(data), []
    table = elf.symbol('gMapGroups')
    matched_groups = set()
    for index, symbol, count, linked in pins[0]:
        actual = elf.word(table + 4 * index)
        expected = elf.symbol(symbol) if linked else 0
        if actual != expected:
            errors.append({'code': 'elf-group-pointer', 'detail': f'{index}: {symbol}'})
        else:
            matched_groups.add(index)
    checked = 0
    for group, index, constant, symbol, linked in pins[1]:
        if not linked or group not in matched_groups:
            continue
        actual = elf.word(elf.word(table + 4 * group) + 4 * index)
        if actual != elf.symbol(symbol):
            errors.append({'code': 'elf-map-pointer', 'detail': constant})
        checked += 1
    return errors, checked


def elf_mutations(data, pins):
    elf = ArmElf(data)
    table = elf.symbol('gMapGroups')
    active = next(g for g in pins[0] if g[3])
    disabled = next(g for g in pins[0] if not g[3])
    group_address = elf.symbol(active[1])
    changes = {
        'linked-group-null': (table + 4 * active[0], 0, 'elf-group-pointer'),
        'disabled-group-linked': (table + 4 * disabled[0], group_address, 'elf-group-pointer'),
        'wrong-header-in-slot': (group_address, elf.word(group_address + 4), 'elf-map-pointer'),
    }
    results = {}
    for name, (address, value, expected) in changes.items():
        changed = bytearray(data)
        struct.pack_into('<I', changed, elf.offset(address), value)
        errors, checked = validate_elf(changed, pins)
        if expected not in {e['code'] for e in errors}:
            raise AssertionError(f'Undetected ELF mutation {name}')
        results[name] = 'DETECTED'
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--engine', type=Path, required=True)
    parser.add_argument('--mutations', action='store_true')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--elf', type=Path, help='Also inspect an actual linked ARM ELF without modifying it')
    args = parser.parse_args()
    engine = args.engine.resolve()
    manifest = engine / 'test/data/averon_map_registry_slots.inc'
    groups_path = engine / 'data/maps/map_groups.json'
    groups = json.loads(groups_path.read_text())
    paths = {name: engine / 'data/maps' / name / 'map.json'
             for key in groups['group_order'] for name in groups[key]}
    maps = {name: json.loads(path.read_text()) for name, path in paths.items()}
    pins = read_pins(manifest)
    warp = re.search(r'struct WarpData\s*\{(.*?)\};',
                     (engine / 'include/global.h').read_text(), re.S)
    if not warp or any(not re.search(r'\bs8\s+' + field + r'\s*;', warp[1])
                       for field in ('mapGroup', 'mapNum', 'warpId')):
        raise ValueError('WarpData signed-byte contract changed; review the capacity policy')
    event_struct = re.search(r'struct MapEvents\s*\{(.*?)\};',
                             (engine / 'include/global.fieldmap.h').read_text(), re.S)
    if not event_struct or any(not re.search(r'\bu8\s+' + field + r'\s*;', event_struct[1])
                               for field in ('objectEventCount', 'warpCount', 'coordEventCount', 'bgEventCount')):
        raise ValueError('MapEvents counter widths changed; review the capacity policy')
    errors = validate(groups, maps, pins)
    counts = [len(groups[name]) for name in groups['group_order']]
    enabled = [count for (_, _, count, linked) in pins[0] if linked]
    report = {'groups': len(counts), 'map_slots': len(pins[1]),
              'linked_groups': len(enabled), 'linked_maps': sum(enabled),
              'disabled_groups': len(counts) - len(enabled),
              'signed_group_slots_remaining': 128 - len(counts),
              'smallest_group_headroom': 128 - max(counts),
              'smallest_linked_group_headroom': 128 - max(enabled),
              'errors': errors, 'mutations': {},
              'input_sha256': {str(p.relative_to(engine)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in [groups_path, manifest, engine / 'include/global.h',
                                         engine / 'include/global.fieldmap.h', *paths.values()]}}
    if not errors and args.mutations:
        report['mutations'] = mutations(groups, maps, pins)
    if not errors and args.elf:
        data = args.elf.read_bytes()
        elf_errors, checked = validate_elf(data, pins)
        errors.extend(elf_errors)
        report['elf'] = {'sha256': hashlib.sha256(data).hexdigest(), 'checked_maps': checked,
                         'mutations': elf_mutations(data, pins) if not elf_errors and args.mutations else {}}
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n')
    for error in errors[:20]:
        print(f'FAIL {error["code"]}: {error["detail"]}')
    if errors:
        raise SystemExit(f'FAIL: {len(errors)} registry errors')
    print(f'PASS: {report["groups"]} groups; {report["map_slots"]} pinned IDs; '
          f'{report["linked_maps"]} linked maps; {len(report["mutations"])} mutations detected')
    print(f'Capacity: {report["signed_group_slots_remaining"]} signed group slots remain; '
          f'minimum per-group headroom {report["smallest_group_headroom"]} '
          f'({report["smallest_linked_group_headroom"]} among linked groups)')
    if 'elf' in report:
        print(f'ELF PASS: {report["elf"]["checked_maps"]} original header symbols; '
              f'{len(report["elf"]["mutations"])} pointer mutations detected')


if __name__ == '__main__':
    main()
