#!/usr/bin/env python3
"""Check the render toolchain and say exactly how to install anything missing.
usage: python check.py PROJECT"""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from toolkit import MAC, WINDOWS, find_browser, hyperframes_bin, project_dir, toolchain

project = project_dir(sys.argv[1]) if len(sys.argv) > 1 else None

if WINDOWS:
    FIX = {
        'Node.js 22+': 'winget install -e --id OpenJS.NodeJS.LTS',
        'FFmpeg with libass': 'winget install -e --id Gyan.FFmpeg',
        'Chrome': 'winget install -e --id Google.Chrome',
        'HyperFrames + GSAP': 'python scripts/setup.py PROJECT',
        'Word timing (faster-whisper)': 'python -m pip install faster-whisper numpy',
    }
elif MAC:
    FIX = {
        'Node.js 22+': 'download the LTS installer from https://nodejs.org',
        'FFmpeg with libass': 'static ffmpeg + ffprobe zips from https://evermeet.cx/ffmpeg/ (versioned links; include libass) into ~/.local/bin, or brew install ffmpeg-full',
        'Chrome': 'download from https://www.google.com/chrome',
        'HyperFrames + GSAP': 'python3 scripts/setup.py PROJECT',
        'Word timing (faster-whisper)': 'python3 -m pip install --user faster-whisper numpy  (if it fails on a new Python such as 3.14, see production.md "Word timing install fallback")',
    }
else:
    FIX = {
        'Node.js 22+': 'install Node.js 22+ from https://nodejs.org or your package manager',
        'FFmpeg with libass': 'sudo apt install ffmpeg',
        'Chrome': 'install Google Chrome or Chromium',
        'HyperFrames + GSAP': 'python3 scripts/setup.py PROJECT',
        'Word timing (faster-whisper)': 'python3 -m pip install faster-whisper numpy',
    }


def node_ok():
    node = shutil.which('node')
    if not node:
        return False
    out = subprocess.run([node, '--version'], capture_output=True, text=True).stdout.strip().lstrip('v')
    try:
        return int(out.split('.')[0]) >= 22
    except ValueError:
        return False


def ffmpeg_ok():
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    if not (ffmpeg and ffprobe):
        return False
    probe = subprocess.run([ffmpeg, '-hide_banner', '-filters'], capture_output=True, text=True, errors='replace')
    return probe.returncode == 0 and any(len(f := line.split()) > 1 and f[1] == 'ass' for line in probe.stdout.splitlines())


checks = {
    'Node.js 22+': node_ok(),
    'FFmpeg with libass': ffmpeg_ok(),
    'Chrome': bool(find_browser()),
    'HyperFrames + GSAP': bool(project and hyperframes_bin(project) and
                               (toolchain(project) / 'node_modules/gsap/dist/gsap.min.js').is_file()),
}
optional = {'Word timing (faster-whisper)': all(importlib.util.find_spec(n) for n in ('faster_whisper', 'numpy'))}

for name, ok in {**checks, **optional}.items():
    print(f'{"OK     " if ok else "MISSING"} {name}' + ('' if ok else f'  ->  {FIX[name]}'))
if not optional['Word timing (faster-whisper)']:
    print('        (word timing is only needed for your own voiceover; the demo does not need it)')
if not all(checks.values()):
    print('\nAfter installing anything, close this terminal and open a NEW one so the new programs are found.')
sys.exit(0 if all(checks.values()) else 1)
