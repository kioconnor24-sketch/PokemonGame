#!/usr/bin/env python3
"""Parse real Emerald Expansion linker memory budgets after native make.

All usage numbers come from the linker's --print-memory-usage output. The
generated report is informational; it never assumes future Sinnoh content fits.
Optional comparisons require the same caller-labeled build profile and memory
capacities. Profile/revision labels do not verify how either build was made.
"""
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

MEMORY = re.compile(
    r"^\s*(EWRAM|IWRAM|ROM):\s+(\d+)\s+B\s+(\d+)\s+(KB|MB)\s+([\d.]+)%\s*$",
    re.M,
)
REGIONS = {"ROM", "EWRAM", "IWRAM"}
REPORT_SCOPE = "Native build and linker footprints, not game runtime"
LABEL_SCOPE = "Caller-supplied labels; build configuration and source revision are not verified"
ROM_BASE = 0x08000000


def verify_linked_rom(elf, rom, used_bytes, capacity_bytes):
    """Bind this ARM ELF's ROM load image and extent to the ROM/linker log.

    Zero-file-size BSS segments are not ROM data. Padding and gaps are not
    claimed as ELF-verified bytes; the full ROM checksum still identifies them.
    This does not authenticate caller profile/source labels or RAM measurements.
    """
    if len(elf) < 52 or elf[:7] != b'\x7fELF\x01\x01\x01':
        raise ValueError('Expected a complete little-endian ELF32 ARM executable')
    fields = struct.unpack_from('<HHIIIIIHHHHHH', elf, 16)
    kind, machine, version, _, phoff, _, _, ehsize, phsize, phnum, _, _, _ = fields
    if (kind, machine, version, ehsize, phsize) != (2, 40, 1, 52, 32) or not phnum:
        raise ValueError('Unsupported ELF executable/program-header contract')
    if phoff < 52 or phoff + phsize * phnum > len(elf):
        raise ValueError('Truncated ELF program-header table')
    segments = []
    for index in range(phnum):
        ptype, offset, _, address, size, memsize, _, _ = struct.unpack_from('<IIIIIIII', elf, phoff + index * phsize)
        if ptype != 1 or not size:
            continue
        if size > memsize or offset + size > len(elf):
            raise ValueError('Truncated/invalid ELF load segment')
        start = address - ROM_BASE
        end = start + size
        if start < 0 or end > capacity_bytes or end > len(rom):
            raise ValueError('ELF load segment outside supplied ROM/capacity')
        if elf[offset:offset + size] != rom[start:end]:
            raise ValueError(f'ELF and ROM load bytes differ at segment {index}')
        segments.append((start, end))
    segments.sort()
    if not segments or segments[0][0] != 0:
        raise ValueError('ELF has no ROM load image starting at the cartridge base')
    if any(left[1] > right[0] for left, right in zip(segments, segments[1:])):
        raise ValueError('Overlapping ELF ROM load segments')
    extent = segments[-1][1]
    if extent != used_bytes:
        raise ValueError(f'ELF linked ROM extent {extent} differs from linker log {used_bytes}')
    return dict(elf_sha256=hashlib.sha256(elf).hexdigest(), rom_sha256=hashlib.sha256(rom).hexdigest(),
                matched_load_segments=len(segments), matched_load_bytes=sum(end - start for start, end in segments),
                linked_rom_extent_bytes=extent,
                scope='ROM load bytes and linker ROM extent verified; gaps/padding, RAM, caller source/profile and gameplay are not certified')


def parse_memory(log_text):
    entries = MEMORY.findall(log_text)
    latest = {}
    for name, used, capacity, unit, reported_percent in entries:
        maximum = int(capacity) * (1024 if unit == "KB" else 1024 * 1024)
        value = int(used)
        if value < 0 or maximum <= 0 or value > maximum:
            raise ValueError(f"Out-of-bounds {name} usage: {value}/{maximum}")
        latest[name] = {
            "used_bytes": value,
            "capacity_bytes": maximum,
            "remaining_bytes": maximum - value,
            "used_percent": round(100 * value / maximum, 2),
            "linker_reported_percent": float(reported_percent),
        }
    if set(latest) != {"ROM", "EWRAM", "IWRAM"}:
        raise ValueError("Missing real linker memory regions: " +
                         ", ".join(sorted(set(("ROM", "EWRAM", "IWRAM")) - set(latest))))
    for name, values in latest.items():
        if abs(values["used_percent"] - values["linker_reported_percent"]) > .02:
            raise ValueError("Inconsistent linker usage percentage for " + name)
    return latest


def build_labels(profile=None, source_revision=None):
    labels = {}
    for name, value in (("profile", profile), ("source_revision", source_revision)):
        if value is not None:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a nonempty caller-supplied label")
            labels[name] = value.strip()
    if labels:
        labels["scope"] = LABEL_SCOPE
    return labels


