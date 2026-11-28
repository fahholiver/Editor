"""Free offline voiceover with Kokoro (Apache-2.0). First run downloads the model (~350 MB, or ~120 MB with --small) to ~/.orbit/kokoro.
usage: python3 scripts/voice.py script.txt vo.wav [--voice am_michael] [--speed 0.95] [--list]
Good voices for documentary narration: am_michael (deep, warm, default), am_fenrir, bm_george (British), af_heart, bf_emma.
"""
import sys, os, re, urllib.request, argparse
ap = argparse.ArgumentParser(); ap.add_argument('src', nargs='?'); ap.add_argument('out', nargs='?'); ap.add_argument('--voice', default='am_michael'); ap.add_argument('--speed', type=float, default=0.95)
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
D = os.path.join(os.path.expanduser('~'), '.orbit', 'kokoro'); os.makedirs(D, exist_ok=True)
REL = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/'
model = 'kokoro-v1.0.int8.onnx' if a.small else 'kokoro-v1.0.onnx'
for f in (model, 'voices-v1.0.bin'):
    p = os.path.join(D, f)
    if not os.path.exists(p) or os.path.getsize(p) < 1_000_000:
        print(f'downloading {f} (one time)...', flush=True); urllib.request.urlretrieve(REL + f, p + '.part'); os.replace(p + '.part', p)
k = Kokoro(os.path.join(D, model), os.path.join(D, 'voices-v1.0.bin'))
if a.list: print(' '.join(sorted(k.get_voices()))); sys.exit(0)
text = open(a.src, encoding='utf-8').read().strip()
# speak sentence by sentence with a short natural pause between them
parts = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
sr, chunks = 24000, []
for s in parts:
    audio, sr = k.create(s, voice=a.voice, speed=a.speed, lang='en-us')
    chunks += [audio, np.zeros(int(sr * (0.32 if s.endswith('?') else 0.24)), dtype=audio.dtype)]
sf.write(a.out, np.concatenate(chunks), sr); print('wrote', a.out, f'{sum(len(c) for c in chunks) / sr:.1f}s')
