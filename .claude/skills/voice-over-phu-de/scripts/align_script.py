#!/usr/bin/env python3
"""Time a subtitle script against the spoken phrases found by vo_segments.py (no speech recognition).

Usage: python3 align_script.py SCRIPT.txt OUT_subs.json VO1.json [VO2.json …] [--lang vi|en|bi] [--max-words 6] [--max-chars 42]
          [--review review.md]
SCRIPT.txt: one subtitle sentence per line, in speaking order (blank lines / '#' ignored).
  --lang bi : each line is "tiếng Việt || English" (or separated by a TAB) — user supplies both.
Method: sentences are mapped to phrase boundaries in order — each sentence's share of the total
characters ≈ its share of speaking time; a boundary always falls in a real pause. Long sentences are
wrapped to ≤ 2 lines of --max-chars; anything shown < 1 s is flagged. Writes OUT (list of
{"start","end","vi","en"}) and a review table (Markdown) to show the user BEFORE writing to CapCut.
Fix a wrong row by editing OUT_subs.json (times in seconds) — or re-split the script line.
"""
import argparse, json, textwrap
def _wrap2(x, n):
    """Wrap to <=2 lines WITHOUT dropping words: if 2 lines of n chars are not enough, widen the lines
    (the review table flags these as too long so the sentence can be split into 2 cards)."""
    if not x: return ""
    lines = textwrap.wrap(x, n)
    if len(lines) <= 2: return "\n".join(lines)
    w = n
    while len(lines) > 2: w += 2; lines = textwrap.wrap(x, w)
    return "\n".join(lines)

ap = argparse.ArgumentParser(); ap.add_argument("script"); ap.add_argument("out"); ap.add_argument("vo", nargs="+")
ap.add_argument("--lang", default="vi", choices=["vi", "en", "bi"]); ap.add_argument("--max-chars", type=int, default=42); ap.add_argument("--review")
ap.add_argument("--max-words", type=int, help="single-language: max words per card (default 6; 0 = whole sentence). Ignored for --lang bi")
a = ap.parse_args()
MAXW = 0 if a.lang == "bi" else (6 if a.max_words is None else a.max_words)
lines = []
for l in open(a.script, encoding="utf-8"):
    l = l.strip()
    if not l or l.startswith("#"): continue
    if a.lang == "bi":
        sep = "||" if "||" in l else "\t"
        if sep not in l: raise SystemExit(f"dòng thiếu bản thứ 2 (cần 'Việt || English'): {l}")
        vi, en = [s.strip() for s in l.split(sep, 1)]
    else: vi, en = (l, "") if a.lang == "vi" else ("", l)
    lines.append((vi, en))
ph = sorted((p for f in a.vo for p in json.load(open(f))["phrases"]), key=lambda p: p["tl_start"])
if not ph: raise SystemExit("không có cụm lời nào")
if len(lines) > len(ph): print(f"LƯU Ý: {len(lines)} câu nhưng chỉ {len(ph)} cụm lời — vài câu sẽ chung một cụm (cần chỉnh tay)")
cum, t = [], 0
for p in ph: t += p["tl_end"] - p["tl_start"]; cum.append(t)          # speech time at end of each phrase
L = [max(1, len((vi or en).replace(" ", ""))) for vi, en in lines]; tot = sum(L)
ends, acc, j = [], 0, 0
for k, l in enumerate(L):
    acc += l
    if k == len(L) - 1: ends.append(len(ph) - 1); break
    target = acc / tot * cum[-1]; lo = j + (0 if not ends else 0)
    hi = len(ph) - (len(L) - k)                 # leave ≥1 phrase for each remaining sentence when possible
    hi = max(hi, lo)
    best = min(range(lo, hi + 1), key=lambda i: abs(cum[i] - target)) if hi >= lo else lo
    ends.append(best); j = best + 1
subs, s0 = [], 0
wrap = lambda x: _wrap2(x, a.max_chars)
for k, (vi, en) in enumerate(lines):
    e = ends[k]; st = ph[min(s0, len(ph) - 1)]["tl_start"]; en_t = ph[e]["tl_end"]
    subs.append({"start": round(st, 3), "end": round(max(en_t, st + 1.0), 3), "vi": wrap(vi), "en": wrap(en)}); s0 = e + 1
for i in range(len(subs) - 1):                     # never overlap the next one
    subs[i]["end"] = min(subs[i]["end"], subs[i + 1]["start"])
import re
def chunks(words, k):
    n = len(words); m = -(-n // k); cuts = [round(n * j / m) for j in range(1, m)]
    for c in range(len(cuts)):
        for d in (0, -1, 1):
            p = cuts[c] + d
            if 0 < p < n and re.search(r"[,.;:?!]$", words[p - 1]) and p - (cuts[c - 1] if c else 0) <= k and (cuts[c + 1] if c + 1 < len(cuts) else n) - p <= k:
                cuts[c] = p; break
    b = [0] + cuts + [n]; return [(b[j], b[j + 1]) for j in range(m)]
if MAXW:   # single language: ≤ MAXW words per card, time split by character share (no word timings here)
    out = []
    for x in subs:
        words = (x["vi"] or x["en"]).replace("\n", " ").split()
        if len(words) <= MAXW: out.append(x); continue
        parts = chunks(words, MAXW); L = [len(" ".join(words[p:q])) for p, q in parts]; T = x["end"] - x["start"]; t = x["start"]
        for (p, q), l in zip(parts, L):
            seg = " ".join(words[p:q]); e = round(t + T * l / sum(L), 3)
            out.append({"start": round(t, 3), "end": e, "vi": seg if x["vi"] else "", "en": seg if x["en"] else ""}); t = e
    subs = out
json.dump(subs, open(a.out, "w"), indent=1, ensure_ascii=False)
rows = ["| # | Bắt đầu | Kết thúc | Tiếng Việt | English |", "|---|---|---|---|---|"]
for i, s in enumerate(subs, 1):
    flag = (" ⚠️ <1s" if s["end"] - s["start"] < 1.0 else "") + (" ⚠️ câu dài, nên tách 2 thẻ" if not MAXW and any(len(x) > a.max_chars for t in (s["vi"], s["en"]) for x in t.split("\n")) else "")
    rows.append(f"| {i} | {s['start']:.2f}s | {s['end']:.2f}s{flag} | {s['vi'].replace(chr(10), ' / ')} | {s['en'].replace(chr(10), ' / ')} |")
md = "\n".join(rows); print(md)
if a.review: open(a.review, "w", encoding="utf-8").write("# Bảng canh giờ phụ đề — cần duyệt\n\n" + md + "\n")
