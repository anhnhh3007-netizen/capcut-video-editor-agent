#!/usr/bin/env python3
"""Find high-frequency click onsets (keyboard typing SFX, shutter clicks) in a sample's audio.

Usage: python3 typing_onsets.py AUDIO.f32 [SR=22050] [MAX_SECONDS=10]
  AUDIO.f32 from `$BIN/pcm sample_audio.m4a AUDIO.f32 22050`
Prints onset times (>2 kHz spectral flux peaks) and a per-0.5 s table of loudness and
high/low energy ratio — bursts of tightly spaced onsets (30–100 ms apart) that line up with
text appearing on screen = typing sound.
"""
import sys, numpy as np
x = np.fromfile(sys.argv[1], dtype=np.float32); sr = int(sys.argv[2]) if len(sys.argv) > 2 else 22050
T = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
x = x[:int(T * sr)]; hop, win = 256, 1024
fr = np.lib.stride_tricks.sliding_window_view(x, win)[::hop] * np.hanning(win)
S = np.abs(np.fft.rfft(fr, axis=1)); f = np.fft.rfftfreq(win, 1 / sr)
flux = np.maximum(np.diff(np.log1p(S[:, f > 2000]), axis=0), 0).sum(1)
th = np.median(flux) * 4; t = np.arange(len(flux)) * hop / sr
on = [round(float(t[i]), 2) for i in range(1, len(flux) - 1) if flux[i] > th and flux[i] >= flux[i - 1] and flux[i] >= flux[i + 1]]
print("onsets:", on)
hi = S[:, f > 3000].sum(1); lo = S[:, f < 300].sum(1)
for s in np.arange(0, T, 0.5):
    a, b = int(s * sr / hop), int((s + .5) * sr / hop); seg = x[int(s * sr):int((s + .5) * sr)]
    if len(seg) == 0: break
    print(f"{s:4.1f}s  {20*np.log10(np.sqrt(np.mean(seg**2))+1e-9):6.1f} dB  hi/lo {hi[a:b].mean()/(lo[a:b].mean()+1e-9):.2f}  clicks {sum(1 for o in on if s <= o < s + .5)}")
