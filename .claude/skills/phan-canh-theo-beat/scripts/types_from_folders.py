#!/usr/bin/env python3
"""Make a clip-type table (file<TAB>type) from the footage folders made by loc-gom-footage, for intro_match.py --types.

Usage: python3 types_from_folders.py FOOTAGE_ROOT OUT_types.tsv
Role folders map to types:  02_A-roll… → selfie, 03_B-roll… → landscape, 04_Am_thuc → food,
05_Di_chuyen → transit, 06_Mua_sam → shop, 07_Trai_nghiem → experience, 08_Outro → landscape.
Other folder names (day/location folders) are matched by keywords (an/bua/com/lau → food, deo/duong/view/song/thac/
hoang_hon → landscape, karaoke/cafe/pho → experience, selfie → selfie); unknown = empty (Claude labels by eye).
Only the file name is used, so it also works for hard links of the same files in a CapCut assets folder.
"""
import os, re, sys
root, out = sys.argv[1], sys.argv[2]
ROLE = [(r"A-roll|Selfie|Noi_chuyen", "selfie"), (r"B-roll|Canh_dep|Outro", "landscape"), (r"Am_thuc", "food"),
        (r"Di_chuyen|Chuyen_canh", "transit"), (r"Mua_sam", "shop"), (r"Trai_nghiem|Vui_choi", "experience")]
KEY = [(r"(^|_)(An|Bua|Com|Lau|BBQ|Okonomiyaki|Udon|Matcha|Cafe_matcha)(_|$)", "food"),
       (r"Deo|Duong|Viewpoint|Song|Thac|Hoang_hon|Lau_dai|Fushimi|Torii|Ruong|Canh_dong", "landscape"),
       (r"Karaoke|Pho_co|Game|Gachapon|Thuy_cung|Chua|Det_lanh|Hang", "experience"), (r"Selfie", "selfie"),
       (r"Tau|Xe|San_bay|Di_chuyen", "transit")]
rows = {}
for d, _, files in os.walk(root):
    rel = os.path.relpath(d, root)
    if rel.startswith("_LRF") or "/_LRF" in rel: continue
    t = next((ty for pat, ty in ROLE if re.search(pat, rel)), "") or next((ty for pat, ty in KEY if re.search(pat, rel, re.I)), "")
    for f in files:
        if f.lower().endswith((".mp4", ".mov")) and t: rows.setdefault(f, t)
open(out, "w").write("".join(f"{f}\t{t}\n" for f, t in sorted(rows.items())))
from collections import Counter
print(len(rows), "clip có loại:", dict(Counter(rows.values())))
