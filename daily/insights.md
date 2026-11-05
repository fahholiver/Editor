# Insights — what works (updated by the daily run from `daily/metrics.py`)

The daily run reads this before writing stories and adds what the latest numbers teach. Keep it short:
facts with numbers, then the rule we follow because of them. Judge a post only after ~2 days.

## Baseline (2026-11-05, last 60 days)
- **mandraketoons**: the 2D horror shorts ("What if?" captions, #animation #terror #whatif #tiktokuk) are
  the account's best by far — 1,000–5,000 views and 20–33 s average watch, vs ~300–600 views / 6–14 s for its
  older AI-fruit/alien/comedy posts. Best: the neighbours story (5,054 views, 33 s avg, 204 likes).
  → Keep the 2D horror format; caption opens with a short "What if…?" style question.
- **anna.20263**: history is UK news/celebrity (median 720 views, 9 s avg). Switching to German horror resets
  the audience: expect a few weak days before TikTok finds German viewers; don't judge the format on week 1.
- **user890997140**: no history yet (first post 2026-11-05).
- Retention: ~20–33 s average on 70–90 s videos ≈ 30–40 % watch-through. The first 3 seconds (hook line +
  fast cuts) decide it.

## Voices (fixed per account — always use these)
| account | voice | since |
|---|---|---|
| mandraketoons (UK) | ElevenLabs **George** `JBFqnCBsd6RMkjVDRZzb` (fallback Edge en-GB-ThomasNeural) | 2026-11-05 |
| anna.20263 (DE) | Microsoft **de-DE-ConradNeural** (Edge) — owner's choice | 2026-11-06 |
| user890997140 (FR) | ElevenLabs **Callum** `N2lVS1w4EtoT3dr4eOWO`, verified French (fallback Edge fr-FR-HenriNeural) — less common | 2026-11-06 |
Not Daniel. Edge voices at -7 % speed for horror pacing. Before: DE Florian, FR Rémy (2026-11-05 only).
Free ElevenLabs keys ≈ 10k characters/month each; George + Callum need ≈ 2,200/day, so the free credit lasts
~2 weeks a month — after that the fallback voice is used until the credit resets (or a paid plan is added).

## Background music (owner's choice 2026-11-05)
"Horror music box" (Pixabay, leberch 585986), stored in Drive `TikTok Daily/_assets/background_music.mp3`,
looped under every video, subtle: about 18 dB under the narration and ducked further while the voice speaks.

## Rules in force
0. Every video 65–125 s (owner's rule, 2026-11-05).
1. Hook in the first line, under 3 s, a concrete threat; first shot already shows it.
2. Caption = one teasing question/line + 4–6 hashtags (local language tags + #animation #horrortok).
3. Change one thing at a time per account and note it here with the date, so the effect can be measured.
