#!/usr/bin/env python3
"""Measure voice vs music loudness and suggest ONE fixed music volume for the whole video, plus check
the music is long enough for the voice-over timeline.

Usage: python3 loudness.py VOICE.f32 MUSIC.f32 [--sr 16000] [--gap 12] [--need SECONDS] [--music-total SECONDS]
  VOICE.f32 / MUSIC.f32 from `$BIN/pcm … 16000` (music = the excerpt that will be used)
  --gap          desired dB by which voice should sit above music (default 12)
  --need         required video length (intro + voice timeline end + outro)
  --music-total  length of the full song (to say whether a longer excerpt exists)
Voice level = RMS of speech-active frames only (pauses would drag it down); music = RMS of the whole
excerpt. Suggested CapCut volume = linear factor (1.0 = 100 %) for the music segment.
"""
import argparse
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("voice"); ap.add_argument("music"); ap.add_argument("--sr", type=int, default=16000)
ap.add_argument("--gap", type=float, default=12.0); ap.add_argument("--need", type=float); ap.add_argument("--music-total", type=float)
a = ap.parse_args(); sr = a.sr
def frames_db(x):
    hop = int(0.05 * sr); n = len(x) // hop
    return 20 * np.log10(np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-9)
v = np.fromfile(a.voice, dtype=np.float32); m = np.fromfile(a.music, dtype=np.float32)
vd = frames_db(v); th = max(np.percentile(vd, 15) + 10, np.percentile(vd, 98) - 30)
v_db = 10 * np.log10(np.mean(10 ** (vd[vd > th] / 10))); m_db = 10 * np.log10(np.mean(10 ** (frames_db(m) / 10)))
cut = max(0.0, a.gap - (v_db - m_db)); vol = float(np.clip(10 ** (-cut / 20), 0.05, 1.0))
print(f"giọng (lúc nói) {v_db:.1f} dB | nhạc {m_db:.1f} dB | chênh hiện tại {v_db - m_db:+.1f} dB")
print(f"ĐỀ XUẤT: giảm nhạc {cut:.1f} dB → âm lượng nhạc ≈ {vol*100:.0f}% (volume {vol:.2f}) để giọng to hơn nhạc {a.gap:.0f} dB")
if a.need:
    ml = len(m) / sr
    if ml >= a.need: print(f"Nhạc đủ dài: đoạn nhạc {ml:.1f}s ≥ cần {a.need:.1f}s")
    elif a.music_total and a.music_total >= a.need: print(f"CẢNH BÁO: đoạn nhạc {ml:.1f}s < cần {a.need:.1f}s — cả bài {a.music_total:.1f}s đủ: cắt đoạn dài hơn (nhac-cat-doan-do-beat)")
    else: print(f"CẢNH BÁO: nhạc không đủ dài ({ml:.1f}s, cả bài {a.music_total or '?'}s) cho {a.need:.1f}s — đề nghị người dùng chọn nhạc khác")
