#!/usr/bin/env python3
"""Move footage into folders from a plan, keep DJI .LRF proxies mirrored, log every move (undoable).

Plan file (TSV, one line per item):   <relative path or stt>\t<target folder (may contain '/')>
  - stt numbers refer to WORK_DIR/index.tsv
  - LRF proxies of moved MP4s go to  _LRF_ban_xem_truoc_DJI/<same folder>
Usage:
  python3 organize.py FOOTAGE_DIR PLAN.tsv [--index WORK/index.tsv] [--dry]
  python3 organize.py FOOTAGE_DIR --undo          # moves everything back using the log
The log is FOOTAGE_DIR/_nhat_ky_sap_xep.csv (stt,file,old_folder,folder). Never deletes anything;
only removes folders it emptied itself.
"""
import os, sys, csv, shutil, argparse, unicodedata

ap = argparse.ArgumentParser(); ap.add_argument("src"); ap.add_argument("plan", nargs="?")
ap.add_argument("--index"); ap.add_argument("--dry", action="store_true"); ap.add_argument("--undo", action="store_true")
ap.add_argument("--lrf-folder", default="_LRF_ban_xem_truoc_DJI")
a = ap.parse_args()
LOG = os.path.join(a.src, "_nhat_ky_sap_xep.csv")
nfc = lambda s: unicodedata.normalize("NFC", s)

def prune(dirs):
    for d in sorted(dirs, key=len, reverse=True):
        while d and d != a.src and os.path.isdir(d) and not [x for x in os.listdir(d) if x != ".DS_Store"]:
            if os.path.exists(os.path.join(d, ".DS_Store")): os.remove(os.path.join(d, ".DS_Store"))
            os.rmdir(d); d = os.path.dirname(d)

if a.undo:
    rows = list(csv.DictReader(open(LOG))); touched = set()
    for r in reversed(rows):
        cur = os.path.join(a.src, r["folder"], r["file"]); back = os.path.join(a.src, r["old_folder"], r["file"])
        if os.path.exists(cur) and not os.path.exists(back):
            os.makedirs(os.path.dirname(back), exist_ok=True); shutil.move(cur, back); touched.add(os.path.dirname(cur))
    prune(touched); os.rename(LOG, LOG + ".undone"); print("undone", len(rows)); sys.exit()

idx = {}
if a.index:
    for l in open(a.index):
        n, rel = l.rstrip("\n").split("\t")[:2]; idx[n] = rel
# map NFC name -> real relative path (macOS stores NFD)
real = {}
for root, _, files in os.walk(a.src):
    for f in files: real[nfc(os.path.relpath(os.path.join(root, f), a.src))] = os.path.relpath(os.path.join(root, f), a.src)
plan = []
for l in open(a.plan):
    if not l.strip() or l.startswith("#"): continue
    key, folder = l.rstrip("\n").split("\t")[:2]
    rel = idx.get(key, key); rel = real.get(nfc(rel), rel)
    if not os.path.exists(os.path.join(a.src, rel)): print("MISSING", key, rel); continue
    plan.append((key, rel, folder))
    base, ext = os.path.splitext(rel)
    for lrf in (base + ".LRF", base + ".lrf"):
        if ext.lower() == ".mp4" and os.path.exists(os.path.join(a.src, lrf)):
            plan.append((key, lrf, os.path.join(a.lrf_folder, folder)))
from collections import Counter
for f, c in sorted(Counter(p[2] for p in plan if not p[2].startswith(a.lrf_folder)).items()): print(c, f)
if a.dry: print("dry run:", len(plan), "moves"); sys.exit()
new = not os.path.exists(LOG); touched = set()
with open(LOG, "a", newline="") as o:
    w = csv.writer(o)
    if new: w.writerow(["stt", "file", "old_folder", "folder"])
    for key, rel, folder in plan:
        dst = os.path.join(a.src, folder, os.path.basename(rel))
        if os.path.abspath(os.path.join(a.src, rel)) == os.path.abspath(dst): continue
        if os.path.exists(dst): print("SKIP exists", dst); continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        touched.add(os.path.dirname(os.path.join(a.src, rel)))
        shutil.move(os.path.join(a.src, rel), dst)
        w.writerow([key, os.path.basename(rel), os.path.dirname(rel), folder])
prune(touched - {a.src})
print("moved", len(plan), "files; log:", LOG)
