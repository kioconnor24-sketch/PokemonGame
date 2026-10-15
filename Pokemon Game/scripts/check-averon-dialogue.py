"""Check authored dialogue against the native normal-font glyph widths.

Dynamic player names use the widest permitted seven-letter name. Starter and
cap placeholders use their actual bounds. This is static layout QA, not UI QA.
"""
from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]
fonts=(root/'engine/src/fonts.c').read_text()
body=re.search(r'gFontNormalLatinGlyphWidths\[\]\s*=\s*\{([^}]+)',fonts).group(1)
widths=[int(x) for x in re.findall(r'\d+',body)]
charmap={}
for line in (root/'engine/charmap.txt').read_text(encoding='utf-8').splitlines():
    match=re.match(r"^'(.+)'\s*=\s*([0-9A-F]{2})\s*$",line)
    if match:
        glyph=match[1].replace("\\'", "'")
        if len(glyph)==1:charmap[glyph]=int(match[2],16)
max_letter=max('ABCDEFGHIJKLMNOPQRSTUVWXYZ',key=lambda c:widths[charmap[c]])
errors=[];count=0;widest=(0,'')
for name in ('averon-opening.inc','averon-first-gym.inc','averon-coast.inc','averon-optional-sidequests.inc'):
    label=''
    for number,line in enumerate((root/'scripts'/name).read_text().splitlines(),1):
        if re.match(r'^\w+:',line):label=line.split(':')[0]
        match=re.search(r'\.string "(.*)"',line)
        if not match:continue
        value=match[1].replace('{PLAYER}',max_letter*7)
        value=value.replace('{STR_VAR_1}','100' if label=='Alderfield_Text_Rules' else 'Fennekin')
        for part in re.split(r'\\[npl]',value.rstrip('$')):
            count+=1
            unknown=set(part)-charmap.keys()
            if unknown:errors.append(f'{name}:{number}: unmapped glyphs {sorted(unknown)}');continue
            width=sum(widths[charmap[c]] for c in part)
            if width>widest[0]:widest=(width,label)
            # Native message window is 216px at x=0. Reserve 8px of margin.
            if width>208:errors.append(f'{name}:{number}: {label} is {width}px (limit 208): {part}')
if errors:
    print('\n'.join(errors));raise SystemExit(1)
print(f'PASS: {count} authored dialogue lines; widest {widest[0]}px ({widest[1]}), limit 208px.')
