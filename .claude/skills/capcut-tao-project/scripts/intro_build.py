#!/usr/bin/env python3
"""Write an INTRO (video shots + title + optional typed line + typing SFX + optional separate intro music) into the
region 0 → intro_end of an EXISTING CapCut 4.6 draft. Intro is always VIDEO (TIEU_CHI_CHON_CANH.md §8c).

Usage: python3 intro_build.py "<draft>" INTRO_MATCH.json --bin "$BIN" --assets <assets_dir>
          [--alt 3=2,5=3]                                  use alternative k for a slot
          [--title "japan trip"] [--title-kind static|typewriter] [--title-color #CDB4FF] [--title-size 22] [--title-y 0.12]
          [--line "[osaka, katsuoji, kyoto]"] [--line-size 8] [--line-y -0.18] [--typing-sfx/--no-typing-sfx]
          [--intro-music intro.m4a --intro-music-volume 1.0 --intro-music-start 0]
          [--original-volume 0.0]
  INTRO_MATCH.json  from phan-canh-theo-beat/scripts/intro_match.py (slots on the beat grid of the intro's music)
Rules:
  - intro_end must equal a cut on the main video track (the body already starts there). If the project has no free
    intro region yet, build it with capcut_draft.py "intro": {"duration": …} (body is shifted after the intro).
  - removes old main-track shots and text that lie entirely inside the intro; keeps everything else.
  - typing SFX is synthesised (typing_sfx.py) so each click lands on the frame a character appears.
  - --intro-music: own audio track for 0→intro_end (whole-video music keeps playing unless the draft was built with
    the body after the intro). Without it the intro simply uses the whole-video music.
Backs up first, refuses if CapCut is running; media are hard-linked into <assets>/clips (CapCut sandbox reads ~/Movies).
"""
import argparse, json, os, shutil, subprocess, sys, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capcut_lib import Draft, ROOT, US, backup, capcut_running, us, write_draft

ap = argparse.ArgumentParser(); ap.add_argument("draft"); ap.add_argument("match"); ap.add_argument("--bin", required=True); ap.add_argument("--assets", required=True)
ap.add_argument("--alt", default=""); ap.add_argument("--title"); ap.add_argument("--title-kind", choices=["static", "typewriter"])
ap.add_argument("--title-color"); ap.add_argument("--title-size", type=float, default=22); ap.add_argument("--title-y", type=float, default=0.12)
ap.add_argument("--line"); ap.add_argument("--line-size", type=float, default=8); ap.add_argument("--line-y", type=float, default=-0.18)
ap.add_argument("--typing-sfx", dest="sfx", action="store_true", default=None); ap.add_argument("--no-typing-sfx", dest="sfx", action="store_false")
ap.add_argument("--intro-music"); ap.add_argument("--intro-music-volume", type=float, default=1.0); ap.add_argument("--intro-music-start", type=float, default=0.0)
ap.add_argument("--original-volume", type=float, default=0.0)
a = ap.parse_args(); O = a.draft.rstrip("/"); ASSETS = os.path.expanduser(a.assets); HERE = os.path.dirname(os.path.abspath(__file__))
if capcut_running(): sys.exit("CapCut đang mở — nhờ người dùng tắt trước.")
m = json.load(open(a.match)); END = us(m["intro_end"]); alt = {int(k): int(v) for k, v in (x.split("=") for x in a.alt.split(",") if x)}
print("backup:", backup([os.path.join(O, f) for f in ("draft_info.json", "draft_info.json.bak", "template-2.tmp", "draft_meta_info.json", "draft_settings")]
                        + [os.path.join(ROOT, "root_meta_info.json")], os.path.join(ASSETS, "_backup"), "truoc_intro_build"))
D = Draft.load(O); M = D.M
main = next(t for t in D.d["tracks"] if t["type"] == "video" and t["segments"])
cuts = {s["target_timerange"]["start"] for s in main["segments"]}
if END not in cuts and any(s["target_timerange"]["start"] < END < s["target_timerange"]["start"] + s["target_timerange"]["duration"] for s in main["segments"]):
    sys.exit(f"intro_end {END/US:.3f}s rơi giữa một cảnh — chỉnh intro_match (--intro-end) cho trùng điểm cắt đầu phần thân")
main["segments"] = [s for s in main["segments"] if s["target_timerange"]["start"] >= END]
txt = {t["id"]: json.loads(t["content"])["text"] for t in M["texts"]}; dropped = []
for t in D.d["tracks"]:
    intro_only_audio = t["type"] == "audio" and t["segments"] and all(x["target_timerange"]["start"] + x["target_timerange"]["duration"] <= END for x in t["segments"])
    if t["type"] == "text" or intro_only_audio:        # old intro texts and old intro-only sounds (typing SFX, intro music)
        keep = []
        for s in t["segments"]:
            st = s["target_timerange"]["start"]; en = st + s["target_timerange"]["duration"]
            if en <= END and st < END: dropped.append(txt.get(s["material_id"], "(âm thanh intro cũ)"))
            else: keep.append(s)
        t["segments"] = keep
