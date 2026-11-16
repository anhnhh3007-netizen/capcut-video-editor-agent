#!/usr/bin/env python3
"""List clips that are probably junk: very short, black/near-black frames, unreadable,
plus byte-identical duplicates ("Bản sao …" copies).

Usage: python3 find_bad_clips.py FOOTAGE_DIR WORK_DIR [--short 1.0] [--dark 20]
Reads WORK_DIR/index.tsv, durations.tsv and frames/ (from contact_sheet.py + frames3).
Prints: stt  file  duration  [brightness of the 3 frames]  reason
"""
import os, sys, hashlib, argparse
from PIL import Image, ImageStat

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("work")
ap.add_argument("--short", type=float, default=1.0); ap.add_argument("--dark", type=float, default=20)
a = ap.parse_args()
F = os.path.join(a.work, "frames")
for l in open(os.path.join(a.work, "index.tsv")):
    n, rel, ts, d = (l.rstrip("\n").split("\t") + [""])[:4]
    if not rel.lower().endswith((".mp4", ".mov")): continue
    base = os.path.splitext(os.path.basename(rel))[0]; d = float(d or 0)
    vals = []
    for j in (1, 2, 3):
        p = f"{F}/{base}_{j}.jpg"
        vals.append(round(ImageStat.Stat(Image.open(p).convert("L")).mean[0]) if os.path.exists(p) else None)
    why = []
    if d < a.short: why.append(f"ngắn <{a.short}s")
    if all(v is None for v in vals): why.append("không đọc được khung")
    elif all(v is not None and v < a.dark for v in vals): why.append("toàn màn hình đen")
    if why: print(n, rel, d, vals, "; ".join(why), sep="\t")

def head_hash(p, n=50_000_000):
    h = hashlib.md5()
    with open(p, "rb") as f: h.update(f.read(n))
    return h.hexdigest()
copies = [os.path.join(r, f) for r, _, fs in os.walk(a.src) for f in fs if f.startswith(("Bản sao", "Bản sao", "Copy of"))]
for c in copies:
    orig = os.path.join(os.path.dirname(c), c.split(" ", 2)[-1] if c.startswith("Copy") else os.path.basename(c).split(" ", 2)[-1])
    same = os.path.exists(orig) and os.path.getsize(orig) == os.path.getsize(c) and head_hash(orig) == head_hash(c)
    print("-", os.path.relpath(c, a.src), "", "", "bản sao " + ("TRÙNG với gốc" if same else "khác gốc / không thấy gốc"), sep="\t")
