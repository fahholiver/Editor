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
import re
import os
import sys
import urllib.parse

import requests

SCOPE = 'https://www.googleapis.com/auth/drive.file'
FULL_SCOPE = 'https://www.googleapis.com/auth/drive'   # only for queue_post.py (reads + trashes the owner's own folder)
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


def access_token(full=False):
    """full=True: token from GDRIVE_FULL_REFRESH_TOKEN (scope drive, sees folders the owner made by hand)"""
    cid, sec = _client()
    env = 'GDRIVE_FULL_REFRESH_TOKEN' if full else 'GDRIVE_REFRESH_TOKEN'
    if not os.environ.get(env):
        sys.exit('%s is not set (python3 daily/gdrive.py auth%s, see daily/README.md)' % (env, ' --full' if full else ''))
    r = requests.post('https://oauth2.googleapis.com/token', timeout=30, data={
        'client_id': cid, 'client_secret': sec, 'grant_type': 'refresh_token',
        'refresh_token': os.environ[env]})
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


IDEAS_DOC = 'IDEIAS — escreva aqui'
IDEAS_TEMPLATE = """IDEIAS PARA OS PRÓXIMOS VÍDEOS
Escreva uma ideia por linha. Comece com a conta (ou "todas") e dois pontos. Exemplos:
anna.20263: uma história num trem noturno da Deutsche Bahn parado no meio do nada
todas: o vizinho que só aparece nas fotos
mandraketoons: deixar os vídeos mais longos, perto de 2 minutos

A rotina diária lê este documento toda manhã, usa as ideias que ainda não foram usadas
(no máximo uma por conta por dia) e registra quais já usou. Pode apagar as antigas quando quiser.
---
"""


def ideas_doc():
    """the Google Doc the owner writes ideas in (created by this app so it can read it); returns its id"""
    d = Drive()
    root = d.folder(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily'))
    fid = d._find(IDEAS_DOC, root)
    if fid:
        return fid
    meta = {'name': IDEAS_DOC, 'parents': [root], 'mimeType': 'application/vnd.google-apps.document'}
    boundary = 'ideasdoc'
    body = ('--%s\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n%s\r\n--%s\r\n'
            'Content-Type: text/plain; charset=UTF-8\r\n\r\n%s\r\n--%s--' % (
                boundary, json.dumps(meta), boundary, IDEAS_TEMPLATE, boundary)).encode('utf-8')
    r = requests.post(UPLOAD, headers=dict(d.h, **{'Content-Type': 'multipart/related; boundary=' + boundary}),
                      params={'uploadType': 'multipart', 'fields': 'id'}, data=body, timeout=60)
    r.raise_for_status()
    return r.json()['id']


def read_ideas():
    d = Drive()
    r = requests.get(API + '/files/%s/export' % ideas_doc(), headers=d.h, params={'mimeType': 'text/plain'}, timeout=60)
    r.raise_for_status()
    text = r.content.decode('utf-8-sig')
    return text.split('---', 1)[1].strip() if '---' in text else text.strip()


VISUAL_DOC = 'IDEIAS VISUAIS — cole imagens aqui'
VISUAL_TEMPLATE = """IDEIAS VISUAIS
Cole imagens aqui (prints, desenhos, personagens, cenários, paletas de cor, capturas de vídeos que você gosta).
Embaixo de cada imagem escreva para qual conta (ou "todas") e o que você quer dela. Exemplo:
[imagem]  todas: quero corredores com essa luz verde e sombras longas
A rotina diária baixa este documento com as imagens toda manhã e adapta o desenho 2D (estilo, cores, cenários,
personagens) - sem copiar a arte, só a ideia.
---
"""


def _make_doc(name, template):
    d = Drive()
    root = d.folder(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily'))
    fid = d._find(name, root)
    if fid:
        return fid
    meta = {'name': name, 'parents': [root], 'mimeType': 'application/vnd.google-apps.document'}
    boundary = 'ideasdoc'
    body = ('--%s\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n%s\r\n--%s\r\n'
            'Content-Type: text/plain; charset=UTF-8\r\n\r\n%s\r\n--%s--' % (
                boundary, json.dumps(meta), boundary, template, boundary)).encode('utf-8')
    r = requests.post(UPLOAD, headers=dict(d.h, **{'Content-Type': 'multipart/related; boundary=' + boundary}),
                      params={'uploadType': 'multipart', 'fields': 'id'}, data=body, timeout=60)
    r.raise_for_status()
    return r.json()['id']


def read_visual_ideas(dest):
    """export the visual-ideas doc as HTML + images into dest; returns (text, [image paths])"""
    import io
    import zipfile
    import html as _html
    d = Drive()
    fid = _make_doc(VISUAL_DOC, VISUAL_TEMPLATE)
    r = requests.get(API + '/files/%s/export' % fid, headers=d.h, params={'mimeType': 'application/zip'}, timeout=120)
    r.raise_for_status()
    os.makedirs(dest, exist_ok=True)
    zipfile.ZipFile(io.BytesIO(r.content)).extractall(dest)
    imgs, text = [], ''
    for root_, _, files in os.walk(dest):
        for f in sorted(files):
            p = os.path.join(root_, f)
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                imgs.append(p)
            elif f.lower().endswith('.html'):
                raw = open(p, encoding='utf-8', errors='replace').read()
                raw = re.sub(r'<img[^>]*src="([^"]+)"[^>]*>', lambda m: '\n[IMAGEM: %s]\n' % m.group(1), raw)
                text = _html.unescape(re.sub(r'<[^>]+>', '\n', raw))
                text = re.sub(r'\n\s*\n+', '\n', text)
    text = text.split('---', 1)[1].strip() if '---' in text else text.strip()
    return text, imgs


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    full = '--full' in sys.argv
    if full:
        sys.argv.remove('--full')
    if cmd == 'auth':
        cid, _ = _client()
        print('https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode({
            'client_id': cid, 'redirect_uri': REDIRECT, 'response_type': 'code', 'scope': FULL_SCOPE if full else SCOPE,
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
        print(('GDRIVE_FULL_REFRESH_TOKEN=' if full else 'GDRIVE_REFRESH_TOKEN=') + j['refresh_token'])
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
                ents = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
                # a file is still needed while any entry from today (e.g. a repost scheduled later) points to it
                keep = {e.get('drive_file_id') for e in ents if e.get('date', today) >= today}
                for fid in {e.get('drive_file_id') for e in ents if e.get('date', today) < today} - keep - {None}:
                    if unshare(fid):
                        n += 1
                print('public links removed:', n)
    elif cmd == 'visual-ideas' and len(sys.argv) > 2:
        t, imgs = read_visual_ideas(sys.argv[2])
        print(t)
        print('images:', ' '.join(imgs) or 'none')
    elif cmd == 'ideas':
        print(read_ideas())
    elif cmd == 'test':
        d = Drive()
        root = d.folder(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily'))
        print('ok - root folder id', root)
    else:
        sys.exit(__doc__)
