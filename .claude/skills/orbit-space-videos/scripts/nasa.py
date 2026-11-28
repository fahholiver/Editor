"""Find and download public NASA images/videos for evidence shots.
  python3 scripts/nasa.py search "venus magellan" [--video] [--n 12]   -> list results (id, title, credit, flags)
  python3 scripts/nasa.py get <nasa_id> [out_dir]                     -> download the largest file + credit.txt
NASA media is generally not copyrighted, but: credit NASA, never imply NASA endorses the video, keep the NASA logo off
thumbnails, and SKIP anything whose credit names another owner (marked THIRD-PARTY below).
If the network blocks images-api.nasa.gov, the script prints links for the user to download by hand."""
import sys, json, os, re, urllib.request, urllib.parse, urllib.error
API = 'https://images-api.nasa.gov'
import ssl
def _ctx():
    # Python from python.org on macOS ships without root certificates until "Install Certificates.command" is run.
    # Fall back to certifi's bundle so NASA downloads work anyway.
    try:
        import certifi; return ssl.create_default_context(cafile=certifi.where())
    except Exception: return ssl.create_default_context()
CTX = _ctx()
def get(u):
    req = urllib.request.Request(u, headers={'User-Agent': 'orbit-space-skill'})
    try:
        with urllib.request.urlopen(req, timeout=30, context=CTX) as r: return r.read()
    except urllib.error.URLError as e:
        if 'CERTIFICATE' not in str(e).upper(): raise
        with urllib.request.urlopen(req, timeout=30, context=ssl.create_default_context()) as r: return r.read()
def third_party(d):
    blob = ' '.join(str(d.get(k, '')) for k in ('photographer', 'secondary_creator', 'description', 'center')).lower()
    return bool(re.search(r'©|copyright|courtesy of (?!nasa)|getty|reuters|associated press|\bap photo\b|esa/|roscosmos|jaxa', blob))
def manual(q): print(f'\nCould not reach NASA from this computer. Open these and download the largest JPG/MP4 by hand:\n  https://images.nasa.gov/search?q={urllib.parse.quote(q)}\n  https://science.nasa.gov/photojournal/ (search "{q}")\nSave them into the project folder and tell Claude the file names.'); sys.exit(2)
cmd = sys.argv[1] if len(sys.argv) > 1 else ''
if cmd == 'search':
    q = sys.argv[2]; mt = 'video' if '--video' in sys.argv else 'image'; n = int(sys.argv[sys.argv.index('--n') + 1]) if '--n' in sys.argv else 12
    try: res = json.loads(get(f'{API}/search?q={urllib.parse.quote(q)}&media_type={mt}'))
    except Exception: manual(q)
    for it in res['collection']['items'][:n]:
        d = it['data'][0]; flag = 'THIRD-PARTY (skip)' if third_party(d) else 'ok'
        print(f"{d['nasa_id']:<28} | {d.get('title','')[:60]:<60} | {d.get('center','')} {d.get('date_created','')[:4]} | {flag}")
elif cmd == 'get':
    nid = sys.argv[2]; out = sys.argv[3] if len(sys.argv) > 3 else 'media'; os.makedirs(out, exist_ok=True)
    try: files = json.loads(get(f'{API}/asset/{urllib.parse.quote(nid)}'))['collection']['items']; meta = json.loads(get(f'{API}/search?nasa_id={urllib.parse.quote(nid)}'))['collection']['items'][0]['data'][0]
    except Exception: manual(nid)
    hrefs = [f['href'] for f in files]
    pick = next((h for pat in ('~orig.jpg', '~large.jpg', '~orig.mp4', '~large.mp4', '~medium.mp4', '.jpg', '.mp4') for h in hrefs if h.lower().endswith(pat)), None)
    if not pick: print('no jpg/mp4 in', hrefs[:5]); sys.exit(1)
    ext = os.path.splitext(pick)[1]; dst = os.path.join(out, re.sub(r'[^\w-]', '_', nid) + ext)
    open(dst, 'wb').write(get(pick.replace(' ', '%20')))
    credit = f"Credit: NASA{('/' + meta['center']) if meta.get('center') else ''}{(' / ' + meta['photographer']) if meta.get('photographer') else ''}"
    open(dst + '.credit.txt', 'w').write(credit + '\n' + meta.get('title', '') + '\n')
    print(dst, '|', credit, '| THIRD-PARTY: do not use' if third_party(meta) else '')
else: print(__doc__)
