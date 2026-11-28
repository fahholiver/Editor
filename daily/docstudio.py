#!/usr/bin/env python3
"""The owner's documentary skills as studio engines of the daily run (added 2026-11-28).

    engine    skill (.claude/skills/...)        format (forced by plan.py FORMAT_LOOK)   look
    finance   finance-documentary-studio        finance_doc                              dark market terminal, real photos,
                                                                                         self-drawing charts, counters, stamps
    orbit     orbit-space-videos                space_killer                             "What would kill you first on ___",
                                                                                         tiny astronaut YOU, drawn planets
    engfail   engineering-failures-video        engineering_failure                      navy grid, evidence boxes, handwritten
                                                                                         notes + arrows, archive footage

The skills were made for long YouTube films with the user's own MP3. In the daily run:
  * voice = ElevenLabs (account voice, word times straight from the TTS - no Whisper), made by studio.py setup;
    this module writes it in each skill's own files (vo.wav + words.json / vo/vo.mp3 + vo/vo.mp3.words.json);
  * picture = the skill's own engine, vertical 1080x1920 (finance: FDS_VERTICAL Shorts layout; orbit: scene
    width/height 1080x1920; engfail: its 1920x1080 film, captions burned in, inside a 9:16 frame over a blurred copy + a red title band);
  * sound = the skill's own score/mix (built to sit under the voice), loudness -14 LUFS;
  * no user questions: the daily run decides topic, length (the account's seconds) and voice itself.
studio.py setup/stills/finish call setup()/stills()/finish() below.
"""
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(os.path.dirname(HERE), '.claude', 'skills')
SKILL = {'finance': os.path.join(SKILLS, 'finance-documentary-studio'),
         'orbit': os.path.join(SKILLS, 'orbit-space-videos'),
         'engfail': os.path.join(SKILLS, 'engineering-failures-video')}
DOC_ENGINES = tuple(SKILL)
NODE_PATH = '/opt/node22/lib/node_modules'   # the machine's Playwright (no browser download)

FINANCE_STARTER = '''"""Daily vertical finance documentary short (1080x1920). Engine: .claude/skills/finance-documentary-studio
Read its references/fin.md ("Shorts") first. Captions are on by themselves in vertical; photos via
  python3 %(skill)s/scripts/photos.py search "..."   /   get "File:..." media/
Cue every shot on the voice: T(<word>) (word times from ElevenLabs, words.json). Then
  python3 episode.py info / stills 1 4 9 ... / all 2   (studio.py stills|finish do this for you)"""
import sys, os
os.environ['FDS_VERTICAL'] = '1'                       # must come before the engine import
sys.path.insert(0, os.environ.get('FDS_ENGINE', %(engine)r))
from fin import *

film = Film(__file__, vo='vo.wav', words='words.json', mood='money')
T = film.cue
D = os.path.dirname(os.path.abspath(__file__))
def cr(f):
    p = os.path.join(D, 'media', f + '.credit.txt')
    return ('Foto: ' + open(p, encoding='utf-8').read().splitlines()[0]) if os.path.exists(p) else ''

fin = Fin(film, xfade=.2, thriller=False)
film.music = {'hits': []}

# --- shots: a new picture every 2-3 s (photos, one clean chart, a counter) - see the Blockbuster short ---
# fin.photo(0, 'media/x.jpg', frm=(.5, .5, 1.0), to=(.5, .45, 1.15))
# fin.chart(T('...') - .2, [(2000, 1.0), ...], '', fmt=lambda v: f'{v:.1f} Mrd. $', crash_from=2004, dur=1.6)

@fin.screen
def words(c, t):
    pass   # credit_line(c, t, t0, t1, cr('x.jpg')) for every photo

fin.render()
film.main()
'''

ORBIT_STARTER = '''"""Daily vertical space short (1080x1920). Engine: .claude/skills/orbit-space-videos
Read references/style.md, elements.md, script.md and examples/build_venus.py first. Overlay x/y are fractions of the
screen; world x/y are pixels of the 1080x1920 frame. Times come from words.json (ElevenLabs word times):
w('word', after=sec) -> start time. Run: python3 build_scene.py  (writes scene.json), then studio.py stills/finish."""
import json, os, re
D = os.path.dirname(os.path.abspath(__file__))
WORDS = json.load(open(os.path.join(D, 'words.json'), encoding='utf-8'))
END = WORDS[-1]['e'] + 0.8
def norm(s): return re.sub(r'[^\\w]', '', s.lower())
def w(word, after=0.0):
    for x in WORDS:
        if x['s'] >= after - 0.05 and norm(x['w']) == norm(word): return round(x['s'], 2)
    raise SystemExit('word not found: %r after %s' % (word, after))

shots = []
def shot(start, end, els, cam=None, bg=None):
    s = {'start': round(start, 2), 'end': round(end, 2), 'els': els}
    if cam: s['cam'] = cam
    if bg: s['bg'] = bg
    shots.append(s)

# shot(0, w('...'), [{'type': 'planet', 'kind': 'venus', 'x': 540, 'y': 900, 'r': 420}, ...])

json.dump({'width': 1080, 'height': 1920, 'fps': 30, 'vk': 0.9, 'shots': shots},
          open(os.path.join(D, 'scene.json'), 'w'), ensure_ascii=False, indent=1)
print('scene.json:', len(shots), 'shots, end', shots[-1]['end'] if shots else 0, '(voice ends %.2f)' % END)
'''

