"""Helpers to read/write CapCut 4.6 (macOS) drafts as plain JSON.

Every structure here was produced by CapCut 4.6.0 itself or verified by opening the result in
CapCut 4.6.0 (videos, photos, music/SFX, text with bold/stroke/shadow, ScaleX/ScaleY/PositionX/
Alpha keyframes, user beat markers). Times are microseconds; snap to the 30 fps frame grid.
"""
import copy, json, os, shutil, subprocess, time, uuid

ROOT = os.environ.get("CAPCUT_ROOT") or os.path.expanduser("~/Movies/CapCut/User Data/Projects/com.lveditor.draft")   # CAPCUT_ROOT = test sandbox
FONT = "/Applications/CapCut.app/Contents/Resources/Font/SystemFont/en.ttf"
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "template_draft")
US = 1_000_000

def uid(): return str(uuid.uuid4()).upper()
def us(t, fps=30): return int(round(t * fps)) * US // fps

def capcut_running():
    return subprocess.run(["pgrep", "-x", "CapCut"], capture_output=True).returncode == 0

def backup(paths, backup_root, label=""):
    """Copy files (draft json, root_meta_info.json …) to backup_root/<timestamp>_<label>/ before any write."""
    d = os.path.join(os.path.expanduser(backup_root), time.strftime("%Y%m%d_%H%M%S") + (("_" + label) if label else ""))
    os.makedirs(d, exist_ok=True)
    for p in paths:
        if os.path.exists(p): shutil.copy2(p, d)
    return d

