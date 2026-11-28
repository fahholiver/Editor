"""Draw a labelled grid on a copy of a screenshot, so the line to highlight can be read off as fractions:
    python3 scripts/grid.py media/clip_10k.png        -> media/clip_10k.grid.png
Then look at the .grid.png and use the numbers in fin.clipping(..., mark=[(x0, y0, x1, y1)]): x0/x1 across, y0/y1 down,
0 = left/top edge, 1 = right/bottom edge. One box per line of text; leave a little room above and below the letters.
The .grid.png is only for reading coordinates; never put it in the video."""
import sys, os
from PIL import Image, ImageDraw
src = sys.argv[1]; im = Image.open(src).convert('RGB'); w, h = im.size; d = ImageDraw.Draw(im, 'RGBA')
for k in range(1, 40):
    f = k / 40; y = int(f * h); major = k % 4 == 0
    d.line([(0, y), (w, y)], fill=(255, 0, 80, 150 if major else 60), width=2 if major else 1)
    d.rectangle([0, y - 9, 44, y + 9], fill=(255, 255, 255, 220)); d.text((3, y - 7), f'{f:.3f}'[1:], fill=(200, 0, 60))
for k in range(1, 20):
    f = k / 20; x = int(f * w)
    d.line([(x, 0), (x, h)], fill=(0, 90, 255, 130 if k % 2 == 0 else 50), width=1)
    d.rectangle([x - 16, 0, x + 18, 14], fill=(255, 255, 255, 220)); d.text((x - 14, 1), f'{f:.2f}'[1:], fill=(0, 60, 200))
out = os.path.splitext(src)[0] + '.grid.png'; im.save(out); print('wrote', out, f'({w}x{h})')
