#!/usr/bin/env python3
"""Performance report of the TikTok posts (Buffer metrics) to learn what works per account.

    python3 metrics.py [stories.jsonl] [--days 60]     # markdown report on stdout

For each account: every sent post with views, average watch time, watch-through (avg watch / video length,
when the length is known from stories.jsonl), engagement rate, likes/comments/shares, plus the story title,
format and hook for our own videos. Then medians, best and worst, so the next stories copy what worked.
"""
import argparse
import datetime as dt
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import buffer_api  # noqa: E402


def sent_posts(days):
    out = []
    for env in buffer_api.api_keys():
        buffer_api.use_key(env)
        for o in buffer_api.organizations():
            out += _sent(o['id'], days)
    buffer_api.use_key('BUFFER_API_KEY')
    return out


def _sent(org, days):
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime('%Y-%m-%d')
    out, after = [], None
    for _ in range(10):
        q = ('query { posts(first: 50%s, input: {organizationId: "%s", filter: {status: [sent]}, '
             'sort: [{field: dueAt, direction: desc}]}) { pageInfo { hasNextPage endCursor } '
             'edges { node { id channelService channel { name } text sentAt externalLink metrics { type value } } } } }'
             % ((', after: "%s"' % after) if after else '', org))
        r = buffer_api.gql(q)['posts']
        nodes = [e['node'] for e in r['edges']]
        out += nodes
        if not r['pageInfo'].get('hasNextPage') or (nodes and (nodes[-1].get('sentAt') or '') < since):
            break
        after = r['pageInfo']['endCursor']
    return [p for p in out if p.get('channelService') in buffer_api.SERVICES and (p.get('sentAt') or '') >= since]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('log', nargs='?')
    ap.add_argument('--days', type=int, default=60)
    a = ap.parse_args()
    log = {}
    if a.log and os.path.exists(a.log):
        for l in open(a.log, encoding='utf-8'):
            if l.strip():
                e = json.loads(l)
                for pid in list((e.get('buffer_posts') or {}).values()) + [e.get('buffer_post_id')]:
                    if pid:
                        log[pid] = e
    by_acc = {}
    for p in sent_posts(a.days):
        m = {x['type']: x['value'] for x in (p.get('metrics') or [])}
        e = log.get(p['id'], {})
        dur = e.get('duration')
        row = dict(date=(p.get('sentAt') or '')[:10], views=int(m.get('views', 0)), avg=m.get('averageTimeWatched', 0),
                   eng=m.get('engagementRate', 0), likes=int(m.get('reactions', m.get('likes', 0))),
                   comments=int(m.get('comments', 0)), shares=int(m.get('shares', 0)),
                   through=(100 * m.get('averageTimeWatched', 0) / dur) if dur else None,
                   title=e.get('title') or '', fmt=e.get('format') or '', hook=e.get('hook') or '',
                   text=(p.get('text') or '').replace('\n', ' ')[:80], ours=bool(e))
        by_acc.setdefault(p['channel']['name'], []).append(row)

    print('# TikTok performance (last %d days, Buffer metrics)\n' % a.days)
    cutoff = (dt.date.today() - dt.timedelta(days=2)).isoformat()
    for acc, rows in sorted(by_acc.items()):
        rows.sort(key=lambda r: r['date'], reverse=True)
        mature = [r for r in rows if r['date'] <= cutoff] or rows
        print('## %s — %d posts, median views %d, median avg watch %.1f s\n' % (
            acc, len(rows), statistics.median(r['views'] for r in mature), statistics.median(r['avg'] for r in mature)))
        print('| date | views | avg watch | through | eng % | likes | com | shares | story / caption |')
        print('|---|---|---|---|---|---|---|---|---|')
        for r in rows:
            th = '%.0f%%' % r['through'] if r['through'] is not None else '–'
            what = ('**%s** (%s) — %s' % (r['title'], r['fmt'], r['hook'][:60])) if r['ours'] else r['text']
            print('| %s | %d | %.1f s | %s | %.1f | %d | %d | %d | %s |' % (
                r['date'], r['views'], r['avg'], th, r['eng'], r['likes'], r['comments'], r['shares'], what))
        label = lambda r: '%s (%d views, %.0f s)' % (r['title'] or r['text'][:40], r['views'], r['avg'])  # noqa: E731
        print('\nbest: ' + '; '.join(label(r) for r in sorted(mature, key=lambda r: (r['views'], r['avg']), reverse=True)[:3]))
        print('worst: ' + '; '.join(label(r) for r in sorted(mature, key=lambda r: (r['views'], r['avg']))[:3]))
        print('(posts younger than 2 days are still growing; judge them later)\n')


if __name__ == '__main__':
    main()
