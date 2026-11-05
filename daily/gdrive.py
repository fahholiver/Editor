#!/usr/bin/env python3
"""Save each day's video + voiceover text to Google Drive, one folder per TikTok account.

    Drive/<GDRIVE_ROOT_FOLDER>/<account>/<YYYY-MM-DD>.mp4
                                        /<YYYY-MM-DD>.txt   (title, voiceover text, caption)

One-time setup (the README explains it step by step):
    python3 gdrive.py auth            # prints a Google sign-in link
    python3 gdrive.py token '<url>'   # paste the address the browser ended on -> prints GDRIVE_REFRESH_TOKEN
    python3 gdrive.py test            # creates the root folder and lists it

Env: GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, GDRIVE_REFRESH_TOKEN, optional GDRIVE_ROOT_FOLDER (default
"TikTok Daily"). Scope is drive.file: the app only sees the files and folders it created itself.
"""
import json
import os
import sys
import urllib.parse

import requests

SCOPE = 'https://www.googleapis.com/auth/drive.file'
REDIRECT = 'http://localhost'
API = 'https://www.googleapis.com/drive/v3'
UPLOAD = 'https://www.googleapis.com/upload/drive/v3/files'
FOLDER = 'application/vnd.google-apps.folder'


def configured():
    return all(os.environ.get(k) for k in ('GDRIVE_CLIENT_ID', 'GDRIVE_CLIENT_SECRET', 'GDRIVE_REFRESH_TOKEN'))


def _client():
    cid, sec = os.environ.get('GDRIVE_CLIENT_ID'), os.environ.get('GDRIVE_CLIENT_SECRET')
    if not cid or not sec:
        sys.exit('set GDRIVE_CLIENT_ID and GDRIVE_CLIENT_SECRET first (see daily/README.md)')
    return cid, sec


def access_token():
    cid, sec = _client()
    r = requests.post('https://oauth2.googleapis.com/token', timeout=30, data={
        'client_id': cid, 'client_secret': sec, 'grant_type': 'refresh_token',
        'refresh_token': os.environ['GDRIVE_REFRESH_TOKEN']})
    if r.status_code != 200:
        raise RuntimeError('Google token refresh failed %d: %s' % (r.status_code, r.text[:300]))
    return r.json()['access_token']


class Drive:
    def __init__(self):
        self.h = {'Authorization': 'Bearer ' + access_token()}

    def _find(self, name, parent, mime=None):
        q = "name = '%s' and trashed = false and '%s' in parents" % (name.replace("'", "\\'"), parent)
        if mime:
            q += " and mimeType = '%s'" % mime
        r = requests.get(API + '/files', headers=self.h, timeout=30, params={'q': q, 'fields': 'files(id,name)'})
        r.raise_for_status()
        f = r.json()['files']
        return f[0]['id'] if f else None

    def folder(self, name, parent='root'):
        fid = self._find(name, parent, FOLDER)
        if fid:
            return fid
        r = requests.post(API + '/files', headers=self.h, timeout=30, params={'fields': 'id'},
                          json={'name': name, 'mimeType': FOLDER, 'parents': [parent]})
        r.raise_for_status()
        return r.json()['id']

    def upload(self, path, name, parent, mime):
        """resumable upload; replaces the content if a file with that name is already in the folder"""
        size = os.path.getsize(path)
        old = self._find(name, parent)
        meta = {'name': name} if old else {'name': name, 'parents': [parent]}
        url = UPLOAD + ('/' + old if old else '')
        r = (requests.patch if old else requests.post)(
            url, headers=dict(self.h, **{'X-Upload-Content-Type': mime, 'X-Upload-Content-Length': str(size)}),
            params={'uploadType': 'resumable', 'fields': 'id'}, json=meta, timeout=60)
        r.raise_for_status()
        with open(path, 'rb') as f:
            r = requests.put(r.headers['Location'], data=f, timeout=1800,
                             headers={'Content-Length': str(size), 'Content-Type': mime})
        r.raise_for_status()
        return r.json()['id']


