#!/usr/bin/env python3
"""Search Wikimedia Commons for free-to-use footage and stills. No account or API key needed.
usage: python commons.py "Key Bridge collapse" [--video | --image] [--limit 30] [--add PROJECT]

Prints each match with its license, author, size and direct download URL. Only public-domain, CC0, CC BY
and CC BY-SA files are shown (CC BY / BY-SA need the credit line in your description). With --add PROJECT,
the matches are appended to PROJECT/assets.json (skipping duplicates) so fetch.py can download them.
Edit or prune assets.json afterwards: keep only files that really show the case."""
import argparse
import html
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

API = 'https://commons.wikimedia.org/w/api.php'
UA = {'User-Agent': 'engineering-failures-video-skill/1.0 (documentary research; free Claude skill)'}
OK_LICENSES = ('public domain', 'pd', 'cc0', 'cc by', 'cc-by')


def clean(text):
    return html.unescape(re.sub(r'<[^>]+>', '', text or '')).strip()


def search(query, kind, limit):
    q = query + {'video': ' filetype:video', 'image': ' filetype:bitmap'}.get(kind, '')
    params = {'action': 'query', 'format': 'json', 'generator': 'search', 'gsrsearch': q, 'gsrnamespace': 6,
              'gsrlimit': limit, 'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata'}
    req = urllib.request.Request(API + '?' + urllib.parse.urlencode(params), headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        pages = json.load(r).get('query', {}).get('pages', {})
    out = []
    for page in sorted(pages.values(), key=lambda p: p.get('index', 0)):
        info = (page.get('imageinfo') or [{}])[0]
        meta = info.get('extmetadata', {})
        lic = clean(meta.get('LicenseShortName', {}).get('value'))
        if not any(lic.lower().startswith(x) for x in OK_LICENSES):
            continue
        title = page['title'].removeprefix('File:')
        out.append({
            'title': title, 'url': info.get('url'), 'page': info.get('descriptionurl'),
            'license': lic, 'author': clean(meta.get('Artist', {}).get('value'))[:120],
            'credit': clean(meta.get('Credit', {}).get('value'))[:120],
            'depicts': clean(meta.get('ImageDescription', {}).get('value'))[:200],
            'mime': info.get('mime', ''), 'size': f'{info.get("width", "?")}×{info.get("height", "?")}',
            'mb': round(info.get('size', 0) / 1e6, 1),
        })
    return out


def safe_name(title):
    stem, _, ext = title.rpartition('.')
    stem = re.sub(r'[^A-Za-z0-9]+', '_', stem).strip('_')[:60] or 'asset'
    return f'{stem}.{ext.lower()}'


ap = argparse.ArgumentParser()
ap.add_argument('query')
ap.add_argument('--video', action='store_const', const='video', dest='kind')
ap.add_argument('--image', action='store_const', const='image', dest='kind')
ap.add_argument('--limit', type=int, default=30)
ap.add_argument('--add', metavar='PROJECT')
a = ap.parse_args()

try:
    hits = search(a.query, a.kind, a.limit)
except Exception as e:
    sys.exit(f'Commons search failed: {e}')
if not hits:
    sys.exit('No free-to-use matches. Try a shorter query, the agency name, or the date.')
for i, h in enumerate(hits, 1):
    print(f'{i:>2}. {h["title"]}\n    {h["license"]} | {h["author"] or h["credit"]} | {h["size"]} | {h["mb"]} MB\n'
          f'    {h["depicts"]}\n    {h["url"]}')

if a.add:
    P = Path(a.add).expanduser().resolve()
    path = P / 'assets.json'
    assets = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    have = {x.get('url') for x in assets}
    added = 0
    for h in hits:
        if h['url'] in have:
            continue
        folder = 'real' if h['mime'].startswith('video') else 'media'
        assets.append({'file': f'{folder}/{safe_name(h["title"])}', 'url': h['url'], 'page': h['page'],
                       'kind': 'commons', 'depicts': h['depicts'] or h['title'],
                       'credit': h['author'] or h['credit'] or 'Wikimedia Commons',
                       'rights': h['license'] + ' (Wikimedia Commons)'})
        added += 1
    path.write_text(json.dumps(assets, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\nAdded {added} entries to {path}. Remove any that do not show the case, then run fetch.py.')
