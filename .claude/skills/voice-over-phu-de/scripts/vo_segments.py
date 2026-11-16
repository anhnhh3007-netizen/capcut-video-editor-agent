#!/usr/bin/env python3
"""Split a voice-over (or a clip's original speech) into spoken phrases by its pauses, and plan how to
drop long silences WITHOUT re-encoding (CapCut plays several segments of the same file).

Usage: python3 vo_segments.py AUDIO.f32 OUT.json [--sr 16000] [--file /path/original/voice.m4a]
          [--window START END] [--offset T] [--max-gap 0.30] [--min-pause 0.35] [--pad 0.08]
  AUDIO.f32  from `$BIN/pcm voice.m4a AUDIO.f32 16000` (for a clip: `$BIN/audio_extract clip.MP4 a.m4a` first)
  --file     path recorded in OUT.json (the real audio CapCut will use)
  --window   only analyse [START, END] s of the audio (e.g. the used part of a clip)
  --offset   timeline time (s) where this audio starts (VO start after the intro, or the shot start)
  --max-gap  pauses longer than this are shortened to it (0 = keep original timing, use for clip speech)
OUT.json: {"file", "phrases": [{"src_start","src_end","tl_start","tl_end"}], "speech_total", "timeline_end"}
A phrase = speech separated by a pause ≥ --min-pause; these are the candidate subtitle boundaries.
"""
import argparse, json
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("audio"); ap.add_argument("out"); ap.add_argument("--sr", type=int, default=16000)
ap.add_argument("--file", default=""); ap.add_argument("--window", nargs=2, type=float); ap.add_argument("--offset", type=float, default=0.0)
ap.add_argument("--max-gap", type=float, default=0.30); ap.add_argument("--min-pause", type=float, default=0.35); ap.add_argument("--pad", type=float, default=0.08)
a = ap.parse_args()
x = np.fromfile(a.audio, dtype=np.float32); sr = a.sr; base = 0.0
if a.window: base = a.window[0]; x = x[int(a.window[0] * sr):int(a.window[1] * sr)]
hop = int(0.02 * sr); n = len(x) // hop
db = 20 * np.log10(np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9)
floor = np.percentile(db, 15); peak = np.percentile(db, 98)
th = max(floor + 10, peak - 35)
act = db > th
# fill tiny holes (<0.15 s) and drop blips (<0.08 s)
def runs(mask):
    r, i = [], 0
    while i < len(mask):
        j = i
        while j < len(mask) and mask[j] == mask[i]: j += 1
        r.append((bool(mask[i]), i, j)); i = j
    return r
for v, i, j in runs(act):
    if not v and (j - i) * 0.02 < 0.15 and i > 0 and j < len(act): act[i:j] = True
for v, i, j in runs(act):
    if v and (j - i) * 0.02 < 0.08: act[i:j] = False
sp = [(i * 0.02, j * 0.02) for v, i, j in runs(act) if v]
# merge into phrases at pauses < min_pause
ph = []
for s, e in sp:
    if ph and s - ph[-1][1] < a.min_pause: ph[-1][1] = e
    else: ph.append([s, e])
dur = len(x) / sr
ph = [[max(0, s - a.pad), min(dur, e + a.pad)] for s, e in ph]
out, t = [], a.offset
for k, (s, e) in enumerate(ph):
    if k:
        gap = s - ph[k - 1][1]
        t += min(gap, a.max_gap) if a.max_gap > 0 else gap
    elif a.max_gap == 0: t += s
    out.append({"src_start": round(base + s, 3), "src_end": round(base + e, 3), "tl_start": round(t, 3), "tl_end": round(t + e - s, 3)})
    t += e - s
res = {"file": a.file, "phrases": out, "speech_total": round(sum(e - s for s, e in ph), 3), "timeline_end": round(t, 3)}
json.dump(res, open(a.out, "w"), indent=1, ensure_ascii=False)
print(f"{len(out)} cụm lời | nói {res['speech_total']:.1f}s | gốc {dur:.1f}s → trên timeline {a.offset:.2f}–{t:.2f}s (ngưỡng {th:.0f} dB)")
for k, p in enumerate(out, 1): print(f"  {k:2d}. {p['tl_start']:7.2f}–{p['tl_end']:7.2f}s  (nguồn {p['src_start']:.2f}–{p['src_end']:.2f})")
