#!/usr/bin/env python3
"""Viral lab: research what went viral in the account's niche in the last 24 h (TikTok via Apify), then score
the scripts written for it and only let an APPROVED script become a video.

Cycle per account (see .claude/skills/daily-shorts/SKILL.md, step 1):
  research -> patterns -> 3 original scripts -> evaluate -> improve -> select the best -> approve -> video

    python3 viral_lab.py research --account <acc>             # Apify search, last 24 h -> /tmp/viral/<acc>.research.md
    python3 viral_lab.py evaluate --account <acc> <story.txt> [<story2.txt> ...] --judge <judge.json>
    python3 viral_lab.py approve  --account <acc> <story.txt>   # exit 0 only if the score >= threshold
    python3 viral_lab.py status                                # today's research / best scores / approvals
    python3 viral_lab.py sync                                  # append today's evaluations to Drive _state/viral_lab.jsonl
    python3 viral_lab.py research --account <acc> --sample items.json   # offline test with saved Apify items

Apify keys rotate: APIFY_TOKENS=key1,key2,... (the first with credit is used; out of credit -> the next one).

research: TikTok search (Apify actor, default `themineworks~tiktok-search-scraper`, override with APIFY_ACTOR)
for the keywords of the account's format + language (daily/viral/niches.json, + "niche_keywords" in
accounts.json), videos of the last 24 h with >= "viral_min_plays" views (default 100000). Each video gets a
viral score from its view velocity (views/hour) and weighted engagement ((likes + 2*comments + 3*shares)/views).
The report lists the top videos, hashtags, recurring words, typical length and openings - techniques and themes
only: never copy a story, line or character. Cached per format+language for the day and in Drive
`_state/viral_research_<format>_<lang>.json`; if Apify fails, the newest cached research (<= 3 days) is used.

evaluate: `--judge` is the strict rubric scoring written by the session (JSON, see JUDGE_TEMPLATE / `judge-template`);
if GEMINI_API_KEY is set an independent Gemini judge scores the same rubric and the two are averaged. Plus
measured checks (length, hook length, final question, loop back to the hook, line length, trend fit,
similarity to the account's past hooks). final = 0.75 * judge + 0.25 * checks. A hard fail (wrong length, no
final question, near-copy of an earlier hook) blocks approval whatever the score.

approve: writes /tmp/viral/<acc>.approved.json with the story's hash. bootstrap.py and studio.py setup refuse
to make a video for --account <acc> unless that exact text is approved (VIRAL_GATE=off disables the gate).
The score is a heuristic judgement of the script, NOT a probability of going viral: metrics.py compares it
with the real views so the rubric can be recalibrated.
"""
import argparse
import collections
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT = os.environ.get('VIRAL_DIR', '/tmp/viral')
NICHES = os.path.join(HERE, 'viral', 'niches.json')
ACTOR = os.environ.get('APIFY_ACTOR', 'themineworks~tiktok-search-scraper')
DEFAULT_THRESHOLD = 80
DEFAULT_MIN_PLAYS = 100000
MAX_KEYWORDS = 7

# rubric: criterion -> (weight, what a 9-10 means). Weights sum to 100.
RUBRIC = collections.OrderedDict([
    ('hook', (20, 'first line (<= 2 s) creates an open loop or a threat the viewer cannot scroll past')),
    ('retention', (15, 'every 3-5 s a new question, reveal or escalation; no line that could be cut')),
    ('payoff', (15, 'the twist/answer is surprising AND fair (set up earlier), lands in the last 10 s')),
    ('trend_fit', (10, 'uses a theme/angle/format that is working in the niche TODAY (research report)')),
    ('originality', (10, 'premise, twist and images are new: not a known creepypasta, not a past story of ours')),
    ('comment_bait', (8, 'final question answerable in one word that people will want to argue about')),
    ('rewatch_loop', (7, 'the last line runs straight back into the first; a detail rewards a 2nd watch')),
    ('emotion', (10, 'a strong, specific feeling (dread, awe, being understood) in a relatable local setting')),
    ('visual', (5, 'every beat is a clear, drawable 2D image for our engine; no crowds/gore/complex action')),
])
JUDGE_TEMPLATE = {
    'scores': {k: 0 for k in RUBRIC},
    'why': {k: 'one line' for k in RUBRIC},
    'improve': ['the 1-3 concrete changes that would raise the lowest scores'],
}
STOP = set('''a an the and or but of to in on at for with from by is are was were be been it its this that these those
i you he she we they me my your our their his her them us as if so not no do does did have has had will would can
could just then than there here what when where who why how all any some one two very into out up down over about
der die das und oder aber ein eine einer eines den dem des ist sind war waren zu im in am an auf für mit von bei
ich du er sie es wir ihr mich dich mir dir sich nicht kein keine wenn dann als wie was wer wo noch nur auch so
le la les un une des du de et ou mais à au aux en dans sur pour par avec est sont était je tu il elle nous vous
ils elles me te se ne pas plus que qui quoi quand où comme si ce cette ces mon ton son ma ta sa mes tes ses
fyp foryou foryoupage viral pourtoi fürdich fy trending tiktok xyzbca parati'''.split())


