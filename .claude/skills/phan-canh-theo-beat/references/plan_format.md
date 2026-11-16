# plan.json — định dạng & ví dụ thật (vlog Nhật, Super Trouper 52s, 118,9 BPM)

```json
{
  "beat": {"period": 0.50455, "first": 0.410},
  "end": 52.067,
  "fps": 30,
  "sections": [
    {"name": "title", "caption": "", "start_beat": null, "end_beat": 8, "chrono": false,
     "shots": [["/…/01_Hook_Canh_dat_nhat/DJI_…0071_D.MP4", 0], ["/…/okonomiyaki.MP4", 1], "… 16 cảnh × nửa phách"]},
    {"name": "day1", "caption": "day 1 · osaka", "start_beat": 8, "end_beat": 44, "chrono": true,
     "captions": {"DJI_20260521225823_0008_D.MP4": "leaving hanoi"},
     "shots": [["/…/DJI_20260521225823_0008_D.MP4", 2], ["…", 1]]},
    {"name": "outro", "caption": "see you next trip", "start_beat": 96, "end_beat": null,
     "shots": [["/…/sunset.MP4", 4], ["/…/train.MP4", 4], ["/…/castle.MP4", 0]]}
  ],
  "overrides": [{"section": "title", "file": "DJI_20260524130805_0237_D.MP4", "src_in": 30.0}]
}
```

- `scoring` (tuỳ chọn): trọng số chấm điểm theo loại video, lấy từ khối "Thông số" trong `TIEU_CHI_CHON_CANH.md` §9 — vd vlog chân thực: `{"motion_div": 60, "jitter_w": 0.03, "dark_level": 20, "dark_penalty": 0.4, "bright_level": 235, "bright_penalty": 0.5, "middle_w": 0.05}`. Không có → mặc định chung.
- `start_beat: null` = đoạn đầu: cảnh đầu (độ dài 0) lấp 0s → phách đầu, rồi đến các cảnh.
- `end_beat: null` = chạy tới hết nhạc (`end`), cảnh có độ dài 0 lấp phần còn lại.
- `chrono: true` = tự sắp theo tên file (DJI_YYYYMMDDhhmmss = thứ tự quay).
- `captions` (tuỳ chọn): chú thích góc phải theo từng file; skill capcut-tao-project gộp các cảnh liền nhau cùng chú thích.
- Tổng độ dài cảnh của chặng phải bằng `end_beat − start_beat` phách — `pick_shots.py` in ra để so; thêm/bớt cảnh cho khớp.

## Phân bổ đã dùng (52s, 103 phách, ~118 cảnh)
| Chặng | Phách | Nhịp |
|---|---|---|
| title | 0 → 8 | 0,41s mở + 16 × nửa phách (sau đổi thành 9 ảnh tĩnh × 1 phách) |
| day1 | 8 → 44 | chủ yếu 1 phách, chen nửa phách, cảnh đẹp 1 phách |
| day2 | 44 → 60 | đồi Daruma 2 phách |
| day3 | 60 → 84 | torii & tàu 2 phách |
| day4 | 84 → 96 | 1 phách / nửa phách |
| outro | 96 → hết | 2 + 2 phách + lấp phần còn lại, mờ dần |

## Chọn clip cho từng chặng
- Đầu: lấy từ `01_Hook_Canh_dat_nhat` (khác khoảnh khắc so với lúc dùng lại ở thân).
- Thân: xen kẽ B-roll → ẩm thực → A-roll ngắn (selfie ~1 phách) → di chuyển làm nối.
- Tránh: clip đã vào `_Loai_bo…`/`_Can_xem_lai`, clip toàn đất/sàn, quá tối, rung mạnh.
- Clip dùng 2 lần: `pick_shots.py` tự chọn cửa sổ khác; nếu vẫn xấu → `overrides`.
