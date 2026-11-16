#!/usr/bin/env python3
"""Match the user's footage to each shot slot of an intro spec and draw a side-by-side comparison sheet.

Usage: python3 intro_match.py INTRO_SPEC.json SCAN.tsv OUT_DIR --bin "$BIN" --beat 0.50455 --first 0.410
          (--clips clip1.MP4 clip2 … | --clips-file list.txt) [--types types.tsv] [--exclude used.txt]
          [--intro-end SECONDS] [--allow-stills]
  INTRO_SPEC.json  from phan-tich-video-mau/scripts/intro_spec.py — or a hand-written spec (no sample video):
                   {"intro_end": <s>, "shots": [{"n":1,"beats":1,"type":"landscape"}, …]}
  SCAN.tsv         `$BIN/scan` output for every candidate clip
  --beat/--first   beat grid of the music the INTRO will use (intro music, or the whole-video music)
  --types          optional TSV "file<TAB>type" (food/landscape/selfie/street/detail/motion…) — same type as the
                   slot gets a big bonus, so Claude should label candidates after viewing the contact sheet
  --exclude        files already used in the body (they are allowed but penalised, to avoid repeats)
How:
  1. slot length: sample length in beats × target beat, snapped to the half-beat grid (min half a beat);
     the slots are then stretched/shrunk proportionally so the intro ends exactly on a target beat.
  2. per clip: best steady window of that length (sharp, low shake) from SCAN; its mid frame is grabbed and
     measured like the sample (brightness, saturation, colourfulness, hue) + motion percentile.
  3. score = type match + closeness of brightness/colour/hue/motion to the sample slot; 'still_like' slots
     (the sample used a photo) prefer the steadiest video moments — stills are never used (§8c).
  4. top-3 per slot; slot choices are made greedily without reusing a clip.
Writes OUT_DIR/intro_match.json (slots with start/dur/choice/alternatives) and OUT_DIR/intro_compare.jpg
(row 1 = sample frames, rows 2–4 = candidates; choice framed in green).
"""
import argparse, collections, colorsys, json, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser(); ap.add_argument("spec"); ap.add_argument("scan"); ap.add_argument("out"); ap.add_argument("--bin", required=True)
ap.add_argument("--beat", type=float, required=True); ap.add_argument("--first", type=float, default=0.0)
ap.add_argument("--clips", nargs="*", default=[]); ap.add_argument("--clips-file"); ap.add_argument("--types"); ap.add_argument("--exclude")
ap.add_argument("--intro-end", type=float); ap.add_argument("--fps", type=int, default=30)
a = ap.parse_args(); os.makedirs(a.out, exist_ok=True); FR = 1 / a.fps
spec = json.load(open(a.spec)); slots = spec["shots"]
clips = list(a.clips) + ([l.strip() for l in open(a.clips_file) if l.strip()] if a.clips_file else [])
types = dict(l.rstrip("\n").split("\t")[:2] for l in open(a.types)) if a.types else {}
excl = {os.path.basename(l.strip()) for l in open(a.exclude)} if a.exclude else set()
data = collections.defaultdict(list)
for l in open(a.scan):
    f, t, br, sh, mo = l.rstrip("\n").split("\t"); data[f].append((float(t), float(br), float(sh), float(mo)))
# 1. slot lengths on the target beat grid
half = a.beat / 2
want = [max(1, round(s.get("beats", s["dur"] / a.beat if "dur" in s else 1) * 2)) for s in slots]   # in half-beats
if a.intro_end or spec.get("intro_end"):
    target_end = a.intro_end or spec["intro_end"]
    k_end = max(len(slots), round((target_end - a.first) / half)) if a.first < target_end else len(slots)
    scale = k_end / sum(want); want = [max(1, round(w * scale)) for w in want]
    while sum(want) > k_end: want[want.index(max(want))] -= 1
    while sum(want) < k_end: want[want.index(min(want))] += 1
grid = [0.0] + [a.first + half * sum(want[:i + 1]) for i in range(len(want))]
grid = [round(g * a.fps) / a.fps for g in grid]
# 2. candidate windows + features
def window(f, L):
    arr = np.array(data[f]); t, br, sh, mo = arr.T; dur = t[-1] + 0.2; shn = sh / (np.percentile(sh, 90) + 1e-6); best = None
    for i in range(len(t)):
        s0 = t[i]; e = s0 + L + 0.2
        if s0 < 0.4 and dur > 3: continue
        if e > dur - 0.1: break
        w = (t >= s0) & (t <= e)
        if w.sum() < 2: continue
        sc = shn[w].mean() - mo[w].mean() / 40 - (0.6 if br[w].mean() < 30 else 0)
        if best is None or sc > best[0]: best = (sc, s0, mo[w].mean(), br[w].mean())
    return best
L_max = max(grid[i + 1] - grid[i] for i in range(len(want)))
cands = []
for c in clips:
    f = os.path.basename(c)
    if not data[f]: continue
    w = window(f, L_max)
    if w: cands.append({"path": c, "file": f, "src_in": round(round(w[1] / FR) * FR, 3), "motion_raw": w[2], "type": types.get(f, "")})
fr = os.path.join(a.out, "_cand"); os.makedirs(fr, exist_ok=True)
subprocess.run([os.path.join(a.bin, "grab")], input="".join(f"{c['path']}\t{c['src_in'] + L_max / 2:.3f}\t{fr}/{i:03d}.jpg\n" for i, c in enumerate(cands)).encode(), check=True)
def feats(img):
    m = np.asarray(Image.open(img).convert("RGB").resize((90, 160)), dtype=np.float32) / 255
    r, g, b = m[..., 0], m[..., 1], m[..., 2]; mx = m.max(2); mn = m.min(2)
    return {"brightness": float(m.mean() * 255), "saturation": float(((mx - mn) / (mx + 1e-6)).mean()),
            "colorful": float(np.sqrt(((r - g) ** 2).mean() + ((0.5 * (r + g) - b) ** 2).mean())), "hue": float(colorsys.rgb_to_hsv(*m.reshape(-1, 3).mean(0))[0])}
