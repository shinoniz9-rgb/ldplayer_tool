# -*- coding: utf-8 -*-
"""
========================================================================================
🔒 [BẢN BACKUP THAM CHIẾU ĐỘC LẬP & KHÓA NGUYÊN BẢN]: CARD D (40 NPC / 2K)
========================================================================================
Ngày tạo: 2026-09-02
Mục đích:
- Lưu trữ độc lập toàn bộ giao diện và logic thực thi của Card D (40 NPC / 2K - Lôi Đài & Nhị Kiều).
- Mã nguồn này đã được tối ưu hóa toàn bộ 100% vùng ROI, ngưỡng và luân phiên Buff Skill (3 HP / 1 SP).
- Độc lập 100% với các chỉnh sửa phát sinh sau này trên file main.py.

========================================================================================
📌 BẢNG TRA CỨU TỌA ĐỘ VÙNG QUÉT ROI & NGƯỠNG THRESHOLD CARD D
========================================================================================
1. d_dichuyen.png : (0, 400, 1280, 720)       - Threshold: 0.70 (70%) [Điểm Gần Cổng]
2. d_conglt.png   : (0, 400, 1280, 720)       - Threshold: 0.80 (80%) [Cổng Lôi Đài]
3. d_vaolt.png    : (0, 400, 1280, 720)       - Threshold: 0.80 (80%) [Vào Lôi Đài]
4. d_chien.png    : (280, 490, 1280, 720)     - Threshold: 0.80 (80%) [Nút Chiến Lôi Đài]
5. d_vaotran.png  : (275, 540, 980, 670)      - Threshold: 0.75 (75%) [Nút Vào Trận Lôi Đài]
6. d_xacdinh.png  : (275, 540, 980, 670)      - Threshold: 0.80 (80%) [Xác Định kết thúc trận]
7. d_35.png       : (1020, 265, 1125, 295)    - Threshold: 0.80 (80%) [Nhận diện mốc 35/35]
8. d_buoc1.png    : (0, 0, 1280, 720)         - Threshold: 0.80 (80%) [Toàn màn hình - Nhị Kiều Bước 1]
9. d_buoc2.png    : (0, 0, 1280, 720)         - Threshold: 0.75 (75%) [Toàn màn hình - Nhị Kiều Bước 2]
10. d_buoc3.png   : (0, 0, 1280, 720)         - Threshold: 0.80 (80%) [Toàn màn hình - Nhị Kiều Bước 3]
11. d_dinh.png    : (1060, 0, 1280, 40)       - Threshold: 0.80 (80%) [Đỉnh Nhị Kiều Trệt - 10]
12. d_thap14.png  : (1060, 0, 1280, 40)       - Threshold: 0.80 (80%) [Tầng 14 Nhị Kiều 11 - 14]
13. f_tieptheo.png: (1050, 530, 1165, 680)    - Threshold: 0.70 - 0.80 [Nút Tiếp Theo]
14. f_vaotran.png : (1215, 0, 1280, 45)       - Threshold: 0.80 (80%) [CHỈ QUÉT NHẬN DIỆN - Báo kết thúc trận]
15. f_dung.png    : (640, 0, 1280, 145)       - Threshold: 0.80 (80%) [CHỈ QUÉT NHẬN DIỆN - Báo lượt đánh mới]
16. login_auto.png: (0, 100, 240, 190)        - Threshold: 0.85 (85%) [Nút Auto góc trên trái]
17. f_hp/f_sp.png : (640, 0, 1280, 145)       - Threshold: 0.85 (85%) [Kỹ năng Buff HP/SP góc trên phải]
========================================================================================
"""

import os
import re
import time
import threading
from datetime import datetime
import customtkinter as ctk

# =========================================================================
# PHẦN 1: MÃ NGUỒN GIAO DIỆN DESKTOP (GUI) CỦA CARD D
# =========================================================================
def build_card_D_ui(self, parent_container, char_options):
    """
    Xây dựng giao diện Card D (40 NPC / 2K) trên Desktop GUI
    """
    # ------------------- CARD D: 40 NPC / 2K -------------------
    self.card_D = ctk.CTkFrame(parent_container, corner_radius=10)
    self.card_D.pack(fill="both", expand=True, padx=6, pady=4)
    self.card_D.grid_columnconfigure(0, weight=1)
    self.card_D.grid_rowconfigure(0, weight=0)
    self.card_D.grid_rowconfigure(1, weight=1)

    hdr_D = ctk.CTkFrame(self.card_D, fg_color="transparent")
    hdr_D.grid(row=0, column=0, padx=8, pady=(4, 2), sticky="ew")
    hdr_D.grid_columnconfigure(0, weight=1)
    hdr_D.grid_columnconfigure(1, weight=0)
    hdr_D.grid_columnconfigure(2, weight=0)

    self.lbl_D = ctk.CTkLabel(
        hdr_D,
        text="40 NPC / 2K",
        font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        text_color="#38BDF8"
    )
    self.lbl_D.grid(row=0, column=0, sticky="w")

    # Ô [ ] Dừng
    self.chk_pause_D = ctk.CTkCheckBox(
        hdr_D,
        text="Dừng",
        variable=self.var_pause_D,
        command=self._on_pause_D_toggled,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
        checkbox_width=16,
        checkbox_height=16,
        border_width=2,
        corner_radius=5,
        fg_color="#EA580C",
        hover_color="#C2410C",
        checkmark_color="#FFFFFF",
        text_color="#FFFFFF"
    )
    self.chk_pause_D.grid(row=0, column=1, padx=(0, 6), sticky="e")

    # Công tắc ON/OFF
    self.switch_D = ctk.CTkSwitch(
        hdr_D,
        text="",
        variable=self.var_switch_D,
        command=self._on_switch_D_toggled,
        width=40,
        height=20,
        switch_width=36,
        switch_height=18,
        fg_color="#374151",
        progress_color="#EA580C"
    )
    self.switch_D.grid(row=0, column=2, sticky="e")

    # Thân Card D
    body_D = ctk.CTkFrame(self.card_D, fg_color="transparent")
    body_D.grid(row=1, column=0, padx=6, pady=(2, 6), sticky="nsew")
    body_D.grid_columnconfigure(0, weight=1)
    body_D.grid_rowconfigure(0, weight=1, uniform="card_d_rows")
    body_D.grid_rowconfigure(1, weight=2, uniform="card_d_rows")

    # Row 1: Tổ Đội + Menu Vị trí xuất chiến
    row_D1 = ctk.CTkFrame(body_D, fg_color="transparent")
    row_D1.grid(row=0, column=0, sticky="ew")

    self.chk_D2 = ctk.CTkCheckBox(
        row_D1, text="Tổ Đội", variable=self.var_D2, command=self._on_checkbox_toggled,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
        fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF",
        checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
    )
    self.chk_D2.pack(side="left", padx=(4, 0))

    self.combo_D_team_char = ctk.CTkOptionMenu(
        row_D1,
        values=char_options,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
        dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
        text_color="#FFFFFF",
        dropdown_text_color="#FFFFFF",
        height=24,
        width=115,
        dynamic_resizing=False,
        fg_color="#374151",
        button_color="#4B5563",
        button_hover_color="#6B7280",
        command=lambda choice: self._on_checkbox_toggled()
    )
    self.combo_D_team_char.set(char_options[0] if char_options else "Xuất Chiến")
    self.combo_D_team_char.pack(side="right", padx=(0, 4))

    # Khung 2 Cột Hoạt Động (40 NPC & Nhị Kiều) với vạch cam đứng ngăn cách
    act_frame_D = ctk.CTkFrame(body_D, fg_color="transparent")
    act_frame_D.grid(row=1, column=0, sticky="nsew")
    act_frame_D.grid_columnconfigure(0, weight=1, uniform="d_act_cols")
    act_frame_D.grid_columnconfigure(1, weight=0)
    act_frame_D.grid_columnconfigure(2, weight=1, uniform="d_act_cols")
    act_frame_D.grid_rowconfigure((0, 1), weight=1, uniform="act_subrows")

    # Hàng 2: [ ] 40 NPC  |  [ ] Nhị Kiều
    self.chk_D3 = ctk.CTkCheckBox(
        act_frame_D, text="40 NPC", variable=self.var_D3, command=self._on_D3_toggled,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
        checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5,
        fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF"
    )
    self.chk_D3.grid(row=0, column=0, sticky="w", padx=(4, 0))

    divider_vert_D = ctk.CTkFrame(act_frame_D, width=2, corner_radius=0, fg_color="#EA580C", border_width=0)
    divider_vert_D.grid(row=0, column=1, rowspan=2, sticky="ns", padx=4, pady=2)

    self.chk_D4 = ctk.CTkCheckBox(
        act_frame_D, text="Nhị Kiều", variable=self.var_D4, command=self._on_D4_toggled,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
        checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5,
        fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF"
    )
    self.chk_D4.grid(row=0, column=2, sticky="w", padx=(4, 0))

    # Hàng 3: Menu Auto/Click (40 NPC)  |  Menu Tầng (Nhị Kiều)
    self.combo_D_chien_dau = ctk.CTkOptionMenu(
        act_frame_D,
        values=["Auto", "Click"],
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
        dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
        text_color="#FFFFFF",
        dropdown_text_color="#FFFFFF",
        height=24,
        width=115,
        dynamic_resizing=False,
        fg_color="#374151",
        button_color="#4B5563",
        button_hover_color="#6B7280",
        command=lambda choice: self._on_checkbox_toggled()
    )
    self.combo_D_chien_dau.set("Auto")
    self.combo_D_chien_dau.grid(row=1, column=0, sticky="ew", padx=(4, 0))

    tang_options = ["Trệt - 10", "11 - 14"]
    self.combo_D_tang = ctk.CTkOptionMenu(
        act_frame_D,
        values=tang_options,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
        dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
        text_color="#FFFFFF",
        dropdown_text_color="#FFFFFF",
        height=24,
        width=115,
        dynamic_resizing=False,
        fg_color="#374151",
        button_color="#4B5563",
        button_hover_color="#6B7280",
        command=lambda choice: self._on_checkbox_toggled()
    )
    self.combo_D_tang.set("Trệt - 10")
    self.combo_D_tang.grid(row=1, column=2, sticky="ew", padx=(0, 4))


