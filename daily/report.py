#!/usr/bin/env python3
"""Daily report of yesterday's posts (no analysis): two short tables, saved to Drive _reports/<date>.md.

    python3 report.py [--date YYYY-MM-DD] [--tz Europe/London]

1. Ranking, worst -> best: profile, views, retention to the end (average time watched / video length).
2. Per post: platform, video, @profile, likes, comments, saves, shares.
"""
import argparse
import datetime as dt
import json
import os
import sys
import tempfile
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import buffer_api  # noqa: E402
import gdrive  # noqa: E402

PLATFORM = {'tiktok': 'TikTok', 'instagram': 'Instagram', 'youtube': 'YouTube'}


def posts_of_day(day, tz):
    out = []
    for env in buffer_api.api_keys():
        buffer_api.use_key(env)
        for o in buffer_api.organizations():
            q = ('query { posts(first: 100, input: {organizationId: "%s", filter: {status: [sent]}, '
                 'sort: [{field: dueAt, direction: desc}]}) { edges { node { id channelService channel { name } '
                 'text sentAt metrics { type value } } } } }' % o['id'])
            for e in buffer_api.gql(q)['posts']['edges']:
                p = e['node']
                if not p.get('sentAt') or p.get('channelService') not in PLATFORM:
                    continue
                local = dt.datetime.fromisoformat(p['sentAt'].replace('Z', '+00:00')).astimezone(ZoneInfo(tz)).date()
                if local.isoformat() == day:
                    out.append(p)
    buffer_api.use_key('BUFFER_API_KEY')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tz', default='Europe/London')
    ap.add_argument('--date')
    a = ap.parse_args()
    day = a.date or (dt.datetime.now(ZoneInfo(a.tz)).date() - dt.timedelta(days=1)).isoformat()

    log = {}
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, 's.jsonl')
        if gdrive.configured() and gdrive.get_state('stories.jsonl', p):
            for l in open(p, encoding='utf-8'):
                if l.strip():
                    e = json.loads(l)
                    for pid in list((e.get('buffer_posts') or {}).values()) + [e.get('buffer_post_id')]:
                        if pid:
                            log[pid] = e

    rows = []
    for p in posts_of_day(day, a.tz):
        m = {x['type']: x['value'] for x in (p.get('metrics') or [])}
        e = log.get(p['id'], {})
        dur = e.get('duration')
        avg = m.get('averageTimeWatched')
        rows.append(dict(
            platform=PLATFORM[p['channelService']], profile=p['channel']['name'],
            video=e.get('title') or (p.get('text') or '').split('#')[0].strip()[:50] or '(sem título)',
            views=int(m.get('views', 0)),
            retention=('%.0f%%' % (100 * avg / dur)) if (avg is not None and dur) else '–',
            likes=int(m.get('likes', m.get('reactions', 0))), comments=int(m.get('comments', 0)),
            saves=('%d' % m['saves']) if 'saves' in m else '–', shares=int(m.get('shares', 0))))

    lines = ['# Relatório diário — vídeos de %s' % day, '']
    if not rows:
        lines.append('Nenhum vídeo publicado nesse dia.')
    else:
        lines += ['## Ranking (pior → melhor)', '', '| perfil | visualizações | retenção até o final |', '|---|---|---|']
        for r in sorted(rows, key=lambda r: r['views']):
            lines.append('| @%s | %d | %s |' % (r['profile'], r['views'], r['retention']))
        lines += ['', '## Interações', '',
                  '| plataforma | vídeo | @ | curtidas | comentários | salvamentos | compartilhamentos |',
                  '|---|---|---|---|---|---|---|']
        for r in sorted(rows, key=lambda r: r['views']):
            lines.append('| %s | %s | @%s | %d | %d | %s | %d |' % (r['platform'], r['video'], r['profile'], r['likes'],
                                                                 r['comments'], r['saves'], r['shares']))
        lines += ['', 'retenção = tempo médio assistido ÷ duração do vídeo. "–" = dado não enviado pela plataforma.']
    text = '\n'.join(lines) + '\n'
    print(text)
    if gdrive.configured():
        d = gdrive.Drive()
        fid = d.folder('_reports', d.folder(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily')))
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, day + '.md')
            open(p, 'w', encoding='utf-8').write(text)
            d.upload(p, day + '.md', fid, 'text/markdown')


if __name__ == '__main__':
    main()
