"""Real archive footage with credit lines (free licences only), cut to the few seconds you need.

  python3 scripts/footage.py search "department store 1950s"           list clips: Wikimedia Commons videos + the Prelinger Archives
  python3 scripts/footage.py get "File:Chicago Scenes (ca. 1974).webm" media/ --start 95 --dur 8 --name chicago_1974
  python3 scripts/footage.py get ia:Shopping1957 media/ --start 120 --dur 7 --name shopping_1957
  python3 scripts/footage.py stock "empty shopping mall"                 optional stock clips from Pexels (needs a free key: see below)
  python3 scripts/footage.py get pexels:1234567 media/ --start 2 --dur 6 --name empty_mall

Where it looks, and why only there:
- Wikimedia Commons videos under public domain, CC0, CC BY or CC BY-SA (same rule as photos.py).
- The Internet Archive's Prelinger Archives and US government film collections (public domain industrial films, adverts,
  newsreels and city scenes, mostly 1900s to 1980s). Other Internet Archive uploads are refused: their licence tags are set
  by whoever uploaded them and are often wrong (TV adverts and VHS rips marked "public domain").
Footage is for the era, the place and the mood (a 1950s department store, Chicago in 1974, a trading floor). There is rarely
free footage of one named company: use photos for the company itself and never present generic footage as that company.
`get` downloads the source once (kept in ~/.finance-studio/footage-cache), cuts --dur seconds from --start, removes the sound
and writes media/<name>.mp4 plus media/<name>.mp4.credit.txt. Look at the clip before using it (`episode.py stills`).
Download one clip at a time. If a download prints SKIPPED, pick another clip instead of waiting."""
import sys, os, json, re, time, ssl, shutil, subprocess, argparse, urllib.request, urllib.parse, urllib.error

API = 'https://commons.wikimedia.org/w/api.php'
UA = 'FinanceDocumentaryStudio/1.1 (https://github.com/MoneyMasteryHub/free-claude-video-skills; documentary research by an individual user)'
OK = re.compile(r'(public domain|^pd|cc0|cc[- ]by(?![- ]nc)(?![- ]nd)|attribution)', re.I)
IA_OK = ('prelinger', 'prelingerhomemovies', 'universal_newsreels', 'FedFlix', 'usgovfilms', 'us_national_archives', 'nasa')
CACHE = os.path.join(os.path.expanduser('~'), '.finance-studio', 'footage-cache')
MAX_MB = 700


def _ctx():
    try:
        import certifi; return ssl.create_default_context(cafile=certifi.where())
    except Exception: return ssl.create_default_context()


def _ffmpeg():
    p = os.environ.get('FFMPEG') or shutil.which('ffmpeg')
    if p: return p
    try:
        import imageio_ffmpeg; return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception: sys.exit('ffmpeg not found. Run the setup script of this skill first.')


def _open(url, tries=4):
    for k in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60, context=_ctx())
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and k < tries - 1:
                wait = min(6 + 6 * k, 20); print(f'  the archive is busy, waiting {wait}s...', flush=True); time.sleep(wait); continue
            if e.code in (429, 503): sys.exit('SKIPPED: the archive kept refusing. Use another clip (do not retry this one now).')
            raise


def fetch(url): 
    with _open(url) as r: return r.read()


def clean(s): return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s or '')).strip()


# ---------------------------------------------------------------- Wikimedia Commons
def commons(params):
    q = dict(action='query', format='json', prop='videoinfo', viprop='url|size|extmetadata|derivatives', **params)
    d = json.loads(fetch(API + '?' + urllib.parse.urlencode(q))); out = []
    for p in (d.get('query', {}).get('pages', {}) or {}).values():
        vi = (p.get('videoinfo') or [{}])[0]; md = vi.get('extmetadata', {})
        lic = clean(md.get('LicenseShortName', {}).get('value')); art = clean(md.get('Artist', {}).get('value'))
        url, size = vi.get('url'), vi.get('size') or 0
        if size > 150e6:                                   # big original: take Commons' own 1080p/720p transcode instead
            ds = [x for x in vi.get('derivatives', []) if (x.get('height') or 0) in (720, 1080) and 'video' in (x.get('type') or '')]
            if ds: url = sorted(ds, key=lambda x: -x['height'])[0]['src']; size = 0
        out.append(dict(title=p['title'], url=url, page=vi.get('descriptionurl'), licence=lic, author=art, dur=vi.get('duration') or 0,
                        w=vi.get('width'), h=vi.get('height'), mb=size / 1e6,
                        ok=bool(OK.search(lic)) and 'non-free' not in lic.lower() and 'fair use' not in lic.lower()))
    return out


