#!/usr/bin/env python3
"""The owner's posting rules come from a Google Sheet ("Buffer Contas"), one row per account:

    Conta principal | Hora de postagem | Conta repostagem | País-Língua | Modelo-skill | Gerar s/n
    mandraketoons   | 14:00            | Coyote's Jazz, proper_laughs_uk | UK-Inglês | confession | s
    strawberry.me27 | 14:00            |                 |             |              | n

- every time is London time (Europe/London); the repost accounts post the same video at the same time
- Conta repostagem: comma-separated Buffer channel names (TikTok, Instagram, YouTube)
- País-Língua: anything naming the country or language (UK / Inglês / en-GB, Alemanha / DE, França / FR ...)
- Modelo-skill: story format (formats/*.md) and/or engine (motion, vintage, vox, cartoon) and/or Motion
  visual style (styles/*.py), separated by / or + (e.g. "parable/vintage")
- Gerar = s: a new story every day (daily-shorts skill); n: the ready-made videos from the Drive queue
  (queue_post.py), one different file per account

The sheet can stay private: it is read with the owner's own Google login (GDRIVE_FULL_REFRESH_TOKEN). Each
successful read is cached in Drive _state/accounts_sheet.csv; if Google fails the run uses that copy.
Technical details (voices, words, seconds, aspect) stay in accounts.json: per account, else per language
(`_languages`).

    python3 sheet.py            # print the rules the run will use
    python3 sheet.py --csv      # print the raw sheet

Env: ACCOUNTS_SHEET_ID (default: the owner's sheet), ACCOUNTS_SHEET_CSV (a local CSV instead, for tests).
"""
import csv
import io
import os
import re
import sys
import tempfile
import unicodedata

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gdrive  # noqa: E402

SHEET_ID = os.environ.get('ACCOUNTS_SHEET_ID', '152_rw1qpLMHeCPw2R48N66MjDgBBHZlKilqIOJx4XKQ')
CACHE = 'accounts_sheet.csv'
TZ = 'Europe/London'
ENGINES = ('motion', 'vintage', 'vox', 'cartoon')
ENGINE_LOOK = {'vintage': {'aspect': '1:1', 'music_bed': False}, 'vox': {'aspect': '1:1', 'music_bed': False},
               'motion': {'aspect': '9:16', 'music_bed': True}, 'cartoon': {'aspect': '9:16', 'music_bed': True}}
# words that name a language/country -> locales/<code>.md
LANG_WORDS = {
    'en-GB': ('en', 'en-gb', 'uk', 'gb', 'ingles', 'english', 'inglaterra', 'reino unido', 'britain', 'england'),
    'de-DE': ('de', 'de-de', 'alemao', 'alema', 'alemanha', 'german', 'germany', 'deutsch', 'deutschland'),
    'fr-FR': ('fr', 'fr-fr', 'frances', 'francesa', 'franca', 'french', 'france', 'francais'),
}
COLS = {'account': ('conta principal', 'conta'), 'time': ('hora', 'horario'), 'repost': ('repost',),
        'lang': ('pais', 'lingua', 'idioma'), 'model': ('modelo', 'skill', 'formato'), 'generate': ('gerar',)}


def _plain(s):
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode()
    return re.sub(r'\s+', ' ', s).strip().lower()


def _fetch():
    """raw CSV text of the sheet's first tab"""
    if os.environ.get('ACCOUNTS_SHEET_CSV'):
        return open(os.environ['ACCOUNTS_SHEET_CSV'], encoding='utf-8').read()
    r = requests.get('%s/files/%s/export' % (gdrive.API, SHEET_ID), params={'mimeType': 'text/csv'}, timeout=60,
                     headers={'Authorization': 'Bearer ' + gdrive.access_token(full=True)})
    if r.status_code != 200:
        raise RuntimeError('sheet export %d: %s' % (r.status_code, r.text[:300]))
    r.encoding = 'utf-8'
    return r.text


