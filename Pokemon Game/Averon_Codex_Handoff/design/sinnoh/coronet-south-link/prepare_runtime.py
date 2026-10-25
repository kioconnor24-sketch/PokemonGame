#!/usr/bin/env python3
"""Reuse South donor geometry in a NEW isolated ten-map Coronet DEV batch."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = 'fb83410f6bbded89a9d99537d952698e80af4cf5'
ENGINE = 'Pokemon Game/engine/'
SOUTH = 'MtCoronet_1F_South'
UPPER = 'SinnohMtCoronet_2F'

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

upper = load('south_existing_upper', HERE.parent/'coronet-upper-floors/prepare_runtime.py')
assets = load('south_existing_assets', HERE.parent/'celestic-north/prepare_runtime.py')
reuse = load('south_existing_art', HERE.parent/'coronet-upper-floors/reuse_south_art.py')
base = upper.base
sha = upper.sha
encode = upper.encode
MAPS = {**upper.MAPS, SOUTH: (42, 32)}


def words(data):
    return list(struct.unpack('<%dH' % (len(data)//2), data))


def assemble(repo):
    repo = Path(repo).resolve()
    files, receipt = upper.assemble(repo)
    # The new main differs only in opt-in QA; never silently use other engine data.
    if base.git(repo, 'rev-parse', 'HEAD:'+ENGINE.rstrip('/')).strip() != base.git(repo, 'rev-parse', BASE+':'+ENGINE.rstrip('/')).strip():
        raise ValueError('exact current baseline required')
    original_raw, original_border, original_header, source_attrs = reuse.south_source()
    art = HERE.parent/'coronet-upper-floors/reused-south-art'
    inventory = json.loads((art/'inventory.json').read_text())
    for path, entry in inventory.items():
        expected = entry['sha256'] if isinstance(entry, dict) else entry
        if sha((art/path).read_bytes()) != expected:
            raise ValueError('reused art hash differs: '+path)
    raw = words((art/SOUTH/'averon-map.bin').read_bytes())
    original = words(original_raw)
    primary = words((art/'cave-family/primary-attributes.bin').read_bytes())
    secondary = words((art/'cave-family/secondary-attributes.bin').read_bytes())
    attrs = primary + secondary
    if len(raw) != 42*32 or len(primary) != 512:
        raise ValueError('existing South dimensions/bank differ')
    for a, b in zip(original, raw):
        if (a & 0xfc00) != (b & 0xfc00) or attrs[b & 1023] != source_attrs[str(a & 1023)]:
            raise ValueError('South physics or full attributes differ')
    if attrs[raw[2*42+29] & 1023] != 0x1061 or raw[2*42+29] & 0xc00:
        raise ValueError('actual South ladder29,2 required')
    # Neutralized donor exits have no reciprocal world yet: seal only those cells.
    closures = [(5, 7), (36, 20)]
    for x, y in closures:
        raw[y*42+x] = 0x0c00 | 513  # native cave wall in isolated bank (verified below)
    if attrs[513] & 0xff != 0:
        raise ValueError('unexpected stock wall behavior')
    header = copy.deepcopy(original_header)
    header['region_map_section'] = 'MAPSEC_ROUTE_201'
    header['music'] = 'MUS_CAVE_OF_ORIGIN'
    header['allow_cycling'] = False; header['allow_escaping'] = False
    upper_header = json.loads(files[f'data/maps/{UPPER}/map.json'])
    old_upper_warps = copy.deepcopy(upper_header['warp_events'])
    upper_header['warp_events'].append(dict(x=27, y=48, elevation=0, dest_map=header['id'], dest_warp_id='0'))
    header['warp_events'] = [dict(x=29, y=2, elevation=0, dest_map=upper_header['id'], dest_warp_id=str(len(old_upper_warps)))]
    key = f'data/layouts/{UPPER}/map.bin'; grid = words(files[key]); before = list(grid)
    # Existing authored lower anchor: activate a native cave ladder, retain all old stairs.
    grid[48*34+27] = 0x3000 | upper.source.LADDER
    shape = list(grid)
    for y in range(47, 50):
        for x in range(26, 29):
            i=y*34+x
            if shape[i] & 0xc00:
                tile=521 if not shape[i+34]&0xc00 else 530 if not shape[i+1]&0xc00 else 528 if not shape[i-1]&0xc00 else upper.source.WALL
                grid[i]=(shape[i]&0xfc00)|tile
    changed = [(i%34, i//34) for i,(a,b) in enumerate(zip(before,grid)) if a!=b]
    if any((a&0xfc00)!=(b&0xfc00) and i!=48*34+27 for i,(a,b) in enumerate(zip(before,grid))):
        raise ValueError('unexpected upper collision/elevation changes')
    files[key] = struct.pack('<%dH'%len(grid),*grid)
    files[f'data/maps/{UPPER}/map.json'] = encode(upper_header)
    files[f'data/maps/{SOUTH}/map.json'] = encode(header)
    files[f'data/maps/{SOUTH}/scripts.inc'] = (SOUTH+'_MapScripts::\n\t.byte 0\n').encode()
    files[f'data/layouts/{SOUTH}/map.bin'] = struct.pack('<%dH'%len(raw),*raw)
    files[f'data/layouts/{SOUTH}/border.bin'] = (art/SOUTH/'averon-border.bin').read_bytes()
    # Metadata only; all graphics, palettes and callbacks alias stock native assets.
    symbols = {}
    for bank, secondary_bank, graphics in [('primary',False,'General'),('secondary',True,'Cave')]:
        symbol = 'CoronetSouth'+bank.title(); symbols[bank]='gTileset_'+symbol
        directory=f'data/tilesets/{bank}/coronet_south_dev/'
        records=(art/f'cave-family/{bank}-metatiles.bin').read_bytes()
        attr=(art/f'cave-family/{bank}-attributes.bin').read_bytes()
        if not records or len(records)%16 or len(records)>8192 or len(attr)*8!=len(records):
            raise ValueError('invalid isolated metadata bank')
        files[directory+'metatiles.bin']=records;files[directory+'metatile_attributes.bin']=attr
        def append(path,text):
            if path not in files: files[path]=base.verified_file(repo,Path(ENGINE)/path,'HEAD')
            files[path]+=text.encode()
        bindings=assets.asset_bindings(base.verified_file(repo,Path(ENGINE)/'src/data/tilesets/headers.h','HEAD').decode(),graphics)
        append('include/tilesets.h',f'\nextern const struct Tileset gTileset_{symbol};\n')
        append('src/data/tilesets/metatiles.h',f'\nconst u16 gMetatiles_{symbol}[] = INCBIN_U16("{directory}metatiles.bin");\nconst u16 gMetatileAttributes_{symbol}[] = INCBIN_U16("{directory}metatile_attributes.bin");\n')
        append('src/data/tilesets/headers.h',f'\nconst struct Tileset gTileset_{symbol} = {{ .isCompressed=TRUE, .isSecondary={"TRUE" if secondary_bank else "FALSE"}, .tiles={bindings["tiles"]}, .palettes={bindings["palettes"]}, .metatiles=gMetatiles_{symbol}, .metatileAttributes=gMetatileAttributes_{symbol}, .callback={bindings["callback"]} }};\n')
    groups=json.loads(files['data/maps/map_groups.json']); group=groups['group_order'].index('gMapGroup_Sinnoh')
    if len(groups['gMapGroup_Sinnoh'])!=28 or SOUTH in groups['gMapGroup_Sinnoh']:
        raise ValueError('unexpected inherited registry')
    groups['gMapGroup_Sinnoh'].append(SOUTH);files['data/maps/map_groups.json']=encode(groups)
    slots=files['test/data/averon_map_registry_slots.inc'].decode().replace(f'REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 28, 1)',f'REGISTRY_GROUP({group}, gMapGroup_Sinnoh, 29, 1)')
    files['test/data/averon_map_registry_slots.inc']=(slots+f'REGISTRY_SLOT({group}, 28, {header["id"]}, {SOUTH}, 1)\n').encode()
    layouts=json.loads(files['data/layouts/layouts.json'])
    if any(v['id']==header['layout'] for v in layouts['layouts']): raise ValueError('South layout already present')
    layouts['layouts'].append(dict(id=header['layout'],name=SOUTH+'_Layout',width=42,height=32,primary_tileset=symbols['primary'],secondary_tileset=symbols['secondary'],layout_version='emerald',border_filepath=f'data/layouts/{SOUTH}/border.bin',blockdata_filepath=f'data/layouts/{SOUTH}/map.bin'))
    files['data/layouts/layouts.json']=encode(layouts)
    files['data/event_scripts.s']+=f'\n\t.include "data/maps/{SOUTH}/scripts.inc"\n'.encode()
    del files['test/averon_coronet_upper_floors_runtime.c']
    files['test/averon_coronet_south_runtime.c']=(HERE/'native-runtime.c').read_bytes()
    receipt.update(base=BASE,temporary_map_slots={n:19+i for i,n in enumerate(MAPS)},source_headers={**receipt['source_headers'],UPPER:upper_header,SOUTH:header},lower_link=dict(south=[29,2],upper=[27,48],upper_appended_index=len(old_upper_warps),closed_donor_exits=closures,upper_changed_cells=changed),files={p:sha(v) for p,v in sorted(files.items())})
    return files,receipt


def install(repo):
    repo=Path(repo).resolve();engine=repo/ENGINE
    if not base.git(repo,'branch','--show-current').decode().strip().startswith('codex/coronet-south-runtime-') or not (engine/'.map_qa_throwaway').is_file():
        raise ValueError('marked South disposable branch required')
    if base.git(repo,'status','--porcelain','--untracked-files=normal','--',ENGINE).decode().splitlines() not in ([],['?? "Pokemon Game/engine/.map_qa_throwaway"']):
        raise ValueError('dirty engine refused')
    if base.git(repo,'rev-parse','HEAD').decode().strip()!=BASE:raise ValueError('exact current baseline required')
    files,receipt=assemble(repo)
    for path in files:
        target=(engine/path).resolve()
        if not target.is_relative_to(engine.resolve()):raise ValueError('output escapes engine')
        try:base.git(repo,'cat-file','-e','HEAD:'+ENGINE+path)
        except subprocess.CalledProcessError:
            if target.exists():raise ValueError('untracked output exists')
    for path,data in files.items():
        target=engine/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo',required=True,type=Path);p.add_argument('--install',action='store_true');a=p.parse_args()
    print(json.dumps(install(a.repo) if a.install else assemble(a.repo)[1],indent=2))