# ---------------------------------------------------------------- Internet Archive (Prelinger + US government only)
def ia_search(q):
    cols = ' OR '.join('collection:' + c for c in IA_OK)
    u = 'https://archive.org/advancedsearch.php?' + urllib.parse.urlencode({'q': f'({q}) AND mediatype:movies AND ({cols})', 'rows': 12, 'output': 'json', 'sort[]': 'downloads desc'}) \
        + '&fl[]=identifier&fl[]=title&fl[]=year&fl[]=collection'
    return json.loads(fetch(u)).get('response', {}).get('docs', [])


def ia_item(ident):
    d = json.loads(fetch('https://archive.org/metadata/' + urllib.parse.quote(ident))); md = d.get('metadata', {})
    cols = md.get('collection', []); cols = [cols] if isinstance(cols, str) else cols
    which = next((c for c in cols if c in IA_OK), None)
    if not which: sys.exit(f"Refused: '{ident}' is not in the Prelinger Archives or a US government film collection, so its licence can't be trusted.")
    vids = [f for f in d.get('files', []) if f.get('name', '').lower().endswith(('.mp4', '.m4v', '.ogv', '.mpeg', '.mpg')) and int(f.get('size') or 0) > 0]
    if not vids: sys.exit('No video file found in that item. Pick another clip.')
    mp4 = [f for f in vids if f['name'].lower().endswith('.mp4')] or vids
    f = sorted(mp4, key=lambda f: abs(int(f['size']) - 120e6))[0]                 # a mid-size copy: good enough at 1080p, quick to fetch
    title = clean(md.get('title') if isinstance(md.get('title'), str) else (md.get('title') or [''])[0]); year = md.get('year') or (md.get('date') or '')[:4]
    src = 'Prelinger Archives' if which.startswith('prelinger') else 'US government film'
    return dict(title=title, url=f'https://archive.org/download/{urllib.parse.quote(ident)}/{urllib.parse.quote(f["name"])}', page=f'https://archive.org/details/{ident}',
                licence='public domain', credit=f'{title}{" (" + str(year) + ")" if year else ""} / {src} / Internet Archive / public domain', mb=int(f['size']) / 1e6)


def search(q):
    print('--- Wikimedia Commons (videos)')
    try:
        for r in commons(dict(generator='search', gsrsearch=f'filetype:video {q}', gsrnamespace=6, gsrlimit=12)):
            print(('OK  ' if r['ok'] else 'NO  ') + f"{r['title']}\n    {r['dur']:.0f}s, {r['w']}x{r['h']} | licence: {r['licence']} | author: {r['author'][:70]}\n    {r['page']}")
    except SystemExit as e: print(' ', e)
    except Exception as e: print('  Could not reach Wikimedia Commons:', e)
    time.sleep(1)
    print('--- Internet Archive (Prelinger Archives and US government films, public domain)')
    try:
        for x in ia_search(q): print(f"OK  ia:{x['identifier']}\n    {x.get('title')} ({x.get('year', '?')})\n    https://archive.org/details/{x['identifier']}")
    except Exception as e: print('  Could not reach the Internet Archive:', e)
    print('\nWatch a clip in the browser first, note the second where the good part starts, then: footage.py get <id> media/ --start S --dur D --name short_name')


# ---------------------------------------------------------------- stock footage (Pexels: free, commercial use allowed, no credit required)
def _pexels_key():
    k = os.environ.get('PEXELS_API_KEY'); f = os.path.join(os.path.expanduser('~'), '.finance-studio', 'pexels.key')
    if not k and os.path.exists(f): k = open(f).read().strip()
    if not k: sys.exit('Stock footage is optional and needs a free Pexels key. Ask the user to make a free account at pexels.com, copy the key from\n'
                       'pexels.com/api and paste it to you; then save it with:  footage.py key THE_KEY   (one time). Without it, use photos and archive film.')
    return k

def _pexels(path):
    try:
        with urllib.request.urlopen(urllib.request.Request('https://api.pexels.com/videos/' + path, headers={'Authorization': _pexels_key(), 'User-Agent': UA}), timeout=40, context=_ctx()) as r: return json.loads(r.read())
    except urllib.error.HTTPError as e: sys.exit('Pexels refused the request (' + str(e.code) + '). Check the key, or use photos and archive film.')

def _best(files):
    v = [f for f in files if (f.get('file_type') or '').endswith('mp4') and f.get('width')]
    ok = [f for f in v if 1280 <= max(f['width'], f['height']) <= 1920] or v
    return sorted(ok, key=lambda f: -f['width'] * f['height'])[0]