def compare_baseline(current, baseline):
    """Compare linker usage only, rejecting incomplete/incompatible reports."""
    profile = current.get("build_labels", {}).get("profile")
    if not profile:
        raise ValueError("Baseline comparison requires a nonempty current profile")
    if not isinstance(baseline, dict) or baseline.get("scope") != REPORT_SCOPE:
        raise ValueError("Malformed baseline: expected a resource-budget report object")
    labels = baseline.get("build_labels")
    if not isinstance(labels, dict):
        raise ValueError("Baseline comparison requires a nonempty baseline profile")
    baseline_labels = build_labels(labels.get("profile"), labels.get("source_revision"))
    if not baseline_labels.get("profile"):
        raise ValueError("Baseline comparison requires a nonempty baseline profile")
    if baseline_labels["profile"] != profile:
        raise ValueError("Baseline profile differs from current profile")
    memory = baseline.get("memory")
    if not isinstance(memory, dict) or set(memory) != REGIONS:
        raise ValueError("Malformed baseline: expected ROM, EWRAM and IWRAM memory regions")
    changes = {}
    for name, current_row in current["memory"].items():
        row = memory[name]
        if not isinstance(row, dict):
            raise ValueError(f"Malformed baseline: invalid {name} memory row")
        for field in ("used_bytes", "capacity_bytes", "remaining_bytes"):
            if type(row.get(field)) is not int:
                raise ValueError(f"Malformed baseline: {name} {field} must be an integer")
        used, capacity = row["used_bytes"], row["capacity_bytes"]
        if capacity <= 0 or not 0 <= used <= capacity or row["remaining_bytes"] != capacity - used:
            raise ValueError(f"Malformed baseline: inconsistent {name} memory bytes")
        for field in ("used_percent", "linker_reported_percent"):
            value = row.get(field)
            if (type(value) not in (int, float) or not 0 <= value <= 100
                    or abs(round(100 * used / capacity, 2) - value) > .02):
                raise ValueError(f"Malformed baseline: inconsistent {name} {field}")
        if capacity != current_row["capacity_bytes"]:
            raise ValueError(f"Baseline {name} capacity differs from current capacity")
        changes[name] = {"baseline_used_bytes": used,
                         "used_bytes_delta": current_row["used_bytes"] - used}
    return {"scope": "Signed linker used-byte changes; ROM artifact padding is excluded",
            "baseline_labels": baseline_labels, "memory": changes}



def linked_inputs(map_text, used_bytes, capacity_bytes):
    """Stable named ROM-VMA inputs only; discard/LTO/RAM/alignment stay residual."""
    marker = 'Linker script and memory map'
    if marker not in map_text:
        raise ValueError('Missing GNU linker memory-map body')
    rows, pending = {}, None
    for line in map_text.split(marker, 1)[1].splitlines():
        match = re.fullmatch(r' (\.[^\s]+)\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s+(.+\.o(?:\))?)', line.rstrip())
        if not match and pending:
            match = re.fullmatch(r'\s+(0x[0-9a-fA-F]+)\s+(0x[0-9a-fA-F]+)\s+(.+\.o(?:\))?)', line.rstrip())
            values = (pending, *match.groups()) if match else None
        else:
            values = match.groups() if match else None
        pending = line.strip() if re.fullmatch(r' \.[^\s]+', line) else None
        if not values:
            continue
        section, address, size, obj = values
        address, size = int(address, 16), int(size, 16)
        if not size or not 0x08000000 <= address < 0x08000000 + capacity_bytes:
            continue
        if address + size > 0x08000000 + used_bytes:
            raise ValueError('Map input extends beyond the reported linked ROM usage')
        # LTO repartitions and temporary absolute paths are not stable source
        # attribution. Avoid presenting changed partition names as new assets.
        if obj.startswith(('/', '\\')) or '.ltrans' in obj or re.match(r'[A-Za-z]:', obj):
            continue
        obj = re.sub(r'^build/[^/]+/', '', obj)
        rows[obj] = rows.get(obj, 0) + size
    if not rows:
        raise ValueError('No stable linked ROM input objects found')
    total = sum(rows.values())
    if total > used_bytes:
        raise ValueError('Input contributions exceed linked ROM usage')
    return {'format': 1, 'map_text_sha256': hashlib.sha256(map_text.encode()).hexdigest(),
            'scope': 'Partial named ROM-VMA inputs; LTO, absolute toolchain paths, initialized RAM loads and padding are not attributed',
            'objects': dict(sorted(rows.items())), 'attributed_bytes': total,
            'unattributed_bytes': used_bytes - total}


