#!/usr/bin/env python3
"""Generate the voiceover for a story + word timings in the format the Motion engine expects.

    python3 voiceover.py <story.txt> <out_dir> [--provider auto|elevenlabs|edge] [--voice NAME]

Writes to <out_dir>:
  narration.wav            mono 16-bit PCM (the engine's narration track; render.py/audio.py read it)
  narration_original.mp3   the same audio as MP3 (for reference / listening)
  transcript_display.txt   the story text exactly as given (used for captions)
  words.json               [display token, start, end] per whitespace token of transcript_display.txt

Each non-empty line of the story is synthesised separately and joined with a short silence, so the pacing
follows the line breaks (a horror narration lives on its pauses). Word times come straight from the TTS
(no forced alignment needed):
  * ElevenLabs  (/with-timestamps, character alignment) if ELEVENLABS_API_KEY is set  -> best quality
  * Microsoft Edge neural voices via `edge-tts` (WordBoundary events)                 -> free, no key
"""
import argparse
import asyncio
import base64
import difflib
import json
import os
import re
import subprocess
import sys
import tempfile
import wave

import numpy as np

SR = 44100                      # one fixed rate for every line; the engine keeps whatever rate it finds
GAP_LINE = 0.45                 # silence between lines (s)
GAP_PARAGRAPH = 0.75            # silence after a blank line / after the opening hook line
TAIL = 0.6                      # silence at the very end
PEAK = 10 ** (-1.0 / 20)        # normalise the finished narration to -1 dBFS peak

EDGE_DEFAULT_VOICE = 'en-GB-RyanNeural'          # calm British male, matches the existing stories
ELEVEN_DEFAULT_VOICE = 'onwK4e9ZLuTAKqWW03F9'    # "Daniel" (British, deep narrator) from the default library
ELEVEN_MODEL = 'eleven_multilingual_v2'


# ------------------------------------------------------------------ text helpers

def norm_chars(s):
    """lower-case alphanumerics only - what we compare between the story text and the TTS output"""
    return re.sub(r'[^0-9a-z]', '', s.lower().replace('’', "'"))


