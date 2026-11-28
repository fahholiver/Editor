#!/usr/bin/env python3
"""Render the graphics layer of every chunk (or one chunk) with HyperFrames.
usage: python render.py PROJECT [CHUNK]
Skips chunks whose MP4 is newer than their index.html, so an interrupted render can simply be rerun.
Set HF_WORKERS to change the number of parallel browser workers (default 2)."""
import json
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from toolkit import need_hyperframes, project_dir, render_env

if len(sys.argv) < 2:
    sys.exit('usage: python render.py PROJECT [CHUNK]')
P = project_dir(sys.argv[1])
only = sys.argv[2] if len(sys.argv) > 2 else None
hf = need_hyperframes(P)
names = json.loads((P / 'shots.json').read_text(encoding='utf-8'))['names']
if only and only not in names:
    sys.exit(f'Unknown chunk: {only}. Chunks are: {", ".join(names)}')
out = P / 'out'
out.mkdir(exist_ok=True)
env = render_env()
for name in ([only] if only else names):
    mp4, html = out / f'{name}.mp4', P / 'chunks' / name / 'index.html'
    if mp4.exists() and mp4.stat().st_mtime > html.stat().st_mtime:
        continue
    tmp, log = out / f'{name}.tmp.mp4', out / f'{name}.log'
    cmd = [str(hf), 'render', str(P / 'chunks' / name), '-o', str(tmp), '-q', 'draft',
           '-w', os.environ.get('HF_WORKERS', '2'), '--quiet']
    with open(log, 'w', encoding='utf-8') as fh:
        code = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, env=env).returncode
    if code != 0:
        print(''.join(log.read_text(encoding='utf-8', errors='replace').splitlines(True)[-25:]), file=sys.stderr)
        sys.exit(f'Render failed for chunk "{name}". Full log: {log}')
    os.replace(tmp, mp4)
    print(f'{name} rendered')
    with open(out / 'progress.txt', 'a', encoding='utf-8') as fh:
        fh.write(f'{name} rendered\n')
