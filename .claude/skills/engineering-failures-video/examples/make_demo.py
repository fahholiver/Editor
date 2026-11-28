#!/usr/bin/env python3
"""Prepare a short synthetic test with moving media, audio, and fixture timings."""
import json
from pathlib import Path
import subprocess
import sys

project = Path(sys.argv[1]).resolve()
for folder in ('vo', 'real', 'media'):
    (project / folder).mkdir(parents=True, exist_ok=True)
if any((project / file).exists() for file in ('shots.json', 'real/demo.mp4', 'vo/vo.mp3')):
    sys.exit('Use a fresh demo project folder.')
subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=30',
                '-t', '5', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', project / 'real/demo.mp4'], check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=220:sample_rate=48000',
                '-t', '16', '-af', 'volume=0.08', project / 'vo/vo.mp3'], check=True)
words = [
    {'w': word, 's': start + i * 0.42, 'e': start + i * 0.42 + 0.33}
    for start, line in [(0.8, 'This is test footage.'), (5, 'Engineering Failures demo.'),
                        (8.8, 'Here is a bridge.'), (12.5, 'A chain of events.')]
    for i, word in enumerate(line.split())
]
(project / 'vo/vo.mp3.words.json').write_text(json.dumps(words, indent=2), encoding='utf-8')
print('Synthetic assets ready. The demo audio is a test tone and captions are sample text.')
