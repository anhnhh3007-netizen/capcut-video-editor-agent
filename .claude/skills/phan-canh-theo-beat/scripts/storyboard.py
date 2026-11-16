#!/usr/bin/env python3
"""Render review storyboard sheets for an EDL so the user can approve shots before anything is
written to CapCut.

Usage: python3 storyboard.py EDL.json GRAB_BIN WORK_DIR OUT_PREFIX
  GRAB_BIN = "$BIN/grab" from video-tools-macos
  OUT_PREFIX e.g. ~/Downloads/Trip/_Phan_canh_duyet  ->  _Phan_canh_duyet_1.jpg, _2.jpg …
Each tile: '<stt>. <section> <start>s (<len>s)' + the frame in the middle of the chosen window.
Look at every sheet yourself first (Read) and fix obviously bad picks (floor, blur, black) via
"overrides" in the plan before sending the sheets to the user.
"""
import json, os, sys, subprocess
from PIL import Image, ImageDraw, ImageFont

edl = json.load(open(sys.argv[1])); grab = sys.argv[2]; work = sys.argv[3]; out = os.path.expanduser(sys.argv[4])
sb = os.path.join(work, "sb"); os.makedirs(sb, exist_ok=True)
for f in os.listdir(sb): os.remove(os.path.join(sb, f))
lines = "".join(f"{s['path']}\t{s['src_in'] + s['dur'] / 2:.3f}\t{sb}/{i:03d}.jpg\n" for i, s in enumerate(edl))
subprocess.run([grab], input=lines.encode(), check=True)
try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 15)
except OSError: font = ImageFont.load_default()
TW, TH, C, PER = 200, 113, 8, 48
for pi in range(0, len(edl), PER):
    pg = edl[pi:pi + PER]; rows = (len(pg) + C - 1) // C
    im = Image.new("RGB", (C * (TW + 4), rows * (TH + 20)), "white"); d = ImageDraw.Draw(im)
    for k, s in enumerate(pg):
        i = pi + k; X = (k % C) * (TW + 4); Y = (k // C) * (TH + 20); p = f"{sb}/{i:03d}.jpg"
        if os.path.exists(p): t = Image.open(p); t.thumbnail((TW, TH)); im.paste(t, (X, Y + 18))
        d.text((X, Y + 1), f"{i+1}. {s['sec']} {s['start']:.1f}s ({s['dur']:.2f}s)", fill="black", font=font)
    im.save(f"{out}_{pi // PER + 1}.jpg", quality=82); print(f"{out}_{pi // PER + 1}.jpg")
