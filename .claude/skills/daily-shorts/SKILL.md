---
name: daily-shorts
description: The owner's daily run - one brand-new 2D-animated short per account with Gerar = s in the owner's Google Sheet 'Buffer Contas' (own language, format, engine, voice, length, post time), scheduled through Buffer and archived in Google Drive. Use for the scheduled daily session or when asked to make/post today's videos.
---

# Daily shorts

A fresh session runs this every morning with no repository attached: the pipeline comes from the public
`fahholiver/Editor` repo, state (engine, music, story log, insights, ideas) from Drive `TikTok Daily/`, output
goes to Buffer + Drive only. The scheduled task's prompt says what is authorised. If one account fails and
cannot be fixed, skip it, finish the others, report it. Never post a broken video.
**Who, when, what:** the owner's Google Sheet "Buffer Contas" (`daily/sheet.py`; columns Conta principal, Hora de
postagem (London), Conta repostagem (comma-separated, same time), País-Língua, Modelo-skill, Gerar s/n). `plan.py`
reads it; accounts.json only adds voices/lengths. Never edit accounts.json to add/remove accounts: the owner uses
the sheet. Accounts with Gerar = n are NOT part of this run: a separate task posts the ready-made Drive videos to
them with `daily/queue_post.py` (one different file per account, see the end). `SHEET:` warnings from plan.py go
into the final report.

