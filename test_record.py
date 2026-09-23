# -*- coding: utf-8 -*-
"""
Trình Phát Kịch Bản LDPlayer (.record) - Bản Thử Nghiệm Độc Lập
CHÚ Ý: File này chạy độc lập để thử nghiệm tính năng, KHÔNG can thiệp vào main.py hay web_server.py.
"""

import os
import sys
import json
import time
import math
import threading
import subprocess
from datetime import datetime
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Cấu hình giao diện CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class RecordPlayerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Trình Phát Kịch Bản LDPlayer (.record) - Bộ Biên Dịch Chuẩn Xác")
        self.geometry("960x850")
        self.minsize(880, 750)

        # Biến điều khiển
        self.ld_path = self._detect_ld_path()
        self.ldconsole_path = self._detect_ldconsole_path()
        self.emulators = []  # list of dicts: {'index': 0, 'name': 'Main', 'w': 1280, 'h': 720}
        self.selected_record_file = None
        self.parsed_actions = []
        self.record_info = {}

        # Luồng chạy ngầm
        self.play_thread = None
        self.stop_event = threading.Event()
        self.is_playing = False

        # Khởi tạo giao diện
        self._build_ui()

        # Quét ban đầu
        self._scan_emulators()
        self._scan_record_files()

    def _detect_ld_path(self):
        """Tự động phát hiện thư mục cài đặt LDPlayer"""
        cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    p = cfg.get("ld_path")
                    if p and os.path.exists(p):
                        return p
            except Exception:
                pass

        for candidate in [r"C:\LDPlayer\LDPlayer9", r"D:\LDPlayer\LDPlayer9", r"C:\leidian\LDPlayer9"]:
            if os.path.exists(candidate):
                return candidate
        return r"C:\LDPlayer\LDPlayer9"

    def _detect_ldconsole_path(self):
        """Tìm file thực thi ldconsole.exe hoặc dnconsole.exe"""
        if not self.ld_path or not os.path.exists(self.ld_path):
            return None
        for name in ["ldconsole.exe", "dnconsole.exe"]:
            p = os.path.join(self.ld_path, name)
            if os.path.exists(p):
                return p
        return None

    def _build_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="#1E222D", corner_radius=10)
        header_frame.pack(fill="x", padx=15, pady=(15, 8))

        title_lbl = ctk.CTkLabel(
            header_frame, 
            text="🎬 BỘ THỬ NGHIỆM GHI CHÉP HÀNH ĐỘNG LDPLAYER (.RECORD)", 
            font=ctk.CTkFont(family="Arial", size=17, weight="bold"),
            text_color="#4FC3F7"
        )
        title_lbl.pack(anchor="w", padx=15, pady=(8, 2))

        sub_lbl = ctk.CTkLabel(
            header_frame,
            text="Biên dịch chuẩn xác Click (giữ phím), Vuốt (quán tính mượt), Cuộn chuột & Đồng bộ thời gian thực 100% như giả lập",
            font=ctk.CTkFont(family="Arial", size=12),
            text_color="#B0BEC5"
        )
        sub_lbl.pack(anchor="w", padx=15, pady=(0, 8))

        # Khung cấu hình 1: Giả lập mục tiêu & Đường dẫn
        emu_frame = ctk.CTkFrame(self, fg_color="#262C3A", corner_radius=10)
        emu_frame.pack(fill="x", padx=15, pady=4)

        ctk.CTkLabel(emu_frame, text="1. Chọn Giả Lập Mục Tiêu:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=15, pady=8, sticky="w")

        self.emu_combobox = ctk.CTkComboBox(emu_frame, values=["(Đang quét...)"], width=340, state="readonly")
        self.emu_combobox.grid(row=0, column=1, padx=10, pady=8, sticky="w")

        btn_refresh_emu = ctk.CTkButton(emu_frame, text="🔄 Quét Giả Lập", width=120, command=self._scan_emulators)
        btn_refresh_emu.grid(row=0, column=2, padx=10, pady=8, sticky="w")

        self.ld_status_lbl = ctk.CTkLabel(emu_frame, text="", font=ctk.CTkFont(size=11), text_color="#81C784")
        self.ld_status_lbl.grid(row=0, column=3, padx=10, pady=8, sticky="w")

        # Khung cấu hình 2: Chọn Kịch Bản .record
        rec_frame = ctk.CTkFrame(self, fg_color="#262C3A", corner_radius=10)
        rec_frame.pack(fill="x", padx=15, pady=4)

        ctk.CTkLabel(rec_frame, text="2. Chọn Kịch Bản (.record):", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=15, pady=8, sticky="w")

        self.rec_combobox = ctk.CTkComboBox(rec_frame, values=["(Chưa có file)"], width=340, state="readonly", command=self._on_select_record)
        self.rec_combobox.grid(row=0, column=1, padx=10, pady=8, sticky="w")

        btn_refresh_rec = ctk.CTkButton(rec_frame, text="🔄 Quét Thư Mục", width=120, command=self._scan_record_files)
        btn_refresh_rec.grid(row=0, column=2, padx=10, pady=8, sticky="w")

        btn_browse_rec = ctk.CTkButton(rec_frame, text="📂 Chọn File Khác...", width=140, fg_color="#455A64", hover_color="#546E7A", command=self._browse_record_file)
        btn_browse_rec.grid(row=0, column=3, padx=10, pady=8, sticky="w")

        # Khung hiển thị tóm tắt kịch bản
        self.info_box = ctk.CTkFrame(rec_frame, fg_color="#1E222D", corner_radius=6)
        self.info_box.grid(row=1, column=0, columnspan=4, padx=15, pady=(0, 8), sticky="ew")

        self.info_lbl = ctk.CTkLabel(
            self.info_box, 
            text="Chưa chọn file kịch bản nào.", 
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#B0BEC5",
            justify="left"
        )
        self.info_lbl.pack(anchor="w", padx=10, pady=6)

        # Khung cấu hình 3: Cài đặt Phát & Công tắc Kích hoạt
        ctl_frame = ctk.CTkFrame(self, fg_color="#262C3A", corner_radius=10)
        ctl_frame.pack(fill="x", padx=15, pady=4)

        # Hàng 1 điều khiển: Switch kích hoạt + Trạng thái
        self.switch_play = ctk.CTkSwitch(
            ctl_frame, 
            text="KÍCH HOẠT PHÁT KỊCH BẢN", 
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FFD54F",
            progress_color="#4CAF50",
            command=self._on_toggle_play
        )
        self.switch_play.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        self.status_lbl = ctk.CTkLabel(
            ctl_frame, 
            text="Trạng thái: Đang Tắt", 
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#EF5350"
        )
        self.status_lbl.grid(row=0, column=4, padx=20, pady=(10, 5), sticky="e")

        # Hàng 2 điều khiển: Tốc độ + Chế độ vuốt + Vòng lặp
        opt_box = ctk.CTkFrame(ctl_frame, fg_color="transparent")
        opt_box.grid(row=1, column=0, columnspan=5, padx=15, pady=(0, 10), sticky="w")

        ctk.CTkLabel(opt_box, text="Tốc độ phát:").pack(side="left", padx=(5, 5))
        self.speed_combobox = ctk.CTkComboBox(opt_box, values=["1.0x (Gốc)", "1.25x", "1.5x", "2.0x", "3.0x"], width=105, state="readonly")
        self.speed_combobox.set("1.0x (Gốc)")
        self.speed_combobox.pack(side="left", padx=5)

        ctk.CTkLabel(opt_box, text="Chế độ vuốt:").pack(side="left", padx=(15, 5))
        self.swipe_mode_combobox = ctk.CTkComboBox(
            opt_box, 
            values=["Vuốt mượt (Quán tính)", "Thời lượng gốc (Kéo rê)"], 
            width=180, 
            state="readonly",
            command=self._on_change_swipe_mode
        )
        self.swipe_mode_combobox.set("Vuốt mượt (Quán tính)")
        self.swipe_mode_combobox.pack(side="left", padx=5)

        ctk.CTkLabel(opt_box, text="Số vòng lặp:").pack(side="left", padx=(15, 5))
        self.loop_combobox = ctk.CTkComboBox(opt_box, values=["Lặp vô tận", "1 lần", "2 lần", "3 lần", "5 lần", "10 lần"], width=115, state="readonly")
        self.loop_combobox.set("Lặp vô tận")
        self.loop_combobox.pack(side="left", padx=5)

        # Khung 4: TabView chứa 2 Tab: Bảng Thao Tác & Live Log
        self.tabview = ctk.CTkTabview(self, fg_color="#1E222D", segmented_button_fg_color="#262C3A", segmented_button_selected_color="#1976D2")
        self.tabview.pack(fill="both", expand=True, padx=15, pady=(4, 15))

        self.tab_actions = self.tabview.add("📑 BẢNG THAO TÁC ĐÃ BIÊN DỊCH (CHI TIẾT)")
        self.tab_log = self.tabview.add("📋 NHẬT KÝ THỜI GIAN THỰC (LIVE ADB LOG)")

        # Giao diện Tab Bảng Thao Tác
        act_header_bar = ctk.CTkFrame(self.tab_actions, fg_color="transparent")
        act_header_bar.pack(fill="x", padx=5, pady=(4, 2))

        ctk.CTkLabel(
            act_header_bar, 
            text="🔍 Danh sách các bước đã được bóc tách từ file .record (Đối chiếu chuẩn xác với giả lập):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#81D4FA"
        ).pack(side="left")

        btn_reparse = ctk.CTkButton(act_header_bar, text="🔄 Biên Dịch Lại", width=110, height=24, fg_color="#37474F", hover_color="#455A64", command=self._reparse_current)
        btn_reparse.pack(side="right")

        self.actions_textbox = ctk.CTkTextbox(self.tab_actions, font=ctk.CTkFont(family="Consolas", size=11), wrap="none")
        self.actions_textbox.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        # Giao diện Tab Live Log
        log_header_bar = ctk.CTkFrame(self.tab_log, fg_color="transparent")
        log_header_bar.pack(fill="x", padx=5, pady=(4, 2))

        ctk.CTkLabel(
            log_header_bar, 
            text="⚡ Tiến trình phát lệnh thời gian thực trên giả lập qua ADB:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#A5D6A7"
        ).pack(side="left")

        btn_clear_log = ctk.CTkButton(log_header_bar, text="Xóa Log", width=80, height=24, fg_color="#37474F", hover_color="#455A64", command=self._clear_log)
        btn_clear_log.pack(side="right")

        self.log_textbox = ctk.CTkTextbox(self.tab_log, font=ctk.CTkFont(family="Consolas", size=11), wrap="none")
        self.log_textbox.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        self.log("✅ Ứng dụng đã khởi động sẵn sàng. Bộ biên dịch tự động chuẩn hóa Click & Vuốt.")

    def log(self, text):
        """Ghi nhật ký lên màn hình với timestamp"""
        ts = datetime.now().strftime("%H:%M:%S")
        msg = f"[{ts}] {text}\n"
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", msg)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _clear_log(self):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.log_textbox.configure(state="disabled")

    def _scan_emulators(self):
        """Quét danh sách máy ảo từ ldconsole list2"""
        if not self.ldconsole_path or not os.path.exists(self.ldconsole_path):
            self.ld_status_lbl.configure(text="❌ Không tìm thấy ldconsole.exe", text_color="#EF5350")
            return

        try:
            res = subprocess.run([self.ldconsole_path, "list2"], capture_output=True, text=True, timeout=5)
            lines = res.stdout.strip().split("\n")
            self.emulators = []
            display_list = []
            for line in lines:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 9:
                    idx = int(parts[0])
                    name = parts[1]
                    w = int(parts[7]) if parts[7].isdigit() else 1280
                    h = int(parts[8]) if parts[8].isdigit() else 720
                    self.emulators.append({"index": idx, "name": name, "w": w, "h": h})
                    display_list.append(f"[{idx}] {name} ({w}x{h})")

            if display_list:
                self.emu_combobox.configure(values=display_list)
                self.emu_combobox.set(display_list[0])
                self.ld_status_lbl.configure(text=f"✅ Tìm thấy {len(display_list)} giả lập", text_color="#81C784")
                self.log(f"🔎 Đã quét danh sách giả lập: {', '.join(display_list)}")
                # Cập nhật lại biên dịch theo độ phân giải giả lập đang chọn
                if self.selected_record_file:
                    self._reparse_current()
            else:
                self.emu_combobox.configure(values=["(Không có giả lập nào)"])
                self.ld_status_lbl.configure(text="⚠️ Chưa tạo giả lập nào", text_color="#FFB74D")
        except Exception as e:
            self.ld_status_lbl.configure(text="❌ Lỗi quét giả lập", text_color="#EF5350")
            self.log(f"❌ Lỗi khi chạy ldconsole list2: {e}")

    def _scan_record_files(self):
        """Quét thư mục vms/operationRecords để tìm file .record"""
        rec_dir = os.path.join(self.ld_path, "vms", "operationRecords")
        self.record_files_map = {}

        if os.path.exists(rec_dir):
            for fname in os.listdir(rec_dir):
                if fname.endswith(".record"):
                    full_p = os.path.join(rec_dir, fname)
                    self.record_files_map[fname] = full_p

        # Quét thêm file mẫu trong GEternal nếu có
        sample_file = os.path.join(self.ld_path, "GEternal", "G ETERNAL_16-9.record")
        if os.path.exists(sample_file):
            self.record_files_map["[Mẫu] G ETERNAL_16-9.record"] = sample_file

        if self.record_files_map:
            names = list(self.record_files_map.keys())
            self.rec_combobox.configure(values=names)
            self.rec_combobox.set(names[0])
            self._load_record_file(self.record_files_map[names[0]])
            self.log(f"📁 Đã quét tìm thấy {len(names)} file kịch bản trong LDPlayer.")
        else:
            self.rec_combobox.configure(values=["(Thư mục trống - hãy ghi kịch bản F10)"])
            self.info_lbl.configure(
                text="⚠️ Chưa có file kịch bản nào trong 'vms\\operationRecords'.\n"
                     "👉 Bạn hãy mở LDPlayer lên, bấm F10 để ghi một thao tác ngắn rồi bấm '🔄 Quét Thư Mục'\n"
                     "   hoặc bấm '📂 Chọn File Khác...' để nạp file từ nơi khác."
            )

    def _browse_record_file(self):
        """Cho phép người dùng chọn bất kỳ file .record nào"""
        path = filedialog.askopenfilename(
            title="Chọn file kịch bản .record của LDPlayer",
            filetypes=[("LDPlayer Record", "*.record"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            fname = os.path.basename(path)
            self.record_files_map[f"[Ngoài] {fname}"] = path
            names = list(self.record_files_map.keys())
            self.rec_combobox.configure(values=names)
            self.rec_combobox.set(f"[Ngoài] {fname}")
            self._load_record_file(path)

    def _on_select_record(self, choice):
        if choice in self.record_files_map:
            self._load_record_file(self.record_files_map[choice])

    def _on_change_swipe_mode(self, choice):
        """Khi đổi chế độ vuốt, tự động biên dịch lại"""
        if self.selected_record_file:
            self._reparse_current()

    def _reparse_current(self):
        """Biên dịch lại file hiện tại với các thiết lập độ phân giải / chế độ vuốt mới"""
        if self.selected_record_file and os.path.exists(self.selected_record_file):
            self._load_record_file(self.selected_record_file)

    def _load_record_file(self, filepath):
        """Đọc và phân tích file kịch bản JSON .record"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.selected_record_file = filepath
            self.record_info = data.get("recordInfo", {})
            operations = data.get("operations", [])

            emu = self._get_selected_emulator_info()
            target_w = emu["w"]
            target_h = emu["h"]

            # Phân tích actions thành danh sách các cú Click / Vuốt / Cuộn / Nhập chữ
            smooth_swipe = ("Vuốt mượt" in self.swipe_mode_combobox.get())
            self.parsed_actions = self._parse_operations(operations, self.record_info, target_w, target_h, smooth_swipe)

            # Thống kê
            rec_w = self.record_info.get("resolutionWidth", target_w)
            rec_h = self.record_info.get("resolutionHeight", target_h)
            circle_dur = self.record_info.get("circleDuration", 0) / 1000.0
            if circle_dur == 0 and self.parsed_actions:
                circle_dur = self.parsed_actions[-1]["timing"] / 1000.0

            click_count = sum(1 for a in self.parsed_actions if a["type"] == "click")
            swipe_count = sum(1 for a in self.parsed_actions if a["type"] == "swipe")
            wheel_count = sum(1 for a in self.parsed_actions if a["type"] == "wheel")
            text_count = sum(1 for a in self.parsed_actions if a["type"] == "text")

            mode_text = "Vuốt Mượt (Quán Tính)" if smooth_swipe else "Thời Lượng Gốc (Kéo Rê)"

            self.info_lbl.configure(
                text=f"📄 File: {os.path.basename(filepath)} | 📐 Phân giải gốc: {rec_w}x{rec_h} ➔ Mục tiêu: {target_w}x{target_h}\n"
                     f"⏱ Thời lượng kịch bản: ~{circle_dur:.1f}s | Chế độ: {mode_text}\n"
                     f"🎯 Chi tiết: {len(self.parsed_actions)} bước "
                     f"({click_count} Click nhấn chuột, {swipe_count} Vuốt màn hình, {wheel_count} Cuộn chuột, {text_count} Nhập chữ)"
            )

            # Hiển thị lên Bảng Thao Tác Chi Tiết
            self._render_actions_table(self.parsed_actions, target_w, target_h)

            self.log(f"📥 Đã nạp & biên dịch kịch bản '{os.path.basename(filepath)}': {len(self.parsed_actions)} thao tác ({circle_dur:.1f}s).")

        except Exception as e:
            self.info_lbl.configure(text=f"❌ Lỗi đọc file: {e}")
            self.log(f"❌ Lỗi khi phân tích file .record: {e}")

    def _parse_operations(self, operations, record_info, target_w, target_h, smooth_swipe=True):
        """
        Thuật toán biên dịch chuẩn xác từ chuỗi PutMultiTouch thành các hành động người dùng:
        1. Nhấn chuột (Click): Chạm xuống và giữ (press_dur từ 70-150ms) rồi nhả tại cùng vị trí.
           -> Biên dịch thành: input swipe x y x y press_dur (đảm bảo 100% nhận diện trong mọi game).
        2. Vuốt màn hình (Swipe): Kéo rê ngón tay/chuột qua một quãng đường >= 15px.
           -> Tối ưu hóa thời lượng vuốt (natural_dur = 180ms - 380ms) để Android tính toán vận tốc
              cuộn (flick velocity) giúp danh sách trôi mượt mà y hệt như thao tác thật trên màn hình cảm ứng!
        3. Cuộn chuột (Wheel, tid != 1): Người dùng lăn chuột giữa.
           -> Chuẩn hóa thành 1 cú cuộn ngắn 90px theo hướng lăn, tránh quét bay cả màn hình.
        4. Nhập chữ (ImeClipboard): Gõ bàn phím.
        """
        rec_w = float(record_info.get("resolutionWidth", target_w))
        rec_h = float(record_info.get("resolutionHeight", target_h))
        is_landscape = (rec_w >= rec_h)
        width_grid = 19200.0 if is_landscape else 10800.0
        height_grid = 10800.0 if is_landscape else 19200.0

        def norm_x(x):
            return max(0.0, min(1.0, float(x) / width_grid))

        def norm_y(y):
            return max(0.0, min(1.0, float(y) / height_grid))

        actions = []
        cur_sessions = {}  # tid -> list of (timing, x, y)

        for op in operations:
            op_id = op.get("operationId")
            timing = op.get("timing", 0)

            if op_id == "ImeClipboard":
                text_val = op.get("text", "")
                actions.append({
                    "type": "text",
                    "timing": timing,
                    "text": text_val,
                    "desc": f"Nhập chữ: '{text_val}'",
                    "cmd": f"action call.keyboard {text_val}"
                })
            elif op_id == "PutMultiTouch":
                pts = op.get("points", [])
                for p in pts:
                    tid = p.get("id", 1)
                    state = p.get("state", -1)
                    px = p.get("x")
                    py = p.get("y")
                    if px is None or py is None:
                        continue

                    if state == 1:
                        if tid not in cur_sessions:
                            cur_sessions[tid] = []
                        cur_sessions[tid].append((timing, px, py))
                    elif state == 0:
                        if tid in cur_sessions:
                            cur_sessions[tid].append((timing, px, py))
                            raw_pts = cur_sessions.pop(tid)
                            act = self._compile_touch_session(raw_pts, tid, norm_x, norm_y, target_w, target_h, smooth_swipe)
                            if act:
                                actions.append(act)

        # Xử lý các touch session chưa kịp nhả state 0 (nếu kịch bản bị cắt ngang)
        for tid, raw_pts in list(cur_sessions.items()):
            act = self._compile_touch_session(raw_pts, tid, norm_x, norm_y, target_w, target_h, smooth_swipe)
            if act:
                actions.append(act)

        # Sắp xếp lại actions theo timing
        actions.sort(key=lambda a: a["timing"])
        return actions

    def _compile_touch_session(self, raw_pts, tid, norm_x, norm_y, target_w, target_h, smooth_swipe):
        """Biên dịch 1 chuỗi chạm thành hành động hoàn chỉnh"""
        if not raw_pts:
            return None

        t_start = raw_pts[0][0]
        t_end = raw_pts[-1][0]
        raw_dur = max(30, t_end - t_start)

        x0, y0 = raw_pts[0][1], raw_pts[0][2]
        x1, y1 = raw_pts[-1][1], raw_pts[-1][2]

        # Tọa độ pixel trên màn hình mục tiêu
        px0 = max(0, min(target_w - 1, int(round(norm_x(x0) * (target_w - 1)))))
        py0 = max(0, min(target_h - 1, int(round(norm_y(y0) * (target_h - 1)))))
        px1 = max(0, min(target_w - 1, int(round(norm_x(x1) * (target_w - 1)))))
        py1 = max(0, min(target_h - 1, int(round(norm_y(y1) * (target_h - 1)))))

        dist = math.hypot(px1 - px0, py1 - py0)
        is_wheel = (tid != 1)

        if is_wheel:
            # Cuộn chuột: LDPlayer gán tọa độ ảo kéo dài, ta quy về cú cuộn tự nhiên 90px
            direction = -1 if py1 < py0 else 1
            dir_str = "LÊN" if direction < 0 else "XUỐNG"
            scroll_dist = 90 * direction
            target_py = max(0, min(target_h - 1, py0 + scroll_dist))
            swipe_dur = 150
            return {
                "type": "wheel",
                "timing": t_start,
                "x1": px0, "y1": py0,
                "x2": px0, "y2": target_py,
                "duration": swipe_dur,
                "raw_duration": raw_dur,
                "desc": f"Cuộn chuột tại ({px0}, {py0}) ➔ {dir_str} (90px)",
                "cmd": f"input swipe {px0} {py0} {px0} {target_py} {swipe_dur}"
            }

        elif dist < 15:
            # Nhấn chuột (Click / Tap): Giữ chuột đúng thời gian thực tế để game nhận 100%
            press_dur = max(70, min(200, raw_dur))
            return {
                "type": "click",
                "timing": t_start,
                "x": px0, "y": py0,
                "duration": press_dur,
                "raw_duration": raw_dur,
                "desc": f"Nhấn chuột (Click) tại ({px0}, {py0}) [Giữ {press_dur}ms]",
                "cmd": f"input swipe {px0} {py0} {px0} {py0} {press_dur}"
            }

        else:
            # Vuốt màn hình (Swipe / Drag):
            if smooth_swipe:
                # Tính toán thời lượng vuốt tự nhiên theo cự ly di chuyển để Android kích hoạt quán tính cuộn (fling)
                calc_dur = int(dist * 1.15)
                swipe_dur = max(180, min(380, calc_dur))
            else:
                swipe_dur = raw_dur

            # Phân tích hướng vuốt
            dx = px1 - px0
            dy = py1 - py0
            if abs(dx) > abs(dy):
                dir_label = "Phải ➔" if dx > 0 else "Trái ⬅"
            else:
                dir_label = "Xuống ⬇" if dy > 0 else "Lên ⬆"

            return {
                "type": "swipe",
                "timing": t_start,
                "x1": px0, "y1": py0,
                "x2": px1, "y2": py1,
                "duration": swipe_dur,
                "raw_duration": raw_dur,
                "dist": int(dist),
                "desc": f"Vuốt màn hình {dir_label}: ({px0}, {py0}) ➔ ({px1}, {py1}) [Cự ly: {int(dist)}px, Tốc độ: {swipe_dur}ms]",
                "cmd": f"input swipe {px0} {py0} {px1} {py1} {swipe_dur}"
            }

    def _render_actions_table(self, actions, target_w, target_h):
        """Hiển thị bảng danh sách các bước thao tác trực quan, rõ ràng"""
        self.actions_textbox.configure(state="normal")
        self.actions_textbox.delete("1.0", "end")

        header = (
            f"{'#':<4} | {'Thời Điểm':<10} | {'Loại':<12} | {'Chi Tiết Thao Tác':<60} | {'Lệnh ADB Sẽ Chạy'}\n"
            f"{'-'*4}-+-{'-'*10}-+-{'-'*12}-+-{'-'*60}-+-{'-'*35}\n"
        )
        self.actions_textbox.insert("end", header)

        type_tags = {
            "click": "[NHẤN CHUỘT]",
            "swipe": "[VUỐT MƯỢT]",
            "wheel": "[CUỘN CHUỘT]",
            "text":  "[NHẬP CHỮ]"
        }

        for i, a in enumerate(actions, start=1):
            t_sec = f"{a['timing'] / 1000.0:.2f}s"
            tag = type_tags.get(a["type"], "[THAO TÁC]")
            desc = a.get("desc", "")
            cmd = a.get("cmd", "")
            row = f"{i:<4} | {t_sec:<10} | {tag:<12} | {desc:<60} | {cmd}\n"
            self.actions_textbox.insert("end", row)

        self.actions_textbox.configure(state="disabled")

    def _get_selected_emulator_info(self):
        """Lấy thông tin index và độ phân giải của giả lập đang chọn"""
        sel_text = self.emu_combobox.get()
        for emu in self.emulators:
            tag = f"[{emu['index']}] {emu['name']}"
            if sel_text.startswith(tag):
                return emu
        if self.emulators:
            return self.emulators[0]
        return {"index": 0, "name": "Main", "w": 1280, "h": 720}

    def _on_toggle_play(self):
        """Xử lý khi người dùng gạt BẬT hoặc TẮT công tắc phát"""
        if self.switch_play.get() == 1:
            if not self.parsed_actions:
                messagebox.showwarning("Cảnh báo", "Vui lòng chọn một file kịch bản hợp lệ trước khi bật!")
                self.switch_play.deselect()
                return

            self.is_playing = True
            self.stop_event.clear()
            self.status_lbl.configure(text="Trạng thái: Đang Chạy ▶", text_color="#4CAF50")
            self.tabview.set("📋 NHẬT KÝ THỜI GIAN THỰC (LIVE ADB LOG)")

            self.play_thread = threading.Thread(target=self._play_worker, daemon=True)
            self.play_thread.start()
        else:
            self.stop_event.set()
            self.is_playing = False
            self.status_lbl.configure(text="Trạng thái: Đang Dừng ⏹", text_color="#EF5350")
            self.log("⏹ Đã gửi tín hiệu DỪNG kịch bản tức thì.")

    def _play_worker(self):
        """Luồng ngầm chạy Replay qua ADB với cơ chế Absolute Timeline Scheduling chuẩn xác 100%"""
        emu = self._get_selected_emulator_info()
        tab_idx = emu["index"]
        emu_name = emu["name"]
        target_w = emu["w"]
        target_h = emu["h"]

        # Đọc tùy chọn tốc độ
        speed_text = self.speed_combobox.get()
        try:
            speed = float(speed_text.split("x")[0].strip())
        except Exception:
            speed = 1.0

        # Đọc số vòng lặp
        loop_setting = self.loop_combobox.get()
        max_loops = 999999
        if "lần" in loop_setting:
            try:
                max_loops = int(loop_setting.replace("lần", "").strip())
            except Exception:
                max_loops = 1

        self.after(0, self.log, f"🚀 BẮT ĐẦU REPLAY trên [{tab_idx}] {emu_name} ({target_w}x{target_h}, Tốc độ: {speed}x)...")

        current_loop = 0
        while current_loop < max_loops and not self.stop_event.is_set():
            current_loop += 1
            loop_tag = f"Vòng {current_loop}/{max_loops if max_loops < 999999 else '∞'}"
            self.after(0, self.log, f"🔄 [{loop_tag}] Bắt đầu chu kỳ...")

            cycle_start = time.time()

            for i, action in enumerate(self.parsed_actions, start=1):
                if self.stop_event.is_set():
                    break

                # Tính toán mốc thời gian đích theo trục thời gian tuyệt đối (Absolute Timeline)
                target_offset = (action["timing"] / 1000.0) / speed
                target_timestamp = cycle_start + target_offset

                # Chờ đến đúng mốc thời gian đích (bù trừ chính xác thời gian thực thi của lệnh ADB trước đó)
                while not self.stop_event.is_set():
                    now = time.time()
                    time_left = target_timestamp - now
                    if time_left <= 0:
                        break
                    sleep_time = min(time_left, 0.02)
                    time.sleep(sleep_time)

                if self.stop_event.is_set():
                    break

                # Thực thi hành động qua ADB
                act_type = action["type"]
                cmd = action.get("cmd", "")

                if act_type in ["click", "swipe", "wheel"]:
                    ok = self._exec_adb(tab_idx, f"shell {cmd}")
                    status_icon = "🎯" if ok else "⚠️"
                    self.after(0, self.log, f"{status_icon} [{i}/{len(self.parsed_actions)}] {action['desc']}")

                elif act_type == "text":
                    raw_text = action["text"]
                    typed = False
                    if self.ldconsole_path and os.path.exists(self.ldconsole_path):
                        try:
                            res = subprocess.run(
                                [self.ldconsole_path, "action", "--index", str(tab_idx), "--key", "call.keyboard", "--value", raw_text],
                                timeout=5,
                                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                            )
                            if res and res.returncode == 0:
                                typed = True
                        except Exception:
                            pass
                    if not typed:
                        safe_text = raw_text.replace(" ", "%s")
                        self._exec_adb(tab_idx, f"shell input text {safe_text}")
                    self.after(0, self.log, f"🎯 [{i}/{len(self.parsed_actions)}] Gõ chữ: '{raw_text}'")

            elapsed = time.time() - cycle_start
            if not self.stop_event.is_set():
                self.after(0, self.log, f"✅ [{loop_tag}] Hoàn thành chu kỳ (Thời gian thực tế: {elapsed:.2f}s).")
                time.sleep(0.4)

        # Kết thúc luồng
        self.after(0, self._on_finish_play)

    def _exec_adb(self, tab_index, cmd_str):
        """Gửi lệnh ADB vào giả lập qua ldconsole.exe adb và fallback sang adb.exe"""
        # 1. Thử qua ldconsole.exe / dnconsole.exe
        if self.ldconsole_path and os.path.exists(self.ldconsole_path):
            try:
                full_cmd = [self.ldconsole_path, "adb", "--index", str(tab_index), "--command", cmd_str]
                res = subprocess.run(
                    full_cmd, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    timeout=5, 
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
                if res and res.returncode == 0:
                    return True
            except Exception:
                pass

        # 2. Dự phòng: gọi trực tiếp qua adb.exe
        adb_path = os.path.join(self.ld_path, "adb.exe")
        if os.path.exists(adb_path):
            port = 5555 + (tab_index * 2)
            emu_serial = f"emulator-{5554 + tab_index * 2}"
            sub_args = cmd_str.split()
            for dev in [f"127.0.0.1:{port}", emu_serial]:
                try:
                    res = subprocess.run(
                        [adb_path, "-s", dev] + sub_args,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                    )
                    if res and res.returncode == 0:
                        return True
                except Exception:
                    pass
        return False

    def _on_finish_play(self):
        """Xử lý UI khi luồng chạy kết thúc"""
        self.is_playing = False
        self.switch_play.deselect()
        self.status_lbl.configure(text="Trạng thái: Đã Dừng ⏹", text_color="#EF5350")
        self.log("🏁 Hoàn tất phát kịch bản.")


if __name__ == "__main__":
    app = RecordPlayerApp()
    app.mainloop()
