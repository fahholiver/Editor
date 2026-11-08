# Visual styles (repertoire)

Set per account in `daily/accounts.json` as `"visual_style": "<name>"`; `bootstrap.py` hooks it into the engine.
No `visual_style` = the default Motion look (flat 2D, dark slate/teal, red key words).

| style | look | reference | used by |
|---|---|---|---|
| `pixel_arcade` | 16-bit pixel game: pixelated scene, 32-colour palette, pixel captions, health-bar HUD, console bezel, scanlines | jared_tomkins + operationco (2026-11-08) | anna.20263 |
| `cinematic_cartoon` | desaturated cinematic 2D, teal shadows, night→dawn colour arc (`style.DAWN`), white captions with one yellow key word, close-ups of hands/objects, slow push-ins, "THE END — …?" card | gas-station "FINAL PART" (2026-11-08) | — (available) |

| `map_kit` (helper) | talking-map look: continuous zoom/pan camera, cartoon faces on any shape (`face`, 8 moods, blink), serif years with arrows, crown, place tags, colour-fill spread, page-turn wipe | GeoGlobeTales Short (2026-11-08) | — (available; `face()` also fits horror objects/houses) |

Helpers for formats (not styles): `series_kit.py` → copied as `kit.py` for `interactive_series` accounts;
`object_kit.py` → copied as `kit.py` for `cursed_object` accounts (hip_sway, head_lag, flash, question_mark, end_pills);
`map_kit.py` → copied as `kit.py` for `map_tales` accounts (any SHOTS may also import its `face()`).
