#!/usr/bin/env python3
"""Time subtitles from a WORD-LEVEL transcript (ElevenLabs creative_transcribe_audio → transcripts[].words)
instead of guessing from pauses. More accurate than align_script.py; use it whenever a transcript exists.

Usage: python3 align_words.py SCRIPT.txt WORDS.json VO.json OUT_subs.json [--lang vi|en|bi] [--max-words 6] [--max-chars 42] [--review review.md]
  Single language (vi/en): each card shows at most --max-words words (default 6, TIEU_CHI_CHON_CANH.md §8b),
  timed to the words being spoken. Bilingual: one sentence per card, ≤ 2 lines per language.
  SCRIPT.txt  one subtitle sentence per line (bilingual: "Việt || English"); emotion tags like [excited] are ignored
  WORDS.json  the transcript JSON as returned/downloaded (a list of words, or {"words": [...]}, or {"transcripts": [{"words": [...]}]});
              each word needs text ("text"/"word") and "start"/"end" in seconds of the ORIGINAL audio file
  VO.json     from vo_segments.py — maps original-audio time to timeline time (silences shortened)
Each script sentence is matched to the transcript by walking words in order with fuzzy token matching
(accents/punctuation ignored), so the subtitle starts on its first spoken word and ends on its last.
Words the speaker skipped/added are tolerated; a sentence that cannot be found is flagged in the review.
"""
import argparse, json, re, textwrap, unicodedata
def _wrap2(x, n):
    """Wrap to <=2 lines WITHOUT dropping words: if 2 lines of n chars are not enough, widen the lines
    (the review table flags these as too long so the sentence can be split into 2 cards)."""
    if not x: return ""
    lines = textwrap.wrap(x, n)
    if len(lines) <= 2: return "\n".join(lines)
    w = n
    while len(lines) > 2: w += 2; lines = textwrap.wrap(x, w)
    return "\n".join(lines)
from difflib import SequenceMatcher

ap = argparse.ArgumentParser(); ap.add_argument("script"); ap.add_argument("words"); ap.add_argument("vo"); ap.add_argument("out")
ap.add_argument("--lang", default="vi", choices=["vi", "en", "bi"]); ap.add_argument("--match", choices=["vi", "en"], help="language of the VOICE (default: en for --lang en/bi, vi for --lang vi)"); ap.add_argument("--max-chars", type=int, default=42); ap.add_argument("--review")
ap.add_argument("--max-words", type=int, help="single-language subtitles: max words per card (default 6; 0 = whole sentence). Ignored for --lang bi")
a = ap.parse_args()
MAXW = 0 if a.lang == "bi" else (6 if a.max_words is None else a.max_words)
MATCH = a.match or ("vi" if a.lang == "vi" else "en")
def norm(s):
    s = unicodedata.normalize("NFD", s.lower()).replace("đ", "d")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z0-9]+", s)
raw = json.load(open(a.words))
if isinstance(raw, dict): raw = raw.get("words") or [w for t in raw.get("transcripts", []) for w in t.get("words", [])]
W = []
for w in raw:
    if w.get("type") in ("spacing", "audio_event"): continue
    for tok in norm(w.get("text") or w.get("word") or ""): W.append((tok, float(w["start"]), float(w["end"])))
if not W: raise SystemExit("transcript không có từ nào (kiểm tra WORDS.json)")
lines = []
for l in open(a.script, encoding="utf-8"):
    l = re.sub(r"\[[^\]]*\]", "", l).strip()
    if not l or l.startswith("#"): continue
    if a.lang == "bi":
        sep = "||" if "||" in l else "\t"
        vi, en = [s.strip() for s in l.split(sep, 1)]
    else: vi, en = (l, "") if a.lang == "vi" else ("", l)
    lines.append((vi, en))
ph = json.load(open(a.vo))["phrases"]
def to_tl(t):                         # original-audio second -> timeline second
    for p in ph:
        if p["src_start"] - 0.05 <= t <= p["src_end"] + 0.05: return p["tl_start"] + min(max(t, p["src_start"]), p["src_end"]) - p["src_start"]
    prev = [p for p in ph if p["src_end"] < t]
    return (prev[-1]["tl_end"] if prev else ph[0]["tl_start"])
