#!/usr/bin/env python3
"""Create a NEW CapCut 4.6 (mac) project from an EDL (phan-canh-theo-beat) + music + project.json.

Usage: python3 capcut_draft.py project.json --bin "$BIN" [--dry]
project.json (see references/project_config.md):
{
  "name": "Japan_Trip_2026_SuperTrouper",
  "edl": "/…/edl.json",
  "music": "/…/_Nhac/Super_Trouper_doan_nhu_mau.m4a",
  "assets_dir": "~/Movies/CapCut_Assets/Japan_Trip_2026",
  "canvas": [1920, 1080], "fps": 30,
  "beat": {"period": 0.50455, "first": 0.410},
  "mute_original": true, "music_fade_out": 0.4,
  "title": {"text": "japan trip", "color": "#CDB4FF", "size": 22, "y": 0.12, "typewriter": true,
            "sub": "osaka · kyoto 2026", "sub_from_beat": 4, "sub_size": 8, "sub_y": -0.18},
  "section_headers": {"size": 12, "y": -0.62, "seconds": 1.0},
  "outro_text": "see you next trip",
  "time_labels": {"regex": "(\\d{8})(\\d{6})", "shift_hours": 2, "shift_from": "2026-05-22 00:00", "x": -0.80, "size": 6},
  "captions": {"x": 0.78, "size": 6},
  "effects": {"section_punch": 1.3, "hold_zoom": 1.08, "hold_min": 0.95, "whip_files": ["DJI_…MP4"], "fade_out_end": 0.8},
  "reserve_overlay_track": true,
  "intro": {"duration": 4.0}            (optional: leave 0→4s free for intro_build.py with its own intro music; body + music start after it)
}
Sections named "title"/"outro" are special; every other section's first shot gets a header (edl "cap").
Media are HARD-LINKED (same volume, zero extra space, originals untouched) into assets_dir/clips — assets_dir is
chosen by the user (recommend ~/Movies/…: the sandboxed CapCut only reads ~/Movies on its own).
"""
import argparse, datetime, json, os, re, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capcut_lib import Draft, ROOT, US, backup, capcut_running, us, write_draft

ap = argparse.ArgumentParser(); ap.add_argument("config"); ap.add_argument("--bin", required=True); ap.add_argument("--dry", action="store_true")
a = ap.parse_args(); C = json.load(open(a.config))
NAME = C["name"]; OUT = os.path.join(ROOT, NAME); ASSETS = os.path.expanduser(C["assets_dir"]); FPS = C.get("fps", 30)
if capcut_running(): sys.exit("CapCut đang mở — nhờ người dùng tắt CapCut trước khi ghi.")
if os.path.exists(OUT): sys.exit(f"Đã có project {OUT} — dùng tên khác hoặc sửa project bằng script edit.")
edl = json.load(open(C["edl"]))

# ---- 1. media into ~/Movies (hard links; copy only if hard link impossible) ----
os.makedirs(os.path.join(ASSETS, "clips"), exist_ok=True); os.makedirs(os.path.join(ASSETS, "music"), exist_ok=True)
def place(src, sub):
    dst = os.path.join(ASSETS, sub, os.path.basename(src))
    if not os.path.exists(dst):
        try: os.link(src, dst)
        except OSError: print("WARN: không hard link được (khác ổ đĩa) → copy", src); shutil.copy2(src, dst)
    return dst
for s in edl: s["asset"] = place(s["path"], "clips")
music = place(C["music"], "music")
paths = sorted({s["asset"] for s in edl}) + [music]
info = {}
for l in subprocess.run([os.path.join(a.bin, "media_info")] + paths, capture_output=True, text=True, check=True).stdout.splitlines():
    p, d, w, h, au = l.split("\t"); info[p] = (int(d), int(w), int(h), int(au))
