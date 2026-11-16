# project.json cho capcut_draft.py — ví dụ đã chạy tốt (vlog Nhật)

```json
{
  "name": "Japan_Trip_2026_SuperTrouper",
  "edl": "/path/to/edl.json",
  "music": "~/Downloads/Trip/_Nhac/Super_Trouper_doan_nhu_mau_0m13.8-1m06.m4a",
  "assets_dir": "~/Movies/CapCut_Assets/Japan_Trip_2026",
  "canvas": [1920, 1080],
  "fps": 30,
  "beat": {"period": 0.50455, "first": 0.410},
  "mute_original": true,
  "music_fade_out": 0.4,
  "title": {"text": "japan trip", "color": "#CDB4FF", "size": 22, "y": 0.12, "typewriter": true,
            "sub": "osaka · kyoto 2026", "sub_from_beat": 4, "sub_size": 8, "sub_y": -0.18},
  "section_headers": {"size": 12, "y": -0.62, "seconds": 1.0},
  "outro_text": "see you next trip",
  "time_labels": {"regex": "(\\d{8})(\\d{6})", "shift_hours": 2, "shift_from": "2026-05-22 00:00", "x": -0.80, "size": 6},
  "captions": {"x": 0.78, "size": 6},
  "effects": {"section_punch": 1.3, "hold_zoom": 1.08, "hold_min": 0.95,
              "whip_files": ["DJI_20260524150545_0254_D.MP4"], "fade_out_end": 0.8},
  "reserve_overlay_track": true
}
```

| Khoá | Ý nghĩa |
|---|---|
| `title` | chữ tiêu đề trên đoạn `sec == "title"`; `typewriter` gõ từng chữ 0,12s/chữ; `sub` hiện từ phách `sub_from_beat` |
| `section_headers` | dòng `cap` của EDL hiện `seconds` giây ở đầu mỗi chặng (trừ title/outro) |
| `time_labels` | giờ quay từ tên file + `src_in`; `shift_hours` cộng thêm từ `shift_from` (đồng hồ máy để giờ nhà). Bỏ khoá = không có giờ |
| `captions` | chú thích bên phải từ trường `caption` của từng cảnh trong EDL, gộp cảnh liền nhau cùng chữ |
| `effects.section_punch` | zoom 1.3→1.0 trong 8 khung ở cảnh đầu mỗi chặng |
| `effects.hold_zoom` | cảnh dài ≥ `hold_min` giây: zoom chậm 1.0→1.08 |
| `effects.whip_files` | các file được "lia vào" (PositionX 0.3→0 + scale 1.35→1 trong 6 khung) |
| `effects.fade_out_end` | cảnh cuối mờ dần sang đen (giây) |
| `mute_original` | tắt tiếng gốc clip, chỉ còn nhạc |
| `original_volume` | (tuỳ chọn, thắng `mute_original`) âm lượng tiếng gốc 0–1 cho mọi clip, vd 0.2 = giữ tiếng môi trường nhỏ cho vlog chân thực (TIEU_CHI_CHON_CANH.md §9.1) |

Màu chữ đã dùng: tím pastel `#CDB4FF` viền trắng (như video mẫu "day in my life"); chữ nhỏ trắng có bóng.
Khung 9:16: `"canvas": [1080, 1920]` — footage ngang sẽ cần scale/crop (chưa làm; nếu cần, thêm `clip.scale` ≈ 1.78 cho video segment và kiểm tra chủ thể ở giữa khung).
