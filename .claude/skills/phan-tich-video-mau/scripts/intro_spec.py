#!/usr/bin/env python3
"""Measure the INTRO of a reference video and write a reusable spec (intro_spec.json).

Usage: python3 intro_spec.py SAMPLE.mp4 OUT_DIR --bin "$BIN" [--max 10] [--end SECONDS]
Measures (no guessing from the model):
  - cuts (frame-difference on 0.04 s frames) and each shot's length
  - intro end: when the title overlay disappears (pixels that stay identical across different shots
    = overlay text/sticker); override with --end if the auto value is wrong
  - title overlay: bounding box (0–1 of frame), mean colour of the text pixels, and the times the overlay
    grows (= characters/words appearing → typewriter) vs appears at once
  - the sample's music: BPM + first beat → every shot length also expressed in BEATS (so the rhythm
    transfers to another song); click/typing onsets inside the intro
  - per shot: brightness, saturation, colourfulness, motion inside the shot, dominant hue, mid-frame jpg
Writes OUT_DIR/intro_spec.json, OUT_DIR/shot_XX.jpg, OUT_DIR/intro_sheet.jpg (read it to label shot types).
"""
import argparse, colorsys, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser(); ap.add_argument("video"); ap.add_argument("out"); ap.add_argument("--bin", required=True)
ap.add_argument("--max", type=float, default=10.0, help="seconds of the sample to analyse"); ap.add_argument("--end", type=float)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); STEP = 0.04
fr_dir = os.path.join(a.out, "_frames"); os.makedirs(fr_dir, exist_ok=True)
for f in os.listdir(fr_dir): os.remove(os.path.join(fr_dir, f))
# frames 0.04 s (only first --max seconds are used)
subprocess.run([os.path.join(a.bin, "dense"), a.video, fr_dir, str(STEP), "320"], check=True, capture_output=True)
fs = sorted(f for f in os.listdir(fr_dir) if f.endswith(".jpg"))[: int(a.max / STEP) + 1]
F = np.stack([np.asarray(Image.open(os.path.join(fr_dir, f)).convert("RGB").resize((90, 160) if Image.open(os.path.join(fr_dir, fs[0])).height > Image.open(os.path.join(fr_dir, fs[0])).width else (160, 90)), dtype=np.float32) for f in fs])
T = len(F); H, W = F.shape[1:3]
# --- cuts
diff = np.abs(F[1:] - F[:-1]).mean(axis=(1, 2, 3)); med = np.median(diff); cuts = [0]
for i, d in enumerate(diff, 1):
    if d > max(22, med * 4) and (i - cuts[-1]) * STEP > 0.15: cuts.append(i)
