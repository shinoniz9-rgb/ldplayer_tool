# -*- coding: utf-8 -*-
"""
========================================================================================
🔒 [BẢN BACKUP THAM CHIẾU ĐỘC LẬP & KHÓA NGUYÊN BẢN]: CARD F (CẤU HÌNH CHIẾN ĐẤU / SKILL BUFF)
========================================================================================
Ngày tạo: 2026-09-02
Mục đích:
- Lưu trữ độc lập toàn bộ giao diện và logic thực thi ngầm của Card F (Chiến Đấu / Tự Động Buff Skill).
- Mã nguồn này đã được tối ưu hóa toàn bộ 100% vùng ROI và các ngưỡng nhận diện cho từng ảnh.
- Độc lập 100% với các chỉnh sửa phát sinh sau này trên file main.py.

========================================================================================
📌 BẢNG TRA CỨU TỌA ĐỘ VÙNG QUÉT ROI & NGƯỠNG THRESHOLD CARD F
========================================================================================
1. f_dung.png      : (640, 0, 1280, 145)    - Threshold: 0.80 (80%) [CHỈ QUÉT NHẬN DIỆN, KHÔNG TAP]
2. f_tieptheo.png : (1050, 530, 1165, 680) - Threshold: 0.80 (80%) [Quét nhanh 0.5s, nếu có tap hoãn 0.3s]
3. f_hp.png       : (640, 0, 1280, 145)    - Threshold: 0.85 (85%) [Tap chiêu ➔ Tap (905,515) ➔ 2x Auto ➔ Nghỉ 5s]
4. f_sp.png       : (640, 0, 1280, 145)    - Threshold: 0.85 (85%) [Tap chiêu ➔ Tap (905,515) ➔ 2x Auto ➔ Nghỉ 5s]
5. login_auto.png : (0, 100, 240, 190)     - Threshold: 0.85 (85%) [Tap 2 lần cách nhau 0.15s]
6. f_vaotran.png  : (1215, 0, 1280, 45)     - Threshold: 0.80 (80%) [CHỈ QUÉT NHẬN DIỆN trạng thái trận đấu]
========================================================================================
"""

import os
import time
import threading
import customtkinter as ctk

# =========================================================================
# PHẦN 1: MÃ NGUỒN GIAO DIỆN DESKTOP (GUI) CỦA CARD F
# =========================================================================
def build_card_F_ui(self, tab_combat):
    """
    Xây dựng giao diện Card F (Cấu Hình Chiến Đấu) trên Desktop GUI
    Đặt tại TAB 3: ⚔️ Cấu Hình Chiến Đấu
    """
    # ------------------- CARD F: CHIẾN ĐẤU (Đặt ở TAB 3: ⚔️ Cấu Hình Chiến Đấu) -------------------
    self.card_combat = ctk.CTkFrame(tab_combat, corner_radius=10)
    self.card_combat.pack(fill="both", expand=True, padx=6, pady=6)
    self.card_combat.grid_columnconfigure(0, weight=1)
    self.card_combat.grid_rowconfigure(0, weight=0)
    self.card_combat.grid_rowconfigure(1, weight=0)

    hdr_combat = ctk.CTkFrame(self.card_combat, fg_color="transparent")
    hdr_combat.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="ew")
    hdr_combat.grid_columnconfigure(0, weight=1)

    lbl_combat = ctk.CTkLabel(
        hdr_combat,
        text="CẤU HÌNH CHIẾN ĐẤU",
        font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
        text_color="#38BDF8"
    )
    lbl_combat.grid(row=0, column=0, sticky="w")

    # Hàng 1: [ ] Buff | ( Tắt Auto ) | [ Menu Dropdown 3 Chế Độ ]
    row_combat1 = ctk.CTkFrame(self.card_combat, fg_color="transparent")
    row_combat1.grid(row=1, column=0, padx=6, pady=6, sticky="ew")

    self.chk_buff = ctk.CTkCheckBox(
        row_combat1,
        text="Skill",
        variable=self.var_buff,
        command=self._on_skill_toggled,
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
        fg_color="#EA580C",
        hover_color="#C2410C",
        checkmark_color="#FFFFFF",
        text_color="#FFFFFF",
        checkbox_width=16,
        checkbox_height=16,
        border_width=2,
        corner_radius=5
    )
    self.chk_buff.pack(side="left", padx=(4, 0))

    lbl_sub_skill = ctk.CTkLabel(
        row_combat1,
        text="( Tắt Auto )",
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
        text_color="#9CA3AF"
    )
    lbl_sub_skill.pack(side="left", padx=(4, 0))

    buff_options = ["Buff HP", "Buff SP", "Buff 3HP / 1SP"]
    self.combo_buff = ctk.CTkOptionMenu(
        row_combat1,
        values=buff_options,
        font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
        dropdown_font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
        text_color="#FFFFFF",
        dropdown_text_color="#FFFFFF",
        height=25,
        width=140,
        dynamic_resizing=False,
        fg_color="#374151",
        button_color="#4B5563",
        button_hover_color="#6B7280",
        command=lambda choice: self._on_checkbox_toggled()
    )
    self.combo_buff.set(buff_options[0])
    self.combo_buff.pack(side="right", padx=(0, 4))

    self._update_buff_state()