ENGFAIL_NOTE = '''# Daily vertical engineering-failure short. Engine: .claude/skills/engineering-failures-video
# Read reference/production.md + scenes.md and examples/bridge_shots.py first, then write shots.py here
# (from vidlib import *; init(PROJECT); sh(...); finish(...)) with ABSOLUTE voice seconds from vo/vo.mp3.words.json.
# Assets: scripts/commons.py "<case>" --video/--image --add PROJECT, then scripts/fetch.py PROJECT
# (archive.org / agency sites may be blocked in the cloud: Commons works). The film is 1920x1080; studio.py finish
# puts it in a 9:16 frame (blurred copy behind, red title band on top = TITLE.txt).
'''


def _run(cmd, cwd, env=None):
    print('$', ' '.join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=cwd, env=env)


def _env():
    e = dict(os.environ)
    e['FDS_ENGINE'] = os.path.join(SKILL['finance'], 'engine')
    e['PYTHONPATH'] = os.path.join(SKILL['engfail'], 'scripts') + ((os.pathsep + e['PYTHONPATH']) if e.get('PYTHONPATH') else '')
    e['NODE_PATH'] = NODE_PATH + ((os.pathsep + e['NODE_PATH']) if e.get('NODE_PATH') else '')
    full = sorted(glob.glob('/opt/pw-browsers/chromium-*/chrome-linux*/chrome'))
    if full:
        e.setdefault('HYPERFRAMES_BROWSER_PATH', full[-1])
        e.setdefault('CHROME_PATH', full[-1])
    return e