## 0. Setup + read (before writing anything)
```bash
cd /home/user && git clone -q --depth 1 -b claude/buffer-tiktok-video-generation-lrudue https://github.com/fahholiver/Editor Editor
cd /home/user/Editor && pip install -q -r daily/requirements.txt
python3 daily/engine.py fetch /home/user/motion            # Motion engine from Drive
for f in stories.jsonl insights.md inspiration.md; do python3 daily/gdrive.py get-state $f /tmp/$f; done
python3 daily/gdrive.py visual-ideas /tmp/visual > /tmp/visual.txt
python3 daily/gdrive.py ideas > /tmp/ideas.txt
python3 daily/gdrive.py cleanup-links                      # remove earlier days' public links
python3 daily/report.py > /tmp/report.md; python3 daily/metrics.py /tmp/stories.jsonl > /tmp/metrics.md
python3 daily/plan.py /tmp/stories.jsonl                   # today's accounts from the sheet (+ engine, format, reposts) + what each already used
```
Read `/tmp/report.md` + `/tmp/metrics.md`, then for EACH account write 2–3 lines in `/tmp/insights.md` under
`## Daily notes <date>`: worst and best recent video (views, retention), what they share, the ONE thing today
changes or keeps. Write the story to follow that note. A post ≥ 2 days old that clearly beats/loses to its
account median → add the lesson (date, numbers, rule) to insights; one change at a time.
Also read `daily/STORY_BRIEF.md`, `/tmp/insights.md` (voices, rules), `/tmp/inspiration.md` (techniques from the
owner's reference videos) and, for Motion accounts, `/home/user/motion/CLAUDE.md`.

## 1. Stories (all accounts first)
- **Owner's ideas first:** a line of `/tmp/ideas.txt` (`<account|todas>: <idea>`) not yet in any `idea` field of
  the log is pending: use it today (max one per account; `todas` = best fit), pass `--idea "<line>"` to publish.
  Instruction-type ideas (length, tone, style) apply from today on; note them in insights.
- **Visual ideas:** new `[IMAGEM: …]` items in `/tmp/visual.txt` (images in `/tmp/visual/`, tile several into one
  look): adapt palette, light, sets, props, character look in today's drawing code; never trace the art. Note it.
- **Series** (`interactive_series`): continue from the account's last log entry (`series`, `part`, `choice`).
- Read the account's `daily/formats/<format>.md` + `daily/locales/<language>.md`; write natively in that
  language to `/home/user/motion/_story_<account>.txt` (dots → underscores) with title, slug (new, ≤ 20 chars
  ASCII), caption. Length = `seconds`/`words`. End on a comment question that loops back to the hook.
- Every story is brand new: never reuse or translate a story, twist or ending (check the log). Accounts that
  share a language get completely different stories.

## 2. Video per account (by `engine` from plan.py)
**motion** (default):
```bash
cd /home/user/motion && python3 /home/user/Editor/daily/bootstrap.py . <slug> "<Title>" _story_<account>.txt --account <account>
cd <slug> && python3 render.py timeline && python3 render.py stills <t1> <t2> ...   # one contact sheet, look at it
python3 render.py video 4 && python3 audio.py && ./finalize.sh && python3 verify_audio.py ../output/<slug>_1080x1920.mp4
```
`LENGTH … OUTSIDE` → change the story length and rerun. `visual_style` (e.g. pixel_arcade) is hooked in by
bootstrap; check one still early. Write `SHOTS` in render.py, `CUES` in audio.py, music in `score.json`.
QC per Motion's CLAUDE.md (clean decode, black/freeze, opening cuts, one 1 fps sheet).

**vintage / vox / cartoon** (`daily/studio/README.md`, its "what to write" section for the engine):
```bash
cd /home/user/motion && python3 /home/user/Editor/daily/studio.py setup . <slug> "<Title>" _story_<account>.txt --account <account>
python3 /home/user/Editor/daily/studio.py stills <slug> 1.5 4 9 ...      # -> <slug>/work/sheet.jpg
python3 /home/user/Editor/daily/studio.py finish <slug> [--workers 3]     # -> output/<slug>_1080x1920.mp4 (+ QC sheet)
```
`cartoon` (user890997140) = `.claude/skills/cartoon-audio-short` (steps 4.2–4.6), no captions, series overlays
from `work/overlay.json`. vintage and cartoon render for 45–90 min: set them up first and run `finish` in the
background while making the other accounts.

## 3. Music and sound (owner 2026-11-10: composed per scene, LOW under the voice)
After the shot list is fixed, write `score.json` (Motion `<slug>/score.json`, studios `work/score.json`): one cue
per scene or group (calm, curious, mystery, tense, danger, sad, hopeful, storybook, mischief, triumph, silence),
one key, a `build` into the twist, a short `silence` before the key line, and only SFX for visible actions
(names in `daily/studio/tools/score.py`). The mixers fix the levels (music ≈ −24 dB, ducked ≈ 8 dB more;
SFX ≈ −18 dB, peaks ≈ −9 dB vs voice): don't raise them. Check the printed levels; the voice is always clearest.

## 4. Publish
```bash
cd /home/user/Editor && cp /home/user/motion/_story_<account>.txt /home/user/motion/<slug>/story.txt
python3 daily/publish.py /home/user/motion/output/<slug>_1080x1920.mp4 --account <account> --slug <slug> \
  --title "<Title>" --hook "<first line>" --caption "<caption + hashtags>" --story /home/user/motion/<slug>/story.txt \
  [--idea "<idea line>"] [--series "<series>" --part N --choice "A|B"]
python3 daily/engine.py save-story /home/user/motion <slug>
```
publish.py: Drive copy (`<day>.mp4/.txt`), temporary public link, Buffer post(s) + the sheet's repost accounts (same time), log
entry; posts now if the time has passed. Every post is marked AI-generated (platform flag + caption note,
owner's final decision 2026-11-10): never switch it off. 1:1 studio videos: use the `_1080x1080.mp4` path.

## 5. Finish
`python3 daily/gdrive.py put-state /tmp/insights.md insights.md`, then one line per account: title, language,
duration, post time, Buffer post id, plus what the metrics taught (or what failed and where).

## Drive queue (separate task, 13:35 London)
```bash
python3 daily/queue_post.py --folder 1Rl38oJZVI8cM8TcaefGtoXCfHKaueAKA --caption "<caption>"
```
Accounts = the sheet's Gerar = n rows, each at its own London time; the row's repost accounts get the same
file. Each main account gets a different file; a file is trashed once all its posts are done (one sent) and is
held back while any waits, so no video ever reaches two main accounts. Run it once a day, in the foreground (waits up to ~90 min). Needs
`GDRIVE_FULL_REFRESH_TOKEN`. On an error report it; never repost or delete to work around it.
