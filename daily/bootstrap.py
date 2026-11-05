#!/usr/bin/env python3
"""Start a new Motion story from a story text: generate the voiceover, then set up the engine folder.

    python3 bootstrap.py <motion_repo_dir> <slug> "<Title>" <story.txt> [--provider ...] [--voice ...]

Same result as Motion's `new_story.py` (narration.wav, transcript_display.txt, words.json, render.py,
audio.py, gfx*.py, finalize.sh, verify_audio.py in <motion>/<slug>/), except that the narration is
synthesised here (voiceover.py) and the word times come from the TTS, so no forced alignment is needed.
Prints the word timings, the pauses and the frame count to plan the shots from.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import voiceover  # noqa: E402

ENGINE_FILES = ('render.py', 'audio.py', 'finalize.sh', 'verify_audio.py', 'gfx.py', 'gfx_emma.py', 'gfx_adam.py')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('motion')
    ap.add_argument('slug')
    ap.add_argument('title')
    ap.add_argument('story')
    ap.add_argument('--provider', default='auto', choices=['auto', 'elevenlabs', 'edge'])
    ap.add_argument('--voice')
    a = ap.parse_args()

    tpl = os.path.join(a.motion, 'template')
    if not os.path.isdir(tpl):
        sys.exit('no template/ in %s - clone fahholiver/Motion (branch claude/radiator-animation) first' % a.motion)
    d = os.path.join(a.motion, a.slug)
    dur, sr, words = voiceover.build(a.story, d, a.provider, a.voice)

    for f in ENGINE_FILES:
        s = open(os.path.join(tpl, f)).read()
        s = s.replace('{{TITLE}}', a.title).replace('{{SLUG}}', a.slug).replace('{{SR}}', str(sr))
        # the engine's audio check compares 20-30 s; make it fit short videos too
        s = s.replace('seg = slice(SR * 20, SR * 30)', 'seg = slice(n // 5, n // 5 + min(SR * 10, n // 2))')
        open(os.path.join(d, f), 'w').write(s)
    os.chmod(os.path.join(d, 'finalize.sh'), 0o755)
    os.makedirs(os.path.join(a.motion, 'output'), exist_ok=True)

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
