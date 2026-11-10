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
  one or two characters, a pet, simple props (format `cursed_object`: bright daytime rooms — classroom,
  office, shop, kitchen, waiting room — with silent background extras). No crowds fighting, no complex action, no gore.
- Accounts on another engine (`engine` in accounts.json, see `daily/studio/README.md`): `vintage` can also do
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

## Also produce
- **Title** — 2–4 words, in the style the format file gives.
- **slug** — lowercase, underscores, ≤ 20 chars (`check_radiator`).
- **Caption** for TikTok — one short teasing line that doesn't spoil the end, then 4–6 hashtags, e.g.
  `Never answer when she calls from the hallway. #horrorstory #scarystories #creepy #horrortok #animation`