# =========================================================================
# PHẦN 2: CÁC CALLBACK ĐIỀU KHIỂN & KIỂM TRA DỪNG AN TOÀN
# =========================================================================
def should_stop_card_D(self) -> bool:
    """Kiểm tra điều kiện dừng / tạm dừng cho Card D 40 NPC / 2K"""
    if self.stop_requested or not self.var_switch_D.get():
        return True
    if hasattr(self, 'var_pause_D') and self.var_pause_D.get():
        self.after(0, self.log_info, "⏸️ [40 NPC] Ô Tạm Dừng đang tích ➔ Tạm dừng tiến trình (nhả ô Tạm Dừng để chạy tiếp)...")
        while self.var_pause_D.get() and self.var_switch_D.get() and not self.stop_requested:
            time.sleep(0.5)
        if self.var_switch_D.get() and not self.stop_requested:
            self.after(0, self.log_info, "▶️ [40 NPC] Đã nhả ô Tạm Dừng ➔ Khôi phục chạy tiếp 40 NPC!")
    return self.stop_requested or not self.var_switch_D.get()


def on_switch_D_toggled(self):
    """Callback công tắc Card D: Khi trượt OFF ➔ Ngắt tiến trình & nhả ô Dừng; khi ON ➔ Khởi chạy worker"""
    self._on_checkbox_toggled()
    if not self.var_switch_D.get():
        if hasattr(self, 'var_pause_D'):
            self.var_pause_D.set(False)
        self.save_config()
        self.log_info("🛑 [CARD D: 40 NPC] Công tắc gạt về OFF ➔ Đã ngắt tiến trình & nhả ô Tạm Dừng Card D!")
    else:
        self.stop_requested = False
        tab_name, tab_index = self._get_selected_ld_info()
        if tab_index is None:
            self.log_error("Vui lòng chọn một Tab LDPlayer trước khi bật công tắc 40 NPC!")
            self.var_switch_D.set(False)
            if hasattr(self, 'var_pause_D'):
                self.var_pause_D.set(False)
            self.save_config()
            return

        dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")
        if not os.path.exists(dnconsole_path):
            dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")

        if not os.path.exists(dnconsole_path):
            self.log_error(f"Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
            self.var_switch_D.set(False)
            if hasattr(self, 'var_pause_D'):
                self.var_pause_D.set(False)
            self.save_config()
            return

        self.log_info(f"⚡ [40 NPC] Công tắc vừa trượt ON ➔ Khởi chạy ngay thao tác trên Tab: {tab_name} (Index: {tab_index})...")
        threading.Thread(target=self._execute_card_D_40_npc, args=(dnconsole_path, tab_name, tab_index), daemon=True).start()


def on_pause_D_toggled(self):
    """Callback ô Tạm Dừng Card 40 NPC"""
    self._on_checkbox_toggled()
    if self.var_pause_D.get():
        self.log_info("⏸️ [40 NPC] Tích ô Dừng ➔ Tạm dừng hoạt động 40 NPC (nhả ô Dừng sẽ chạy tiếp)!")
    else:
        self.log_info("▶️ [40 NPC] Nhả ô Dừng ➔ Khôi phục chạy tiếp 40 NPC!")
    self.save_config()


def on_D3_toggled(self):
    """Khi tích sự kiện 40 NPC -> Tự động bỏ chọn Nhị Kiều"""
    if self.var_D3.get():
        self.var_D4.set(False)
    self._update_card_D_row2_state()
    self._on_checkbox_toggled()


def on_D4_toggled(self):
    """Khi tích sự kiện Nhị Kiều -> Tự động bỏ chọn 40 NPC"""
    if self.var_D4.get():
        self.var_D3.set(False)
    self._update_card_D_row2_state()
    self._on_checkbox_toggled()


def update_card_D_row2_state(self):
    """Cập nhật trạng thái đóng/mở sáng các ô checkbox & dropdown của Card D"""
    if not hasattr(self, 'combo_D_chien_dau') or not hasattr(self, 'combo_D_tang'):
        return
    if self.var_D3.get():
        self.combo_D_chien_dau.configure(state="normal", fg_color="#374151", button_color="#4B5563", button_hover_color="#6B7280", text_color="#FFFFFF")
    else:
        self.combo_D_chien_dau.configure(state="disabled", fg_color="#1E293B", button_color="#1E293B", button_hover_color="#1E293B", text_color="#64748B")

    if self.var_D4.get():
        self.combo_D_tang.configure(state="normal", fg_color="#374151", button_color="#4B5563", button_hover_color="#6B7280", text_color="#FFFFFF")
    else:
        self.combo_D_tang.configure(state="disabled", fg_color="#1E293B", button_color="#1E293B", button_hover_color="#1E293B", text_color="#64748B")


# =========================================================================
# PHẦN 3: LOGIC THỰC THI CHI TIẾT TỔ ĐỘI & ĐỔI VỊ TRÍ TƯỚNG
# =========================================================================
def run_40_npc_team_and_char_position(self, dnconsole_path: str, tab_index: str, selected_team_char: str, skip_char_change: bool = False):
    """PHẦN 4: TỔ ĐỘI VÀ CHUYỂN ĐỔI VỊ TRÍ NHÂN VẬT"""
    if self._should_stop_card_D(): return

    if not skip_char_change and not self.var_D2.get():
        self.after(0, self.log_info, "ℹ️ [40 NPC - Phần 4] Ô 'Tổ Đội' KHÔNG được tích -> Bỏ qua Phần 4.")
        return

    self.after(0, self.log_info, f"🚀 [40 NPC - Phần 4] Kích hoạt Tổ Đội (Vị trí: '{selected_team_char}', Bỏ qua đổi vị trí: {skip_char_change})...")

    if skip_char_change or selected_team_char == "Xuất Chiến":
        self.after(0, self.log_info, "ℹ️ Giữ nguyên vị trí nhân vật hiện tại ➔ Bỏ qua bước đổi đội hình.")
        return

    # Quét mở giao diện Đội
    if self._should_stop_card_D(): return
    self.after(0, self.log_info, "👁️ [40 NPC - Phần 4] Quét tìm ảnh 'card_b/b_doi.png' (85%)...")
    b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
    if b_doi_x is not None and b_doi_y is not None:
        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_b/b_doi.png' tại ({b_doi_x}, {b_doi_y})! Tap click vào ảnh ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
        time.sleep(0.4)
    else:
        self.after(0, self.log_info, "👉 Chưa thấy 'card_b/b_doi.png' ➔ Tap nút xanh góc dưới phải (1240, 680) mở menu ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
        time.sleep(0.4)
        if self._should_stop_card_D(): return
        b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
        if b_doi_x is not None and b_doi_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_b/b_doi.png' tại ({b_doi_x}, {b_doi_y})! Tap click vào ảnh ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
            time.sleep(0.4)

    # Thao tác đổi vị trí nhân vật cụ thể (Mỗi lượt tap hoãn 0.5s)
    if self._should_stop_card_D(): return
    if selected_team_char == "Vị Trí 1":
        self.after(0, self.log_info, "👉 [Vị Trí 1] Tap (560, 340) ➔ (560, 255) ➔ (1090, 110) (Hoãn 0.5s)...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
        time.sleep(0.5)
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
        time.sleep(0.5)
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
        time.sleep(0.5)
    elif selected_team_char == "Vị Trí 2":
        self.after(0, self.log_info, "👉 [Vị Trí 2] Tap (560, 255) ➔ (560, 340) ➔ (1090, 110) (Hoãn 0.5s)...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
        time.sleep(0.5)
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
        time.sleep(0.5)
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
        time.sleep(0.5)
    elif selected_team_char == "Vị Trí 3":
        self.after(0, self.log_info, "👉 [Vị Trí 3] Tap (560, 255) ➔ (560, 430) ➔ (1090, 110) (Hoãn 0.5s)...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
        time.sleep(0.5)
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 430"])
        time.sleep(0.5)
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
        time.sleep(0.5)
    elif selected_team_char == "Vị Trí 4":
        self.after(0, self.log_info, "👉 [Vị Trí 4] Tap (560, 255) ➔ (560, 520) ➔ (1090, 110) (Hoãn 0.5s)...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
        time.sleep(0.5)
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
        time.sleep(0.5)
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
        time.sleep(0.5)

    # Đóng menu giao diện Đội
    if self._should_stop_card_D(): return
    self.after(0, self.log_info, "👉 Tap (1240, 680) ➔ Hoãn 0.4s để đóng menu giao diện Đội...")
    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
    time.sleep(0.4)


# =========================================================================
# PHẦN 4: CHUỖI BUFF SKILL (3 HP / 1 SP) LUÂN PHIÊN
# =========================================================================
def execute_buff_skill_cycle(self, dnconsole_path: str, tab_index: str, log_tag: str = "40 NPC / 2K"):
    """Thực thi chuỗi Buff Skill (3 HP / 1 SP) lặp lại liên tục cho 40 NPC và Nhị Kiều"""
    def _wait_for_turn_start():
        """
        Quét card_f/f_vaotran.png (80%, 1s/lần) song song card_f/f_dung.png (80%, 0.5s/lần).
        - Nếu thấy f_vaotran.png -> ngắt toàn bộ chuỗi Buff (return 'END_BATTLE').
        - Nếu thấy f_dung.png -> ngưng quét f_vaotran.png -> quét f_tieptheo.png (80%, ROI 1050,530,1165,680) 0.25s/lần trong 0.5s.
          Tap f_tieptheo nếu có, hoãn 0.2s -> return 'START_TURN'.
        """
        last_vaotran_check = 0.0
        while not self._should_stop_card_D():
            now = time.time()
            if now - last_vaotran_check >= 1.0:
                vt_x, vt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_vaotran.png", threshold=0.80, region=(1215, 0, 1280, 45))
                if vt_x is not None and vt_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_f/f_vaotran.png' tại ({vt_x}, {vt_y}) ➔ Kết thúc trận đánh!")
                    return "END_BATTLE"
                last_vaotran_check = now

            dung_x, dung_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_dung.png", threshold=0.80, region=(640, 0, 1280, 145))
            if dung_x is not None and dung_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_f/f_dung.png' tại ({dung_x}, {dung_y}) ➔ Bắt đầu lượt mới!")
                found_tt = False
                for _ in range(2):
                    if self._should_stop_card_D(): break
                    tt_x, tt_y = self._find_template_on_screen(
                        dnconsole_path, tab_index, "card_f/f_tieptheo.png",
                        threshold=0.80, region=(1050, 530, 1165, 680)
                    )
                    if tt_x is not None and tt_y is not None:
                        self.after(0, self.log_info, f"🎯 Phát hiện 'card_f/f_tieptheo.png' tại ({tt_x}, {tt_y})! Tap click ➔ Hoãn 0.2s...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {tt_x} {tt_y}"])
                        found_tt = True
                        break
                    time.sleep(0.25)

                if not found_tt:
                    self.after(0, self.log_info, "ℹ️ Không thấy 'f_tieptheo.png' trong 0.5s ➔ Hoãn 0.2s sang Bước 2...")
                time.sleep(0.2)
                return "START_TURN"

            time.sleep(0.1)

        return "END_BATTLE"

    while not self._should_stop_card_D():
        # Phase 1: Lượt 1 - Buff HP (3 Lần liên tiếp: hp_round = 1 ➔ 3)
        for hp_round in range(1, 4):
            if self._should_stop_card_D(): return
            self.after(0, self.log_info, f"🔄 [{log_tag} - Buff 3HP/1SP] ➔ [HP Lần {hp_round}/3 - Bước 1] Quét song song f_vaotran (1s) & f_dung (0.5s)...")
            res = _wait_for_turn_start()
            if res == "END_BATTLE":
                return

            self.after(0, self.log_info, f"🔄 [{log_tag} - Buff 3HP/1SP] ➔ [HP Lần {hp_round}/3 - Bước 2] Quét & Buff HP...")
            hp_x, hp_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/skill/f_hp.png", threshold=0.85, region=(640, 0, 1280, 145))
            if hp_x is not None and hp_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'f_hp.png' tại ({hp_x}, {hp_y})! Tap skill ➔ Tap target (905, 515)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {hp_x} {hp_y}"])
                time.sleep(0.2)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 905 515"])
                time.sleep(0.2)
            self._tap_login_auto_twice(dnconsole_path, tab_index)
            self.after(0, self.log_info, "⏳ Hoãn cố định 5.0s (chờ hồi skill/lượt đánh)...")
            if self._sleep_with_stop_check(5.0): return

        # Phase 2: Lượt 2 - Buff SP (1 Lần)
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, f"🔄 [{log_tag} - Buff 3HP/1SP] ➔ [SP Lượt 2 - Bước 1] Quét song song f_vaotran (1s) & f_dung (0.5s)...")
        res = _wait_for_turn_start()
        if res == "END_BATTLE":
            return

        self.after(0, self.log_info, f"🔄 [{log_tag} - Buff 3HP/1SP] ➔ [SP Lượt 2 - Bước 2] Quét & Buff SP...")
        sp_x, sp_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/skill/f_sp.png", threshold=0.85, region=(640, 0, 1280, 145))
        if sp_x is not None and sp_y is not None:
            self.after(0, self.log_info, f"🎯 Phát hiện 'f_sp.png' tại ({sp_x}, {sp_y})! Tap skill ➔ Tap target (905, 515)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {sp_x} {sp_y}"])
            time.sleep(0.2)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 905 515"])
            time.sleep(0.2)
        self._tap_login_auto_twice(dnconsole_path, tab_index)
        self.after(0, self.log_info, "⏳ Hoãn cố định 5.0s (chờ hồi skill/lượt đánh)...")
        if self._sleep_with_stop_check(5.0): return


# =========================================================================
# PHẦN 5: QUY TRÌNH THỰC THI SỰ KIỆN 40 NPC (AUTO & CLICK)
# =========================================================================
def run_40_npc_su_kien_tang(self, dnconsole_path: str, tab_index: str, selected_tang: str, selected_team_char: str, selected_chien_dau: str = "Auto"):
    """THAO TÁC 2: 40 NPC (CHỈ THỰC THI KHI Ô 40 NPC VAR_D3 ĐƯỢC TÍCH)"""
    if self._should_stop_card_D(): return

    if not self.var_D3.get():
        self.after(0, self.log_info, "ℹ️ [40 NPC] Ô '40 NPC' KHÔNG được tích -> Bỏ qua.")
        return

    self.after(0, self.log_info, f"🚀 [40 NPC] Khởi chạy ô 40 NPC (Chế độ menu: '{selected_chien_dau}')...")

    if selected_chien_dau == "Auto":
        # =========================================================================
        # 📌 QUY TRÌNH 1: CHẾ ĐỘ MENU: AUTO
        # =========================================================================
        # BƯỚC 1 (Chờ 20H00): Vòng lặp chờ đồng hồ hệ thống chạm mốc 20:00:00
        if self._should_stop_card_D(): return
        now = datetime.now()
        target_time = now.replace(hour=20, minute=0, second=0, microsecond=0)
        if now < target_time:
            self.after(0, self.log_info, f"⏳ [40 NPC - Auto - Bước 1] Đang chờ đến mốc 20:00:00 (Hiện tại: {now.strftime('%H:%M:%S')})...")
            while datetime.now() < target_time:
                if self._should_stop_card_D(): return
                time.sleep(1.0)

        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "🎯 [40 NPC - Auto - Bước 1] Đã đến mốc 20:00:00!")

        # 2. Kiểm Tra Đủ Thành Viên Tổ Đội (Lần 1)
        if self._should_stop_card_D(): return
        list_B = list(getattr(self, 'list_E_B', []))
        if list_B:
            self.after(0, self.log_info, f"👁️ [40 NPC - Auto] Kiểm tra độ đầy đủ tổ đội Lần 1 ({len(list_B)} thành viên: {', '.join(list_B)})...")
            while not self._should_stop_card_D():
                lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(860, 70, 1170, 200))
                if lx_x is not None and lx_y is not None:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                    time.sleep(0.4)

                if self._should_stop_card_D(): return
                b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(730, 405, 1200, 720))
                if b_doi_x is not None and b_doi_y is not None:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                    time.sleep(0.4)
                else:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
                    time.sleep(0.4)
                    if self._should_stop_card_D(): return
                    b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(730, 405, 1200, 720))
                    if b_doi_x is not None and b_doi_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                        time.sleep(0.4)

                all_present = True
                missing_list = []
                for char_name in list_B:
                    if self._should_stop_card_D(): return
                    chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/40npc2k/{char_name}.png", threshold=0.80, region=(305, 150, 1105, 625))
                    if chk_x is None or chk_y is None:
                        chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/{char_name}.png", threshold=0.80, region=(305, 150, 1105, 625))
                    if chk_x is None or chk_y is None:
                        all_present = False
                        missing_list.append(char_name)

                if all_present:
                    self.after(0, self.log_info, f"✅ [40 NPC - Auto] Lần 1: Tổ đội đã ĐỦ {len(list_B)} thành viên!")
                    lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(860, 70, 1170, 200))
                    if lx_x is not None and lx_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                        time.sleep(0.4)
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
                    time.sleep(0.4)
                    break
                else:
                    self.after(0, self.log_info, f"⚠️ [40 NPC - Auto] Lần 1: Đội thiếu: {', '.join(missing_list)} ➔ Gọi Thao tác 1 Tổ Đội...")
                    lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(860, 70, 1170, 200))
                    if lx_x is not None and lx_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                        time.sleep(0.4)
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
                    time.sleep(0.4)
                    self._execute_card_E_for_mode(dnconsole_path, "", tab_index, mode=1)

        # BƯỚC 3 (Vào Lôi Đài):
        # 3.1: Quét & Tap d_dichuyen.png (70%, ROI 0,400,1280,720) -> Hoãn 2.0s
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👁️ [40 NPC - Bước 3.1] Quét & tap Điểm Gần Cổng 'card_d/40npc/d_dichuyen.png' (70%, ROI 0,400,1280,720)...")
        while not self._should_stop_card_D():
            dc_x, dc_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/40npc/d_dichuyen.png", threshold=0.70, region=(0, 400, 1280, 720))
            if dc_x is not None and dc_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút Điểm Gần Cổng tại ({dc_x}, {dc_y})! Tap click ➔ Hoãn 2.0s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {dc_x} {dc_y}"])
                time.sleep(2.0)
                break
            time.sleep(0.5)

        # 3.2: Quét & Tap d_conglt.png (80%, ROI 0,400,1280,720) -> Hoãn 2.0s
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👁️ [40 NPC - Bước 3.2] Quét & tap Cổng Lôi Đài 'card_d/40npc/d_conglt.png' (80%, ROI 0,400,1280,720)...")
        while not self._should_stop_card_D():
            clt_x, clt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/40npc/d_conglt.png", threshold=0.80, region=(0, 400, 1280, 720))
            if clt_x is not None and clt_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện Cổng Lôi Đài 'card_d/40npc/d_conglt.png' tại ({clt_x}, {clt_y})! Tap click ➔ Hoãn 2.0s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {clt_x} {clt_y}"])
                time.sleep(2.0)
                break
            time.sleep(0.5)

        # 3.3: Quét & Tap d_vaolt.png (80%, ROI 0,400,1280,720) -> Hoãn 3.0s
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👁️ [40 NPC - Bước 3.3] Quét & tap nút Vào Lôi Đài 'card_d/40npc/d_vaolt.png' (80%, ROI 0,400,1280,720)...")
        while not self._should_stop_card_D():
            vlt_x, vlt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/40npc/d_vaolt.png", threshold=0.80, region=(0, 400, 1280, 720))
            if vlt_x is not None and vlt_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'card_d/40npc/d_vaolt.png' tại ({vlt_x}, {vlt_y})! Tap click ➔ Hoãn 3.0s bước vào Lôi Đài...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {vlt_x} {vlt_y}"])
                time.sleep(3.0)
                break
            time.sleep(0.5)

        # BƯỚC 4 (Kiểm tra Đội lần 2): Quét lại danh sách thành viên tổ đội sau khi đã vào bản đồ lôi đài
        if self._should_stop_card_D(): return
        if list_B:
            self.after(0, self.log_info, f"👁️ [40 NPC - Auto - Bước 4] Kiểm tra độ đầy đủ tổ đội Lần 2 ({len(list_B)} thành viên)...")
            while not self._should_stop_card_D():
                lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(860, 70, 1170, 200))
                if lx_x is not None and lx_y is not None:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                    time.sleep(0.4)

                if self._should_stop_card_D(): return
                b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(730, 405, 1200, 720))
                if b_doi_x is not None and b_doi_y is not None:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                    time.sleep(0.4)
                else:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
                    time.sleep(0.4)
                    if self._should_stop_card_D(): return
                    b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(730, 405, 1200, 720))
                    if b_doi_x is not None and b_doi_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                        time.sleep(0.4)

                all_present = True
                missing_list = []
                for char_name in list_B:
                    if self._should_stop_card_D(): return
                    chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/40npc2k/{char_name}.png", threshold=0.80, region=(305, 150, 1105, 625))
                    if chk_x is None or chk_y is None:
                        chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/{char_name}.png", threshold=0.80, region=(305, 150, 1105, 625))
                    if chk_x is None or chk_y is None:
                        all_present = False
                        missing_list.append(char_name)

                if all_present:
                    self.after(0, self.log_info, f"✅ [40 NPC - Auto - Bước 4] Lần 2: Tổ đội đã ĐỦ {len(list_B)} thành viên!")
                    lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(860, 70, 1170, 200))
                    if lx_x is not None and lx_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                        time.sleep(0.4)
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
                    time.sleep(0.4)
                    break
                else:
                    self.after(0, self.log_info, f"⚠️ [40 NPC - Auto - Bước 4] Lần 2: Đội thiếu: {', '.join(missing_list)} ➔ Gọi Thao tác 1 Tổ Đội...")
                    lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(860, 70, 1170, 200))
                    if lx_x is not None and lx_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                        time.sleep(0.4)
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
                    time.sleep(0.4)
                    self._execute_card_E_for_mode(dnconsole_path, "", tab_index, mode=1)

        # BƯỚC 5 (Vào trận đầu tiên - 9 Thao tác):
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "🚀 [40 NPC - Auto - Bước 5] Bắt đầu 9 Thao tác vào trận đầu tiên...")

        # 5.1: Di chuyển Chéo Phải - Trên (W+D) giữ 3.0s (640,360 -> 890,110) -> Hoãn 0.2s
        self.after(0, self.log_info, "🕹️ [Bước 5.1] Swipe Chéo Phải - Trên (W+D) 3.0s (640,360 ➔ 890,110)...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 640 360 890 110 3000"])
        if self._should_stop_card_D(): return
        time.sleep(0.2)

        # 5.2: Di chuyển Phải (D) giữ 0.3s (640,360 -> 890,360) -> Hoãn 0.2s
        self.after(0, self.log_info, "🕹️ [Bước 5.2] Swipe Phải (D) 0.3s (640,360 ➔ 890,360)...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 640 360 890 360 300"])
        if self._should_stop_card_D(): return
        time.sleep(0.2)

        # 5.3: Di chuyển Chéo Phải - Trên (W+D) giữ 1.0s (640,360 -> 890,110) -> Hoãn 0.2s
        self.after(0, self.log_info, "🕹️ [Bước 5.3] Swipe Chéo Phải - Trên (W+D) 1.0s (640,360 ➔ 890,110)...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 640 360 890 110 1000"])
        if self._should_stop_card_D(): return
        time.sleep(0.2)

        # 5.4: Di chuyển Phải (D) giữ 1.0s (640,360 -> 890,360) -> Hoãn 0.2s
        self.after(0, self.log_info, "🕹️ [Bước 5.4] Swipe Phải (D) 1.0s (640,360 ➔ 890,360)...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 640 360 890 360 1000"])
        if self._should_stop_card_D(): return
        time.sleep(0.2)

        # 5.5: Tap liên tục (1240, 605) mỗi 0.4s (tối đa 20 lần) tìm d_chien.png (80%, ROI 280,490,1280,720)
        self.after(0, self.log_info, "👉 [Bước 5.5] Tap liên tục (1240, 605) mỗi 0.4s (tối đa 20 lần) tìm 'card_d/40npc/d_chien.png' (80%)...")
        for retry in range(20):
            if self._should_stop_card_D(): return
            ch_x, ch_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/40npc/d_chien.png", threshold=0.80, region=(280, 490, 1280, 720))
            if ch_x is not None and ch_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_d/40npc/d_chien.png' tại ({ch_x}, {ch_y})! Dừng click.")
                break
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 605"])
            time.sleep(0.4)

        # 5.6: Tap (1135, 565) -> Hoãn 0.4s (Chọn trận)
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👉 [Bước 5.6] Tap (1135, 565) chọn trận ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1135 565"])
        time.sleep(0.4)

        # 5.7: Quét & Tap card_f/f_tieptheo.png (70%, ROI 1050,530,1165,680) -> Hoãn 0.4s
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👁️ [Bước 5.7] Quét & tap 'card_f/f_tieptheo.png' (70%) ➔ Hoãn 0.4s...")
        while not self._should_stop_card_D():
            tt1_x, tt1_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_tieptheo.png", threshold=0.70, region=(1050, 530, 1165, 680))
            if tt1_x is not None and tt1_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {tt1_x} {tt1_y}"])
                time.sleep(0.4)
                break
            time.sleep(0.4)

        # 5.8: Quét & Tap card_d/40npc/d_vaotran.png (75%, ROI 275,540,980,670) -> Hoãn 0.4s
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👁️ [Bước 5.8] Quét & tap 'card_d/40npc/d_vaotran.png' (75%) ➔ Hoãn 0.4s...")
        while not self._should_stop_card_D():
            vt_x, vt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/40npc/d_vaotran.png", threshold=0.75, region=(275, 540, 980, 670))
            if vt_x is not None and vt_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {vt_x} {vt_y}"])
                time.sleep(0.4)
                break
            time.sleep(0.4)

        # 5.9: Quét & Tap card_f/f_tieptheo.png (70%, ROI 1050,530,1165,680) liên tục mỗi 0.4s cho tới khi mất hẳn
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👉 [Bước 5.9] Quét & tap 'card_f/f_tieptheo.png' (70%) cho tới khi mất hoàn toàn...")
        while not self._should_stop_card_D():
            tt2_x, tt2_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_tieptheo.png", threshold=0.70, region=(1050, 530, 1165, 680))
            if tt2_x is not None and tt2_y is not None:
                while not self._should_stop_card_D():
                    tt_curr_x, tt_curr_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_tieptheo.png", threshold=0.70, region=(1050, 530, 1165, 680))
                    if tt_curr_x is None or tt_curr_y is None: break
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {tt_curr_x} {tt_curr_y}"])
                    time.sleep(0.4)
                break
            time.sleep(0.4)

        # BƯỚC 6 (Vòng lặp đánh Lôi Đài 38 lượt trận - Lượt 1 -> 38):
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "🚀 [40 NPC - Auto - Bước 6] Bắt đầu Vòng lặp đánh Lôi Đài 38 lượt...")
        has_seen_d35 = False
        auto_tapped_d35 = False

        for loidai_round in range(1, 39):
            if self._should_stop_card_D(): return

            # 6.1: Quét (không tap) f_vaotran.png (80%, ROI 1215,0,1280,45) mỗi 1.0s cho đến khi thấy
            self.after(0, self.log_info, f"🔄 [40 NPC - Auto - Lượt {loidai_round}/38 - Bước 6.1] Quét (không tap) 'card_f/f_vaotran.png' (80%) mỗi 1.0s...")
            while not self._should_stop_card_D():
                vt_chk_x, vt_chk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_vaotran.png", threshold=0.80, region=(1215, 0, 1280, 45))
                if vt_chk_x is not None and vt_chk_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_f/f_vaotran.png' tại ({vt_chk_x}, {vt_chk_y})!")
                    break
                time.sleep(1.0)

            # 6.2: Quét & Tap d_xacdinh.png (80%, ROI 275,540,980,670). Chưa thấy d_35: Hoãn 5.0s. Đã thấy d_35: Hoãn 0.5s.
            if self._should_stop_card_D(): return
            self.after(0, self.log_info, f"👁️ [40 NPC - Auto - Lượt {loidai_round}/38 - Bước 6.2] Quét & Tap nút Xác Định 'card_d/40npc/d_xacdinh.png' (80%)...")
            xd_x, xd_y = None, None
            while not self._should_stop_card_D():
                xd_x, xd_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/40npc/d_xacdinh.png", threshold=0.80, region=(275, 540, 980, 670))
                if xd_x is not None and xd_y is not None:
                    self.after(0, self.log_info, f"🎯 Tap 'd_xacdinh.png' tại ({xd_x}, {xd_y})!")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xd_x} {xd_y}"])
                    if has_seen_d35:
                        self.after(0, self.log_info, "⚡ [Đã thấy d_35] ➔ Hoãn 0.5s...")
                        time.sleep(0.5)
                    else:
                        self.after(0, self.log_info, "⏳ [Chưa thấy d_35] ➔ Hoãn 5.0s...")
                        for _ in range(5):
                            if self._should_stop_card_D(): return
                            time.sleep(1.0)
                    break
                time.sleep(0.5)

            # 6.3 (Kiểm tra mốc d_35.png):
            if self._should_stop_card_D(): return
            found_d35_this_round = False
            if has_seen_d35:
                self.after(0, self.log_info, "⚡ [Bước 6.3] Đã từng thấy d_35.png ở lượt trước ➔ BỎ QUA QUÉT d_35.png, nhảy thẳng sang 6.4!")
                found_d35_this_round = True
            else:
                self.after(0, self.log_info, "👁️ [Bước 6.3] Quét (không tap) 'card_d/40npc/d_35.png' (80%, ROI 1020,265,1125,295) mỗi 1.0s (tối đa 5 lần)...")
                for _ in range(5):
                    if self._should_stop_card_D(): break
                    d35_x, d35_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/40npc/d_35.png", threshold=0.80, region=(1020, 265, 1125, 295))
                    if d35_x is not None and d35_y is not None:
                        found_d35_this_round = True
                        has_seen_d35 = True
                        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_d/40npc/d_35.png' tại ({d35_x}, {d35_y})!")
                        break
                    time.sleep(1.0)

            # 6.4 (Phân nhánh Buff Skill):
            if self._should_stop_card_D(): return
            if found_d35_this_round or has_seen_d35:
                if not auto_tapped_d35:
                    self.after(0, self.log_info, "🔴 Lần đầu tiên thấy d_35.png ➔ Tap 1 LẦN duy nhất nút Auto 'login_auto.png' (85%, ROI 0,100,240,190) ➔ Hoãn 0.3s...")
                    auto_x, auto_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_auto.png", threshold=0.85, region=(0, 100, 240, 190))
                    if auto_x is not None and auto_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {auto_x} {auto_y}"])
                    time.sleep(0.3)
                    auto_tapped_d35 = True
                else:
                    self.after(0, self.log_info, "⚡ Các lượt sau d_35 ➔ Bỏ qua tap nút Auto!")

                # Kích hoạt Buff Skill (3 HP / 1 SP)
                self._execute_buff_skill_cycle(dnconsole_path, tab_index, log_tag="40 NPC")
            else:
                self.after(0, self.log_info, "🔴 Không thấy d_35.png (sau 5 lần) ➔ Quay lại Bước 6.1 cho lượt kế tiếp.")

    elif selected_chien_dau == "Click":
        # =========================================================================
        # 📌 QUY TRÌNH 2: CHẾ ĐỘ MENU: CLICK (3 BƯỚC THỰC THI)
        # =========================================================================
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "🚀 [40 NPC - Click] Bắt đầu Quy Trình 2: Chế độ Click...")

        # BƯỚC 1 (Tìm trận): Tap liên tục (1240, 605) mỗi 0.4s (tối đa 20 lần) tìm d_chien.png (80%, ROI 280,490,1280,720)
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👉 [40 NPC - Click - Bước 1] Tap liên tục (1240, 605) mỗi 0.4s (tối đa 20 lần) tìm ảnh 'card_d/40npc/d_chien.png' (80%)...")
        for retry in range(20):
            if self._should_stop_card_D(): return
            ch_x, ch_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/40npc/d_chien.png", threshold=0.80, region=(280, 490, 1280, 720))
            if ch_x is not None and ch_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'card_d/40npc/d_chien.png' tại ({ch_x}, {ch_y})! Dừng click.")
                break
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 605"])
            time.sleep(0.4)

        # BƯỚC 2 (Chọn trận): Tap (1135, 565) -> Hoãn 0.4s
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👉 [40 NPC - Click - Bước 2] Tap (1135, 565) chọn trận ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1135 565"])
        time.sleep(0.4)

        # BƯỚC 3 (Vòng lặp 38 lượt trận - Lượt 1 -> 38):
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "🚀 [40 NPC - Click - Bước 3] Bắt đầu Vòng lặp 38 lượt trận...")
        has_seen_d35_click = False
        auto_tapped_d35_click = False

        for loidai_round in range(1, 39):
            if self._should_stop_card_D(): return

            # 3.1: Quét (không tap) f_vaotran.png (80%, ROI 1215,0,1280,45) mỗi 1.0s cho tới khi thấy
            self.after(0, self.log_info, f"🔄 [40 NPC - Click - Lượt {loidai_round}/38 - Bước 3.1] Quét (không tap) 'card_f/f_vaotran.png' (80%) mỗi 1.0s...")
            while not self._should_stop_card_D():
                vt_chk_x, vt_chk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_vaotran.png", threshold=0.80, region=(1215, 0, 1280, 45))
                if vt_chk_x is not None and vt_chk_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_f/f_vaotran.png' tại ({vt_chk_x}, {vt_chk_y})!")
                    break
                time.sleep(1.0)

            # 3.2: Quét & Tap d_xacdinh.png (80%, ROI 275,540,980,670). Chưa thấy d_35: Hoãn 5.0s. Đã thấy d_35: Hoãn 0.5s.
            if self._should_stop_card_D(): return
            self.after(0, self.log_info, f"👁️ [40 NPC - Click - Lượt {loidai_round}/38 - Bước 3.2] Quét & Tap nút Xác Định 'card_d/40npc/d_xacdinh.png' (80%)...")
            xd_x, xd_y = None, None
            while not self._should_stop_card_D():
                xd_x, xd_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/40npc/d_xacdinh.png", threshold=0.80, region=(275, 540, 980, 670))
                if xd_x is not None and xd_y is not None:
                    self.after(0, self.log_info, f"🎯 Tap 'd_xacdinh.png' tại ({xd_x}, {xd_y})!")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xd_x} {xd_y}"])
                    if has_seen_d35_click:
                        self.after(0, self.log_info, "⚡ [Đã thấy d_35] ➔ Hoãn 0.5s...")
                        time.sleep(0.5)
                    else:
                        self.after(0, self.log_info, "⏳ [Chưa thấy d_35] ➔ Hoãn 5.0s...")
                        for _ in range(5):
                            if self._should_stop_card_D(): return
                            time.sleep(1.0)
                    break
                time.sleep(0.5)

            # 3.3 (Kiểm tra mốc d_35.png):
            if self._should_stop_card_D(): return
            found_d35_this_round = False
            if has_seen_d35_click:
                self.after(0, self.log_info, "⚡ [Bước 3.3] Đã từng thấy d_35.png ở lượt trước ➔ BỎ QUA QUÉT d_35.png, nhảy thẳng sang 3.4!")
                found_d35_this_round = True
            else:
                self.after(0, self.log_info, "👁️ [Bước 3.3] Quét (không tap) 'card_d/40npc/d_35.png' (80%, ROI 1020,265,1125,295) mỗi 1.0s (tối đa 5 lần)...")
                for _ in range(5):
                    if self._should_stop_card_D(): break
                    d35_x, d35_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/40npc/d_35.png", threshold=0.80, region=(1020, 265, 1125, 295))
                    if d35_x is not None and d35_y is not None:
                        found_d35_this_round = True
                        has_seen_d35_click = True
                        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_d/40npc/d_35.png' tại ({d35_x}, {d35_y})!")
                        break
                    time.sleep(1.0)

            # 3.4 (Phân nhánh Buff Skill):
            if self._should_stop_card_D(): return
            if found_d35_this_round or has_seen_d35_click:
                if not auto_tapped_d35_click:
                    self.after(0, self.log_info, "🔴 Lần đầu tiên thấy d_35.png ➔ Tap 1 LẦN duy nhất nút Auto 'login_auto.png' (85%, ROI 0,100,240,190) ➔ Hoãn 0.3s...")
                    auto_x, auto_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_auto.png", threshold=0.85, region=(0, 100, 240, 190))
                    if auto_x is not None and auto_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {auto_x} {auto_y}"])
                    time.sleep(0.3)
                    auto_tapped_d35_click = True
                else:
                    self.after(0, self.log_info, "⚡ Các lượt sau d_35 ➔ Bỏ qua tap nút Auto!")

                # Kích hoạt Buff Skill (3 HP / 1 SP)
                self._execute_buff_skill_cycle(dnconsole_path, tab_index, log_tag="40 NPC")
            else:
                self.after(0, self.log_info, "🔴 Không thấy d_35.png (sau 5 lần) ➔ Quay lại Bước 3.1 cho lượt kế tiếp.")


