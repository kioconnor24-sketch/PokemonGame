#!/usr/bin/env python3
"""Existing-Averon City/207 family; source-only, no production ID allocation.

The geometry is merged204, mine art is merged198, and Route207 metadata is
reviewable205 at its pinned commit. Only existing Averon pixels/palettes render.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('oreburgh_accepted',HERE/'build_oreburgh.py')
accepted=importlib.util.module_from_spec(spec)
spec.loader.exec_module(accepted)
ROUTE_ART='920cf050e4a79f4899ff86539540cb0efcadfe3e'
ROUTE_PATH='Pokemon Game/Averon_Codex_Handoff/design/sinnoh/oreburgh-donor/corridor/Route207/'


def words(records,index):
    if len(records)%16 or not 0<=index<len(records)//16:
        raise ValueError('metatile record outside bank')
    return tuple(struct.unpack_from('<8H',records,index*16))


def attribute(attrs,index):
    if len(attrs)%2 or not 0<=index<len(attrs)//2:
        raise ValueError('attribute outside bank')
    return struct.unpack_from('<H',attrs,index*2)[0]


def pack_art(raw, desired, source_attrs, primary, primary_attrs, secondary, secondary_attrs):
    """Select existing records or append deduplicated art+attribute pairs.

    Per-cell graphics may change; source collision/elevation and full behavior/
    layer words may not. This is art packing, not another donor binary converter.
    """
    if (len(raw)%2 or len(desired)!=len(raw)//2 or len(primary)!=8192
            or len(primary_attrs)!=1024 or len(secondary)%16
            or len(secondary_attrs)*8!=len(secondary) or len(secondary)>8192):
        raise ValueError('invalid map/art/bank dimensions')
    lookup={}
    for bank,(records,attrs) in enumerate(((primary,primary_attrs),(secondary,secondary_attrs))):
        for i in range(len(records)//16):
            lookup.setdefault((words(records,i),attribute(attrs,i)),bank*512+i)
    records,attrs=bytearray(secondary),bytearray(secondary_attrs)
    result=[]
    for (cell,),wanted in zip(struct.iter_unpack('<H',raw),desired):
        if len(wanted)!=8 or any(type(w) is not int or not 0<=w<=65535 for w in wanted):
            raise ValueError('invalid requested art words')
        bank,i=divmod(cell&1023,512)
        original=attribute(source_attrs[bank],i)
        key=(tuple(wanted),original)
        target=lookup.get(key)
        if target is None:
            if len(records)//16>=512:
                raise ValueError('secondary metatile capacity exceeded')
            target=512+len(records)//16
            records.extend(struct.pack('<8H',*wanted));attrs.extend(struct.pack('<H',original))
            lookup[key]=target
        result.append((cell&0xFC00)|target)
    return struct.pack('<%dH'%len(result),*result),bytes(records),bytes(attrs)


def compact_warps(city, b1, b2, gate):
    """Prove a coupled source-index translation; keep ALL six mine events."""
    accepted.mine_warps(b1,b2)
    if len(city) != 15 or [(w['x'],w['y'],w['elevation']) for w in city[11:15]] != [(50,57,0),(51,57,0),(52,57,0),(53,57,0)]:
        raise ValueError('City mine anchor contract changed')
    source_ids=(0,11,12,13,14)
    if len(city)!=15 or len(gate)!=2:
        raise ValueError('source warp array contract changed')
    translation={old:new for new,old in enumerate(source_ids)}
    c=[dict(city[i]) for i in source_ids]
    a,b,g=[dict(w) for w in b1],[dict(w) for w in b2],[dict(w) for w in gate]
    for w in a[:2]:
        old=int(w['dest_warp_id'])
        if old not in (11,14):raise ValueError('unreviewed City return index')
        w['dest_warp_id']=str(translation[old])
    maps={'MAP_OREBURGH_CITY':c,'MAP_OREBURGH_MINE_B1F':a,'MAP_OREBURGH_MINE_B2F':b,
          'MAP_OREBURGH_GATE_1F':g}
    for name,events in maps.items():
        for w in events:
            if w['dest_map'] in maps and not 0<=int(w['dest_warp_id'])<len(maps[w['dest_map']]):
                raise ValueError('invalid coupled destination warp')
    if (g[1]['x'],g[1]['y'],g[1]['elevation'],g[1]['dest_map'],str(g[1]['dest_warp_id']))!=(25,20,0,'MAP_OREBURGH_CITY','0'):
        raise ValueError('Gate east/City return mismatch')
    if any(w['dest_map']!='MAP_OREBURGH_MINE_B1F' for w in c[1:]):
        raise ValueError('unreviewed retained City destination')
    if (c[0]['x'],c[0]['y'],c[0]['dest_map'],str(c[0]['dest_warp_id']))!=(6,12,'MAP_OREBURGH_GATE_1F','1'):
        raise ValueError('City/Gate entrance mismatch')
    if [int(w['dest_warp_id']) for w in c[1:]]!=[0,0,1,1]:
        raise ValueError('City wide mine entrance mismatch')
    return dict(scope='OFF_ENGINE_COUPLED_INDEX_PLAN_NO_SAVED_IDS',
        city_source_to_candidate=translation,events=maps,
        source_city_return_ids=[11,14],candidate_city_return_ids=[1,4],
        b1_event_count_preserved=6,b1_four_downstairs_and_b2_return2_unchanged=True,
        section=None,gate_status='RESTORE_EAST_ONLY_IN_COHERENT_DISPOSABLE_CANDIDATE')


def stamp(desired, raw, stock, banks, rectangle, destination, width=70):
    """Existing facade art within a source footprint, preserving source physics."""
    sx,sy,sw,sh=rectangle;dx,dy,dw,dh=destination
    if min(sx,sy,dx,dy)<0 or min(sw,sh,dw,dh)<1 or sx+sw>40 or sy+sh>60 or dx+dw>width or (dy+dh)*width>len(desired):
        raise ValueError('facade footprint outside map')
    for y in range(dh):
        for x in range(dw):
            source=stock[(sy+min(sh-1,y*sh//dh))*40+sx+min(sw-1,x*sw//dw)]
            i=(dy+y)*width+dx+x
            # These are reviewed source building envelopes; retain source C/E
            # even where its roof art is nonblocking, rather than transplanting physics.
            bank,mid=divmod(source&1023,512)
            desired[i]=words(banks[bank],mid)


def build(donor,engine,out):
    donor,engine,out=map(lambda p:Path(p).resolve(),(donor,engine,out))
    if out.exists() or 'engine' in out.parts or out.is_relative_to(donor):
        raise ValueError('new off-engine/off-donor output required')
    if accepted.base.git(donor,'rev-parse','HEAD').decode().strip()!=accepted.REVISION:
        raise ValueError('wrong donor revision')
    root=Path(accepted.base.git(engine,'rev-parse','--show-toplevel').decode().strip())
    rev=accepted.base.git(engine,'rev-parse','HEAD').decode().strip()
    consumed={}
    def existing(rel):
        value=accepted.base.verified_file(root,engine.relative_to(root)/rel,rev)
        consumed[rel]=accepted.base.sha(value);return value
    def reference(rel):return accepted.base.verified_file(donor,rel,accepted.REVISION)
    def prior(rel):return accepted.base.git(root,'show',ROUTE_ART+':'+ROUTE_PATH+rel)
    general='data/tilesets/primary/general/'
    rustboro='data/tilesets/secondary/rustboro/'
    stock_banks=[existing(general+'metatiles.bin'),existing(rustboro+'metatiles.bin')]
    stock_attrs=[existing(general+'metatile_attributes.bin'),existing(rustboro+'metatile_attributes.bin')]
    source_attrs=[reference('data/tilesets/'+f+'/metatile_attributes.bin') for f in ('primary/general','secondary/jubilife')]
    for contract in ('include/fieldmap.h','include/constants/metatile_behaviors.h'):
        if existing(contract)!=reference(contract):raise ValueError('runtime contract mismatch')
    primary=prior('banks/primary/metatiles.bin')
    primary_attrs=source_attrs[0] # one common semantic bank for streamed neighbors
    secondary=bytearray(stock_banks[1]+bytes((386-350)*16))
    secondary_attrs=bytearray(stock_attrs[1]+bytes((386-350)*2))
    prior_secondary=prior('banks/secondary/metatiles.bin')
    prior_sa=prior('banks/secondary/metatile_attributes.bin')
    route_receipt=json.loads(prior('art-receipt.json'))
    for mid in route_receipt['used_graphics']['metatiles']:
        if mid<512:continue
        i=mid-512;secondary[i*16:(i+1)*16]=prior_secondary[i*16:(i+1)*16]
        secondary_attrs[i*2:(i+1)*2]=prior_sa[i*2:(i+1)*2]
    # Mine entrance and adjacent prop are not present in Averon's stock bank.
    for mid,template in ((896,207),(897,225)):
        i=mid-512;secondary[i*16:(i+1)*16]=stock_banks[0][template*16:(template+1)*16]
        secondary_attrs[i*2:(i+1)*2]=source_attrs[1][i*2:(i+1)*2]
    raw=(HERE/'corridor/OreburghCity/map.bin').read_bytes()
    if accepted.base.sha(raw)!='bbad53605044afb179affd2aa7c44c5bde025c3a707e34f446af1db6093f422c':
        raise ValueError('reviewed City geometry changed')
    city=list(struct.unpack('<4130H',raw));desired=[]
    for i,cell in enumerate(city):
        bank,mid=divmod(cell&1023,512)
        art=words((primary,secondary)[bank],mid)
        # Donor secondary ordinals are NOT a visual compatibility contract.
        # Clear foreign architecture/path edges before stamping Averon facades.
        if bank and mid != 896:
            art=tuple((w&0xFFF)|0x3000 for w in words(stock_banks[0],289))
        if mid in (515,516,518,519,525,526,527,531,532,533,534,535):
            art=(0x3108,0x3118,0x3118,0x3108,0x314E,0x314F,0x314E,0x314F)
        if mid in (512,513,514,520,522,528,529,530):art=words(stock_banks[0],289)
        if mid in (517,523,524,536):art=words(stock_banks[0],225)
        if i//70>=38 and i%70>=41:
            if cell&1023==896:art=words(stock_banks[0],207)
            elif (cell>>10)&3:
                art=tuple([0x3108,0x3118,0x3118,0x3108,0x314E,0x314F,0x314E,0x314F])
            else:art=tuple((w&0xFFF)|0x3000 for w in words(stock_banks[0],289))
        desired.append(art)
    stock_raw=existing('data/layouts/RustboroCity/map.bin');stock=struct.unpack('<2400H',stock_raw)
    # Source-grounded envelopes; existing gray two-storey/ordinary facades,
    # neutral Devon-style museum shell, and original Center/Mart/Gym cues.
    facades=[((31,15,5,5),(16,8,5,6)),((31,15,5,5),(23,8,5,6)),
        ((14,42,5,4),(29,10,5,4)),((6,7,12,9),(49,8,16,8)),
        ((31,15,5,5),(34,10,5,4)),((31,15,5,5),(39,10,5,10)),
        ((31,15,5,5),(19,18,5,4)),((24,15,7,5),(27,18,7,5)),
        ((14,35,5,4),(49,19,5,4)),((31,15,5,5),(57,24,5,6)),
        ((31,15,5,5),(18,26,5,4)),((31,15,5,5),(23,26,5,4)),
        ((31,15,5,5),(55,34,5,4)),((6,7,12,9),(60,34,9,6))]
    for rectangle,destination in facades:stamp(desired,city,stock,stock_banks,rectangle,destination)
    staged,secondary,secondary_attrs=pack_art(raw,desired,source_attrs,primary,primary_attrs,secondary,secondary_attrs)
    route=(HERE/'corridor/Route207/map.bin').read_bytes()
    verified_cells=0
    for original, adapted in ((raw,staged),(route,route)):
        for (before,), (after,) in zip(struct.iter_unpack('<H',original),struct.iter_unpack('<H',adapted)):
            if before&0xFC00 != after&0xFC00:
                raise ValueError('collision/elevation changed')
            sb,si=divmod(before&1023,512);db,di=divmod(after&1023,512)
            if attribute(source_attrs[sb],si)!=attribute((primary_attrs,secondary_attrs)[db],di):
                raise ValueError('behavior/layer changed')
            verified_cells+=1
    for mid in route_receipt['used_graphics']['metatiles']:
        if mid<512:continue
        i=mid-512
        if words(secondary,i)!=words(prior_secondary,i) or attribute(secondary_attrs,i)!=attribute(prior_sa,i):
            raise ValueError('Route207 art changed')
    images=[accepted.dual.indexed(existing(f+'tiles.png')) for f in (general,rustboro)]
    palettes={i:accepted.base.palette(existing((general if i<6 else rustboro)+'palettes/%02d.pal'%i)) for i in range(16)}
    dependencies={}
    previews={}
    for name,geometry,width,height in (('OreburghCity',staged,70,59),('Route207',route,64,32)):
        border=(HERE/'corridor'/name/'border.bin').read_bytes()
        dependencies[name]=accepted.dual.closure(geometry+border,[primary,secondary],images)
        previews[name]=accepted.dual.render(geometry,[primary,secondary],images,palettes,width,height)
    import io
    from PIL import Image
    with Image.open(io.BytesIO(prior('averon.png'))) as previous:
        if previous.convert('RGB').tobytes()!=previews['Route207'].convert('RGB').tobytes() or previous.size!=previews['Route207'].size:
            raise ValueError('Route207 rendered appearance changed')
    headers={n:json.loads(reference('data/maps/'+n+'/map.json')) for n in ('OreburghCity','OreburghMine_B1F','OreburghMine_B2F','OreburghGate_1F')}
    warp_plan=compact_warps(headers['OreburghCity']['warp_events'],headers['OreburghMine_B1F']['warp_events'],headers['OreburghMine_B2F']['warp_events'],headers['OreburghGate_1F']['warp_events'])
    receipt=dict(status='OFF_ENGINE_CITY_ART_CANDIDATE_REQUIRES_VISUAL_AND_RUNTIME_REVIEW',donor_revision=accepted.REVISION,
        engine_revision=rev,route_art_source=ROUTE_ART,existing_averon_sha256=consumed,
        source_geometry_sha256=accepted.base.sha(raw),city_art_geometry_sha256=accepted.base.sha(staged),
        route_geometry_sha256=accepted.base.sha(route),shared_bank_records=len(secondary)//16,
        remaining_secondary_slots=512-len(secondary)//16,source_behavior_layer_words_preserved=True,
        collision_elevation_preserved=True,verified_cells=verified_cells,
        source_used_attributes={name:{str(cell&1023):attribute(source_attrs[(cell&1023)//512],(cell&1023)%512) for (cell,) in struct.iter_unpack('<H',data)} for name,data in (('OreburghCity',raw),('Route207',route))},
        source_attribute_sha256=[accepted.base.sha(a) for a in source_attrs],route207_used_secondary_records_unchanged=True,route207_render_pixels_unchanged=True,dependencies=dependencies,facade_templates=facades,
        limits=['Existing Averon style, not donor visual equivalence; no donor art copied',
                'Gray/gold neutral facades and timber yard replace unverified blue industrial art',
                'No permanent section, engine install, ROM, mGBA or services acceptance'])
    out.mkdir(parents=True)
    for name,geometry in (('OreburghCity',staged),('Route207',route)):
        p=out/name;p.mkdir();(p/'map.bin').write_bytes(geometry);previews[name].save(p/'averon.png')
    for bank,records,attrs in (('primary',primary,primary_attrs),('secondary',secondary,secondary_attrs)):
        p=out/'banks'/bank;p.mkdir(parents=True);(p/'metatiles.bin').write_bytes(records);(p/'metatile_attributes.bin').write_bytes(attrs)
    for filename,data in (('receipt.json',receipt),('warp-plan.json',warp_plan)):
        (out/filename).write_text(json.dumps(data,indent=2)+'\n')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for n in ('donor','engine','out'):parser.add_argument('--'+n,required=True,type=Path)
    args=parser.parse_args();print(json.dumps(build(args.donor,args.engine,args.out),indent=2))
