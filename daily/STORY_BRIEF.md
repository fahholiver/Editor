# Story brief — rules for every daily short (vertical, ~60–90 s, in the account's language)

The story is the narration script for one Motion video. It is read by a TTS voice exactly as written, and
every word becomes a karaoke caption, so write for the ear.

## Shape
Each TikTok account has its own **format** (see `daily/accounts.json`). The format file in
`daily/formats/<format>.md` gives the shape, voice and title style; the rules below apply to every format.

## Rules
- Length: the `words` range of the account in `daily/accounts.json` (≈ 60–90 s of narration). One sentence or short beat per line; blank lines only for a
  longer pause (a paragraph break = ~0.75 s silence, a line break = ~0.45 s).
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
