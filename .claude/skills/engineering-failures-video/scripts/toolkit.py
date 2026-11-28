"""Shared helpers for the cross-platform scripts (Windows, macOS, Linux)."""
import os
from pathlib import Path
import shutil
import sys

WINDOWS = os.name == 'nt'
MAC = sys.platform == 'darwin'


def project_dir(arg):
    """Absolute project path from a command-line argument."""
    return Path(arg).expanduser().resolve()


def toolchain(project):
    """The .toolchain folder for a project: in the project itself or in any parent folder
    (a studio folder can hold one shared toolchain for all its episodes)."""
    p = Path(project).resolve()
    for d in (p, *p.parents):
        if (d / '.toolchain' / 'node_modules').is_dir():
            return d / '.toolchain'
    return p / '.toolchain'


def hyperframes_bin(project):
    """The HyperFrames launcher that setup.py installed (project or a parent folder)."""
    bin_dir = toolchain(project) / 'node_modules' / '.bin'
    for name in (('hyperframes.cmd', 'hyperframes.ps1', 'hyperframes') if WINDOWS else ('hyperframes',)):
        if (bin_dir / name).exists():
            return bin_dir / name
    return None


def find_browser():
    """Chrome or Chromium for HyperFrames. HYPERFRAMES_BROWSER_PATH wins when set."""
    env = os.environ.get('HYPERFRAMES_BROWSER_PATH')
    if env and Path(env).is_file():
        return env
    names = ('chrome', 'google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser')
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    candidates = []
    if WINDOWS:
        for base in (os.environ.get('PROGRAMFILES'), os.environ.get('PROGRAMFILES(X86)'), os.environ.get('LOCALAPPDATA')):
            if base:
                candidates.append(Path(base) / 'Google/Chrome/Application/chrome.exe')
        for base in (os.environ.get('PROGRAMFILES(X86)'), os.environ.get('PROGRAMFILES')):
            if base:
                candidates.append(Path(base) / 'Microsoft/Edge/Application/msedge.exe')
    elif MAC:
        candidates += [Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
                       Path('/Applications/Chromium.app/Contents/MacOS/Chromium')]
    for path in candidates:
        if path.is_file():
            return str(path)
    return None


def render_env():
    """Environment for HyperFrames with the browser path filled in when we can find it."""
    env = dict(os.environ)
    browser = find_browser()
    if browser:
        env['HYPERFRAMES_BROWSER_PATH'] = browser
    return env


def need_hyperframes(project):
    hf = hyperframes_bin(project)
    if not hf:
        sys.exit('HyperFrames is not installed in this project yet. Run: python scripts/setup.py PROJECT')
    return hf
