# House rule: footage full screen, boxes for stills

Moving footage (archive video, drone, response B-roll) always plays **full screen**, edge to edge, like a normal documentary, with only the captions on top. White evidence boxes, handwritten notes and arrows are only for **photos, documents, report figures and diagrams**. `vidlib` enforces this: a `box` shot that contains a `V(...)` video is converted to a full-screen shot automatically (pass `boxed=True` to `sh()` only if the creator explicitly asks for a boxed clip). Alternate the two so the viewer gets real footage, then a detail explained on a still, then footage again.

# Scene types (shot list reference)

Every shot is `sh(t0, type, **params)`. `t0` is in absolute voiceover seconds, and a shot lasts until the next one starts. Helpers come from `scripts/vidlib.py`:
- `w(word, near)`: the time the word is spoken
- `V(...)`: a video box
- `I(...)`: a photo box
- `N(...)`: a note
- `OVL(...)`: a manual footage overlay
- `A43` and `A169`: box sizes
- `NX`: the note column

| type | use | key params |
|---|---|---|
| `box` | real footage / photos with notes | `boxes=[V(src, ss, geo, cap) or I(img, geo, cap, rot)]`, `notes=[N(text, x, y, at, color, size, sub, arrow=[[x1,y1],[x2,y2]])]`, `src='Source line'` |
| `full` | full-screen footage. **All moving footage plays this way**, for as long as the beat needs | `clip=dict(src='st_name', ss=0.5)` |
| `title` | series title / end card | `lines=['Engineering','Failures']`, `kicker`, `sub` |
| `section` | chapter card | `no='03'`, `name=['Loss of','Power']`, `sub`, `img`, `cap` |
| `head` | big Anton text beat | `lines`, `accent=1`, `acol='red'`, `fs`, `sub`, `subAt`, `at=[per-line times]` |
| `counter` | counting number | `steps=[dict(value, label, at, accent)]`, `prefix='$'`, `suffix`, `dec`, `more` (handwritten line above), `fs` |
| `doc` | typed paper card with highlight | `header`, `body` with `[[highlighted words]]`, `hlAt`, `fs`, `notes` |
| `bars` | cost vs payout style comparison | `lines`, `bars=[dict(value, label, h (0-1), at, color)]` |
| `list` | words stacking on cue | `items=[dict(text, at, accent)]`, `fs` |
| `timeline` | two dates with a gap | `events=[dict(date, label, at, accent)]`, `gap=dict(from=0, to=1, label, at)` |
| `saiddid` | "X said / Y said" split | `lk`, `said`, `saidAt`, `rk`, `did`, `didAt` |
| `blueprint` | neon diagram | `kind`, `title`, plus kind-specific `...At` times |

## Box geometry
- `A43 = x170 y165 w880 h660`: 4:3 archive film. `A169 = x150 y200 w1040 h585`: 16:9 stock or photo. Notes go at `x=NX (1250)`, `y` between 200 and 700.
- Two boxes in one shot are fine. Give the second one its own `at=` so it drops in on its word.
- Portrait documents use about `w520 h673` centred (`x≈560`), with notes on the right at x≈1190.
- **Video box options:** `grade='warm'|'cool'`, `nov=True` (then add overlays with `OVL`, for clips that continue across shots or two clips in one box), `dy=0` (no drop, for a box that is already on screen).
- **Photo box options:** `fit='cover'|'contain'`, `pos='50% 30%'`, `push` (zoom amount, default 0.06), `origin` (zoom toward a detail, e.g. a headline), `bg='#ffffff'` for documents.

## Blueprint kinds

- `chain` uses two or three `nodes`. Give each node a short `label` and absolute reveal time `at`, plus optional `detail` and `accent=True`. Use one clear causal sequence per diagram.
- `structure` draws custom SVG `paths` with `d`, `at`, optional `color` of red or yellow, `width`, and `dur`. Optional `labels` have `x`, `y`, `text`, `at`, plus `color`, `size`, and `align`. Use for a bridge elevation, route, process line, or system schematic.
- [bridge_shots.py](../examples/bridge_shots.py) demonstrates both kinds. Keep the explanatory paths and labels above y=930. Use absolute episode time for all cue times, including chunks after the opening.
- For motion beyond these patterns, add a case-specific blueprint in `engine/engine.js` and compute it deterministically from the seek time `t`. Avoid random or timer-driven effects.

## Timing tips
- Note `at` should be about 0.2 to 0.6 s before the word, so it is half written when the word is said.
- Shots that follow each other on the same footage: set the later box's `at` before its `t0` and `dy=0`, and drive the footage with one `OVL` spanning both shots.
- Footage appears 0.45 s after the box lands, and ends 0.35 s before the shot ends. Choose `ss` so the key moment lands on the right word: `moment_in_film = ss + (t - (at + 0.45))`.
