# Daily run — what the scheduled Claude session does

Every day: **one new, different 2D-animated video per TikTok account** connected in Buffer, each account in
its own format (`daily/accounts.json` → `daily/formats/<format>.md`), all scheduled for **14:00** UK time.
The scheduled task's own prompt (written by the repo owner) says what the session is allowed to do; this
file only describes the steps. If one account's video fails and cannot be fixed, skip that account, carry
on with the others, and report it (never post a broken video).

## 0. Setup (≈2 min)
```bash
cd /home/user/Editor && git fetch -q origin "${PIPELINE_REF:-main}" && git checkout -q FETCH_HEAD -- daily   # latest pipeline
pip install -q -r daily/requirements.txt
```
The Motion engine must be at `/home/user/motion` (branch `claude/radiator-animation`); if it is missing,
attach `fahholiver/Motion` with `add_repo` and clone it there. Read `/home/user/motion/CLAUDE.md` (engine
workflow, brief, QC) and `daily/STORY_BRIEF.md`.

Today's plan + the story log (so nothing repeats):
```bash
cd /home/user/Editor
git fetch -q --depth 1 origin media && git show FETCH_HEAD:stories.jsonl > /tmp/stories.jsonl || touch /tmp/stories.jsonl
python3 daily/plan.py /tmp/stories.jsonl      # one line per account: format + brief + titles already used
```

## 1. Stories (you write them) — all accounts first
For each account in the plan, read its format file and write a story to
`/home/user/motion/_story_<account>.txt` (account name with dots → underscores), plus title, slug (new
folder name in the Motion repo, ≤ 20 chars) and caption. Write them together so the accounts get clearly
different stories and settings today. Re-read each once as a listener.

## 2–4. For each account, in plan order (≈ 30–45 min each)
**Voiceover + engine folder**
```bash
cd /home/user/motion && python3 /home/user/Editor/daily/bootstrap.py . <slug> "<Title>" _story_<account>.txt
```
ElevenLabs keys (`ELEVENLABS_API_KEYS`) rotate automatically; with none left it uses the free Edge voice.
Check the printout: total 55–95 s, sensible word times.

**Animation** — write `SHOTS` in `<slug>/render.py` and `CUES`/`build_music` in `<slug>/audio.py` (reuse the
engine's rigs/sets and the existing story folders; for `phone_horror` lean on `phone_frame`/`call_ui`/message
bubbles). Then:
```bash
cd /home/user/motion/<slug>
python3 render.py timeline && python3 render.py stills <a few times>    # one contact sheet to check
python3 render.py video 4 && python3 audio.py && ./finalize.sh
python3 verify_audio.py ../output/<slug>_1080x1920.mp4
```
QC from Motion's CLAUDE.md (decode clean, black/freeze, opening cuts, one 1 fps contact sheet).

**Publish to that account only**
```bash
cd /home/user/Editor
python3 daily/publish.py /home/user/motion/output/<slug>_1080x1920.mp4 --channels <account> --format <format> \
  --slug <slug> --title "<Title>" --hook "<first line>" --caption "<caption + hashtags>" \
  --story /home/user/motion/_story_<account>.txt
```
14:00 `Europe/London` by default (`POST_TIME`/`POST_TZ`); if it has already passed it posts immediately.
`publish.py` rewrites (force-pushes) the `media` branch of fahholiver/Editor (newest videos + story log) and,
when `GDRIVE_*` is set, saves `<day>.mp4` + `<day>.txt` in the account's Google Drive folder. Run it only if
the scheduled task's prompt authorises that.

## 4b. After ALL accounts are published
Commit each `<slug>/` (it has a `.gitignore` for `build/`, `stills/`, `stems/`, `mix.wav`) to a new branch
`daily/<slug>` of the Motion repo. Do this only at the end: switching branches removes the other stories'
files from the working tree (restore with `git checkout daily/<slug> -- <slug> && git reset -q -- <slug>`).
Then free disk space: `rm -rf /home/user/motion/*/build /home/user/motion/*/stills /home/user/motion/output/*`.

## 5. Report
One line per account: title, format, duration, Buffer post id + time — or what failed and at which step.
