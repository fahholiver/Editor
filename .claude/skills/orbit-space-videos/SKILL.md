---
name: orbit-space-videos
description: Makes faceless "What Would Kill You First On ___" space explainer videos: researches 10 topic ideas, writes and fact-checks the script, makes a free voiceover (or uses yours), animates it in a dark space style with a tiny astronaut "YOU", adds real NASA images, and renders the MP4. Use when someone wants a space, planet, moon, star or black hole explainer video, or says "space video", "Orbit", or "what would kill you first on".
---

# Orbit: space explainer videos

Orbit turns a space topic into a narrated 2D video. Every picture is drawn in code (planets, the astronaut, gauges, captions), so there is no stock footage to license. Real NASA images can be dropped in as "evidence" shots.

**The format.** The viewer is the tiny astronaut, marked with a red "YOU" arrow. They fall toward or into a place, and the dangers arrive in order, each one bigger than the last: a chapter card, one picture per idea, a number that counts up, a verdict stamp. It ends on a twist. Titles use the "What Would Kill You First On ___" pattern.

Folder map:
- `engine/`: the renderer (`engine.js`) and its page. Fonts are in `assets/fonts` (Anton and Inter, both OFL).
- `scripts/render.mjs`: scene JSON → MP4, or a set of stills for checking.
- `scripts/voice.py`: free offline voiceover (Kokoro, Apache-2.0).
- `scripts/timestamps.py`: word timings from the voiceover (Whisper).
- `scripts/sound.py`: music and sound effects synthesised from the scene, mixed under the voice.
- `scripts/nasa.py`: searches and downloads NASA images with their credit lines.
- `references/elements.md`: every element type and its fields. **Read it before writing scene JSON.**
- `references/style.md`: shot grammar, colours and pacing. **Read it before planning.**
- `references/script.md`: the script formula (cold open that breaks a "rule", a planted callback, question transitions, a comparison for every number, the survival game, the reversal). **Read it before writing any script.**
- `examples/venus.json`: a complete 2-minute film to copy from.

## 0. Setup (do this yourself; the user should not have to)
Before you start, tell the user in one line: "Setting Orbit up now. The first time takes a few minutes while it installs." Then run `bash setup.sh` (macOS/Linux) or `powershell -ExecutionPolicy Bypass -File setup.ps1` (Windows) from this folder. It installs whatever is missing (Node packages, Chromium for Playwright, Python packages, ffmpeg) and renders a 3-second test.
- If Node or Python is missing, tell the user the one link printed by the script, wait, then run it again.
- The free voice is not installed here. It installs itself the first time `voice.py` runs, and only if the user picks it.
- If word timing still fails to install (very new Python versions), install Python 3.12 from python.org for the user's account and rerun setup with it, or tell the user that one link.
- Don't ask the user to create folders or type commands. Make a project folder yourself, for example `~/Orbit/<topic>/`.

## 1. Ten topic ideas
Unless the user already named a topic, research before suggesting anything:
- Search the web for what people currently ask about space. Use recent NASA/ESA news, missions in the news, and "what would happen if" questions people search. Prefer topics with built-in danger and a measurable number (temperature, pressure, gravity, radiation, speed, time survived).
- Give **10 ideas**, numbered. For each one give:
  1. A title using the "What Would Kill You First On ___" pattern (or close to it).
  2. A one-line "you" hook.
  3. The killer facts in order, with their numbers.
  4. The twist ending.
  5. Why people would click now (news hook or evergreen curiosity).
- Never invent trend data. Say "evergreen" when there's no news hook.
- Ask the user to pick one, and to say their target length (default 8–10 minutes for channel videos, 2–3 minutes for a short demo).

## 2. Script
- Follow `references/script.md` beat by beat. Write in the second person ("you"), with short spoken sentences, at about 150 words a minute (a 9-minute video is about 1,350 words).
- Shape: the rule, then the break → correct the misconception → the promise → killers in order, each one worse, every number with an everyday comparison, a question opening each section and a light joke after each scare → "picture it again" → a true story with a date → recent research → the survival game → the reversal → a closing callback to the rule.
- **Fact-check every number** against NASA, ESA, JPL or another primary source, and write the sources into `sources.md` in the project folder (not in the narration). If sources disagree, use the safer round number and say "about". Don't present a hypothesis as fact ("may still be erupting", not "is erupting").
- Before showing the script, run it through the humanizer skill if one is available: no em dashes, no "not just X but Y", no filler.
- Write numbers as words the way they should be spoken ("four hundred and sixty-five degrees") so the voice reads them correctly.
- Show the script and wait for the user's OK.

