#!/usr/bin/env python3
"""One isolated existing-Averon art family for the five staged central outdoors.

Reuses pack_art; source cells, headers, full behavior/layer words and elevations
are immutable. Donor pixels/palettes are neither read nor emitted by this tool.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('central_outdoor_pack',HERE.parent/'oreburgh-donor/build_city_family.py')
pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
MAPS={'HearthomeCity':(58,52),'Route208':(68,38),'Route209':(68,72),
      'SolaceonTown':(66,44),'Route210_South':(42,94)}
# Destination source-envelope, then existing Rustboro facade. Inclusive endpoint
# resampling preserves the bounding footprint rather than installing new maps.
HOUSE=(31,15,5,5);CENTER=(15,35,4,4);MART=(14,42,5,4);DEVON=(6,7,12,9)
FACADES={
 'HearthomeCity':[((24,6,11,7),DEVON),((12,15,5,5),CENTER),((18,17,5,3),HOUSE),
  ((34,14,5,6),HOUSE),((46,16,8,4),(24,15,7,5)),((7,24,7,8),DEVON),
  ((19,28,5,3),HOUSE),((26,27,4,4),MART),((36,27,5,4),HOUSE),((42,24,5,7),HOUSE),
  ((6,0,6,7),HOUSE),((48,0,6,7),HOUSE),((0,42,5,5),HOUSE),((53,42,5,5),HOUSE)],
 'Route208':[((55,12,5,3),HOUSE),((63,21,5,5),HOUSE)],
 'Route209':[((60,5,4,13),DEVON),((0,59,5,5),HOUSE)],
 'SolaceonTown':[((9,9,5,3),HOUSE),((22,10,4,3),HOUSE),((36,13,4,4),HOUSE),
  ((22,20,5,5),CENTER),((28,22,4,3),HOUSE),((38,21,4,3),HOUSE),((28,30,4,4),MART)],
 'Route210_South':[((28,44,5,4),HOUSE)]}
SECONDARY={
 'Route208':{925:107,926:113,927:114,932:1,933:121,934:123,943:33,951:33,
  952:256,953:470,954:471,955:478,959:33,960:1,967:33},
 'Route209':{527:257,534:312,535:256,542:265,543:266,549:312,550:1,
  557:107,559:121,565:123,566:125,567:427,573:368,574:376,581:384,582:392,
  583:428,590:400,591:408,599:428,606:427,607:428,611:428,619:428,
  644:289,645:225,652:289,653:225,660:225,661:225,668:225,669:225,
  697:1,698:1,704:312,705:313,706:314,712:225,713:225,714:225,720:225,
  721:225,722:225,728:225,729:225,730:225,731:225,732:225,733:225,736:225,738:225},
 'Route210_South':{516:13,647:13,654:107,655:281,662:123,663:470,670:479,
  671:1,676:478,677:24,678:25,679:26,684:478,685:24,686:25,687:26,
  692:1,693:19,694:19,708:19,709:19,710:19,711:19,717:256,718:257,719:258}}
WHITE={536,537,538,539,544,545,546,547,550,551,552,553,554,556,557,558,560,561,562,563,
       564,565,566,568,569,571,572,573,576,577,579,580,581}
HEDGE={540:704,541:704,542:704,543:704,548:462,549:463,559:471}
PRIMARY={171:175,172:207,147:175,148:175,155:175,156:175,163:175,164:175,267:1,268:1,269:1}


def source(name):
    folder=HERE/'staged'/name;w,h=MAPS[name]
    raw=(folder/'map.bin').read_bytes();border=(folder/'border.bin').read_bytes()
    header=json.loads((folder/'map.json').read_text())
    attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
    if len(raw)!=w*h*2 or len(border)!=8:raise ValueError('source dimensions changed')
    if header['region_map_section']!='MAPSEC_PENDING_OWNER' or any(header[k] for k in ('object_events','coord_events','bg_events')):
        raise ValueError('neutral off-engine stage required')
    if any(not 0<=int(mid)<1024 or type(value) is not int or not 0<=value<=65535 for mid,value in attrs.items()):
        raise ValueError('invalid full source attribute word')
    return raw,border,header,attrs


def desired_art(name,raw,border,header,attrs,banks,stock):
    w,h=MAPS[name]
    if len(raw)!=w*h*2 or len(border)!=8 or len(stock)!=2400:raise ValueError('art dimensions changed')
    desired=[]
    used={cell[0]&1023 for cell in struct.iter_unpack('<H',raw+border)}
    if set(map(int,attrs))!=used:raise ValueError('source used attribute coverage changed')
    if name in SECONDARY and {mid for mid in used if mid>=512}!=set(SECONDARY[name]):
        raise ValueError('unreviewed secondary dependency')
    for (cell,) in struct.iter_unpack('<H',raw+border):
        mid=cell&1023
        if mid<512:target=PRIMARY.get(mid,mid)
        elif name in SECONDARY:target=SECONDARY[name][mid]
        elif name=='HearthomeCity':
            # Gold pavers, pale street and planted edging; every foreign
            # architectural envelope is subsequently replaced by a facade.
            target=HEDGE.get(mid,256 if mid in WHITE else 699 if mid<=530 else 1)
        elif name=='SolaceonTown':target=1
        else:raise ValueError('unreviewed source map')
        b,i=divmod(target,512);art=pack.words(banks[b],i)
        if (name=='Route208' and mid in (943,951,959,967)) or (name=='Route209' and mid in (565,566,567,573,574,581,582,583,590,591,599,606,607,611,619)):
            wood=pack.words(banks[1],528-512)
            art=tuple(wood[i] for i in (1,1,3,3,5,5,7,7))
        desired.append(art)
    for (dx,dy,dw,dh),(sx,sy,sw,sh) in FACADES[name]:
        if min(dx,dy,sx,sy)<0 or min(dw,dh,sw,sh)<1 or dx+dw>w or dy+dh>h or sx+sw>40 or sy+sh>60:
            raise ValueError('facade outside source footprint')
        if (sx,sy,sw,sh)==CENTER:
            # Preserve the real 4x4 Center facade instead of duplicating its
            # curved roof row when fitting the donor's 5x5 envelope.
            for yy in range(dy,dy+dh):
                for xx in range(dx,dx+dw):desired[yy*w+xx]=pack.words(banks[0],1)
            dx+=(dw-sw)//2;dy+=dh-sh;dw=sw;dh=sh
        for y in range(dh):
            for x in range(dw):
                mid=stock[(sy+y*(sh-1)//max(1,dh-1))*40+sx+x*(sw-1)//max(1,dw-1)]&1023
                b,i=divmod(mid,512);desired[(dy+y)*w+dx+x]=pack.words(banks[b],i)
    # The donor's southern unbuilt Route212 gateway is clipped by this map's
    # bottom edge. Show its already-closed envelope as a neutral stock rail,
    # rather than leaving foreign roof fragments at that closed boundary.
    if name=='HearthomeCity':
        for y in range(47,52):
            for x in range(6,12):desired[y*w+x]=pack.words(banks[0],312)
    # Retained gateways are visibly marked exactly at their source anchors;
    # unavailable building doors remain collision-closed in the original data.
    for warp in header['warp_events']:
        x,y=warp['x'],warp['y']
        if not (0<=x<w and 0<=y<h):raise ValueError('gateway outside source footprint')
        desired[y*w+x]=pack.words(banks[0],207)
    return desired


def build(engine,out):
    engine,out=Path(engine).resolve(),Path(out).resolve()
    if out.exists() or out.is_relative_to(engine) or 'engine' in out.parts:raise ValueError('new off-engine output required')
    base=pack.accepted.base;dual=pack.accepted.dual
    root=Path(base.git(engine,'rev-parse','--show-toplevel').decode().strip());rev=base.git(engine,'rev-parse','HEAD').decode().strip();assets={}
    def read(path):
        data=base.verified_file(root,engine.relative_to(root)/path,rev);assets[path]=base.sha(data);return data
    paths=['data/tilesets/primary/general/','data/tilesets/secondary/rustboro/']
    stock_banks=[read(p+'metatiles.bin') for p in paths];pa=read(paths[0]+'metatile_attributes.bin')
    if len(stock_banks[0])!=8192 or len(pa)!=1024:raise ValueError('primary capacity contract changed')
    stock=struct.unpack('<2400H',read('data/layouts/RustboroCity/map.bin'))
    images=[dual.indexed(read(p+'tiles.png')) for p in paths]
    secondary=sa=b'';result={};hashes={};verified=0;heights={}
    for name,(w,h) in MAPS.items():
        raw,border,header,attrs=source(name)
        hashes[name]={p:base.sha((HERE/'staged'/name/p).read_bytes()) for p in ('map.bin','border.bin','map.json','attributes.json')}
        source_attrs=[bytearray(1024),bytearray(1024)]
        for mid,value in attrs.items():b,i=divmod(int(mid),512);struct.pack_into('<H',source_attrs[b],i*2,value)
        wanted=desired_art(name,raw,border,header,attrs,stock_banks,stock)
        adapted,secondary,sa=pack.pack_art(raw+border,wanted,source_attrs,stock_banks[0],pa,secondary,sa)
        for (old,),(new,) in zip(struct.iter_unpack('<H',raw+border),struct.iter_unpack('<H',adapted)):
            b,i=divmod(new&1023,512)
            if old&0xFC00!=new&0xFC00 or pack.attribute((pa,sa)[b],i)!=attrs[str(old&1023)]:
                raise ValueError('source physics/full behavior/layer changed')
            verified+=1
        heights[name]=sum(cell[0]>>12==15 for cell in struct.iter_unpack('<H',raw))
        result[name]=(adapted[:len(raw)],adapted[len(raw):])
    if heights['Route208']!=58:raise ValueError('source bridge elevation15 changed')
    # Validate every final shared-bank dependency before creating any output.
    banks=[stock_banks[0],secondary];dependencies={};previews={}
    for name,(raw,border) in result.items():
        dependencies[name]=dual.closure(raw+border,banks,images)
        palettes={i:base.palette(read(paths[i>=6]+'palettes/%02d.pal'%i)) for i in dependencies[name]['palettes']}
        previews[name]=dual.render(raw,banks,images,palettes,*MAPS[name])
    out.mkdir(parents=True);(out/'outdoor-family').mkdir()
    for name,(raw,border) in result.items():
        folder=out/name;folder.mkdir();(folder/'averon-map.bin').write_bytes(raw);(folder/'averon-border.bin').write_bytes(border);previews[name].save(folder/'averon.png')
    for name,data in [('primary-metatiles',banks[0]),('primary-attributes',pa),('secondary-metatiles',secondary),('secondary-attributes',sa)]:
        (out/'outdoor-family'/(name+'.bin')).write_bytes(data)
    receipt=dict(status='EXISTING_AVERON_CENTRAL_OUTDOOR_ART_NOT_RUNTIME_ACCEPTANCE',engine_source=rev,
        existing_averon_sha256=assets,source_sha256=hashes,source_headers_and_gate_art_unchanged=True,
        verified_physics_behavior_cells=verified,elevation15_preserved=heights,primary_records=512,
        secondary_records=len(secondary)//16,remaining_secondary_slots=512-len(secondary)//16,
        dependencies=dependencies,facades=FACADES,secondary_remap=SECONDARY,primary_remap=PRIMARY,
        limits=['Existing Rustboro facades resampled into source envelopes; no donor pixels/palettes/music',
               'Neutral facades replace contest hall, cathedral and tower; no services, lore or interiors introduced',
               'Existing wood replaces donor rope/yellow bridge art; original collision/elevation/full attributes survive',
               'Grass replaces brown soil and foreign structure remnants; stock tree colors and shadows differ',
               'Source art only: no ROM/native/mGBA/bridge sprite-priority/production/save acceptance or permanent origins'])
    (out/'outdoor-art-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('engine','out'):p.add_argument('--'+n,required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(args.engine,args.out),indent=2))
