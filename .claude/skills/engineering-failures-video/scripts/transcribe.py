#!/usr/bin/env python3
"""Word-level timings for the voiceover.
usage: python transcribe.py <project_dir>
Reads <project>/vo/*.mp3 (sorted by name), joins them into vo/vo.mp3, writes vo/vo.mp3.words.json
and vo/sentences.txt (one sentence per line with its start time: use it to write the shot list)."""
import sys, os, glob, json, subprocess, wave
import numpy as np
P = os.path.abspath(sys.argv[1]); VO = f'{P}/vo'
parts = sorted(f for f in glob.glob(f'{VO}/*.mp3') if os.path.basename(f) != 'vo.mp3')
if not parts and not os.path.isfile(f'{VO}/vo.mp3'):
    sys.exit('Put the voiceover MP3 in <project>/vo/ first.')
if len(parts) == 1:
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', parts[0], '-c', 'copy', f'{VO}/vo.mp3'], check=True)
elif parts:
    inp = sum((['-i', p] for p in parts), [])
    subprocess.run(['ffmpeg', '-v', 'error', '-y'] + inp + ['-filter_complex', ''.join(f'[{i}:a]' for i in range(len(parts))) + f'concat=n={len(parts)}:v=0:a=1', f'{VO}/vo.mp3'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{VO}/vo.mp3', '-ac', '1', '-ar', '16000', f'{VO}/vo.wav'], check=True)
from faster_whisper import WhisperModel
m = WhisperModel(os.environ.get('WHISPER_MODEL', 'base.en'), device='cpu', compute_type='int8', cpu_threads=2)
wf = wave.open(f'{VO}/vo.wav'); a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768
segs, _ = m.transcribe(a, word_timestamps=True, language='en', vad_filter=False)
words = [dict(w=w.word.strip(), s=round(w.start, 2), e=round(w.end, 2)) for s in segs for w in s.words]
if not words:
    sys.exit('No speech found in the voiceover.')
json.dump(words, open(f'{VO}/vo.mp3.words.json', 'w', encoding='utf-8'))
out = []; line = []; st = None
for x in words:
    if st is None: st = x['s']
    line.append(x['w'])
    if x['w'][-1:] in '.?!': out.append(f"{st:7.2f} {' '.join(line)}"); line = []; st = None
if line: out.append(f"{st:7.2f} {' '.join(line)}")
open(f'{VO}/sentences.txt', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print(len(words), 'words; total', words[-1]['e'], 's; see vo/sentences.txt')
