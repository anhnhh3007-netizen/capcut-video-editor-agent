#!/usr/bin/env python3
"""Synthesize a royalty-free mechanical-keyboard typing track whose clicks land exactly on the frames where each
character of a typed line appears.

Usage: python3 typing_sfx.py "[osaka, katsuoji, kyoto]" OUT.wav TIMES.json --start 0.30 --end 4.4333 [--fps 30] [--seed 7]
        [--times-from spec_clicks.json]   (optional: reuse the sample's click rhythm, scaled to fit start→end)
  --start  time (s) the first character appears      --end  length of the WAV (= end of the intro)
Key intervals are humanised (2–4 frames, +2 after punctuation); space = deeper spacebar thump; every key has a press
transient + body + soft release. Peak normalised to −3 dBFS, 44.1 kHz stereo 16-bit.
TIMES.json = {"line", "times" (s, frame-snapped, one per character), "end"} → used by intro_build.py.
"""
import argparse, json, wave
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("line"); ap.add_argument("wav"); ap.add_argument("times")
ap.add_argument("--start", type=float, default=0.3); ap.add_argument("--end", type=float, required=True)
ap.add_argument("--fps", type=int, default=30); ap.add_argument("--seed", type=int, default=7); ap.add_argument("--type-until", type=float,
                help="finish typing by this time (default: 65%% of the intro)")
a = ap.parse_args(); rng = np.random.default_rng(a.seed); sr = 44100; FPS = a.fps
fr = round(a.start * FPS); times = []
for c in a.line:
    times.append(fr / FPS); fr += int(rng.choice([2, 3, 3, 3, 4])) + (2 if c in ",.;:" else 0)
limit = a.type_until or (a.start + (a.end - a.start) * 0.65)
if times[-1] > limit:                                       # compress to fit the intro, keep the humanised spacing
    k = (limit - a.start) / max(1e-6, times[-1] - a.start); times = [round((a.start + (t - a.start) * k) * FPS) / FPS for t in times]
if times[-1] >= a.end: raise SystemExit("dòng quá dài cho intro này — rút ngắn dòng")

def key(space=False):
    n = int(0.12 * sr); t = np.arange(n) / sr; y = np.zeros(n)
    nb = np.diff(np.r_[0, rng.normal(0, 1, int(0.003 * sr))]); y[:len(nb)] += 0.5 * nb * np.exp(-np.arange(len(nb)) / (0.0008 * sr))
    for f in rng.uniform(1900, 3400, 3): y += rng.uniform(.08, .16) * np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / 0.010)
    lf = rng.uniform(170, 260) if space else rng.uniform(320, 520)
    y += (0.45 if space else 0.25) * np.sin(2 * np.pi * lf * t) * np.exp(-t / (0.030 if space else 0.018))
    r = int(rng.uniform(0.045, 0.075) * sr); nb2 = np.diff(np.r_[0, rng.normal(0, 1, int(0.002 * sr))])
    y[r:r + len(nb2)] += 0.18 * nb2; y[r:] += 0.08 * np.sin(2 * np.pi * rng.uniform(2200, 3000) * t[:n - r]) * np.exp(-t[:n - r] / 0.006)
    return y * rng.uniform(0.75, 1.0)

L = int(a.end * sr); out = np.zeros(L + sr)
for c, tt in zip(a.line, times):
    k = key(c == " "); s = int(tt * sr); out[s:s + len(k)] += k
out = out[:L]; out = out / np.abs(out).max() * 10 ** (-3 / 20)
st = np.stack([out, np.roll(out, int(0.0004 * sr))], 1)
w = wave.open(a.wav, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((st * 32767).astype("<i2").tobytes()); w.close()
json.dump({"line": a.line, "times": times, "end": a.end}, open(a.times, "w"), ensure_ascii=False)
print(f"{len(a.line)} phím, {times[0]:.2f}s → {times[-1]:.2f}s, file {a.wav}")
