# CapCut 4.6 (mac) draft — ghi chú định dạng

## Thư mục một project
```
com.lveditor.draft/<Tên>/
  draft_info.json        timeline (= draft_info.json.bak = template-2.tmp, ghi cả 3 giống nhau)
  draft_meta_info.json   draft_id, draft_name, draft_fold_path, draft_materials[type 0] = media đã import
  draft_settings         [General] draft_create_time / draft_last_edit_time
  draft_cover.jpg        ảnh bìa trong danh sách project
  draft.extra, draft_agency_config.json, attachment_pc_common.json, template.tmp, draft_biz_config.json
  Resources/{audioAlg,videoAlg,digitalHuman/{audio,bsinfo,video}}, matting/, smart_crop/, adjust_mask/, common_attachment/
  .locked                CapCut tạo khi mở — để nguyên
com.lveditor.draft/root_meta_info.json   {"all_draft_store":[…], "draft_ids": N, "root_path": …}
```
Mẫu draft rỗng: `assets/template_draft/` (lấy từ một project trống CapCut 4.6 tạo ra).

## draft_info.json
- `canvas_config` {width, height, ratio}, `fps` 30.0, `duration` µs, `tracks` [], `materials` {…}.
- Mỗi **segment**: `material_id`, `target_timerange` {start, duration} (µs trên timeline), `source_timerange` (video/audio; `null` cho text), `extra_material_refs` (id trong materials), `clip` {scale, transform{x,y}, alpha…} (audio: `null`), `volume`, `common_keyframes`, `track_render_index` = vị trí track.
- Video segment refs: speed, canvas_color, sticker_animation, sound_channel_mapping, vocal_separation.
- Audio segment refs: speed, audio_fade, (beats), sound_channel_mapping, vocal_separation. Nhạc/SFX nhập từ file: material `type: "extract_music"`.
- Text segment refs: 1 sticker_animation. `render_index` ~14001+.
- Track: `{"type": "video"|"audio"|"text", "segments": [...], "flag": 0, "attribute": 0}`. Đoạn trong cùng track **không được chồng nhau** → mỗi lớp chữ một track.
- Toạ độ `clip.transform`: đơn vị nửa khung; x −1 trái … +1 phải; y +1 trên … −1 dưới. `scale` 1.0 = vừa khung (4K tự fit).
- Keyframe: `common_keyframes: [{"property_type": "KFTypeScaleX"|"KFTypeScaleY"|"KFTypePositionX"|"KFTypePositionY"|"KFTypeAlpha"|"KFTypeRotation", "keyframe_list": [{"time_offset": µs từ đầu segment, "values": [v], "curveType": "Line", …}]}]`. Khi có keyframe scale dùng `uniform_scale.on = false`.
- Mốc beat người dùng: material `beats.user_beats` = list µs, gắn vào refs của segment nhạc → hiện chấm beat trên track nhạc.
- Text content: chuỗi JSON `{"text": "...", "styles": [{"range": [0, len_utf16], "size", "bold", "fill": {...solid color [r,g,b] 0–1}, "strokes": [...], "shadows": [...], "font": {"path": ...}}]}`.

## Đã thử thành công trong CapCut 4.6.0
118 cảnh video + 9 ảnh, nhạc + SFX 2 track audio, 150+ đoạn chữ trên 5 track, keyframe ScaleX/Y, PositionX, Alpha, user_beats. Mở và phát bình thường, không báo lỗi.