def setup(d, engine, c, wav, words, story):
    """d = the project dir (already has voice.mp3, audio/voice48.wav, work/words.json, script.txt)"""
    os.makedirs(os.path.join(d, 'media'), exist_ok=True)
    ff = ['ffmpeg', '-y', '-loglevel', 'error', '-i', wav]
    if engine == 'finance':
        subprocess.check_call(ff + ['-ar', '48000', '-ac', '1', os.path.join(d, 'vo.wav')])
        json.dump([[round(s, 3), round(e, 3), w] for w, s, e in words],
                  open(os.path.join(d, 'words.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        open(os.path.join(d, 'episode.py'), 'w').write(
            FINANCE_STARTER % {'skill': SKILL['finance'], 'engine': os.path.join(SKILL['finance'], 'engine')})
        os.makedirs(os.path.join(d, 'music'), exist_ok=True)
        nxt = 'write episode.py (finance Shorts layout, see %s/references/fin.md + examples/blockbuster/short/)' % SKILL['finance']
    elif engine == 'orbit':
        subprocess.check_call(ff + ['-ar', '48000', '-ac', '1', os.path.join(d, 'vo.wav')])
        json.dump([{'w': w, 's': round(s, 3), 'e': round(e, 3)} for w, s, e in words],
                  open(os.path.join(d, 'words.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        open(os.path.join(d, 'build_scene.py'), 'w').write(ORBIT_STARTER)
        nxt = 'write build_scene.py (see %s/examples/build_venus.py), python3 build_scene.py' % SKILL['orbit']
    else:
        for sub in ('vo', 'real', 'stock', 'audio'):
            os.makedirs(os.path.join(d, sub), exist_ok=True)
        subprocess.check_call(ff + ['-c:a', 'libmp3lame', '-b:a', '192k', os.path.join(d, 'vo', 'vo.mp3')])
        json.dump([{'w': w, 's': round(s, 3), 'e': round(e, 3)} for w, s, e in words],
                  open(os.path.join(d, 'vo', 'vo.mp3.words.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        open(os.path.join(d, 'vo', 'sentences.txt'), 'w', encoding='utf-8').write(open(story, encoding='utf-8').read())
        open(os.path.join(d, 'SHOTS_README.txt'), 'w').write(ENGFAIL_NOTE)
        root = os.path.dirname(d)   # one shared HyperFrames + GSAP toolchain for all episodes (vidlib finds it in a parent)
        if not os.path.isdir(os.path.join(root, '.toolchain', 'node_modules', 'hyperframes')):
            _run([sys.executable, os.path.join(SKILL['engfail'], 'scripts', 'setup.py'), root, '--toolchain-only'], root)
        nxt = 'write shots.py (see %s/examples/bridge_shots.py), fetch assets, then studio.py stills/finish' % SKILL['engfail']
    return nxt


def _orbit_scene(d):
    if os.path.exists(os.path.join(d, 'build_scene.py')):
        _run([sys.executable, 'build_scene.py'], d, _env())
    return os.path.join(d, 'scene.json')


def stills(d, engine, secs, out):
    """frames at secs -> out/ (jpg); the caller tiles them into work/sheet.jpg"""
    e = _env()
    if engine == 'finance':
        _run([sys.executable, 'episode.py', 'stills'] + [str(s) for s in secs], d, e)
        got = sorted(glob.glob(os.path.join(d, 'build', 'stills', '*.*')) + glob.glob(os.path.join(d, 'stills', '*.*')),
                     key=os.path.getmtime)[-len(secs):]
        for i, p in enumerate(got):
            shutil.copy(p, os.path.join(out, 's%02d%s' % (i, os.path.splitext(p)[1])))
    elif engine == 'orbit':
        _run(['node', os.path.join(SKILL['orbit'], 'scripts', 'render.mjs'), _orbit_scene(d), 'x.mp4', '--stills',
              ','.join(str(s) for s in secs), '--dir', out], d, e)
    else:
        sk = os.path.join(SKILL['engfail'], 'scripts')
        _run([sys.executable, 'shots.py', d], d, e)
        names = json.load(open(os.path.join(d, 'shots.json')))['names']
        cuts = json.load(open(os.path.join(d, 'shots.json'))).get('cuts', [])
        for s in secs:   # the chunk that holds second s
            k = max([i for i, t in enumerate([0] + cuts[:len(names) - 1]) if t <= float(s)] or [0])
            loc = float(s) - ([0] + cuts)[k]
            _run([sys.executable, os.path.join(sk, 'stills.py'), os.path.join(d, 'chunks', names[k]), '%.2f' % loc], d, e)
            for p in glob.glob(os.path.join(d, 'chunks', names[k], 'stills', '*.png')):
                shutil.move(p, os.path.join(out, 't%06.2f_%s' % (float(s), os.path.basename(p))))


VFRAME = ('[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2,eq=brightness=-0.25[bg];'
          '[0:v]scale=1080:-2[fg];[bg][fg]overlay=0:(H-h)/2-120[v0]')


def finish(d, engine, title, workers=2):
    """renders with the skill's engine -> work/doc_final.mp4 (1080x1920, voice + the skill's score, -14 LUFS)"""
    e = _env()
    out = os.path.join(d, 'work', 'doc_final.mp4')
    if engine == 'finance':
        _run([sys.executable, 'episode.py', 'all', str(max(1, workers))], d, e)
        src = sorted(glob.glob(os.path.join(d, '*_final.mp4')), key=os.path.getmtime)[-1]
        shutil.copy(src, out)
    elif engine == 'orbit':
        scene = _orbit_scene(d)
        sk = os.path.join(SKILL['orbit'], 'scripts')
        mood = json.load(open(scene)).get('mood', 'dread')
        _run([sys.executable, os.path.join(sk, 'sound.py'), scene, 'vo.wav', 'work/mix.wav', '--mood', mood], d, e)
        _run(['node', os.path.join(sk, 'render.mjs'), scene, out, '--audio', 'work/mix.wav'], d, e)
    else:
        sk = os.path.join(SKILL['engfail'], 'scripts')
        e['HF_WORKERS'] = str(max(1, workers))
        _run([sys.executable, 'shots.py', d], d, e)
        _run([sys.executable, os.path.join(sk, 'render.py'), d], d, e)
        _run([sys.executable, os.path.join(sk, 'assemble.py'), d], d, e)
        film = sorted(glob.glob(os.path.join(d, '*.mp4')) + glob.glob(os.path.join(d, 'out', 'final*.mp4')),
                      key=os.path.getmtime)[-1]
        t = os.path.join(d, 'work', 'title.txt')
        open(t, 'w', encoding='utf-8').write((open(os.path.join(d, 'TITLE.txt'), encoding='utf-8').read().strip()
                                              if os.path.exists(os.path.join(d, 'TITLE.txt')) else title).upper())
        font = glob.glob(os.path.join(SKILL['finance'], 'assets', 'fonts', 'BebasNeue-Regular.ttf'))[0]
        vf = VFRAME + (";[v0]drawtext=fontfile=%s:textfile=%s:fontsize=92:fontcolor=white:x=(w-tw)/2:y=330:"
                       "box=1:boxcolor=0xC8102E@0.95:boxborderw=24[v]" % (font, t))
        _run(['ffmpeg', '-y', '-loglevel', 'error', '-i', film, '-filter_complex', vf, '-map', '[v]', '-map', '0:a',
              '-c:v', 'libx264', '-crf', '19', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-r', '30',
              '-af', 'loudnorm=I=-14:TP=-1.5', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', out], d)
    return out
