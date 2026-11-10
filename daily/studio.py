#!/usr/bin/env python3
"""Lumenstick animation studios (daily/studio/) inside the daily pipeline: same story, voice, music bed,
publish and archive steps as the Motion engine, only the picture is made by another engine.

Accounts pick one with `"engine"` in daily/accounts.json (default `motion` = the Motion engine):
    vintage   2D Vintage  - flat cartoon characters in a hand-painted three.js world (Playwright frames)
    vox       Vox Style   - paper-collage case file: cut-outs, tape, grain, slamming headlines (Remotion)
    modern    2D Modern   - needs the third-party aiTrends 2D Studio plugin; not available in the daily run

    python3 studio.py setup <root> <slug> "<Title>" <story.txt> --account <acc> [--engine vintage|vox]
    python3 studio.py stills <root>/<slug> <sec> [<sec> ...]        # contact sheet -> work/sheet.jpg
    python3 studio.py finish <root>/<slug> [--workers 2]            # -> <root>/output/<slug>_1080x1920.mp4

`setup` makes the voice exactly like bootstrap.py (account voice, ElevenLabs or Edge, word times from the
TTS), copies the kit + tools into <root>/<slug>, converts the voice/word times to the kit's files
(voice.mp3, audio/voice48.wav, work/words.json), adds the channel's background track and runs npm install.
`finish` renders, makes the sound (audio/audio.py cues + background track, voice-first mix.py), burns the
captions (vintage) and encodes to the path publish.py expects; then checks length, black frames and makes
a 12-frame QC sheet. See daily/studio/README.md for the horror rules of each style.
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STUDIO = os.path.join(HERE, 'studio')
sys.path.insert(0, HERE)

ENGINES = ('vintage', 'vox')
SHARED = ['tts.py', 'words.py', 'captions.py', 'srt.py', 'thumbnail.mjs', 'sheet.py', 'align.py', 'paper.py',
          'textures.py']
AUDIO = ['dsp.py', 'instruments.py', 'mix.py']
BED_SHARE = 0.6   # background track's share of the music stem (the cue music in audio.py is the rest)


def chromium():
    """the browser that is already on the machine (no download; Remotion/Playwright would fetch their own)"""
    full = sorted(glob.glob('/opt/pw-browsers/chromium-*/chrome-linux*/chrome'))
    shell = sorted(glob.glob('/opt/pw-browsers/chromium_headless_shell-*/*/chrome-headless-shell'))
    return (full[-1] if full else os.environ.get('CHROMIUM_PATH')), (shell[-1] if shell else None)


def env():
    e = dict(os.environ)
    full, _ = chromium()
    if full:
        e['CHROMIUM_PATH'] = full
    e.setdefault('PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD', '1')
    if not os.environ.get('GPU'):
        e.setdefault('SWIFTSHADER', '1')   # cloud machine has no GPU
    return e


def run(cmd, cwd, **kw):
    print('$', ' '.join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    subprocess.check_call(cmd, cwd=cwd, env=env(), **kw)


def meta(d):
    return json.load(open(os.path.join(d, 'studio.json')))


def patch_browser(d):
    """Playwright scripts of the vintage kit: launch the pre-installed Chromium when CHROMIUM_PATH is set"""
    for f in ['render.mjs', 'work/probe.mjs', 'work/thumbframes.mjs']:
        p = os.path.join(d, f)
        if not os.path.exists(p):
            continue
        s = open(p).read()
        s2 = re.sub(r'chromium\.launch\(\{ args \}\)',
                    'chromium.launch({ args, ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}) })', s)
        s2 = re.sub(r'chromium\.launch\(\)',
                    'chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {})', s2)
        # probe.mjs / thumbframes.mjs ask for a GPU only; the cloud machine needs SwiftShader
        s2 = s2.replace("chromium.launch({ args: ['--ignore-gpu-blocklist', '--enable-gpu'] })",
                        "chromium.launch({ args: process.env.SWIFTSHADER ? ['--use-angle=swiftshader', "
                        "'--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] : ['--ignore-gpu-blocklist', "
                        "'--enable-gpu'], ...(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {}) })")
        if s2 != s:
            open(p, 'w').write(s2)


VOX_ROOT = '''import "./index.css";
import { Composition, Still } from "remotion";
import { DURATION, ThumbA, ThumbB, WindowShort } from "./story/WindowShort";

// Today's daily video. src/story/ starts as a copy of the example (src/window/, "Why Airplane Windows
// Are Never Square"): rewrite its scenes.tsx / art.tsx / SCENES table / DURATION / thumbnails.
// studio.py finish renders the composition "Story".
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="Story" component={WindowShort} durationInFrames={Math.ceil(DURATION * 30)} fps={30} width={1080} height={1920} />
      <Still id="StoryThumbA" component={ThumbA} width={1080} height={1920} />
      <Still id="StoryThumbB" component={ThumbB} width={1080} height={1920} />
    </>
  );
};
'''


def setup(a):
    import plan
    import voiceover
    c = plan.account_cfg(a.account) if a.account else {}
    engine = a.engine or c.get('engine') or 'motion'
    if engine == 'modern':
        sys.exit('engine "modern" (2D Modern) runs on the aiTrends 2D Studio plugin, which is not part of this '
                 'repo and cannot run in the daily session. Use vintage or vox (or motion) for %s.' % a.account)
    if engine not in ENGINES:
        sys.exit('engine %r is not a studio engine (%s); use bootstrap.py for the Motion engine'
                 % (engine, ', '.join(ENGINES)))
    d = os.path.join(os.path.abspath(a.root), a.slug)
    if os.path.isdir(d) and os.listdir(d):
        sys.exit('%s already exists and is not empty - pick a new slug' % d)

    # 1. kit + tools (same layout as the plugin's new_project.py)
    shutil.copytree(os.path.join(STUDIO, 'kits', engine), d, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('node_modules', '__pycache__'))
    for sub in ('tools', 'audio', 'work', 'out', 'thumb', 'stills'):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    for f in SHARED:
        shutil.copy2(os.path.join(STUDIO, 'tools', f), os.path.join(d, 'tools', f))
    for f in AUDIO:
        shutil.copy2(os.path.join(STUDIO, 'tools', f), os.path.join(d, 'audio', f))
    # captions in a bundled font that has every accent (Arial Black is not installed on the cloud machine)
    cap = os.path.join(d, 'tools', 'captions.py')
    s = open(cap).read()
    assert 'Style: Cap,Arial Black,' in s, 'captions.py changed - update the font patch'
    open(cap, 'w').write(s.replace('Style: Cap,Arial Black,', 'Style: Cap,Archivo Black,'))
    shutil.copytree(os.path.join(STUDIO, 'fonts'), os.path.join(d, 'fonts'), dirs_exist_ok=True)
    if engine == 'vintage':
        patch_browser(d)
    else:
        shutil.copytree(os.path.join(d, 'src', 'window'), os.path.join(d, 'src', 'story'))
        open(os.path.join(d, 'src', 'Root.tsx'), 'w').write(VOX_ROOT)

    # 2. voice: the account's voice, word times straight from the TTS (no Whisper)
    edge_voice, provider, voice = c.get('edge_voice'), a.provider, a.voice
    if c.get('elevenlabs_voice'):
        voice = voice or c['elevenlabs_voice']
    elif provider == 'auto' and edge_voice:
        provider, voice = 'edge', voice or edge_voice
    tts = os.path.join(d, 'work', 'tts')
    dur, sr, words = voiceover.build(a.story, tts, provider, voice, edge_voice)
    wav = os.path.join(tts, 'narration.wav')
    ff = ['ffmpeg', '-y', '-loglevel', 'error', '-i', wav]
    subprocess.check_call(ff + ['-c:a', 'libmp3lame', '-b:a', '192k', os.path.join(d, 'voice.mp3')])
    subprocess.check_call(ff + ['-ar', '48000', '-ac', '2', os.path.join(d, 'audio', 'voice48.wav')])
    json.dump([{'w': w, 's': s, 'e': e} for w, s, e in words],
              open(os.path.join(d, 'work', 'words.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    shutil.copy(a.story, os.path.join(d, 'script.txt'))

    # 3. the channel's background track (same one the Motion videos use), 48 kHz stereo
    bed = sorted(glob.glob(os.path.join(HERE, 'assets', 'background_music.*')))
    if not bed:
        try:
            import gdrive
            if gdrive.configured():
                got = gdrive.get_asset('background_music.mp3', os.path.join(HERE, 'assets', 'background_music.mp3'))
                bed = [got] if got else []
        except Exception as ex:  # noqa: BLE001
            print('WARNING: could not fetch the background music from Drive:', ex)
    if bed:
        subprocess.check_call(['ffmpeg', '-y', '-loglevel', 'error', '-i', bed[0], '-ar', '48000', '-ac', '2',
                               '-c:a', 'pcm_s16le', os.path.join(d, 'audio', 'music_bed.wav')])
    print('background music:', os.path.basename(bed[0]) if bed else 'none')

    # 4. node packages (browsers are not downloaded: the machine's Chromium is used)
    run(['npm', 'install', '--no-audit', '--no-fund', '--loglevel=error'], d)

    n = int(round(dur * 30))
    json.dump({'engine': engine, 'slug': a.slug, 'title': a.title, 'account': a.account, 'duration': dur,
               'frames': n, 'language': c.get('language')}, open(os.path.join(d, 'studio.json'), 'w'), indent=1)
    os.makedirs(os.path.join(os.path.abspath(a.root), 'output'), exist_ok=True)
    lo, hi = c.get('seconds', [65, 125])
    if not lo <= dur <= hi:
        print('\n*** LENGTH %.1f s IS OUTSIDE %d-%d s: %s the story and run setup again (new slug or delete %s) ***'
              % (dur, lo, hi, 'lengthen' if dur < lo else 'shorten', d))
    print('\n%s [%s]: %.3f s -> N = %d frames at 30 fps\n' % (a.slug, engine, dur, n))
    print(' '.join('%s@%.2f' % (w[0], w[1]) for w in words))
    print('\npauses > 0.35 s:')
    for x, y in zip(words, words[1:]):
        if y[1] - x[2] > 0.35:
            print('  %.2f-%.2f  after "%s"' % (x[2], y[1], x[0]))
    guide = os.path.join(STUDIO, 'skills', engine + '.md')
    if engine == 'vintage':
        print('\nnext: read %s steps 3-6 and daily/studio/README.md; write work/PLAN.md, web/story.js (N = %d), '
              'web/main.js world, web/cast.js, audio/audio.py cues; then studio.py stills / finish' % (guide, n))
    else:
        print('\nnext: read %s steps 3-5 and daily/studio/README.md; rewrite src/story/ (DURATION = %d), '
              'audio/audio.py cues; then studio.py stills / finish' % (guide, -(-n // 30)))


def sheet(d, src, out):
    subprocess.check_call([sys.executable, os.path.join(d, 'tools', 'sheet.py'), src, out])
    print('contact sheet:', out)


def stills(a):
    d = os.path.abspath(a.dir)
    m = meta(d)
    out = os.path.join(d, 'stills', 'check')
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)
    if m['engine'] == 'vintage':
        frames = ','.join(str(min(m['frames'] - 1, int(round(float(s) * 30)))) for s in a.secs)
        run(['node', 'render.mjs', out, frames], d)
    else:
        _, shell = chromium()
        if shell:
            os.environ['REMOTION_BROWSER'] = shell
        run(['node', 'qa.mjs', 'Story', out] + a.secs, d)
    sheet(d, out, os.path.join(d, 'work', 'sheet.jpg'))


def wav_len(p):
    import wave
    with wave.open(p) as w:
        return w.getnframes() / w.getframerate()


def sound(d):
    """audio.py cues -> music.wav + sfx.wav; background track mixed into the music stem; voice-first mix"""
    ad = os.path.join(d, 'audio')
    run([sys.executable, 'audio.py'], ad)
    bed = os.path.join(ad, 'music_bed.wav')
    if os.path.exists(bed):
        sys.path.insert(0, ad)
        import numpy as np
        from dsp import read_wav, write_wav  # noqa: E402
        mus, _ = read_wav(os.path.join(ad, 'music.wav'))
        b, _ = read_wav(bed)
        n = mus.shape[1]
        if b.shape[0] == 1:
            b = np.concatenate([b, b])
        b = np.tile(b, (1, n // b.shape[1] + 1))[:, :n]
        fade = np.minimum(1, np.minimum(np.arange(n), n - np.arange(n)) / (1.5 * 48000))
        b = b * fade
        rms = lambda x: float(np.sqrt((x ** 2).mean())) + 1e-9  # noqa: E731
        cue = rms(mus)
        if cue > 1e-4:   # cues + bed at BED_SHARE of the music level; mix.py then sets the whole stem
            mus = mus * (1 - BED_SHARE) + b * (BED_SHARE * cue / rms(b))
        else:
            mus = b
        os.replace(os.path.join(ad, 'music.wav'), os.path.join(ad, 'music_cues.wav'))
        write_wav(os.path.join(ad, 'music.wav'), mus)
        print('background track mixed into the music stem')
    run([sys.executable, 'mix.py', 'voice48.wav', 'music.wav', 'sfx.wav'], ad)
    return os.path.join(ad, 'mix.wav')


def qc(d, mp4, dur):
    p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', mp4],
                       capture_output=True, text=True)
    got = float(p.stdout.strip() or 0)
    ok = abs(got - dur) < 0.25
    print('QC length: video %.2f s, voice %.2f s -> %s' % (got, dur, 'OK' if ok else 'MISMATCH'))
    r = subprocess.run(['ffmpeg', '-v', 'info', '-i', mp4, '-vf', 'blackdetect=d=0.4:pix_th=0.06,'
                        'freezedetect=n=0.002:d=2.5', '-an', '-f', 'null', '-'], capture_output=True, text=True)
    bad = [l.split(']')[-1].strip() for l in r.stderr.splitlines() if 'black_start' in l or 'freeze_start' in l]
    print('QC black/freeze:', '; '.join(bad) if bad else 'none')
    q = os.path.join(d, 'work', 'final_qc')
    shutil.rmtree(q, ignore_errors=True)
    os.makedirs(q)
    for i in range(12):
        t = (i + 0.5) * got / 12
        subprocess.check_call(['ffmpeg', '-y', '-loglevel', 'error', '-ss', '%.2f' % t, '-i', mp4, '-frames:v', '1',
                               '-q:v', '3', os.path.join(q, 'q%02d.jpg' % i)])
    sheet(d, q, os.path.join(d, 'work', 'final_sheet.jpg'))
    if not ok:
        sys.exit('video length does not match the voice - fix N / DURATION and run finish again')


def finish(a):
    d = os.path.abspath(a.dir)
    m = meta(d)
    root = os.path.dirname(d)
    mp4 = os.path.join(root, 'output', '%s_1080x1920.mp4' % m['slug'])
    if os.path.exists(mp4):
        os.replace(mp4, mp4.replace('.mp4', '_v1.mp4'))   # keep the previous version
    dur = wav_len(os.path.join(d, 'audio', 'voice48.wav'))
    if m['engine'] == 'vintage':
        n = int(re.search(r'export const N = (\d+)', open(os.path.join(d, 'web', 'story.js')).read()).group(1))
        if n < round(dur * 30):
            sys.exit('web/story.js N = %d but the voice needs %d frames' % (n, round(dur * 30)))
        frames = os.path.join(d, 'frames')
        k = max(1, a.workers)
        step = -(-n // k)
        procs = []
        for i in range(k):
            lo, hi = i * step, min(n, (i + 1) * step) - 1
            if lo <= hi:
                e = env()
                e['RESUME'] = '1'
                procs.append(subprocess.Popen(['node', 'render.mjs', 'frames', '%d-%d' % (lo, hi)], cwd=d, env=e))
        if any(p.wait() for p in procs):
            sys.exit('frame render failed (RESUME keeps finished frames: run finish again)')
        mix = sound(d)
        run([sys.executable, 'tools/captions.py', 'work/words.json', 'work/captions.ass'], d)
        run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', 'frames/f%04d.jpg', '-i', mix,
             '-vf', 'subtitles=work/captions.ass:fontsdir=fonts', '-c:v', 'libx264', '-profile:v', 'high',
             '-crf', '18', '-preset', 'slow', '-pix_fmt', 'yuv420p', '-r', '30', '-c:a', 'aac', '-b:a', '192k',
             '-shortest', '-movflags', '+faststart', mp4], d)
    else:
        _, shell = chromium()
        cmd = ['npx', 'remotion', 'render', 'Story', 'work/video_silent.mp4', '--muted', '--crf=16',
               '--concurrency=%d' % max(1, a.workers * 2)]
        if shell:
            cmd.append('--browser-executable=' + shell)
        run(cmd, d)
        mix = sound(d)
        run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'work/video_silent.mp4', '-i', mix, '-map', '0:v',
             '-map', '1:a', '-c:v', 'libx264', '-profile:v', 'high', '-crf', '23', '-preset', 'slow',
             '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', mp4], d)
    print('->', mp4)
    qc(d, mp4, dur)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('setup')
    s.add_argument('root')
    s.add_argument('slug')
    s.add_argument('title')
    s.add_argument('story')
    s.add_argument('--account')
    s.add_argument('--engine', choices=ENGINES + ('modern',))
    s.add_argument('--provider', default='auto', choices=['auto', 'elevenlabs', 'edge'])
    s.add_argument('--voice')
    t = sub.add_parser('stills')
    t.add_argument('dir')
    t.add_argument('secs', nargs='+')
    f = sub.add_parser('finish')
    f.add_argument('dir')
    f.add_argument('--workers', type=int, default=2)
    a = ap.parse_args()
    {'setup': setup, 'stills': stills, 'finish': finish}[a.cmd](a)


if __name__ == '__main__':
    main()
