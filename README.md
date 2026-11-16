# CapCut Video Editor — Claude Code agent + skills

Agent **`capcut-video-editor`** cho Claude Code: dựng vlog du lịch / video ngắn (TikTok, Reels, Facebook) thành project **CapCut desktop 4.6 trên macOS** bằng cách ghi thẳng file dự án — không mở CapCut, không điều khiển màn hình, không sửa file gốc.

*A Claude Code agent that turns travel footage into a beat-synced CapCut (macOS, v4.6) project by writing the draft JSON directly.*

## Agent làm được gì
- Lọc & gom footage theo ngày, địa điểm, vai trò dựng (Hook, A-roll, B-roll, Ẩm thực…).
- Phân tích video mẫu: nhịp cắt, chữ, intro, nhạc.
- Tìm đoạn nhạc như video mẫu, cắt có fade, đo BPM, dò beat.
- Lên phân cảnh vắt theo nhịp nhạc, tự chọn đoạn đẹp nhất mỗi clip, xuất storyboard để duyệt.
- Intro bằng video theo mẫu (bảng đối chiếu + video preview).
- Voice over (ElevenLabs, tự thu hoặc lời gốc) và phụ đề Việt / Anh / song ngữ.
- Tạo / sửa project CapCut: chữ, hiệu ứng keyframe, chuyển cảnh, track trống cho motion graphic.

## Cấu trúc
```
.claude/agents/capcut-video-editor.md     agent
.claude/skills/
  video-tools-macos/      công cụ Swift + AVFoundation (không cần ffmpeg)
  loc-gom-footage/        lọc, chia nhóm footage
  phan-tich-video-mau/    phân tích video mẫu, đo intro
  nhac-cat-doan-do-beat/  cắt nhạc, dò beat
  phan-canh-theo-beat/    phân cảnh theo beat, intro
  voice-over-phu-de/      voice over + phụ đề
  capcut-tao-project/     ghi project CapCut 4.6
TIEU_CHI_CHON_CANH.md     tiêu chí chọn cảnh (bạn tự sửa / bổ sung)
```

## Cài đặt
1. Yêu cầu: macOS, Xcode Command Line Tools (`swiftc`), `python3` + `numpy` + `Pillow`, CapCut desktop 4.6.
2. Clone repo này làm thư mục dự án (hoặc chép `.claude/` và `TIEU_CHI_CHON_CANH.md` vào thư mục dự án của bạn), rồi mở Claude Code tại đó.
3. Build công cụ video (một lần):
   ```bash
   bash .claude/skills/video-tools-macos/scripts/build.sh
   ```
4. Gọi agent: `@capcut-video-editor dựng vlog từ folder …`

## Lưu ý
- **CapCut chạy sandbox:** chỉ đọc được media trong `~/Movies`. Agent hard-link media vào thư mục bạn chọn (khuyên dùng `~/Movies/CapCut_Assets/...`).
- **Tắt CapCut trước khi agent ghi project.** Mỗi lần ghi đều sao lưu trước.
- **ElevenLabs:** dòng `tools:` của agent có tên tool của connector ElevenLabs theo máy tác giả (`mcp__<id>__creative_*`). Trên máy bạn, thay `<id>` bằng id connector ElevenLabs của bạn, hoặc bỏ đi nếu không dùng voice over tạo bằng AI.
- Định dạng draft dựa trên CapCut 4.6 mac; phiên bản khác có thể cần chỉnh `capcut-tao-project/assets/template_draft`.
