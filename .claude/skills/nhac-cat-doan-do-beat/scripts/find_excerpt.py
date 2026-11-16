#!/usr/bin/env python3
"""Locate where a short excerpt (music taken from a sample video) sits inside the full song.

Usage: python3 find_excerpt.py SONG.f32 EXCERPT.f32 [SR=11025]
  both from `$BIN/pcm file out.f32 11025`
Uses log-spectral band features (robust to re-encoding; raw waveform correlation is NOT —
it gave corr 0.03 on the real case), scans speed ratios 0.85–1.20 for sped-up TikTok audio,
then verifies 6 s chunks one by one. Prints: offset in song, speed ratio, per-chunk drift.
Cut the song from OFFSET to OFFSET + excerpt_len * ratio with `$BIN/audio_cut`.
"""
import sys, numpy as np
sr = int(sys.argv[3]) if len(sys.argv) > 3 else 11025
song = np.fromfile(sys.argv[1], dtype=np.float32); ref = np.fromfile(sys.argv[2], dtype=np.float32)
HOP = 256
def feat(x, win=1024):
    fr = np.lib.stride_tricks.sliding_window_view(x, win)[::HOP] * np.hanning(win)
    S = np.abs(np.fft.rfft(fr, axis=1))[:, :256]
    b = np.log1p(S.reshape(len(S), 32, 8).sum(2)); return b - b.mean(1, keepdims=True)
Fs, Fr = feat(song), feat(ref); hop = HOP / sr
def best_offset(R, step=1):
    L = len(R); nr = np.linalg.norm(R); best = (-9, 0)
    for o in range(0, len(Fs) - L, step):
        seg = Fs[o:o + L]; c = np.sum(seg * R) / (np.linalg.norm(seg) * nr + 1e-9)
        if c > best[0]: best = (c, o)
    return best
best = None
for r in np.arange(0.85, 1.21, 0.01):
    idx = np.clip((np.arange(int(len(Fr) * r)) / r).astype(int), 0, len(Fr) - 1)
    c, o = best_offset(Fr[idx], step=4)
    if best is None or c > best[0]: best = (c, o, r)
c, o, r = best
print(f"best: offset {o*hop:.2f}s  speed ratio {r:.2f}  corr {c:.3f}   (corr > 0.6 = khớp tốt)")
L = int(6 / hop); drift = []
for st in range(0, int(len(ref) / sr) - 6, 6):
    cc, oo = best_offset(Fr[int(st / hop):int(st / hop) + L])
    drift.append(oo * hop - st); print(f"  mẫu {st:3d}s -> bài {oo*hop:7.2f}s  (lệch {oo*hop-st:6.2f})  corr {cc:.2f}")
if len(drift) > 1:
    rate = (drift[-1] - drift[0]) / (6 * (len(drift) - 1)) + 1
    print(f"suggest: start {drift[0]:.2f}s, end {drift[0] + len(ref)/sr*rate:.2f}s  (tốc độ mẫu/bài ≈ {1/rate:.4f})")
