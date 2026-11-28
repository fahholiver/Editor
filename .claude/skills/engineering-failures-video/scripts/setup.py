#!/usr/bin/env python3
"""Create the project folders and install the pinned HyperFrames + GSAP toolchain.
usage: python setup.py PROJECT [--toolchain-only]   (works on Windows, macOS and Linux)
--toolchain-only installs the shared toolchain without creating episode folders (for a studio folder)."""
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from toolkit import project_dir, toolchain

if len(sys.argv) < 2:
    sys.exit('usage: python setup.py PROJECT')
P = project_dir(sys.argv[1])
P.mkdir(parents=True, exist_ok=True)
if '--toolchain-only' not in sys.argv:
    for folder in ('vo', 'media', 'real', 'stock', 'audio'):
        (P / folder).mkdir(parents=True, exist_ok=True)
if (toolchain(P) / 'node_modules/gsap').is_dir() and (toolchain(P) / 'node_modules/hyperframes').is_dir():
    print(f'Toolchain already installed at {toolchain(P)}. Project ready: {P}')
    sys.exit(0)
npm = shutil.which('npm')
if not npm:
    sys.exit('npm was not found. Install Node.js 22 or later, open a NEW terminal, and run this again.')
subprocess.run([npm, 'install', '--no-audit', '--no-fund', '--prefix', str(P / '.toolchain'),
                'hyperframes@0.8.219', 'gsap@3.15.0'], check=True)
print(f'Project ready: {P}')
print('Next: python scripts/check.py PROJECT')
