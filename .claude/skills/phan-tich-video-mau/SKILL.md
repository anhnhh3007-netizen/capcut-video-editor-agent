---
name: phan-tich-video-mau
description: Phân tích video mẫu (reference video tải từ Pinterest/TikTok/Instagram, vd PinGrab_*.mp4) để học phong cách dựng — khung hình, thời lượng, số cảnh và nhịp cắt, cấu trúc intro/tiêu đề/thân/kết, kiểu chữ tiêu đề và phụ đề, hiệu ứng, chuyển cảnh, ảnh tĩnh mở đầu, tiếng gõ chữ, tách nhạc nền ra file riêng. Dùng khi người dùng gửi "video mẫu", "làm giống video này", "edit theo style này", "lấy nhạc trong video này", "tìm tên nhạc", "mở đầu như video mẫu", hoặc đưa một file video ngắn để tham khảo trước khi dựng.
---

# Phân tích video mẫu

Kết quả cần có: một bản ghi phân tích ngắn, cụ thể bằng số (thời gian, số cảnh, độ dài cảnh) mà bước dựng sau dùng trực tiếp được, và đối chiếu với footage của người dùng (khung hình, độ phân giải).

Công cụ: skill **video-tools-macos** (`BIN=$(bash ~/.claude/skills/video-tools-macos/scripts/build.sh)`). Script: `~/.claude/skills/phan-tich-video-mau/scripts/`. Việc tạm ở scratchpad.

## Các bước
1. **Thông số:** `mdls` (thời lượng, W×H, bitrate audio). Ghi lại dọc 9:16 hay ngang 16:9.
2. **Điểm cắt:** `$BIN/dense VIDEO $W/d 0.04 320` → `python3 scripts/analyze_sample.py $W/d DURATION $W/out`. Đọc `shots_*.jpg` bằng Read.
3. **Chữ & hiệu ứng:** lấy vài khung full-res (`$BIN/still VIDEO 5.3 x.jpg`) ở chỗ có tiêu đề/phụ đề để đọc font (serif/sans, đậm, màu, viền), vị trí, chữ hiện kiểu gõ từng ký tự hay hiện cả dòng, sticker, giờ/chú thích ở góc. Chữ gõ dần: dựng sheet các khung 0.1s vùng chữ để thấy ký tự tăng dần.
4. **Âm thanh:** `$BIN/audio_extract VIDEO $W/audio.m4a`; `$BIN/pcm $W/audio.m4a $W/a.f32 22050`; `python3 scripts/typing_onsets.py $W/a.f32` để thấy tiếng gõ/click khớp lúc chữ hiện.
5. **Nhạc:** muốn dùng nhạc của mẫu → lưu `audio.m4a` vào folder dự án `_Nhac/`. Tên bài: ShazamKit/Speech không chạy được từ CLI — thử tìm web theo chữ trên video; nếu không ra, hướng dẫn người dùng dùng *Music Recognition* (Control Center) hoặc app Shazam. Khi có bản đầy đủ → skill **nhac-cat-doan-do-beat**.
6. **Ghi kết quả** vào `_Phan_tich_video_mau.md` trong folder dự án (thêm mục mới cho mỗi video mẫu, không xoá mục cũ) theo mẫu ở [references/mau_ghi_chep.md](references/mau_ghi_chep.md).
7. **Đối chiếu footage:** kiểm tra độ phân giải footage (`mdls … kMDItemPixelWidth`). Nếu mẫu dọc mà footage ngang: crop 1920×1080 → 9:16 chỉ còn ~608×1080 — **hỏi người dùng** chọn khung (đăng TikTok/Reels thường 9:16). Hỏi luôn: 1 video cả chuyến hay mỗi ngày 1 video.

## Intro của mẫu
Khi người dùng muốn intro "tương tự mẫu": `python3 scripts/intro_spec.py MẪU.mp4 $W/intro --bin "$BIN"` → `intro_spec.json` (điểm cắt, độ dài theo phách, tiêu đề, tiếng gõ) + `intro_sheet.jpg`; điền `type` từng shot sau khi xem. Tiếp theo: `~/.claude/skills/phan-canh-theo-beat/references/intro.md`.

## Ghi nhớ từ các mẫu đã gặp
- Mẫu "solo in Japan" (dọc, 55,8s): 49 cảnh, ~1,1s/cảnh, tiêu đề gõ chữ + sticker, phụ đề serif nhỏ kiểu độc thoại, cắt thẳng.
- Mẫu "day in my life at ucla" (ngang, 52s): 113 cảnh, ~0,46s/cảnh, tiêu đề đậm tím pastel, giờ quay ở trái + chú thích ở phải, nhạc = ABBA *Super Trouper* đoạn 0:13.8–1:05.9.
- Mẫu "week in my life" (dọc, 36s): 0–3,1s là chuỗi **ảnh tĩnh** ~0,4s/ảnh, tiêu đề đứng yên, dòng `[art gallery, concert…]` gõ dần kèm **tiếng gõ phím**; chữ "[monday]" gõ ở đầu mỗi ngày.
- Khi mẫu mở đầu bằng **ảnh tĩnh**: ghi nhận nhịp/chữ/tiếng gõ để học, nhưng khi áp dụng thì **làm intro bằng video** (người dùng không muốn intro ảnh tĩnh — TIEU_CHI_CHON_CANH.md §8c).