def today():
    from zoneinfo import ZoneInfo
    return os.environ.get('PLAN_DATE') or dt.datetime.now(ZoneInfo('Europe/London')).date().isoformat()


def acc_file(acc, ext):
    os.makedirs(OUT, exist_ok=True)
    return os.path.join(OUT, '%s.%s' % (acc.replace('/', '_'), ext))


def account(acc):
    import plan
    return plan.account_cfg(acc)


def lang2(c):
    return c.get('language', 'en-GB')


# ---------------------------------------------------------------- research
def keywords(c):
    n = json.load(open(NICHES, encoding='utf-8'))
    lang = lang2(c)
    fmt = n.get(c.get('format'), {})
    own = list(c.get('niche_keywords') or [])
    local = fmt.get(lang, []) if not lang.startswith('en') else []
    eng = fmt.get('en', []) or n['_any']['en']
    seen, out = set(), []
    extra = (n['_any'].get(lang, []) + n['_any']['en']) if not fmt else []   # unknown format: generic dark animation
    for k in own + local + eng + extra:
        if k.lower() not in seen:
            seen.add(k.lower())
            out.append(k)
    return out[:MAX_KEYWORDS]


def apify_tokens():
    """APIFY_TOKENS = several keys separated by commas, used in order: when one runs out of credit (or is
    refused) the next one takes over - like ELEVENLABS_API_KEYS. APIFY_TOKEN with a single key also works;
    with none, a placeholder that the proxy replaces with a network secret saved for api.apify.com."""
    toks = []
    for name in ('APIFY_TOKENS', 'APIFY_TOKEN', 'APIFY_API_TOKEN'):
        toks += [t.strip() for t in os.environ.get(name, '').replace(';', ',').split(',') if t.strip()]
    return list(dict.fromkeys(toks)) or ['apify_api_placeholder']


class KeyExhausted(RuntimeError):
    """this Apify key cannot run the search (no credit, usage limit, invalid): try the next key"""


