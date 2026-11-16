---
name: loc-gom-footage
description: Lọc, chia nhóm, đặt tên theo chủ đề và gom ảnh/video (footage DJI, điện thoại…) vào folder để chuẩn bị dựng vlog — xem nội dung từng clip qua khung hình, phát hiện clip lỗi/đen/quá ngắn/bản sao trùng, xếp theo ngày–địa điểm hoặc theo vai trò dựng (Hook, A-roll, B-roll, Ẩm thực, Di chuyển, Mua sắm, Trải nghiệm, Outro, Ảnh). Dùng khi người dùng đưa một folder ảnh/video và nói "lọc ảnh và video", "chia theo chủ đề", "gom nhóm", "sắp xếp footage", "tổng hợp thành folder", "chia nhóm theo nhu cầu vlog", kể cả khi chưa nói rõ tiêu chí chia.
---

# Lọc & gom footage cho vlog

Mục tiêu: người dùng mở folder là biết ngay clip nào dùng cho đoạn nào của vlog, không mất file nào, và có thể hoàn tác.

Công cụ đọc video: skill **video-tools-macos** (`BIN=$(bash .claude/skills/video-tools-macos/scripts/build.sh)`). Script của skill này ở `.claude/skills/loc-gom-footage/scripts/`. Việc nặng để ở scratchpad (`WORK=<scratchpad>/footage`).

**Tiêu chí lọc/loại clip:** đọc `TIEU_CHI_CHON_CANH.md` (thư mục gốc dự án) (mục 1–2 và "Bổ sung của tôi") trước; khác mặc định thì làm theo file đó (vd đổi ngưỡng → truyền `--short`/`--dark` cho `find_bad_clips.py`).

## Quy trình

1. **Tìm folder & kiểm kê.** Folder người dùng nêu có thể không nằm trong thư mục làm việc — tìm bằng `mdfind -name` / `ls ~/Downloads`. Đếm theo đuôi file, dung lượng, phân bố ngày (tên `DJI_YYYYMMDDhhmmss`). File `.LRF` là proxy của DJI, đi kèm `.MP4` cùng tên.
2. **Trích khung hình:** `ls *.MP4 | … | xargs -0 -P 6 -n 10 $BIN/frames3 $WORK/frames > $WORK/durations.tsv`.
3. **Contact sheet:** `python3 scripts/contact_sheet.py FOOTAGE $WORK` → `index.tsv` + `sheet_XX.jpg`. **Xem hết các sheet bằng Read** — phân loại dựa trên nội dung thật, không đoán từ tên file.
4. **Clip lỗi:** `python3 scripts/find_bad_clips.py FOOTAGE $WORK` (ngắn <1s, đen, không đọc được, bản sao trùng). Clip rất dài mà cả 3 khung giống nhau (quay trần nhà, quên tắt máy) → folder `_Can_xem_lai`, không bỏ hẳn (có thể còn tiếng).
5. **Đề xuất nhóm** (xem [references/nhom.md](references/nhom.md)) — hai kiểu:
   - *Theo thời gian/địa điểm* (`NN_NgayX_DD-MM_Dia_diem`) — tốt để rà lại chuyến đi.
   - *Theo vai trò dựng vlog* (`01_Hook…09_Anh_chup`, bên trong subfolder theo ngày/địa điểm) — tốt khi dựng.
   Nếu người dùng chưa nói, làm kiểu thời gian trước rồi gợi ý kiểu vai trò. Hỏi khi tiêu chí không rõ.
6. **Viết plan TSV** (`stt<TAB>folder`) rồi chạy thử `python3 scripts/organize.py FOOTAGE plan.tsv --index $WORK/index.tsv --dry`, sau đó chạy thật. Script tự kéo `.LRF` theo vào `_LRF_ban_xem_truoc_DJI/<folder>`, ghi nhật ký `_nhat_ky_sap_xep.csv`, `--undo` để hoàn tác.
7. **Báo cáo:** bảng folder | nội dung | số file; nêu rõ folder `_Loai_bo…` / `_Can_xem_lai` để người dùng tự quyết xoá; ghi chú ảnh burst gần giống nhau; viết `_Goi_y_dung_vlog.md` nếu chia theo vai trò.

## Nguyên tắc
- **Chỉ di chuyển, không xoá, không sửa file gốc.** Folder rỗng có sẵn của người dùng giữ nguyên.
- Tên folder **không dấu**, nối bằng `_` (Premiere/CapCut đọc ổn định hơn), có số thứ tự đầu để sắp đúng trình tự vlog.
- Folder lọc bắt đầu bằng `_` để nằm cuối danh sách.
- Đồng hồ máy quay có thể để giờ nhà (vd DJI để giờ VN khi đi Nhật: +2h). Kiểm tra bằng cảnh có mốc giờ rõ (hoàng hôn, giờ mở cửa) và ghi chú lại.
- Khi gom lại lần 2, đọc `_nhat_ky_sap_xep.csv` để biết vị trí hiện tại của từng file (đừng giả định vị trí cũ).
