#!/usr/bin/env python3
"""Write voice-over, original-speech unmuting, a fixed music volume, cinematic subtitles and an optional
letterbox into an EXISTING CapCut 4.6 draft (made by capcut-tao-project). Backs up first; refuses if
CapCut is running; never touches the audio/video originals (segments just point into them).

Usage: python3 add_vo_subs.py "<draft folder>" --bin "$BIN" --assets <assets_dir>
          [--vo vo1.json vo2.json …]           voice-over plans from vo_segments.py (file must be readable by CapCut)
          [--speech-files DJI_a.MP4 DJI_b.MP4]  main-track clips whose ORIGINAL sound is turned back on
          [--speech-volume 1.0] [--vo-volume 1.0]
          [--music-volume 0.25]                 fixed volume of the music segment (from loudness.py, user-approved)
          [--subs subs.json] [--letterbox 2.35]
Subtitle style "cinematic": white, thin (no stroke), soft shadow, centred low; bilingual = Vietnamese on top,
English smaller/greyer below. Each language is its own text track. Letterbox = transparent PNG with black
bars on an extra video track above the picture (aspect ratio given, e.g. 2.35).
"""
import argparse, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "capcut-tao-project", "scripts"))
from capcut_lib import Draft, ROOT, US, backup, capcut_running, us, write_draft

ap = argparse.ArgumentParser(); ap.add_argument("draft"); ap.add_argument("--bin", required=True); ap.add_argument("--assets", required=True)
ap.add_argument("--vo", nargs="*", default=[]); ap.add_argument("--speech-files", nargs="*", default=[])
ap.add_argument("--speech-volume", type=float, default=1.0); ap.add_argument("--vo-volume", type=float, default=1.0)
ap.add_argument("--music-volume", type=float); ap.add_argument("--subs"); ap.add_argument("--letterbox", type=float)
ap.add_argument("--letterbox-px", type=int, help="fixed bar height in px (use this for vertical 9:16 video, e.g. 120)")
ap.add_argument("--sub-style", default="cinematic", choices=["cinematic", "yellow-italic"], help="cinematic = trắng mảnh + bóng mờ; yellow-italic = vàng ấm #F0D66B, đậm nghiêng, viền tối mảnh, không bóng (mẫu phim, dự án Hà Giang)")
ap.add_argument("--vi-size", type=float, default=7.0); ap.add_argument("--en-size", type=float, default=5.5)
ap.add_argument("--vi-y", type=float, help="subtitle y (half-canvas units, -1 = bottom); default -0.76 bilingual / -0.82"); ap.add_argument("--en-y", type=float, help="English line y; default -0.88 bilingual")
a = ap.parse_args(); O = a.draft.rstrip("/"); ASSETS = os.path.expanduser(a.assets)
if capcut_running(): sys.exit("CapCut đang mở — nhờ người dùng tắt trước.")
print("backup:", backup([os.path.join(O, f) for f in ("draft_info.json", "draft_meta_info.json", "draft_settings")] + [os.path.join(ROOT, "root_meta_info.json")],
                        os.path.join(ASSETS, "_backup"), "truoc_voice_over_phu_de"))
D = Draft.load(O); M = D.M; items = []; END = D.d["duration"]

# --- music volume (the longest audio segment = music) ---
if a.music_volume is not None:
    segs = [s for t in D.d["tracks"] if t["type"] == "audio" for s in t["segments"]]
    mus = max(segs, key=lambda s: s["target_timerange"]["duration"]); mus["volume"] = a.music_volume; mus["last_nonzero_volume"] = a.music_volume
    print(f"nhạc: volume {a.music_volume:.2f}")

# --- voice-over segments (several cuts of the same file, silences shortened) ---
vo_segs = []
for f in a.vo:
    plan = json.load(open(f)); path = plan["file"]
    if not os.path.exists(path): sys.exit("không thấy file voice over: " + path)
    dur = int(subprocess.run([os.path.join(a.bin, "media_info"), path], capture_output=True, text=True, check=True).stdout.split("\t")[1])
    mat = D.audio_material(path, dur); items.append((path, dur, 0, 0, "music"))
    for p in plan["phrases"]:
        t0 = us(p["tl_start"]); L = us(p["src_end"]) - us(p["src_start"])
        if t0 + L > END: print(f"WARN: lời đọc vượt cuối video ({(t0+L)/US:.2f}s > {END/US:.2f}s) — kéo dài video hoặc rút kịch bản"); L = max(0, END - t0)
        if L > 0: vo_segs.append(D.audio_seg(mat, t0, L, us(p["src_start"]), a.vo_volume))
