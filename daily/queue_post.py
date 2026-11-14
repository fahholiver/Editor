#!/usr/bin/env python3
"""Post ready-made videos from ONE Google Drive folder: a DIFFERENT video to each account, every day.

    python3 daily/queue_post.py --folder <id> --caption "#emotional #respectpeople"
        # accounts = the owner's sheet rows with Gerar = n (daily/sheet.py): each at its own London time, and
        # the row's repost accounts get the same file at the same time
    python3 daily/queue_post.py --folder <id> --channel a,b,c --at 14:00   # without the sheet
    python3 daily/queue_post.py --folder <id> --list          # show the queue, post nothing

1. lists the videos in the folder (not trashed), by file name (01_, 02_ ... sets the order)
2. drops every file already in the Drive log `queue_posted.jsonl` that was sent or is still waiting at Buffer
   (sent -> trashed now), so a video is never offered twice, to the same or another channel
3. gives account 1 the first video, account 2 the second, ... (fewer videos than accounts: the first ones only);
   the account's repost channels get the same file
4. once every post of a file is done and at least one was sent, moves that file to the Drive trash (30 days
   recoverable) and logs it. A file whose posts all failed stays in the folder for the next run.

Needs GDRIVE_CLIENT_ID/SECRET + GDRIVE_FULL_REFRESH_TOKEN (scope drive: `python3 daily/gdrive.py auth --full`)
and the Buffer key(s) of the channels.
"""
import argparse
import datetime as dt
import json
import os
import sys
import tempfile
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import buffer_api  # noqa: E402
import gdrive  # noqa: E402
from publish import due_time  # noqa: E402

API = gdrive.API
P = {'supportsAllDrives': True}


class FullDrive:
    def __init__(self):
        self.h = {'Authorization': 'Bearer ' + gdrive.access_token(full=True)}

    def videos(self, folder):
        out, page = [], None
        while True:
            r = requests.get(API + '/files', headers=self.h, timeout=30, params={
                'q': "'%s' in parents and trashed = false and mimeType contains 'video/'" % folder,
                'fields': 'nextPageToken, files(id,name,size)', 'orderBy': 'name_natural,createdTime',
                'pageSize': 200, 'pageToken': page, 'includeItemsFromAllDrives': True, **P})
            r.raise_for_status()
            out += r.json().get('files', [])
            page = r.json().get('nextPageToken')
            if not page:
                return out

    def share(self, fid):
        requests.post(API + '/files/%s/permissions' % fid, headers=self.h, timeout=30, params=P,
                      json={'role': 'reader', 'type': 'anyone'}).raise_for_status()
        return 'https://drive.usercontent.google.com/download?id=%s&export=download&confirm=t' % fid

    def unshare(self, fid):
        r = requests.get(API + '/files/%s/permissions' % fid, headers=self.h, timeout=30, params=P)
        if r.status_code == 404:
            return
        r.raise_for_status()
        for p in r.json().get('permissions', []):
            if p.get('type') == 'anyone':
                requests.delete(API + '/files/%s/permissions/%s' % (fid, p['id']), headers=self.h, timeout=30,
                                params=P).raise_for_status()

    def trash(self, fid):
        requests.patch(API + '/files/' + fid, headers=self.h, timeout=30, params=P,
                       json={'trashed': True}).raise_for_status()


def post_status(channel, post_id):
    buffer_api.use_key(channel.get('key_env', 'BUFFER_API_KEY'))
    try:
        q = 'query { post(input: {id: %s}) { id status error { message } sentAt externalLink } }' % buffer_api.lit(post_id)
        return buffer_api.gql(q)['post'] or {}
    finally:
        buffer_api.use_key('BUFFER_API_KEY')


def read_log():
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, 'q.jsonl')
        if gdrive.get_state('queue_posted.jsonl', p):
            return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
    return []