def contribution_changes(current, previous):
    def checked(row):
        if not isinstance(row, dict) or type(row.get('format')) is not int or row['format'] != 1 or not isinstance(row.get('objects'), dict):
            raise ValueError('Malformed linker input inventory')
        if not row['objects'] or any(not isinstance(k, str) or type(v) is not int or v < 0 for k, v in row['objects'].items()):
            raise ValueError('Malformed linker object bytes')
        if row.get('attributed_bytes') != sum(row['objects'].values()) or type(row.get('unattributed_bytes')) is not int or row['unattributed_bytes'] < 0:
            raise ValueError('Malformed linker contribution totals')
        return row['objects']
    now, before = checked(current), checked(previous)
    rows = [{'object': name, 'baseline_bytes': before.get(name, 0), 'bytes': now.get(name, 0),
             'delta_bytes': now.get(name, 0) - before.get(name, 0)}
            for name in sorted(now.keys() | before.keys()) if now.get(name, 0) != before.get(name, 0)]
    rows.sort(key=lambda row: (-abs(row['delta_bytes']), row['object']))
    return {'changed_objects': rows,
            'attributed_delta_bytes': current['attributed_bytes'] - previous['attributed_bytes'],
            'unattributed_delta_bytes': current['unattributed_bytes'] - previous['unattributed_bytes'],
            'scope': 'Partial contributions; residual changes are not claimed as content savings'}

def report(log_text, rom=None, *, profile=None, source_revision=None, baseline=None, linker_map=None, elf=None):
    metadata = {"scope": REPORT_SCOPE,
                "memory": parse_memory(log_text)}
    labels = build_labels(profile, source_revision)
    if labels:
        metadata["build_labels"] = labels
    if baseline is not None:
        metadata["comparison"] = compare_baseline(metadata, baseline)
    if linker_map is not None:
        rom_memory = metadata['memory']['ROM']
        metadata['linker_inputs'] = linked_inputs(linker_map, rom_memory['used_bytes'], rom_memory['capacity_bytes'])
        if baseline is not None and 'linker_inputs' in baseline:
            metadata['comparison']['contributions'] = contribution_changes(metadata['linker_inputs'], baseline['linker_inputs'])
            previous = baseline['linker_inputs']
            if previous['attributed_bytes'] + previous['unattributed_bytes'] != baseline['memory']['ROM']['used_bytes']:
                raise ValueError('Baseline contributions do not match its linked ROM usage')
    if rom is not None:
        path = Path(rom)
        digest = hashlib.sha256()
        length = 0
        with path.open("rb") as fp:
            for chunk in iter(lambda: fp.read(1024 * 1024), b""):
                digest.update(chunk)
                length += len(chunk)
        if length <= 0 or length > metadata["memory"]["ROM"]["capacity_bytes"]:
            raise ValueError("ROM binary size outside GBA address space")
        metadata["rom_artifact"] = {"size_bytes": length, "sha256": digest.hexdigest()}
    if elf is not None:
        if rom is None:
            raise ValueError('ELF verification requires --rom')
        memory = metadata['memory']['ROM']
        verified = verify_linked_rom(Path(elf).read_bytes(), Path(rom).read_bytes(),
                                     memory['used_bytes'], memory['capacity_bytes'])
        if verified['rom_sha256'] != metadata['rom_artifact']['sha256']:
            raise ValueError('ROM changed while reporting; rebuild a coherent artifact set')
        metadata['linked_artifact_verification'] = verified
    return metadata


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log", required=True, type=Path)
    ap.add_argument("--rom", type=Path)
    ap.add_argument("--elf", type=Path, help="Optional matching ARM ELF: verify ROM load bytes and linker ROM extent")
    ap.add_argument("--linker-map", type=Path, help="Optional matching GNU .map for partial named-object contributions")
    ap.add_argument("--json", required=True, type=Path)
    ap.add_argument("--profile", help="Caller label for the exact build configuration; not verified")
    ap.add_argument("--source-revision", help="Caller source revision label; not verified")
    ap.add_argument("--baseline", type=Path,
                    help="Previous JSON report with matching nonempty profile and capacities")
    args = ap.parse_args()
    try:
        baseline = None
        if args.baseline is not None:
            baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
            if baseline is None:
                raise ValueError("Malformed baseline: expected a resource-budget report object")
        result = report(args.log.read_text(encoding="utf-8", errors="replace"), args.rom,
                        profile=args.profile, source_revision=args.source_revision, baseline=baseline,
                        linker_map=args.linker_map.read_text() if args.linker_map else None, elf=args.elf)
    except (OSError, ValueError) as exc:
        ap.error(str(exc))
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for name, row in result["memory"].items():
        print(f"{name}: {row['used_bytes']} / {row['capacity_bytes']} bytes "
              f"({row['used_percent']:.2f}% used, {row['remaining_bytes']} bytes free)")
    if "rom_artifact" in result:
        print("ROM SHA-256: " + result["rom_artifact"]["sha256"])
    if "build_labels" in result:
        print(LABEL_SCOPE)
    if "comparison" in result:
        for name, row in result["comparison"]["memory"].items():
            print(f"{name}: linked usage change {row['used_bytes_delta']:+d} bytes")
        contributions = result['comparison'].get('contributions')
        if contributions:
            for row in contributions['changed_objects'][:10]:
                print(f"ROM input {row['object']}: {row['delta_bytes']:+d} bytes")
            print(f"ROM unattributed change: {contributions['unattributed_delta_bytes']:+d} bytes (includes LTO/padding)")


if __name__ == "__main__":
    main()
