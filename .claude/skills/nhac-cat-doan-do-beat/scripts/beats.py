#!/usr/bin/env python3
"""Tempo + beat grid for a music excerpt, written for beat-matched editing.

Usage: python3 beats.py EXCERPT.f32 OUT_DIR [SR=11025] [--cuts SAMPLE_CUTS.txt]
Writes OUT_DIR/beats.txt (seconds, one per line) and OUT_DIR/beat_markers_<bpm>bpm.csv
(beat, giay, phach_trong_o_nhip). Prints BPM, first beat, loudness per bar (4 beats) to find
drops/sections, and — with --cuts — how many of the sample video's cuts fall on beat/half-beat.
The grid is constant-tempo (fine for pop/disco); check that BPM matches the song's known tempo.
"""
import sys, os, argparse, numpy as np
ap = argparse.ArgumentParser(); ap.add_argument("audio"); ap.add_argument("out"); ap.add_argument("sr", nargs="?", type=int, default=11025)
ap.add_argument("--cuts"); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
sr = a.sr; x = np.fromfile(a.audio, dtype=np.float32); hop, win = 128, 1024
fr = np.lib.stride_tricks.sliding_window_view(x, win)[::hop] * np.hanning(win)
S = np.log1p(10 * np.abs(np.fft.rfft(fr, axis=1)))
flux = np.r_[0, np.maximum(np.diff(S, axis=0), 0).sum(1)]
flux = np.maximum(flux - np.convolve(flux, np.ones(16) / 16, "same"), 0); fps = sr / hop
ac = np.correlate(flux, flux, "full")[len(flux) - 1:]; lags = np.arange(1, len(ac)) / fps; bpm = 60 / lags
m = (bpm > 70) & (bpm < 180); cand = np.argsort(ac[1:][m])[::-1][:5]
print("tempo candidates:", [round(float(bpm[m][c]), 1) for c in cand])
T0 = 60 / bpm[m][cand[0]]; best = None; dur = len(x) / sr
for t in np.arange(T0 * 0.98, T0 * 1.02, 0.0005):
    for ph in np.arange(0, t, 0.005):
        idx = (np.arange(ph, dur, t) * fps).astype(int); idx = idx[idx < len(flux)]
        s = flux[idx].mean()
        if best is None or s > best[0]: best = (s, t, ph)
_, t, ph = best; B = 60 / t
beats = np.arange(ph, dur, t)
print(f"BPM {B:.2f} | 1 phách {t:.4f}s | nửa phách {t/2:.4f}s | phách đầu {ph:.3f}s | {len(beats)} phách / {dur:.2f}s")
np.savetxt(os.path.join(a.out, "beats.txt"), beats, fmt="%.3f")
with open(os.path.join(a.out, f"beat_markers_{B:.1f}bpm.csv"), "w") as o:
    o.write("beat,giay,phach_trong_o_nhip\n")
    for i, b in enumerate(beats): o.write(f"{i+1},{b:.3f},{i%4+1}\n")
for i in range(0, len(beats) - 1, 4):
    s, e = int(beats[i] * sr), int(beats[min(i + 4, len(beats) - 1)] * sr)
    db = 20 * np.log10(np.sqrt(np.mean(x[s:e] ** 2)) + 1e-9)
    print(f"bar {i//4+1:2d} {beats[i]:6.2f}s {db:6.1f} dB " + "#" * int(max(0, db + 30)))
if a.cuts:
    c = np.array([float(l) for l in open(a.cuts)]); grid = np.r_[beats, beats + t / 2]
    d = np.array([np.min(np.abs(v - grid)) for v in c]); print(f"mẫu: {(d < 0.06).sum()}/{len(c)} điểm cắt nằm trên phách/nửa phách (±60ms)")