def log(entries):
    """append to Drive state queue_posted.jsonl"""
    if not entries:
        return
    try:
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, 'q.jsonl')
            if not gdrive.get_state('queue_posted.jsonl', p):
                open(p, 'w').close()
            with open(p, 'a', encoding='utf-8') as f:
                for e in entries:
                    f.write(json.dumps(e, ensure_ascii=False) + '\n')
            gdrive.put_state(p, 'queue_posted.jsonl')
    except Exception as e:  # noqa: BLE001
        print('warning: could not write the Drive log:', e)


def free_videos(d, vids):
    """files from earlier runs: all posts done + one sent -> trash; any still waiting at Buffer -> held back; all errors -> free again"""
    ids = {v['id'] for v in vids}
    held, chans, out = set(), None, []
    for e in read_log():   # the log must be readable: without it a video could go out twice
        if e.get('file_id') not in ids or e.get('trashed') or e.get('file_id') in held:
            continue
        chans = chans or {c['name']: c for c in buffer_api.all_channels()}
        st = []
        for p in e.get('posts', []):
            ch = chans.get(p['channel'])
            st.append(str(post_status(ch, p['id']).get('status', '')).lower() if ch else 'unknown')
        if any(s not in ('sent', 'error') for s in st):
            print('earlier run: %s still waiting at Buffer (%s) -> held back' % (e['file'], ', '.join(st)))
            held.add(e['file_id'])
        elif 'sent' in st:
            d.trash(e['file_id'])
            print('earlier run: %s went out after all -> trashed' % e['file'])
            out.append(dict(e, trashed=True, date=dt.date.today().isoformat()))
            held.add(e['file_id'])
    log(out)
    return [v for v in vids if v['id'] not in held]


