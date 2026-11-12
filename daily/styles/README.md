# Visual styles and format helpers (Motion engine)

`"visual_style": "<name>"` in `daily/accounts.json`; `bootstrap.py` hooks it in. None = the default Motion look.

| file | what | used by |
|---|---|---|
| `pixel_arcade.py` | 16-bit pixel game: pixelated scene, 32-colour palette, pixel captions, health-bar HUD, bezel, scanlines | anna.20263 |
| `series_kit.py` | `interactive_series` helpers: `part_tag`, `red_circle`, `choice_card` (copied as `kit.py`; the cartoon engine draws them with `studio/tools/overlay.py`) | user890997140 |

Other engines (vintage, vox, cartoon) are made with `daily/studio.py`, see `daily/studio/README.md`.
Removed looks (cinematic_cartoon, map_kit, object_kit) are in the git history if a format needs them again.