vo_segs.sort(key=lambda s: s["target_timerange"]["start"])
for i in range(len(vo_segs) - 1):        # same track → no overlap
    s, n = vo_segs[i]["target_timerange"], vo_segs[i + 1]["target_timerange"]
    if s["start"] + s["duration"] > n["start"]: s["duration"] = n["start"] - s["start"]; vo_segs[i]["source_timerange"]["duration"] = s["duration"]
if vo_segs: D.d["tracks"].append(D.track("audio", vo_segs)); print(f"voice over: {len(vo_segs)} đoạn")

# --- original speech: unmute chosen clips on the main video track ---
if a.speech_files:
    main = next(t for t in D.d["tracks"] if t["type"] == "video" and t["segments"]); byid = {m["id"]: m for m in M["videos"]}; n = 0
    for s in main["segments"]:
        if byid[s["material_id"]]["material_name"] in a.speech_files: s["volume"] = a.speech_volume; s["last_nonzero_volume"] = a.speech_volume; n += 1
    print(f"bật tiếng gốc: {n} cảnh")

# --- subtitles ---
def STY(lang):
    if a.sub_style == "yellow-italic":
        return dict(color="#F0D66B", bold=True, italic=True, border="#151515", border_width=0.04, border_alpha=0.85, shadow=False)
    return dict(color="#FFFFFF" if lang == "vi" else "#E6E6E6", bold=False, border=None, shadow=True)
if a.subs:
    subs = json.load(open(a.subs)); bi = any(s["vi"] for s in subs) and any(s["en"] for s in subs)
    vi_t, en_t = [], []
    for s in subs:
        t0, t1 = us(s["start"]), min(us(s["end"]), END)
        if t1 <= t0: continue
        if s["vi"]: vi_t.append(D.text_seg(D.text_material(s["vi"], a.vi_size, **STY("vi")), t0, t1, 0.0, a.vi_y if a.vi_y is not None else (-0.76 if bi else -0.82), 14010))
        if s["en"]: en_t.append(D.text_seg(D.text_material(s["en"], a.en_size if bi else a.vi_size, **STY("en" if bi else "vi")), t0, t1, 0.0, a.en_y if a.en_y is not None else (-0.88 if bi else -0.82), 14011))
    for tr in (vi_t, en_t):
        if tr: D.d["tracks"].append(D.track("text", tr))
    print(f"phụ đề: {len(vi_t)} dòng Việt, {len(en_t)} dòng Anh")

# --- letterbox bars ---
if a.letterbox or a.letterbox_px:
    from PIL import Image, ImageDraw
    W, H = D.d["canvas_config"]["width"], D.d["canvas_config"]["height"]
    bar = a.letterbox_px if a.letterbox_px else max(0, int(round((H - W / a.letterbox) / 2)))
    if bar > H * 0.2: sys.exit(f"dải đen {bar}px quá dày (>20% chiều cao) — với video dọc dùng --letterbox-px, vd 120")
    png = os.path.join(ASSETS, "overlays", f"letterbox_{bar}px.png"); os.makedirs(os.path.dirname(png), exist_ok=True)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im); d.rectangle([0, 0, W, bar - 1], fill=(0, 0, 0, 255)); d.rectangle([0, H - bar, W, H], fill=(0, 0, 0, 255)); im.save(png)
    m = D.video_material(png, 0, W, H, False, photo=True); items.append((png, 5_000_000, W, H, "photo"))
    D.d["tracks"].append(D.track("video", [D.video_seg(m, 0, END, 0, 1.0)])); print(f"letterbox: dải đen {bar}px trên/dưới")

D.finish(D.d.get("name") or os.path.basename(O), END)
write_draft(O, D, items, new=False)
print("OK — chạy validate_draft.py rồi báo người dùng mở CapCut kiểm tra")
