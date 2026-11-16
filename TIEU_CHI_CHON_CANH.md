# Tiêu chí đánh giá video & chọn cảnh

File này là **nguồn quy tắc chính** cho agent `capcut-video-editor` và các skill `loc-gom-footage`, `phan-canh-theo-beat`.
Agent đọc file này trước khi lọc footage hoặc chọn cảnh. Khi quy tắc ở đây khác với mặc định trong skill/script, **làm theo file này**.

**Cách bổ sung:** thêm dòng vào mục **"10. Bổ sung của tôi"** ở cuối, hoặc sửa thẳng con số trong các bảng.
- Đổi con số (ngưỡng, độ dài…) → agent cập nhật script tương ứng (cột "Nằm ở") trước khi chạy và báo lại đã đổi gì.
- Quy tắc mới bằng lời (vd "không dùng cảnh có người lạ nhìn vào máy") → agent áp dụng ở bước xem nội dung và khi tự xem lại bảng phân cảnh.

---

## 1. Lọc tự động — loại clip hỏng
| Tiêu chí | Ngưỡng | Xử lý | Nằm ở |
|---|---|---|---|
| Quá ngắn | < 1 giây | `_Loai_bo…` | `loc-gom-footage/scripts/find_bad_clips.py --short` |
| Màn hình đen | cả 3 khung (15/50/85%) độ sáng < 20/255 | `_Loai_bo…` | `find_bad_clips.py --dark` |
| Không đọc được | không lấy được khung nào | `_Loai_bo…` | `find_bad_clips.py` |
| Bản sao trùng | cùng dung lượng + giống hệt 50 MB đầu | `_Loai_bo…/Ban_sao_trung_lap` | `find_bad_clips.py` |
| Nghi quên tắt máy | clip rất dài, các khung gần như giống nhau | `_Can_xem_lai` (không bỏ hẳn, có thể dùng tiếng) | xem bằng mắt |

Không bao giờ xoá — chỉ di chuyển, có nhật ký để hoàn tác.

## 2. Xem nội dung — phân loại & chọn clip
- Phân loại theo **nội dung thật** trên ảnh thu nhỏ, không đoán từ tên file.
- **Vai trò:** Hook (mở đầu) · A-roll nói chuyện/selfie · B-roll cảnh đẹp/địa danh · Ẩm thực · Di chuyển · Mua sắm · Trải nghiệm · Outro · Ảnh.
- **Hook / mở đầu:** địa danh biểu tượng, món ăn đẹp, khoảnh khắc nổi bật nhất; khi dùng lại ở thân thì lấy khoảnh khắc khác.
- **Loại bằng mắt:** quay xuống sàn/đất, toàn trời trống, ống kính bị che, quá tối, ảnh chụp liên tiếp gần giống nhau (giữ 1–2 tấm).
- Clip vừa thuộc 2 vai trò → xếp theo nội dung chính.

## 3. Nhịp kể trong mỗi chặng
- Xen kẽ: **cảnh đẹp → đồ ăn → selfie ngắn (~1 phách) → di chuyển làm cầu nối**.
- Sắp theo **giờ quay** (thứ tự thời gian của chuyến đi).
- Có voice over → cảnh phải **khớp nội dung câu đang đọc**.

## 4. Chọn đoạn đẹp nhất trong mỗi clip (chấm điểm tự động)
Đo ~5 lần/giây (`video-tools-macos` → `scan`), chấm từng đoạn dài bằng cảnh cần lấy (`phan-canh-theo-beat/scripts/pick_shots.py`):

| Yếu tố | Cách tính | Mức | Tác dụng |
|---|---|---|---|
| Độ nét (+) | tương phản điểm ảnh liền nhau ở vùng giữa khung, so với mức nét 90% của chính clip | ×1.0 | ưu tiên khung nét |
| Rung / chuyển động (−) | thay đổi giữa 2 lần đo | chia 25 | tránh máy lắc, lia mạnh |
| Rung giật (−) | dao động của chuyển động trong đoạn | ×0.03 | tránh lúc êm lúc giật |
| Quá tối (−) | sáng TB < 35/255 | −0.8 | |
| Cháy sáng (−) | sáng TB > 225/255 | −0.5 | |
| Xa giữa clip (−) | khoảng cách tới giữa clip | ×0.1 | ưu tiên đoạn giữa |
| 0,4 giây đầu | bỏ qua | — | lúc vừa bấm quay hay rung |
| Đoạn đã dùng | cấm trong ±1,5 giây (hoặc ±độ dài cảnh + 0,5s) | — | dùng lại clip → khoảnh khắc khác |

