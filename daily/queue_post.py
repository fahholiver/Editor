#!/usr/bin/env python3
"""Post ready-made videos from ONE Google Drive folder: a DIFFERENT video to each channel, every day.

    python3 daily/queue_post.py --folder <id> --channel strawberry.me27,user971745690815,stevevrcxj0 \\
        --caption "#emotional #respectpeople" --at 14:00 --tz Europe/London
    python3 daily/queue_post.py --folder <id> --list          # show the queue, post nothing

1. lists the videos in the folder (not trashed), by file name (01_, 02_ ... sets the order)
2. drops every file already in the Drive log `queue_posted.jsonl` that was sent or is still waiting at Buffer
   (sent -> trashed now), so a video is never offered twice, to the same or another channel
3. gives channel 1 the first video, channel 2 the second, ... (fewer videos than channels: the first ones only)
4. after Buffer reports a post as sent, moves that file to the Drive trash (30 days recoverable) and logs it.
   A failed post leaves its file in the folder for the next run.

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
    """files from earlier runs: sent -> trash; still waiting at Buffer -> held back; all errors -> free again"""
    ids = {v['id'] for v in vids}
    held, chans, out = set(), None, []
    for e in read_log():   # the log must be readable: without it a video could go out twice
        if e.get('file_id') not in ids or e.get('trashed'):
            continue
        chans = chans or {c['name']: c for c in buffer_api.all_channels()}
        st = []
        for p in e.get('posts', []):
            ch = chans.get(p['channel'])
            st.append(str(post_status(ch, p['id']).get('status', '')).lower() if ch else 'unknown')
        if 'sent' in st:
            d.trash(e['file_id'])
            print('earlier run: %s went out after all -> trashed' % e['file'])
            out.append(dict(e, trashed=True, date=dt.date.today().isoformat()))
            held.add(e['file_id'])
        elif any(s != 'error' for s in st):
            print('earlier run: %s still waiting at Buffer (%s) -> held back' % (e['file'], ', '.join(st)))
            held.add(e['file_id'])
    log(out)
    return [v for v in vids if v['id'] not in held]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--folder', required=True, help='Drive folder id (the part after /folders/ in its link)')
    ap.add_argument('--channel', default='strawberry.me27', help='Buffer channel names, comma-separated: one video each')
    ap.add_argument('--caption', default='')
    ap.add_argument('--at', default='14:00')
    ap.add_argument('--tz', default='Europe/London')
    ap.add_argument('--wait', type=int, default=90, help='minutes to wait for Buffer to send them')
    ap.add_argument('--list', action='store_true')
    a = ap.parse_args()

    d = FullDrive()
    vids = d.videos(a.folder)
    if not a.list:
        vids = free_videos(d, vids)
    print('%d video(s) in the queue' % len(vids))
    for v in vids[:20]:
        print('  %-50s %6.1f MB' % (v['name'], int(v.get('size', 0)) / 1e6))
    if a.list:
        return
    names = [c.strip() for c in a.channel.split(',') if c.strip()]
    if len(set(names)) != len(names):
        sys.exit('a channel is listed twice')
    found = {c['name']: c for c in buffer_api.find_channels(','.join(names))}
    missing = [n for n in names if n not in found]
    if missing:
        sys.exit('not connected in Buffer: ' + ', '.join(missing))
    if len(vids) < len(names):
        print('ONLY %d video(s) for %d channels: %s get nothing today' % (len(vids), len(names), ', '.join(names[len(vids):])))
    pairs = list(zip([found[n] for n in names], vids))   # one distinct file per channel
    if not pairs:
        print('QUEUE EMPTY - nothing posted')
        return

    due, mode = due_time(a.at, a.tz, 'now')
    today = dt.date.today().isoformat()
    jobs = []
    for ch, v in pairs:
        try:
            url = d.share(v['id'])
            p = buffer_api.create_post(ch, a.caption, video_url=url, due_at=due, mode=mode, title=a.caption or v['name'])
            print('Buffer post %s -> %s: %s (%s)' % (p['id'], ch['name'], v['name'], p.get('dueAt') or 'now'))
            jobs.append((ch, v, p))
        except Exception as e:  # noqa: BLE001
            d.unshare(v['id'])
            print('FAILED %s: %s (file stays in the queue)' % (ch['name'], e))
    # log before waiting, so a crash during the wait can never free these files for another channel
    log([{'date': today, 'file': v['name'], 'file_id': v['id'],
          'posts': [{'channel': ch['name'], 'id': p['id'], 'status': 'pending'}]} for ch, v, p in jobs])

    end = time.time() + 60 * a.wait + (max(0, (dt.datetime.fromisoformat(due.replace('Z', '+00:00')) -
                                               dt.datetime.now(dt.timezone.utc)).total_seconds()) if due else 0)
    pending = {p['id']: (ch, v) for ch, v, p in jobs}
    done = []
    while pending and time.time() < end:
        time.sleep(60)
        for pid, (ch, v) in list(pending.items()):
            s = post_status(ch, pid)
            st = str(s.get('status', '')).lower()
            if st not in ('sent', 'error'):
                continue
            pending.pop(pid)
            e = {'date': today, 'file': v['name'], 'file_id': v['id'],
                 'posts': [{'channel': ch['name'], 'id': pid, 'status': st, 'link': s.get('externalLink')}]}
            if st == 'sent':
                d.trash(v['id'])
                e['trashed'] = True
                print('POSTED %s -> %s %s (trashed)' % (v['name'], ch['name'], s.get('externalLink') or ''))
            else:
                d.unshare(v['id'])
                print('FAILED %s -> %s: %s (stays for the next run)' % (v['name'], ch['name'], (s.get('error') or {}).get('message', '')))
            done.append(e)
    log(done)
    for pid, (ch, v) in pending.items():
        print('NOT CONFIRMED %s -> %s: Buffer has not sent it yet (held back from other channels)' % (v['name'], ch['name']))
    left = len(d.videos(a.folder))
    print('%d video(s) left in the folder' % left)
    if pending or any(e['posts'][0]['status'] != 'sent' for e in done) or len(jobs) < len(names):
        sys.exit(1)


if __name__ == '__main__':
    main()