# =========================================================================
# PHẦN 2: CÁC HÀM XỬ LÝ TRẠNG THÁI & LUỒNG THỰC THI NGẦM
# =========================================================================
def update_buff_state(self):
    """Cập nhật trạng thái ô dropdown Skill (luôn luôn mở sáng để chọn trước chế độ)"""
    if not hasattr(self, 'combo_buff'):
        return
    self.combo_buff.configure(state="normal", fg_color="#374151", button_color="#4B5563", button_hover_color="#6B7280", text_color="#FFFFFF")


def on_skill_toggled(self):
    """Callback riêng cho ô Skill (Tab Chiến Đấu): Bật/tắt menu dropdown Skill và kích hoạt chạy song song độc lập (Chỉ phụ thuộc nút Dừng tổng)"""
    self._update_buff_state()
    self.save_config()

    if self.var_buff.get():
        self.stop_requested = False
        tab_name, tab_index = self._get_selected_ld_info()
        if tab_index is None:
            self.log_error("Vui lòng chọn một Tab LDPlayer trước khi kích hoạt ô Skill!")
            return

        dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")
        if not os.path.exists(dnconsole_path):
            dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")

        if not os.path.exists(dnconsole_path):
            self.log_error(f"Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
            return

        choice = self.combo_buff.get() if hasattr(self, 'combo_buff') else "Buff HP"
        self.log_info(f"⚡ [SKILL] Ô Skill vừa tích BẬT ➔ Kích hoạt tiến trình Skill song song (Chế độ: {choice}) trên Tab: {tab_name} (Index: {tab_index})...")
        threading.Thread(target=self._run_skill_standalone, args=(dnconsole_path, tab_name, tab_index), daemon=True).start()
    else:
        self.log_info("🛑 [SKILL] Ô Skill vừa bỏ tích ➔ Đã ngắt tiến trình Skill song song!")


def run_skill_standalone(self, dnconsole_path: str, tab_name: str, tab_index: str):
    """Worker thread thực thi độc lập/song song cho ô Skill mà không ảnh hưởng tới các Card khác"""
    try:
        while self.var_buff.get() and not self.stop_requested:
            choice = self.combo_buff.get() if hasattr(self, 'combo_buff') else "Buff HP"
            if choice == "Buff HP":
                self._handle_skill_buff_hp(dnconsole_path, tab_name, tab_index)
            elif choice == "Buff SP":
                self._handle_skill_buff_sp(dnconsole_path, tab_name, tab_index)
            elif choice in ["Buff 3HP / SP", "Buff 3HP / 1SP"]:
                self._handle_skill_buff_3hp_1sp(dnconsole_path, tab_name, tab_index)
            else:
                self._handle_skill_buff_hp(dnconsole_path, tab_name, tab_index)

            time.sleep(0.1)

        if not self.stop_requested and not self.var_buff.get():
            self.after(0, self.log_info, "🛑 [SKILL] Đã dừng tiến trình Skill theo yêu cầu bỏ tích ô.")
    except Exception as e:
        self.after(0, self.log_error, f"❌ Lỗi luồng thực thi Skill song song: {str(e)}")


def tap_login_auto_twice(self, dnconsole_path: str, tab_index: str):
    """Quét và tap 2 lần cách nhau 0.15s ảnh card_top/login/login_auto.png (85%, ROI 0,100,240,190)"""
    for tap_idx in range(1, 3):
        if not self.var_buff.get() or self.stop_requested:
            break
        auto_x, auto_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_auto.png", threshold=0.85, region=(0, 100, 240, 190))
        if auto_x is not None and auto_y is not None:
            self.after(0, self.log_info, f"🎯 [SKILL] Mắt thần phát hiện 'login_auto.png' (85%) tại ({auto_x}, {auto_y}) ➔ Tap lần {tap_idx}/2...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {auto_x} {auto_y}"])
        else:
            self.after(0, self.log_warning, f"⚠️ [SKILL] Không tìm thấy 'login_auto.png' (85%) ở lần thử {tap_idx}/2")
        time.sleep(0.15)


