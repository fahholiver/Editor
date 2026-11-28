"""Free offline voiceover with Kokoro (Apache-2.0). First run downloads the model (~350 MB, or ~120 MB with --small) to ~/.hds/kokoro.
usage: python3 scripts/voice.py script.txt vo.wav [--voice am_michael] [--speed 0.95] [--doc-speed 0.9] [--short] [--list]
--short: Shorts pacing (normal speed, short gaps between sentences, the model's own silences trimmed).
Documentary pacing (house style): the cold open (everything before the first chapter marker) is read at --speed
with short gaps; from the first chapter on, the narrator slows to --doc-speed with longer breaths between sentences
and paragraphs. --flat reads everything at --speed.
A line [CHAPTER: PART ONE | THE KINGS] in the script becomes a 2.2 s silence; its time goes to chapters.json.
Good voices for documentary narration: am_michael (deep, warm, default), am_fenrir, bm_george (British), af_heart, bf_emma.
"""
import sys, os, re, urllib.request, argparse
ap = argparse.ArgumentParser(); ap.add_argument('src', nargs='?'); ap.add_argument('out', nargs='?'); ap.add_argument('--voice', default='am_michael'); ap.add_argument('--speed', type=float, default=0.95); ap.add_argument('--doc-speed', type=float, default=0.9); ap.add_argument('--flat', action='store_true'); ap.add_argument('--short', action='store_true', help='Shorts pacing: normal read, short gaps between sentences')
ap.add_argument('--list', action='store_true'); ap.add_argument('--small', action='store_true', help='use the small 90 MB model (faster download, slightly rougher voice)')
a = ap.parse_args()
import numpy as np
try:
    import soundfile as sf
    from kokoro_onnx import Kokoro
except ImportError:
    import subprocess
    print('installing the free voice (one time, a few minutes)...', flush=True)
    req = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'requirements-voice.txt')
    ok = any(subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', *extra, '-r', req]).returncode == 0 for extra in ([], ['--user'], ['--break-system-packages']))
    try:
        import soundfile as sf
        from kokoro_onnx import Kokoro
    except ImportError:
        print(f'\nThe free voice can\'t be installed on this computer (Python {sys.version_info.major}.{sys.version_info.minor}: its onnxruntime package has no build for it yet).'
              '\nUse your own voice file instead: paste the script into ElevenLabs (or any voice tool), export an MP3 and attach it in the chat.'
              '\nOr install Python 3.12 from https://www.python.org/downloads/ and run this again.')
        sys.exit(3)
D = os.path.join(os.path.expanduser('~'), '.hds', 'kokoro'); os.makedirs(D, exist_ok=True)
REL = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/'
model = 'kokoro-v1.0.int8.onnx' if a.small else 'kokoro-v1.0.onnx'
for f in (model, 'voices-v1.0.bin'):
    p = os.path.join(D, f)
    if not os.path.exists(p) or os.path.getsize(p) < 1_000_000:
        print(f'downloading {f} (one time)...', flush=True); urllib.request.urlretrieve(REL + f, p + '.part'); os.replace(p + '.part', p)
k = Kokoro(os.path.join(D, model), os.path.join(D, 'voices-v1.0.bin'))
if a.list: print(' '.join(sorted(k.get_voices()))); sys.exit(0)
text = open(a.src, encoding='utf-8').read().strip()
# A line like [CHAPTER: PART ONE | THE PLAN] is not spoken: it becomes a 2.2 s silence for the chapter card.
# A line like [TITLE: HOW BLOCKBUSTER WENT FROM | $6 BILLION TO ONE STORE] ends a thriller cold open: a 3.4 s silence for the title card.
CH = re.compile(r'^\s*\[(CHAPTER|TITLE):\s*(.+?)\s*\|\s*(.+?)\s*\]\s*$', re.M)
blocks, pos = [], 0
for m in CH.finditer(text):
    blocks.append(('text', text[pos:m.start()])); blocks.append(('chapter', (m.group(2) if m.group(1) == 'CHAPTER' else 'TITLE:' + m.group(2), m.group(3)))); pos = m.end()
blocks.append(('text', text[pos:]))
sr, chunks, chapters, n = 24000, [], [], 0
doc = False   # becomes True after the first chapter marker
for kind, val in blocks:
    if kind == 'chapter':
        title = val[0].startswith('TITLE:'); d = 3.4 if title else 2.2
        if not title: doc = not a.flat
        chapters.append([round(n / sr, 2), val[0], val[1], d]); z = np.zeros(int(sr * d), dtype=np.float32); chunks.append(z); n += len(z); continue
    speed = 1.0 if a.short else a.doc_speed if doc else a.speed
    gap, qgap, pgap = (0.18, 0.22, 0.32) if a.short else (0.42, 0.5, 0.85) if doc else (0.3, 0.36, 0.62)
    paras = [p.strip() for p in re.split(r'\n\s*\n', val.strip()) if p.strip()]
    for pi, para in enumerate(paras):
        sents = [x.strip() for x in re.split(r'(?<=[.!?])\s+', para) if x.strip()]
        for si, s in enumerate(sents):
            audio, sr = k.create(s, voice=a.voice, speed=speed, lang='en-us')
            if a.short:      # trim the model's own lead-in and tail silence so lines run into each other
                loud = np.where(np.abs(audio) > 0.012)[0]
                if len(loud): audio = audio[max(0, loud[0] - int(.03 * sr)):loud[-1] + int(.06 * sr)]
            last = si == len(sents) - 1 and pi < len(paras) - 1
            z = np.zeros(int(sr * (pgap if last else qgap if s.endswith('?') else gap)), dtype=audio.dtype); chunks += [audio, z]; n += len(audio) + len(z)
sf.write(a.out, np.concatenate(chunks), sr); print('wrote', a.out, f'{n / sr:.1f}s')
import json
json.dump(chapters, open(os.path.join(os.path.dirname(os.path.abspath(a.out)), 'chapters.json'), 'w'))
for c in chapters: print(f'chapter card at {c[0]:.2f}s: {c[1]} / {c[2]}')
