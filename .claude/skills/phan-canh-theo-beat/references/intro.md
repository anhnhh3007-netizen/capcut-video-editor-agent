# Quy trình làm INTRO (luôn bằng video — TIEU_CHI_CHON_CANH.md §8c)

## 0. Hỏi trước
- **Có video mẫu cho intro không?** (có thể là cùng video mẫu của cả video, hoặc một mẫu riêng chỉ cho intro)
- **Nhạc intro:** có nhạc riêng cho intro không?
  - **Có** → người dùng gửi file → phân tích nhạc intro (skill nhac-cat-doan-do-beat: BPM, phách đầu, mốc beat). Intro cắt theo beat **của nhạc intro**; khi tạo project dùng `"intro": {"duration": …}` trong `project.json` để phần thân và nhạc chính bắt đầu SAU intro, rồi `intro_build.py --intro-music`.
  - **Không** → intro dùng **nhạc chung của cả video**, cắt theo beat của bài đó; vùng intro = các phách đầu bài (vd 8 phách).

## A. CÓ video mẫu → "làm tương tự"
1. **Đo intro mẫu** → `python3 ~/.claude/skills/phan-tich-video-mau/scripts/intro_spec.py MẪU.mp4 $W/intro --bin "$BIN" [--max 10] [--end <s>]`
   - Ra: điểm cắt, độ dài từng cảnh **theo phách nhạc mẫu**, cảnh nào giống ảnh tĩnh, khung + màu + kiểu hiện của tiêu đề (gõ dần / đứng yên), tiếng click/gõ.
   - Xem `intro_sheet.jpg` (Read), **điền `type` cho từng shot** trong `intro_spec.json` (selfie/food/landscape/shop/experience/transit/detail). Nếu `intro_end` sai (vd lẫn chữ của cảnh sau) → chạy lại với `--end`.
2. **Ghép footage vào từng ô** → `types_from_folders.py FOOTAGE $W/types.tsv` (loại cảnh từ folder vai trò/địa điểm), rồi
   `python3 scripts/intro_match.py $W/intro/intro_spec.json scan.tsv $W/match --bin "$BIN" --beat <phách nhạc intro> --first <phách đầu> --clips-file clips.txt --types $W/types.tsv [--exclude body_files.txt] [--intro-end <s>]`
   - Độ dài ô = số phách của mẫu × phách nhạc của mình (bám lưới nửa phách); ô mẫu là ảnh tĩnh → chọn khoảnh khắc video đứng yên nhất.
   - Phạt cảnh trông giống cảnh vừa chọn → intro đa dạng. Top-3 mỗi ô.
3. **Tự xem `intro_compare.jpg`** (hàng 1 = mẫu, 3 hàng dưới = gợi ý, khung xanh = đang chọn); đổi ô chưa hợp bằng `--alt ô=k`.
4. **Preview** → `python3 scripts/intro_preview.py $W/match/intro_match.json "<folder dự án>/_Intro_preview.mp4" --bin "$BIN" --music <nhạc intro hoặc nhạc chung> [--alt 3=2] --size 1080x1920|1920x1080` → gửi người dùng **bảng đối chiếu + video preview** để duyệt.
5. **Ghi vào CapCut** (sau khi duyệt) → `python3 ~/.claude/skills/capcut-tao-project/scripts/intro_build.py "<draft>" $W/match/intro_match.json --bin "$BIN" --assets <assets> --title "<tiêu đề>" [--title-kind static|typewriter] [--title-color <màu đo từ mẫu>] [--line "[a, b, c]"] [--intro-music file]` → `validate_draft.py`.

## B. KHÔNG có video mẫu
1. Hỏi nhạc intro (mục 0). Chọn kiểu intro (TIEU_CHI §8c): cắt nhanh nửa phách + tiêu đề gõ, hoặc 1 cảnh rộng 2–3s + tiêu đề tự nói (vlog chân thực §9.1).
2. Viết tay `intro_spec.json` tối giản: `{"intro_end": 4.43, "shots": [{"n":1,"beats":0.5,"type":"landscape"}, …], "title": {"kind":"typewriter","color":"#CDB4FF"}}` → đi tiếp A.2–A.5 (không có hàng ảnh mẫu trong bảng đối chiếu).

## Ghi chú
- Font: chỉ font hệ thống CapCut → gần giống; sticker/hiệu ứng có sẵn của CapCut không tự thêm được (làm tương tự bằng keyframe hoặc để người dùng thêm).
- Màu tiêu đề đo từ mẫu (`title.color`) — kiểm tra lại bằng mắt, vì nền sau chữ có thể làm lệch màu đo.
- Tiếng gõ: `typing_sfx.py` tự tạo, mỗi tiếng đúng khung một ký tự hiện ra; tắt bằng `--no-typing-sfx`.