# =========================================================================
# PHẦN 6: QUY TRÌNH THỰC THI SỰ KIỆN NHỊ KIỀU (MỐC TRỆT - 10 & 11 - 14)
# =========================================================================
def run_nhi_kieu_tang_tret_10(self, dnconsole_path: str, tab_index: str, loop_count: int = 10, mode_name: str = "Trệt - 10", run_stages_1_to_3: bool = True, only_stages_1_to_3: bool = False, check_until_dinh: bool = False, card_name: str = "40 NPC"):
    """THAO TÁC CHI TIẾT MỐC ĐÀI NHỊ KIỀU: Trệt - 10 & 11 - 14"""
    def should_stop() -> bool:
        return self._should_stop_card_D()

    def _tap_f_tieptheo_until_lost(tap_interval: float = 0.5, delay_after: float = 0.0):
        """Tap f_tieptheo.png (ROI: 1050, 530, 1165, 680, 80%) mỗi tap_interval đến khi mất hẳn ➔ Hoãn delay_after"""
        while not should_stop():
            tt_x, tt_y = self._find_template_on_screen(
                dnconsole_path, tab_index, "card_f/f_tieptheo.png",
                threshold=0.80, region=(1050, 530, 1165, 680)
            )
            if tt_x is not None and tt_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {tt_x} {tt_y}"])
                time.sleep(tap_interval)
            else:
                break
        if delay_after > 0:
            if delay_after >= 1.0:
                for _ in range(int(delay_after)):
                    if should_stop(): return
                    time.sleep(1.0)
                rem = delay_after - int(delay_after)
                if rem > 0:
                    time.sleep(rem)
            else:
                time.sleep(delay_after)

    def _wait_for_f_vaotran():
        """Quét (không tap) card_f/f_vaotran.png (ROI: 1215, 0, 1280, 45, 80%) cho tới khi thấy"""
        self.after(0, self.log_info, "👁️ Quét (không tap) 'card_f/f_vaotran.png' (ROI 1215,0,1280,45)...")
        while not should_stop():
            vt_x, vt_y = self._find_template_on_screen(
                dnconsole_path, tab_index, "card_f/f_vaotran.png",
                threshold=0.80, region=(1215, 0, 1280, 45)
            )
            if vt_x is not None and vt_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_f/f_vaotran.png' tại ({vt_x}, {vt_y})!")
                break
            time.sleep(1.0)

    def _swipe_dpad_direction(direction: str, duration_ms: int):
        """Vuốt D-Pad theo hướng chỉ định qua ADB swipe"""
        swipe_coords = {
            "UP_RIGHT": (640, 360, 890, 110),
            "UP_LEFT": (640, 360, 390, 110),
            "DOWN_RIGHT": (640, 360, 890, 610),
        }
        coords = swipe_coords.get(direction, (640, 360, 890, 110))
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input swipe {coords[0]} {coords[1]} {coords[2]} {coords[3]} {duration_ms}"])

    def _swipe_dpad_until_tieptheo(direction: str, timeout_sec: float = 8.0) -> bool:
        """Vuốt D-Pad giữ 3 giây (3000ms) lặp lại sau 0.2s cho tới khi thấy f_tieptheo.png (ROI 1050,530,1165,680) hoặc hết timeout"""
        start_t = time.time()
        while time.time() - start_t < timeout_sec:
            if should_stop(): return False
            _swipe_dpad_direction(direction, 3000)
            tt_x, tt_y = self._find_template_on_screen(
                dnconsole_path, tab_index, "card_f/f_tieptheo.png",
                threshold=0.80, region=(1050, 530, 1165, 680)
            )
            if tt_x is not None and tt_y is not None:
                return True
            time.sleep(0.2)
        return False

    # -------------------------------------------------------------
    # THỰC THI GIAI ĐOẠN 1 -> 3 (NẾU MỐC LÀ "TRỆT - 10")
    # -------------------------------------------------------------
    if run_stages_1_to_3:
        # === GIAI ĐOẠN 1 ===
        self.after(0, self.log_info, f"🚀 [{mode_name}] Bắt đầu Giai Đoạn 1...")
        # 1.1: Quét & Tap card_d/nhikieu/d_buoc1.png (Threshold 80%, Toàn màn hình)
        self.after(0, self.log_info, f"👁️ [{mode_name} - Bước 1.1] Quét 'card_d/nhikieu/d_buoc1.png' (80%, Toàn màn hình)...")
        while not should_stop():
            b1_x, b1_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/nhikieu/d_buoc1.png", threshold=0.80)
            if b1_x is not None and b1_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'd_buoc1.png' tại ({b1_x}, {b1_y})! Tap lần 1...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b1_x} {b1_y}"])
                break
            time.sleep(1.0)
        if should_stop(): return

        # 1.1b: Quét card_f/f_tieptheo.png (ROI: 1050, 530, 1165, 680, Threshold 80%) đến khi xuất hiện
        self.after(0, self.log_info, f"👁️ [{mode_name} - Bước 1.1b] Quét 'f_tieptheo.png' (ROI 1050,530,1165,680)...")
        while not should_stop():
            tt_x, tt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_tieptheo.png", threshold=0.80, region=(1050, 530, 1165, 680))
            if tt_x is not None and tt_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'f_tieptheo.png' tại ({tt_x}, {tt_y})!")
                break
            time.sleep(0.5)
        if should_stop(): return

        # 1.2: Tap f_tieptheo.png mỗi 0.5s đến khi mất ➔ Hoãn 5.0s
        self.after(0, self.log_info, f"👉 [{mode_name} - Bước 1.2] Tap 'f_tieptheo.png' mỗi 0.5s đến khi mất ➔ Hoãn 5.0s...")
        _tap_f_tieptheo_until_lost(tap_interval=0.5, delay_after=5.0)
        if should_stop(): return

        # 1.3: Quét (không tap) card_f/f_vaotran.png (ROI: 1215, 0, 1280, 45, Threshold 80%) cho tới khi thấy
        self.after(0, self.log_info, f"👁️ [{mode_name} - Bước 1.3] Quét (không tap) 'f_vaotran.png'...")
        _wait_for_f_vaotran()
        if should_stop(): return

        # 1.4: Tap f_tieptheo.png mỗi 0.5s đến khi mất ➔ Hoãn 0.5s
        self.after(0, self.log_info, f"👉 [{mode_name} - Bước 1.4] Tap 'f_tieptheo.png' mỗi 0.5s đến khi mất ➔ Hoãn 0.5s...")
        _tap_f_tieptheo_until_lost(tap_interval=0.5, delay_after=0.5)
        if should_stop(): return

        # 1.5: Quét & Tap card_d/nhikieu/d_buoc1.png (Threshold 80%, Toàn màn hình) lần 2 ➔ Hoãn 2.0s
        self.after(0, self.log_info, f"👁️ [{mode_name} - Bước 1.5] Quét 'd_buoc1.png' lần 2 (Toàn màn hình) ➔ Hoãn 2.0s...")
        while not should_stop():
            b1_x2, b1_y2 = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/nhikieu/d_buoc1.png", threshold=0.80)
            if b1_x2 is not None and b1_y2 is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b1_x2} {b1_y2}"])
                time.sleep(2.0)
                break
            time.sleep(1.0)
        if should_stop(): return

        # === GIAI ĐOẠN 2 ===
        self.after(0, self.log_info, f"🚀 [{mode_name}] Bắt đầu Giai Đoạn 2...")
        # 2.1: Quét & Tap card_d/nhikieu/d_buoc2.png (Threshold 75%, Toàn màn hình)
        self.after(0, self.log_info, f"👁️ [{mode_name} - Bước 2.1] Quét 'd_buoc2.png' (75%, Toàn màn hình)...")
        while not should_stop():
            b2_x, b2_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/nhikieu/d_buoc2.png", threshold=0.75)
            if b2_x is not None and b2_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'd_buoc2.png' tại ({b2_x}, {b2_y})! Tap lần 1...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b2_x} {b2_y}"])
                break
            time.sleep(1.0)
        if should_stop(): return

        # 2.1b: Quét f_tieptheo.png (ROI: 1050, 530, 1165, 680, Threshold 80%) đến khi thấy
        self.after(0, self.log_info, f"👁️ [{mode_name} - Bước 2.1b] Quét 'f_tieptheo.png' (ROI 1050,530,1165,680)...")
        while not should_stop():
            tt_x, tt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_tieptheo.png", threshold=0.80, region=(1050, 530, 1165, 680))
            if tt_x is not None and tt_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'f_tieptheo.png' tại ({tt_x}, {tt_y})!")
                break
            time.sleep(0.5)
        if should_stop(): return

        # 2.2: Tap f_tieptheo.png mỗi 0.5s đến khi mất ➔ Hoãn 5.0s
        self.after(0, self.log_info, f"👉 [{mode_name} - Bước 2.2] Tap 'f_tieptheo.png' mỗi 0.5s đến khi mất ➔ Hoãn 5.0s...")
        _tap_f_tieptheo_until_lost(tap_interval=0.5, delay_after=5.0)
        if should_stop(): return

        # 2.3: Quét (không tap) f_vaotran.png (ROI: 1215, 0, 1280, 45, Threshold 80%)
        self.after(0, self.log_info, f"👁️ [{mode_name} - Bước 2.3] Quét (không tap) 'f_vaotran.png'...")
        _wait_for_f_vaotran()
        if should_stop(): return

        # 2.4: Tap f_tieptheo.png mỗi 0.5s đến khi mất ➔ Hoãn 0.5s
        self.after(0, self.log_info, f"👉 [{mode_name} - Bước 2.4] Tap 'f_tieptheo.png' mỗi 0.5s đến khi mất ➔ Hoãn 0.5s...")
        _tap_f_tieptheo_until_lost(tap_interval=0.5, delay_after=0.5)
        if should_stop(): return

        # 2.5: Tap card_d/nhikieu/d_buoc2.png (75%, Toàn màn hình) mỗi 0.5s đến khi mất ➔ Hoãn 2.0s
        self.after(0, self.log_info, f"👉 [{mode_name} - Bước 2.5] Tap 'd_buoc2.png' mỗi 0.5s đến khi mất ➔ Hoãn 2.0s...")
        while not should_stop():
            b2_curr_x, b2_curr_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/nhikieu/d_buoc2.png", threshold=0.75)
            if b2_curr_x is not None and b2_curr_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b2_curr_x} {b2_curr_y}"])
                time.sleep(0.5)
            else:
                self.after(0, self.log_info, "✅ 'd_buoc2.png' đã mất! ➔ Hoãn 2.0s...")
                time.sleep(2.0)
                break
        if should_stop(): return

        # === GIAI ĐOẠN 3 ===
        self.after(0, self.log_info, f"🚀 [{mode_name}] Bắt đầu Giai Đoạn 3...")
        # 3.1: Tap cố định (225, 220) ➔ Hoãn 2.0s
        self.after(0, self.log_info, f"👉 [{mode_name} - Bước 3.1] Tap (225, 220) ➔ Hoãn 2.0s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 225 220"])
        time.sleep(2.0)
        if should_stop(): return

        # 3.2: Tap f_tieptheo.png mỗi 0.5s đến khi mất ➔ Hoãn 5.0s
        self.after(0, self.log_info, f"👉 [{mode_name} - Bước 3.2] Tap 'f_tieptheo.png' mỗi 0.5s đến khi mất ➔ Hoãn 5.0s...")
        _tap_f_tieptheo_until_lost(tap_interval=0.5, delay_after=5.0)
        if should_stop(): return

        # 3.3: Quét (không tap) f_vaotran.png (ROI: 1215, 0, 1280, 45, Threshold 80%)
        self.after(0, self.log_info, f"👁️ [{mode_name} - Bước 3.3] Quét (không tap) 'f_vaotran.png'...")
        _wait_for_f_vaotran()
        if should_stop(): return

        # 3.4: Tap f_tieptheo.png mỗi 0.5s đến khi mất ➔ Hoãn 0.5s
        self.after(0, self.log_info, f"👉 [{mode_name} - Bước 3.4] Tap 'f_tieptheo.png' mỗi 0.5s đến khi mất ➔ Hoãn 0.5s...")
        _tap_f_tieptheo_until_lost(tap_interval=0.5, delay_after=0.5)
        if should_stop(): return

        # 3.5: Tap nút Auto login_auto.png (ROI: 0, 100, 240, 190, 85%) ➔ Hoãn 0.3s
        self.after(0, self.log_info, f"👉 [{mode_name} - Bước 3.5] Quét & Tap nút Auto 'login_auto.png' (ROI 0,100,240,190) ➔ Hoãn 0.3s...")
        auto_x, auto_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_auto.png", threshold=0.85, region=(0, 100, 240, 190))
        if auto_x is not None and auto_y is not None:
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {auto_x} {auto_y}"])
        time.sleep(0.3)
        if should_stop(): return

        # 3.6: Tap d_buoc3.png (80%, Toàn màn hình) mỗi 0.5s đến khi mất ➔ Hoãn 2.0s
        self.after(0, self.log_info, f"👉 [{mode_name} - Bước 3.6] Tap 'd_buoc3.png' (Toàn màn hình) mỗi 0.5s đến khi mất ➔ Hoãn 2.0s...")
        while not should_stop():
            b3_x, b3_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/nhikieu/d_buoc3.png", threshold=0.80)
            if b3_x is not None and b3_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b3_x} {b3_y}"])
                time.sleep(0.5)
            else:
                self.after(0, self.log_info, "✅ 'd_buoc3.png' đã mất! ➔ Hoãn 2.0s...")
                time.sleep(2.0)
                break
    else:
        self.after(0, self.log_info, f"ℹ️ [{mode_name}] Bỏ qua Giai đoạn 1, 2, 3 ➔ Bắt đầu Vòng lặp Giai đoạn 4 ➔ 7...")

    # --- LẶP GIAI ĐOẠN 4, 5, 6, 7 ---
    loop_idx = 0
    while not should_stop():
        loop_idx += 1
        self.after(0, self.log_info, f"🔄 [{mode_name}] Khởi chạy Vòng lặp Giai Đoạn 4 ➔ 7 (Lượt {loop_idx})...")

        # === GIAI ĐOẠN 4 ===
        if should_stop(): return
        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 4.1: Vuốt UP_RIGHT tìm f_tieptheo.png...")
        _swipe_dpad_until_tieptheo("UP_RIGHT", timeout_sec=8.0)
        
        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 4.2: Tap f_tieptheo.png mỗi 0.5s đến khi mất...")
        _tap_f_tieptheo_until_lost(tap_interval=0.5, delay_after=0.0)

        # Buff Skill 3 HP / 1 SP
        self.after(0, self.log_info, f"🔄 [{mode_name} - Lượt {loop_idx}] Kích hoạt Chuỗi Buff 3 HP / 1 SP...")
        self._execute_buff_skill_cycle(dnconsole_path, tab_index, log_tag=mode_name)

        if should_stop(): return
        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 4.3: Quét f_vaotran.png...")
        _wait_for_f_vaotran()

        # 4.4: Tap f_tieptheo.png mỗi 0.3s đến khi mất ➔ Hoãn 0.5s
        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 4.4: Tap f_tieptheo.png mỗi 0.3s đến khi mất ➔ Hoãn 0.5s...")
        _tap_f_tieptheo_until_lost(tap_interval=0.3, delay_after=0.5)

        # === GIAI ĐOẠN 5 ===
        if should_stop(): return
        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 5.1: Vuốt UP_RIGHT trong 1.0s...")
        _swipe_dpad_direction("UP_RIGHT", 1000)
        time.sleep(0.5)

        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 5.2: Vuốt UP_LEFT tìm f_tieptheo.png...")
        _swipe_dpad_until_tieptheo("UP_LEFT", timeout_sec=8.0)

        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 5.3: Tap f_tieptheo.png mỗi 0.5s đến khi mất...")
        _tap_f_tieptheo_until_lost(tap_interval=0.5, delay_after=0.0)

        # Buff Skill 3 HP / 1 SP
        self.after(0, self.log_info, f"🔄 [{mode_name} - Lượt {loop_idx}] Kích hoạt Chuỗi Buff 3 HP / 1 SP...")
        self._execute_buff_skill_cycle(dnconsole_path, tab_index, log_tag=mode_name)

        if should_stop(): return
        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 5.4: Quét f_vaotran.png...")
        _wait_for_f_vaotran()

        # 5.5: Tap f_tieptheo.png mỗi 0.3s đến khi mất ➔ Hoãn 0.5s
        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 5.5: Tap f_tieptheo.png mỗi 0.3s đến khi mất ➔ Hoãn 0.5s...")
        _tap_f_tieptheo_until_lost(tap_interval=0.3, delay_after=0.5)

        # === GIAI ĐOẠN 6 ===
        if should_stop(): return
        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 6.1: Vuốt UP_LEFT trong 1.0s...")
        _swipe_dpad_direction("UP_LEFT", 1000)
        time.sleep(0.5)

        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 6.2: Vuốt UP_RIGHT tìm f_tieptheo.png...")
        _swipe_dpad_until_tieptheo("UP_RIGHT", timeout_sec=8.0)

        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 6.3: Tap f_tieptheo.png mỗi 0.5s đến khi mất...")
        _tap_f_tieptheo_until_lost(tap_interval=0.5, delay_after=0.0)

        # Buff Skill 3 HP / 1 SP
        self.after(0, self.log_info, f"🔄 [{mode_name} - Lượt {loop_idx}] Kích hoạt Chuỗi Buff 3 HP / 1 SP...")
        self._execute_buff_skill_cycle(dnconsole_path, tab_index, log_tag=mode_name)

        if should_stop(): return
        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 6.4: Quét f_vaotran.png...")
        _wait_for_f_vaotran()

        # 6.5: Tap f_tieptheo.png mỗi 0.3s đến khi mất ➔ Hoãn 0.5s
        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 6.5: Tap f_tieptheo.png mỗi 0.3s đến khi mất ➔ Hoãn 0.5s...")
        _tap_f_tieptheo_until_lost(tap_interval=0.3, delay_after=0.5)

        # === GIAI ĐOẠN 7: HOÀN THÀNH ===
        if should_stop(): return
        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 7.1: Vuốt UP_RIGHT trong 2.0s...")
        _swipe_dpad_direction("UP_RIGHT", 2000)
        time.sleep(0.5)

        self.after(0, self.log_info, f"👉 [{mode_name} - Lượt {loop_idx}] Giai Đoạn 7.2: Vuốt DOWN_RIGHT trong 1.0s...")
        _swipe_dpad_direction("DOWN_RIGHT", 1000)
        time.sleep(0.5)

        # 7.3: Kiểm tra hoàn thành theo mốc tầng
        self.after(0, self.log_info, f"👁️ [{mode_name} - Lượt {loop_idx}] Giai Đoạn 7.3: Quét kiểm tra hoàn thành...")
        target_img = "card_d/nhikieu/d_dinh.png" if mode_name in ["Trệt - 10", "Trệt"] else "card_d/nhikieu/d_thap14.png"
        
        found_finish = False
        start_chk = time.time()
        while time.time() - start_chk < 3.0:
            if should_stop(): return
            fin_x, fin_y = self._find_template_on_screen(
                dnconsole_path, tab_index, target_img,
                threshold=0.80, region=(1060, 0, 1280, 40)
            )
            if fin_x is not None and fin_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện '{target_img}' tại ({fin_x}, {fin_y})! Hoàn thành dứt điểm mốc '{mode_name}'.")
                found_finish = True
                break
            time.sleep(0.5)

        if found_finish:
            self.after(0, self.log_info, f"✅ [NHỊ KIỀU] Đã hoàn thành mốc '{mode_name}' thành công!")
            break