def save_day(accounts, day, video_path, text):
    """upload <day>.mp4 and <day>.txt into <root>/<account>/ for every account; returns {account: folder_id}"""
    d = Drive()
    root = d.folder(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily'))
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        txt = os.path.join(tmp, day + '.txt')
        open(txt, 'w', encoding='utf-8').write(text)
        out = {}
        for acc in accounts:
            fid = d.folder(acc, root)
            d.upload(video_path, day + '.mp4', fid, 'video/mp4')
            d.upload(txt, day + '.txt', fid, 'text/plain')
            out[acc] = fid
            print('Google Drive: saved %s.mp4 + %s.txt in %s/%s' % (day, day, os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily'), acc))
    return out


def put_asset(path, name):
    """store a shared file (e.g. the background music) in <root>/_assets on Drive"""
    d = Drive()
    fid = d.folder('_assets', d.folder(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily')))
    return d.upload(path, name, fid, 'audio/mpeg' if name.endswith('.mp3') else 'application/octet-stream')


def get_asset(name, dest):
    """download <root>/_assets/<name> to dest; returns dest or None"""
    d = Drive()
    root = d._find(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily'), 'root', FOLDER)
    fold = root and d._find('_assets', root, FOLDER)
    fid = fold and d._find(name, fold)
    if not fid:
        return None
    r = requests.get(API + '/files/' + fid, headers=d.h, params={'alt': 'media'}, timeout=300, stream=True)
    r.raise_for_status()
    with open(dest, 'wb') as f:
        for ch in r.iter_content(1 << 16):
            f.write(ch)
    return dest


def share_public(file_id):
    """anyone with the link can read the file (Buffer downloads the video from it); returns a direct URL"""
    d = Drive()
    r = requests.post(API + '/files/%s/permissions' % file_id, headers=d.h, timeout=30,
                      json={'role': 'reader', 'type': 'anyone'})
    r.raise_for_status()
    return 'https://drive.usercontent.google.com/download?id=%s&export=download&confirm=t' % file_id


def unshare(file_id):
    """remove the public link again (the file stays in its folder, private)"""
    d = Drive()
    r = requests.get(API + '/files/%s/permissions' % file_id, headers=d.h, timeout=30)
    if r.status_code == 404:
        return False
    r.raise_for_status()
    done = False
    for p in r.json().get('permissions', []):
        if p.get('type') == 'anyone':
            requests.delete(API + '/files/%s/permissions/%s' % (file_id, p['id']), headers=d.h, timeout=30).raise_for_status()
            done = True
    return done


def save_video(account, day, path):
    """<root>/<account>/<day>.mp4 - returns the file id"""
    d = Drive()
    fid = d.folder(account, d.folder(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily')))
    return d.upload(path, day + '.mp4', fid, 'video/mp4')


def save_text(account, day, text):
    import tempfile
    d = Drive()
    fid = d.folder(account, d.folder(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily')))
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, day + '.txt')
        open(p, 'w', encoding='utf-8').write(text)
        return d.upload(p, day + '.txt', fid, 'text/plain')


def get_state(name, dest):
    """download <root>/_state/<name> (story log, insights); None if it does not exist yet"""
    return _get(('_state', name), dest)


def put_state(path, name):
    d = Drive()
    fid = d.folder('_state', d.folder(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily')))
    return d.upload(path, name, fid, 'text/plain' if not name.endswith('.gz') else 'application/gzip')


def _get(parts, dest):
    d = Drive()
    cur = d._find(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily'), 'root', FOLDER)
    for i, p in enumerate(parts):
        if not cur:
            return None
        cur = d._find(p, cur, FOLDER if i < len(parts) - 1 else None)
    if not cur:
        return None
    r = requests.get(API + '/files/' + cur, headers=d.h, params={'alt': 'media'}, timeout=600, stream=True)
    r.raise_for_status()
    with open(dest, 'wb') as f:
        for ch in r.iter_content(1 << 16):
            f.write(ch)
    return dest


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'auth':
        cid, _ = _client()
        print('https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode({
            'client_id': cid, 'redirect_uri': REDIRECT, 'response_type': 'code', 'scope': SCOPE,
            'access_type': 'offline', 'prompt': 'consent'}))
    elif cmd == 'token' and len(sys.argv) > 2:
        cid, sec = _client()
        arg = sys.argv[2]
        code = urllib.parse.parse_qs(urllib.parse.urlparse(arg).query).get('code', [arg])[0]
        r = requests.post('https://oauth2.googleapis.com/token', timeout=30, data={
            'client_id': cid, 'client_secret': sec, 'code': code, 'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT})
        j = r.json()
        if 'refresh_token' not in j:
            sys.exit('failed: %s' % json.dumps(j)[:400])
        print('GDRIVE_REFRESH_TOKEN=' + j['refresh_token'])
    elif cmd == 'put-asset' and len(sys.argv) > 3:
        print('uploaded', put_asset(sys.argv[2], sys.argv[3]))
    elif cmd == 'get-asset' and len(sys.argv) > 3:
        print(get_asset(sys.argv[2], sys.argv[3]) or 'not found')
    elif cmd == 'get-state' and len(sys.argv) > 3:
        print(get_state(sys.argv[2], sys.argv[3]) or 'not found')
    elif cmd == 'put-state' and len(sys.argv) > 3:
        print('uploaded', put_state(sys.argv[2], sys.argv[3]))
    elif cmd == 'cleanup-links':
        # remove the public links of videos from earlier days (their posts have gone out by now)
        import datetime as _dt, tempfile as _tf
        today = _dt.date.today().isoformat()
        with _tf.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, 's.jsonl')
            if get_state('stories.jsonl', p):
                n = 0
                for l in open(p, encoding='utf-8'):
                    e = json.loads(l) if l.strip() else {}
                    if e.get('drive_file_id') and e.get('date', today) < today and unshare(e['drive_file_id']):
                        n += 1
                print('public links removed:', n)
    elif cmd == 'test':
        d = Drive()
        root = d.folder(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily'))
        print('ok - root folder id', root)
    else:
        sys.exit(__doc__)
