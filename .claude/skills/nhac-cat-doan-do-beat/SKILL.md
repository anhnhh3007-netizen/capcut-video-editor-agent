---
name: nhac-cat-doan-do-beat
description: Chuẩn bị nhạc cho video dựng theo nhịp — tìm đúng đoạn nhạc mà video mẫu dùng bên trong bài đầy đủ (mp3/m4a), cắt đoạn đó có fade, đo tempo/BPM, dò beat và xuất mốc beat (CSV) để cắt cảnh khớp nhạc. Dùng khi người dùng gửi file nhạc và nói "lấy đoạn như video mẫu", "cắt nhạc", "phân tích nhịp nhạc", "dò beat", "BPM", "dựng vắt theo nhịp nhạc", hoặc khi bước dựng cần lưới beat mà chưa có.
---

# Cắt đoạn nhạc & dò beat

Công cụ: skill **video-tools-macos** (`BIN=$(bash ~/.claude/skills/video-tools-macos/scripts/build.sh)`). Script: `~/.claude/skills/nhac-cat-doan-do-beat/scripts/`. Nhạc dùng chung để trong folder dự án `_Nhac/`.

## Khi có nhạc mẫu (tách từ video mẫu) + bài đầy đủ
1. Giải mã cả hai: `$BIN/pcm "BÀI.mp3" $W/song.f32 11025` và `$BIN/pcm _Nhac/nhac_tu_video_mau.m4a $W/ref.f32 11025`.
2. `python3 scripts/find_excerpt.py $W/song.f32 $W/ref.f32` → offset, tỉ lệ tốc độ, độ lệch từng đoạn 6s. Lệch tăng dần vài phần trăm giây là bình thường (mẫu chậm/nhanh rất ít) — nếu lệch cuối < ~0,15s thì cắt thẳng, không cần đổi tốc độ.
3. Cắt: `$BIN/audio_cut "BÀI.mp3" "_Nhac/<Ten>_doan_nhu_mau_<a>-<b>.m4a" START END 0.4` (fade-out 0,4s để khỏi tiếng bụp; mẫu thường dừng đột ngột).
4. Kiểm tra lại: pcm đoạn vừa cắt rồi chạy `find_excerpt.py` lần nữa với đoạn cắt làm "SONG" → lệch ở 0s phải ≈ 0.

## Dò beat
`$BIN/pcm <doan.m4a> $W/cut.f32 11025` → `python3 scripts/beats.py $W/cut.f32 _Nhac/ [--cuts <cuts.txt của video mẫu>]`.
- Đối chiếu BPM với tempo đã biết của bài (vd Super Trouper ≈ 118–119 BPM). Nếu ra gấp đôi/nửa, chọn ứng viên hợp lý.
- Bảng dB theo ô nhịp giúp chọn chỗ đổi chặng; nhạc pop/disco thường phẳng → chia chặng theo số ô nhịp.
- Gợi ý nhịp cắt cho người dùng: tiêu đề/cao trào = nửa phách; đoạn thường = 1 phách; cảnh đẹp giữ 2 phách.

## Ghi lại
Thêm vào `_Phan_tich_video_mau.md`: bài, đoạn (giây), file, BPM, độ dài phách, phách đầu, số phách, file CSV.

## Khi nhạc người dùng gửi không có mẫu
Bỏ bước 1–4; hỏi người dùng muốn đoạn nào (điệp khúc? độ dài?) rồi cắt bằng `audio_cut`, sau đó dò beat. Nhạc chưa có → bảo người dùng gửi; không tự tải nhạc có bản quyền.
