"""Word timings for a voiceover: python3 scripts/timestamps.py vo.wav words.json
Writes [[start, end, word], ...] and prints the text with times so shots can be cut on stressed words."""
import sys, os, json, shutil, subprocess, numpy as np
_B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bin')
FF = shutil.which('ffmpeg') or next((os.path.join(_B, n) for n in ('ffmpeg', 'ffmpeg.exe') if os.path.exists(os.path.join(_B, n))), 'ffmpeg')
from faster_whisper import WhisperModel
src, out = sys.argv[1], sys.argv[2]
pcm = subprocess.run([FF, '-loglevel', 'error', '-i', src, '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
x = np.frombuffer(pcm, np.float32)
m = WhisperModel('small.en', device='cpu', compute_type='int8')
segs, _ = m.transcribe(x, word_timestamps=True, vad_filter=False)
w = [[round(t.start, 2), round(t.end, 2), t.word.strip()] for s in segs for t in s.words]
json.dump(w, open(out, 'w')); print(f'duration {len(x) / 16000:.2f}s, {len(w)} words')
line = ''
for a, b, t in w:
    line += f'{a:.2f}:{t} '
    if t.endswith(('.', '?', '!')): print(line); line = ''
if line: print(line)
