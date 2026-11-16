#!/usr/bin/env python3
"""Render a quick MP4 preview of the matched intro (with its music) so the user can judge the rhythm before
anything is written to CapCut.

Usage: python3 intro_preview.py INTRO_MATCH.json OUT.mp4 --bin "$BIN" [--music music.m4a --music-start 0]
          [--size 1080x1920] [--alt 3=2,5=3]
  --alt slot=k  use alternative k (1–3) instead of the choice for that slot (to compare quickly)
Text/typing sound are NOT rendered here (preview = pictures + rhythm); they are added by intro_build.py in CapCut.
"""
import argparse, json, os, subprocess, tempfile
ap = argparse.ArgumentParser(); ap.add_argument("match"); ap.add_argument("out"); ap.add_argument("--bin", required=True)
ap.add_argument("--music"); ap.add_argument("--music-start", type=float, default=0.0); ap.add_argument("--size", default="1080x1920"); ap.add_argument("--alt", default="")
a = ap.parse_args(); m = json.load(open(a.match)); W, H = map(int, a.size.split("x"))
alt = {int(k): int(v) for k, v in (x.split("=") for x in a.alt.split(",") if x)}
segs = []
for s in m["slots"]:
    c = s["alternatives"][alt[s["slot"]] - 1] if s["slot"] in alt else s["choice"]
    segs.append({"path": c["path"], "src_in": c["src_in"], "dur": s["dur"]})
plan = {"width": W, "height": H, "fps": 30, "segments": segs}
if a.music: plan.update(audio=os.path.abspath(a.music), audio_start=a.music_start)
p = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False); json.dump(plan, p); p.close()
subprocess.run([os.path.join(a.bin, "compose"), p.name, os.path.abspath(a.out)], check=True)
