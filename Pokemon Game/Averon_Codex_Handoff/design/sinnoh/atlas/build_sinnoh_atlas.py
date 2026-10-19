#!/usr/bin/env python3
"""Build sinnoh-atlas.json: the SOURCE layer of the Sinnoh topology atlas (roadmap C02).

For every area in SINNOH_AREA_REGISTER.csv it fetches the Bulbapedia page's lead section through
the MediaWiki API, reads the location/route infobox and records its compass neighbours, size and
map images, with the page revision as provenance. Raw API responses are cached OUTSIDE the repo
(--cache) and never committed; only the extracted facts are.

  python3 build_sinnoh_atlas.py --register .../SINNOH_AREA_REGISTER.csv --cache DIR [--offline]

This is the reference layer only. Averon adaptations (which links exist, offsets, closures) are a
separate, clearly labelled layer in SINNOH_ATLAS.md; nothing here approves a map or an ID.
"""
import argparse
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = 'https://bulbapedia.bulbagarden.net/w/api.php'
UA = 'Mozilla/5.0 (X11; Linux x86_64) averon-atlas-research'
DIRS = ('north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest')
TITLE = {  # register name -> Bulbapedia page title, where they differ
    'Pokémon League': 'Pokémon League (Sinnoh)',
    'Battle Park / Battle Frontier': 'Battle Frontier (Generation IV)',
    'Eterna Galactic Building': 'Galactic Eterna Building',
    'Veilstone Galactic Headquarters': 'Galactic HQ',
    'Victory Road': 'Victory Road (Sinnoh)',
    'Pal Park': 'Pal Park',
    'Cycling Road': 'Sinnoh Route 206',   # Bulbapedia's "Cycling Road" is a disambiguation page
}


def title_for(name):
    m = re.fullmatch(r'Route (2\d\d)', name)
    if m:
        return f'Sinnoh Route {m.group(1)}'
    return TITLE.get(name, name)


def fetch(title, cache, offline):
    path = cache / (re.sub(r'[^A-Za-z0-9]+', '_', title) + '.json')
    if path.exists():
        return json.loads(path.read_text())
    if offline:
        raise SystemExit(f'not cached: {title}')
    q = urllib.parse.urlencode({'action': 'parse', 'page': title, 'prop': 'wikitext|revid', 'section': 0,
                                'redirects': 1, 'format': 'json'})
    req = urllib.request.Request(f'{API}?{q}', headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    path.write_text(json.dumps(data))
    time.sleep(1.0)  # be polite to the wiki
    return data


def infobox(wikitext):
    """The first {{... infobox ...}} template as key -> raw value (nested templates kept intact)."""
    start = wikitext.find('{{')
    while start != -1:
        name = re.split(r'[|\n}]', wikitext[start + 2:start + 80], maxsplit=1)[0].lower()
        if 'infobox' in name:
            break
        start = wikitext.find('{{', start + 2)
    if start == -1:
        return {}
    depth, i = 0, start
    while i < len(wikitext):
        if wikitext.startswith('{{', i):
            depth += 1
            i += 2
        elif wikitext.startswith('}}', i):
            depth -= 1
            i += 2
            if depth == 0:
                break
        else:
            i += 1
    body = wikitext[start + 2:i - 2]
    fields, depth, cur = [], 0, ''
    for ch in body:  # split on top-level pipes only
        if ch in '{[':
            depth += 1
        elif ch in '}]':
            depth -= 1
        if ch == '|' and depth == 0:
            fields.append(cur)
            cur = ''
        else:
            cur += ch
    fields.append(cur)
    out = {'_template': fields[0].strip()}
    for f in fields[1:]:
        if '=' in f:
            k, v = f.split('=', 1)
            out[k.strip().lower()] = v.strip()
    return out


def clean(v):
    """Wiki markup -> plain place names (a field may hold several, e.g. 'A<br>B')."""
    v = re.sub(r'\{\{rt\|(\d+)\|Sinnoh[^}]*\}\}', r'Route \1', v)
    v = re.sub(r'\{\{[^|}]*\|([^|}]+)[^}]*\}\}', r'\1', v)
    v = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', v)
    v = re.sub(r'<br\s*/?>|<small>|</small>|\(.*?\)', '\n', v)
    names = [re.sub(r'^Sinnoh ', '', n.strip(" '")) for n in v.split('\n')]
    return [n for n in names if n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--register', required=True)
    ap.add_argument('--cache', required=True)
    ap.add_argument('--offline', action='store_true')
    ap.add_argument('--out', default=str(Path(__file__).with_name('sinnoh-atlas.json')))
    a = ap.parse_args()
    cache = Path(a.cache)
    cache.mkdir(parents=True, exist_ok=True)
    areas = []
    for row in csv.DictReader(open(a.register, encoding='utf-8')):
        name, title = row['LocationOrZone'], title_for(row['LocationOrZone'])
        rec = {'key': row['TrackerKey'], 'name': name, 'kind': row['Kind'], 'source': {'page': title}}
        try:
            data = fetch(title, cache, a.offline)
        except Exception as exc:  # recorded, never invented
            rec['source']['error'] = f'{type(exc).__name__}: {exc}'
            areas.append(rec)
            continue
        if 'error' in data:
            rec['source']['error'] = data['error'].get('info', 'error')
            areas.append(rec)
            continue
        p = data['parse']
        box = infobox(p['wikitext']['*'])
        rec['source'].update(resolved=p['title'], revid=p['revid'],
                             url='https://bulbapedia.bulbagarden.net/wiki/' + p['title'].replace(' ', '_'),
                             template=box.get('_template'))
        rec['neighbours'] = {d: clean(box[d]) for d in DIRS if box.get(d)}
        if box.get('location'):   # landmarks: a prose relation ("West end of Route 201") instead of compass fields
            rec['located'] = re.sub(r'\{\{sup/[^}]*\}\}', '', box['location'])
            rec['located_links'] = sorted(set(clean(rec['located'])) & {
                n for n in (title_for(x) for x in [r['LocationOrZone'] for r in csv.DictReader(open(a.register, encoding='utf-8'))])} |
                {f'Route {m}' for m in re.findall(r'rt\|(\d+)\|Sinnoh', box['location'])})
        for k in ('size', 'type', 'image', 'imageiv', 'imagedp', 'imagept', 'mapdesc'):
            if box.get(k):
                rec.setdefault('infobox', {})[k] = box[k]
        areas.append(rec)
    out = {'about': 'SOURCE layer only: Bulbapedia infobox facts per area, with page revision. '
                    'Not an approval of any Averon map, connection or ID.',
           'api': API, 'areas': areas}
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    ok = sum(1 for r in areas if 'revid' in r['source'])
    print(f'{ok}/{len(areas)} pages resolved; {sum(len(r.get("neighbours", {})) > 0 for r in areas)} with compass '
          f'neighbours; {sum(1 for r in areas if r.get("located"))} with a location relation')
    for r in areas:
        if 'revid' not in r['source']:
            print('  unresolved:', r['key'], r['name'], r['source'].get('error'))


if __name__ == '__main__':
    main()