def check_and_tap_f_tieptheo(self, dnconsole_path: str, tab_index: str):
    """
    Ngay khi thấy card_f/f_dung.png:
    Quét liên tục tìm ảnh card_f/f_tieptheo.png (80%) (nghỉ 0.25s/lần) trong vùng ROI (1050, 530, 1165, 680) trong 0.5s.
    Nếu thấy: tap vào ảnh card_f/f_tieptheo.png, hoãn 0.3s.
    Nếu không thấy: bỏ qua, chuyển sang Bước 2.
    """
    if not self.var_buff.get() or self.stop_requested: return
    self.after(0, self.log_info, "👁️ [SKILL] Quét tìm 'card_f/f_tieptheo.png' (80%, ROI 1050,530,1165,680) nghỉ 0.25s/lần trong 0.5s...")
    start_tt = time.time()
    while time.time() - start_tt < 0.5:
        if not self.var_buff.get() or self.stop_requested: return
        tt_x, tt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_tieptheo.png", threshold=0.80, region=(1050, 530, 1165, 680))
        if tt_x is not None and tt_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_f/f_tieptheo.png' tại ({tt_x}, {tt_y})! Tap click ➔ Hoãn 0.3s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {tt_x} {tt_y}"])
            time.sleep(0.3)
            break
        time.sleep(0.25)