def run_nhi_kieu_tang(self, dnconsole_path: str, tab_index: str, selected_tang: str, card_name: str = "40 NPC"):
    """THAO TÁC: TẦNG / ĐÀI (NHỊ KIỀU)"""
    if self._should_stop_card_D(): return

    prefix_tag = "[40 NPC / 2K - Tầng]"
    self.after(0, self.log_info, f"🚀 {prefix_tag} Khởi chạy ô Tầng (Mốc: '{selected_tang}')...")

    if selected_tang in ["Trệt - 10", "Trệt"]:
        self._run_nhi_kieu_tang_tret_10(dnconsole_path, tab_index, loop_count=0, mode_name="Trệt - 10", run_stages_1_to_3=True, only_stages_1_to_3=False, check_until_dinh=True, card_name=card_name)
    elif selected_tang == "11 - 14":
        self._run_nhi_kieu_tang_tret_10(dnconsole_path, tab_index, loop_count=0, mode_name="11 - 14", run_stages_1_to_3=False, only_stages_1_to_3=False, check_until_dinh=True, card_name=card_name)
    else:
        self.after(0, self.log_info, f"ℹ️ Mốc '{selected_tang}' đang được cập nhật thao tác chi tiết...")


# =========================================================================
# PHẦN 7: BỘ ĐIỀU PHỐI TỔNG CARD D (40 NPC / 2K)
# =========================================================================
def execute_card_D_40_npc(self, dnconsole_path: str, tab_name: str, tab_index: str):
    """Thực thi Card 5: 40 NPC / 2K (D)"""
    if self._should_stop_card_D():
        self.after(0, self.log_info, "ℹ️ [5/6: 40 NPC / 2K] Công tắc ON/OFF đang TẮT -> Bỏ qua.")
        return

    checked = [
        ("Tổ Đội", self.var_D2),
        ("40 NPC", self.var_D3),
        ("Nhị Kiều", self.var_D4)
    ]
    active_items = [(name, var) for name, var in checked if var.get()]
    if not active_items:
        self.after(0, self.log_info, "ℹ️ [5/6: 40 NPC / 2K] Công tắc ON nhưng không có mục nào được chọn -> Tắt công tắc & Bỏ qua.")
        self.after(0, lambda: self.var_switch_D.set(False))
        self.after(0, self.save_config)
        return

    selected_team_char = self.combo_D_team_char.get() if hasattr(self, 'combo_D_team_char') else "Xuất Chiến"
    selected_chien_dau = self.combo_D_chien_dau.get() if hasattr(self, 'combo_D_chien_dau') else "Auto"
    selected_tang = self.combo_D_tang.get() if hasattr(self, 'combo_D_tang') else "Trệt - 10"

    info_details = []
    if self.var_D2.get():
        info_details.append(f"Tổ Đội (Vị trí: '{selected_team_char}')")
    if self.var_D3.get():
        info_details.append(f"40 NPC (Chế độ: '{selected_chien_dau}')")
    if self.var_D4.get():
        info_details.append(f"Nhị Kiều (Mốc: '{selected_tang}')")

    self.after(0, self.log_info, f"▶️ [5/6: 40 NPC / 2K] Đang thực thi {len(info_details)} mục đã chọn: {', '.join(info_details)}...")

    # THAO TÁC 1: TỔ ĐỘI & ĐỔI VỊ TRÍ TƯỚNG (KHI Ô VAR_D2 ĐƯỢC TÍCH)
    if self.var_D2.get():
        self.after(0, self.log_info, f"🚀 [40 NPC / 2K - 1. Tổ Đội] Khởi chạy ô Tổ Đội (Vị trí: '{selected_team_char}')...")
        self._run_40_npc_team_and_char_position(dnconsole_path, tab_index, selected_team_char)
        self._execute_card_E_for_mode(dnconsole_path, tab_name, tab_index, mode=1)
    else:
        self.after(0, self.log_info, "ℹ️ [40 NPC / 2K - 1. Tổ Đội] Ô 'Tổ Đội' KHÔNG được tích ➔ Bỏ qua.")

    # THAO TÁC 2: 40 NPC (KHI Ô VAR_D3 ĐƯỢC TÍCH)
    if self.var_D3.get():
        self.after(0, self.log_info, f"🚀 [40 NPC / 2K - 2. 40 NPC] Khởi chạy ô 40 NPC (Chế độ: '{selected_chien_dau}')...")
        self._run_40_npc_su_kien_tang(dnconsole_path, tab_index, "Cố Định", selected_team_char, selected_chien_dau)
    else:
        self.after(0, self.log_info, "ℹ️ [40 NPC / 2K - 2. 40 NPC] Ô '40 NPC' KHÔNG được tích ➔ Bỏ qua.")

    # THAO TÁC 3: NHỊ KIỀU (KHI Ô VAR_D4 ĐƯỢC TÍCH)
    if self.var_D4.get():
        self.after(0, self.log_info, f"🚀 [40 NPC / 2K - 3. Nhị Kiều] Khởi chạy ô Nhị Kiều (Mốc: '{selected_tang}')...")
        self._run_nhi_kieu_tang(dnconsole_path, tab_index, selected_tang, card_name="40 NPC / 2K")
    else:
        self.after(0, self.log_info, "ℹ️ [40 NPC / 2K - 3. Nhị Kiều] Ô 'Nhị Kiều' KHÔNG được tích ➔ Bỏ qua.")

    # Tự động tắt công tắc ON/OFF (False) & nhả ô Tạm Dừng sau khi hoàn thành, giữ nguyên các ô check
    self.after(0, lambda: self.var_switch_D.set(False))
    if hasattr(self, 'var_pause_D'):
        self.after(0, lambda: self.var_pause_D.set(False))
    self.after(0, self.save_config)
    self.after(0, self.log_info, "✅ [5/6: 40 NPC / 2K] Đã thực thi hoàn tất dứt điểm! (Đã tự động tắt công tắc ON/OFF & giữ nguyên các ô tích)")
