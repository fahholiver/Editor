#!/usr/bin/env python3
"""Post ONE ready-made video per day from a Google Drive folder, then move it to the Drive trash.

    python3 daily/queue_post.py --folder <drive folder id> --channel strawberry.me27 [--at 14:00 --tz Europe/London]
    python3 daily/queue_post.py --folder <id> --list          # show the queue, post nothing

1. lists the videos in the folder (not trashed), oldest-named first (sort by file name: 01_, 02_ ... controls the order)
2. takes the first one, gives it a temporary public link (Buffer downloads the video from it)
3. creates the Buffer post (no caption) for --at in --tz today; if that time has passed it posts now
4. waits until Buffer reports the post as sent, then moves the file to the Drive trash (recoverable for 30 days)
   and logs it in Drive state `queue_posted.jsonl`. If the post fails, the file stays (link removed) for tomorrow.

Needs GDRIVE_CLIENT_ID/SECRET + GDRIVE_FULL_REFRESH_TOKEN (scope `drive`: `python3 daily/gdrive.py auth --full`;
the normal drive.file token cannot see folders made by hand) and the Buffer key(s) of the channel.
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


class FullDrive:
    def __init__(self):
        self.h = {'Authorization': 'Bearer ' + gdrive.access_token(full=True)}

    def videos(self, folder):
        out, page = [], None
        while True:
            r = requests.get(API + '/files', headers=self.h, timeout=30, params={
                'q': "'%s' in parents and trashed = false and mimeType contains 'video/'" % folder,
                'fields': 'nextPageToken, files(id,name,size,mimeType,createdTime)', 'orderBy': 'name_natural,createdTime',
                'pageSize': 200, 'pageToken': page, 'supportsAllDrives': True, 'includeItemsFromAllDrives': True})
            r.raise_for_status()
            j = r.json()
            out += j.get('files', [])
            page = j.get('nextPageToken')
            if not page:
                return out

    def share(self, fid):
        requests.post(API + '/files/%s/permissions' % fid, headers=self.h, timeout=30, params={'supportsAllDrives': True},
                      json={'role': 'reader', 'type': 'anyone'}).raise_for_status()
        return 'https://drive.usercontent.google.com/download?id=%s&export=download&confirm=t' % fid

    def unshare(self, fid):
        r = requests.get(API + '/files/%s/permissions' % fid, headers=self.h, timeout=30, params={'supportsAllDrives': True})
        if r.status_code == 404:
            return
        r.raise_for_status()
        for p in r.json().get('permissions', []):
            if p.get('type') == 'anyone':
                requests.delete(API + '/files/%s/permissions/%s' % (fid, p['id']), headers=self.h, timeout=30,
                                params={'supportsAllDrives': True}).raise_for_status()

    def trash(self, fid):
        requests.patch(API + '/files/' + fid, headers=self.h, timeout=30, params={'supportsAllDrives': True},
                       json={'trashed': True}).raise_for_status()


def post_status(channel, post_id):
    buffer_api.use_key(channel.get('key_env', 'BUFFER_API_KEY'))
    try:
        q = 'query { post(input: {id: %s}) { id status error { message } sentAt externalLink } }' % buffer_api.lit(post_id)
        return buffer_api.gql(q)['post']
    finally:
        buffer_api.use_key('BUFFER_API_KEY')


def read_log():
    try:
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, 'q.jsonl')
            if gdrive.get_state('queue_posted.jsonl', p):
                return [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
    except Exception as e:  # noqa: BLE001
        print('warning: could not read the Drive log:', e)
    return []


def finish_earlier(d, vids):
    """a file from an earlier run whose post went out later than that run waited: trash it now (no double post)"""
    ids = {v['id'] for v in vids}
    chans = None
    for e in read_log():
        if e.get('trashed') or e.get('file_id') not in ids:
            continue
        chans = chans or {c['name']: c for c in buffer_api.all_channels()}
        for p in e.get('posts', []):
            ch = chans.get(p['channel'])
            if ch and str(post_status(ch, p['id']).get('status', '')).lower() == 'sent':
                d.trash(e['file_id'])
                print('earlier run: %s was posted after all -> moved to trash' % e['file'])
                log(dict(e, trashed=True, date=dt.date.today().isoformat()))
                ids.discard(e['file_id'])
                break
    return [v for v in vids if v['id'] in ids]


def log(entry):
    """append to Drive state queue_posted.jsonl (best effort)"""
    try:
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, 'q.jsonl')
            if not gdrive.get_state('queue_posted.jsonl', p):
                open(p, 'w').close()
            with open(p, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            gdrive.put_state(p, 'queue_posted.jsonl')
    except Exception as e:  # noqa: BLE001
        print('warning: could not write the Drive log:', e)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--folder', required=True, help='Drive folder id (the part after /folders/ in its link)')
    ap.add_argument('--channel', default='strawberry.me27', help='Buffer channel name(s) or id(s), comma-separated')
    ap.add_argument('--caption', default='', help='post text (default: none)')
    ap.add_argument('--at', default='14:00')
    ap.add_argument('--tz', default='Europe/London')
    ap.add_argument('--wait', type=int, default=90, help='minutes to wait for Buffer to send it before giving up')
    ap.add_argument('--list', action='store_true', help='only list the queue')
    a = ap.parse_args()

    d = FullDrive()
    vids = d.videos(a.folder)
    if not a.list:
        vids = finish_earlier(d, vids)
    print('%d video(s) in the queue' % len(vids))
    for v in vids[:20]:
        print('  %-50s %6.1f MB' % (v['name'], int(v.get('size', 0)) / 1e6))
    if a.list:
        return
    if not vids:
        print('QUEUE EMPTY - nothing posted')
        return
    v = vids[0]
    channels = buffer_api.find_channels(a.channel)
    due, mode = due_time(a.at, a.tz, 'now')
    url = d.share(v['id'])
    posts = []
    try:
        for ch in channels:
            p = buffer_api.create_post(ch, a.caption, video_url=url, due_at=due, mode=mode, title=a.caption or v['name'])
            print('Buffer post %s -> %s (%s) %s' % (p['id'], ch['name'], ch['service'], p.get('dueAt') or 'now'))
            posts.append((ch, p))
    except Exception:
        if not posts:
            d.unshare(v['id'])
        raise

    # wait until every post has gone out (Buffer downloads the video only when it sends it)
    wait_until = time.time() + 60 * a.wait + (max(0, (dt.datetime.fromisoformat(due.replace('Z', '+00:00')) -
                                                     dt.datetime.now(dt.timezone.utc)).total_seconds()) if due else 0)
    pending = {p['id']: (ch, p) for ch, p in posts}
    results = {}
    while pending and time.time() < wait_until:
        time.sleep(60)
        for pid, (ch, _) in list(pending.items()):
            s = post_status(ch, pid)
            st = str(s.get('status', '')).lower()
            if st in ('sent', 'error'):
                results[pid] = s
                pending.pop(pid)
                print('%s: %s %s' % (ch['name'], st, (s.get('error') or {}).get('message', '') or s.get('externalLink') or ''))
    sent = [pid for pid, s in results.items() if str(s.get('status')).lower() == 'sent']
    entry = {'date': dt.date.today().isoformat(), 'file': v['name'], 'file_id': v['id'],
             'posts': [{'channel': ch['name'], 'id': p['id'], 'status': (results.get(p['id']) or {}).get('status', 'pending'),
                        'link': (results.get(p['id']) or {}).get('externalLink')} for ch, p in posts]}
    if sent and not pending:
        d.trash(v['id'])
        entry['trashed'] = True
        print('POSTED %s and moved it to the Drive trash; %d left in the queue' % (v['name'], len(vids) - 1))
    elif pending:
        print('NOT CONFIRMED: Buffer has not sent %d post(s) yet; file kept (public link kept for Buffer)' % len(pending))
    else:
        d.unshare(v['id'])
        print('FAILED: Buffer reported an error; %s stays in the folder for the next run' % v['name'])
    log(entry)
    if not (sent and not pending):
        sys.exit(1)


if __name__ == '__main__':
    main()
