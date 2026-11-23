#!/usr/bin/env python3
"""Inspiration videos sent by the owner -> measurable facts + a contact sheet, archived in Drive.

    python3 inspire.py <video> [--account NAME|all] [--note "what the owner likes about it"]

Prints duration, cut rhythm (all, first 7 s), hook timing, loudness/music, brightness, and writes a contact
sheet (1 frame/s) next to the video for Claude to look at. Then Claude writes the "reference card" (what to
copy: hook, pacing, framing, captions, sound, story shape) and stores it with:
    python3 inspire.py --save-card card.md <video>      # -> Drive _inspiration/<file> + _state/inspiration.md
The daily run reads _state/inspiration.md before writing stories and shots. To keep that read cheap it holds
only the rules of the newest MAX_CARDS cards (heading + "rules to apply" bullets, at most MAX_LINES lines);
the full cards go to _state/inspiration_archive.md, which the daily run does not read.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile

MAX_CARDS = 8      # cards whose rules stay in inspiration.md
MAX_LINES = 60     # hard cap for inspiration.md

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def probe(path):
    j = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries',
                                            'format=duration:stream=codec_type,width,height,r_frame_rate',
                                            '-of', 'json', path]))
    v = [s for s in j['streams'] if s['codec_type'] == 'video'][0]
    return float(j['format']['duration']), v['width'], v['height'], v['r_frame_rate'], \
        any(s['codec_type'] == 'audio' for s in j['streams'])


def cuts(path, thr=0.3):
    out = subprocess.run(['ffmpeg', '-i', path, '-vf', "select='gt(scene,%s)',showinfo" % thr, '-an', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r'pts_time:([\d.]+)', out)]


def loudness(path):
    out = subprocess.run(['ffmpeg', '-i', path, '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = re.search(r'Summary:.*?I:\s+(-?[\d.]+) LUFS', out, re.S)  # the summary, not the first per-frame line
    return float(m.group(1)) if m else None


def analyse(path):
    dur, w, h, fps, has_audio = probe(path)
    c = cuts(path)
    first7 = [t for t in c if t <= 7]
    gaps = [b - a for a, b in zip([0] + c, c + [dur])]
    sheet = os.path.splitext(path)[0] + '_sheet.png'
    cols, n = 8, min(int(dur) + 1, 48)            # <= 48 small frames: one cheap image to look at
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-vf',
                    'fps=%.4f,scale=120:-2,tile=%dx%d' % (n / max(dur, 1), cols, (n + cols - 1) // cols),
                    '-frames:v', '1', sheet])
    facts = {
        'duration_s': round(dur, 1), 'size': '%dx%d' % (w, h), 'fps': fps, 'audio': has_audio,
        'cuts_total': len(c), 'avg_shot_s': round(sum(gaps) / len(gaps), 2) if gaps else dur,
        'cuts_first_7s': len(first7), 'first_cut_s': round(c[0], 2) if c else None,
        'loudness_lufs': loudness(path) if has_audio else None, 'contact_sheet': sheet,
    }
    return facts


HEADER = ('# Inspiration rules (owner\'s reference videos)\n\nRead before writing stories and shots. Newest last. '
          'Apply what fits the account; never copy a story. Full cards: _state/inspiration_archive.md (do not read daily).\n')


def rules_only(card):
    """'## <date> · <file> · for <acc>' + the bullets under the rules heading (fallback: the last 8 bullets)."""
    lines = card.strip().splitlines()
    head = next((l for l in lines if l.startswith('## ')), '## ' + dt.date.today().isoformat())
    out, on = [], False
    for l in lines:
        if l.startswith('#'):
            on = bool(re.search(r'rule|regra|apply|aplicar', l, re.I))
        elif on and l.strip():
            out.append(l.rstrip())
    if not out:
        out = [l.rstrip() for l in lines if l.lstrip().startswith(('-', '*'))][-8:]
    return [head] + out


def compact(text):
    """Keep the newest MAX_CARDS cards and at most MAX_LINES lines (oldest cards dropped first)."""
    cards = re.split(r'\n(?=## )', text.split('\n## ', 1)[1] if '\n## ' in text else '')
    cards = ['## ' + c.strip() if not c.startswith('## ') else c.strip() for c in cards if c.strip()][-MAX_CARDS:]
    while len(cards) > 1 and sum(len(c.splitlines()) + 1 for c in cards) + 3 > MAX_LINES:
        cards.pop(0)
    return HEADER + '\n' + '\n\n'.join(cards) + '\n'


def save_card(card_path, video):
    import gdrive
    d = gdrive.Drive()
    root = d.folder(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily'))
    d.upload(video, os.path.basename(video), d.folder('_inspiration', root), 'video/mp4')
    card = open(card_path, encoding='utf-8').read().strip()
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, 'inspiration.md')
        old = open(p, encoding='utf-8').read() if gdrive.get_state('inspiration.md', p) else ''
        a = os.path.join(tmp, 'inspiration_archive.md')
        if not gdrive.get_state('inspiration_archive.md', a):
            open(a, 'w').write('# Inspiration cards (full, archive)\n')
        with open(a, 'a', encoding='utf-8') as f:
            if old and not old.startswith(HEADER[:30]):      # old full-card file: archive it once, then condense
                f.write('\n\n' + old.split('\n## ', 1)[-1].join(['## ', '\n']) if '\n## ' in old else '')
                old = '\n\n'.join('\n'.join(rules_only('## ' + c)) for c in old.split('\n## ')[1:])
            f.write('\n\n' + card + '\n')
        gdrive.put_state(a, 'inspiration_archive.md')
        new = compact(old + '\n\n' + '\n'.join(rules_only(card)))
        open(p, 'w', encoding='utf-8').write(new)
        gdrive.put_state(p, 'inspiration.md')
    print('saved: Drive _inspiration/%s + _state/inspiration.md (%d lines) + inspiration_archive.md'
          % (os.path.basename(video), len(new.splitlines())))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('video')
    ap.add_argument('--account', default='all')
    ap.add_argument('--note', default='')
    ap.add_argument('--save-card')
    a = ap.parse_args()
    if a.save_card:
        save_card(a.save_card, a.video)
    else:
        f = analyse(a.video)
        f.update(account=a.account, note=a.note, date=dt.date.today().isoformat(), file=os.path.basename(a.video))
        print(json.dumps(f, ensure_ascii=False))
