# Daily run — what the scheduled Claude session does

Every day: **one new, different 2D-animated video per TikTok account** connected in Buffer. Each account
has its own **language/country, format, voice, length and posting time** (`daily/accounts.json`); the posting
times are at least 1 h apart. The scheduled task's own prompt (written by the repo owner) says what the
session is allowed to do; this file only describes the steps. If one account's video fails and cannot be
fixed, skip it, finish the others, and report it (never post a broken video).

## 0. Setup + learn from the numbers (≈5 min)
```bash
cd /home/user/Editor && git fetch -q origin "${PIPELINE_REF:-main}" && git checkout -q FETCH_HEAD -- daily
pip install -q -r daily/requirements.txt
git fetch -q --depth 1 origin media && git show FETCH_HEAD:stories.jsonl > /tmp/stories.jsonl || touch /tmp/stories.jsonl
python3 daily/metrics.py /tmp/stories.jsonl > /tmp/metrics.md     # views, watch time, likes per post
python3 daily/plan.py /tmp/stories.jsonl                          # today's accounts + everything already used
```
Read `/tmp/metrics.md` and `daily/insights.md`. If posts that are now ≥ 2 days old teach something new
(a hook type, length, format, caption, posting time that clearly beats or loses to the account's median),
add it to `daily/insights.md` (date, numbers, the rule) and apply it today. Change one thing at a time.

The Motion engine must be at `/home/user/motion` (branch `claude/radiator-animation`); if missing, attach
`fahholiver/Motion` with `add_repo` and clone it there. Read `/home/user/motion/CLAUDE.md`, `daily/STORY_BRIEF.md`.

## 1. Stories (you write them) — all accounts first
For each account read its format file AND its locale file (`daily/locales/<language>.md`) and write the story
natively in that language to `/home/user/motion/_story_<account>.txt` (dots → underscores), with title, slug
(new Motion folder, ≤ 20 chars, ASCII) and caption in that language. Length = the account's `words` range.
Every story is brand new: never reuse or translate a story, twist or ending from any account or any day.

## 2–4. For each account (≈ 30–45 min each)
**Voiceover + engine folder** (voice and language come from the account; background music is added
automatically when `daily/assets/background_music.*` exists)
```bash
cd /home/user/motion && python3 /home/user/Editor/daily/bootstrap.py . <slug> "<Title>" _story_<account>.txt --account <account>
```
**Animation** — `SHOTS` in `<slug>/render.py`, `CUES`/`build_music` in `<slug>/audio.py` (keep `build_music`
light: the background track already plays; use it for stingers/risers). All on-screen text (tags, phone UI,
contact names, call status) in the account's language. Then:
```bash
cd /home/user/motion/<slug>
python3 render.py timeline && python3 render.py stills <a few times>    # one contact sheet to check
python3 render.py video 4 && python3 audio.py && ./finalize.sh
python3 verify_audio.py ../output/<slug>_1080x1920.mp4
```
QC from Motion's CLAUDE.md (decode clean, black/freeze, opening cuts, one 1 fps contact sheet). Render the
next account's video in the background while finishing this one.

**Publish** (channel, local post time and format come from the account)
```bash
cd /home/user/Editor
python3 daily/publish.py /home/user/motion/output/<slug>_1080x1920.mp4 --account <account> \
  --slug <slug> --title "<Title>" --hook "<first line>" --caption "<caption + hashtags>" \
  --story /home/user/motion/<slug>/story.txt
```
If the post time has already passed it posts immediately. `publish.py` rewrites (force-pushes) the `media`
branch of fahholiver/Editor (newest videos + story log) and saves `<day>.mp4` + `<day>.txt` to the
account's Google Drive folder. Run it only if the scheduled task's prompt authorises that.

## 4b. After ALL accounts are published
Save each story folder on its own Motion branch **with a git worktree** (never switch branches in
/home/user/motion — that deletes the other stories' files):
```bash
cd /home/user/motion && s=<slug> && W=/tmp/wt_$s
git worktree add -q -b daily/$s "$W" claude/radiator-animation
mkdir -p "$W/$s" && for f in $s/*; do case "$(basename $f)" in build|stills|stems|mix.wav|music_bed.wav|__pycache__) ;; *) cp -r "$f" "$W/$s/";; esac; done
(cd "$W" && git add -f $s && git commit -qm "Daily short $s" && git push -q -u origin daily/$s); git worktree remove --force "$W"
```
Commit `daily/insights.md` changes to the Editor pipeline branch. Free disk: delete `<slug>/build`, `<slug>/stills`
and `/home/user/motion/output/*.mp4`.

## 5. Report
One line per account: title, language, duration, post time, Buffer post id — plus what the metrics taught
today (or what failed and at which step).