def handle_skill_buff_hp(self, dnconsole_path: str, tab_name: str, tab_index: str):
    """
    Hành động 1 - Buff HP:
    1. Quét chờ xuất hiện: Quét tìm ảnh card_f/f_dung.png (80%, ROI 640,0,1280,145) (0.5s/lần) cho tới khi xuất hiện (CHỈ QUÉT KHÔNG TAP)
       - Ngay khi thấy ➔ Quét tìm ảnh card_f/f_tieptheo.png (80%, ROI 1050,530,1165,680) nghỉ 0.25s/lần trong 0.5s.
       - Nếu thấy: tap vào ảnh card_f/f_tieptheo.png, hoãn 0.3s ➔ sang Bước 2.
       - Nếu không thấy: chuyển tiếp sang Bước 2.
    2. Bước 2: quét tìm ảnh card_f/skill/f_hp.png (85%, ROI 640,0,1280,145) trong 0.5s
       - NHÁNH A (KHÔNG thấy f_hp.png): quét / tap 2 lần cách nhau 0.15s ảnh card_top/login/login_auto.png (85%, ROI 0,100,240,190) hoãn 5s, sau đó quay lại 1.
       - NHÁNH B (CÓ thấy f_hp.png): tap vào ảnh card_f/skill/f_hp.png (85%) hoãn 0.2s, tap tiếp tọa độ (905, 515) hoãn 0.2s,
         quét / tap 2 lần cách nhau 0.15s ảnh card_top/login/login_auto.png (85%) hoãn 5s, sau đó quay lại 1.
    """
    if not self.var_buff.get() or self.stop_requested: return

    # 1. Quét chờ xuất hiện: Quét tìm ảnh card_f/f_dung.png (80%, ROI 640,0,1280,145) (0.5s/lần) cho tới khi xuất hiện (CHỈ QUÉT KHÔNG TAP)
    self.after(0, self.log_info, "👁️ [SKILL - BUFF HP] Quét chờ xuất hiện 'card_f/f_dung.png' (80%, ROI 640,0,1280,145) (0.5s/lần)...")
    d_x, d_y = None, None
    while not self.stop_requested and self.var_buff.get():
        d_x, d_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_dung.png", threshold=0.80, region=(640, 0, 1280, 145))
        if d_x is not None and d_y is not None:
            break
        if self._sleep_with_stop_check(0.5): return

    if not self.var_buff.get() or self.stop_requested: return
    self.after(0, self.log_info, f"🎯 [SKILL - BUFF HP] Đã thấy 'card_f/f_dung.png' tại ({d_x}, {d_y}) (CHỈ QUÉT KHÔNG TAP)...")

    # Quét tìm f_tieptheo.png trong 0.5s
    self._check_and_tap_f_tieptheo(dnconsole_path, tab_index)

    if not self.var_buff.get() or self.stop_requested: return
    self.after(0, self.log_info, "👉 [SKILL - BUFF HP] Chuyển sang Bước 2 ➔ Quét tìm 'card_f/skill/f_hp.png' (85%, ROI 640,0,1280,145)...")

    # 2. Tiếp tục quét tìm ảnh card_f/skill/f_hp.png (85%) trong 0.5s
    hp_x, hp_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/skill/f_hp.png", threshold=0.85, region=(640, 0, 1280, 145))
    if hp_x is None or hp_y is None:
        self.after(0, self.log_info, "⚠️ [SKILL - BUFF HP] KHÔNG thấy 'card_f/skill/f_hp.png' (85%) ➔ Quét/Tap 2 lần 'login_auto.png' hoãn 5s...")
        self._tap_login_auto_twice(dnconsole_path, tab_index)
        if self._sleep_with_stop_check(5.0): return
    else:
        self.after(0, self.log_info, f"🎯 [SKILL - BUFF HP] Đã thấy 'card_f/skill/f_hp.png' tại ({hp_x}, {hp_y}) ➔ Tap click ➔ Hoãn 0.2s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {hp_x} {hp_y}"])
        time.sleep(0.2)

        if not self.var_buff.get() or self.stop_requested: return
        self.after(0, self.log_info, "🎯 [SKILL - BUFF HP] Tap tọa độ cố định (905, 515) ➔ Hoãn 0.2s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 905 515"])
        time.sleep(0.2)

        if not self.var_buff.get() or self.stop_requested: return
        self.after(0, self.log_info, "🎯 [SKILL - BUFF HP] Quét/Tap 2 lần 'login_auto.png' ➔ Hoãn 5s...")
        self._tap_login_auto_twice(dnconsole_path, tab_index)
        if self._sleep_with_stop_check(5.0): return


