# Daily run — what the scheduled Claude session does

This is the instruction file for the scheduled task (a fresh Claude Code cloud session every day, started
in the morning so the post is ready before **14:00**). The scheduled task's own prompt (written by the repo
owner) says what the session is allowed to do; this file only describes the steps. If a step fails and
cannot be fixed, stop and report what failed (don't post a broken video).

## 0. Setup (≈2 min)
```bash
cd /home/user/Editor && git fetch -q origin "${PIPELINE_REF:-main}" && git checkout -q FETCH_HEAD -- daily   # latest pipeline
pip install -q -r daily/requirements.txt
```
Attach and clone the animation engine: call `add_repo` for `fahholiver/Motion`, then
`git clone --depth 1 -b claude/radiator-animation https://github.com/fahholiver/motion /home/user/motion`.
Read `/home/user/motion/CLAUDE.md` (the engine workflow, brief and QC) and `daily/STORY_BRIEF.md`.

Read the story log so today's story is new:
```bash
git -C /home/user/Editor fetch -q --depth 1 origin media && git -C /home/user/Editor show FETCH_HEAD:stories.jsonl | tail -30
```
(no `media` branch yet = first run, nothing to avoid except the six stories already in the Motion repo.)

## 1. Story (you write it)
Write today's story following `daily/STORY_BRIEF.md` to `/home/user/motion/_story.txt`, and decide the
title, slug (must not already exist as a folder in the Motion repo) and TikTok caption.
Re-read it once as a listener: hook in the first line, every beat drawable, ending lands.

## 2. Voiceover + engine folder (≈1–2 min)
```bash
cd /home/user/motion
python3 /home/user/Editor/daily/bootstrap.py . <slug> "<Title>" _story.txt
```
ElevenLabs is used when `ELEVENLABS_API_KEY` is set, otherwise the free Edge voice `en-GB-RyanNeural`.
Listen-check by numbers: total length 70–110 s, no line under 0.3 s or with a pause > 2 s inside it. If the
TTS mangled a word (bad timing in the printout), rewrite that word in `_story.txt` and rerun.

## 3. Animation (the main work — follow Motion's CLAUDE.md exactly)
Write `SHOTS` in `<slug>/render.py` and `CUES`/`build_music` in `<slug>/audio.py`, reusing the engine's rigs
and sets (and the existing story folders as examples). Then:
```bash
cd /home/user/motion/<slug>
python3 render.py timeline && python3 render.py stills <a few times>    # one contact sheet to check
python3 render.py video 4
python3 audio.py
./finalize.sh
python3 verify_audio.py ../output/<slug>_1080x1920.mp4
```
Do the QC from Motion's CLAUDE.md (decode clean, black/freeze detect, opening cuts, one 1 fps contact
sheet). Keep image reviews to one sheet per stage.

## 4. Publish (≈2 min)
```bash
cd /home/user/Editor
python3 daily/publish.py /home/user/motion/output/<slug>_1080x1920.mp4 \
  --slug <slug> --title "<Title>" --hook "<first line of the story>" --caption "<caption + hashtags>"
```
Defaults: 14:00 `America/Sao_Paulo` (env `POST_TIME` / `POST_TZ` override); if 14:00 has already passed it
posts immediately (`--late now`). Note that `publish.py` rewrites (force-pushes) the `media` branch of
fahholiver/Editor, which holds only the newest videos + the story log; run it only if the scheduled task's
prompt authorises that.

Optional, only if the run went smoothly and time allows: commit `<slug>/` (without `build/`, `stills/`,
`output/`) to a new branch `daily/<slug>` of the Motion repo so the shots can be reused later.

## 5. Report
End with a short summary: title, hook, duration, Buffer post id and scheduled time, video URL — or what
failed and at which step.
