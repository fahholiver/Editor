#!/usr/bin/env python3
"""Publish a finished Motion video to TikTok through Buffer, scheduled for a local time.

    python3 publish.py <final.mp4> --slug <slug> --title "<Title>" --caption "<caption + #hashtags>"
                       [--at 14:00] [--tz Europe/London] [--late now|queue|fail] [--now] [--channels all|name1,name2] [--dry-run]

1. makes a lighter upload copy (same picture/sound, H.264 CRF 21, <= 4 Mb/s, ~45 MB for 90 s) - TikTok re-encodes anyway
2. hosts it at a public URL: by default in the account's Google Drive folder (<day>.mp4 next to <day>.txt)
   with a public link that the next run removes (MEDIA_HOST=drive); or (MEDIA_HOST=github) on the `media`
   branch of this public repo via raw.githubusercontent.com. The branch is rewritten as ONE commit holding only the newest
   --keep videos + stories.jsonl, so the repo does not grow by a video a day.
   (Or skip this with --video-url if you host the file yourself.)
3. creates one Buffer post per TikTok channel (--channels: 'all' or names/ids) at --at in --tz, today.
   If that time has already passed: --late now -> post immediately, queue -> next Buffer queue slot,
   fail -> stop with an error.
4. if GDRIVE_* is set, saves <day>.mp4 + <day>.txt (voiceover text, caption) to Google Drive,
   one folder per TikTok account (see gdrive.py)
5. appends a line to stories.jsonl on the media branch (the story log the next run reads to avoid repeats).

Env: BUFFER_API_KEY, optional BUFFER_TIKTOK_CHANNELS (default 'all'), MEDIA_REPO_DIR (default: the git repo this file is in),
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
import plan  # noqa: E402
import gdrive  # noqa: E402


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


def video_duration(path):
    try:
        return round(float(sh('ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path,
                              capture=True)), 2)
    except Exception:  # noqa: BLE001
        return None


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
    ap.add_argument('--tz', default=os.environ.get('POST_TZ', 'Europe/London'))
    ap.add_argument('--late', default='now', choices=['now', 'queue', 'fail'])
    ap.add_argument('--thumb-ms', type=int, default=None, help='thumbnail frame offset (ms)')
    ap.add_argument('--video-url', help='already-hosted public URL (skips the media branch upload)')
    ap.add_argument('--keep', type=int, default=8, help='videos kept on the media branch (~2 days x accounts)')
    ap.add_argument('--dry-run', action='store_true', help='encode only; no upload, no Buffer post')
    ap.add_argument('--account', help='TikTok account: channel, post time, tz and format from daily/accounts.json')
    ap.add_argument('--format', default='', help='story format (logged, see daily/accounts.json)')
    ap.add_argument('--story', help='story/voiceover text file (saved to Google Drive with the video)')
    ap.add_argument('--channels', '--channel', dest='channels', default=os.environ.get('BUFFER_TIKTOK_CHANNELS', 'all'),
                    help="'all' (every TikTok channel in Buffer) or comma-separated names/ids, e.g. anna.20263,strawberry.me27")
    ap.add_argument('--now', action='store_true', help='post immediately instead of at --at')
    a = ap.parse_args()
    if a.account:
        import plan
        c = plan.account_cfg(a.account)
        a.channels = a.account
        a.format = a.format or c['format']
        if 'POST_TIME' not in os.environ:
            a.at, a.tz = c['post_time'], c['tz']

    targets = [] if a.dry_run else buffer_api.find_channels(a.channels)
    if targets:
        print('posting to: ' + ', '.join('%s (%s)' % (c['name'], c['service']) for c in targets))

    zone = ZoneInfo(a.tz)
    day = dt.datetime.now(zone).strftime('%Y-%m-%d')
    name = '%s_%s.mp4' % (day, a.slug)
    due_at, mode = (None, 'shareNow') if a.now else due_time(a.at, a.tz, a.late)
    entry = {'date': day, 'slug': a.slug, 'title': a.title, 'hook': a.hook, 'caption': a.caption,
             'format': a.format, 'channels': a.channels, 'account': a.account or a.channels,
             'duration': video_duration(a.video),
             'scheduled': '%s %s' % (a.at, a.tz) if mode == 'customScheduled' else mode}

    with tempfile.TemporaryDirectory() as tmp:
        up = os.path.join(tmp, name)
        upload_copy(a.video, up)
        if a.dry_run:
            shutil.copy(up, os.path.join(os.path.dirname(os.path.abspath(a.video)), name))
            print('dry run: would post %s with mode=%s dueAt=%s' % (name, mode, due_at))
            return

        story = open(a.story, encoding='utf-8').read().strip() if a.story and os.path.exists(a.story) else ''
        text = '%s\n%s\n\nVOICEOVER\n%s\n\nCAPTION\n%s\n' % (a.title, day, story or a.hook, a.caption)
        host = os.environ.get('MEDIA_HOST', 'drive' if gdrive.configured() else 'github')
        folder = a.account or (targets[0]['name'] if targets else 'misc')
        repo_dir = branch = None
        if a.video_url:
            url = a.video_url
        elif host == 'drive':
            # the video goes straight into the account's Drive folder next to its VoiceOver text; it gets a
            # public link only until it is posted (the next run removes the link: gdrive.py cleanup-links)
            gdrive.save_text(folder, day, text)
            fid = gdrive.save_video(folder, day, up)
            url = gdrive.share_public(fid)
            entry.update(drive_file_id=fid, gdrive='saved')
            print('saved to Drive %s/%s.mp4 + .txt (public link until posted)' % (folder, day))
        else:
            repo_dir = os.environ.get('MEDIA_REPO_DIR') or sh('git', 'rev-parse', '--show-toplevel', cwd=HERE, capture=True)
            branch = os.environ.get('MEDIA_BRANCH', 'media')
            owner, repo = repo_owner_name(repo_dir)
            base = os.environ.get('MEDIA_PUBLIC_BASE') or 'https://raw.githubusercontent.com/%s/%s/%s' % (owner, repo, branch)
            url = '%s/videos/%s' % (base.rstrip('/'), name)
            media_branch_update(repo_dir, branch, [up], dict(entry, status='uploading'), a.keep)
            print('hosted at', url)
        entry['video_url'] = url
        posts, errors = {}, {}
        for ch in targets:
            cname = ch['name']  # one post per account; a failure on one doesn't stop the others
            try:
                post = buffer_api.create_post(ch, a.caption, url, due_at, mode, a.thumb_ms, a.title)
                posts[cname] = post.get('id')
                print('Buffer post created on %s: id=%s dueAt=%s mode=%s' % (cname, post.get('id'), post.get('dueAt'), mode))
            except Exception as e:  # noqa: BLE001
                errors[cname] = str(e)[:500]
                print('FAILED on %s: %s' % (cname, e))
        # re-post the same video to the account's mirror channels (other Buffer accounts, Instagram, YouTube...)
        for m in (plan.account_cfg(a.account).get('also_post_to', []) if a.account else []):
            try:
                ch = buffer_api.find_channels(m['channel'])[0]
                m_due, m_mode = (None, 'shareNow') if a.now else due_time(m.get('post_time', a.at), m.get('tz', a.tz), a.late)
                post = buffer_api.create_post(ch, m.get('caption', a.caption), url, m_due, m_mode, a.thumb_ms, a.title)
                posts[ch['name']] = post.get('id')
                print('mirror post on %s (%s): id=%s dueAt=%s' % (ch['name'], ch['service'], post.get('id'), post.get('dueAt')))
            except BaseException as e:  # noqa: BLE001 - a mirror never blocks the main post
                errors[m.get('channel', '?')] = str(e)[:300]
                print('mirror FAILED on %s: %s' % (m.get('channel'), e))
        entry.update(status='scheduled' if posts else 'failed', buffer_posts=posts, errors=errors)
        if host == 'drive' or a.video_url:
            append_drive_log(entry)
        else:
            if posts and gdrive.configured():
                try:
                    gdrive.save_day(list(posts), day, up, text)
                except Exception as e:  # noqa: BLE001
                    print('WARNING: Google Drive save failed:', e)
            fix_log_status(repo_dir, branch, entry)
        if not posts:
            sys.exit('no Buffer post was created')


def append_drive_log(entry):
    """the story log lives in Drive (TikTok Daily/_state/stories.jsonl)"""
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, 'stories.jsonl')
        if not gdrive.get_state('stories.jsonl', p):
            open(p, 'w').close()
        with open(p, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        gdrive.put_state(p, 'stories.jsonl')


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
