#!/usr/bin/env python3
"""Turn a beat-based shot plan into an EDL (edl.json) by picking the best in-point of every clip.

Usage: python3 pick_shots.py PLAN.json SCAN.tsv OUT_edl.json
  SCAN.tsv = concatenated output of `$BIN/scan` over every clip in the plan
PLAN.json (see references/plan_format.md):
  {"beat": {"period": 0.50455, "first": 0.410}, "end": 52.067, "fps": 30,
   "sections": [{"name": "title", "caption": "", "start_beat": null, "end_beat": 8, "chrono": false,
                 "shots": [["/abs/clip.MP4", 0], ["/abs/clip2.MP4", 1], ...]}, ...],
   "overrides": [{"section": "title", "file": "DJI_x.MP4", "src_in": 30.0}]}
  shot length unit = half-beats (1 = nửa phách, 2 = 1 phách, 4 = 2 phách); 0 = fill to the
  section's end (title: from 0 s to the first beat).
In-point score: sharpness (normalised per clip) − motion/shake − too dark/bright − distance from
the clip's middle; skips the first 0.4 s (handheld start shake) and windows already used.
Prints per-section beat totals so you can check the plan fills the music exactly.
"""
import json, os, sys, collections
import numpy as np

plan = json.load(open(sys.argv[1])); FPS = plan.get("fps", 30); FR = 1 / FPS
T = plan["beat"]["period"]; B0 = plan["beat"]["first"]; END = plan["end"]
beat = lambda u: B0 + u * T / 2              # u in half-beats
data = collections.defaultdict(list)
for l in open(sys.argv[2]):
    f, t, br, sh, mo = l.rstrip("\n").split("\t"); data[f].append((float(t), float(br), float(sh), float(mo)))
ovr = {(o["section"], o["file"]): o["src_in"] for o in plan.get("overrides", [])}
# scoring weights — defaults = generic; video-type profiles (TIEU_CHI_CHON_CANH.md §9) override via plan["scoring"]
W = {"motion_div": 25, "jitter_w": 0.03, "dark_level": 35, "dark_penalty": 0.8, "bright_level": 225, "bright_penalty": 0.5, "middle_w": 0.1}
W.update(plan.get("scoring", {}))
print("scoring:", W)
used = collections.defaultdict(list)

def choose(path, L, sec):
    f = os.path.basename(path)
    if (sec, f) in ovr: used[f].append(ovr[(sec, f)]); return ovr[(sec, f)]
    if not data[f]: print("WARN no scan data for", f); return 0.0
    a = np.array(data[f]); t, br, sh, mo = a.T; dur = t[-1] + 0.2
    shn = sh / (np.percentile(sh, 90) + 1e-6); best = None
    for i in range(len(t)):
        s = t[i]; e = s + L + 0.3
        if s < 0.4 and dur > 3: continue
        if e > dur - 0.2: break
        if any(abs(s - u) < max(1.5, L + 0.5) for u in used[f]): continue
        w = (t >= s) & (t <= e)
        if w.sum() < 2: continue
        b = br[w].mean()
        sc = shn[w].mean() - mo[w].mean() / W["motion_div"] - (W["dark_penalty"] if b < W["dark_level"] else 0) \
             - (W["bright_penalty"] if b > W["bright_level"] else 0) \
             - W["jitter_w"] * np.abs(np.diff(mo[w])).mean() - W["middle_w"] * abs((s + L / 2) / dur - 0.5)
        if best is None or sc > best[0]: best = (sc, s)
    s = best[1] if best else max(0, (dur - L) / 2)
    used[f].append(s); return round(s / FR) * FR

shots = []
for sec in plan["sections"]:
    a = sec.get("start_beat"); lst = sec["shots"]
    if sec.get("chrono"): lst = sorted(lst, key=lambda x: os.path.basename(x[0]))
    u = 0 if a is None else a * 2; total = 0
    for k, (path, l) in enumerate(lst):
        if l == 0:
            st = 0 if a is None else beat(u)
            en = beat(0) if a is None and k == 0 else (beat(sec["end_beat"] * 2) if sec.get("end_beat") is not None else END)
        else:
            st, en = beat(u), beat(u + l); u += l; total += l
        if a is None and k == 0: st = 0.0
        shots.append({"sec": sec["name"], "cap": sec.get("caption", ""), "path": path, "file": os.path.basename(path),
                      "caption": sec.get("captions", {}).get(os.path.basename(path)),
                      "start": round(st / FR) * FR, "dur": 0})
    want = (sec["end_beat"] if sec.get("end_beat") is not None else (END - B0) / T) - (a or 0)
    print(f"{sec['name']:8s} {total/2:5.1f} phách / cần {want:5.1f}")
for i in range(len(shots) - 1): shots[i]["dur"] = shots[i + 1]["start"] - shots[i]["start"]
shots[-1]["dur"] = int(END * FPS) / FPS - shots[-1]["start"]
for s in shots: s["src_in"] = choose(s["path"], s["dur"], s["sec"])
bad = [s for s in shots if s["dur"] <= 0]
json.dump(shots, open(sys.argv[3], "w"), indent=1, ensure_ascii=False)
print(len(shots), "cảnh, tổng", round(shots[-1]["start"] + shots[-1]["dur"], 3), "s;", "LỖI độ dài <=0: %d" % len(bad) if bad else "ok")
