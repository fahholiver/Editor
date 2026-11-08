#!/usr/bin/env python3
"""Start a new Motion story from a story text: generate the voiceover, then set up the engine folder.

    python3 bootstrap.py <motion_repo_dir> <slug> "<Title>" <story.txt> [--provider ...] [--voice ...]

Same result as Motion's `new_story.py` (narration.wav, transcript_display.txt, words.json, render.py,
audio.py, gfx*.py, finalize.sh, verify_audio.py in <motion>/<slug>/), except that the narration is
synthesised here (voiceover.py) and the word times come from the TTS, so no forced alignment is needed.
Prints the word timings, the pauses and the frame count to plan the shots from.
"""
import argparse
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import voiceover  # noqa: E402

MUSIC_BED = '''
MUSIC_UNDER_DB = 15   # music this many dB under the narration (before the engine's extra ducking while it speaks)


def music_bed():
    """the channel's background track (music_bed.wav), looped, faded in/out, level relative to the narration"""
    p = os.path.join(HERE, 'music_bed.wav')
    if not os.path.exists(p):
        return np.zeros(N)
    with wave.open(p) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    x = x / (np.sqrt(np.mean(x ** 2)) + 1e-9)
    narr_rms = np.sqrt(np.mean(NARR[np.abs(NARR) > 0.01] ** 2)) if np.any(np.abs(NARR) > 0.01) else 0.1
    x = np.tile(x, N // len(x) + 1)[:N]
    f = np.minimum(1, np.minimum(np.arange(N), N - np.arange(N)) / (1.5 * SR))
    return x * f * narr_rms * 10 ** (-MUSIC_UNDER_DB / 20) / 0.3   # main() scales music by 0.3
'''

STYLE_HOOK_OLD = '''    draw_hud(ctx, t, opt)
    for al, c in flashes(t):
        ctx.rectangle(0, 0, W, H)
        ctx.set_source_rgba(*c, al)
        ctx.fill()
    draw_caption(ctx, t, opt.get('cap_y', 1400))
'''
STYLE_HOOK_NEW = '''    if STYLE:   # account visual style (daily/styles/<style>.py copied here as style.py)
        STYLE.after_scene(surf, W, H)
        for al, c in flashes(t):
            ctx.rectangle(0, 0, W, H)
            ctx.set_source_rgba(*c, al)
            ctx.fill()
        STYLE.bezel(ctx, W, H)
        STYLE.overlay(surf, W, H, lambda c: (draw_hud(c, t, opt), draw_caption(c, t, opt.get('cap_y', 1400)),
                                             STYLE.game_hud(c, t, DUR)))
    else:
''' + ''.join('    ' + l + '\n' for l in STYLE_HOOK_OLD.splitlines())


def apply_style(render_py, style, dest):
    """copy daily/styles/<style>.py to dest/style.py and hook it into render.py's render_frame"""
    import shutil
    shutil.copy(os.path.join(HERE, 'styles', style + '.py'), os.path.join(dest, 'style.py'))
    s = open(render_py).read()
    if 'STYLE.after_scene' not in s:
        assert STYLE_HOOK_OLD in s, 'render_frame changed - update STYLE_HOOK_OLD'
        s = s.replace(STYLE_HOOK_OLD, STYLE_HOOK_NEW)
        # caption key words in the style's colour (if it has one)
        s = s.replace("col = RED if (raw in KEY", "col = (getattr(STYLE, 'KEY_COLOR', None) or RED) if (raw in KEY")
        s = s.replace('    rgb = rgb * vignette() + grain(fi)\n',
                      '    rgb = rgb * vignette() + grain(fi)\n    if STYLE:\n        rgb = STYLE.post(rgb)\n')
        s = s.replace('\nFPS = 30\n', '\ntry:\n    import style as STYLE\nexcept ImportError:\n    STYLE = None\n'
                      'if STYLE and hasattr(STYLE, "font"):\n    font = STYLE.font  # captions in the style font\n\nFPS = 30\n', 1)
    open(render_py, 'w').write(s)


