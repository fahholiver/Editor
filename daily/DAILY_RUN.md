# Daily run — what the scheduled Claude session does

A **fresh** Claude Code session starts every morning. It has no repositories attached and cannot write to
GitHub: everything it needs comes from the public `fahholiver/Editor` repo (this pipeline) and from Google
Drive (`TikTok Daily/`: engine, music, story log, insights). Its output goes to Buffer and Drive only.

Every day: **one new, different 2D-animated video per account** (`daily/accounts.json`), each with its own
language/country, format, voice, length (`seconds`, 61–80 s from 2026-11-11) and posting time (≥ 1 h apart). The scheduled task's own
prompt (written by the owner) says what the session may do; this file only describes the steps. If one
account's video fails and cannot be fixed, skip it, finish the others, and report it (never post a broken video).

## 0. Setup (≈5 min)
```bash
cd /home/user && git clone -q --depth 1 -b claude/buffer-tiktok-video-generation-lrudue https://github.com/fahholiver/Editor Editor
cd /home/user/Editor && pip install -q -r daily/requirements.txt
python3 daily/engine.py fetch /home/user/motion               # Motion animation engine from Drive
python3 daily/gdrive.py get-state stories.jsonl /tmp/stories.jsonl
python3 daily/gdrive.py get-state insights.md /tmp/insights.md
python3 daily/gdrive.py get-state inspiration.md /tmp/inspiration.md   # owner's reference videos (may not exist yet)
python3 daily/gdrive.py visual-ideas /tmp/visual > /tmp/visual.txt  # owner's pasted images + notes ("IDEIAS VISUAIS")
python3 daily/gdrive.py ideas > /tmp/ideas.txt               # owner's ideas doc in Drive ("IDEIAS — escreva aqui")
python3 daily/gdrive.py cleanup-links                         # earlier videos: remove their public links
python3 daily/report.py > /tmp/report.md                     # yesterday's videos: ranking + interactions
python3 daily/metrics.py /tmp/stories.jsonl > /tmp/metrics.md  # views, watch time, likes per post
python3 daily/plan.py /tmp/stories.jsonl                       # today's accounts + everything already used
```
**Read the video analysis BEFORE writing anything new (mandatory).** Read `/tmp/report.md` (yesterday) and
`/tmp/metrics.md` (last 60 days). For EACH account you will make a video for today, write 2–3 lines in
`/tmp/insights.md` under `## Daily notes <date>`: its worst and best recent video (views, retention), what
they had in common, and the ONE thing today's story/shots will change or keep because of it. Then write the
story so that it follows that note. Include these notes in the final report.

Read `/home/user/motion/CLAUDE.md` (engine workflow + QC), `daily/STORY_BRIEF.md`, `/tmp/insights.md` (voices,
music, rules learned), `/tmp/inspiration.md` (techniques from the owner's reference videos — apply them in
stories and shots) and `/tmp/metrics.md`. If posts now ≥ 2 days old clearly beat or lose to their account's
median, add the lesson (date, numbers, rule) to `/tmp/insights.md` and apply it today — one change at a time.
Save it back at the end: `python3 daily/gdrive.py put-state /tmp/insights.md insights.md`.

## 1. Stories (you write them) — all accounts first
**Series:** for an account with format `interactive_series`, read its last entries in `/tmp/stories.jsonl`
(`series`, `part`, `choice`) and write the next part, or a new Partie 1 after the final part.

**Owner's ideas first:** `/tmp/ideas.txt` has one idea per line (`<account|todas>: <idea>`). An idea whose text
is not yet in any `idea` field of `/tmp/stories.jsonl` is pending: use it today for that account (`todas` = the
best-fitting account), at most one idea per account per day, and pass it to publish.py with `--idea "<line>"`.
Ideas that are instructions (length, tone, style) apply to that account from today on — also note them in insights.
**Visual ideas:** `/tmp/visual.txt` lists the owner's notes with `[IMAGEM: …]` markers; the images are under
`/tmp/visual/`. If there are new ones (not yet noted in insights), look at them (tile several into one image to
save cost), and adapt the 2D drawing to them — palette, light, sets, props, character look — by writing new
cairo drawing code in the story's render.py; never trace or copy the artwork itself. Note in insights which
image was adopted for which account and what changed.
For each account read its format file and locale file (`daily/locales/<language>.md`) and write the story
natively in that language to `/home/user/motion/_story_<account>.txt` (dots → underscores), with title, slug
(new folder, ≤ 20 chars, ASCII) and caption in that language. Length = the account's `seconds`/`words`. End on a comment question that loops back to the hook (STORY_BRIEF). Every story is
brand new: never reuse or translate a story, twist or ending from any account or any day (see the log).

