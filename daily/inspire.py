#!/usr/bin/env python3
"""Inspiration videos sent by the owner -> measurable facts + a contact sheet, archived in Drive.

    python3 inspire.py <video> [--account NAME|all] [--note "what the owner likes about it"]

Prints duration, cut rhythm (all, first 7 s), hook timing, loudness/music, brightness, and writes a contact
sheet (1 frame/s) next to the video for Claude to look at. Then Claude writes the "reference card" (what to
copy: hook, pacing, framing, captions, sound, story shape) and stores it with:
    python3 inspire.py --save-card card.md <video>      # -> Drive _inspiration/<file> + _state/inspiration.md
The daily run reads _state/inspiration.md before writing stories and shots.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile

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
    cols = 8
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-vf',
                    'fps=1,scale=180:-2,tile=%dx%d' % (cols, int(dur) // cols + 1), '-frames:v', '1', sheet])
    facts = {
        'duration_s': round(dur, 1), 'size': '%dx%d' % (w, h), 'fps': fps, 'audio': has_audio,
        'cuts_total': len(c), 'avg_shot_s': round(sum(gaps) / len(gaps), 2) if gaps else dur,
        'cuts_first_7s': len(first7), 'first_cut_s': round(c[0], 2) if c else None,
        'loudness_lufs': loudness(path) if has_audio else None, 'contact_sheet': sheet,
    }
    return facts


def save_card(card_path, video):
    import gdrive
    d = gdrive.Drive()
    root = d.folder(os.environ.get('GDRIVE_ROOT_FOLDER', 'TikTok Daily'))
    d.upload(video, os.path.basename(video), d.folder('_inspiration', root), 'video/mp4')
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, 'inspiration.md')
        if not gdrive.get_state('inspiration.md', p):
            open(p, 'w').write('# Inspiration references (sent by the owner)\n\nRead before writing stories and shots. '
                               'Newest last. Apply what fits the account; never copy a story.\n')
        with open(p, 'a', encoding='utf-8') as f:
            f.write('\n\n' + open(card_path, encoding='utf-8').read().strip() + '\n')
        gdrive.put_state(p, 'inspiration.md')
    print('saved: Drive _inspiration/%s + _state/inspiration.md' % os.path.basename(video))


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
        print(json.dumps(f, indent=1, ensure_ascii=False))
