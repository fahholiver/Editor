# Daily run — what the scheduled Claude session does

A **fresh** Claude Code session starts every morning. It has no repositories attached and cannot write to
GitHub: everything it needs comes from the public `fahholiver/Editor` repo (this pipeline) and from Google
Drive (`TikTok Daily/`: engine, music, story log, insights). Its output goes to Buffer and Drive only.

Every day: **one new, different 2D-animated video per account** (`daily/accounts.json`), each with its own
language/country, format, voice, length (65–125 s) and posting time (≥ 1 h apart). The scheduled task's own
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
python3 daily/metrics.py /tmp/stories.jsonl > /tmp/metrics.md  # views, watch time, likes per post
python3 daily/plan.py /tmp/stories.jsonl                       # today's accounts + everything already used
```
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
(new folder, ≤ 20 chars, ASCII) and caption in that language. 65–125 s (≈ 165–290 words). Every story is
brand new: never reuse or translate a story, twist or ending from any account or any day (see the log).

## 2–4. For each account (≈ 30–45 min each)
**Voiceover + engine folder** (voice, language and background music come from the account / Drive)
```bash
cd /home/user/motion && python3 /home/user/Editor/daily/bootstrap.py . <slug> "<Title>" _story_<account>.txt --account <account>
```
If it prints `LENGTH … OUTSIDE 65-125 s`, lengthen/shorten the story and run it again.

**Visual style:** if the account has `visual_style` (e.g. `pixel_arcade`, see `daily/styles/`), bootstrap already
hooked it in — draw the shots as usual; the style pixelates them and adds its HUD/frame. Check one still early.

**Animation** — `SHOTS` in `<slug>/render.py`, `CUES`/`build_music` in `<slug>/audio.py` (the background
track already plays; keep `build_music` to stingers/risers). Reuse the engine's rigs/sets and the existing
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

## 5. Finish + report
`python3 daily/gdrive.py put-state /tmp/insights.md insights.md`. Then one line per account: title,
language, duration, post time, Buffer post id — plus what the metrics taught today (or what failed and where).
