# Story brief — rules for every daily short (61–80 s from 2026-11-11, in the account's language)

The story is the narration script for one Motion video. It is read by a TTS voice exactly as written, and
every word becomes a karaoke caption, so write for the ear.

## Shape
Each TikTok account has its own **format** (see `daily/accounts.json`). The format file in
`daily/formats/<format>.md` gives the shape, voice and title style; the rules below apply to every format.

## Rules
- **Length: 61–80 s** (from 2026-11-11; `seconds` per account in `daily/accounts.json`, `words` is the
  matching text length). Why: 2026-11-10 analysis — viewers leave at ~12–19 s whatever the length, so the 90–118 s
  videos were watched only 5–21 % through and never left TikTok's first test pool (~300–900 views). Shorter =
  higher completion; over 60 s keeps them eligible for the Creator Rewards programme. bootstrap.py / studio.py
  print a warning if the narration is outside — then lengthen/shorten the story and redo it. One sentence or short beat per line; blank lines only for a
  longer pause (a paragraph break = ~0.75 s silence, a line break = ~0.45 s).
- **Ending (every format, from 2026-11-11): a question for the comments + a loop.** The last line asks the
  viewer something they can answer in one word (the interactive series got the best engagement, 7.7 %, from its
  comment choice; the other formats got 0–1 comments and ~0 shares). And the last line echoes the hook (the same
  object, number or phrase) so the end runs straight back into the start and people watch it again.
- **Language & place from the account's locale** (`daily/locales/<language>.md`): write natively in that
  language (never translate an English draft), set it in that country with local places, homes, habits and
  names, so a local viewer recognises their own life. Every on-screen text (tags, phone messages, contact
  names, UI words) is in that language too.
- Point of view as the format says; keep tense and person consistent.
- Dialogue in curly quotes “ ” (the captions tint quotes cream). Keep speakers obvious.
- Numbers as you want them shown (*3:18 a.m.*, *Flight 628*); the TTS reads them.
- Every event must be drawable as flat 2D vector shots with the engine: night interiors (bedroom,
  kitchen, hallway, bathroom/mirror, lift, flat, plane cabin), windows/facades, phones and call screens,
  one or two characters, a pet, simple props. No crowds fighting, no complex action, no gore.
- Accounts on another engine (`engine` in accounts.json, see `daily/studio/README.md`): `vintage` and `cartoon` can also do
  outdoor sets, streets, forests, water and weather (a 3D world); `vox` tells the story as a case file
  (documents, clippings, maps, timelines, drawn cut-outs), so write beats that can be shown as evidence.
- Visual beats are concrete nouns the animator can show at the moment they are said (a radiator, wet
  footprints, a sleeve hanging loose). Don't reveal later events early.
- TikTok-safe: creepy, not graphic. No self-harm, no harm to children or animals shown, no real people,
  places of tragedy or brands.
- **Always a brand-new story.** Never repeat or translate a story, twist or ending — not from earlier days,
  not from another account, not from the older videos on the accounts.
- **Original every day, and different on every account.** Read the recent log first and do not reuse a
  hook, setting + twist pair, or ending mechanic from the last 30 entries (all accounts), nor give two
  accounts the same story or setting on the same day. The "only child" tell has already been used three times —
  find new tells (a detail only the real person would know, a sound that's wrong, a reflection, a
  timestamp, a floor number, a photo, a pet's behaviour…).

## The 5-step viral formula (every format, from 2026-11-13 — owner's reference scripts)
Owner's model scripts: the "What do you do when a killer has seen your face?" series (parts 1–6), the mall
mannequins, the deer + porch light, and the curiosity "o governo começou a pagar R$ 1…". Every story, horror
or not, follows these five steps (the format file says how they look in that format):
1. **Impact hook (0–3 s):** start *inside* an extreme, dangerous or absurd situation — no intro, no name, no
   "one night…". A question or a statement the viewer can't leave unanswered (*"What do you do when a killer has
   seen your face?"*, *"I got locked in the mall overnight."*, *"In our town, there's one rule."*).
2. **Clear rules or an absurd premise (by ~8 s):** one or two rules/mechanics the viewer must remember
   (*"The mannequins move when the lights go out. And the lights go out when you stop moving."*). Say them
   plainly; later beats test them. Numbered rules (*"Rule one: kill the light."*) are spoken alone on a line and
   shown as a big on-screen tag.
3. **Escalation by micro-conflicts:** a new obstacle every 5–8 s — a sound, a footstep, a text, a price, a
   count, a time that repeats (*9:41*). Each beat is one concrete fact, never a mood. No beat repeats the last.
4. **Critical choice / cliffhanger:** end when the danger lands or when the character has two bad options —
   each option with one advantage and one cost (*"A, the balcony: one metre gap, six floors. B, the bathroom:
   one lock — and she has a key to every room."*). A rule is broken or turns out to be a trap
   (*"If help is already waiting for you, it isn't help."*).
5. **CTA for the algorithm:** the last line asks for a one-word comment (*"A or B — comment now."*) and/or
   promises the next part (*"Follow for part two."*), and echoes the hook so the video loops.

Pacing rule of thumb from the references: ~2.5 spoken words per second, a twist or new fact every 10 s,
the rule/premise stated before 10 s, the choice or sting in the last 8–15 s.

## Also produce
- **Title** — 2–4 words, in the style the format file gives.
- **slug** — lowercase, underscores, ≤ 20 chars (`check_radiator`).
- **Caption** for TikTok — one short teasing line that doesn't spoil the end, then 4–6 hashtags, e.g.
  `Never answer when she calls from the hallway. #horrorstory #scarystories #creepy #horrortok #animation`