def _apify(method, path, tok, body=None, timeout=90):
    req = urllib.request.Request('https://api.apify.com/v2' + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        msg = 'Apify %s %s: %s' % (e.code, path.split('?')[0], e.read().decode('utf-8', 'replace')[:300])
        if e.code in (401, 402, 403, 429):
            raise KeyExhausted(msg)
        raise RuntimeError(msg)


def key_has_credit(tok):
    """False when the key's monthly usage already reached its limit (skip it without starting a run)"""
    try:
        d = _apify('GET', '/users/me/limits', tok, timeout=30)['data']
        used = (d.get('current') or {}).get('monthlyUsageUsd')
        cap = (d.get('limits') or {}).get('maxMonthlyUsageUsd')
        return not (used is not None and cap and used >= cap * 0.98)
    except KeyExhausted:
        return False
    except Exception:  # noqa: BLE001 - cannot tell: try it
        return True


def run_actor(kws, min_plays, per_kw=30, max_wait=900):
    """run the search with the first Apify key that has credit; on running out, the next key"""
    toks, errors = apify_tokens(), []
    for i, tok in enumerate(toks):
        label = 'key %d/%d' % (i + 1, len(toks))
        if len(toks) > 1 and not key_has_credit(tok):
            errors.append('%s: monthly limit reached' % label)
            print('Apify %s: no credit left - next key' % label)
            continue
        try:
            run = _apify('POST', '/acts/%s/runs?waitForFinish=60' % urllib.parse.quote(ACTOR, safe='~'), tok,
                         actor_input(kws, min_plays, per_kw))['data']
            t0 = time.time()
            while run.get('status') in ('READY', 'RUNNING') and time.time() - t0 < max_wait:
                run = _apify('GET', '/actor-runs/%s?waitForFinish=60' % run['id'], tok)['data']
            if run.get('status') != 'SUCCEEDED':
                why = 'Apify run %s ended %s: %s' % (run.get('id'), run.get('status'), run.get('statusMessage', ''))
                if re.search(r'credit|limit|usage|quota|memory', why, re.I):
                    raise KeyExhausted(why)
                raise RuntimeError(why)   # not a key problem: do not spend the other keys on it
            items = _apify('GET', '/datasets/%s/items?format=json&clean=true&limit=2000' % run['defaultDatasetId'],
                           tok, timeout=180)
            print('Apify %s: %d items' % (label, len(items)))
            return items
        except KeyExhausted as e:
            errors.append('%s: %s' % (label, str(e)[:160]))
            print('Apify %s failed (%s) - next key' % (label, str(e)[:160]))
    raise RuntimeError('every Apify key failed: ' + ' | '.join(errors))


def actor_input(kws, min_plays, per_kw):
    if 'clockworks' in ACTOR:   # clockworks~tiktok-scraper style input (no date filter: filtered here)
        return {'searchQueries': kws, 'resultsPerPage': per_kw, 'searchSection': '/video',
                'shouldDownloadVideos': False, 'shouldDownloadCovers': False}
    return {'searchQueries': kws, 'contentType': 'videos', 'maxItems': per_kw, 'sortBy': 'most_liked',
            'datePosted': 'last_24_hours', 'deepSearch': True, 'uniqueAuthors': False, 'minPlays': min_plays,
            'includeSuggestions': False}


def _num(*xs):
    for x in xs:
        try:
            if x is not None and x != '':
                return float(x)
        except (TypeError, ValueError):
            pass
    return 0.0


def normalise(v):
    """one video in a common shape, from either actor's field names; None if not a video"""
    if v.get('result_type') not in (None, 'video'):
        return None
    st = v.get('stats') or v.get('statistics') or {}
    vid = v.get('video_id') or v.get('id') or v.get('aweme_id')
    if not vid:
        return None
    created = _num(v.get('created_utc'), v.get('createTime'), v.get('create_time'))
    if not created and v.get('createTimeISO'):
        created = dt.datetime.fromisoformat(v['createTimeISO'].replace('Z', '+00:00')).timestamp()
    author = v.get('author_username') or (v.get('authorMeta') or {}).get('name') or \
        (v.get('author') if isinstance(v.get('author'), str) else (v.get('author') or {}).get('uniqueId')) or ''
    desc = v.get('description') or v.get('text') or v.get('desc') or ''
    tags = [h.get('name') if isinstance(h, dict) else h for h in (v.get('hashtags') or [])]
    tags = [t.lower().lstrip('#') for t in tags if t] or [t.lower() for t in re.findall(r'#(\w+)', desc)]
    return {
        'id': str(vid), 'url': v.get('video_url') or v.get('webVideoUrl') or v.get('url') or '',
        'keyword': v.get('keyword') or v.get('searchQuery') or '', 'author': author, 'desc': desc.strip(),
        'created': created, 'tags': tags,
        'plays': _num(v.get('play_count'), v.get('playCount'), st.get('playCount')),
        'likes': _num(v.get('like_count'), v.get('diggCount'), st.get('diggCount')),
        'comments': _num(v.get('comment_count'), v.get('commentCount'), st.get('commentCount')),
        'shares': _num(v.get('share_count'), v.get('shareCount'), st.get('shareCount')),
        'duration': _num(v.get('duration_sec'), (v.get('videoMeta') or {}).get('duration'), v.get('duration')),
    }


def viral_score(x, now=None):
    """velocity (views/hour since posting) + weighted engagement, 0-100 (same formula as the original lab)"""
    age = max(1.0, ((now or time.time()) - (x['created'] or 0)) / 3600)
    vel = x['plays'] / age
    eng = (x['likes'] + 2 * x['comments'] + 3 * x['shares']) / x['plays'] if x['plays'] else 0
    x.update(age_h=round(age, 1), velocity=round(vel), engagement=round(eng, 4),
             score=round(100 * (0.65 * min(1, vel / 100000) + 0.35 * min(1, eng / 0.20)), 1))
    return x


def words_of(text):
    return [w for w in re.findall(r"[^\W\d_][\w'’-]{2,}", text.lower()) if w not in STOP]


def patterns(vids):
    """measured patterns of the top videos (weighted by viral score)"""
    tags, words, bigr, bdocs = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
    for v in vids:
        w = max(1.0, v['score'])
        for t in set(v['tags']):
            if t not in STOP:
                tags[t] += w
        ws = words_of(re.sub(r'#\w+', ' ', v['desc']))
        for x in set(ws):
            words[x] += w
        for a, b in set(zip(ws, ws[1:])):
            bigr[a + ' ' + b] += w
            bdocs[a + ' ' + b] += 1
    durs = sorted(v['duration'] for v in vids if v['duration'])
    med = lambda xs: xs[len(xs) // 2] if xs else 0  # noqa: E731
    return {
        'hashtags': [t for t, _ in tags.most_common(15)],
        'words': [t for t, _ in words.most_common(20)],
        'phrases': [t for t, _ in bigr.most_common(40) if bdocs[t] >= 2][:12],   # in 2+ different videos
        'duration_median_s': med(durs),
        'duration_range_s': [durs[len(durs) // 5], durs[(4 * len(durs)) // 5]] if len(durs) >= 5 else durs[:1] + durs[-1:],
        'velocity_median': med(sorted(v['velocity'] for v in vids)),
        'engagement_median': med(sorted(v['engagement'] for v in vids)),
        'share_rate_median': med(sorted(v['shares'] / v['plays'] for v in vids if v['plays'])),
    }


def research(a):
    c = account(a.account)
    kws = keywords(c)
    min_plays = int(c.get('viral_min_plays') or DEFAULT_MIN_PLAYS)
    key = '%s_%s' % (c.get('format'), lang2(c))
    cache = os.path.join(OUT, 'research_%s_%s.json' % (key, today()))
    os.makedirs(OUT, exist_ok=True)
    data, source = None, ''
    if a.sample:
        items, source = json.load(open(a.sample, encoding='utf-8')), 'sample ' + a.sample
    elif os.path.exists(cache) and not a.fresh:
        data, source = json.load(open(cache, encoding='utf-8')), 'today\'s cache (same format + language)'
    else:
        try:
            items, source = run_actor(kws, min_plays), 'Apify %s, %d keywords' % (ACTOR, len(kws))
        except Exception as e:  # noqa: BLE001
            print('WARNING: research failed: %s' % e)
            data = drive_cached(key)
            if data:
                source = 'CACHED research from %s (Apify failed: %s)' % (data.get('date'), str(e)[:120])
            else:
                data = {'date': today(), 'status': 'unavailable', 'error': str(e)[:300], 'keywords': kws, 'videos': []}
                source = 'NONE (Apify failed, no cache) - write from metrics/insights only and say so in the report'
    if data is None:
        now = time.time()
        vids, seen = [], set()
        for raw in items:
            v = normalise(raw)
            if not v or v['id'] in seen or v['plays'] < min_plays:
                continue
            if v['created'] and now - v['created'] > 24 * 3600 * (1 if not a.sample else 10 ** 6):
                continue
            seen.add(v['id'])
            vids.append(viral_score(v, now))
        vids.sort(key=lambda v: v['score'], reverse=True)
        relaxed = False
        if len(vids) < 5 and not a.sample:   # thin niche today: keep the best of what was found (>= 20k views)
            relaxed = True
            for raw in items:
                v = normalise(raw)
                if v and v['id'] not in seen and v['plays'] >= 20000 and (not v['created'] or now - v['created'] <= 72 * 3600):
                    seen.add(v['id'])
                    vids.append(viral_score(v, now))
            vids.sort(key=lambda v: v['score'], reverse=True)
        data = {'date': today(), 'status': 'ok', 'format': c.get('format'), 'language': lang2(c), 'keywords': kws,
                'min_plays': min_plays, 'relaxed_to_72h_20k': relaxed, 'found': len(items), 'videos': vids[:40],
                'patterns': patterns(vids[:40])}
        json.dump(data, open(cache, 'w', encoding='utf-8'), ensure_ascii=False)
        if not a.sample:
            drive_put(key, cache)
    data['source'] = source
    json.dump(data, open(acc_file(a.account, 'research.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    md = report_md(a.account, c, data)
    open(acc_file(a.account, 'research.md'), 'w', encoding='utf-8').write(md)
    print(md)


def report_md(acc, c, d):
    L = ['# Viral research - %s (%s, %s) - %s' % (acc, c.get('format'), lang2(c), d.get('date')),
         'source: %s; keywords: %s' % (d.get('source'), ', '.join(d.get('keywords', [])))]
    vids = d.get('videos') or []
    if not vids:
        L.append('\n**No viral videos found** (%s). Use metrics + insights; note it in the report.' % d.get('error', 'empty search'))
        return '\n'.join(L) + '\n'
    p = d.get('patterns') or {}
    if d.get('relaxed_to_72h_20k'):
        L.append('(few videos passed 24 h / %d views - list relaxed to 72 h / 20k views)' % d.get('min_plays', 0))
    L += ['', '## Patterns (weighted by viral score)',
          '- hashtags: ' + ' '.join('#' + t for t in p.get('hashtags', [])),
          '- recurring words: ' + ', '.join(p.get('words', [])),
          '- recurring phrases: ' + (', '.join(p.get('phrases', [])) or '-'),
          '- length: median %ss, middle 60%% %s s' % (p.get('duration_median_s'), p.get('duration_range_s')),
          '- velocity median %s views/h, engagement median %.1f%%, shares median %.2f%% of views' % (
              p.get('velocity_median'), 100 * p.get('engagement_median', 0), 100 * p.get('share_rate_median', 0)),
          '', '## Top videos (score = velocity + engagement; themes and techniques only, never copy)',
          '| score | views | views/h | eng | s | caption (opening) | link |', '|---|---|---|---|---|---|---|']
    for v in vids[:15]:
        L.append('| %.0f | %s | %s | %.1f%% | %d | %s | %s |' % (
            v['score'], human(v['plays']), human(v['velocity']), 100 * v['engagement'], v['duration'],
            v['desc'].replace('|', '/').replace('\n', ' ')[:110], v['url']))
    L += ['', 'Next: write the patterns note (what themes/hooks/angles win today and WHY) in insights, then 3 '
              'original scripts that use them.']
    return '\n'.join(L) + '\n'


def human(n):
    n = float(n)
    return '%.1fM' % (n / 1e6) if n >= 1e6 else ('%.0fk' % (n / 1e3) if n >= 1e3 else '%d' % n)


def drive_put(key, path):
    try:
        import gdrive
        if gdrive.configured():
            gdrive.put_state(path, 'viral_research_%s.json' % key)
    except Exception as e:  # noqa: BLE001
        print('WARNING: could not save the research to Drive: %s' % e)


def drive_cached(key):
    try:
        import gdrive
        if not gdrive.configured():
            return None
        p = os.path.join(OUT, 'drive_%s.json' % key)
        if gdrive.get_state('viral_research_%s.json' % key, p):
            d = json.load(open(p, encoding='utf-8'))
            if d.get('date', '') >= (dt.date.fromisoformat(today()) - dt.timedelta(days=3)).isoformat():
                return d
    except Exception as e:  # noqa: BLE001
        print('WARNING: no cached research from Drive: %s' % e)
    return None


# ---------------------------------------------------------------- evaluate
def story_hash(text):
    return hashlib.sha256(text.strip().encode('utf-8')).hexdigest()[:16]


def past_hooks(acc):
    p = os.environ.get('STORY_LOG', '/tmp/stories.jsonl')
    out = []
    if os.path.exists(p):
        for l in open(p, encoding='utf-8'):
            try:
                e = json.loads(l)
            except ValueError:
                continue
            out.append((e.get('account') or e.get('channels'), e.get('hook') or '', e.get('title') or ''))
    return out


def jaccard(a, b):
    a, b = set(words_of(a)), set(words_of(b))
    return len(a & b) / len(a | b) if a and b else 0.0


def checks(acc, c, text, research_data):
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    nw = len(text.split())
    lo, hi = c.get('words', [150, 195])
    first, last = lines[0] if lines else '', lines[-1] if lines else ''
    per_line = [len(l.split()) for l in lines] or [0]
    res = []   # (name, points 0..1, weight, hard_fail, note)
    if lo * 0.9 <= nw <= hi * 1.1:
        res.append(('length', 1.0 if lo <= nw <= hi else 0.6, 15, False, '%d words (target %d-%d)' % (nw, lo, hi)))
    else:
        res.append(('length', 0.0, 15, True, '%d words, outside %d-%d (+-10%%): will not fit the video length' % (nw, lo, hi)))
    fw = len(first.split())
    res.append(('hook_short', 1.0 if fw <= 14 else (0.5 if fw <= 20 else 0.0), 15, False,
                'first line %d words (<= 14 reads in ~2 s)' % fw))
    tension = bool(re.search(r'\d|\?|!|[“"«]|\b(never|don\'t|nie|niemals|nicht|jamais|ne |n\'|you|du|tu|vous|dein|ton|ta)\b',
                             first.lower()))
    res.append(('hook_tension', 1.0 if tension else 0.4, 10, False,
                'opening has a number/negation/direct address/question' if tension else 'opening has no number, rule, "you" or question - weak scroll stop'))
    q = last.rstrip('”"» ').endswith('?')
    res.append(('final_question', 1.0 if q else 0.0, 15, not q, 'last line is a one-word comment question' if q else 'last line must be a comment question (STORY_BRIEF)'))
    loop = bool(set(words_of(first)) & set(words_of(' '.join(lines[-2:]))))
    res.append(('loop', 1.0 if loop else 0.3, 10, False, 'ending echoes the hook' if loop else 'ending does not echo a word/object of the first line'))
    avg = sum(per_line) / len(per_line)
    res.append(('line_rhythm', 1.0 if avg <= 13 and max(per_line) <= 24 else 0.5, 10, False,
                'avg %.1f words/line, longest %d' % (avg, max(per_line))))
    terms = set()
    p = (research_data or {}).get('patterns') or {}
    for t in p.get('words', [])[:20] + p.get('hashtags', [])[:15]:
        terms.add(t.lower())
    sw = set(words_of(text))
    hits = sorted(t for t in terms if t in sw or any(t in w for w in sw if len(t) >= 5))
    res.append(('trend_terms', min(1.0, len(hits) / 3) if terms else 0.5, 10, False,
                ('uses trend words: ' + ', '.join(hits[:6])) if hits else ('no trend word from today\'s research' if terms else 'no research')))
    base = acc.split('-')[0] if re.search(r'-\d+$', acc) else acc
    sims = [(jaccard(first, h), h) for a_, h, _ in past_hooks(acc) if h]
    mine = [(jaccard(first, h), h) for a_, h, _ in past_hooks(acc) if h and a_ in (acc, base)]
    top = max(sims or [(0, '')])
    hard = top[0] >= 0.6
    res.append(('novelty', 0.0 if hard else (0.6 if max(mine or [(0, '')])[0] >= 0.35 else 1.0), 15, hard,
                ('hook nearly repeats an earlier one: "%s"' % top[1][:80]) if hard else 'hook is new vs the story log'))
    score = 100 * sum(pt * w for _, pt, w, _, _ in res) / sum(w for _, _, w, _, _ in res)
    return round(score, 1), res


def judge_score(j):
    s = j.get('scores', j)
    missing = [k for k in RUBRIC if k not in s]
    if missing:
        sys.exit('judge is missing criteria: %s (see `viral_lab.py judge-template`)' % ', '.join(missing))
    return round(sum(RUBRIC[k][0] * max(0.0, min(10.0, float(s[k]))) / 10 for k in RUBRIC), 1)


def gemini_judge(c, text, research_md):
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        return None
    prompt = ('You are a strict, sceptical TikTok short-form script editor. Score this ORIGINAL %s script (format %s) '
              'for a 2D-animated short, 0-10 per criterion (10 = top 1%% of the niche; most scripts are 4-7). '
              'Criteria: %s. Today\'s niche research:\n%s\n\nReturn JSON {"scores":{criterion:number},'
              '"improve":[string]} only.\n\nSCRIPT:\n%s') % (
        lang2(c), c.get('format'), '; '.join('%s = %s' % (k, v[1]) for k, v in RUBRIC.items()), research_md[:4000], text)
    body = json.dumps({'contents': [{'parts': [{'text': prompt}]}],
                       'generationConfig': {'responseMimeType': 'application/json', 'temperature': 0.2}}).encode()
    models = [m for m in [os.environ.get('GEMINI_MODEL'), 'gemini-flash-latest', 'gemini-3-flash-preview',
                          'gemini-flash-lite-latest'] if m]
    try:
        d, err = None, None
        for model in models:   # 429/503 = overloaded model: retry once, then the next model
            for wait in (5, 0):
                req = urllib.request.Request(
                    'https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent' % urllib.parse.quote(model),
                    data=body, headers={'content-type': 'application/json', 'x-goog-api-key': key}, method='POST')
                try:
                    with urllib.request.urlopen(req, timeout=120) as r:
                        d = json.loads(r.read().decode('utf-8'))
                    break
                except urllib.error.HTTPError as e:
                    err = '%s %s' % (model, e.code)
                    if e.code not in (429, 500, 503) or not wait:
                        break
                    time.sleep(wait)
            if d:
                break
        if not d:
            raise RuntimeError(err)
        raw = ''.join(p.get('text', '') for p in d['candidates'][0]['content']['parts'])
        return json.loads(raw)
    except Exception as e:  # noqa: BLE001
        print('WARNING: Gemini judge failed (%s) - using the session judge only' % str(e)[:200])
        return None


def evaluate(a):
    c = account(a.account)
    rpath = acc_file(a.account, 'research.json')
    rdata = json.load(open(rpath, encoding='utf-8')) if os.path.exists(rpath) else None
    rmd = open(acc_file(a.account, 'research.md'), encoding='utf-8').read() if rdata else ''
    if rdata is None:
        print('WARNING: no research for %s yet - run `viral_lab.py research --account %s` first' % (a.account, a.account))
    judges = json.load(open(a.judge, encoding='utf-8')) if a.judge else None
    if isinstance(judges, dict):
        judges = [judges]
    if judges is not None and len(judges) != len(a.stories):
        sys.exit('--judge must hold one rubric object per story (a JSON list in the same order)')
    rows = []
    for i, sp in enumerate(a.stories):
        text = open(sp, encoding='utf-8').read().strip()
        chk, res = checks(a.account, c, text, rdata)
        js = []
        if judges:
            js.append(('session', judge_score(judges[i]), judges[i].get('improve', [])))
        g = None if a.no_gemini else gemini_judge(c, text, rmd)
        if g:
            try:
                js.append(('gemini', judge_score(g), g.get('improve', [])))
            except SystemExit:
                print('WARNING: Gemini judge returned an incomplete rubric - ignored')
        if not js:
            sys.exit('no judge: pass --judge <json> (session rubric) and/or set GEMINI_API_KEY')
        jscore = sum(s for _, s, _ in js) / len(js)
        final = round(0.75 * jscore + 0.25 * chk, 1)
        hard = [n for n, _, _, h, note in res if h]
        rec = {'date': today(), 'account': a.account, 'format': c.get('format'), 'file': sp, 'hash': story_hash(text),
               'hook': text.split('\n')[0][:200], 'final': final, 'judge': {n: s for n, s, _ in js}, 'checks': chk,
               'hard_fail': hard, 'threshold': threshold(c),
               'criteria': (judges[i].get('scores', judges[i]) if judges else (g or {}).get('scores')),
               'improve': [x for _, _, imp in js for x in imp][:6],
               'notes': {n: note for n, pt, w, h, note in res if pt < 1}}
        rows.append(rec)
        with open(acc_file(a.account, 'evals.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
        if len(js) == 2 and abs(js[0][1] - js[1][1]) > 15:
            print('NOTE: judges disagree on %s (%s) - be stricter, re-read the rubric' % (
                sp, ', '.join('%s %.0f' % (n, s) for n, s, _ in js)))
    rows.sort(key=lambda r: (not r['hard_fail'], r['final']), reverse=True)
    print('# Evaluation - %s (threshold %d)\n' % (a.account, threshold(c)))
    for r in rows:
        ok = 'PASS' if r['final'] >= r['threshold'] and not r['hard_fail'] else 'FAIL'
        print('%s %5.1f  %s  (judge %s, checks %.0f)%s' % (
            ok, r['final'], r['file'], ', '.join('%s %.0f' % kv for kv in r['judge'].items()), r['checks'],
            ('  HARD FAIL: ' + ', '.join(r['hard_fail'])) if r['hard_fail'] else ''))
        if r['criteria']:
            low = sorted(r['criteria'].items(), key=lambda kv: float(kv[1]))[:3]
            print('      lowest: ' + ', '.join('%s %s' % kv for kv in low))
        for n, note in r['notes'].items():
            print('      - %s: %s' % (n, note))
        for x in r['improve'][:4]:
            print('      > ' + x)
    best = rows[0]
    print('\nbest: %s (%.1f)%s' % (best['file'], best['final'],
                                   '' if best['final'] >= best['threshold'] and not best['hard_fail']
                                   else ' - below the bar: improve the lowest criteria and evaluate again'))


def threshold(c):
    return int(os.environ.get('VIRAL_THRESHOLD') or c.get('viral_threshold') or DEFAULT_THRESHOLD)


def approve(a):
    c = account(a.account)
    text = open(a.story, encoding='utf-8').read().strip()
    h = story_hash(text)
    evals = []
    p = acc_file(a.account, 'evals.jsonl')
    if os.path.exists(p):
        evals = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
    mine = [e for e in evals if e['hash'] == h]
    if not mine:
        sys.exit('NOT APPROVED: this exact text was never evaluated - run `viral_lab.py evaluate` on it first '
                 '(any edit after the evaluation needs a new evaluation)')
    e = mine[-1]
    rpath = acc_file(a.account, 'research.json')
    if not os.path.exists(rpath):
        sys.exit('NOT APPROVED: research first (`viral_lab.py research --account %s`)' % a.account)
    if e['hard_fail']:
        sys.exit('NOT APPROVED: hard fail %s' % ', '.join(e['hard_fail']))
    if e['final'] < threshold(c):
        sys.exit('NOT APPROVED: %.1f < %d - improve and evaluate again' % (e['final'], threshold(c)))
    rs = json.load(open(rpath, encoding='utf-8'))
    out = {'account': a.account, 'hash': h, 'score': e['final'], 'judge': e['judge'], 'checks': e['checks'],
           'threshold': threshold(c), 'date': today(), 'story': os.path.abspath(a.story),
           'research': rs.get('source', ''), 'rounds': len({x['hash'] for x in evals})}
    json.dump(out, open(acc_file(a.account, 'approved.json'), 'w', encoding='utf-8'), indent=1)
    print('APPROVED %s: %.1f >= %d (%d versions evaluated)' % (a.account, e['final'], threshold(c), out['rounds']))


def require_approval(acc, story_path):
    """called by bootstrap.py / studio.py before any video work; exits if the story is not approved"""
    if os.environ.get('VIRAL_GATE', 'on').lower() in ('off', '0', 'no'):
        print('viral gate OFF (VIRAL_GATE=off)')
        return None
    p = acc_file(acc, 'approved.json')
    text = open(story_path, encoding='utf-8').read().strip()
    if not os.path.exists(p):
        sys.exit('VIRAL GATE: no approved script for %s - research, evaluate and approve it first '
                 '(daily/viral_lab.py; VIRAL_GATE=off to bypass for a manual test)' % acc)
    ap_ = json.load(open(p, encoding='utf-8'))
    if ap_.get('hash') != story_hash(text):
        sys.exit('VIRAL GATE: %s differs from the approved script for %s - evaluate + approve the final text' % (story_path, acc))
    if ap_.get('date') != today():
        sys.exit('VIRAL GATE: the approval for %s is from %s, not today' % (acc, ap_.get('date')))
    print('viral gate: approved script for %s, score %.1f (threshold %d)' % (acc, ap_['score'], ap_['threshold']))
    return ap_


def approval(acc):
    """the approval record (for publish.py's log entry), or None"""
    p = acc_file(acc, 'approved.json') if acc else ''
    return json.load(open(p, encoding='utf-8')) if acc and os.path.exists(p) else None


def status(_a):
    os.makedirs(OUT, exist_ok=True)
    for f in sorted(os.listdir(OUT)):
        if f.endswith('.approved.json'):
            d = json.load(open(os.path.join(OUT, f), encoding='utf-8'))
            print('approved  %-18s %.1f (>= %d) %s' % (d['account'], d['score'], d['threshold'], d['story']))
        elif f.endswith('.evals.jsonl'):
            ev = [json.loads(l) for l in open(os.path.join(OUT, f), encoding='utf-8') if l.strip()]
            b = max(ev, key=lambda e: e['final'])
            print('evaluated %-18s %d versions, best %.1f %s' % (b['account'], len(ev), b['final'], b['file']))
        elif f.endswith('.research.json'):
            d = json.load(open(os.path.join(OUT, f), encoding='utf-8'))
            print('research  %-18s %d videos - %s' % (f[:-14], len(d.get('videos', [])), d.get('source', '')))


def sync(_a):
    """append today's evaluations (+ approvals) to Drive _state/viral_lab.jsonl (history for calibration)"""
    import gdrive
    p = os.path.join(OUT, 'viral_lab.jsonl')
    if not gdrive.get_state('viral_lab.jsonl', p):
        open(p, 'w').close()
    have = {(e.get('account'), e.get('hash'), e.get('kind')) for e in
            (json.loads(l) for l in open(p, encoding='utf-8') if l.strip())}
    new = []
    for f in sorted(os.listdir(OUT)):
        fp = os.path.join(OUT, f)
        if f.endswith('.evals.jsonl'):
            for l in open(fp, encoding='utf-8'):
                if l.strip():
                    e = dict(json.loads(l), kind='eval')
                    if (e['account'], e['hash'], 'eval') not in have:
                        new.append(e)
                        have.add((e['account'], e['hash'], 'eval'))
        elif f.endswith('.approved.json'):
            e = dict(json.load(open(fp, encoding='utf-8')), kind='approved')
            if (e['account'], e['hash'], 'approved') not in have:
                new.append(e)
    with open(p, 'a', encoding='utf-8') as f:
        for e in new:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')
    gdrive.put_state(p, 'viral_lab.jsonl')
    print('viral_lab.jsonl: +%d records' % len(new))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest='cmd', required=True)
    r = sp.add_parser('research')
    r.add_argument('--account', required=True)
    r.add_argument('--sample', help='saved Apify dataset items (JSON list) instead of a live search')
    r.add_argument('--fresh', action='store_true', help='ignore today\'s cache for this format + language')
    e = sp.add_parser('evaluate')
    e.add_argument('--account', required=True)
    e.add_argument('stories', nargs='+')
    e.add_argument('--judge', help='session rubric JSON: one object, or a list (one per story, same order)')
    e.add_argument('--no-gemini', action='store_true')
    p = sp.add_parser('approve')
    p.add_argument('--account', required=True)
    p.add_argument('story')
    sp.add_parser('status')
    sp.add_parser('sync')
    sp.add_parser('judge-template')
    a = ap.parse_args()
    if a.cmd == 'judge-template':
        print(json.dumps(JUDGE_TEMPLATE, indent=1))
        print('\n'.join('# %-13s weight %2d  10 = %s' % (k, w, d) for k, (w, d) in RUBRIC.items()))
        return
    {'research': research, 'evaluate': evaluate, 'approve': approve, 'status': status, 'sync': sync}[a.cmd](a)


if __name__ == '__main__':
    main()
