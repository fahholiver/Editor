#!/usr/bin/env python3
"""Download the episode's assets into the project, log them in CREDITS.md and write an inventory.
usage: python fetch.py PROJECT

Reads PROJECT/assets.json, a list like:
[{"file": "real/salvage_drone.mp4", "url": "https://.../direct-download.mp4",
  "page": "https://item page", "kind": "aftermath", "depicts": "Controlled salvage demolition, May 2024",
  "credit": "U.S. Coast Guard / DVIDS", "rights": "U.S. federal work, public domain", "manual": false}]

Direct links are downloaded. Items marked "manual": true (for example DVIDS files that need a free login)
are listed with their page so the creator can download them into the right folder; rerun afterwards.
Writes PROJECT/CREDITS.md and PROJECT/inventory.md (duration, size and resolution of every file),
so the final script can be written around the footage that actually exists."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from toolkit import project_dir

if len(sys.argv) < 2:
    sys.exit('usage: python fetch.py PROJECT')
P = project_dir(sys.argv[1])
assets = json.loads((P / 'assets.json').read_text(encoding='utf-8'))
UA = {'User-Agent': 'Mozilla/5.0 (documentary research; engineering-failures-video skill)'}
manual, failed = [], []

for a in assets:
    dest = P / a['file']
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        continue
    if a.get('manual') or not a.get('url'):
        manual.append(a)
        continue
    try:
        tmp = dest.with_suffix(dest.suffix + '.part')
        with urllib.request.urlopen(urllib.request.Request(a['url'], headers=UA), timeout=60) as r, open(tmp, 'wb') as fh:
            if 'text/html' in (r.headers.get('Content-Type') or ''):
                raise ValueError('the link opened a web page, not a file (it may need a login)')
            shutil.copyfileobj(r, fh)
        tmp.replace(dest)
        print(f'downloaded  {a["file"]}')
    except Exception as e:  # keep going; report at the end
        failed.append((a, str(e)))
        Path(str(dest) + '.part').unlink(missing_ok=True)


def probe(path):
    if not shutil.which('ffprobe'):
        return ''
    r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_type,width,height',
                        '-of', 'json', str(path)], capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return 'unreadable'
    v = next((s for s in d.get('streams', []) if s.get('codec_type') == 'video'), None)
    dur = float(d.get('format', {}).get('duration', 0) or 0)
    size = f'{v["width"]}×{v["height"]}' if v and v.get('width') else ''
    return ', '.join(x for x in (f'{dur:.1f} s' if dur > 0.2 else '', size) if x)


rows, inv = [], []
for a in assets:
    dest = P / a['file']
    have = dest.exists() and dest.stat().st_size > 0
    rows.append(f'| {a["file"]} | {a.get("page") or a.get("url", "")} | {a.get("credit", "")} | {a.get("depicts", "")} '
                f'| {a.get("rights", "")} | {"in project" if have else "MISSING"} |')
    if have:
        inv.append(f'- `{a["file"]}` ({a.get("kind", "asset")}): {a.get("depicts", "")}. {probe(dest)}')
(P / 'CREDITS.md').write_text(
    '# Source ledger\n\n| Local file | Source page | Credit | What it depicts | Reuse | Status |\n|---|---|---|---|---|---|\n'
    + '\n'.join(rows) + '\n', encoding='utf-8')
(P / 'inventory.md').write_text('# Assets in the project\n\n' + ('\n'.join(inv) or 'None yet.') + '\n', encoding='utf-8')

print(f'\n{len(inv)} of {len(assets)} assets are in the project. Ledger: CREDITS.md, inventory: inventory.md')
for a in manual:
    print(f'DOWNLOAD BY HAND  {a["file"]}  <-  {a.get("page") or a.get("url")}')
for a, err in failed:
    print(f'COULD NOT DOWNLOAD  {a["file"]}  ({err})  page: {a.get("page") or a.get("url")}')
if manual or failed:
    print('Save each file under the exact name shown, then run this again.')