subs, i, miss = [], 0, []
for k, (vi, en) in enumerate(lines):
    toks = norm((en or vi) if MATCH == "en" else (vi or en)); n = max(1, len(toks))
    best = (0, i, i + n)
    for s in range(i, min(len(W), i + 40 + n)):            # search a little ahead of the cursor
        for e in (s + n - 1, s + n, s + n + 1):
            if e <= s or e > len(W): continue
            r = SequenceMatcher(None, toks, [w[0] for w in W[s:e]]).ratio()
            if r > best[0]: best = (r, s, e)
    r, s, e = best
    s = min(s, len(W) - 1); e = max(s + 1, min(e, len(W)))
    if r < 0.5: miss.append(k + 1)
    st, en_t = to_tl(W[s][1]), to_tl(W[min(e, len(W)) - 1][2])
    wrap = lambda x: _wrap2(x, a.max_chars)
    subs.append({"start": round(st, 3), "end": round(max(en_t, st + 1.0), 3), "vi": wrap(vi), "en": wrap(en), "match": round(r, 2), "_s": s, "_e": e}); i = e
for j in range(len(subs) - 1):
    # words left between this sentence and the next (spelled differently by the recogniser) still belong to it
    gap_end = subs[j + 1]["_s"] - 1
    if gap_end >= subs[j]["_e"]: subs[j]["end"] = round(max(subs[j]["end"], to_tl(W[gap_end][2])), 3)
    subs[j]["end"] = min(subs[j]["end"], subs[j + 1]["start"])
def chunks(words, k):
    """split into ceil(n/k) balanced chunks of <= k words, nudging a cut to just after , . ; ? ! when it is 1 word away"""
    n = len(words); m = -(-n // k); cuts = [round(n * j / m) for j in range(1, m)]
    for c in range(len(cuts)):
        for d in (0, -1, 1):
            p = cuts[c] + d
            if 0 < p < n and re.search(r"[,.;:?!]$", words[p - 1]) and p - (cuts[c - 1] if c else 0) <= k and (cuts[c + 1] if c + 1 < len(cuts) else n) - p <= k:
                cuts[c] = p; break
    b = [0] + cuts + [n]; return [(b[j], b[j + 1]) for j in range(m)]
if MAXW:
    out = []
    for x in subs:
        txt = x["vi"] or x["en"]; words = txt.replace("\n", " ").split()
        if len(words) <= MAXW: out.append(x); continue
        s0, e0 = x["_s"], x["_e"]; span = max(1, e0 - s0); parts = chunks(words, MAXW)
        for j, (p, q) in enumerate(parts):
            ws = s0 + min(span - 1, round(p / len(words) * span)); we = s0 + max(1, round(q / len(words) * span)) - 1
            st = x["start"] if j == 0 else round(to_tl(W[ws][1]), 3)
            en_t = x["end"] if j == len(parts) - 1 else round(to_tl(W[min(we, len(W) - 1)][2]), 3)
            seg = " ".join(words[p:q]); out.append({"start": st, "end": en_t, "vi": seg if x["vi"] else "", "en": seg if x["en"] else "", "match": x["match"], "_s": ws, "_e": we + 1})
    for j in range(len(out) - 1):
        out[j]["end"] = out[j + 1]["start"] if out[j]["end"] > out[j + 1]["start"] else out[j]["end"]
    subs = out
for x in subs: x.pop("_s"); x.pop("_e")
json.dump(subs, open(a.out, "w"), indent=1, ensure_ascii=False)
rows = ["| # | Bắt đầu | Kết thúc | Khớp | Tiếng Việt | English |", "|---|---|---|---|---|---|"]
for j, s in enumerate(subs, 1):
    f = (" ⚠️" if s["match"] < 0.5 or s["end"] - s["start"] < 1.0 else "") + (" ⚠️ câu dài, nên tách 2 thẻ" if not MAXW and any(len(x) > a.max_chars for t in (s["vi"], s["en"]) for x in t.split("\n")) else "")
    rows.append(f"| {j} | {s['start']:.2f}s | {s['end']:.2f}s | {s['match']:.0%}{f} | {s['vi'].replace(chr(10), ' / ')} | {s['en'].replace(chr(10), ' / ')} |")
md = "\n".join(rows); print(md)
if miss: print(f"\nCÂU KHÔNG TÌM THẤY RÕ trong bản thu (máy đọc khác kịch bản?): {miss}")
if a.review: open(a.review, "w", encoding="utf-8").write("# Bảng canh giờ phụ đề (theo bản chuyển giọng thành chữ) — cần duyệt\n\n" + md + "\n")