## 2–4. For each account (≈ 30–45 min each)
**Engine:** `plan.py` prints each account's `engine`. `motion` (the default) → the steps below.
`vintage` or `vox` (Lumenstick studio looks) → read `daily/studio/README.md` and use
`daily/studio.py setup / stills / finish` in place of "Voiceover + engine folder" and "Animation". Publish and
save-story stay the same. A `vintage` render takes ≈ 90 min, so set it up first and let it render in the background
while you make the other accounts' videos.

**Voiceover + engine folder** (voice, language and background music come from the account / Drive)
```bash
cd /home/user/motion && python3 /home/user/Editor/daily/bootstrap.py . <slug> "<Title>" _story_<account>.txt --account <account>
```
If it prints `LENGTH … OUTSIDE …`, lengthen/shorten the story and run it again.

**Visual style:** if the account has `visual_style` (e.g. `pixel_arcade`, see `daily/styles/`), bootstrap already
hooked it in — draw the shots as usual; the style pixelates them and adds its HUD/frame. Check one still early.

**Animation** — `SHOTS` in `<slug>/render.py`, `CUES` in `<slug>/audio.py` and the **music per scene** in
`<slug>/score.json` (see "Music and sound" below; the background track already plays under it; keep
`build_music` for one-off stingers/risers). Reuse the engine's rigs/sets and the existing
story folders as examples. All on-screen text in the account's language. Then:
```bash
cd /home/user/motion/<slug>
python3 render.py timeline && python3 render.py stills <a few times>    # one contact sheet to check
python3 render.py video 4 && python3 audio.py && ./finalize.sh
python3 verify_audio.py ../output/<slug>_1080x1920.mp4
```
QC from Motion's CLAUDE.md (decode clean, black/freeze, opening cuts, one 1 fps contact sheet). Render the
next account in the background while finishing this one.

**Publish** (channel, local time, format, mirrors come from the account)
```bash
cd /home/user/Editor
cp /home/user/motion/_story_<account>.txt /home/user/motion/<slug>/story.txt
python3 daily/publish.py /home/user/motion/output/<slug>_1080x1920.mp4 --account <account> \
  --slug <slug> --title "<Title>" --hook "<first line>" --caption "<caption + hashtags>" \
  --story /home/user/motion/<slug>/story.txt [--idea "<the idea line used>"] \
  [--series "<series title>" --part N --choice "A|B"]     # interactive_series accounts
python3 daily/engine.py save-story /home/user/motion <slug>
```
`publish.py` saves `<day>.mp4` + `<day>.txt` in the account's Drive folder, gives the video a public link
(Buffer downloads it from there; tomorrow's `cleanup-links` removes it), creates the Buffer post(s) and
appends to the story log in Drive. If the post time has passed it posts immediately.
**AI label (owner's final decision, 2026-11-10):** every post is marked AI-generated: `buffer_api.py` sets the
platform flag (`isAiGenerated: True`) and `publish.py` adds "KI-generiert" / "Généré par IA" / "AI-generated" at the
end of every caption, mirrors included. Never switch them off, whatever an older note in insights.md says.
Studio videos (engine vintage/vox) are published from the path `studio.py finish` prints (`_1080x1080.mp4` for 1:1).

## Music and sound (owner, 2026-11-10: compose for the scenes; music and effects LOW under the voice)
- **Compose the music for the scenes.** After the shot list is fixed (`render.py timeline` / the studio scene
  table), write `score.json`: one music cue per scene or per group of scenes that share a feeling, each with the
  mood that fits what is shown and said (calm, curious, mystery, tense, danger, sad, hopeful, storybook, mischief,
  triumph, silence), one key for the whole video, a `build` on the climb to the twist, and a short `silence` cue
  right before the key line. List the scene SFX in the same file (`daily/studio/tools/score.py` has the moods and
  SFX names). Motion: `<slug>/score.json` (audio.py adds it to the background track). Studios: `work/score.json`.
- **Levels are fixed by the mixer, don't raise them:** music ≈ 24 dB under the voice and ducked ≈ 8 dB more while
  it speaks; effects ≈ 18 dB under the voice, their peaks ≈ 9 dB under the voice peak. Fewer effects: only for
  actions you see (a door, a slam on a headline, a page turn), never on every cut.
- Check the printed levels (Motion `audio.py`, studio `mix.py`) and listen to the first 10 s of the final MP4 if
  anything sounds busy. The voice must always be the clearest thing.

## 5. Finish + report
`python3 daily/gdrive.py put-state /tmp/insights.md insights.md`. Then one line per account: title,
language, duration, post time, Buffer post id — plus what the metrics taught today (or what failed and where).