def raw_csv():
    """the sheet (cached to Drive on success); on failure the last cached copy; None if neither exists"""
    try:
        text = _fetch()
        if not os.environ.get('ACCOUNTS_SHEET_CSV'):
            try:
                with tempfile.TemporaryDirectory() as tmp:
                    p = os.path.join(tmp, CACHE)
                    open(p, 'w', encoding='utf-8').write(text)
                    gdrive.put_state(p, CACHE)
            except Exception as e:  # noqa: BLE001
                print('warning: could not cache the sheet in Drive: %s' % e, file=sys.stderr)
        return text
    except BaseException as e:  # noqa: BLE001 - SystemExit from a missing token too
        print('WARNING: could not read the accounts sheet (%s); using the last copy in Drive' % e, file=sys.stderr)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                p = os.path.join(tmp, CACHE)
                if gdrive.get_state(CACHE, p):
                    return open(p, encoding='utf-8').read()
        except BaseException as e2:  # noqa: BLE001
            print('WARNING: no cached sheet either (%s)' % e2, file=sys.stderr)
    return None


def _language(v, errors, acc):
    p = _plain(v)
    if not p:
        return None
    for code in LANG_WORDS:   # exact code first (en-GB)
        if p == code.lower():
            return code
    toks = set(re.split(r'[\s/\-_,;()|]+', p)) | {p}
    for code, words in LANG_WORDS.items():
        if any(w in toks or (' ' in w and w in p) for w in words):
            return code
    errors.append('%s: País-Língua "%s" not understood (known: %s)' % (acc, v, ', '.join(LANG_WORDS)))
    return None


def _model(v, errors, acc):
    out = {}
    formats = {f[:-3] for f in os.listdir(os.path.join(HERE, 'formats')) if f.endswith('.md')}
    styles = {f[:-3] for f in os.listdir(os.path.join(HERE, 'styles')) if f.endswith('.py') and f != 'series_kit.py'}
    for t in [t for t in re.split(r'[/+,;|]+|\s+', _plain(v)) if t]:
        t = t.replace('-', '_')
        if t in ENGINES:
            out['engine'] = t
        elif t in formats:
            out['format'] = t
        elif t in styles:
            out['visual_style'] = t
        else:
            errors.append('%s: Modelo-skill "%s" not understood (formats: %s; engines: %s; styles: %s)'
                          % (acc, t, ', '.join(sorted(formats)), ', '.join(ENGINES), ', '.join(sorted(styles))))
    return out


def parse(text):
    """-> (rows, errors); a row = {account, post_time, reposts, language, model, generate}"""
    rows, errors = [], []
    table = [r for r in csv.reader(io.StringIO(text or '')) if any(c.strip() for c in r)]
    if not table:
        return rows, ['the sheet is empty']
    head = [_plain(h) for h in table[0]]
    idx = {}
    for key, words in COLS.items():
        for i, h in enumerate(head):
            if i not in idx.values() and any(w in h for w in words) and not (key == 'account' and 'repost' in h):
                idx[key] = i
                break
    missing = [k for k in ('account', 'time', 'generate') if k not in idx]
    if missing:
        return rows, ['header row not recognised (missing %s): %s' % (', '.join(missing), table[0])]
    cell = lambda r, k: (r[idx[k]].strip() if k in idx and idx[k] < len(r) else '')  # noqa: E731
    for r in table[1:]:
        acc = cell(r, 'account').lstrip('@')
        if not acc:
            continue
        t = cell(r, 'time').lower().replace('h', ':').replace('.', ':').rstrip(':')
        m = re.match(r'^(\d{1,2})(?::(\d{2}))?', t)
        if not m or int(m.group(1)) > 23:
            errors.append('%s: Hora de postagem "%s" not understood (use 14:00)' % (acc, cell(r, 'time')))
            continue
        gen = _plain(cell(r, 'generate'))
        rows.append({
            'account': acc,
            'post_time': '%02d:%s' % (int(m.group(1)), m.group(2) or '00'),
            'reposts': [x.strip().lstrip('@') for x in re.split(r'[,;\n]+', cell(r, 'repost')) if x.strip()],
            'language': _language(cell(r, 'lang'), errors, acc),
            'model': _model(cell(r, 'model'), errors, acc),
            'generate': gen[:1] in ('s', 'y', '1', 't', 'x'),   # s / sim / yes / TRUE (checkbox)
        })
    seen = set()
    for row in rows:
        if row['account'].lower() in seen:
            errors.append('%s: listed twice (the last row wins)' % row['account'])
        seen.add(row['account'].lower())
    return rows, errors