for i, c in enumerate(cands): c.update(feats(f"{fr}/{i:03d}.jpg")); c["img"] = f"{fr}/{i:03d}.jpg"
mr = np.array([c["motion_raw"] for c in cands]); [c.__setitem__("motion_pct", float((mr < c["motion_raw"]).mean())) for c in cands]
sm = np.array([s.get("motion", 0) for s in slots]); [s.__setitem__("motion_pct", float((sm < s.get("motion", 0)).mean())) for s in slots]
# 3. score
def score(s, c):
    sc = 0.0
    if s.get("type") and c["type"]: sc += 2.0 if s["type"] == c["type"] else -0.5
    if "brightness" in s: sc -= abs(s["brightness"] - c["brightness"]) / 80
    if "colorful" in s: sc -= abs(s["colorful"] - c["colorful"]) * 3
    if "saturation" in s: sc -= abs(s["saturation"] - c["saturation"]) * 1.5
    if "hue" in s: dh = abs(s["hue"] - c["hue"]); sc -= min(dh, 1 - dh) * 1.5
    sc -= abs(s["motion_pct"] - c["motion_pct"]) * (1.5 if s.get("still_like") else 0.8)
    if s.get("still_like"): sc -= c["motion_pct"] * 0.8           # sample used a photo → steadiest video moment
    if c["file"] in excl: sc -= 0.7
    return sc
def look(c): return np.array([c["brightness"] / 255, c["saturation"], c["colorful"] * 2, c["hue"]])
def similar_penalty(c, picked):
    if not picked: return 0.0
    dmin = min(np.abs(look(c) - look(p)).sum() for p in picked)
    return max(0.0, 0.35 - dmin) * 4 + (0.4 if c["type"] and any(p["type"] == c["type"] for p in picked[-2:]) else 0)
used = set(); picked = []; out = []
choice = {}
for i in range(len(slots)):                     # in timeline order so "looks like the previous shots" is meaningful
    ranked = sorted(cands, key=lambda c: -(score(slots[i], c) - similar_penalty(c, picked)))
    top = [c for c in ranked if c["file"] not in used][:3] or ranked[:3]
    pick = top[0]; used.add(pick["file"]); picked.append(pick); choice[i] = (pick, top)
for i, s in enumerate(slots):
    pick, top = choice[i]; L = round(grid[i + 1] - grid[i], 3)
    out.append({"slot": i + 1, "start": grid[i], "dur": L, "half_beats": want[i], "sample_frame": s.get("frame"), "sample_type": s.get("type", ""),
                "choice": {"path": pick["path"], "file": pick["file"], "src_in": pick["src_in"]},
                "alternatives": [{"path": c["path"], "file": c["file"], "src_in": c["src_in"], "type": c["type"], "score": round(score(s, c), 2)} for c in top]})
res = {"intro_end": grid[-1], "beat": a.beat, "first_beat": a.first, "slots": out, "title": spec.get("title"), "clicks": spec.get("clicks", [])}
json.dump(res, open(os.path.join(a.out, "intro_match.json"), "w"), indent=1, ensure_ascii=False)
# 4. comparison sheet
try: font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 14)
except OSError: font = ImageFont.load_default()
portrait_sample = spec.get("orientation", "portrait") == "portrait"
cw = 120; sh_h = 213 if portrait_sample else 68
cimg = Image.open(cands[0]["img"]); cand_h = int(cw * cimg.height / cimg.width)
TW = cw; n = len(out); rowh = [sh_h + 20] + [cand_h + 34] * 3; TH = sh_h
sheet = Image.new("RGB", (n * (TW + 6) + 70, sum(rowh) + 10), "white"); d = ImageDraw.Draw(sheet)
ys = [16]; [ys.append(ys[-1] + rowh[r]) for r in range(3)]
for r, lab in enumerate(["MẪU", "#1", "#2", "#3"]): d.text((4, ys[r] + 20), lab, fill="black", font=font)
for k, o in enumerate(out):
    x = 70 + k * (TW + 6)
    d.text((x, 0), f"ô{o['slot']} {o['dur']:.2f}s", fill="black", font=font)
    if o["sample_frame"] and os.path.exists(o["sample_frame"]):
        im = Image.open(o["sample_frame"]); im.thumbnail((TW, sh_h)); sheet.paste(im, (x, ys[0]))
    elif o.get("sample_type"): d.text((x, ys[0] + 20), o["sample_type"], fill="gray", font=font)
    for r, alt in enumerate(o["alternatives"][:3], 1):
        c = next(c for c in cands if c["file"] == alt["file"]); im = Image.open(c["img"]); im.thumbnail((TW, cand_h)); y = ys[r]
        sheet.paste(im, (x, y)); d.text((x, y + im.height + 2), (c["type"] or "")[:16], fill="gray", font=font)
        if alt["file"] == o["choice"]["file"]: d.rectangle([x - 2, y - 2, x + im.width + 1, y + im.height + 1], outline=(0, 180, 0), width=3)
sheet.save(os.path.join(a.out, "intro_compare.jpg"), quality=85)
print(f"intro {res['intro_end']:.3f}s, {n} ô | độ dài (nửa phách): {want}")
for o in out: print(f"  ô{o['slot']}: {o['start']:.2f}s +{o['dur']:.2f}s → {o['choice']['file']} @ {o['choice']['src_in']}s")
print("bảng đối chiếu:", os.path.join(a.out, "intro_compare.jpg"))