class Draft:
    def __init__(self, d): self.d = d; self.M = d["materials"]

    @classmethod
    def new(cls, width=1920, height=1080, fps=30.0):
        d = json.load(open(os.path.join(TEMPLATE, "draft_info.json")))
        d["canvas_config"] = {"background": None, "height": height, "ratio": "original", "width": width}
        d["fps"] = fps; d["color_space"] = 0; d["tracks"] = []
        return cls(d)

    @classmethod
    def load(cls, folder): return cls(json.load(open(os.path.join(folder, "draft_info.json"))))

    # ----- tiny materials every segment references -----
    def _add(self, kind, m): self.M[kind].append(m); return m["id"]
    def speed(self): return self._add("speeds", {"curve_speed": None, "id": uid(), "mode": 0, "speed": 1.0, "type": "speed"})
    def canvas(self): return self._add("canvases", {"album_image": "", "blur": 0.0, "color": "", "id": uid(), "image": "", "image_id": "", "image_name": "", "source_platform": 0, "team_id": "", "type": "canvas_color"})
    def anim(self): return self._add("material_animations", {"animations": [], "id": uid(), "multi_language_current": "none", "type": "sticker_animation"})
    def chmap(self): return self._add("sound_channel_mappings", {"audio_channel_mapping": 0, "id": uid(), "is_config_open": False, "type": "none"})
    def vocsep(self): return self._add("vocal_separations", {"choice": 0, "id": uid(), "production_path": "", "time_range": None, "type": "vocal_separation"})
    def fade(self, out_us=0, in_us=0): return self._add("audio_fades", {"fade_in_duration": in_us, "fade_out_duration": out_us, "fade_type": 0, "id": uid(), "type": "audio_fade"})
    def beats(self, beat_us): return self._add("beats", {"ai_beats": {"beat_speed_infos": [], "beats_path": "", "beats_url": "", "melody_path": "", "melody_percents": [0.0], "melody_url": ""}, "enable_ai_beats": False, "gear": 404, "gear_count": 0, "id": uid(), "mode": 404, "type": "beats", "user_beats": list(beat_us), "user_delete_ai_beats": None})

    # ----- media materials -----
    def video_material(self, path, dur_us, w, h, has_audio=True, photo=False):
        m = {"aigc_history_id": "", "aigc_item_id": "", "aigc_type": "none", "audio_fade": None, "beauty_body_preset_id": "", "beauty_face_preset_infos": [], "cartoon_path": "", "category_id": "", "category_name": "", "check_flag": 63487,
             "crop": {"lower_left_x": 0.0, "lower_left_y": 1.0, "lower_right_x": 1.0, "lower_right_y": 1.0, "upper_left_x": 0.0, "upper_left_y": 0.0, "upper_right_x": 1.0, "upper_right_y": 0.0},
             "crop_ratio": "free", "crop_scale": 1.0, "duration": 10800000000 if photo else dur_us, "extra_type_option": 0, "formula_id": "", "freeze": None, "has_audio": bool(has_audio) and not photo, "has_sound_separated": False, "height": h, "id": uid(), "intensifies_audio_path": "", "intensifies_path": "", "is_ai_generate_content": False, "is_copyright": False, "is_text_edit_overdub": False, "is_unified_beauty_mode": False, "local_id": "", "local_material_from": "", "local_material_id": "", "material_id": "",
             "material_name": os.path.basename(path), "material_url": "", "matting": {"flag": 0, "has_use_quick_brush": False, "has_use_quick_eraser": False, "interactiveTime": [], "path": "", "strokes": []}, "media_path": "", "multi_camera_info": None, "object_locked": None, "origin_material_id": "", "path": path, "picture_from": "none", "picture_set_category_id": "", "picture_set_category_name": "", "request_id": "", "reverse_intensifies_path": "", "reverse_path": "", "smart_match_info": None, "smart_motion": None, "source": 0, "source_platform": 0,
             "stable": {"matrix_path": "", "stable_level": 0, "time_range": {"duration": 0, "start": 0}}, "team_id": "", "type": "photo" if photo else "video",
             "video_algorithm": {"ai_background_configs": [], "aigc_generate": None, "algorithms": [], "complement_frame_config": None, "deflicker": None, "gameplay_configs": [], "motion_blur_config": None, "mouth_shape_driver": None, "noise_reduction": None, "path": "", "quality_enhance": None, "smart_complement_frame": None, "super_resolution": None, "time_range": None},
             "width": w}
        self.M["videos"].append(m); return m

    def audio_material(self, path, dur_us):
        m = {"ai_music_type": 0, "aigc_history_id": "", "aigc_item_id": "", "app_id": 0, "category_id": "", "category_name": "", "check_flag": 1, "copyright_limit_type": "none", "duration": dur_us, "effect_id": "", "formula_id": "", "id": uid(), "intensifies_path": "", "is_ai_clone_tone": False, "is_ai_clone_tone_post": False, "is_text_edit_overdub": False, "is_ugc": False, "local_material_id": "", "music_id": "", "music_source": "", "name": os.path.basename(path), "path": path, "pgc_id": "", "pgc_name": "", "query": "", "request_id": "", "resource_id": "", "search_id": "", "similiar_music_info": {"original_song_id": "", "original_song_name": ""}, "sound_separate_type": "", "source_from": "", "source_platform": 0, "team_id": "", "text_id": "", "tone_category_id": "", "tone_category_name": "", "tone_effect_id": "", "tone_effect_name": "", "tone_emotion_name_key": "", "tone_emotion_role": "", "tone_emotion_scale": 0.0, "tone_emotion_selection": "", "tone_emotion_style": "", "tone_platform": "", "tone_second_category_id": "", "tone_second_category_name": "", "tone_speaker": "", "tone_type": "", "type": "extract_music", "video_id": "", "wave_points": []}
        self.M["audios"].append(m); return m

    # ----- segments -----
    SEG_BASE = {"caption_info": None, "cartoon": False, "common_keyframes": [], "currect_adjust_mask_index": 0, "desc": "", "enable_adjust": True, "enable_adjust_mask": False, "enable_color_correct_adjust": False, "enable_color_curves": True, "enable_color_match_adjust": False, "enable_color_wheels": True, "enable_lut": True, "enable_smart_color_adjust": False, "enable_track_adjust_mask": False, "group_id": "", "hdr_settings": {"intensity": 1.0, "mode": 1, "nits": 1000}, "intensifies_audio": False, "is_placeholder": False, "is_tone_modify": False, "keyframe_refs": [], "last_nonzero_volume": 1.0, "raw_segment_id": "", "render_index": 0, "responsive_layout": {"enable": False, "horizontal_pos_layout": 0, "size_layout": 0, "target_follow": "", "vertical_pos_layout": 0}, "reverse": False, "speed": 1.0, "template_id": "", "template_scene": "default", "track_attribute": 0, "track_render_index": 0, "visible": True, "volume": 1.0}

    @staticmethod
    def clip(x=0.0, y=0.0, sc=1.0):
        return {"alpha": 1.0, "flip": {"horizontal": False, "vertical": False}, "rotation": 0.0, "scale": {"x": sc, "y": sc}, "transform": {"x": x, "y": y}}

    def video_seg(self, mat, start_us, dur_us, src_us=0, volume=1.0, keyframes=None):
        s = copy.deepcopy(self.SEG_BASE)
        s.update({"id": uid(), "material_id": mat["id"], "clip": self.clip(), "extra_material_refs": [self.speed(), self.canvas(), self.anim(), self.chmap(), self.vocsep()],
                  "source_timerange": {"duration": dur_us, "start": src_us}, "target_timerange": {"duration": dur_us, "start": start_us},
                  "uniform_scale": {"on": not keyframes, "value": 1.0}, "volume": volume, "common_keyframes": keyframes or []})
        return s

    def audio_seg(self, mat, start_us, dur_us, src_us=0, volume=1.0, fade_out_us=0, beat_us=None):
        refs = [self.speed(), self.fade(fade_out_us)] + ([self.beats(beat_us)] if beat_us else []) + [self.chmap(), self.vocsep()]
        s = copy.deepcopy(self.SEG_BASE)
        s.update({"id": uid(), "material_id": mat["id"], "clip": None, "enable_adjust": False, "enable_lut": False, "hdr_settings": None, "extra_material_refs": refs,
                  "source_timerange": {"duration": dur_us, "start": src_us}, "target_timerange": {"duration": dur_us, "start": start_us}, "uniform_scale": None, "volume": volume})
        return s

    @staticmethod
    def kf(prop, pts):
        """prop: KFTypeScaleX / KFTypeScaleY / KFTypePositionX / KFTypePositionY / KFTypeAlpha / KFTypeRotation;
        pts: [(offset_us_from_segment_start, value)]"""
        return {"id": uid(), "keyframe_list": [{"curveType": "Line", "graphID": "", "id": uid(), "left_control": {"x": 0.0, "y": 0.0}, "right_control": {"x": 0.0, "y": 0.0}, "time_offset": int(o), "values": [float(v)]} for o, v in pts], "material_id": "", "property_type": prop}

    def zoom(self, a, b, t0, t1): return [self.kf("KFTypeScaleX", [(t0, a), (t1, b)]), self.kf("KFTypeScaleY", [(t0, a), (t1, b)])]

    # ----- text -----
    @staticmethod
    def _rgb(h): h = h.lstrip("#"); return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]

    def text_material(self, txt, size=8.0, color="#FFFFFF", bold=False, border=None, shadow=True, align=1, font=FONT, italic=False, border_width=0.08, border_alpha=1.0):
        st = {"fill": {"alpha": 1.0, "content": {"render_type": "solid", "solid": {"alpha": 1.0, "color": self._rgb(color)}}}, "font": {"id": "", "path": font},
              "range": [0, len(txt.encode("utf-16-le")) // 2], "size": size, "bold": bold, "italic": italic, "underline": False}
        if border: st["strokes"] = [{"content": {"render_type": "solid", "solid": {"alpha": border_alpha, "color": self._rgb(border)}}, "width": border_width}]
        if shadow: st["shadows"] = [{"content": {"render_type": "solid", "solid": {"alpha": 0.5, "color": [0, 0, 0]}}, "diffuse": 0.15, "distance": 4.0, "angle": -45.0, "alpha": 0.5}]
        m = {"add_type": 0, "alignment": align, "background_alpha": 1.0, "background_color": "", "background_height": 0.14, "background_horizontal_offset": 0.0, "background_round_radius": 0.0, "background_style": 0, "background_vertical_offset": 0.0, "background_width": 0.14, "base_content": "", "bold_width": 0.0, "border_alpha": border_alpha, "border_color": border or "", "border_width": border_width if border else 0.0,
             "caption_template_info": {"category_id": "", "category_name": "", "effect_id": "", "is_new": False, "path": "", "request_id": "", "resource_id": "", "resource_name": "", "source_platform": 0},
             "check_flag": 7, "combo_info": {"text_templates": []}, "content": json.dumps({"styles": [st], "text": txt}, ensure_ascii=False),
             "fixed_height": -1.0, "fixed_width": -1.0, "font_category_id": "", "font_category_name": "", "font_id": "", "font_name": "", "font_path": font, "font_resource_id": "", "font_size": size, "font_source_platform": 0, "font_team_id": "", "font_title": "none", "font_url": "", "fonts": [], "force_apply_line_max_width": False, "global_alpha": 1.0, "group_id": "", "has_shadow": shadow, "id": uid(), "initial_scale": 1.0, "inner_padding": -1.0, "is_rich_text": False, "italic_degree": 0, "ktv_color": "", "language": "", "layer_weight": 1, "letter_spacing": 0.0, "line_feed": 1, "line_max_width": 0.82, "line_spacing": 0.02, "multi_language_current": "none", "name": "", "original_size": [], "preset_category": "", "preset_category_id": "", "preset_has_set_alignment": False, "preset_id": "", "preset_index": 0, "preset_name": "", "recognize_task_id": "", "recognize_type": 0, "relevance_segment": [],
             "shadow_alpha": 0.5, "shadow_angle": -45.0, "shadow_color": "#000000" if shadow else "", "shadow_distance": 4.0, "shadow_point": {"x": 0.6363961030678928, "y": -0.6363961030678928}, "shadow_smoothing": 0.45, "shape_clip_x": False, "shape_clip_y": False, "source_from": "", "style_name": "", "sub_type": 0, "subtitle_keywords": None, "subtitle_template_original_fontsize": 0.0, "text_alpha": 1.0, "text_color": color, "text_curve": None, "text_preset_resource_id": "", "text_size": 30, "text_to_audio_ids": [], "tts_auto_update": False, "type": "text", "typesetting": 0, "underline": False, "underline_offset": 0.22, "underline_width": 0.05, "use_effect_default_color": True, "words": {"end_time": [], "start_time": [], "text": []}}
        self.M["texts"].append(m); return m

    def text_seg(self, mat, t0, t1, x=0.0, y=0.0, render_index=14001):
        """x, y in half-canvas units: x=-1 left edge, +1 right edge; y=+1 top, -1 bottom."""
        s = copy.deepcopy(self.SEG_BASE)
        s.update({"id": uid(), "material_id": mat["id"], "clip": self.clip(x, y), "extra_material_refs": [self.anim()], "enable_lut": False, "hdr_settings": None, "render_index": render_index,
                  "source_timerange": None, "target_timerange": {"duration": int(t1 - t0), "start": int(t0)}, "uniform_scale": {"on": True, "value": 1.0}})
        return s

    def typewriter(self, text, t_start, step_us, t_end, **style):
        """One text segment per prefix (no CapCut text-animation resource needed). Returns (segs, char_times)."""
        segs, times, t = [], [], t_start
        for i in range(1, len(text) + 1):
            nxt = t + step_us if i < len(text) else t_end
            times.append(t)
            if text[i - 1] != " " or i == len(text):
                segs.append(self.text_seg(self.text_material(text[:i], **{k: v for k, v in style.items() if k not in ("x", "y")}), t, nxt, style.get("x", 0.0), style.get("y", 0.0)))
            else:
                segs and segs[-1]["target_timerange"].update(duration=segs[-1]["target_timerange"]["duration"] + step_us)
            t = nxt
        return segs, times

    # ----- tracks / finish -----
    @staticmethod
    def track(kind, segs): return {"attribute": 0, "flag": 0, "id": uid(), "is_default_name": True, "name": "", "segments": segs, "type": kind}

    def finish(self, name, duration_us):
        for ti, tr in enumerate(self.d["tracks"]):
            for sg in tr["segments"]: sg["track_render_index"] = ti
        now = int(time.time())
        self.d.update({"name": name, "duration": int(duration_us), "update_time": now})
        if not self.d.get("create_time"): self.d["create_time"] = now
        if not self.d.get("id") or self.d["id"] == json.load(open(os.path.join(TEMPLATE, "draft_info.json")))["id"]: self.d["id"] = uid()

    def prune_materials(self):
        """Drop materials no segment references any more (after removing segments)."""
        refd = {s["material_id"] for t in self.d["tracks"] for s in t["segments"]} | {r for t in self.d["tracks"] for s in t["segments"] for r in s["extra_material_refs"]}
        for k, arr in self.M.items():
            if isinstance(arr, list): self.M[k] = [m for m in arr if not (isinstance(m, dict) and "id" in m) or m["id"] in refd]

    def dumps(self): return json.dumps(self.d, ensure_ascii=False, separators=(",", ":"))

def write_draft(folder, draft, media_items, cover_jpg=None, new=True):
    """Write draft_info.json (+ .bak, template-2.tmp), draft_meta_info.json, draft_settings; create folder from template if new.
    media_items: [(path, duration_us, w, h, 'video'|'photo'|'music')]"""
    name = os.path.basename(folder); js = draft.dumps(); now = int(time.time()); nowus = int(time.time() * 1e6)
    if new:
        if os.path.exists(folder): raise SystemExit("refusing to overwrite existing draft " + folder)
        os.makedirs(folder)
        for l in open(os.path.join(TEMPLATE, "_dirs.txt")): os.makedirs(os.path.join(folder, l.strip()), exist_ok=True)
        for f in ("draft_agency_config.json", "attachment_pc_common.json", "draft.extra", "template.tmp", "draft_biz_config.json"):
            shutil.copy(os.path.join(TEMPLATE, f), folder)
        meta = json.load(open(os.path.join(TEMPLATE, "draft_meta_info.json")))
        meta.update({"tm_draft_create": nowus})
        open(os.path.join(folder, "draft_settings"), "w").write(f"[General]\ndraft_create_time={now}\ndraft_last_edit_time={now}\nreal_edit_keys=1\nreal_edit_seconds=1\n")
    else:
        meta = json.load(open(os.path.join(folder, "draft_meta_info.json")))
    for f in ("draft_info.json", "draft_info.json.bak", "template-2.tmp"):
        open(os.path.join(folder, f), "w", encoding="utf-8").write(js)
    if cover_jpg: shutil.copy(cover_jpg, os.path.join(folder, "draft_cover.jpg"))
    grp = next(g for g in meta["draft_materials"] if g["type"] == 0)
    have = {i["file_Path"] for i in grp["value"]}
    for p, dur, w, h, kind in media_items:
        if p in have: continue
        grp["value"].append({"create_time": now, "duration": dur, "extra_info": os.path.basename(p), "file_Path": p, "height": h, "id": str(uuid.uuid4()), "import_time": now, "import_time_ms": nowus, "item_source": 1, "md5": "", "metetype": kind,
                             "roughcut_time_range": {"duration": dur if kind != "photo" else -1, "start": 0 if kind != "photo" else -1}, "sub_time_range": {"duration": -1, "start": -1}, "type": 0, "width": w})
    meta.update({"draft_fold_path": folder, "draft_id": draft.d["id"], "draft_name": name, "draft_root_path": ROOT, "draft_timeline_materials_size_": len(js.encode()), "tm_draft_modified": nowus, "tm_duration": draft.d["duration"], "draft_cover": "draft_cover.jpg"})
    json.dump(meta, open(os.path.join(folder, "draft_meta_info.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    register(folder, draft, len(js.encode()))

def register(folder, draft, size):
    """Add/update the project in CapCut's project list (root_meta_info.json). Back it up first!"""
    rp = os.path.join(ROOT, "root_meta_info.json"); root = json.load(open(rp)); nowus = int(time.time() * 1e6)
    e = next((x for x in root["all_draft_store"] if x["draft_fold_path"] == folder), None)
    if e is None:
        e = {"draft_cloud_last_action_download": False, "draft_cloud_purchase_info": "", "draft_cloud_template_id": "", "draft_cloud_tutorial_info": "", "draft_cloud_videocut_purchase_info": "", "draft_cover": os.path.join(folder, "draft_cover.jpg"), "draft_fold_path": folder, "draft_id": draft.d["id"], "draft_is_ai_shorts": False, "draft_is_invisible": False, "draft_json_file": os.path.join(folder, "draft_info.json"), "draft_name": os.path.basename(folder), "draft_new_version": "", "draft_root_path": ROOT, "draft_timeline_materials_size": size, "draft_type": "", "tm_draft_cloud_completed": "", "tm_draft_cloud_modified": 0, "tm_draft_create": nowus, "tm_draft_modified": nowus, "tm_draft_removed": 0, "tm_duration": draft.d["duration"]}
        root["all_draft_store"].insert(0, e); root["draft_ids"] = root.get("draft_ids", 0) + 1
    e.update({"tm_draft_modified": nowus, "draft_timeline_materials_size": size, "tm_duration": draft.d["duration"]})
    json.dump(root, open(rp, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
