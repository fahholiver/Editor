#!/usr/bin/env python3
"""Screen overlays on rendered JPEG frames (engine `cartoon`, format interactive_series).

    python3 tools/overlay.py            # in the project: work/overlay.json + frames/ -> frames_ov/

work/overlay.json (all optional, times in seconds):
  {"part": 2,
   "circles": [{"t0": 3.2, "t1": 6.0, "x": 540, "y": 900, "r": 160}],
   "choice": {"t0": 62.0, "question": "À QUI TU FAIS CONFIANCE ?", "a": "OUVRIR", "b": "FERMER", "next": 3}}
Drawing comes from tools/kit.py (daily/styles/series_kit.py: part_tag, red_circle, choice_card).
"""
import glob
import json
import os
import sys

import cairo
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit  # noqa: E402

spec = json.load(open('work/overlay.json', encoding='utf-8'))
os.makedirs('frames_ov', exist_ok=True)
for p in sorted(glob.glob('frames/f*.jpg')):
    t = int(os.path.basename(p)[1:5]) / 30.0
    a = np.ascontiguousarray(np.array(Image.open(p).convert('RGBA'))[:, :, [2, 1, 0, 3]])
    h, w = a.shape[:2]
    s = cairo.ImageSurface.create_for_data(memoryview(a), cairo.FORMAT_ARGB32, w, h, w * 4)
    ctx = cairo.Context(s)
    for c in spec.get('circles', []):
        if c['t0'] <= t <= c.get('t1', 1e9):
            kit.red_circle(ctx, c['x'], c['y'], c['r'], t, c['t0'])
    if spec.get('part'):
        kit.part_tag(ctx, spec['part'])
    ch = spec.get('choice')
    if ch:
        kit.choice_card(ctx, t, ch['t0'], ch['question'], ch['a'], ch['b'], ch['next'])
    s.flush()
    Image.fromarray(a[:, :, [2, 1, 0]]).save(os.path.join('frames_ov', os.path.basename(p)), quality=95)
print('overlay -> frames_ov/')