def map_tokens(tokens, units):
    """tokens: display tokens of one line. units: [(text, start, end)] from the TTS (words or characters).
    Returns [(token, start, end)] by aligning the normalised character streams of both sides
    (robust to the TTS spelling out numbers, dropping punctuation, etc.)."""
    a_chars, a_owner = [], []
    for i, t in enumerate(tokens):
        for c in norm_chars(t):
            a_chars.append(c)
            a_owner.append(i)
    b_chars, b_time = [], []
    for text, s, e in units:
        n = norm_chars(text)
        for k, c in enumerate(n):
            b_chars.append(c)
            # spread the unit's span over its characters
            b_time.append((s + (e - s) * k / len(n), s + (e - s) * (k + 1) / len(n)))
    times = [[None, None] for _ in tokens]
    sm = difflib.SequenceMatcher(None, a_chars, b_chars, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            pairs = zip(range(i1, i2), range(j1, j2))
        elif tag == 'replace':  # e.g. "36000" vs "thirtysixthousand": stretch proportionally
            pairs = ((i1 + (k * (i2 - i1)) // max(1, j2 - j1), j1 + k) for k in range(j2 - j1))
        else:
            continue
        for ia, jb in pairs:
            tk = a_owner[ia]
            s, e = b_time[jb]
            if times[tk][0] is None or s < times[tk][0]:
                times[tk][0] = s
            if times[tk][1] is None or e > times[tk][1]:
                times[tk][1] = e
    # tokens that got no time (punctuation-only, or unmatched): inherit from neighbours
    out, last_end = [], (units[0][1] if units else 0.0)
    for tk, (s, e) in zip(tokens, times):
        if s is None:
            s = e = last_end
        s = max(s, last_end - 0.02) if out else s
        out.append([tk, s, max(e, s)])
        last_end = out[-1][2]
    return out


# ------------------------------------------------------------------ audio helpers

def decode_to_pcm(path):
    raw = subprocess.check_output(['ffmpeg', '-loglevel', 'error', '-i', path, '-f', 's16le', '-ac', '1',
                                   '-ar', str(SR), '-'])
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def trim(x, thr=10 ** (-50 / 20)):
    """cut leading/trailing silence; returns (audio, seconds cut at the start)"""
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx):
        return x, 0.0
    a = max(0, idx[0] - int(0.01 * SR))
    b = min(len(x), idx[-1] + int(0.04 * SR))
    return x[a:b], a / SR


# ------------------------------------------------------------------ providers

def tts_edge(text, voice, mp3_path):
    import edge_tts

    async def run():
        kw = dict(boundary='WordBoundary')
        proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
        if proxy:
            kw['proxy'] = proxy  # aiohttp ignores the proxy env vars on its own
        com = edge_tts.Communicate(text, voice, rate='-4%', **kw)
        units = []
        with open(mp3_path, 'wb') as f:
            async for ch in com.stream():
                if ch['type'] == 'audio':
                    f.write(ch['data'])
                elif ch['type'] == 'WordBoundary':
                    s = ch['offset'] / 1e7
                    units.append((ch['text'], s, s + ch['duration'] / 1e7))
        return units

    for attempt in range(3):
        try:
            return asyncio.run(asyncio.wait_for(run(), 60))
        except Exception as e:  # noqa: BLE001 - network hiccups: retry
            if attempt == 2:
                raise
            print('  edge-tts retry after error:', e, file=sys.stderr)


def tts_elevenlabs(text, voice, mp3_path, prev_text=None, next_text=None):
    import requests
    body = {'text': text, 'model_id': ELEVEN_MODEL,
            'voice_settings': {'stability': 0.55, 'similarity_boost': 0.8, 'style': 0.15, 'speed': 0.95}}
    if prev_text:
        body['previous_text'] = prev_text   # keeps intonation continuous across separately rendered lines
    if next_text:
        body['next_text'] = next_text
    r = requests.post('https://api.elevenlabs.io/v1/text-to-speech/%s/with-timestamps' % voice,
                      params={'output_format': 'mp3_44100_128'},
                      headers={'xi-api-key': os.environ['ELEVENLABS_API_KEY']}, json=body, timeout=120)
    if r.status_code != 200:
        raise RuntimeError('ElevenLabs %d: %s' % (r.status_code, r.text[:400]))
    j = r.json()
    open(mp3_path, 'wb').write(base64.b64decode(j['audio_base64']))
    al = j.get('alignment') or j.get('normalized_alignment')
    return list(zip(al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']))


# ------------------------------------------------------------------ main

def build(story_path, out_dir, provider='auto', voice=None):
    text = open(story_path, encoding='utf-8').read().strip()
    lines = text.split('\n')
    if provider == 'auto':
        provider = 'elevenlabs' if os.environ.get('ELEVENLABS_API_KEY') else 'edge'
    voice = voice or (ELEVEN_DEFAULT_VOICE if provider == 'elevenlabs' else EDGE_DEFAULT_VOICE)
    os.makedirs(out_dir, exist_ok=True)
    print('voiceover: %s / %s' % (provider, voice))

    spoken = [(i, ln.strip()) for i, ln in enumerate(lines) if ln.strip()]
    pieces, words, t = [], [], 0.0
    with tempfile.TemporaryDirectory() as tmp:
        for k, (li, ln) in enumerate(spoken):
            mp3 = os.path.join(tmp, '%03d.mp3' % k)
            if provider == 'elevenlabs':
                units = tts_elevenlabs(ln, voice, mp3, spoken[k - 1][1] if k else None,
                                       spoken[k + 1][1] if k + 1 < len(spoken) else None)
            else:
                units = tts_edge(ln, voice, mp3)
            x, cut = trim(decode_to_pcm(mp3))
            dur = len(x) / SR
            units = [(u, min(max(s - cut, 0), dur), min(max(e - cut, 0), dur)) for u, s, e in units]
            for tk, s, e in map_tokens(ln.split(), units):
                words.append([tk, round(t + s, 3), round(t + e, 3)])
            pieces.append(x)
            t += dur
            # pause after this line: longer after the hook (first line) and at paragraph breaks
            nxt = spoken[k + 1][0] if k + 1 < len(spoken) else None
            gap = TAIL if nxt is None else (GAP_PARAGRAPH if (k == 0 or nxt - li > 1) else GAP_LINE)
            pieces.append(np.zeros(int(gap * SR), np.float32))
            t += int(gap * SR) / SR
            print('  %5.2fs  %s' % (dur, ln[:70]))

    audio = np.concatenate(pieces)
    audio *= PEAK / max(1e-6, float(np.abs(audio).max()))
    pcm = (np.clip(audio, -1, 1) * 32767).astype(np.int16)
    wav = os.path.join(out_dir, 'narration.wav')
    with wave.open(wav, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    subprocess.check_call(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-c:a', 'libmp3lame', '-b:a', '192k',
                           os.path.join(out_dir, 'narration_original.mp3')])
    # captions use the whole text with single spaces/newlines exactly as written
    open(os.path.join(out_dir, 'transcript_display.txt'), 'w', encoding='utf-8').write(text + '\n')
    assert len(words) == len(text.split()), 'token count mismatch'
    json.dump(words, open(os.path.join(out_dir, 'words.json'), 'w'), ensure_ascii=False)
    total = len(pcm) / SR
    print('narration: %.2f s @ %d Hz, %d words -> %s' % (total, SR, len(words), out_dir))
    return total, SR, words


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('story')
    ap.add_argument('out_dir')
    ap.add_argument('--provider', default='auto', choices=['auto', 'elevenlabs', 'edge'])
    ap.add_argument('--voice')
    a = ap.parse_args()
    build(a.story, a.out_dir, a.provider, a.voice)
