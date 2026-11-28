#!/usr/bin/env python3
"""Today's plan: one new video per TikTok account in Buffer, each with its own language, format, voice and
posting time: the owner's Google Sheet (daily/sheet.py) decides who/when/format/reposts, accounts.json holds
the technical details (voices, length). Without a sheet (or a cached copy) accounts.json alone is used.

    python3 plan.py [stories.jsonl]     # one block per account + the titles/hooks it already used
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def _today():
    import datetime as dt
    from zoneinfo import ZoneInfo
    return os.environ.get('PLAN_DATE') or dt.datetime.now(ZoneInfo('Europe/London')).date().isoformat()


_CFG = {}


# formats that only work with one engine/look: forced whatever the account or the sheet had before
# (2026-11-22: kaelusuxkzx kept vintage 1:1 with mindset_explainer and the video lost the whole look)
FORMAT_LOOK = {
    'mindset_explainer': {'engine': 'motion', 'visual_style': 'spotlight_line', 'aspect': '9:16', 'music_bed': False},
    # the owner's documentary skills (2026-11-28, daily/docstudio.py): format = skill, engine forced
    'finance_doc': {'engine': 'finance', 'aspect': '9:16', 'music_bed': False, 'visual_style': None},
    'space_killer': {'engine': 'orbit', 'aspect': '9:16', 'music_bed': False, 'visual_style': None},
    'engineering_failure': {'engine': 'engfail', 'aspect': '9:16', 'music_bed': False, 'visual_style': None},
}


# documentary skills: one narrator per language (ElevenLabs library, chosen 2026-11-28; Edge stays the fallback)
DOC_VOICE = {'de-DE': 'nPczCjzI2devNBz1zQrb',   # Brian - deep, resonant (premade: library voices need a paid plan)
             'fr-FR': 'JBFqnCBsd6RMkjVDRZzb',   # George - warm, captivating storyteller (premade, multilingual v2)
             'en-GB': 'onwK4e9ZLuTAKqWW03F9'}   # Daniel - steady British broadcaster (premade)
DOC_SECONDS = [60, 90]
DOC_WORDS = {'de-DE': [125, 175], 'fr-FR': [140, 195], 'en-GB': [150, 210]}   # documentary pace ~150 wpm


def format_look(c):
    c.update(FORMAT_LOOK.get(c.get('format'), {}))
    if c.get('engine') in ('finance', 'orbit', 'engfail'):
        c['elevenlabs_voice'] = DOC_VOICE.get(c.get('language'), c.get('elevenlabs_voice'))
        c['seconds'] = DOC_SECONDS
        c['words'] = DOC_WORDS.get(c.get('language'), c.get('words'))
    if c.get('visual_style') is None:
        c.pop('visual_style', None)
    return c


def config():
    """accounts.json merged with the sheet (only the sheet's gerar=s accounts), or accounts.json alone"""
    if 'cfg' not in _CFG:
        cfg = json.load(open(os.path.join(HERE, 'accounts.json')))
        try:
            import sheet
            m = sheet.merged(cfg, _today())
        except Exception as e:  # noqa: BLE001
            print('WARNING: accounts sheet failed (%s); using accounts.json' % e, file=sys.stderr)
            m = None
        _CFG['cfg'] = m if m is not None else cfg
    return _CFG['cfg']


def is_active(acc):
    return config().get(acc, {}).get('active_from', '0000') <= _today()


def account_cfg(acc):
    cfg = config()
    c = dict(cfg.get('_default', {}))
    c.update(cfg.get(acc, {}))
    today = _today()
    for day, over in sorted((c.pop('changes_from', None) or {}).items()):   # dated changes
        if day <= today:
            c.update(over)
    format_look(c)
    c['account'] = acc
    c['brief'] = os.path.join(HERE, 'formats', c['format'] + '.md')
    c['locale'] = os.path.join(HERE, 'locales', c['language'] + '.md')
    for k in ('brief', 'locale'):
        if not os.path.exists(c[k]):
            sys.exit('%s for %s: missing %s' % (k, acc, c[k]))
    return c


def plan(accounts):
    return [account_cfg(a) for a in accounts]


if __name__ == '__main__':
    import buffer_api
    cfg = config()
    chans = buffer_api.all_channels()
    # only the sheet's gerar=s accounts get their own new story; repost accounts only receive copies
    # (also_post_to), gerar=n accounts get the ready-made Drive queue videos (queue_post.py)
    names = {c['name'].lower() for c in chans}
    accounts = []
    for a, c in cfg.items():   # key = account, or <account>-2 for its 2nd post of the day (a different story)
        if a.startswith('_') or not is_active(a):
            continue
        if c.get('channel', a).lower() not in names:
            print('WARNING: %s is in the sheet but not connected in Buffer - skipped' % c.get('channel', a))
            continue
        accounts.append(a)
    only = os.environ.get('BUFFER_TIKTOK_CHANNELS')
    if only and only != 'all':
        accounts = [a for a in accounts if cfg[a].get('channel', a) in [x.strip() for x in only.split(',')]]
    p = plan(accounts)
    log = []
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        log = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8') if l.strip()]
    for c in p:
        print('%-18s %s  %s  engine %s%s  post %s %s  %d-%d words' % (
            c['account'], c['language'], c['format'], c.get('engine', 'motion'),
            (' style ' + c['visual_style']) if c.get('visual_style') else '', c['post_time'], c['tz'],
            c['words'][0], c['words'][1]))
        print('    brief=%s locale=%s' % (c['brief'], c['locale']))
        if c.get('also_post_to'):
            print('    reposts: ' + ', '.join('%s %s' % (m.get('name', m['channel']), m.get('post_time', c['post_time'])) for m in c['also_post_to']))
        for e in [e for e in log if e.get('channels') == c['account'] or e.get('account') == c['account']][-15:]:
            print('    already used (%s): %s - %s' % (e.get('date'), e.get('title'), e.get('hook')))
    print('all past titles:', '; '.join(e.get('title', '') for e in log[-40:]))
    print(json.dumps(p))
