#!/usr/bin/env python3
"""Source-pinned reuse inventory; no converter, network calls or production writes.

Capture immutable Git evidence with --donor/--repo/--refs. Render the same CSV
from a saved --inputs snapshot without donor checkout or historical Git objects.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import unicodedata

REV = '38228bb574a3557345852b758d5f1a65eb01bb22'
DEV = 'Pokemon Game/Averon_Codex_Handoff/development/'
DESIGN = 'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/'
FIELDS = ['site_or_child_key','row_kind','covered_sites','donor_map_name','pinned_git_revision',
          'map_json_present','layout_bin_present','source_dimensions','original_warps',
          'external_connections','source_graphics_family','source_geometry_status','known_repair',
          'existing_averon_stage_path','source_stage_sha_or_pr','permitted_art_status',
          'actual_runtime_QA_status','production_registry_status','next_action','evidence']


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE)


def read(repo, ref, path):
    return git(repo, 'show', ref + ':' + path)


def normalized(name):
    text = ''.join(c for c in unicodedata.normalize('NFKD', name) if not unicodedata.combining(c))
    return re.sub('[^a-z0-9]', '', text.lower())


# Donor spellings are source facts, never renamed on disk or in map headers.
ALIASES = {'pokmonleague':'pokemonleague','floaromatwon':'floaromatown',
           'twinleaftownhaouse':'twinleaftownhouse','valleywindoworks':'valleywindworks'}


def sites_for(name, sites):
    token = normalized(name)
    for wrong, right in ALIASES.items():
        token = token.replace(wrong, right)
    special = [('eternacitygalacticbuilding','SN-O03'),('mtcoronet','SN-L07'),
               ('oldchateau','SN-L15'),('oreburghgate','SN-L09'),('oreburghmine','SN-L10'),
               ('hotelgrandlake','SN-L05')]
    for prefix, key in special:
        if token.startswith(prefix):
            return [key]
    matches = [(len(normalized(s['LocationOrZone'])), s['TrackerKey']) for s in sites
               if token.startswith(normalized(s['LocationOrZone']))]
    if not matches:
        raise ValueError('unmapped source site: ' + name)
    answer = [max(matches)[1]]
    if name.startswith('Route206'):
        answer.append('SN-L18')  # Same physical Cycling Road, not another constructed map.
    return answer


def source_facts(donor):
    registry_raw = read(donor, REV, 'data/maps/map_groups.json')
    registry = json.loads(registry_raw)
    names = [name for group in registry['group_order'][:18] for name in registry[group]]
    if len(names) != 159 or len(set(names)) != 159:
        raise ValueError('pinned 159-map registry changed')
    layout_raw = read(donor, REV, 'data/layouts/layouts.json')
    layouts = {x['id']: x for x in json.loads(layout_raw)['layouts']}
    facts = []
    for name in names:
        path = 'data/maps/' + name + '/map.json'
        header_raw = read(donor, REV, path)
        h = json.loads(header_raw)
        layout = layouts[h['layout']]
        raw = read(donor, REV, layout['blockdata_filepath'])
        if len(raw) != layout['width'] * layout['height'] * 2:
            raise ValueError('source dimensions mismatch: ' + name)
        technical = {k:h[k] for k in ('id','name','layout','warp_events','connections','map_type','weather','requires_flash','allow_cycling','allow_escaping','allow_running','battle_scene') if k in h}
        facts.append(dict(name=name, header=technical, layout=layout, map_sha256=digest(raw),
                          map_blob=git(donor,'rev-parse',REV+':'+layout['blockdata_filepath']).decode().strip(),
                          header_sha256=digest(header_raw)))
    blobs = {line.split('\t',1)[1]:line.split()[2] for line in git(donor,'ls-tree','-r',REV,'--','data/layouts').decode().splitlines()}
    for layout in layouts.values():
        layout['blockdata_git_blob'] = blobs.get(layout['blockdata_filepath'])
    # Explicitly inspect ALL layout names, not just the registered map list.
    return dict(revision=REV, registry_sha256=digest(registry_raw), layouts_sha256=digest(layout_raw),
                registered=names, maps=facts,
                unregistered_layouts=[x for x in layouts.values() if x['id'] not in
                                      {f['header']['layout'] for f in facts}])


def dictionaries(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from dictionaries(child)
    elif isinstance(value, list):
        for child in value:
            yield from dictionaries(child)


def evidence_snapshot(repo, refs, facts):
    """Inspect committed current-main and exact PR trees, never working-tree caches."""
    snapshots = []
    source_ids = {f['header']['id']:f['name'] for f in facts['maps']}
    for label, ref in refs.items():
        commit = git(repo,'rev-parse',ref+'^{commit}').decode().strip()
        paths = git(repo,'ls-tree','-r','--name-only',commit,'--',DESIGN).decode().splitlines()
        records = []
        for path in paths:
            if not path.endswith('.json') or not any(word in Path(path).name for word in
                       ('receipt', 'manifest', 'recipe', 'result', 'identity')):
                continue
            raw = read(repo,commit,path)
            try:
                doc = json.loads(raw)
            except ValueError:
                continue
            # Pin evidence by complete file hash and actual named/hash-linked maps.
            linked = set()
            stage_maps = set()
            for node in dictionaries(doc):
                explicit = node.get('map') or source_ids.get(node.get('source_map'))
                if isinstance(explicit,str) and explicit in facts['registered']:
                    linked.add(explicit)
                    if 'receipt' in Path(path).name:
                        stage_maps.add(explicit)
                for field in ('maps','identity_roundtrips','source_geometry_headers'):
                    value = node.get(field)
                    if isinstance(value,dict):
                        linked.update(set(value) & set(facts['registered']))
                        if 'receipt' in Path(path).name:
                            stage_maps.update(set(value) & set(facts['registered']))
            runtime = None
            if isinstance(doc,dict) and isinstance(doc.get('checks'),list) and isinstance(doc.get('maps'),list):
                linked.update(source_ids[x] for x in doc['maps'] if isinstance(x,str) and x in source_ids)
                checks=doc['checks']
                runtime=dict(passed=sum(c.get('ok') is True for c in checks),
                             failed=sum(c.get('ok') is not True for c in checks),
                             rom_sha256=doc.get('rom_sha256','UNKNOWN'),build=doc.get('build','UNKNOWN'))
            if linked:
                records.append(dict(path=path,sha256=digest(raw),maps=sorted(linked),
                                    stage_maps=sorted(stage_maps),runtime=runtime))
        snapshots.append(dict(label=label,commit=commit,paths=paths,records=records))
    # Verify legacy source receipts against actual immutable donor bytes when they
    # publish a source-map SHA, not a remapped/staged output SHA.
    for snap in snapshots:
        for record in snap['records']:
            doc=json.loads(read(repo,snap['commit'],record['path']))
            by_name={f['name']:f for f in facts['maps']}
            for node in dictionaries(doc):
                named=node.get('maps')
                if isinstance(named,dict):
                    for name,value in named.items():
                        if name in by_name and isinstance(value,dict) and 'source_sha256' in value:
                            if value['source_sha256']!=by_name[name]['map_sha256']:
                                raise ValueError('stale named source hash: '+record['path']+' '+name)
            for field in ('donor_sha256','consumed_donor_sha256'):
                for path, expected in doc.get(field,{}).items():
                    if path.endswith('/map.bin'):
                        matches=[f for f in facts['maps'] if f['layout']['blockdata_filepath']==path]
                        if matches and any(f['map_sha256']!=expected for f in matches):
                            raise ValueError('stale receipt source hash: '+record['path']+' '+path)
    return snapshots


def validate(data):
    facts=data['donor']; names=facts['registered']
    if facts['revision']!=REV or len(names)!=159 or len(set(names))!=159:
        raise ValueError('invalid pinned source inventory')
    if sorted(names)!=sorted(x['name'] for x in facts['maps']):
        raise ValueError('source definition missing or duplicated')
    keys=[s['TrackerKey'] for s in data['sites']]
    if len(keys)!=87 or len(set(keys))!=87:
        raise ValueError('expected 87 distinct master sites')
    for f in facts['maps']:
        if not re.fullmatch('[0-9a-f]{64}',f['map_sha256']):
            raise ValueError('invalid source hash')
        sites_for(f['name'],data['sites'])


def rows(data):
    validate(data)
    output=[]; covered=set()
    production=set(data['production_maps'])
    for f in data['donor']['maps']:
        name=f['name']; sites=sites_for(name,data['sites']);covered.update(sites)
        evidence=[];stages=[];art=[];qa=[]
        for snap in data['snapshots']:
            for rec in snap['records']:
                if name not in rec['maps']:
                    continue
                link=f"{snap['label']}@{snap['commit']}:{rec['path']}#{rec['sha256']}"
                evidence.append(link)
                if rec.get('runtime'):
                    rt=rec['runtime']
                    qa.append(f"COMMITTED_SOURCE_BOUND_CLUSTER:{rt['build']}:{rt['passed']}PASS/{rt['failed']}FAIL:ROM={rt['rom_sha256']}:{link}")
                if name in rec['stage_maps'] or f['map_sha256'] in rec.get('source_hashes',[]):
                    stages.append(link)
            # Exact candidate filenames are evidence of staged art, not approval.
            for path in snap['paths']:
                if '/'+name+'/averon-map.bin' in path:
                    art.append(f"CANDIDATE:{snap['label']}@{snap['commit']}:{path}")
        h=f['header']; l=f['layout']; prod=name in production
        # Hash-linked early conversion receipts also establish source staging.
        if not stages:
            stages=[e for e in evidence if 'receipt' in e]
        known=[]
        if any(w.get('dest_map')==h['id'] for w in h.get('warp_events',[])):
            known.append('source self-warp; review exact destination indices')
        if name=='Route218': known.append('known donor destination repair; use committed canalave-west receipt')
        if name=='OreburghCity': known.append('known city warp repair; use committed oreburgh-connected evidence')
        if name=='LakeAcuity': known.append('zero source warps/connections; not linked automatically')
        if name in ('Route216','Route217','AcuityLakefront','SnowpointCity'):
            qa.append('PR235:source-bound DEV evidence; bridge visual unresolved; NOT production acceptance')
        elif name in production:
            qa.append('UNKNOWN:production membership is not a fresh runtime verdict; consult linked acceptance')
        elif stages:
            qa.append('source stage alone is not acceptance; consult pinned evidence' if qa else 'UNKNOWN:source stage is not acceptance')
        elif not qa: qa.append('NOT_TESTED')
        source_status='PRODUCTION_PRESENT' if prod else 'STAGED_SOURCE' if stages else 'AVAILABLE_UNSTAGED'
        output.append(dict(zip(FIELDS,['source:'+name,'SOURCE_MAP','|'.join(sites),name,REV,'YES','YES',
            f"{l['width']}x{l['height']}",json.dumps(h.get('warp_events',[]),sort_keys=True,separators=(',',':')),
            json.dumps(h.get('connections') or [],sort_keys=True,separators=(',',':')),
            l['primary_tileset']+' + '+l['secondary_tileset'],source_status,'; '.join(known) or 'UNKNOWN',
            '; '.join(stages) or 'NONE','; '.join(sorted({s.split(':',1)[0] for s in stages})) or 'NONE',
            '; '.join(art) or ('PRODUCTION_ART_PRESENT; review evidence' if prod else 'UNKNOWN'),
            '; '.join(qa),'REGISTERED_ON_MAIN' if prod else 'NOT_REGISTERED_ON_MAIN',
            'preserve/reuse existing work' if (prod or stages) else 'stage with existing converter; validate dependencies',
            '; '.join(evidence) or 'pinned source hashes in SINNOH_DONOR_REUSE_INPUTS.json'])))
    for site in data['sites']:
        key=site['TrackerKey']
        targets=[]
        if key not in covered:
            targets.append(('geography','no registered donor definition; inspect explicit unregistered layout candidates before original construction'))
        if site['Kind'] in ('SETTLEMENT','POSTGAME_HUB'):
            targets.append(('uncovered-interiors','audit/build remaining neutral interiors; existing exterior/child source does not satisfy a complete settlement'))
        for child,action in targets:
            row={key:'UNKNOWN' for key in FIELDS}
            row.update(site_or_child_key='target:'+key+':'+child,row_kind='BUILD_TARGET',covered_sites=key,
                donor_map_name='NONE',pinned_git_revision=REV,map_json_present='NO_REGISTERED_SOURCE',
                layout_bin_present='UNKNOWN: see unregistered_layouts in inputs',source_geometry_status='GAP_TARGET',
                known_repair='NOT_AN_IMPLEMENTED_MAP',existing_averon_stage_path='UNKNOWN',source_stage_sha_or_pr='NONE',
                permitted_art_status='NOT_ESTABLISHED',actual_runtime_QA_status='NOT_TESTED',
                production_registry_status='NOT_ESTABLISHED',next_action=action,
                evidence='SINNOH_AREA_REGISTER.csv:'+key+'; SINNOH_FULL_AREA_COVERAGE.md')
            candidates=[l for l in data['donor']['unregistered_layouts']
                        if normalized(site['LocationOrZone']) in normalized(l['id'])]
            if child=='geography' and candidates:
                row['known_repair']='UNREGISTERED_LAYOUT_NAMES_ARE_NOT_SINNOH_PROOF:'+json.dumps([
                    {'layout':l['id'],'path':l['blockdata_filepath'],'blob':l.get('blockdata_git_blob')}
                    for l in candidates],sort_keys=True,separators=(',',':'))
            output.append(row)
    extra_children=[('SN-L07','remaining-upper-coronet','Only four lower Coronet donor maps; construct uncovered upper floors and summit links'),
                    ('SN-L09','basement','Only OreburghGate1F donor map; construct missing basement without enabling closed exits'),
                    ('','underground','Master roadmap W8: source absent; feasibility first, no unsupported DS mechanics'),
                    ('SN-T02','neutral-lab','Donor Sandgem door references Hoenn Birch lab; neutral Sinnoh interior needed'),
                    ('SN-T04','neutral-museum','Donor Oreburgh door references Hoenn Lilycove museum; neutral interior needed'),
                    ('SN-T09','neutral-department-store','Donor Veilstone door references Hoenn Lilycove store; neutral interior needed')]
    for site,child,action in extra_children:
        row={key:'UNKNOWN' for key in FIELDS}
        row.update(site_or_child_key='target:'+(site or 'ROADMAP-W8')+':'+child,row_kind='BUILD_TARGET',
            covered_sites=site,donor_map_name='NONE',pinned_git_revision=REV,map_json_present='NO_REGISTERED_SINNOH_SOURCE',
            source_geometry_status='GAP_TARGET',actual_runtime_QA_status='NOT_TESTED',
            production_registry_status='NOT_ESTABLISHED',next_action=action,
            evidence='SINNOH_MASTER_PRODUCTION_ROADMAP.md; pinned source headers/layout inventory')
        output.append(row)
    ids=[r['site_or_child_key'] for r in output]
    if len(ids)!=len(set(ids)) or (set('|'.join(r['covered_sites'] for r in output).split('|'))-{''})!=set(s['TrackerKey'] for s in data['sites']):
        raise ValueError('duplicate target or uncovered master site')
    return output


def render(data):
    out=io.StringIO(newline=''); writer=csv.DictWriter(out,FIELDS,lineterminator='\n')
    writer.writeheader();writer.writerows(rows(data));return out.getvalue()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--donor',type=Path);p.add_argument('--repo',type=Path);p.add_argument('--refs',type=Path)
    a=p.parse_args()
    if a.donor:
        if not a.repo or not a.refs: p.error('--donor requires --repo and --refs')
        refs=json.loads(a.refs.read_text());facts=source_facts(a.donor)
        sites=list(csv.DictReader(io.StringIO(read(a.repo,refs['main'],DEV+'SINNOH_AREA_REGISTER.csv').decode())))
        registry=json.loads(read(a.repo,refs['main'],'Pokemon Game/engine/data/maps/map_groups.json'))
        data=dict(donor=facts,sites=sites,snapshots=evidence_snapshot(a.repo,refs,facts),
                  production_maps=registry['gMapGroup_Sinnoh'])
        validate(data);a.inputs.write_text(json.dumps(data,indent=2)+'\n')
    else: data=json.loads(a.inputs.read_text())
    a.out.write_text(render(data))


if __name__=='__main__': main()
