#!/usr/bin/env bash
# One-step setup for macOS / Linux. Claude runs this; the user should not have to.
# Everything goes into the studio's own Python environment (~/.finance-studio/venv), so it never touches the system
# Python and keeps working when the computer has a very new Python (3.14) that some packages don't support yet.
set -e
cd "$(dirname "$0")"
say() { printf '\n▸ %s\n' "$1"; }
HOME_DIR="$HOME/.finance-studio"; VENV="$HOME_DIR/venv"; mkdir -p "$HOME_DIR"

ok_py() { "$1" -c 'import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,13) else 1)' 2>/dev/null; }
BASE=""
if [ -x "$VENV/bin/python" ] && ok_py "$VENV/bin/python"; then BASE="$VENV/bin/python"
else
  for c in python3.12 python3.13 python3.11 python3.10 python3 /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12 /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12; do
    if command -v "$c" >/dev/null 2>&1 && ok_py "$c"; then BASE="$(command -v "$c")"; break; fi
  done
  if [ -z "$BASE" ] && command -v brew >/dev/null 2>&1; then
    say "Installing Python 3.12 with Homebrew (one time)"; brew install python@3.12 >/dev/null && BASE="$(brew --prefix python@3.12)/bin/python3.12"
  fi
  if [ -z "$BASE" ]; then
    echo "The studio needs Python 3.10 to 3.13. Install Python 3.12 from https://www.python.org/downloads/ (the macOS installer), then run this again."; exit 2
  fi
  say "Making the studio's own Python environment ($("$BASE" --version))"
  "$BASE" -m venv "$VENV"
fi
PY="$VENV/bin/python"
echo "$PY" > "$HOME_DIR/python.txt"

say "Python packages (drawing, sound, word timing). The first time takes a few minutes."
"$PY" -m pip install --quiet --disable-pip-version-check --upgrade pip >/dev/null 2>&1 || true
pipi() { "$PY" -m pip install --quiet --disable-pip-version-check "$@"; }
pipi skia-python numpy scipy soundfile pillow certifi imageio-ffmpeg || { echo "Could not install the drawing packages; see SKILL.md, section 0."; exit 1; }
if ! pipi "faster-whisper>=1.0"; then
  echo "  installing faster-whisper without onnxruntime"
  pipi ctranslate2 tokenizers huggingface_hub av tqdm && pipi --no-deps "faster-whisper>=1.0" || echo "  (word timing could not be installed; see SKILL.md, section 0)"
fi
echo "  (the free voice is installed later, only if you choose it)"
say "Depth layers for paintings (optional; films still render without them)"
pipi opencv-python-headless rembg onnxruntime 2>/dev/null || echo "  (depth layers not installed: photos will use a flat push)"

say "ffmpeg"
mkdir -p bin
if command -v ffmpeg >/dev/null 2>&1; then echo "using system ffmpeg"
else ln -sf "$("$PY" -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())')" bin/ffmpeg; echo "ffmpeg installed into ./bin"; fi

say "Test frame"
"$PY" engine/selftest.py && echo "✓ Setup complete. Use this Python for every studio command: $PY"