END = (info[music][0] * FPS // US) * US // FPS
if a.dry: print("dry run ok:", len(edl), "shots,", len(paths) - 1, "clips, music", END / US, "s"); sys.exit()

# ---- 2. backup CapCut's project list ----
bk = backup([os.path.join(ROOT, "root_meta_info.json")], os.path.join(ASSETS, "_backup"), "truoc_tao_" + NAME)
print("backup:", bk)

# ---- 3. build timeline ----
D = Draft.new(*C.get("canvas", [1920, 1080]), float(FPS)); E = C.get("effects", {})
beat = lambda i: us(C["beat"]["first"] + i * C["beat"]["period"], FPS)   # music time (body); add IOFF for timeline
IOFF = us(C.get("intro", {}).get("duration", 0), FPS)      # free intro region 0→IOFF (filled later by intro_build.py, own intro music)
starts = [us(s["start"], FPS) + IOFF for s in edl] + [END + IOFF]
mats = {}; vsegs = []; prev = None
for k, s in enumerate(edl):
    d, w, h, au = info[s["asset"]]
    m = mats.get(s["asset"]) or mats.setdefault(s["asset"], D.video_material(s["asset"], d, w, h, au))
    t0, t1 = starts[k], starts[k + 1]; dur = t1 - t0; src = us(s["src_in"], FPS)
    if src + dur > d: src = max(0, d - dur - US // FPS)
    kfs = []
    if E.get("section_punch") and s["sec"] not in ("title", "outro") and s["sec"] != prev:
        p = min(8 * US // FPS, dur); kfs += D.zoom(E["section_punch"], 1.0, 0, p)
    elif s["file"] in E.get("whip_files", []):
        p = min(6 * US // FPS, dur); kfs += [D.kf("KFTypePositionX", [(0, 0.3), (p, 0.0)])] + D.zoom(1.35, 1.0, 0, p)
    elif E.get("hold_zoom") and dur >= E.get("hold_min", 0.95) * US:
        kfs += D.zoom(1.0, E["hold_zoom"], 0, dur)
    if k == len(edl) - 1 and E.get("fade_out_end"):
        f = min(int(E["fade_out_end"] * US), dur); kfs.append(D.kf("KFTypeAlpha", [(dur - f, 1.0), (dur, 0.0)]))
    # original sound: "original_volume" (0–1, e.g. 0.2 ambience for authentic vlogs) wins over "mute_original"
    ov = C["original_volume"] if "original_volume" in C else (0.0 if C.get("mute_original", True) else 1.0)
    seg = D.video_seg(m, t0, dur, src, ov if au else 0.0, kfs); vsegs.append(seg); prev = s["sec"]

amat = D.audio_material(music, info[music][0])
bus = [beat(i) for i in range(1000) if beat(i) < END]
aseg = D.audio_seg(amat, IOFF, END, 0, 1.0, int(C.get("music_fade_out", 0.4) * US), bus)

T = C.get("title", {}); LIL = T.get("color", "#CDB4FF"); title_end = next((starts[k] for k, s in enumerate(edl) if s["sec"] != "title"), 0)
title_segs, head_segs, time_segs, cap_segs = [], [], [], []
if T.get("text") and title_end:
    sty = dict(size=T.get("size", 22), color=LIL, bold=True, border="#FFFFFF", x=0.0, y=T.get("y", 0.12))
    if T.get("typewriter", True): title_segs, _ = D.typewriter(T["text"], us(0.1, FPS), us(0.12, FPS), title_end, **sty)
    else: title_segs = [D.text_seg(D.text_material(T["text"], sty["size"], LIL, True, "#FFFFFF"), 0, title_end, 0.0, sty["y"])]
    if T.get("sub"):
        head_segs.append(D.text_seg(D.text_material(T["sub"], T.get("sub_size", 8), "#FFFFFF", True), beat(T.get("sub_from_beat", 4)) + IOFF, title_end, 0.0, T.get("sub_y", -0.18), 14002))

TL = C.get("time_labels")
def clock(s):
    m = re.search(TL["regex"], s["file"])
    if not m: return None
    dt = datetime.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S") + datetime.timedelta(seconds=s["src_in"])
    if TL.get("shift_hours") and dt >= datetime.datetime.strptime(TL.get("shift_from", "1970-01-01 00:00"), "%Y-%m-%d %H:%M"):
        dt += datetime.timedelta(hours=TL["shift_hours"])
    return dt.strftime("%-I:%M ") + ("am" if dt.hour < 12 else "pm")
def runs(fn):
    out = []
    for k, s in enumerate(edl):
        if s["sec"] in ("title", "outro"): continue
        v = fn(s)
        if v is None: continue
        if out and out[-1][0] == v and out[-1][2] == starts[k]: out[-1][2] = starts[k + 1]
        else: out.append([v, starts[k], starts[k + 1]])
    return out
if TL:
    time_segs = [D.text_seg(D.text_material(v, TL.get("size", 6)), x, y, TL.get("x", -0.80), 0.0, 14003) for v, x, y in runs(clock)]
CP = C.get("captions")
if CP:
    cap_segs = [D.text_seg(D.text_material(v, CP.get("size", 6)), x, y, CP.get("x", 0.78), 0.0, 14004) for v, x, y in runs(lambda s: s.get("caption"))]
SH = C.get("section_headers")
if SH:
    seen = set()
    for k, s in enumerate(edl):
        if s["sec"] in ("title", "outro") or s["sec"] in seen or not s.get("cap"): continue
        seen.add(s["sec"]); t0 = starts[k]
        head_segs.append(D.text_seg(D.text_material(s["cap"], SH.get("size", 12), LIL, True, "#FFFFFF"), t0, t0 + us(SH.get("seconds", 1.0), FPS), 0.0, SH.get("y", -0.62), 14002))
if C.get("outro_text"):
    ks = [k for k, s in enumerate(edl) if s["sec"] == "outro"]
    if ks: head_segs.append(D.text_seg(D.text_material(C["outro_text"], 14.0, LIL, True, "#FFFFFF"), starts[ks[-1]], END + IOFF, 0.0, 0.0, 14002))

D.d["tracks"] = [D.track("video", vsegs)] + ([D.track("video", [])] if C.get("reserve_overlay_track", True) else []) + [D.track("audio", [aseg])] \
    + [D.track("text", t) for t in (title_segs, head_segs, time_segs, cap_segs) if t]
D.finish(NAME, END + IOFF)

# ---- 4. cover + write + register ----
cover = os.path.join(ASSETS, "_cover.jpg")
subprocess.run([os.path.join(a.bin, "still"), edl[0]["asset"], str(edl[0]["src_in"] + 0.2), cover], check=True)
items = [(p, info[p][0], info[p][1], info[p][2], "video") for p in mats] + [(music, info[music][0], 0, 0, "music")]
write_draft(OUT, D, items, cover)
os.makedirs(os.path.join(ASSETS, "_build"), exist_ok=True)
shutil.copy(a.config, os.path.join(ASSETS, "_build", "project.json")); shutil.copy(C["edl"], os.path.join(ASSETS, "_build", "edl.json"))
print(f"OK {OUT}\n  {len(vsegs)} cảnh | {sum(len(t) for t in (title_segs, head_segs, time_segs, cap_segs))} đoạn chữ | {len(bus)} beat | {END/US:.3f}s")
