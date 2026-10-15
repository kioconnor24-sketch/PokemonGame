"""Render native Emerald metatiles for layout review; no random map generation."""
import json, struct, sys
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1] / 'engine'
layouts = json.loads((ROOT/'data/layouts/layouts.json').read_text())['layouts']

def render(layout, output, grid=False):
    def tileset(symbol):
        name = symbol.removeprefix('gTileset_')
        # Upstream folder names use snake_case.
        import re
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        candidates = list((ROOT/'data/tilesets').glob('*/'+name))
        return candidates[0]
    dirs = [tileset(layout['primary_tileset']), tileset(layout['secondary_tileset'])]
    tiles = [Image.open(d/'tiles.png') for d in dirs]
    metas = [list(struct.iter_unpack('<8H', (d/'metatiles.bin').read_bytes())) for d in dirs]
    palettes = []
    for p in range(16):
        d = dirs[0 if p < 6 else 1]
        palettes.append([tuple(map(int,s.split())) for s in (d/'palettes'/f'{p:02}.pal').read_text().splitlines()[3:19]])
    cache = {}
    def metatile(mid):
        if mid in cache: return cache[mid]
        ts = int(mid >= 512)
        result = Image.new('RGB',(16,16),palettes[0][0])
        for i, entry in enumerate(metas[ts][mid-512*ts]):
            tid=entry&1023; source=int(tid>=512); tid-=512*source
            sheet=tiles[source]; cols=sheet.width//8
            tile=sheet.crop(((tid%cols)*8,(tid//cols)*8,(tid%cols)*8+8,(tid//cols)*8+8))
            pix=list(tile.getdata()); palette=palettes[entry>>12]
            rgba=Image.new('RGBA',(8,8)); rgba.putdata([(*palette[v],0 if v==0 and i>=4 else 255) for v in pix])
            if entry&1024: rgba=rgba.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if entry&2048: rgba=rgba.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            result.paste(rgba,((i%2)*8,((i%4)//2)*8),rgba)
        cache[mid]=result; return result
    w,h=layout['width'],layout['height']
    values=struct.unpack('<'+'H'*(w*h),(ROOT/layout['blockdata_filepath']).read_bytes())
    image=Image.new('RGB',(w*16,h*16))
    for y in range(h):
        for x in range(w): image.paste(metatile(values[y*w+x]&1023),(x*16,y*16))
    if grid:
        draw=ImageDraw.Draw(image)
        for x in range(w): draw.text((x*16,0),str(x),fill='red')
        for y in range(h): draw.text((0,y*16),str(y),fill='red')
    Path(output).parent.mkdir(parents=True,exist_ok=True); image.save(output)

if __name__=='__main__':
    name=sys.argv[1]; layout=next(l for l in layouts if l['name']==name+'_Layout')
    render(layout,sys.argv[2], '--grid' in sys.argv)
