"""Real photos with credit lines from Wikimedia Commons (free licences only).

  python3 scripts/photos.py search "Crown of Empress Eugenie"        list matches with licence and author
  python3 scripts/photos.py get "File:Some name.jpg" media/            download (1920 px) + write media/<name>.credit.txt

Accepted licences: public domain, CC0, CC BY, CC BY-SA (credit shown on screen and in the description).
Anything else (fair use, non-free, "all rights reserved") is refused. Download photos one at a time (never in parallel);
if a file prints SKIPPED, move on to another photo instead of waiting. If the network blocks Commons, the script prints
the page links so the user can save the images into media/ by hand."""
import sys, os, json, re, time, ssl, urllib.request, urllib.parse, urllib.error

API = 'https://commons.wikimedia.org/w/api.php'
UA = 'FinanceDocumentaryStudio/1.1 (https://github.com/MoneyMasteryHub/free-claude-video-skills; documentary research by an individual user)'
OK = re.compile(r'(public domain|^pd|cc0|cc[- ]by(?![- ]nc)(?![- ]nd)|attribution)', re.I)


def _ctx():
    try:
        import certifi; return ssl.create_default_context(cafile=certifi.where())
    except Exception: return ssl.create_default_context()


def fetch(url, tries=4):
    """Short, capped waits when Commons is busy (about 30 s at most in total), then give up on this file so the film
    never stalls on one photo: pick another photo instead."""
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=30, context=_ctx()) as r: return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and k < tries - 1:
                ra = e.headers.get('Retry-After', '') if e.headers else ''
                wait = min(int(ra) if ra.isdigit() else 4 + 4 * k, 12)
                print(f'  Commons is busy, waiting {wait}s...', flush=True); time.sleep(wait); continue
            if e.code in (429, 503): sys.exit('SKIPPED: Commons kept refusing this file. Use another photo (do not retry this one now).')
            raise


def clean(s): return re.sub(r'<[^>]+>', '', s or '').strip()


def info(params):
    q = dict(action='query', format='json', prop='imageinfo', iiprop='url|extmetadata', iiurlwidth=1920, **params)
    d = json.loads(fetch(API + '?' + urllib.parse.urlencode(q)))
    out = []
    for p in (d.get('query', {}).get('pages', {}) or {}).values():
        ii = (p.get('imageinfo') or [{}])[0]; md = ii.get('extmetadata', {})
        lic = clean(md.get('LicenseShortName', {}).get('value')); art = clean(md.get('Artist', {}).get('value'))
        out.append(dict(title=p['title'], url=ii.get('thumburl') or ii.get('url'), page=ii.get('descriptionurl'), licence=lic, author=art,
                        ok=bool(OK.search(lic)) and 'non-free' not in lic.lower() and 'fair use' not in lic.lower()))
    return out


def search(q):
    try: res = info(dict(generator='search', gsrsearch=f'filetype:bitmap {q}', gsrnamespace=6, gsrlimit=12))
    except Exception as e:
        print('Could not reach Wikimedia Commons:', e)
        print('Open this search and save the images into media/ yourself, noting the author and licence:')
        print('  https://commons.wikimedia.org/w/index.php?search=' + urllib.parse.quote(q) + '&title=Special:MediaSearch&type=image'); return
    for r in res: print(('OK  ' if r['ok'] else 'NO  ') + f"{r['title']}\n    licence: {r['licence']} | author: {r['author'][:80]}\n    {r['page']}")


def get(title, dest):
    os.makedirs(dest, exist_ok=True)
    r = info(dict(titles=title))[0]
    if not r['ok']: sys.exit(f"Refused: licence is '{r['licence']}'. Pick a public-domain or CC BY / CC BY-SA image.")
    name = re.sub(r'[^A-Za-z0-9._-]+', '_', title.split(':', 1)[1]); path = os.path.join(dest, name)
    open(path, 'wb').write(fetch(r['url'])); time.sleep(1)      # one file at a time with a short pause: Commons throttles bursts
    credit = f"{r['author'] or 'Unknown author'} / Wikimedia Commons / {r['licence']}"
    open(path + '.credit.txt', 'w').write(credit + '\n' + r['page'] + '\n'); print('saved', path, '\ncredit:', credit)


if __name__ == '__main__':
    if len(sys.argv) < 3: print(__doc__); sys.exit()
    {'search': lambda: search(sys.argv[2]), 'get': lambda: get(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'media')}[sys.argv[1]]()
