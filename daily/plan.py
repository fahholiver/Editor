#!/usr/bin/env python3
"""Today's plan: one new video per TikTok account in Buffer, each in that account's format.

    python3 plan.py [stories.jsonl]      # prints one line per account: account, format, brief file

Formats come from daily/accounts.json; an account that is not listed gets the first format of
_default_order not already used today. With a stories.jsonl (the log on the media branch) it also prints
the last titles/hooks per format, so today's stories don't repeat them.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def plan(accounts):
    cfg = json.load(open(os.path.join(HERE, 'accounts.json')))
    order = cfg.get('_default_order', [])
    used, out = set(), []
    for acc in accounts:  # explicit mappings first
        if acc in cfg:
            used.add(cfg[acc])
    for acc in accounts:
        fmt = cfg.get(acc)
        if not fmt:
            fmt = next((f for f in order if f not in used), order[0] if order else 'rule_horror')
            used.add(fmt)
        brief = os.path.join(HERE, 'formats', fmt + '.md')
        if not os.path.exists(brief):
            sys.exit('format %s for %s has no file %s' % (fmt, acc, brief))
        out.append({'account': acc, 'format': fmt, 'brief': brief})
    return out


if __name__ == '__main__':
    import buffer_api
    accounts = [name for _, name in buffer_api.find_tiktok_channels(os.environ.get('BUFFER_TIKTOK_CHANNELS', 'all'))]
    p = plan(accounts)
    log = []
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        log = [json.loads(l) for l in open(sys.argv[1], encoding='utf-8') if l.strip()]
    for item in p:
        print('%-20s format=%-13s brief=%s' % (item['account'], item['format'], item['brief']))
        past = [e for e in log if e.get('format') == item['format']][-10:]
        for e in past:
            print('      already used (%s): %s - %s' % (e.get('date'), e.get('title'), e.get('hook')))
    print(json.dumps(p))
