#!/usr/bin/env python3
"""Cut detection + shot sheets for a reference ("video mẫu") clip.

Usage: python3 analyze_sample.py FRAMES_DIR DURATION OUT_DIR [--step 0.04] [--thresh 25]
  FRAMES_DIR = output of  `$BIN/dense video FRAMES_DIR 0.04 320`
Writes OUT_DIR/cuts.txt (one cut time per line, first = 0), OUT_DIR/shots_N.jpg
(each shot: first frame + middle frame, label '#i start (len)'), prints pacing stats
(shot count, mean/median length, cuts per 4 s window) to paste into the analysis note.
"""
import os, sys, argparse, statistics
from PIL import Image, ImageChops, ImageStat, ImageDraw, ImageFont

ap = argparse.ArgumentParser(); ap.add_argument("frames"); ap.add_argument("duration", type=float); ap.add_argument("out")
ap.add_argument("--step", type=float, default=0.04); ap.add_argument("--thresh", type=float, default=25)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
fs = sorted(f for f in os.listdir(a.frames) if f.endswith(".jpg"))
prev = None; cuts = [0.0]; diffs = []
for i, f in enumerate(fs):
    im = Image.open(os.path.join(a.frames, f)).convert("RGB").resize((48, 48))
    if prev is not None:
        d = sum(ImageStat.Stat(ImageChops.difference(im, prev)).mean) / 3; diffs.append(d)
        med = statistics.median(diffs) if diffs else 0
        if d > max(a.thresh, med * 4) and i * a.step - cuts[-1] > 0.18: cuts.append(round(i * a.step, 2))
    prev = im
open(os.path.join(a.out, "cuts.txt"), "w").write("\n".join(map(str, cuts)))
shots = list(zip(cuts, cuts[1:] + [a.duration])); lens = [b - s for s, b in shots]
print(f"{len(shots)} cảnh / {a.duration:.1f}s | TB {statistics.mean(lens):.2f}s | trung vị {statistics.median(lens):.2f}s | ngắn nhất {min(lens):.2f}s | dài nhất {max(lens):.2f}s")
print("số điểm cắt mỗi 4s:", [sum(1 for t in cuts if s <= t < s + 4) for s in range(0, int(a.duration) + 1, 4)])
print("độ dài từng cảnh:", [round(x, 2) for x in lens])
w, h = Image.open(os.path.join(a.frames, fs[0])).size
portrait = h > w; TW, TH = (150, 267) if portrait else (240, 135); C = 5 if portrait else 6; PER = 25 if portrait else 36
try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 16)
except OSError: font = ImageFont.load_default()
frame_at = lambda t: os.path.join(a.frames, fs[min(len(fs) - 1, int(t / a.step))])
for p in range(0, len(shots), PER):
    part = shots[p:p + PER]; rows = (len(part) + C - 1) // C; cw = TW * 2 + 8
    sh = Image.new("RGB", (C * cw, rows * (TH + 24)), "white"); d = ImageDraw.Draw(sh)
    for k, (s, b) in enumerate(part):
        x = (k % C) * cw; y = (k // C) * (TH + 24)
        for j, t in enumerate([s + 0.08, (s + b) / 2]):
            im = Image.open(frame_at(t)); im.thumbnail((TW, TH)); sh.paste(im, (x + j * TW, y + 22))
        d.text((x, y + 2), f"#{p+k+1} {s:.2f}s ({b-s:.2f}s)", fill="black", font=font)
    sh.save(os.path.join(a.out, f"shots_{p // PER + 1}.jpg"), quality=82)
print("sheets:", (len(shots) + PER - 1) // PER, "in", a.out)
