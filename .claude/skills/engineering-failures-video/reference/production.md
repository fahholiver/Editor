# From narration to MP4

## Local setup

The scripts are plain Python, so the same commands work in Windows PowerShell, macOS Terminal and Linux. WSL is not needed. Use a project folder separate from the skill folder.

Requirements: Node.js 22 or later, Python 3.10 or later, Chrome (Edge or Chromium also work), and FFmpeg with FFprobe and the libass `ass` filter.

- **Windows:** `winget install -e --id OpenJS.NodeJS.LTS`, `winget install -e --id Python.Python.3.12`, `winget install -e --id Gyan.FFmpeg`, `winget install -e --id Google.Chrome`. Open a new terminal afterwards so the new programs are on PATH. Use `python`, not `python3` (on Windows `python3` can open the Microsoft Store instead).
- **macOS:** Node.js and Chrome from their websites, Python from python.org, and FFmpeg with libass (`brew install ffmpeg`, or `ffmpeg-full` if libass is missing). Use `python3`.
- **Linux:** your package manager. Use `python3`.

Run these from the skill folder (`PY` is `python` on Windows, `python3` elsewhere):

```
PY scripts/setup.py PROJECT
PY scripts/check.py PROJECT
```

`setup.py` installs the pinned HyperFrames and GSAP packages into the project and creates `vo/`, `media/`, `real/`, `stock/` and `audio/`. `check.py` prints OK or MISSING for each tool, with the exact install command for the current system. Use `media/` for stills and original SVG illustrations, `real/` for archive clips and `stock/` for named MP4s. A project can have no music or sound effects. Set `HYPERFRAMES_BROWSER_PATH` only if Chrome is installed somewhere unusual.

When a viewer asks Claude to set things up, run `check.py`, install whatever it reports as missing with the command it prints (ask before installing), tell the user to reopen the terminal if PATH changed, and run `check.py` again until everything except word timing is OK.

### Word timing install fallback

`faster-whisper` sometimes fails to install on the newest Python (for example 3.14 on Intel Macs) because `onnxruntime` or `av` have no prebuilt package yet. The skill runs Whisper with `vad_filter=False`, so `onnxruntime` is not needed. Install the rest from binaries, then faster-whisper without its dependency check:

```
PY -m pip install --user --only-binary :all: ctranslate2 tokenizers huggingface_hub av numpy tqdm
PY -m pip install --user --no-deps faster-whisper
```

If `av` still has no binary, install Python 3.12 or 3.13 alongside and use it for `transcribe.py`.

### FFmpeg on a Mac without Homebrew

Download the static `ffmpeg` and `ffprobe` zips from https://evermeet.cx/ffmpeg/ (use the versioned links; the "latest" redirect sometimes returns 410). They include libass. Unzip both into `~/.local/bin`, run `xattr -d com.apple.quarantine` on them if macOS blocks them, and make sure `~/.local/bin` comes first on PATH. An existing Homebrew FFmpeg can stay as it is.

## Optional 16-second setup test

Use a fresh demo project. The demo uses a generated test pattern and a tone with sample captions. No case footage or Whisper model is needed.

```
PY examples/make_demo.py PROJECT
PY examples/bridge_shots.py PROJECT
PY scripts/stills.py PROJECT/chunks/mechanism 2,6
PY scripts/render.py PROJECT
PY scripts/assemble.py PROJECT
```

Open `out/final.mp4` to confirm the video box, title, two diagram styles, and captions. Use a separate project for the real case.

## Real episode

1. Put your recording in `vo/vo.mp3` or put the segments in `vo/01.mp3`, `vo/02.mp3`, and so on. Supply the voiceover yourself or use a voice provider you have permission to use. For automatic English word timing, install with `PY -m pip install faster-whisper numpy` (a virtual environment is fine too). Run `PY scripts/transcribe.py PROJECT`. The first run downloads a small Whisper model. It writes `vo/vo.mp3.words.json` and `vo/sentences.txt`. Alternatively supply timings as JSON objects `{"w":"word","s":0.3,"e":0.6}` in an array. Review names and technical terms.
2. Write `PROJECT/shots.py` using the bridge demo as a structural example. Replace its import-path line with a reference to the installed skill's `scripts` folder, or set `PYTHONPATH` to that folder when running it. Set `end` to the measured VO duration, leaving a small tail if needed. Use 30 fps and choose cuts on frame boundaries, ideally between shots. Use roughly 20–60 second chunks and give each chunk a unique name. Change the visual or reveal something meaningful every 3–6 seconds. Keep title and note text clear of the lower caption strip. Pass `music=[]` and `sfx=[]` when they're unused. Build with `PY PROJECT/shots.py PROJECT`.
3. Take a few stills with `PY scripts/stills.py PROJECT/chunks/hook 2,5` using the actual chunk name. The graphics stage shows magenta where archive footage will be composited. Check text wrapping, overlays, and legibility before rendering.
4. Render and assemble the opening with `PY scripts/render.py PROJECT hook`, then `PY scripts/assemble.py PROJECT --preview hook`. Use the actual first chunk name. Watch the preview. After adjustments, rebuild the affected project and repeat the preview. Then run `PY scripts/render.py PROJECT` and `PY scripts/assemble.py PROJECT`.
5. Check `out/final.mp4` in a player. Verify footage placement and source captions, check chapter seams and word highlights, and scan for any visible magenta. Check resolution, duration, and streams with `ffprobe -v error -show_streams -show_format PROJECT/out/final.mp4`. Check loudness with `ffmpeg -hide_banner -i PROJECT/out/final.mp4 -af ebur128 -f null -`; the mix targets −14 LUFS with a true-peak target of −1.5 dB. Include `CREDITS.md` with the handoff.

If local software or source downloads are unavailable, complete the research, script, shot plan, and the missing-assets list, then move the project to a supported local runtime. If Chrome or FFmpeg fails, report the exact blocker. For an interrupted render, use the same project and rerun the render command to reuse completed graphics. Rebuild the shot list after edits so stale chunks are rendered again.
