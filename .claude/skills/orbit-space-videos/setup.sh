#!/bin/bash
# One-step setup for macOS / Linux. Safe to run again. Installs only what is missing, then makes a 3-second test video.
set -e
cd "$(dirname "$0")"
say() { printf '\n▸ %s\n' "$1"; }
if ! command -v node >/dev/null 2>&1; then echo "Node.js 18+ is needed. Install it from https://nodejs.org (the LTS installer), then run this again."; exit 1; fi
if ! command -v python3 >/dev/null 2>&1; then echo "Python 3.10+ is needed. Install it from https://www.python.org/downloads/, then run this again."; exit 1; fi
say "Node packages (Playwright + its Chromium)"
npm install --no-audit --no-fund --silent
npx --yes playwright install chromium >/dev/null 2>&1 || echo "(couldn't download Playwright's Chromium; Orbit will use Google Chrome if it's installed)"
say "Python packages (word timing, sound). This can take a few minutes the first time."
pipi() { python3 -m pip install --quiet --disable-pip-version-check "$@" 2>/dev/null || python3 -m pip install --quiet --disable-pip-version-check --user "$@" 2>/dev/null || python3 -m pip install --quiet --disable-pip-version-check --break-system-packages "$@" 2>/dev/null; }
for p in soundfile numpy scipy imageio-ffmpeg certifi; do pipi "$p" || echo "  (could not install $p)"; done
# faster-whisper pulls in onnxruntime, which has no build yet for some new Pythons (for example 3.14 on Intel Macs).
# Orbit doesn't need onnxruntime for word timing, so fall back to installing faster-whisper without it.
if ! pipi "faster-whisper>=1.0"; then
  echo "  faster-whisper's full install failed (probably onnxruntime); installing it without onnxruntime"
  pipi ctranslate2 tokenizers huggingface_hub av tqdm && pipi --no-deps "faster-whisper>=1.0" || echo "  (word timing could not be installed; see SKILL.md, section 0)"
fi
echo "  (the free voice is installed later, only if you choose it)"
say "ffmpeg"
mkdir -p bin
if command -v ffmpeg >/dev/null 2>&1 && ffmpeg -version | head -1 | grep -qE 'version (n?[5-9]|[1-9][0-9])'; then echo "using system ffmpeg"
else ln -sf "$(python3 -c 'import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())')" bin/ffmpeg; echo "ffmpeg installed into ./bin"; fi
say "Test render"
node scripts/render.mjs examples/test.json examples/test.mp4 >/dev/null && echo "✓ Setup complete: examples/test.mp4"
