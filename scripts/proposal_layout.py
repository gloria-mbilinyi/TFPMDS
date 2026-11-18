"""Shared A4 plate layout. Preserve every source pixel with overlapping tiles."""
from pathlib import Path
import math
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent / 'work' / 'proposal-compatibility'
FRAGMENTS = {
  1: 'Combined fragments: alt [registration valid] / [registration invalid]; opt [account approved].',
  2: 'Combined fragments: alt [produce available] and [quantity sufficient] / [stock insufficient]; opt [order created]; alt [farmer accepts] / [farmer rejects].',
  3: 'Combined fragments: alt completion entry [buyer simulation path] / [callback path]; alt [payment successful] / [payment failed] / [payment cancelled]; opt [payment successful] view receipt.',
  4: 'Combined fragments: opt [approved transporter available]; loop [per tracking milestone and party enquiry]; opt [delivery confirmed].',
}


def figure_caption(section, index, text):
    return f'Figure {section}.{index}  {text}'


def plates(relative):
    if relative.startswith('uml/previews/'):
        from generate_readable_panels import interaction_panels
        return interaction_panels(relative)
    source = ROOT / 'docs' / relative
    with Image.open(source) as image:
        width, height = image.size
        # UML exports were authored for poster sheets. A4 uses two columns,
        # with extra rows for the taller shipment model. Screens use full width.
        cols = 2 if relative.startswith('uml/') else 1
        rows = math.ceil(height / 1200) if cols == 2 else (2 if height > 1400 else 1)
        overlap = 120 if cols == 2 else 70
        tile_w = math.ceil((width + overlap * (cols - 1)) / cols)
        tile_h = math.ceil((height + overlap * (rows - 1)) / rows)
        target = WORK / 'plates'
        target.mkdir(parents=True, exist_ok=True)
        result = ([{'path':str(source),'row':1,'col':1,'rows':1,'cols':1,'source':relative,
                    'overview':True,'caption':'Complete model overview. Enlarged overlapping detail panels follow.'}]
                  if cols==2 else [])
        for row in range(rows):
            for col in range(cols):
                left = min(col * (tile_w - overlap), width - tile_w)
                top = min(row * (tile_h - overlap), height - tile_h)
                path = target / f'{source.stem}-r{row+1}-c{col+1}.png'
                image.crop((left, top, left + tile_w, top + tile_h)).save(path, optimize=True)
                result.append({'path': str(path), 'row': row+1, 'col': col+1,
                               'rows': rows, 'cols': cols, 'source': relative,
                               'box': [left, top, left+tile_w, top+tile_h],
                               'source_size': [width, height]})
        return result
