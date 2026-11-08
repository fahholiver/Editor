#!/usr/bin/env python3
"""Today's plan: one new video per TikTok account in Buffer, each with its own language, format, voice and
posting time (daily/accounts.json).

    python3 plan.py [stories.jsonl]     # one block per account + the titles/hooks it already used
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def account_cfg(acc):
    cfg = json.load(open(os.path.join(HERE, 'accounts.json')))
    c = dict(cfg.get('_default', {}))
    c.update(cfg.get(acc, {}))
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
    cfg = json.load(open(os.path.join(HERE, 'accounts.json')))
    chans = buffer_api.all_channels()
    # only accounts listed in accounts.json get their own new story; other channels (e.g. reposting accounts
    # on a second Buffer key) only receive copies through also_post_to
    accounts = [c['name'] for c in chans if c['name'] in cfg and not c['name'].startswith('_')]
    only = os.environ.get('BUFFER_TIKTOK_CHANNELS')
    if only and only != 'all':
        accounts = [a for a in accounts if a in [x.strip() for x in only.split(',')]]
    p = plan(accounts)
    log = []
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        log = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8') if l.strip()]
    for c in p:
        print('%-16s %s  %s  post %s %s  %d-%d words' % (c['account'], c['language'], c['format'], c['post_time'],
                                                        c['tz'], c['words'][0], c['words'][1]))
        print('    brief=%s locale=%s' % (c['brief'], c['locale']))
        for e in [e for e in log if e.get('channels') == c['account'] or e.get('account') == c['account']][-15:]:
            print('    already used (%s): %s - %s' % (e.get('date'), e.get('title'), e.get('hook')))
    print('all past titles:', '; '.join(e.get('title', '') for e in log[-40:]))
    print(json.dumps(p))
