---
name: video-tools-macos
description: Bộ công cụ xử lý video/âm thanh trên macOS KHÔNG cần ffmpeg (Swift + AVFoundation) — trích khung hình, ảnh tĩnh full-res, chấm điểm độ nét/rung/sáng từng khung, tách nhạc khỏi video, giải mã PCM, cắt đoạn audio có fade, đọc thời lượng/độ phân giải. Dùng skill này bất cứ khi nào cần đọc nội dung video/audio trên máy Mac mà `ffmpeg`/`ffprobe` không có, kể cả khi đang chạy các skill loc-gom-footage, phan-tich-video-mau, nhac-cat-doan-do-beat, phan-canh-theo-beat, capcut-tao-project.
---

# Video tools cho macOS (không ffmpeg)

Máy này không có ffmpeg/ffprobe/opencv/scipy. Có sẵn: `swiftc` (AVFoundation), `python3` + Pillow + numpy, `mdls`, `sips`, `afinfo`.
Các tool ở `scripts/*.swift`, biên dịch một lần rồi dùng lại:

```bash
BIN=$(bash ~/.claude/skills/video-tools-macos/scripts/build.sh)
```

| Tool | Cách gọi | Kết quả |
|---|---|---|
| `frames3` | `$BIN/frames3 OUTDIR file1.MP4 file2.MP4 …` | 3 khung (15/50/85%) mỗi video, 360px → `OUTDIR/<tên>_1..3.jpg`; in `tên<TAB>thời lượng` |
| `dense` | `$BIN/dense video OUTDIR STEP SIZE` | khung đều mỗi STEP giây (vd 0.04 = phát hiện điểm cắt) → `f_00000.jpg…`; in fps, dur |
| `still` | `$BIN/still video GIÂY out.jpg` | 1 khung chính xác, tối đa 1920px, JPG q0.92 (dùng làm ảnh tĩnh cho CapCut) |
| `grab` | stdin: `path<TAB>giây<TAB>out.jpg` mỗi dòng | nhiều khung 320px (storyboard), cache asset theo file |
| `scan` | `$BIN/scan out.tsv file1 file2 …` | ~5 mẫu/giây: `file t brightness sharpness motion` — đọc tuần tự bằng AVAssetReader nên nhanh; chạy song song bằng `xargs -P 4` |
| `audio_extract` | `$BIN/audio_extract video.mp4 out.m4a` | tách audio sang m4a + in metadata |
| `pcm` | `$BIN/pcm in.(mp3/m4a/wav) out.f32 SR` | mono float32 raw ở sample rate SR (numpy: `np.fromfile(...,np.float32)`) |
| `audio_cut` | `$BIN/audio_cut in out.m4a START END FADE` | cắt đoạn [START,END] giây, fade-out FADE giây cuối, xuất m4a |
| `compose` | `$BIN/compose plan.json out.mp4` | ghép nhanh các đoạn clip (lấp khung, cắt giữa) + nhạc thành MP4 preview; plan: `{"width","height","fps","audio","audio_start","segments":[{"path","src_in","dur"}]}` (render hình trước rồi ghép nhạc — tránh lỗi -11838) |
| `media_info` | `$BIN/media_info file…` | `path<TAB>duration_µs<TAB>w<TAB>h<TAB>số track audio` (dùng cho CapCut) |

## Lưu ý đã gặp
- **zsh: không đặt tên biến `path`** trong vòng lặp shell — nó là mảng gắn với `$PATH`, làm mất mọi lệnh. Dùng `src`, `f`…
- Tên file tiếng Việt trên macOS là Unicode NFD: so khớp tên file bằng `os.listdir()` thay vì gõ chuỗi cố định.
- File `.LRF` của DJI là bản proxy độ phân giải thấp; AVFoundation không nhận đuôi lạ — dùng file `.MP4`.
- `mdls -name kMDItemDurationSeconds` nhanh để xem thời lượng/độ phân giải hàng loạt.
- **ShazamKit không dùng được** từ CLI (lỗi 202 — cần entitlement nhà phát triển); `SFSpeechRecognizer` cũng bị chặn. Muốn nhận diện bài hát: nhờ người dùng bật *Music Recognition* trong Control Center hoặc dùng app Shazam trên điện thoại, phát file nhạc đã tách.
- Ảnh/tệp tạm để ở scratchpad; tool không bao giờ ghi đè file nguồn.
