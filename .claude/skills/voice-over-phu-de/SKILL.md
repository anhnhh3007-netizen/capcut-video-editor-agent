---
name: voice-over-phu-de
description: Thêm voice over (giọng đọc tạo bằng ElevenLabs, từ công cụ bên thứ 3, tự thu, hoặc lời nói gốc trong clip) và phụ đề kiểu phim (cinematic, tiếng Việt / tiếng Anh / song ngữ) vào video dựng bằng CapCut — tách câu theo khoảng ngắt hơi, bỏ khoảng lặng dài mà không cắt file gốc, canh giờ phụ đề theo kịch bản (không cần nhận dạng giọng nói), đo độ to để đề xuất mức nhạc nền, kiểm tra nhạc đủ dài, dải đen letterbox tuỳ chọn. Dùng khi người dùng nói "voice over", "lồng tiếng", "giọng đọc", "thuyết minh", "phụ đề", "sub", "caption", "song ngữ", hoặc gửi file ghi âm/kịch bản lời cho video.
---

# Voice over & phụ đề

Công cụ: **video-tools-macos** (`BIN=$(bash ~/.claude/skills/video-tools-macos/scripts/build.sh)`), thư viện CapCut của **capcut-tao-project**. Script: `~/.claude/skills/voice-over-phu-de/scripts/`.

## 0. Hỏi trước — có làm bước này không
Hỏi người dùng: **"Video này có voice over và phụ đề không?"** Không → bỏ qua toàn bộ skill, dựng theo nhạc như bình thường. Có → hỏi tiếp (gộp một lần):
- **Nguồn voice over** (chọn được nhiều): Claude tạo bằng **ElevenLabs** (skill `elevenlabs-emotion-voiceover`: gắn thẻ cảm xúc → báo đường cong cảm xúc (mục 0b) → chọn model/giọng → demo ~10s → bản đầy đủ, mỗi bước người dùng duyệt, tốn credit của người dùng) / file tạo bằng công cụ bên thứ 3 (người dùng gửi lại) / file tự thu / lời nói gốc trong clip.
- **Ngôn ngữ phụ đề**: Tiếng Việt / Tiếng Anh / Song ngữ Việt – Anh. Song ngữ → người dùng **đưa kịch bản có sẵn cả 2 ngôn ngữ** (`Việt || English` mỗi dòng); không tự dịch.
- **Kịch bản lời**: mỗi câu phụ đề một dòng, đúng thứ tự nói. Chưa có → xin người dùng.
- **Letterbox:** KHÔNG hỏi. Mặc định không có dải đen; chỉ thêm khi người dùng tự yêu cầu (họ sẽ báo, kèm độ dày nếu muốn — video dọc dùng `--letterbox-px`).
Chưa có file giọng → bảo người dùng gửi; đợi đủ file rồi mới làm tiếp.

## 0b. Báo "đường cong cảm xúc của cả bài"
Ngay khi có kịch bản lời (người dùng đưa hoặc Claude tự viết; với ElevenLabs là sau khi đã gắn thẻ cảm xúc), gửi kịch bản kèm phần này **trước khi chọn model/giọng, tạo giọng hay người dùng thu âm**:
- Một bảng theo thứ tự lời đọc:

  | Đoạn | Thẻ / cách đọc | Cảm xúc / vai trò | Lý do |
  |---|---|---|---|
  | Mở đầu | `[excited]` | Gây chú ý | Hook: con số, tên hành trình |
  | … | … | … | … |
  | Kết | `[warmly]` → `[excited]` | … | … |

  Đoạn không có thẻ mới thì ghi "(giữ `[thẻ trước]`)". Giọng không phải ElevenLabs (tự thu, công cụ bên thứ 3) thì cột này ghi cách đọc gợi ý (vd "nhanh, hào hứng", "chậm, nhỏ lại") để người đọc làm theo. Cột lý do dựa vào chính chữ trong lời đọc (vd "thong thả", "yên bình" → `[warmly]`) và vị trí của đoạn trong mạch (trước/sau cao trào).
- Một câu tóm hình dạng đường cong: cao trào ở đâu, đoạn lắng ở đâu, câu kết bật lên hay lắng xuống.
- Một dòng nói rõ đây là lựa chọn của Claude, chưa ai nghe thử, và người dùng đổi được cảm xúc của bất kỳ đoạn nào trước khi tạo/thu giọng.
Bỏ qua mục này khi nguồn là **lời nói gốc trong clip** (lời đã có sẵn, không đổi được).

## 1. Chuẩn bị (trước bước phân cảnh — lời đọc quyết định độ dài video)
0. **Giọng ElevenLabs:** làm theo `elevenlabs-emotion-voiceover` (dùng chung 1 flow_id cho dự án). Khi người dùng chốt bản đầy đủ, lấy `full_res_url` bằng `creative_get_generations` → hỏi người dùng rồi tải về `<assets>/voice/` (`curl -L -o`). Kịch bản gửi model có thẻ `[…]`; kịch bản phụ đề **bỏ thẻ** (align_words.py tự bỏ).
1. Đặt file giọng vào thư mục asset đã chốt (`<assets>/voice/`, copy hoặc hard link — không sửa file gốc) để CapCut đọc được.
2. `$BIN/pcm <voice> $W/vo.f32 16000` → `python3 scripts/vo_segments.py $W/vo.f32 $W/vo.json --file <assets>/voice/<file> --offset <giây bắt đầu đọc, vd sau đoạn mở đầu>`
   - Khoảng lặng > 0,3s được rút còn 0,3s (chỉ đổi chỗ đặt các đoạn, file giữ nguyên). Muốn giữ nhịp gốc: `--max-gap 0`.
   - **Lời nói gốc trong clip**: `$BIN/audio_extract clip.MP4 $W/c.m4a` → pcm → `vo_segments.py … --window <src_in> <src_in+dur> --offset <giờ bắt đầu cảnh> --max-gap 0` (một file json mỗi cảnh có lời).