**Ảnh tĩnh:** không dùng cho intro (xem §8c). Chỉ dùng nếu người dùng yêu cầu riêng: chọn 1 khung nét nhất mà cả trước và sau đều ít chuyển động; bỏ 0,5 giây đầu.

## 5. Ghép theo nhịp nhạc
- Điểm cắt đúng **phách / nửa phách**, khớp khung 30fps; các cảnh liền nhau, không hở.
- Độ dài cảnh: **nửa phách (~0,25s)** tiêu đề & cao trào · **1 phách (~0,5s)** đoạn thường · **2 phách (~1s)** cảnh đẹp.
- Nhịp tổng thể bám video mẫu (vd mẫu ~0,46s/cảnh → chủ yếu 1 phách).

## 6. Hiệu ứng (bằng keyframe)
- Đầu mỗi chặng: zoom đẩy 1,3 → 1,0 trong 8 khung.
- Cảnh ≥ 0,95s: zoom chậm 1,0 → 1,08.
- Cảnh tàu/chuyển động mạnh: lia vào (vị trí 0,3 → 0 + zoom 1,35 → 1,0 trong 6 khung).
- Cảnh cuối: mờ dần 0,8s.
(Nằm ở `capcut-tao-project` → `project.json` mục `effects`.)

## 7. Tự kiểm tra trước khi đưa duyệt
- Xem lại **toàn bộ bảng phân cảnh**; cảnh xấu (sàn nhà nhiều chi tiết bị tưởng là nét, mờ, đen, đá trống…) → đổi clip hoặc chỉ định giây cụ thể (`overrides`).
- Sau đó mới gửi người dùng duyệt; người dùng đổi cảnh theo số thứ tự.

## 8. Giới hạn
Chấm điểm tự động chỉ đo **kỹ thuật** (nét, sáng, rung) — không biết khoảnh khắc ý nghĩa, ai đang cười, góc nào đẹp. Phần đó do Claude xem và người dùng duyệt.

---

## 9. Tiêu chí theo loại video
Agent hỏi **loại video** ngay từ đầu dự án. Bộ tiêu chí của loại đó **được ưu tiên hơn** các mục 1–7 khi hai bên khác nhau. Mỗi loại có khối `Thông số` để agent đưa vào `plan.json` (`scoring`) và `project.json` (`original_volume`).

### 9.1 Vlog du lịch trải nghiệm — chân thực, gần gũi
**Ưu tiên khoảnh khắc thật hơn cảnh đẹp**
- Chọn: cười, phản ứng bất ngờ, nói chuyện tự nhiên, ăn thử món mới, lạc đường, trời mưa, mệt, chờ tàu. Những lúc "không hoàn hảo" tạo cảm giác gần gũi.
- Cảnh selfie / nói với camera là "xương sống": ưu tiên và **giữ lâu hơn** (1–2 phách; 3–4 phách nếu đang nói), không cắt vụn.
- Cảnh đẹp/địa danh để làm bối cảnh, không chiếm phần lớn video.

**Nới tiêu chí kỹ thuật**
- **Không phạt** cảnh cầm máy đi bộ góc nhìn thứ nhất và chuyển động tự nhiên; chỉ phạt rung giật mạnh hoặc mờ hẳn.
- Giữ cảnh hơi tối nếu có không khí thật (quán ăn tối, phố đêm, thuỷ cung).
- Cảnh hơi mờ nhưng có biểu cảm thật vẫn giữ, ưu tiên hơn cảnh nét mà vô hồn.

**Âm thanh thật**
- **Không tắt hết tiếng gốc**: giữ tiếng môi trường nhỏ (~20%) dưới nhạc — tiếng phố, tiếng chảo xèo xèo, tiếng tàu, tiếng cười.
- Khoảnh khắc nói/phản ứng hay: **bật to tiếng gốc, hạ nhạc** để người xem nghe được (skill `voice-over-phu-de`, `--speech-files`).

**Nhịp chậm hơn, có chỗ thở**
- Cắt nhanh 0,25s chỉ cho đoạn mở đầu hoặc chuyển chặng.
- Thân video phần lớn 1–2 phách; mỗi chặng có 1–2 cảnh giữ lâu (3–4 phách) để người xem "ở trong" khoảnh khắc.

