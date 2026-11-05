#!/usr/bin/env python3
"""The Motion animation engine as a package in Google Drive, so a fresh daily session (which cannot clone the
private Motion repo) can use it; and archiving each day's story folder back to Drive.

    python3 engine.py pack <motion_dir>          # upload engine -> Drive TikTok Daily/_assets/motion_engine.tar.gz
    python3 engine.py fetch <dest_dir>           # download + unpack it (daily run, step 0)
    python3 engine.py save-story <motion_dir> <slug>   # Drive TikTok Daily/_stories/<slug>.tar.gz
"""
import os
import sys
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gdrive  # noqa: E402

HEAVY = ('.wav', '.mp3', '.mkv', '.mp4', '.png', '.jpg')
SKIP_DIRS = {'build', 'stills', 'stems', 'output', '__pycache__', '.git'}


def _filter(ti):
    parts = set(ti.name.split('/'))
    if parts & SKIP_DIRS or ti.name.endswith(HEAVY) or '/_story' in ti.name:
        return None
    return ti


def pack(motion):
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, 'motion_engine.tar.gz')
        with tarfile.open(p, 'w:gz') as t:
            for name in sorted(os.listdir(motion)):
                if name in SKIP_DIRS or name.startswith('_story') or name.startswith('.'):
                    continue
                t.add(os.path.join(motion, name), arcname=name, filter=_filter)
        print('engine package %.1f MB' % (os.path.getsize(p) / 1e6))
        print('uploaded', gdrive.put_asset(p, 'motion_engine.tar.gz'))


def fetch(dest):
    os.makedirs(dest, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, 'e.tar.gz')
        if not gdrive.get_asset('motion_engine.tar.gz', p):
            sys.exit('motion_engine.tar.gz not found in Drive TikTok Daily/_assets')
        with tarfile.open(p) as t:
            t.extractall(dest, filter='data')
    print('engine unpacked in', dest, ':', ', '.join(sorted(os.listdir(dest))))


def save_story(motion, slug):
    d = gdrive.Drive()
    fid = d.folder('_stories', d.folder(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily')))
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, slug + '.tar.gz')
        with tarfile.open(p, 'w:gz') as t:
            t.add(os.path.join(motion, slug), arcname=slug, filter=_filter)
        d.upload(p, slug + '.tar.gz', fid, 'application/gzip')
    print('story folder saved to Drive _stories/%s.tar.gz' % slug)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'pack' and len(sys.argv) > 2:
        pack(sys.argv[2])
    elif cmd == 'fetch' and len(sys.argv) > 2:
        fetch(sys.argv[2])
    elif cmd == 'save-story' and len(sys.argv) > 3:
        save_story(sys.argv[2], sys.argv[3])
    else:
        sys.exit(__doc__)