def stock_search(q):
    d = _pexels('search?' + urllib.parse.urlencode(dict(query=q, per_page=12, orientation='landscape')))
    for v in d.get('videos', []): print(f"OK  pexels:{v['id']}\n    {v['duration']}s, {v['width']}x{v['height']} | by {v['user']['name']}\n    {v['url']}")
    print('\nStock is for mood only (a skyline, an empty mall, a trading screen). Never tag it with a date or place, and never present it as the real event.')


def download(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 1000: return
    os.makedirs(os.path.dirname(path), exist_ok=True); tmp = path + '.part'
    with _open(url) as r, open(tmp, 'wb') as f:
        total = int(r.headers.get('Content-Length') or 0)
        if total > MAX_MB * 1e6: sys.exit(f'SKIPPED: that file is {total / 1e6:.0f} MB. Pick a smaller clip.')
        done = 0; last = time.time()
        while True:
            b = r.read(1 << 20)
            if not b: break
            f.write(b); done += len(b)
            if done > MAX_MB * 1e6: sys.exit('SKIPPED: file too large. Pick a smaller clip.')
            if time.time() - last > 5: print(f'  {done / 1e6:.0f} MB' + (f' of {total / 1e6:.0f}' if total else ''), flush=True); last = time.time()
    os.replace(tmp, path)


def get(ref, dest, start, dur, name):
    os.makedirs(dest, exist_ok=True)
    if ref.lower().startswith('pexels:'):
        v = _pexels('videos/' + ref[7:]); f = _best(v['video_files'])
        r = dict(url=f['link'], page=v['url']); key = 'pexels_' + ref[7:]; credit = f"Stock video: {v['user']['name']} / Pexels (free licence, mood footage, not the real event)"
    elif ref.lower().startswith('ia:'):
        r = ia_item(ref[3:]); key = 'ia_' + ref[3:]; credit = r['credit']
    else:
        r = commons(dict(titles=ref))[0]
        if not r.get('url'): sys.exit('Not found on Wikimedia Commons: ' + ref)
        if not r['ok']: sys.exit(f"Refused: licence is '{r['licence']}'. Pick a public-domain or CC BY / CC BY-SA clip.")
        key = 'c_' + ref.split(':', 1)[-1]; credit = f"{r['author'] or 'Unknown author'} / Wikimedia Commons / {r['licence']}"
    key = re.sub(r'[^A-Za-z0-9._-]+', '_', key)[:90]; src = os.path.join(CACHE, key + (os.path.splitext(urllib.parse.urlparse(r['url']).path)[1] or '.mp4'))
    print('downloading the source once (kept for other cuts):', r['url']); download(r['url'], src)
    name = re.sub(r'[^A-Za-z0-9._-]+', '_', name or key); out = os.path.join(dest, name + '.mp4')
    vf = "scale='if(gt(a,16/9),-2,1920)':'if(gt(a,16/9),1080,-2)',fps=30,format=yuv420p"
    p = subprocess.run([_ffmpeg(), '-v', 'error', '-y', '-ss', str(start), '-i', src, '-t', str(dur), '-an', '-vf', vf, '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', '-movflags', '+faststart', out])
    if p.returncode or not os.path.exists(out) or os.path.getsize(out) < 2000: sys.exit('Could not cut that clip (is --start past the end?). Try other times or another clip.')
    open(out + '.credit.txt', 'w', encoding='utf-8').write(credit + '\n' + r['page'] + f'\nseconds {start} to {float(start) + float(dur):g}\n')
    print('saved', out, f'({dur}s)\ncredit:', credit); time.sleep(1)


if __name__ == '__main__':
    if len(sys.argv) < 3: print(__doc__); sys.exit()
    if sys.argv[1] == 'search': search(' '.join(sys.argv[2:]))
    elif sys.argv[1] == 'stock': stock_search(' '.join(sys.argv[2:]))
    elif sys.argv[1] == 'key':
        os.makedirs(os.path.dirname(CACHE), exist_ok=True); open(os.path.join(os.path.dirname(CACHE), 'pexels.key'), 'w').write(sys.argv[2].strip()); print('Pexels key saved.')
    elif sys.argv[1] == 'get':
        a = argparse.ArgumentParser(); a.add_argument('ref'); a.add_argument('dest', nargs='?', default='media')
        a.add_argument('--start', type=float, default=0); a.add_argument('--dur', type=float, default=8); a.add_argument('--name')
        o = a.parse_args(sys.argv[2:]); get(o.ref, o.dest, o.start, o.dur, o.name)
    else: print(__doc__)
