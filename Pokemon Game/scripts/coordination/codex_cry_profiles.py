#!/usr/bin/env python3
"""Compare built RELEASE CRIES=on/off profiles without editing game inputs.

Run from any directory: codex_cry_profiles.py ENGINE --output FILE
Build both profiles first. Reports linked occupancy, hashes, source identity,
song-object equality and retained non-cry samples. No ROMs are published.
"""
import argparse
import json
from pathlib import Path
import subprocess
import codex_rom_capacity as capacity


def compare(on, off, on_songs, off_songs):
    if on['samples']['totals'].get('cries', {}).get('count', 0) <= 0:
        raise ValueError('ON image has no verified linked cries')
    if off['samples']['totals'].get('cries', {}).get('count', 0):
        raise ValueError('OFF image still contains linked cries')
    if not on_songs or on_songs != off_songs:
        raise ValueError('music/effect song objects missing or changed')
    def retained(inv):
        return {b['label']: (b['bytes'], b['sha256'])
                for b in inv['samples']['blobs'] if b['category'] != 'cries'}
    if not retained(on) or retained(on) != retained(off):
        raise ValueError('non-cry sound samples missing or changed')
    if on['song_names_sha256'] != off['song_names_sha256']:
        raise ValueError('linked music/effect symbol inventory changed')
    saving = on['linked_used_bytes'] - off['linked_used_bytes']
    if saving <= 0:
        raise ValueError('OFF profile did not save linked ROM bytes')
    return {'linked_saving_bytes': saving,
            'identical_song_objects': len(on_songs),
            'song_objects_sha256': capacity.sha(json.dumps(on_songs, sort_keys=True).encode()),
            'identical_noncry_samples': len(retained(on)),
            'on': on, 'off': off,
            'scope': 'BUILD/static byte proof; not gameplay, listening, or Delta acceptance'}


def songs(directory):
    return {str(p.relative_to(directory)): capacity.sha(p.read_bytes())
            for p in sorted((directory/'sound/songs').rglob('*.o'))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('engine', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    engine = args.engine.resolve()
    rows, objects = {}, {}
    for profile in ('on', 'off'):
        stem = engine/f'pokeemerald-cries-{profile}-release'
        rows[profile] = capacity.inventory(engine, stem.with_suffix('.elf'), stem.with_suffix('.gba'))
        objects[profile] = songs(engine/f'build/emerald-cries-{profile}-release')
    result = compare(rows['on'], rows['off'], objects['on'], objects['off'])
    result['source_commit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=engine, text=True).strip()
    result['source_status'] = subprocess.check_output(['git', 'status', '--short', '--', '.'], cwd=engine, text=True).splitlines()
    result['engine_tree'] = subprocess.check_output(['git', 'rev-parse', 'HEAD:Pokemon Game/engine'], cwd=engine, text=True).strip()
    result['commands'] = ['make -j8 -O RELEASE=1 CRIES=on', 'make -j8 -O RELEASE=1 CRIES=off']
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(f"Saved {result['linked_saving_bytes']} linked bytes; "
          f"{result['identical_song_objects']} identical song objects; "
          f"{result['identical_noncry_samples']} identical other sound samples")


if __name__ == '__main__':
    main()