# --- overlay mask: pixels nearly constant across shot middles while the shots differ
mids = [(cuts[k] + (cuts[k + 1] if k + 1 < len(cuts) else T)) // 2 for k in range(len(cuts))]
if len(mids) >= 3:
    M = F[mids[: min(len(mids), 4)]]          # overlay = what the FIRST shots share (later scenes have their own captions)
    stab = M.std(axis=0).mean(axis=2) < 10
    bright = M.mean(axis=0).mean(axis=2)
    mask = stab & ((bright > 150) | (bright < 60))
else: mask = np.zeros((H, W), bool)
ref = F[mids[: min(len(mids), 4)]].mean(axis=0) if mask.any() else None
present = []
for t in range(T):
    if ref is None: present.append(0.0); continue
    present.append(float((np.abs(F[t][mask] - ref[mask]).mean(axis=1) < 18).mean()))
present = np.array(present)
end_i = None
if a.end: end_i = int(a.end / STEP)
elif mask.sum() > 30:
    on = present > 0.5
    # intro ends where the overlay is gone for >= 0.2 s (not the last time it flickers back)
    run = int(0.2 / STEP); end_i = None
    for t in range(1, T - run):
        if on[t - 1] and not on[t:t + run].any(): end_i = t; break
    if end_i is None and on.any(): end_i = int(np.where(on)[0][-1]) + 1
if end_i is None: end_i = cuts[min(len(cuts) - 1, 8)] if len(cuts) > 1 else T
end_i = min(end_i, T); intro_end = round(end_i * STEP, 3)
# snap intro end to the nearest cut after the overlay leaves
after = [c for c in cuts if c >= end_i - 3]; intro_end_cut = round((after[0] if after else end_i) * STEP, 3)
# --- title box + colour + growth (typewriter) inside the intro
title = None
if mask.any():
    ys, xs = np.where(mask); box = [round(xs.min() / W, 3), round(ys.min() / H, 3), round((xs.max() + 1) / W, 3), round((ys.max() + 1) / H, 3)]
    col = ref[mask].mean(axis=0); hexcol = "#%02X%02X%02X" % tuple(int(c) for c in col)
    # growth: count of overlay pixels matching ref per frame (rising steps = characters appearing)
    cnt = np.array([(np.abs(F[t][mask] - ref[mask]).mean(axis=1) < 18).sum() for t in range(end_i)])
    steps = [round(t * STEP, 2) for t in range(1, len(cnt)) if cnt[t] - cnt[t - 1] > max(3, 0.01 * mask.sum())]
    title = {"box": box, "color": hexcol, "appears_at": round(float(np.argmax(cnt > 0.3 * mask.sum())) * STEP, 2) if (cnt > 0.3 * mask.sum()).any() else 0.0,
             "growth_steps": steps, "kind": "typewriter" if len(steps) >= 4 else "static"}
# --- audio: BPM, first beat, onsets
au = os.path.join(a.out, "_audio.m4a"); pcm = os.path.join(a.out, "_audio.f32")
subprocess.run([os.path.join(a.bin, "audio_extract"), a.video, au], capture_output=True)
music = None; clicks = []
if os.path.exists(au) and subprocess.run([os.path.join(a.bin, "pcm"), au, pcm, "11025"], capture_output=True).returncode == 0:
    sr = 11025; x = np.fromfile(pcm, dtype=np.float32)
    hop, win = 128, 1024; frm = np.lib.stride_tricks.sliding_window_view(x, win)[::hop] * np.hanning(win)
    S = np.log1p(10 * np.abs(np.fft.rfft(frm, axis=1))); fl = np.r_[0, np.maximum(np.diff(S, axis=0), 0).sum(1)]
    fl = np.maximum(fl - np.convolve(fl, np.ones(16) / 16, "same"), 0); fps = sr / hop
    ac = np.correlate(fl, fl, "full")[len(fl) - 1:]; lag = np.arange(1, len(ac)) / fps; bpm = 60 / lag; mm = (bpm > 70) & (bpm < 180)
    t0 = 60 / bpm[mm][np.argmax(ac[1:][mm])]; best = None
    for tt in np.arange(t0 * 0.98, t0 * 1.02, 0.001):
        for ph in np.arange(0, tt, 0.01):
            idx = (np.arange(ph, len(x) / sr, tt) * fps).astype(int); idx = idx[idx < len(fl)]
            s = fl[idx].mean()
            if best is None or s > best[0]: best = (s, tt, ph)
    music = {"bpm": round(60 / best[1], 2), "beat": round(best[1], 4), "first_beat": round(best[2], 3)}
    hf = np.fft.rfftfreq(win, 1 / sr) > 2000
    f2 = np.maximum(np.diff(S[:, hf], axis=0), 0).sum(1); th = np.median(f2) * 4; tt = np.arange(len(f2)) * hop / sr
    clicks = [round(float(tt[i]), 2) for i in range(1, len(f2) - 1) if f2[i] > th and f2[i] >= f2[i - 1] and f2[i] >= f2[i + 1] and tt[i] < intro_end_cut]
# --- shots
shots = []
for k, c in enumerate(cuts):
    e = cuts[k + 1] if k + 1 < len(cuts) else T
    if c * STEP >= intro_end_cut: break
    seg = F[c:e]; mid = seg[len(seg) // 2] / 255.0
    r, g, b = mid[..., 0], mid[..., 1], mid[..., 2]; mx = mid.max(2); mn = mid.min(2)
    sat = float(((mx - mn) / (mx + 1e-6)).mean()); colorful = float(np.sqrt(((r - g) ** 2).mean() + ((0.5 * (r + g) - b) ** 2).mean()))
    hue = colorsys.rgb_to_hsv(*mid.reshape(-1, 3).mean(0))[0]
    motion = float(np.abs(seg[1:] - seg[:-1]).mean()) if len(seg) > 1 else 0.0
    L = (min(e, int(intro_end_cut / STEP)) - c) * STEP
    jpg = os.path.join(a.out, f"shot_{k+1:02d}.jpg"); Image.open(os.path.join(fr_dir, fs[(c + e) // 2])).save(jpg)
    sh = {"n": k + 1, "start": round(c * STEP, 3), "dur": round(L, 3), "brightness": round(float(mid.mean() * 255), 1), "saturation": round(sat, 3),
          "colorful": round(colorful, 3), "hue": round(float(hue), 3), "motion": round(motion, 2), "still_like": motion < 3.0, "frame": jpg, "type": ""}
    if music: sh["beats"] = round(L / music["beat"], 2)
    shots.append(sh)
spec = {"source": os.path.abspath(a.video), "orientation": "portrait" if H > W else "landscape", "intro_end": intro_end_cut,
        "n_shots": len(shots), "shots": shots, "title": title, "music": music, "clicks": clicks,
        "note": "Điền 'type' cho từng shot (vd food/landscape/selfie/street/detail/motion) sau khi xem intro_sheet.jpg"}
json.dump(spec, open(os.path.join(a.out, "intro_spec.json"), "w"), indent=1, ensure_ascii=False, default=float)
# --- sheet
try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 15)
except OSError: font = ImageFont.load_default()
tw = 150 if spec["orientation"] == "portrait" else 240; th_ = int(tw * (16 / 9 if spec["orientation"] == "portrait" else 9 / 16)); C = 6
rows = (len(shots) + C - 1) // C; sheet = Image.new("RGB", (C * (tw + 4), max(1, rows) * (th_ + 36)), "white"); d = ImageDraw.Draw(sheet)
for k, s in enumerate(shots):
    x = (k % C) * (tw + 4); y = (k // C) * (th_ + 36); im = Image.open(s["frame"]); im.thumbnail((tw, th_)); sheet.paste(im, (x, y + 34))
    d.text((x, y + 1), f"#{s['n']} {s['start']:.2f}s {s['dur']:.2f}s" + (f" {s['beats']}ph" if 'beats' in s else ""), fill="black", font=font)
    d.text((x, y + 17), ("TĨNH " if s["still_like"] else "") + f"mo {s['motion']:.1f}", fill="red" if s["still_like"] else "gray", font=font)
sheet.save(os.path.join(a.out, "intro_sheet.jpg"), quality=85)
print(f"intro {intro_end_cut}s, {len(shots)} cảnh, độ dài TB {np.mean([s['dur'] for s in shots]):.2f}s" if shots else "không tách được cảnh")
if music: print(f"nhạc mẫu {music['bpm']} BPM, phách {music['beat']}s → độ dài cảnh theo phách: {[s.get('beats') for s in shots]}")
if title: print(f"tiêu đề: {title['kind']}, màu {title['color']}, khung {title['box']}, {len(title['growth_steps'])} lần chữ tăng")
print(f"click/tiếng gõ trong intro: {len(clicks)}", clicks[:20]); print("spec:", os.path.join(a.out, "intro_spec.json"))