**Kể theo góc nhìn của mình**
- Theo đúng trình tự thời gian và địa điểm, như kể lại một ngày.
- Chữ trên màn hình viết như **tự nói, ngôi thứ nhất, chữ thường** ("đói quá nên ghé luôn", "mưa mà vẫn đẹp"), không viết kiểu quảng cáo.
- Voice over (nếu có) là giọng kể chuyện thân mật, không như đọc bản tin.

**Hình ảnh tự nhiên**
- Màu gần thực tế, không filter nặng; chủ yếu cắt thẳng, zoom nhẹ.
- Giữ chi tiết đời thường: vé tàu, đồ ăn konbini, đôi giày, cửa sổ khách sạn.

**Tránh**
<!-- Người dùng sẽ bổ sung. -->

**Thông số**
```json
"scoring": {"motion_div": 60, "jitter_w": 0.03, "dark_level": 20, "dark_penalty": 0.4, "bright_level": 235, "bright_penalty": 0.5, "middle_w": 0.05}
"original_volume": 0.2
```
(So với mặc định: `motion_div` 25 → 60 = phạt chuyển động nhẹ hơn nhiều; ngưỡng tối 35 → 20 và phạt 0.8 → 0.4; tiếng gốc 0 → 20%.)

<!-- Thêm loại khác ở đây: ### 9.2 <Tên loại> … (cùng cấu trúc, kèm khối Thông số) -->

---

## 8b. Phụ đề (subtitle)
| Trường hợp | Quy tắc | Nằm ở |
|---|---|---|
| **Chỉ 1 thứ tiếng** (Việt hoặc Anh) | Mỗi lần hiện **tối đa 6 từ**; câu dài tự tách thành nhiều thẻ nối tiếp, mỗi thẻ hiện đúng lúc nói các từ đó | `voice-over-phu-de/scripts/align_words.py`, `align_script.py` → `--max-words 6` (mặc định khi `--lang vi`/`en`) |
| Song ngữ Việt – Anh | Theo câu, tối đa 2 dòng mỗi ngôn ngữ (không áp giới hạn 6 từ) | như trên, `--lang bi` |

Mọi trường hợp: mỗi thẻ hiện ≥ 1 giây khi có thể, không chồng thẻ sau.

**Kiểu chữ phụ đề ưa dùng:** vàng ấm `#F0D66B`, **đậm + nghiêng**, viền tối rất mảnh, **không bóng mờ**, giữa–dưới (theo ảnh mẫu phim). Script: `add_vo_subs.py --sub-style yellow-italic`.

## 8c. Intro (đoạn mở đầu)
- **Dùng VIDEO, không dùng ảnh tĩnh.** Không làm intro kiểu chuỗi ảnh tĩnh, trừ khi người dùng yêu cầu riêng cho một video.
- Chọn những khoảnh khắc đẹp nhất có chuyển động thật (lấy từ `01_Hook` hoặc cảnh rộng ấn tượng nhất); cảnh dùng lại ở thân video thì lấy khoảnh khắc khác.
- Độ dài intro = số phách nhạc (vd 8 phách ≈ 4,4s ở 119 BPM); điểm cắt đúng beat, nối liền chặng đầu.
- **Nhạc intro:** hỏi người dùng. Có nhạc riêng → phân tích nhạc đó, intro cắt theo beat của nó, phần thân bắt đầu sau intro. Không có → intro dùng nhạc chung của cả video.
- **Có video mẫu:** đo intro mẫu (số cảnh, độ dài theo phách, tiêu đề, tiếng gõ) → ghép footage cùng loại cảnh vào từng ô → bảng đối chiếu + video preview để duyệt (quy trình: `phan-canh-theo-beat/references/intro.md`).
- Hai kiểu đã dùng (đều bằng video):
  - **Cắt nhanh + chữ gõ:** nhiều cảnh ngắn nửa phách, tiêu đề hiện từng ký tự (`capcut_draft.py`, `title.typewriter`).
  - **Tiêu đề tự nói trên 1 cảnh đẹp:** 1 cảnh rộng 2–3s, chữ thường kiểu tự nói (hợp vlog chân thực §9.1).

## 10. Bổ sung của tôi
<!-- Thêm quy tắc riêng ở đây, mỗi dòng một quy tắc. Ví dụ:
- Ưu tiên cảnh có mặt người trong A-roll hơn cảnh chỉ có lưng.
- Không dùng cảnh quay dọc trong video ngang.
- Selfie tối đa 2 cảnh liên tiếp.
-->
