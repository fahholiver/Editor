---
name: finance-documentary-studio
description: Makes faceless finance documentaries (the rise and fall of companies, how brands make money, scams and frauds, billionaires, bubbles and crashes) in a dark market-terminal look: finds topics people are searching for, researches real numbers from annual reports and SEC filings, writes a hook-first script, voices it free, tells it with real free photos, charts that draw themselves and turn red at the crash, big money counters, versus screens, stamps (BANKRUPT) and a ticker tape, adds an original tense score, and renders the MP4. Everything is free. Use for "finance documentary", "rise and fall of", "how X went bankrupt", "how X makes money", "business documentary", "company collapse", or when someone asks for this skill by name.
---

# Finance Documentary Studio

Turns a money story into a finished documentary (2 to 30 minutes), plus a vertical Short from it, that looks like a streaming-service business film:
- **A thriller cold open** (about 30 seconds): letterbox bars, hard cuts with a glitch on every cut, a red pulse on a heartbeat, a ticking clock, a typed date line, a rewind, a fast photo montage; then a hard cut to black and the episode title slams in ("HOW BLOCKBUSTER WENT FROM / $6 BILLION TO ONE STORE"). After the title the film settles into the calm documentary look.
- **Real photos** of the stores, products, buildings and people (free licences, credited on screen), graded cool so they sit in the dark look, with a slow push. Or shown whole on a floating card (an envelope, a sign, a document).
- **Source clippings**: the real article, SEC filing or press release on a tilted card, pushing in while a yellow marker sweeps across the key line as the narrator says it, with a "Source: sec.gov" label. Proof on screen.
- **Numbers that move**: line charts that draw themselves and turn red after the peak, big counters rolling up to "$6,100,000,000", horizontal bars, a VERSUS split screen, a ticker tape, year badges.
- **Type**: Bebas Neue headlines, Oswald captions, IBM Plex Mono numbers; green tags, gold events, red for the fall; BANKRUPT / SOLD / CLOSED stamps.
- **Sound**: a free narrator (Kokoro `am_michael`, deep and warm) or the user's ElevenLabs MP3; an original score (synth pulse, piano, risers into impacts) that never gets a copyright claim.

The reference film is `examples/blockbuster/` (How Blockbuster went from $6 billion to one store, 75-second preview: thriller open, title, a source clipping on the late fees, chapter one; and `short/`, its own 33-second vertical Short). Copy its `episode.py` for every new film. No paid tools, no AI images.

Folder map: `engine/fin.py` the finance look (start here, and its vertical Shorts layout) · `engine/film.py` cues and render · `engine/audio.py` score (mood `money`) · `scripts/voice.py` free narrator · `scripts/timestamps.py` word timings · `scripts/vocheck.py` recording vs script · `scripts/grid.py` coordinates for clipping highlights · `scripts/photos.py` free photos with credits · `references/fin.md` (read before the episode file) · `references/script.md` (read before writing) · `references/legal.md` (read before research) · `references/research.md` (topic finding, data sources) · `references/music.md`.

## Credits rule (always)
Before writing or rendering anything long, **ask how many minutes the video should be.** Always render a **60 to 90 second preview first** and the full film only after the user approves it.

## 0. Setup (do it yourself; the user never types commands)
Tell the user in one line: "Setting the studio up now. The first time takes a few minutes." Then run `bash setup.sh` (macOS/Linux) or `powershell -ExecutionPolicy Bypass -File setup.ps1` (Windows) from this folder. It installs the Python packages and ffmpeg and draws `selftest.png` (a revenue chart that crashes); look at it.
- On macOS/Linux it builds the studio's own Python environment at `~/.finance-studio/venv` (Python 3.10 to 3.13; it finds one, or installs 3.12 with Homebrew), so a very new system Python (3.14) can't break it. **Use `~/.finance-studio/venv/bin/python` in place of `python3` for every command in this file** (episode.py, voice.py, timestamps.py, photos.py). Don't install the packages into the system Python yourself.
- This skill must be installed and run from Claude Code (the Code tab of the desktop app), which can run its engine. If the user is in a normal chat, tell them in one line to open the Code tab, drop the zip there and say "Set up this skill for me."
- If Python is missing, give the user the one link the script prints, wait, run it again.
- Make the project folder yourself: `~/FinanceStudio/<topic>/` with `media/` and `music/`. Copy `examples/blockbuster/episode.py` there and set `ENGINE` to this skill's `engine` folder (or the env var `FDS_ENGINE`).

## 1. Topic
Ask once whether they have a topic. If not, follow `references/research.md`: 10 ideas built on what people are watching now, each with title, the hook moment, demand proof (real numbers you saw), whether real numbers and free photos exist, sensitivity, suggested length. Never invent view counts.

## 2. Research and numbers
Follow `references/legal.md`. Build `sources.md`: every number with its source and year (annual reports, SEC 10-K filings on sec.gov EDGAR, company press releases, reputable news). Note restated figures. Mark estimates as estimates. Chart data goes into a small table in `sources.md` first.

## 3. Script
Follow `references/script.md`: a thriller cold open (the collapse, the rewind, the decision that doomed them), then the title line `[TITLE: HOW BLOCKBUSTER WENT FROM | $6 BILLION TO ONE STORE]`, then chapters with `[CHAPTER: CHAPTER ONE | THE GOLD RUSH]` markers, one number per beat, a callback ending. About 150 words a minute. Run it through the humanizer skill. Show the script and wait for the user's OK. Then write `shots.txt`: per paragraph, the photo, chart, counter or statement, and the tags.

