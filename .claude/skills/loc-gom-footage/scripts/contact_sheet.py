#!/usr/bin/env python3
"""Index all photos/videos in a footage folder chronologically and render contact sheets.

Usage: python3 contact_sheet.py FOOTAGE_DIR WORK_DIR
  - needs WORK_DIR/frames/ filled by `frames3` (videos) — photos are thumbnailed here with Pillow
  - needs WORK_DIR/durations.tsv (stdout of frames3)
Writes WORK_DIR/index.tsv (stt, relative path, timestamp, duration) and WORK_DIR/sheet_XX.jpg
(40 items per sheet: label '#stt dd/mm hh:mm Ns' + 3 frames; photos labelled ẢNH in red).
"""
import os, re, sys
from PIL import Image, ImageDraw, ImageFont

src, work = sys.argv[1], sys.argv[2]
F = os.path.join(work, "frames"); os.makedirs(F, exist_ok=True)
dur = {}
if os.path.exists(os.path.join(work, "durations.tsv")):
    for l in open(os.path.join(work, "durations.tsv")):
        a = l.rstrip("\n").split("\t")
        if len(a) == 2: dur[a[0]] = float(a[1])
VID = (".mp4", ".mov", ".m4v"); IMG = (".jpg", ".jpeg", ".png", ".heic")
items = []
for root, _, files in os.walk(src):
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if f.startswith(".") or ext not in VID + IMG or f.startswith("Bản sao") or f.startswith("Bản sao"): continue
        rel = os.path.relpath(os.path.join(root, f), src)
        m = re.search(r"(\d{8})[_-]?(\d{6})", f)          # DJI_YYYYMMDDhhmmss / IMG_YYYYMMDD_hhmmss
        ts = m.group(1) + m.group(2) if m else "%014d" % int(os.path.getmtime(os.path.join(root, f)))
        items.append((ts, rel))
items.sort()
with open(os.path.join(work, "index.tsv"), "w") as o:
    for i, (t, rel) in enumerate(items):
        o.write(f"{i+1}\t{rel}\t{t}\t{dur.get(os.path.splitext(os.path.basename(rel))[0], '')}\n")
try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 16)
except OSError: font = ImageFont.load_default()
TW, TH = 128, 72; W = TW * 3; H = TH + 22; C, R = 4, 10
for s in range(0, len(items), C * R):
    sheet = Image.new("RGB", (W * C + (C - 1) * 6, (H + 6) * R), "white"); d = ImageDraw.Draw(sheet)
    for k, (t, rel) in enumerate(items[s:s + C * R]):
        x = (k % C) * (W + 6); y = (k // C) * (H + 6)
        base = os.path.splitext(os.path.basename(rel))[0]; isv = rel.lower().endswith(VID)
        if isv: frames = [f"{F}/{base}_{j}.jpg" for j in (1, 2, 3)]
        else:
            p = f"{F}/{base}_1.jpg"
            if not os.path.exists(p):
                try: im = Image.open(os.path.join(src, rel)); im.thumbnail((360, 360)); im.convert("RGB").save(p)
                except Exception: pass
            frames = [p]
        for j, p in enumerate(frames):
            if os.path.exists(p):
                im = Image.open(p); im.thumbnail((TW, TH)); sheet.paste(im, (x + j * TW, y + 22))
        lab = f"#{s+k+1} {t[6:8]}/{t[4:6]} {t[8:10]}:{t[10:12]} " + (f"{dur.get(base, 0):.0f}s" if isv else "ẢNH")
        d.text((x, y + 2), lab, fill="black" if isv else "red", font=font)
    sheet.save(os.path.join(work, f"sheet_{s // (C * R) + 1:02d}.jpg"), quality=80)
print(len(items), "items;", (len(items) + C * R - 1) // (C * R), "sheets in", work)
