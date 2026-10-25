#!/usr/bin/env python3
"""Reuse the existing donor South map through the existing northern cave art packer.

No geography, header, warp or shared General asset is reconstructed or edited.
The eight extra reviewed source roles are ocean-water records, not pixel matches.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
PACKER_PATH=HERE.parent/'celestic-north/adapt_cave_art.py'
SOUTH='MtCoronet_1F_South'
WATER={635,640,641,648,649,650,657,658}

def load_packer():
    p=PACKER_PATH
    s=importlib.util.spec_from_file_location('reuse_south_existing_cave',p)
    a=importlib.util.module_from_spec(s);s.loader.exec_module(a);return a

def south_source(root=ROOT):
    root=Path(root);facts=json.loads((HERE/'reuse-existing-south.json').read_text())
    for path,h in facts['staged_files_sha256'].items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest()!=h:raise ValueError('existing South source hash differs')
    folder=root/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/remaining-donor/staged'/SOUTH
    raw=(folder/'map.bin').read_bytes();border=(folder/'border.bin').read_bytes();header=json.loads((folder/'map.json').read_text());attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
    if len(raw)!=42*32*2 or len(border)!=8 or header['warp_events'] or any(header[k] for k in ('object_events','coord_events','bg_events','connections')):raise ValueError('neutral existing South packet required')
    if {int(k) for k in attrs if int(k)>=512}-load_packer().USED!=WATER or any(attrs[str(k)]!=0x1015 for k in WATER):raise ValueError('unreviewed South water role/full attributes')
    if struct.unpack_from('<H',raw,2*(2*42+29))[0]!=0x33a5 or attrs['933']!=0x1061:raise ValueError('existing South stair differs')
    return raw,border,header,attrs

def build(engine,out):
    a=load_packer();old_source=a.source;south=south_source()
    a.MAPS={**a.MAPS,SOUTH:(42,32)};a.USED=a.USED|WATER
    a.REPLACEMENTS={**a.REPLACEMENTS,**dict.fromkeys(WATER,161)}
    a.source=lambda name:south if name==SOUTH else old_source(name)
    # The existing packer independently hashes its staged inputs. Supply the
    # same files through a temporary view, rather than copying/rebuilding maps.
    with tempfile.TemporaryDirectory() as temp:
        view=Path(temp);(view/'staged').mkdir()
        for name in a.MAPS:
            source=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh'/('remaining-donor' if name==SOUTH else 'celestic-north')/'staged'/name
            (view/'staged'/name).symlink_to(source,target_is_directory=True)
        a.HERE=view
        result=a.build(engine,out)
    result['status']='REUSED_EXISTING_SOUTH_GEOGRAPHY_WITH_EXISTING_AVERON_ART_NOT_RUNTIME_ACCEPTANCE'
    result['south_source_dimensions']=[42,32];result['south_existing_stair']=[29,2]
    result['south_water_source_ids']=sorted(WATER);result['south_geometry_or_header_changes']=False
    result['limits']+=['Existing staged South reused byte-for-byte before art-only ID remap; all C/E and full behavior/layer words preserved','Eight explicit ocean-water roles use existing General161 water art with source0x1015 semantics,not raw-record visual equivalence','No South warp added or upper scene changed;2F lower seam still closed pending actual source/graphics/approach integration']
    out=Path(out);(out/'cave-art-receipt.json').write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('engine','out'):p.add_argument('--'+n,required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.engine,args.out),indent=2))