def handle_skill_buff_sp(self, dnconsole_path: str, tab_name: str, tab_index: str):
    """
    Hành động 2 - Buff SP:
    1. Quét chờ xuất hiện: Quét tìm ảnh card_f/f_dung.png (80%, ROI 640,0,1280,145) (0.5s/lần) cho tới khi xuất hiện (CHỈ QUÉT KHÔNG TAP)
       - Ngay khi thấy ➔ Quét tìm ảnh card_f/f_tieptheo.png (80%, ROI 1050,530,1165,680) nghỉ 0.25s/lần trong 0.5s.
       - Nếu thấy: tap vào ảnh card_f/f_tieptheo.png, hoãn 0.3s ➔ sang Bước 2.
       - Nếu không thấy: chuyển tiếp sang Bước 2.
    2. Bước 2: quét tìm ảnh card_f/skill/f_sp.png (85%, ROI 640,0,1280,145) trong 0.5s
       - NHÁNH A (KHÔNG thấy f_sp.png): quét / tap 2 lần cách nhau 0.15s ảnh card_top/login/login_auto.png (85%, ROI 0,100,240,190) hoãn 5s, sau đó quay lại 1.
       - NHÁNH B (CÓ thấy f_sp.png): tap vào ảnh card_f/skill/f_sp.png (85%) hoãn 0.2s, tap tiếp tọa độ (905, 515) hoãn 0.2s,
         quét / tap 2 lần cách nhau 0.15s ảnh card_top/login/login_auto.png (85%) hoãn 5s, sau đó quay lại 1.
    """
    if not self.var_buff.get() or self.stop_requested: return

    # 1. Quét chờ xuất hiện: Quét tìm ảnh card_f/f_dung.png (80%, ROI 640,0,1280,145) (0.5s/lần) cho tới khi xuất hiện (CHỈ QUÉT KHÔNG TAP)
    self.after(0, self.log_info, "👁️ [SKILL - BUFF SP] Quét chờ xuất hiện 'card_f/f_dung.png' (80%, ROI 640,0,1280,145) (0.5s/lần)...")
    d_x, d_y = None, None
    while not self.stop_requested and self.var_buff.get():
        d_x, d_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_dung.png", threshold=0.80, region=(640, 0, 1280, 145))
        if d_x is not None and d_y is not None:
            break
        if self._sleep_with_stop_check(0.5): return

    if not self.var_buff.get() or self.stop_requested: return
    self.after(0, self.log_info, f"🎯 [SKILL - BUFF SP] Đã thấy 'card_f/f_dung.png' tại ({d_x}, {d_y}) (CHỈ QUÉT KHÔNG TAP)...")

    # Quét tìm f_tieptheo.png trong 0.5s
    self._check_and_tap_f_tieptheo(dnconsole_path, tab_index)

    if not self.var_buff.get() or self.stop_requested: return
    self.after(0, self.log_info, "👉 [SKILL - BUFF SP] Chuyển sang Bước 2 ➔ Quét tìm 'card_f/skill/f_sp.png' (85%, ROI 640,0,1280,145)...")

    # 2. Tiếp tục quét tìm ảnh card_f/skill/f_sp.png (85%) trong 0.5s
    sp_x, sp_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/skill/f_sp.png", threshold=0.85, region=(640, 0, 1280, 145))
    if sp_x is None or sp_y is None:
        # NHÁNH A: KHÔNG tìm thấy f_sp.png
        self.after(0, self.log_info, "⚠️ [SKILL - BUFF SP] KHÔNG thấy 'card_f/skill/f_sp.png' (85%) ➔ Quét/Tap 2 lần 'login_auto.png' hoãn 5s...")
        self._tap_login_auto_twice(dnconsole_path, tab_index)
        if self._sleep_with_stop_check(5.0): return
    else:
        # NHÁNH B: CÓ tìm thấy f_sp.png
        self.after(0, self.log_info, f"🎯 [SKILL - BUFF SP] Đã thấy 'card_f/skill/f_sp.png' tại ({sp_x}, {sp_y}) ➔ Tap click ➔ Hoãn 0.2s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {sp_x} {sp_y}"])
        time.sleep(0.2)

        if not self.var_buff.get() or self.stop_requested: return
        self.after(0, self.log_info, "🎯 [SKILL - BUFF SP] Tap tọa độ cố định (905, 515) ➔ Hoãn 0.2s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 905 515"])
        time.sleep(0.2)

        if not self.var_buff.get() or self.stop_requested: return
        self.after(0, self.log_info, "🎯 [SKILL - BUFF SP] Quét/Tap 2 lần 'login_auto.png' ➔ Hoãn 5s...")
        self._tap_login_auto_twice(dnconsole_path, tab_index)
        if self._sleep_with_stop_check(5.0): return


def handle_skill_buff_3hp_1sp(self, dnconsole_path: str, tab_name: str, tab_index: str):
    """
    Hành động 3 - Buff 3HP / 1SP (Tự động luân phiên 3 Lượt HP ➔ 1 Lượt SP):
    - Lượt 1 (1/3, 2/3, 3/3): Chạy 3 chu kỳ hoàn chỉnh Buff HP
    - Lượt 2: Chạy 1 chu kỳ hoàn chỉnh Buff SP
    """
    if not self.var_buff.get() or self.stop_requested: return

    for hp_round in range(1, 4):
        if not self.var_buff.get() or self.stop_requested: return
        self.after(0, self.log_info, f"🔄 [SKILL - BUFF 3HP/1SP] ➔ [Lượt 1 - Lần {hp_round}/3] Bắt đầu chu kỳ hoàn chỉnh Buff HP...")
        self._handle_skill_buff_hp(dnconsole_path, tab_name, tab_index)

    if not self.var_buff.get() or self.stop_requested: return
    self.after(0, self.log_info, "🔄 [SKILL - BUFF 3HP/1SP] ➔ [Lượt 2] Bắt đầu chu kỳ hoàn chỉnh Buff SP...")
    self._handle_skill_buff_sp(dnconsole_path, tab_name, tab_index)
