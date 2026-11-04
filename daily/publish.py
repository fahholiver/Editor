#!/usr/bin/env python3
"""Publish a finished Motion video to TikTok through Buffer, scheduled for a local time.

    python3 publish.py <final.mp4> --slug <slug> --title "<Title>" --caption "<caption + #hashtags>"
                       [--at 14:00] [--tz America/Sao_Paulo] [--late now|queue|fail] [--dry-run]

1. makes a lighter upload copy (same picture/sound, H.264 CRF 21, <= 4 Mb/s, ~45 MB for 90 s) - TikTok re-encodes anyway
2. hosts it at a public URL: pushes it to the `media` branch of this (public) repo and uses the
   raw.githubusercontent.com link. The branch is rewritten as ONE commit holding only the newest
   --keep videos + stories.jsonl, so the repo does not grow by a video a day.
   (Or skip this with --video-url if you host the file yourself.)
3. creates the Buffer post on the TikTok channel (BUFFER_TIKTOK_CHANNEL_ID) at --at in --tz, today.
   If that time has already passed: --late now -> post immediately, queue -> next Buffer queue slot,
   fail -> stop with an error.
4. appends a line to stories.jsonl on the media branch (the story log the next run reads to avoid repeats).

Env: BUFFER_API_KEY, BUFFER_TIKTOK_CHANNEL_ID, optional MEDIA_REPO_DIR (default: the git repo this file is in),
MEDIA_BRANCH (default media), MEDIA_PUBLIC_BASE (default https://raw.githubusercontent.com/<owner>/<repo>/<branch>).
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import buffer_api  # noqa: E402


def sh(*cmd, cwd=None, capture=False):
    if capture:
        return subprocess.check_output(cmd, cwd=cwd, text=True).strip()
    subprocess.check_call(cmd, cwd=cwd)


def upload_copy(src, dst):
    sh('ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-map', '0:v:0', '-map', '0:a:0',
       '-c:v', 'libx264', '-profile:v', 'high', '-preset', 'medium', '-crf', '21', '-maxrate', '4M', '-bufsize', '8M',
       '-pix_fmt', 'yuv420p', '-r', '30', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', dst)
    mb = os.path.getsize(dst) / 1e6
    print('upload copy: %.1f MB' % mb)
    if mb > 95:
        sys.exit('upload copy is %.0f MB - over GitHub\'s 100 MB file limit; host it elsewhere (--video-url)' % mb)


def repo_owner_name(repo_dir):
    url = sh('git', 'remote', 'get-url', 'origin', cwd=repo_dir, capture=True)
    m = re.search(r'[/:]([^/:]+)/([^/]+?)(?:\.git)?/?$', url)
    if not m:
        sys.exit('cannot parse owner/repo from origin url: %s' % url)
    return m.group(1), m.group(2)


def media_branch_update(repo_dir, branch, add_files, log_entry, keep):
    """Rewrite <branch> as a single commit: newest `keep` videos (incl. the new one) + stories.jsonl."""
    origin = sh('git', 'remote', 'get-url', 'origin', cwd=repo_dir, capture=True)
    with tempfile.TemporaryDirectory() as tmp:
        sh('git', 'init', '-q', tmp)
        sh('git', 'remote', 'add', 'origin', origin, cwd=tmp)
        have = subprocess.call(['git', 'fetch', '-q', '--depth', '1', 'origin', branch], cwd=tmp) == 0
        if have:
            sh('git', 'checkout', '-q', 'FETCH_HEAD', cwd=tmp)
        vdir = os.path.join(tmp, 'videos')
        os.makedirs(vdir, exist_ok=True)
        for f in add_files:
            shutil.copy(f, vdir)
        vids = sorted(os.listdir(vdir))  # names start with the date -> oldest first
        for old in vids[:-keep] if keep > 0 else []:
            os.remove(os.path.join(vdir, old))
        logp = os.path.join(tmp, 'stories.jsonl')
        with open(logp, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        if not os.path.exists(os.path.join(tmp, 'README.md')):
            open(os.path.join(tmp, 'README.md'), 'w').write(
                'Hosting for the daily TikTok videos (see daily/README.md on the main branch).\n'
                'This branch is rewritten on every run and keeps only the newest videos + stories.jsonl.\n')
        sh('git', 'checkout', '-q', '--orphan', '_new', cwd=tmp)
        sh('git', 'add', '-A', cwd=tmp)
        sh('git', '-c', 'user.name=daily-video-bot', '-c', 'user.email=daily-video-bot@users.noreply.github.com',
           'commit', '-q', '-m', 'media: %s' % log_entry.get('slug', ''), cwd=tmp)
        for attempt in range(4):
            if subprocess.call(['git', 'push', '-q', '-f', 'origin', 'HEAD:refs/heads/' + branch], cwd=tmp) == 0:
                return
            import time
            time.sleep(2 ** (attempt + 1))
        sys.exit('git push of the media branch failed')


def due_time(at, tz, late):
    zone = ZoneInfo(tz)
    now = dt.datetime.now(zone)
    h, m = map(int, at.split(':'))
    due = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if due <= now + dt.timedelta(minutes=2):
        if late == 'fail':
            sys.exit('%s %s already passed (now %s)' % (at, tz, now.strftime('%H:%M')))
        return None, ('shareNow' if late == 'now' else 'addToQueue')
    return due.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'), 'customScheduled'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('video')
    ap.add_argument('--slug', required=True)
    ap.add_argument('--title', required=True)
    ap.add_argument('--caption', required=True)
    ap.add_argument('--hook', default='', help='the story\'s first line, saved in the log')
    ap.add_argument('--at', default=os.environ.get('POST_TIME', '14:00'))
    ap.add_argument('--tz', default=os.environ.get('POST_TZ', 'America/Sao_Paulo'))
    ap.add_argument('--late', default='now', choices=['now', 'queue', 'fail'])
    ap.add_argument('--thumb-ms', type=int, default=None, help='thumbnail frame offset (ms)')
    ap.add_argument('--video-url', help='already-hosted public URL (skips the media branch upload)')
    ap.add_argument('--keep', type=int, default=2, help='videos kept on the media branch')
    ap.add_argument('--dry-run', action='store_true', help='encode only; no upload, no Buffer post')
    a = ap.parse_args()

    channel = os.environ.get('BUFFER_TIKTOK_CHANNEL_ID')
    if not a.dry_run and not channel:
        sys.exit('BUFFER_TIKTOK_CHANNEL_ID is not set (run: python3 daily/buffer_api.py channels)')

    zone = ZoneInfo(a.tz)
    day = dt.datetime.now(zone).strftime('%Y-%m-%d')
    name = '%s_%s.mp4' % (day, a.slug)
    due_at, mode = due_time(a.at, a.tz, a.late)
    entry = {'date': day, 'slug': a.slug, 'title': a.title, 'hook': a.hook, 'caption': a.caption,
             'scheduled': '%s %s' % (a.at, a.tz) if mode == 'customScheduled' else mode}

    with tempfile.TemporaryDirectory() as tmp:
        up = os.path.join(tmp, name)
        upload_copy(a.video, up)
        if a.dry_run:
            shutil.copy(up, os.path.join(os.path.dirname(os.path.abspath(a.video)), name))
            print('dry run: would post %s with mode=%s dueAt=%s' % (name, mode, due_at))
            return

        repo_dir = os.environ.get('MEDIA_REPO_DIR') or sh('git', 'rev-parse', '--show-toplevel', cwd=HERE, capture=True)
        branch = os.environ.get('MEDIA_BRANCH', 'media')
        if a.video_url:
            url = a.video_url
        else:
            owner, repo = repo_owner_name(repo_dir)
            base = os.environ.get('MEDIA_PUBLIC_BASE') or 'https://raw.githubusercontent.com/%s/%s/%s' % (owner, repo, branch)
            url = '%s/videos/%s' % (base.rstrip('/'), name)
        entry['video_url'] = url

        # create the post first (so a failed post does not leave a dangling log line), then record it
        if not a.video_url:
            media_branch_update(repo_dir, branch, [up], dict(entry, status='uploading'), a.keep)
            print('hosted at', url)
        post = buffer_api.create_post(channel, a.caption, url, due_at, mode, a.thumb_ms)
        print('Buffer post created: id=%s dueAt=%s mode=%s' % (post.get('id'), post.get('dueAt'), mode))
        entry.update(status='scheduled', buffer_post_id=post.get('id'))
        if not a.video_url:  # rewrite the log line from "uploading" to "scheduled" (video already there)
            fix_log_status(repo_dir, branch, entry)


def fix_log_status(repo_dir, branch, entry):
    origin = sh('git', 'remote', 'get-url', 'origin', cwd=repo_dir, capture=True)
    with tempfile.TemporaryDirectory() as tmp:
        sh('git', 'init', '-q', tmp)
        sh('git', 'remote', 'add', 'origin', origin, cwd=tmp)
        sh('git', 'fetch', '-q', '--depth', '1', 'origin', branch, cwd=tmp)
        sh('git', 'checkout', '-q', 'FETCH_HEAD', cwd=tmp)
        p = os.path.join(tmp, 'stories.jsonl')
        lines = open(p, encoding='utf-8').read().splitlines()
        lines[-1] = json.dumps(entry, ensure_ascii=False)
        open(p, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
        sh('git', 'add', 'stories.jsonl', cwd=tmp)
        sh('git', '-c', 'user.name=daily-video-bot', '-c', 'user.email=daily-video-bot@users.noreply.github.com',
           'commit', '-q', '--amend', '-m', 'media: %s' % entry['slug'], cwd=tmp)
        if subprocess.call(['git', 'push', '-q', '-f', 'origin', 'HEAD:refs/heads/' + branch], cwd=tmp):
            print('warning: could not update the log status (the post itself is scheduled)')


if __name__ == '__main__':
    main()