## 3. Voice
When the script is approved, ask once with two options: **"Use the free voice"** or **"I'll attach my own MP3"**. Don't word it as "Approve, free voice"; the user should see both choices at the same time.
- **Free voice:** `python3 scripts/voice.py script.txt vo.wav --voice am_michael`. The first run downloads the voice model (~350 MB). Other good voices: `bm_george` (British), `am_fenrir`, `af_heart`, `bf_emma`. `--list` shows all of them. If it exits saying the voice can't be installed on this computer, tell the user plainly and ask for their own MP3 instead.
- **Their own voice file** (for example from ElevenLabs, which gives the most natural results): ask them to export the script as MP3 and attach it. Use it as `vo.mp3`.

Then run `python3 scripts/timestamps.py vo.wav words.json`. It prints every word with its start time; every cue in the scene comes from these times.

## 4. NASA images and clips (recommended)
- Choose 3–6 proof moments for real images (`evidence`) or short videos (`clip`): a radar map, a rover photo, launch or mission footage. Use `python3 scripts/nasa.py search "..." --video` for videos.
- Search with `python3 scripts/nasa.py search "venus magellan"` and download with `python3 scripts/nasa.py get <nasa_id> media/`. The credit line is saved next to each file. Never use a result flagged THIRD-PARTY.
- If the network blocks NASA, the script prints links. Give the user the links and the exact file names you need, and ask them to save the images into the project's `media/` folder.
- Rules (NASA media guidelines): always show the credit, never imply NASA made or endorses the video, keep the NASA logo off thumbnails, and skip images of identifiable astronauts in promotional use. Soviet, ESA and JAXA images are **not** NASA's: skip them unless their own licence allows it.

## 5. Scene JSON
Read `references/style.md` and `references/elements.md` first, then write `scene.json`:
- **Hold the stage and build inside it** (see the editing lessons in `references/style.md`): fewer, longer shots (usually 8–15 s), with new elements appearing every 1.5–3 s. Cut only when the place or the idea changes.
- **Every joke gets a gag prop** (`receipt`, `doc`, `loading` + CANCEL stamp, `stick`, `eyes`, `meters`…), and the survival game uses `options`.
- Use `label` for most on-screen text, and save `caption`/`big` for the 3–5 biggest moments.
- One shot per place or idea. A shot's `start` and `end` come from the word times. Element `t0` is **relative to its shot** and should land on the stressed word.
- Each danger opens with a `chapter` card ("KILLER #2 / ACID CLOUDS").
- One new thing on screen every 1.5–3 s: a caption, a number, a pill, a stamp, a gauge or an image.
- The astronaut is "YOU": use the `you` arrow in the first shot. Keep the astronaut in most world shots, and vary its size and spin.
- The last shot ends 0.8 s after the last word. The renderer fades in and out by itself.
- Building the JSON from a small Python script (see `examples/build_venus.py`) is easier than writing it by hand.

## 6. Check, then render
1. Stills first: `node scripts/render.mjs scene.json x.mp4 --stills 2,8,15,... --dir stills`. Use one still in the middle of every shot, then look at them. Check that text is readable, nothing overlaps, numbers are right, and every shot has something happening. Fix anything wrong and check again.
2. Sound (music sits well under the voice; if the user says the music is too loud, add `--music-gain 0.5`): `python3 scripts/sound.py scene.json vo.wav mix.wav --mood dread` (also `tense` or `wonder`). Add `--music track.mp3` to use their own music instead.
3. Render: `node scripts/render.mjs scene.json final.mp4 --audio mix.wav`. A 2-minute video takes a few minutes.
4. Pull 6–8 frames from the finished MP4 and check them before sending.

Deliver the MP4, `sources.md`, and a suggested title, description (with the NASA credits) and 3 thumbnail ideas. The thumbnail should show the tiny "YOU" astronaut against the huge danger, with 2–3 words in Anton font: one white, one red.

## Extending
- New planet look: add an entry to `PRESET` in `engine.js` (base colour, palette, atmosphere colour, style: `bands`, `venus`, `mars`, `earth` or `cratered`).
- New element: add `E.name` (drawn in the world, moves with the camera) or `O.name` (fixed on screen) and document it in `references/elements.md`.
