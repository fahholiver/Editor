#!/usr/bin/env python3
"""Save still frames from one chunk to check layout before rendering.
usage: python stills.py PROJECT/chunks/CHUNK 2,6"""
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from toolkit import need_hyperframes, project_dir, render_env

if len(sys.argv) < 3:
    sys.exit('usage: python stills.py PROJECT/chunks/CHUNK 2,6')
chunk = project_dir(sys.argv[1])
P = chunk.parent.parent
hf = need_hyperframes(P)
subprocess.run([str(hf), 'snapshot', str(chunk), '--at', sys.argv[2], '--no-end', '-o', str(chunk / 'stills')],
               check=True, env=render_env())
