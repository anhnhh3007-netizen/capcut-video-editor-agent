---
name: phan-canh-theo-beat
description: Lên kịch bản/bảng phân cảnh dựng video theo nhịp nhạc — chia chặng theo số phách, chọn clip cho từng cảnh, tự tìm đoạn đẹp nhất trong mỗi clip (nét, không rung, đủ sáng, bỏ đoạn lặp/dừng lâu/lỗi), canh mọi điểm cắt đúng beat, xuất EDL và ảnh storyboard để người dùng duyệt. Dùng khi người dùng muốn "dựng vắt theo nhịp nhạc", "chọn video", "cắt bớt nội dung lặp, lỗi, dừng lâu", "Claude tự edit", "lên phân cảnh", hoặc ngay trước khi tạo project CapCut/Premiere từ footage + nhạc đã dò beat.
---

# Phân cảnh theo beat

Đầu vào: footage đã gom (skill loc-gom-footage), lưới beat (skill nhac-cat-doan-do-beat), phân tích video mẫu (nhịp, cấu trúc). Đầu ra: `edl.json` + `_Phan_canh_duyet_N.jpg` đã được người dùng **duyệt**.

Công cụ: skill **video-tools-macos** (`BIN=$(bash ~/.claude/skills/video-tools-macos/scripts/build.sh)`). Script: `~/.claude/skills/phan-canh-theo-beat/scripts/`.

**Tiêu chí chọn cảnh:** đọc `~/Downloads/edit_video/TIEU_CHI_CHON_CANH.md` trước (người dùng tự bổ sung). Khác với mặc định dưới đây hoặc trong `pick_shots.py` thì làm theo file đó; đổi con số thì sửa script cho khớp và báo người dùng.

## Các bước
1. **Hỏi kịch bản.** Có kịch bản → bám kịch bản (cùng người dùng làm rõ từng chặng). Không → tự dựng theo video mẫu. Hỏi luôn khung hình (16:9/9:16) và có chữ hay không nếu chưa chốt.
2. **Chia chặng theo phách** (intro/tiêu đề, từng ngày/địa điểm, kết) — tổng = số phách của đoạn nhạc. Nhịp lấy từ video mẫu (vd mẫu ~0,46s/cảnh → chủ yếu 1 phách ≈ 0,5s).
3. **Viết `plan.json`** ([references/plan_format.md](references/plan_format.md)): danh sách `[đường_dẫn_clip, số_nửa_phách]` mỗi chặng, chọn bằng mắt từ contact sheet. Thời gian quay trong tên file DJI = thứ tự → `chrono: true`.
4. **Chấm điểm khung:** liệt kê clip trong plan → `export BIN W; tr '\n' '\0' < list | xargs -0 -n 12 -P 4 sh -c '"$BIN"/scan "$W/scan_$$.tsv" "$@"' _` rồi `cat $W/scan_*.tsv > $W/scan_all.tsv` (clip thêm sau thì scan thêm và nối vào).
5. `python3 scripts/pick_shots.py plan.json $W/scan_all.tsv $W/edl.json` — chỉnh plan đến khi mỗi chặng in ra đúng số phách cần.
6. `python3 scripts/storyboard.py $W/edl.json $BIN/grab $W "<folder dự án>/_Phan_canh_duyet"` → **tự xem hết** các sheet; cảnh xấu (quay sàn, mờ, đen, đá trống) → thay clip trong plan hoặc thêm `overrides` (`src_in` = giây đẹp, lấy từ khung trong contact sheet), chạy lại 5–6.
7. **Gửi storyboard** (SendUserFile) + bảng chặng (thời gian, số cảnh, chữ dự kiến, hiệu ứng) và **chờ duyệt**. Người dùng đổi cảnh theo số thứ tự trên sheet.

## Intro
Intro có quy trình riêng (đo intro mẫu → ghép footage từng ô → bảng đối chiếu + video preview → ghi CapCut): **đọc [references/intro.md](references/intro.md)**. Scripts: `intro_match.py`, `intro_preview.py`, `types_from_folders.py`. Luôn hỏi nhạc intro trước.

## Ghi chú
- Mọi mốc thời gian snap về khung 30fps (pick_shots làm sẵn) — các cảnh liền nhau, không hở.
- Footage đồng hồ giờ nhà: ghi nhận lệch giờ (vd +2h VN→Nhật) để nhãn giờ ở bước CapCut đúng giờ địa phương.
- Giữ `plan.json`, `edl.json`, `scan_all.tsv` cùng nhau (sau lưu vào `_build/` của dự án) để sửa lại về sau.