def groups(a):
    """[(account, [repost names], 'HH:MM')]: the sheet's Gerar = n rows, or --channel"""
    if a.channel:
        return [(n.strip(), [], a.at) for n in a.channel.split(',') if n.strip()]
    import sheet
    rows = sheet.queue_rows()
    if rows is None:
        sys.exit('no accounts sheet (and no cached copy): pass --channel')
    return [(r['account'], r['reposts'], r['post_time']) for r in sorted(rows, key=lambda r: r['post_time'])]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--folder', required=True, help='Drive folder id (the part after /folders/ in its link)')
    ap.add_argument('--channel', default='', help='Buffer channel names, comma-separated (default: the sheet\'s Gerar = n rows)')
    ap.add_argument('--caption', default='')
    ap.add_argument('--at', default='14:00', help='time for --channel (the sheet has its own times)')
    ap.add_argument('--tz', default='Europe/London')
    ap.add_argument('--wait', type=int, default=90, help='minutes to wait for Buffer after the last due time')
    ap.add_argument('--max-wait', type=int, default=240, help='never wait longer than this (minutes); later posts '
                    'are confirmed and trashed by the next run')
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()

    d = FullDrive()
    vids = d.videos(a.folder)
    if not a.list:
        vids = free_videos(d, vids)
    print('%d video(s) in the queue' % len(vids))
    for v in vids[:20]:
        print('  %-50s %6.1f MB' % (v['name'], int(v.get('size', 0)) / 1e6))
    gs = groups(a)
    print('accounts: ' + '; '.join('%s %s%s' % (g[0], g[2], (' + ' + ', '.join(g[1])) if g[1] else '') for g in gs))
    if a.list:
        return
    names = [g[0] for g in gs] + [r for g in gs for r in g[1]]
    if len(set(n.lower() for n in names)) != len(names):
        sys.exit('an account is listed twice (as main or repost)')
    known = buffer_api.all_channels()
    bad = 0

    def chan(n):
        want = n.lower().lstrip('@')
        m = [c for c in known if want in (str(c.get('name', '')).lower().lstrip('@'), str(c['id']).lower())]
        return m[0] if len(m) == 1 else None
    ok = []
    for acc, reps, at in gs:
        if not chan(acc):
            print('NOT CONNECTED in Buffer: %s - skipped' % acc)
            bad += 1
            continue
        rc = []
        for r in reps:
            if chan(r):
                rc.append(chan(r))
            else:
                print('NOT CONNECTED in Buffer: %s (repost of %s) - skipped' % (r, acc))
                bad += 1
        ok.append((chan(acc), rc, at))
    if len(vids) < len(ok):
        print('ONLY %d video(s) for %d accounts: %s get nothing today' % (
            len(vids), len(ok), ', '.join(g[0]['name'] for g in ok[len(vids):])))
    pairs = list(zip(ok, vids))   # one distinct file per main account (+ its reposts)
    if not pairs:
        print('QUEUE EMPTY - nothing posted')
        sys.exit(1 if bad else 0)

    today = dt.date.today().isoformat()
    jobs = []   # (file, [(channel, post, due)])
    for (main_ch, reps, at), v in pairs:
        due, mode = due_time(at, a.tz, 'now')
        url, posts = None, []
        for ch in [main_ch] + reps:
            try:
                url = url or d.share(v['id'])
                p = buffer_api.create_post(ch, a.caption, video_url=url, due_at=due, mode=mode, title=a.caption or v['name'])
                print('Buffer post %s -> %s: %s (%s)' % (p['id'], ch['name'], v['name'], p.get('dueAt') or 'now'))
                posts.append((ch, p, due))
            except Exception as e:  # noqa: BLE001
                print('FAILED %s: %s' % (ch['name'], e))
                bad += 1
        if posts:
            jobs.append((v, posts))
        elif url:
            d.unshare(v['id'])
    # log before waiting, so a crash during the wait can never free these files for another account
    log([{'date': today, 'file': v['name'], 'file_id': v['id'],
          'posts': [{'channel': ch['name'], 'id': p['id'], 'status': 'pending'} for ch, p, _ in posts]}
         for v, posts in jobs])

    def at_utc(due):
        return dt.datetime.fromisoformat(due.replace('Z', '+00:00')) if due else dt.datetime.now(dt.timezone.utc)
    now = dt.datetime.now(dt.timezone.utc)
    last = max(at_utc(due) for _, posts in jobs for _, _, due in posts)
    end = time.time() + min(60 * a.max_wait, max(0, (last - now).total_seconds()) + 60 * a.wait)
    status = {p['id']: '' for _, posts in jobs for _, p, _ in posts}
    open_files = {v['id']: (v, posts) for v, posts in jobs}
    done = []
    while open_files and time.time() < end:
        time.sleep(60)
        for fid, (v, posts) in list(open_files.items()):
            for ch, p, _ in posts:
                if status[p['id']] in ('sent', 'error'):
                    continue
                s = post_status(ch, p['id'])
                status[p['id']] = str(s.get('status', '')).lower()
                if status[p['id']] == 'sent':
                    print('POSTED %s -> %s %s' % (v['name'], ch['name'], s.get('externalLink') or ''))
                elif status[p['id']] == 'error':
                    print('FAILED %s -> %s: %s' % (v['name'], ch['name'], (s.get('error') or {}).get('message', '')))
                    bad += 1
            st = [status[p['id']] for _, p, _ in posts]
            if any(x not in ('sent', 'error') for x in st):
                continue
            open_files.pop(fid)
            e = {'date': today, 'file': v['name'], 'file_id': fid,
                 'posts': [{'channel': ch['name'], 'id': p['id'], 'status': status[p['id']]} for ch, p, _ in posts]}
            if 'sent' in st:
                d.trash(fid)
                e['trashed'] = True
                print('%s: all posts done -> trashed' % v['name'])
            else:
                d.unshare(fid)
                print('%s: every post failed -> stays for the next run' % v['name'])
            done.append(e)
    log(done)
    late = 0
    for v, posts in open_files.values():
        for ch, p, due in posts:
            if status[p['id']] in ('sent', 'error'):
                continue
            overdue = (dt.datetime.now(dt.timezone.utc) - at_utc(due)).total_seconds() > 60 * a.wait
            late += overdue
            print('%s %s -> %s: %s' % ('NOT SENT YET' if overdue else 'SCHEDULED', v['name'], ch['name'],
                                       'Buffer is late' if overdue else 'the next run confirms it and trashes the file'))
    print('%d video(s) left in the folder' % len(d.videos(a.folder)))
    if bad or late:
        sys.exit(1)


if __name__ == '__main__':
    main()