print("bỏ phần intro cũ:", sorted(set(dropped))[:12], "…" if len(set(dropped)) > 12 else "")
# --- video shots
os.makedirs(os.path.join(ASSETS, "clips"), exist_ok=True)
def place(src):
    dst = os.path.join(ASSETS, "clips", os.path.basename(src))
    if not os.path.exists(dst):
        try: os.link(src, dst)
        except OSError: shutil.copy2(src, dst)
    return dst
chosen = [(s, (s["alternatives"][alt[s["slot"]] - 1] if s["slot"] in alt else s["choice"])) for s in m["slots"]]
paths = sorted({place(c["path"]) for _, c in chosen}); info = {}
for l in subprocess.run([os.path.join(a.bin, "media_info")] + paths, capture_output=True, text=True, check=True).stdout.splitlines():
    p, d, w, h, au = l.split("\t"); info[p] = (int(d), int(w), int(h), int(au))
existing = {mm["path"]: mm for mm in M["videos"] if mm["type"] == "video"}
starts = [us(s["start"]) for s, _ in chosen] + [END]; new = []
for k, (s, c) in enumerate(chosen):
    p = os.path.join(ASSETS, "clips", os.path.basename(c["path"])); d, w, h, au = info[p]
    mat = existing.get(p) or D.video_material(p, d, w, h, au); existing[p] = mat
    L = starts[k + 1] - starts[k]; src = us(c["src_in"])
    if src + L > d: src = max(0, d - L - US // 30)
    new.append(D.video_seg(mat, starts[k], L, src, a.original_volume if au else 0.0))
main["segments"] = new + main["segments"]
# --- title + typed line + typing SFX
T = m.get("title") or {}; kind = a.title_kind or ("typewriter" if T.get("kind") == "typewriter" and not a.line else "static")
color = a.title_color or T.get("color") or "#FFFFFF"; items = [(p, info[p][0], info[p][1], info[p][2], "video") for p in paths]
if a.title:
    sty = dict(size=a.title_size, color=color, bold=True, border="#FFFFFF" if color.upper() != "#FFFFFF" else None, x=0.0, y=a.title_y)
    if kind == "typewriter": segs, _ = D.typewriter(a.title, us(0.1), us(0.12), END, **sty)
    else: segs = [D.text_seg(D.text_material(a.title, a.title_size, color, True, sty["border"]), 0, END, 0.0, a.title_y, 14001)]
    D.d["tracks"].append(D.track("text", segs))
sfx = a.sfx if a.sfx is not None else len(m.get("clicks", [])) >= 4
if a.line:
    W = os.path.join(ASSETS, "sfx"); os.makedirs(W, exist_ok=True); wav = os.path.join(W, "typing_intro.wav"); tj = os.path.join(W, "typing_intro.json")
    subprocess.run([sys.executable, os.path.join(HERE, "typing_sfx.py"), a.line, wav, tj, "--start", "0.30", "--end", f"{END/US:.4f}"], check=True)
    tm = json.load(open(tj)); times = [us(t) for t in tm["times"]] + [END]
    D.d["tracks"].append(D.track("text", [D.text_seg(D.text_material(a.line[:i], a.line_size, "#FFFFFF", True), times[i - 1], times[i], 0.0, a.line_y, 14005) for i in range(1, len(a.line) + 1)]))
    if sfx:
        wv = wave.open(wav); sd = int(wv.getnframes() / wv.getframerate() * US); wv.close()
        am = D.audio_material(wav, sd); D.d["tracks"].append(D.track("audio", [D.audio_seg(am, 0, min(sd, END), 0, 1.0)])); items.append((wav, sd, 0, 0, "music"))
# --- separate intro music
if a.intro_music:
    src = os.path.join(ASSETS, "music", os.path.basename(a.intro_music)); os.makedirs(os.path.dirname(src), exist_ok=True)
    if not os.path.exists(src):
        try: os.link(a.intro_music, src)
        except OSError: shutil.copy2(a.intro_music, src)
    d = int(subprocess.run([os.path.join(a.bin, "media_info"), src], capture_output=True, text=True, check=True).stdout.split("\t")[1])
    am = D.audio_material(src, d); L = min(END, d - us(a.intro_music_start))
    D.d["tracks"].append(D.track("audio", [D.audio_seg(am, 0, L, us(a.intro_music_start), a.intro_music_volume, fade_out_us=min(300000, L // 4))])); items.append((src, d, 0, 0, "music"))
D.d["tracks"] = [t for t in D.d["tracks"] if t["segments"] or t["type"] == "video"]   # drop emptied text/audio tracks, keep empty video (motion graphics)
D.prune_materials(); D.finish(D.d.get("name") or os.path.basename(O), D.d["duration"])
write_draft(O, D, items, new=False)
print(f"OK intro {END/US:.3f}s: {len(new)} cảnh video" + (f", tiêu đề '{a.title}' ({kind})" if a.title else "") + (f", dòng gõ + {'tiếng gõ' if sfx else 'không tiếng gõ'}" if a.line else "")
      + (", nhạc intro riêng" if a.intro_music else ", dùng nhạc chung của video") + " — chạy validate_draft.py")