## 4. Voice
Free narrator: `python3 scripts/voice.py script.txt vo.wav --voice am_michael` (the house voice; others: am_fenrir, bm_george for British, af_heart). For a more realistic voice, mention ElevenLabs once. If the free voice can't be installed, or the user prefers ElevenLabs, ask for an MP3 (`vo.mp3`) with a 2-second pause at each chapter marker (`<break time="2s" />`). Then `python3 scripts/timestamps.py vo.wav words.json`.
With the user's own recording, also run `python3 scripts/vocheck.py script.txt words.json`: it lists any line that was skipped, added or changed. The recording is the source of truth: cue on the words actually said, and for a skipped line drop its shot or ask the user to redo that line. Tell the user in one line what it found.

## 5. Photos and music
- Footage (optional, when it exists): `python3 scripts/footage.py search "department store 1950s"`, then `get <id> media/ --start S --dur D --name short_name` and `fin.footage(T('...'), 'media/short_name.mp4')`. It searches Wikimedia Commons videos and the public-domain Prelinger Archives / US government films only. Free footage is for the era, the place and the mood (a 1957 shopping centre, Chicago in 1974, a trading floor); there is almost never free footage of one named company, and little after about 1985, so photos stay the base. Use 2 to 5 clips of 3 to 8 seconds in a film where they fit, credit each one, tag the place and year, and never pass era footage off as the company. If nothing fits, use none and say so.
- Photos: `python3 scripts/photos.py search "Blockbuster store"`, `get "File:..." media/` (free licences only; the credit is saved next to the photo). Download them one at a time, never in parallel; if a file prints SKIPPED (Commons is throttling), take another photo instead of waiting. Prefer stores, products, headquarters, the founders and executives (public figures, real photos only), closing-down sales. Crop out private bystanders' faces (use the push focus) and never show a private person as if they were part of the story.
- Clippings: pick 1 or 2 lines per chapter worth showing as proof (`references/fin.md`, "Source clippings"). Give the user a short numbered list: what to screenshot (the page, and which line must be visible), the file name (`media/clip_10k.png`) and the fallback if they skip it (the exact published text, recreated and labelled as such). Never wait on screenshots: anything not sent uses the fallback.
- Music: the generated score is the default. A real track the user saves into `music/` replaces it (`references/music.md`).

## 6. Episode file
Read `references/fin.md`, then write `episode.py` from the Blockbuster example:
1. A shot for almost every sentence: `fin.photo`, `fin.chart`, `fin.number`, `fin.bars`, `fin.versus`, `fin.statement`, `fin.clipping` (the real source with the line highlighted; 1 or 2 per chapter), `fin.flash` (fast montage for the cold open), or `fin.scene` for anything custom (the example's `rewind`).
   The cold open needs a new shot every 1 to 3 seconds; everything before the `[TITLE: ...]` pause gets the thriller treatment by itself.
2. Never more than two number shots in a row: put a photo between them.
3. Cue everything on the voiceover's words (`T('phrase')`).
4. Overlays in `@fin.screen`: `datestamp` (typed date line) to open the film, a `credit_line` on every photo, `tag` for places and facts, `name_tag` for people, `year_badge` at time jumps, `stamp` for the big turn (BANKRUPT), `ticker` under counters.

## 7. Check, render, deliver
1. `python3 episode.py info`, then `python3 episode.py stills 2 6 12 ...` and look at every sheet: overlapping text, a number that doesn't match the script, a photo without a credit.
2. Preview first. `python3 episode.py all 2` renders, mixes and writes `<episode>_final.mp4` at -14 LUFS (70 seconds take about 4 minutes on a laptop; tell the user before starting).
3. Pull frames from the final MP4 before sending.
4. The Short (after the full film is approved): a separate vertical video, not a cut of the long one. Follow "Shorts" in `references/fin.md`: its own 25 to 35 second script (the most shocking fact in the first second, one idea, a loop ending), its own voiceover (`voice.py --short`: brisk, not rushed), captions and photo credits as the only words on screen (no callouts), and its own episode file in `<project>/short/` with `os.environ['FDS_VERTICAL'] = '1'` before the engine import. Every shot is then laid out for 1080x1920 and big word-by-word captions are on by themselves. Copy `examples/blockbuster/short/blockbuster_short.py`. Run the script through the humanizer and show it before voicing it.

Deliver: the MP4, the Short (`short/<name>_final.mp4`), `sources.md`, `upload.md` (3 titles, a description with chapters, the photo credits, a short sources line, tags, 3 thumbnail ideas: one striking photo, a big number, 2 to 4 words; and for the Short a title, a one-line description that links the full video, and hashtags).

## Bend it (other niches this skill makes)
The look is built for money stories, so it fits any channel where numbers carry the plot:
- **Company collapses**: Blockbuster, Toys"R"Us, Kodak, Nokia, WeWork, Sears.
- **How X makes money**: Costco, McDonald's real estate, Disney, the NFL.
- **Scams and frauds**: Enron, FTX, Theranos, Bernie Madoff (court records and SEC filings are free sources).
- **Billionaires and dynasties**: how a fortune was built and lost.
- **Bubbles and crashes**: tulips, the dot-com crash, 2008, meme stocks.
- **Economics of everyday things**: why a stadium hot dog costs $12, the real cost of owning a Ferrari.
Change the topic, keep the engine. For a lighter channel, change the colours at the top of `engine/fin.py`.