ENGINE_FILES = ('render.py', 'audio.py', 'finalize.sh', 'verify_audio.py', 'gfx.py', 'gfx_emma.py', 'gfx_adam.py')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('motion')
    ap.add_argument('slug')
    ap.add_argument('title')
    ap.add_argument('story')
    ap.add_argument('--provider', default='auto', choices=['auto', 'elevenlabs', 'edge'])
    ap.add_argument('--voice')
    ap.add_argument('--account', help='TikTok account: takes language/voices from daily/accounts.json')
    a = ap.parse_args()
    edge_voice = None
    import plan
    if a.account:
        c = plan.account_cfg(a.account)
        edge_voice = c.get('edge_voice')
        if c.get('elevenlabs_voice'):
            a.voice = a.voice or c['elevenlabs_voice']
        elif a.provider == 'auto':          # this account uses its Microsoft voice only
            a.provider, a.voice = 'edge', a.voice or edge_voice
        print('account %s: %s, voices %s / %s' % (a.account, c['language'], a.voice, edge_voice))

    tpl = os.path.join(a.motion, 'template')
    if not os.path.isdir(tpl):
        sys.exit('no template/ in %s - clone fahholiver/Motion (branch claude/radiator-animation) first' % a.motion)
    d = os.path.join(a.motion, a.slug)
    dur, sr, words = voiceover.build(a.story, d, a.provider, a.voice, edge_voice)

    for f in ENGINE_FILES:
        s = open(os.path.join(tpl, f)).read()
        s = s.replace('{{TITLE}}', a.title).replace('{{SLUG}}', a.slug).replace('{{SR}}', str(sr))
        if f == 'audio.py':  # background music track (daily/assets/background_music.*) under every story
            s = s.replace('    mus = build_music()\n', '    mus = build_music() + music_bed()\n')
            s = s.replace('\ndef main():', MUSIC_BED + '\n\ndef main():', 1)
        # the engine's audio check compares 20-30 s; make it fit short videos too
        s = s.replace('seg = slice(SR * 20, SR * 30)', 'seg = slice(n // 5, n // 5 + min(SR * 10, n // 2))')
        open(os.path.join(d, f), 'w').write(s)
    os.chmod(os.path.join(d, 'finalize.sh'), 0o755)
    if a.account and plan.account_cfg(a.account).get('format') == 'interactive_series':
        import shutil
        kit = open(os.path.join(HERE, 'styles', 'series_kit.py')).read().replace(
            "LANG = 'fr'", "LANG = '%s'" % plan.account_cfg(a.account)['language'][:2])
        open(os.path.join(d, 'kit.py'), 'w').write(kit)
        print('series kit: kit.py (part_tag, red_circle, choice_card)')
    style = plan.account_cfg(a.account).get('visual_style') if a.account else None
    if style:
        apply_style(os.path.join(d, 'render.py'), style, d)
        print('visual style:', style)
    bed = sorted(glob.glob(os.path.join(HERE, 'assets', 'background_music.*')))
    if not bed:  # the track lives in Google Drive (TikTok Daily/_assets) - the repo is public
        try:
            import gdrive
            if gdrive.configured():
                got = gdrive.get_asset('background_music.mp3', os.path.join(HERE, 'assets', 'background_music.mp3'))
                bed = [got] if got else []
        except Exception as e:  # noqa: BLE001
            print('WARNING: could not fetch the background music from Drive:', e)
    if bed:  # decoded at the narration's rate, mono
        subprocess.check_call(['ffmpeg', '-y', '-loglevel', 'error', '-i', bed[0], '-ac', '1', '-ar', str(sr),
                               '-c:a', 'pcm_s16le', os.path.join(d, 'music_bed.wav')])
        print('background music: %s' % os.path.basename(bed[0]))
    else:
        print('background music: none (put the track at daily/assets/background_music.mp3)')
    os.makedirs(os.path.join(a.motion, 'output'), exist_ok=True)

    lo, hi = (plan.account_cfg(a.account).get('seconds', [65, 125]) if a.account else [65, 125])
    if not lo <= dur <= hi:
        print('\n*** LENGTH %.1f s IS OUTSIDE %d-%d s: %s the story and run bootstrap again ***'
              % (dur, lo, hi, 'lengthen' if dur < lo else 'shorten'))
    print('\n%s: %.3f s @ %d Hz -> %d frames at 30 fps\n' % (a.slug, dur, sr, int(dur * 30)))
    print(' '.join('%s@%.2f' % (w[0], w[1]) for w in words))
    print('\npauses > 0.35 s:')
    for x, y in zip(words, words[1:]):
        if y[1] - x[2] > 0.35:
            print('  %.2f-%.2f  after "%s"' % (x[2], y[1], x[0]))
    print('\nnext: write shots in %s/render.py (SHOTS) and cues in %s/audio.py, then follow Motion CLAUDE.md'
          % (a.slug, a.slug))


if __name__ == '__main__':
    main()
