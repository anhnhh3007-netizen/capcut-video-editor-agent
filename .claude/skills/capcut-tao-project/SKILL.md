---
name: capcut-tao-project
description: Tạo mới hoặc sửa project CapCut (CapCut desktop 4.6 trên macOS) bằng cách ghi thẳng file draft JSON trong ~/Movies/CapCut — không mở CapCut, không điều khiển màn hình, không sửa video gốc, sao lưu trước mỗi lần ghi. Dựng timeline từ bảng phân cảnh (EDL) + nhạc: cắt theo beat, tắt tiếng gốc, mốc beat trên track nhạc, chữ tiêu đề gõ dần, tiêu đề chặng, giờ quay, chú thích, hiệu ứng zoom/whip/mờ dần bằng keyframe, track trống cho motion graphic. Dùng khi người dùng nói "tạo capcut project", "edit capcut project", "ghi vào CapCut", "đưa vào CapCut", "dựng video ngắn đăng TikTok/Instagram/Facebook bằng CapCut", hoặc muốn thêm/sửa cảnh, chữ, nhạc, hiệu ứng trong một project CapCut có sẵn.
---

# Tạo / sửa project CapCut bằng file

Script: `.claude/skills/capcut-tao-project/scripts/` (`capcut_lib.py` = thư viện định dạng, `capcut_draft.py` = tạo project mới, `validate_draft.py` = kiểm tra). Công cụ media: skill **video-tools-macos** (`BIN=$(bash .claude/skills/video-tools-macos/scripts/build.sh)`).

## Yêu cầu của người dùng (luôn giữ)
- **Không mở CapCut, không điều khiển màn hình** — chỉ ghi file qua quyền truy cập thư mục.
- **Không sửa file video gốc.** Media đưa vào bằng hard link / file mới.
- **Sao lưu trước mỗi lần ghi** (root_meta_info.json + draft của project) vào `<assets>/_backup/<thời gian>_<nhãn>/`.
- **Hỏi người dùng nơi lưu file tạo ra** (clip hard link, nhạc, ảnh, SFX, backup) trước lần ghi đầu tiên của dự án. Không tự mặc định. Khuyên chọn `~/Movies/CapCut_Assets/<Dự_án>/` vì CapCut tự đọc được (xem lý do dưới). Nếu người dùng chọn chỗ khác thì nói rõ hệ quả (đã xảy ra thật với ~/Downloads: CapCut báo "File not accessible" cho mọi media; cách sửa = hard link media sang ~/Movies/CapCut_Assets/<Dự_án>/ rồi thay đường dẫn trong draft_info.json, .bak, template-2.tmp, draft_meta_info.json): CapCut có thể báo thiếu media và phải liên kết lại hoặc import folder đó một lần; nếu khác ổ đĩa thì phải copy và tốn dung lượng. Chỗ đã chốt ghi vào `assets_dir`.
- Hỏi để xác nhận/làm rõ trước khi ghi: có kịch bản không, khung hình, chữ, mức hiệu ứng, nhạc (chưa có thì bảo người dùng gửi). Người dùng có thể bổ sung motion graphic sau → để sẵn 1 track video trống.

## Sự thật về CapCut trên máy này (đã kiểm chứng)
- CapCut 4.6.0 (`com.lemon.lvoverseas`) chạy **sandbox**: tự đọc được `~/Movies` (entitlement `assets.movies.read-write`); file ở `~/Downloads` chỉ đọc được nếu người dùng tự import qua hộp thoại. → vì vậy khuyên hard link footage vào `~/Movies/CapCut_Assets/<Dự_án>/clips/` (cùng ổ APFS: không tốn thêm dung lượng, `du` vẫn báo to — giải thích cho người dùng).
- Draft là **JSON thường** (chưa mã hoá ở bản 4.6) tại `~/Movies/CapCut/User Data/Projects/com.lveditor.draft/<Tên>/draft_info.json`; danh sách project ở `root_meta_info.json` cùng thư mục.
- **Không có transition/effect nào được cache** trên máy (`Cache/effect` chỉ có id, không có tên) → làm chuyển cảnh & hiệu ứng bằng **keyframe** (zoom đẩy, whip PositionX + scale 1.35 để không lộ viền đen, Alpha mờ dần). Transition thật của CapCut: để người dùng tự thêm.
- Chữ: font hệ thống `/Applications/CapCut.app/Contents/Resources/Font/SystemFont/en.ttf`; gõ từng chữ = mỗi tiền tố 1 đoạn text (không cần tài nguyên animation).
- Ảnh tĩnh: material `type: "photo"`, duration 10800000000 (dùng cho overlay như letterbox; **intro không dùng ảnh tĩnh** — TIEU_CHI_CHON_CANH.md §8c).
- Chi tiết trường JSON & toạ độ: [references/capcut_format.md](references/capcut_format.md).

## Tạo project mới
1. Có `edl.json` đã duyệt (skill phan-canh-theo-beat) + đoạn nhạc (skill nhac-cat-doan-do-beat).
2. Viết `project.json` ([references/project_config.md](references/project_config.md)) — tên project tự đặt dạng `Chu_De_Nam_TenNhac`.
3. Nhờ người dùng **tắt CapCut** (script tự kiểm tra `pgrep -x CapCut` và dừng nếu đang mở).
4. `python3 scripts/capcut_draft.py project.json --bin "$BIN" --dry` → rồi chạy thật (tự backup, hard link, ghi, đăng ký, lưu config + edl vào `<assets>/_build/`).
5. `python3 scripts/validate_draft.py "<thư mục draft>"` → phải "OK".
6. Báo người dùng: tên project (nằm đầu danh sách), nội dung timeline, nơi backup, điều chưa kiểm chứng (chưa mở thử). Nếu CapCut báo thiếu media → liên kết lại tới `<assets>`.

## Intro
- `intro_build.py`: ghi intro (cảnh video + tiêu đề + dòng gõ + tiếng gõ tự tạo + nhạc intro riêng tuỳ chọn) vào vùng 0→intro_end của project; quy trình đầy đủ ở `.claude/skills/phan-canh-theo-beat/references/intro.md`.
- Nhạc intro riêng: tạo project với `"intro": {"duration": <s>}` trong `project.json` → phần thân + nhạc chính bắt đầu sau intro, vùng intro để trống cho `intro_build.py --intro-music`.
- `typing_sfx.py`: tiếng gõ phím tự tổng hợp, khớp từng ký tự.
- Thử nghiệm an toàn: đặt `CAPCUT_ROOT=<thư mục tạm có bản sao project + root_meta_info.json>` để script ghi vào bản sao, không đụng danh sách project thật.

## Sửa project có sẵn
- Kiểm tra CapCut đã tắt; so `mtime`/kích thước `draft_info.json` với lần ghi trước — nếu người dùng đã sửa trong CapCut, **đọc bản hiện tại và sửa trên đó**, không ghi đè bằng bản cũ.
- `backup([draft_info.json, draft_meta_info.json, draft_settings, root_meta_info.json], …)` rồi dùng `Draft.load(folder)` → thay đổi → `prune_materials()` → `write_draft(folder, D, items, new=False)` → validate.
- Khôi phục: copy các file trong thư mục `_backup/<…>/` về chỗ cũ (draft_info.json cả `.bak` và `template-2.tmp`).