3. **Độ dài video = phần mở đầu + `timeline_end` + phần kết.** `python3 scripts/loudness.py $W/vo.f32 $W/music.f32 --need <độ dài cần> --music-total <độ dài cả bài>`:
   - nhạc không đủ → cắt đoạn dài hơn trong cùng bài (skill nhac-cat-doan-do-beat); cả bài không đủ → **cảnh báo, đề nghị người dùng chọn nhạc khác** (không tự lặp nhạc).
   - in **mức nhạc đề xuất** (cố định cả bài, giọng to hơn nhạc ~12 dB) → **người dùng chốt**.
4. **Canh giờ phụ đề**, chọn một trong hai cách:
   - **Theo từng từ (chính xác hơn):** chuyển giọng thành chữ bằng `creative_transcribe_audio` (model `eleven_scribe_v1`, tốn credit nên phải hỏi người dùng trước).
     - Giọng ElevenLabs: `creative_add_flow_asset_node(generation_id=…)`, rồi chuyển thành chữ với `connect_from` trỏ vào node đó.
     - File của người dùng: cần người dùng chọn file trong hộp tải lên, nên phiên chính phải làm bước này.
     - Kết quả nằm trong `transcripts[].words`, hoặc tải `words_download_url` về `$W/words.json`. Sau đó chạy:
       `python3 scripts/align_words.py kich_ban.txt $W/words.json $W/vo.json $W/subs.json --lang vi|en|bi [--match vi|en = ngôn ngữ của giọng đọc] --review "<folder dự án>/_Phu_de_duyet.md"`
     - Đọc lại phần chữ để bắt chỗ máy đọc sai tên riêng hoặc đọc nhầm thẻ cảm xúc.
   - **Theo chỗ ngắt hơi (không tốn credit):**
     `python3 scripts/align_script.py kich_ban.txt $W/subs.json $W/vo.json [clip jsons…] --lang vi|en|bi --review "<folder dự án>/_Phu_de_duyet.md"`
   - Gửi bảng **câu – bắt đầu – kết thúc** cho người dùng **duyệt**. Câu ghép sai thì sửa giờ trong `subs.json` hoặc tách lại dòng kịch bản.
5. Chuyển sang **phan-canh-theo-beat** với độ dài mới: mỗi câu lời = một nhóm cảnh khớp nội dung câu đó (câu nói về okonomiyaki → cảnh okonomiyaki), vẫn cắt theo beat; `end` của plan = độ dài video mới.

**Quy tắc độ dài thẻ** (TIEU_CHI_CHON_CANH.md §8b): **chỉ 1 thứ tiếng → mỗi thẻ tối đa 6 từ** (cả hai script tự tách, `--max-words 6` là mặc định khi `--lang vi`/`en`; mỗi thẻ hiện đúng lúc nói các từ đó). Song ngữ → theo câu, ≤ 2 dòng mỗi ngôn ngữ. Thẻ < 1s được đánh dấu ⚠️ trong bảng duyệt.

## 2. Ghi vào CapCut (sau khi project đã tạo bằng capcut-tao-project)
Tắt CapCut →
```
python3 scripts/add_vo_subs.py "<draft>" --bin "$BIN" --assets <assets> --vo $W/vo.json \
   [--speech-files DJI_a.MP4 …] --music-volume <đã chốt> --subs $W/subs.json [--letterbox 2.35 | --letterbox-px 120 (video dọc)]
```
→ `python3 ~/.claude/skills/capcut-tao-project/scripts/validate_draft.py "<draft>"` phải OK.
- Voice over trên track audio riêng; clip có lời gốc được bật lại tiếng, clip khác vẫn tắt.
- Kiểu chữ (`--sub-style`): **`yellow-italic`** = vàng ấm #F0D66B, đậm nghiêng, viền tối rất mảnh, không bóng (mẫu phim người dùng gửi, đã dùng cho Hà Giang); `cinematic` = chữ trắng mảnh, bóng mờ nhẹ. Vị trí giữa–dưới; song ngữ: Việt trên, Anh nhỏ & xám nhạt dưới; tối đa 2 dòng, mỗi lần hiện ≥ 1s.
- Font hệ thống của CapCut (`en.ttf`) — nếu dấu tiếng Việt hiển thị lỗi, báo người dùng đổi font trong CapCut (chọn font có hỗ trợ tiếng Việt).

## Báo cáo
Số đoạn voice over, thời lượng lời, mức nhạc đã dùng, số dòng phụ đề mỗi ngôn ngữ, letterbox (chỉ nếu người dùng đã yêu cầu), nơi backup, điều chưa kiểm chứng (chưa nghe thử trong CapCut).
