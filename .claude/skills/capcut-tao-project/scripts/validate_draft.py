#!/usr/bin/env python3
"""Structural check of a CapCut draft before telling the user to open it.

Usage: python3 validate_draft.py "<draft folder>"
Checks: JSON parses (draft, meta, root list); no overlapping segments in any track; no zero-length
segments; main video track has no gaps; every material_id / extra_material_ref exists; video source
ranges inside the media duration; keyframes inside their segment; every media path exists and is
under ~/Movies (sandbox-readable); project registered in root_meta_info.json with the same id.
Exit code 1 if anything fails.
"""
import json, os, sys
O = sys.argv[1].rstrip("/"); R = os.path.dirname(O); home_movies = os.path.expanduser("~/Movies/")
d = json.load(open(os.path.join(O, "draft_info.json"))); meta = json.load(open(os.path.join(O, "draft_meta_info.json")))
root = json.load(open(os.path.join(R, "root_meta_info.json")))
M = d["materials"]; ids = {x["id"] for a in M.values() if isinstance(a, list) for x in a if isinstance(x, dict) and "id" in x}
vid = {m["id"]: m for m in M.get("videos", [])}; err = []; warn = []
for ti, t in enumerate(d["tracks"]):
    segs = sorted(t["segments"], key=lambda s: s["target_timerange"]["start"]); end = 0
    for s in segs:
        a = s["target_timerange"]["start"]; L = s["target_timerange"]["duration"]
        if a < end: err.append(f"track {ti}: chồng lấn tại {a/1e6:.3f}s")
        if L <= 0: err.append(f"track {ti}: đoạn dài 0 tại {a/1e6:.3f}s")
        end = max(end, a + L)
        if s["material_id"] not in ids: err.append(f"track {ti}: thiếu material")
        err += [f"track {ti}: thiếu ref" for r in s["extra_material_refs"] if r not in ids]
        m = vid.get(s["material_id"])
        if m and m["type"] == "video" and s["source_timerange"]["start"] + s["source_timerange"]["duration"] > m["duration"]: err.append(f"vượt độ dài nguồn: {m['material_name']}")
        for k in s.get("common_keyframes") or []:
            err += ["keyframe ngoài đoạn" for p in k["keyframe_list"] if p["time_offset"] > L]
    print(f"track {ti:2d} {t['type']:5s} {len(segs):4d} đoạn  hết {end/1e6:7.3f}s")
main = next(t for t in d["tracks"] if t["type"] == "video" and t["segments"])["segments"]
gaps = {main[i + 1]["target_timerange"]["start"] - main[i]["target_timerange"]["start"] - main[i]["target_timerange"]["duration"] for i in range(len(main) - 1)}
if gaps - {0}: err.append(f"track video chính có khoảng hở/chồng: {sorted(gaps)[:5]}")
for m in M.get("videos", []) + M.get("audios", []):
    if not os.path.exists(m["path"]): err.append("không thấy file: " + m["path"])
    elif not m["path"].startswith(home_movies): warn.append(m["path"])
e = next((x for x in root["all_draft_store"] if x["draft_fold_path"] == O), None)
if not e: err.append("chưa đăng ký trong root_meta_info.json")
elif not (e["draft_id"] == d["id"] == meta["draft_id"]): err.append("draft_id không khớp giữa draft / meta / root")
print(f"thời lượng {d['duration']/1e6:.3f}s | video {len(M.get('videos', []))} | audio {len(M.get('audios', []))} | text {len(M.get('texts', []))}")
if warn: print(f"LƯU Ý: {len(warn)} file nằm ngoài ~/Movies (nơi người dùng đã chọn). CapCut sandbox có thể báo thiếu media, khi đó cần liên kết lại hoặc import folder một lần. Vd: {warn[0]}")
print("LỖI:\n  " + "\n  ".join(err[:20]) if err else "OK — không thấy lỗi cấu trúc")
sys.exit(1 if err else 0)