_CACHE = {}


def rows():
    """parsed rows of the sheet, or None when there is no sheet at all (then accounts.json alone is used)"""
    if 'rows' not in _CACHE:
        text = raw_csv()
        if text is None:
            _CACHE['rows'] = None
        else:
            r, errors = parse(text)
            for e in errors:
                print('SHEET: ' + e, file=sys.stderr)
            _CACHE['rows'] = {x['account']: x for x in r} if r else None
    return _CACHE['rows']


def _past_changes(c, today):
    c = dict(c)
    for day, over in sorted((c.pop('changes_from', None) or {}).items()):
        if day <= today:
            c.update(over)
    c.pop('active_from', None)
    return c


def merged(cfg, today):
    """accounts.json + the sheet -> the same shape as accounts.json, holding only the sheet's gerar=s accounts.
    None when there is no sheet (the caller keeps accounts.json as it is)."""
    sheet = rows()
    if sheet is None:
        return None
    langs = cfg.get('_languages', {})
    out = {k: v for k, v in cfg.items() if k.startswith('_')}
    for acc, row in sheet.items():
        if not row['generate']:
            continue
        old = _past_changes(cfg.get(acc, {}), today)
        lang = row['language'] or old.get('language') or cfg.get('_default', {}).get('language', 'en-GB')
        c = dict(old)
        if lang != old.get('language'):   # new account or a new language: voices + lengths from that language
            for k in ('elevenlabs_voice', 'edge_voice', 'words', 'seconds'):
                c.pop(k, None)
            c.update(langs.get(lang, {}))
        m = row['model']
        if m.get('engine') and m['engine'] != old.get('engine', 'motion'):
            c.update(ENGINE_LOOK[m['engine']])
            if m['engine'] != 'motion':
                c.pop('visual_style', None)
        c.update(m)
        if m.get('engine') == 'motion' and 'visual_style' not in m:
            c.pop('visual_style', None)
        c.update(language=lang, post_time=row['post_time'], tz=TZ,
                 also_post_to=[{'channel': n, 'name': n, 'post_time': row['post_time'], 'tz': TZ} for n in row['reposts']])
        out[acc] = c
    return out


def queue_rows():
    """gerar=n rows (the Drive queue accounts), or None when there is no sheet"""
    sheet = rows()
    return None if sheet is None else [r for r in sheet.values() if not r['generate']]


if __name__ == '__main__':
    if '--csv' in sys.argv:
        print(raw_csv() or '(no sheet)')
        sys.exit()
    import plan
    cfg = plan.config()
    print('source:', 'sheet' if rows() is not None else 'accounts.json (no sheet)')
    for acc, c in cfg.items():
        if acc.startswith('_'):
            continue
        print('NEW STORY  %-18s %s %s %s  %s  engine %s%s  reposts: %s' % (
            acc, c['post_time'], c['tz'], c['language'], c['format'], c.get('engine', 'motion'),
            (' style ' + c['visual_style']) if c.get('visual_style') else '',
            ', '.join(m['name'] for m in c.get('also_post_to', [])) or '-'))
    for r in queue_rows() or []:
        print('DRIVE QUEUE %-17s %s %s  reposts: %s' % (r['account'], r['post_time'], TZ, ', '.join(r['reposts']) or '-'))
