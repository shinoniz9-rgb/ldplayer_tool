# -*- coding: utf-8 -*-
"""
========================================================================================
🔒 [BẢN BACKUP THAM CHIẾU ĐỘC LẬP & KHÓA NGUYÊN BẢN]: CARD C (DỊ GIỚI ĐÊM)
========================================================================================
Ngày tạo: 2026-09-02
Mục đích:
- Lưu trữ độc lập toàn bộ giao diện và logic thực thi của Card C (Dị Giới Đêm).
- Mã nguồn này đã được kiểm tra thực tế, tối ưu hóa các vùng ROI và thời gian trễ hoàn chỉnh.
- Độc lập 100% với các chỉnh sửa phát sinh sau này trên file main.py.

========================================================================================
📌 BẢNG TRA CỨU TỌA ĐỘ VÙNG QUÉT ROI & NGƯỠNG THRESHOLD CARD C
========================================================================================
1. login_x.png   : (990, 50, 1165, 200)    - Threshold: 0.75 (75%)  [Đóng quảng cáo/thông báo]
2. c_vitri.png   : (735, 405, 1280, 720)   - Threshold: 0.85 (85%)  [Nút Vị Trí về Safezone / Chuyển Map]
3. a_co.png      : (275, 540, 1150, 670)   - Threshold: 0.85 (85%)  [Nút Có về Thành]
4. c_ai.png      : (735, 405, 1280, 720)   - Threshold: 0.85 (85%)  [Nút mở bảng AI menu góc dưới phải]
5. c_digioi.png  : (1060, 0, 1280, 40)     - Threshold: 0.85 (85%)  [Tên map Dị Giới góc trên phải]
6. c_aitim.png   : (0, 100, 240, 190)      - Threshold: 0.75 (75%)  [Nút AI Tìm tắt/bật auto đánh quái]
7. c_phucthan.png: (305, 165, 705, 605)    - Threshold: 0.85 (85%)  [Trạng thái ô Phúc Thần]
8. c_kyluc.png   : (305, 165, 705, 605)    - Threshold: 0.85 (85% - 95% lúc 22h50) [Trạng thái ô Ký Lục]
9. c_rutgon.png  : (305, 165, 705, 605)    - Threshold: 0.85 (85%)  [Trạng thái ô Rút Gọn]
========================================================================================
"""

import time
from datetime import datetime, timedelta
import customtkinter as ctk

# =========================================================================
# PHẦN 1: MÃ NGUỒN GIAO DIỆN DESKTOP (GUI) CỦA CARD C
# =========================================================================
def build_card_C_ui(self, parent_container):
    """
    Xây dựng giao diện Card C (Dị Giới Đêm) trên Desktop GUI
    Vị trí: Hàng 0, Cột 1 (song song bên phải Card A Boss Thế Giới)
    """
    # ------------------- CARD C: DỊ GIỚI ĐÊM (Hàng 1, Cột 1) -------------------
    self.card_C = ctk.CTkFrame(parent_container, corner_radius=10)
    self.card_C.grid(row=0, column=1, padx=3, pady=2, sticky="nsew")
    self.card_C.grid_columnconfigure(0, weight=1)
    self.card_C.grid_rowconfigure(0, weight=0)
    self.card_C.grid_rowconfigure((1, 2, 3), weight=1)

    hdr_C = ctk.CTkFrame(self.card_C, fg_color="transparent")
    hdr_C.grid(row=0, column=0, padx=8, pady=(2, 0), sticky="ew")
    hdr_C.grid_columnconfigure(0, weight=1)
    hdr_C.grid_columnconfigure(1, weight=0)

    lbl_C = ctk.CTkLabel(hdr_C, text="DỊ GIỚI ĐÊM", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color="#38BDF8")
    lbl_C.grid(row=0, column=0, sticky="w")

    self.switch_C = ctk.CTkSwitch(
        hdr_C, text="", variable=self.var_switch_C, command=self._on_switch_C_toggled,
        width=28, height=14, switch_width=28, switch_height=14, fg_color="#374151", progress_color="#EA580C", text_color="#FFFFFF"
    )
    self.switch_C.grid(row=0, column=1, sticky="e")

    # Row 1: Phúc Thần + ( OFF / ON )
    row_C1 = ctk.CTkFrame(self.card_C, fg_color="transparent")
    row_C1.grid(row=1, column=0, padx=6, pady=0, sticky="ew")

    self.chk_C1 = ctk.CTkCheckBox(row_C1, text="Phúc Thần", variable=self.var_C1, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
    self.chk_C1.pack(side="left")

    lbl_C1_tag = ctk.CTkLabel(row_C1, text="( OFF / ON )", font=ctk.CTkFont(family="Segoe UI", size=8, weight="normal"), text_color="#FFFFFF")
    lbl_C1_tag.pack(side="right", padx=(0, 10))

    # Row 2: Ký Lục + ( OFF / ON )
    row_C2 = ctk.CTkFrame(self.card_C, fg_color="transparent")
    row_C2.grid(row=2, column=0, padx=6, pady=0, sticky="ew")

    self.chk_C2 = ctk.CTkCheckBox(row_C2, text="Ký Lục", variable=self.var_C2, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
    self.chk_C2.pack(side="left")

    lbl_C2_tag = ctk.CTkLabel(row_C2, text="( OFF / ON )", font=ctk.CTkFont(family="Segoe UI", size=8, weight="normal"), text_color="#FFFFFF")
    lbl_C2_tag.pack(side="right", padx=(0, 10))

    # Row 3: Rút Gọn + ( OFF / ON )
    row_C3 = ctk.CTkFrame(self.card_C, fg_color="transparent")
    row_C3.grid(row=3, column=0, padx=6, pady=(0, 2), sticky="ew")

    self.chk_C3 = ctk.CTkCheckBox(row_C3, text="Rút Gọn", variable=self.var_C3, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
    self.chk_C3.pack(side="left")

    lbl_C3_tag = ctk.CTkLabel(row_C3, text="( OFF / ON )", font=ctk.CTkFont(family="Segoe UI", size=8, weight="normal"), text_color="#FFFFFF")
    lbl_C3_tag.pack(side="right", padx=(0, 10))


# =========================================================================
# PHẦN 2: MÃ NGUỒN LOGIC VỀ KHU AN TOÀN CHO DỊ GIỚI
# =========================================================================
def run_safezone_di_gioi(self, dnconsole_path: str, tab_index: str, px_x: int, px_y: int):
    """QUY TRÌNH VỀ KHU AN TOÀN CHO CARD DỊ GIỚI (Cập nhật thao tác chuẩn theo Card Boss TG)"""
    if self._should_stop_card_C(): return
    self.after(0, self.log_info, "👁️ Quét tìm nút 'card_top/login/login_x.png' (ROI 990,50,1165,200) để đóng bảng quảng cáo/thông báo...")
    lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(990, 50, 1165, 200))
    if lx_x is not None and lx_y is not None:
        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_top/login/login_x.png' tại ({lx_x}, {lx_y})! Click chọn ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
        time.sleep(0.4)

    if self._should_stop_card_C(): return
    self.after(0, self.log_info, "👁️ [Dị Giới - Về Khu An Toàn] Quét tìm nút Vị Trí 'card_c/c_vitri.png' (85%, ROI 735,405,1280,720)...")
    v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
    if v_x is not None and v_y is not None:
        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_vitri.png' tại ({v_x}, {v_y})! Tap click trực tiếp ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
        time.sleep(0.4)
    else:
        self.after(0, self.log_info, f"👉 Chưa thấy 'card_c/c_vitri.png' ➔ Click nút xanh lá góc dưới phải ({px_x}, {px_y}) mở menu ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
        time.sleep(0.4)
        if self._should_stop_card_C(): return
        v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
        if v_x is not None and v_y is not None:
            self.after(0, self.log_info, f"🎯 Phát hiện nút 'card_c/c_vitri.png' tại ({v_x}, {v_y})! Tap click trực tiếp ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'card_c/c_vitri.png' trong bảng menu.")

    if self._should_stop_card_C(): return
    self.after(0, self.log_info, "👉 Click liên tục (435, 250) mỗi 0.5s cho đến khi xuất hiện nút Có 'card_a/a_co.png' (85%, ROI 275,540,1150,670)...")
    while not self._should_stop_card_C():
        co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_co.png", threshold=0.85, region=(275, 540, 1150, 670))
        if co_x is not None and co_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút Có 'card_a/a_co.png' tại ({co_x}, {co_y})! Dừng click (435, 250).")
            break
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 435 250"])
        time.sleep(0.5)

    if self._should_stop_card_C(): return
    self.after(0, self.log_info, "👁️ Click liên tục nút Có 'card_a/a_co.png' (0.5s mỗi lần) cho tới khi hết ảnh...")
    while not self._should_stop_card_C():
        co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_co.png", threshold=0.85, region=(275, 540, 1150, 670))
        if co_x is not None and co_y is not None:
            self.after(0, self.log_info, f"🎯 Phát hiện nút Có 'card_a/a_co.png' tại ({co_x}, {co_y}) ➔ Click vào vị trí ảnh...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {co_x} {co_y}"])
            time.sleep(0.5)
        else:
            self.after(0, self.log_info, "ℹ️ Không còn thấy ảnh nút Có 'card_a/a_co.png' ➔ Hoàn thành Về Khu An Toàn!")
            break

    if self._should_stop_card_C(): return
    self.after(0, self.log_info, "⏳ [Dị Giới - Về Khu An Toàn] Hoãn 3.0s trước khi quét kiểm tra lại nút 'card_c/c_vitri.png'...")
    time.sleep(3.0)

    if self._should_stop_card_C(): return
    self.after(0, self.log_info, "👁️ [Dị Giới - Về Khu An Toàn] Quét kiểm tra lại nút 'card_c/c_vitri.png' (85%, ROI 735,405,1280,720)...")
    v_check_x, v_check_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
    if v_check_x is not None and v_check_y is not None:
        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_vitri.png' vẫn còn tại ({v_check_x}, {v_check_y}) ➔ Click ({px_x}, {px_y}) để thu gọn menu ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
        time.sleep(0.4)
    else:
        self.after(0, self.log_info, "ℹ️ Không thấy nút 'card_c/c_vitri.png' ➔ Bỏ qua thu gọn menu.")


# =========================================================================
# PHẦN 3: MÃ NGUỒN LOGIC THỰC THI CHÍNH CARD C (DỊ GIỚI ĐÊM)
# =========================================================================
def execute_card_C_di_gioi(self, dnconsole_path: str, tab_name: str, tab_index: str):
    """Thực thi Card DỊ GIỚI (C) theo quy trình mới được tích hợp mặc định vào công tắc trượt ON/OFF"""
    if self._should_stop_card_C():
        return

    # =========================================================================
    # 📌 BƯỚC 1: TÍNH TOÁN TỌA ĐỘ THEO TỶ LỆ MÀN HÌNH
    # =========================================================================
    screen_w, screen_h = self._get_emulator_screen_size(dnconsole_path, tab_index)

    if screen_w == 1280 and screen_h == 720:
        px_x, px_y = 1213, 648
        pt_tap_x, pt_tap_y = 630, 310
        kl_tap_x, kl_tap_y = 630, 355
        rg_tap_x, rg_tap_y = 630, 525
        c_x, c_y = 687, 595
        end_x, end_y = 1090, 125
        v1_x, v1_y = 235, 450
        v2_x, v2_y = 1035, 210
    else:
        px_x = int(round((1213 / 1280.0) * screen_w))
        px_y = int(round((648 / 720.0) * screen_h))
        pt_tap_x = int(round((630 / 1280.0) * screen_w))
        pt_tap_y = int(round((310 / 720.0) * screen_h))
        kl_tap_x = int(round((630 / 1280.0) * screen_w))
        kl_tap_y = int(round((355 / 720.0) * screen_h))
        rg_tap_x = int(round((630 / 1280.0) * screen_w))
        rg_tap_y = int(round((525 / 720.0) * screen_h))
        c_x = int(round((687 / 1280.0) * screen_w))
        c_y = int(round((595 / 720.0) * screen_h))
        end_x = int(round((1090 / 1280.0) * screen_w))
        end_y = int(round((125 / 720.0) * screen_h))
        v1_x = int(round((235 / 1280.0) * screen_w))
        v1_y = int(round((450 / 720.0) * screen_h))
        v2_x = int(round((1035 / 1280.0) * screen_w))
        v2_y = int(round((210 / 720.0) * screen_h))

    self.after(0, self.log_info, f"🖥️ [DỊ GIỚI - BƯỚC 1] LDPlayer Tab '{tab_name}' ({screen_w}x{screen_h})")

    # =========================================================================
    # 📌 BƯỚC 2: QUY TRÌNH DỊ GIỚI ĐÊM (TÍCH HỢP MẶC ĐỊNH VÀO CÔNG TẮC TRƯỢT ON/OFF)
    # =========================================================================
    # 1. Đếm giờ đến 22H50
    now = datetime.now()
    target_2250 = now.replace(hour=22, minute=50, second=0, microsecond=0)

    if now < target_2250:
        self.after(0, self.log_info, f"⏳ [DỊ GIỚI - BƯỚC 2.1] Đang đếm giờ chờ đến 22H50 đêm (Hiện tại: {now.strftime('%H:%M:%S')})...")
        while datetime.now() < target_2250:
            if self._should_stop_card_C():
                return
            time.sleep(1.0)

    if self._should_stop_card_C(): return

    # 2. Tắt Ký Lục lúc 22H50
    self.after(0, self.log_info, "▶️ [DỊ GIỚI - BƯỚC 2.2] Đã đến 22H50! Quét Cài Đặt AI để TẮT Ký Lục...")
    ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_ai.png", threshold=0.85, region=(735, 405, 1280, 720))
    if ai_x is not None and ai_y is not None:
        self.after(0, self.log_info, f"🎯 Phát hiện nút 'card_c/c_ai.png' tại ({ai_x}, {ai_y}) ➔ Tap click ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
        time.sleep(0.4)
    else:
        self.after(0, self.log_info, f"👉 Chưa thấy 'card_c/c_ai.png' ➔ Tap ({px_x}, {px_y}) mở menu ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
        time.sleep(0.4)
        if self._should_stop_card_C(): return
        ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_ai.png", threshold=0.85, region=(735, 405, 1280, 720))
        if ai_x is not None and ai_y is not None:
            self.after(0, self.log_info, f"🎯 Phát hiện nút 'card_c/c_ai.png' tại ({ai_x}, {ai_y}) ➔ Tap click ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'card_c/c_ai.png'.")

    if self._should_stop_card_C(): return
    self.after(0, self.log_info, f"👉 Tap Cài đặt AI tại ({c_x}, {c_y}) ➔ Hoãn 0.4s...")
    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {c_x} {c_y}"])
    time.sleep(0.4)

    if self._should_stop_card_C(): return
    self.after(0, self.log_info, "👁️ Quét kiểm tra 'card_c/c_kyluc.png' (95%, ROI 305,165,705,605)...")
    kl_x, kl_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_kyluc.png", threshold=0.95, region=(305, 165, 705, 605))
    if kl_x is None:
        self.after(0, self.log_info, f"🎯 Giao diện ĐANG BẬT Ký Lục ➔ Tap ({kl_tap_x}, {kl_tap_y}) để TẮT Ký Lục ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {kl_tap_x} {kl_tap_y}"])
        time.sleep(0.4)
    else:
        self.after(0, self.log_info, "ℹ️ Giao diện ĐÃ TẮT Ký Lục sẵn ➔ Bỏ qua.")

    if self._should_stop_card_C(): return
    self.after(0, self.log_info, f"👉 Tap đóng bảng tại ({end_x}, {end_y}) ➔ Tap ({px_x}, {px_y}) thu gọn menu ➔ Hoãn 0.4s...")
    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {end_x} {end_y}"])
    time.sleep(0.4)
    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
    time.sleep(0.4)

    # 3. Đếm giờ qua ngày mới (00H00)
    now = datetime.now()
    target_0000 = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if now >= target_0000:
        target_0000 += timedelta(days=1)

    self.after(0, self.log_info, f"⏳ [DỊ GIỚI - BƯỚC 2.3] Tiếp tục đếm giờ chờ đến 00H00 ngày mới (Hiện tại: {now.strftime('%H:%M:%S')})...")
    while datetime.now() < target_0000:
        if self._should_stop_card_C():
            return
        time.sleep(1.0)

    if self._should_stop_card_C(): return

    # 4. Quét nhận diện bản đồ Dị Giới lúc 00H00
    self.after(0, self.log_info, "👁️ [DỊ GIỚI - BƯỚC 2.4 - 00H00] Quét nhận diện map Dị Giới 'card_c/c_digioi.png' (85%, ROI 1060,0,1280,40)...")
    dg_x, dg_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_digioi.png", threshold=0.85, region=(1060, 0, 1280, 40))
    if dg_x is not None and dg_y is not None:
        self.after(0, self.log_info, f"🎯 Đã phát hiện map Dị Giới 'card_c/c_digioi.png' tại ({dg_x}, {dg_y}) ➔ Quét Mắt Thần nút AI Tìm 'card_c/c_aitim.png' (75%, ROI 0,100,240,190) liên tục trong 5.0s...")
        aitim_x, aitim_y = None, None
        for _ in range(10):
            if self._should_stop_card_C(): return
            aitim_x, aitim_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_aitim.png", threshold=0.75, region=(0, 100, 240, 190))
            if aitim_x is not None and aitim_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_aitim.png' tại ({aitim_x}, {aitim_y})! Click chọn nút AI Tìm để TẮT tự động đánh quái ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {aitim_x} {aitim_y}"])
                time.sleep(0.4)
                break
            time.sleep(0.5)

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "⏳ Hoãn 20s (bỏ qua các bước di chuyển)...")
        for _ in range(20):
            if self._should_stop_card_C(): return
            time.sleep(1.0)
    else:
        self.after(0, self.log_info, "👉 Chưa thấy map 'card_c/c_digioi.png' ➔ Gọi Về Khu An Toàn trước khi vào Dị Giới...")
        self._run_safezone_di_gioi(dnconsole_path, tab_index, px_x, px_y)

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "👉 Quét nút Vị Trí 'card_c/c_vitri.png' (85%, ROI 735,405,1280,720)...")
        v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
        if v_x is not None and v_y is not None:
            self.after(0, self.log_info, f"🎯 Phát hiện 'card_c/c_vitri.png' tại ({v_x}, {v_y}) ➔ Tap click ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, f"👉 Chưa thấy 'card_c/c_vitri.png' ➔ Tap ({px_x}, {px_y}) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
            time.sleep(0.4)
            if self._should_stop_card_C(): return
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'card_c/c_vitri.png' tại ({v_x}, {v_y}) ➔ Tap click ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                time.sleep(0.4)

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, f"👉 Tap tọa độ chuyển map 1 ({v1_x}, {v1_y}) ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v1_x} {v1_y}"])
        time.sleep(0.4)

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, f"👉 Tap tọa độ chuyển map 2 ({v2_x}, {v2_y}) ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v2_x} {v2_y}"])
        time.sleep(0.4)

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "⏳ [DỊ GIỚI] Tạm nghỉ 3.0s nạp map Dị Giới...")
        for _ in range(3):
            if self._should_stop_card_C(): return
            time.sleep(1.0)

    # 5. Bật Ký Lục lúc 00H00
    if self._should_stop_card_C(): return
    self.after(0, self.log_info, "▶️ [DỊ GIỚI - BƯỚC 2.5 - 00H00] Tự động kích hoạt BẬT KÝ LỤC trở lại...")
    ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_ai.png", threshold=0.85, region=(735, 405, 1280, 720))
    if ai_x is not None and ai_y is not None:
        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_ai.png' tại ({ai_x}, {ai_y}) ➔ Tap click ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
        time.sleep(0.4)
    else:
        self.after(0, self.log_info, f"👉 Chưa thấy 'card_c/c_ai.png' ➔ Tap ({px_x}, {px_y}) mở menu ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
        time.sleep(0.4)
        if self._should_stop_card_C(): return
        ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_ai.png", threshold=0.85, region=(735, 405, 1280, 720))
        if ai_x is not None and ai_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_ai.png' tại ({ai_x}, {ai_y}) ➔ Tap click ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
            time.sleep(0.4)

    if self._should_stop_card_C(): return
    self.after(0, self.log_info, f"👉 Tap Cài đặt AI tại ({c_x}, {c_y}) ➔ Hoãn 0.4s...")
    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {c_x} {c_y}"])
    time.sleep(0.4)

    if self._should_stop_card_C(): return
    self.after(0, self.log_info, "👁️ Quét kiểm tra 'card_c/c_kyluc.png' (85%, ROI 305,165,705,605)...")
    kl_x, kl_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_kyluc.png", threshold=0.85, region=(305, 165, 705, 605))
    if kl_x is not None and kl_y is not None:
        self.after(0, self.log_info, f"🎯 Giao diện ĐANG TẮT Ký Lục ➔ Tap ({kl_tap_x}, {kl_tap_y}) để BẬT Ký Lục ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {kl_tap_x} {kl_tap_y}"])
        time.sleep(0.4)
    else:
        self.after(0, self.log_info, "ℹ️ Giao diện ĐÃ BẬT Ký Lục sẵn ➔ Bỏ qua.")

    if self._should_stop_card_C(): return
    self.after(0, self.log_info, f"👉 Tap đóng bảng tại ({end_x}, {end_y}) ➔ Tap ({px_x}, {px_y}) thu gọn menu ➔ Hoãn 0.4s...")
    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {end_x} {end_y}"])
    time.sleep(0.4)
    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
    time.sleep(0.4)

    # =========================================================================
    # 📌 BƯỚC 3: BẬT / TẮT 3 Ô CHECK PHÚC THẦN, KÝ LỤC, RÚT GỌN (C1, C2, C3)
    # =========================================================================
    has_phuc_than = self.var_C1.get()
    has_ky_luc = self.var_C2.get()
    has_rut_gon = self.var_C3.get()

    # 1. Mục Phúc Thần (C1)
    if self._should_stop_card_C(): return
    self.after(0, self.log_info, f"▶️ [DỊ GIỚI - BƯỚC 3.1] Kiểm tra ô Phúc Thần (Trạng thái: {'BẬT' if has_phuc_than else 'TẮT'})...")
    ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_ai.png", threshold=0.85, region=(735, 405, 1280, 720))
    if ai_x is not None and ai_y is not None:
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
        time.sleep(0.4)
    else:
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
        time.sleep(0.4)
        if self._should_stop_card_C(): return
        ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_ai.png", threshold=0.85, region=(735, 405, 1280, 720))
        if ai_x is not None and ai_y is not None:
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
            time.sleep(0.4)

    pt_x, pt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_phucthan.png", threshold=0.85, region=(305, 165, 705, 605))
    if has_phuc_than:
        if pt_x is not None and pt_y is not None:
            self.after(0, self.log_info, f"🎯 [BẬT] Tap ({pt_tap_x}, {pt_tap_y}) để Bật Phúc Thần ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {pt_tap_x} {pt_tap_y}"])
            time.sleep(0.4)
    else:
        if pt_x is None:
            self.after(0, self.log_info, f"🎯 [TẮT] Tap ({pt_tap_x}, {pt_tap_y}) để Tắt Phúc Thần ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {pt_tap_x} {pt_tap_y}"])
            time.sleep(0.4)

    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {end_x} {end_y}"])
    time.sleep(0.4)
    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
    time.sleep(0.4)

    # 2. Mục Ký Lục (C2)
    if self._should_stop_card_C(): return
    self.after(0, self.log_info, f"▶️ [DỊ GIỚI - BƯỚC 3.2] Kiểm tra ô Ký Lục (Trạng thái: {'BẬT' if has_ky_luc else 'TẮT'})...")
    ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_ai.png", threshold=0.85, region=(735, 405, 1280, 720))
    if ai_x is not None and ai_y is not None:
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
        time.sleep(0.4)
    else:
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
        time.sleep(0.4)
        if self._should_stop_card_C(): return
        ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_ai.png", threshold=0.85, region=(735, 405, 1280, 720))
        if ai_x is not None and ai_y is not None:
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
            time.sleep(0.4)

    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {c_x} {c_y}"])
    time.sleep(0.4)

    kl_x, kl_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_kyluc.png", threshold=0.85, region=(305, 165, 705, 605))
    if has_ky_luc:
        if kl_x is not None and kl_y is not None:
            self.after(0, self.log_info, f"🎯 [BẬT] Tap ({kl_tap_x}, {kl_tap_y}) để Bật Ký Lục ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {kl_tap_x} {kl_tap_y}"])
            time.sleep(0.4)
    else:
        if kl_x is None:
            self.after(0, self.log_info, f"🎯 [TẮT] Tap ({kl_tap_x}, {kl_tap_y}) để Tắt Ký Lục ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {kl_tap_x} {kl_tap_y}"])
            time.sleep(0.4)

    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {end_x} {end_y}"])
    time.sleep(0.4)
    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
    time.sleep(0.4)

    # 3. Mục Rút Gọn (C3)
    if self._should_stop_card_C(): return
    self.after(0, self.log_info, f"▶️ [DỊ GIỚI - BƯỚC 3.3] Kiểm tra ô Rút Gọn (Trạng thái: {'BẬT' if has_rut_gon else 'TẮT'})...")
    ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_ai.png", threshold=0.85, region=(735, 405, 1280, 720))
    if ai_x is not None and ai_y is not None:
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
        time.sleep(0.4)
    else:
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
        time.sleep(0.4)
        if self._should_stop_card_C(): return
        ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_ai.png", threshold=0.85, region=(735, 405, 1280, 720))
        if ai_x is not None and ai_y is not None:
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
            time.sleep(0.4)

    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {c_x} {c_y}"])
    time.sleep(0.4)

    rg_x, rg_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_rutgon.png", threshold=0.85, region=(305, 165, 705, 605))
    if has_rut_gon:
        if rg_x is not None and rg_y is not None:
            self.after(0, self.log_info, f"🎯 [BẬT] Tap ({rg_tap_x}, {rg_tap_y}) để Bật Rút Gọn ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {rg_tap_x} {rg_tap_y}"])
            time.sleep(0.4)
    else:
        if rg_x is None:
            self.after(0, self.log_info, f"🎯 [TẮT] Tap ({rg_tap_x}, {rg_tap_y}) để Tắt Rút Gọn ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {rg_tap_x} {rg_tap_y}"])
            time.sleep(0.4)

    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {end_x} {end_y}"])
    time.sleep(0.4)
    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
    time.sleep(0.4)

    if has_rut_gon:
        self.after(0, self.log_info, "⚙️ [DỊ GIỚI - BƯỚC 3.3] Hoàn thành thao tác Rút Gọn (giữ nguyên ô tích).")

    # =========================================================================
    # 📌 BƯỚC 4: KÍCH HOẠT NÚT AI TÌM ('card_c/c_aitim.png') HOẶC THOÁT GAME
    # =========================================================================
    if self._should_stop_card_C(): return
    self.after(0, self.log_info, "▶️ [DỊ GIỚI - BƯỚC 4] Quét kiểm tra nút AI Tìm 'card_c/c_aitim.png' (75%, ROI 0,100,240,190) liên tục trong 5.0s...")
    aitim_x, aitim_y = None, None
    for _ in range(10):
        if self._should_stop_card_C(): return
        aitim_x, aitim_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_aitim.png", threshold=0.75, region=(0, 100, 240, 190))
        if aitim_x is not None and aitim_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút AI Tìm 'card_c/c_aitim.png' tại ({aitim_x}, {aitim_y})! Click chọn ngay ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {aitim_x} {aitim_y}"])
            time.sleep(0.4)
            break
        time.sleep(0.5)

    if aitim_x is None or aitim_y is None:
        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "⚠️ Không phát hiện thấy ảnh 'card_c/c_aitim.png' sau 5.0s ➔ Tiến hành Thoát Game...")
        # Đóng ứng dụng game trên LDPlayer (Bỏ hoãn 1s dư thừa)
        self._exec_cmd([dnconsole_path, "killapp", "--index", str(tab_index)])
        for pkg in ["com.vtcmobile.gz06"]:
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell am force-stop {pkg}"])
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input keyevent 3"])

    # =========================================================================
    # 📌 BƯỚC 5: HOÀN TẤT & TỰ ĐỘNG TẮT CÔNG TẮC
    # =========================================================================
    self.after(0, lambda: self.var_switch_C.set(False))
    self.after(0, self.save_config)
    self.after(0, self.log_info, "✅ [DỊ GIỚI - BƯỚC 5] Đã hoàn thành toàn bộ chuỗi thao tác Dị Giới ➔ Tự động tắt công tắc ON/OFF C về OFF!")
    self.after(0, lambda: self._send_notification("🎉 Dị Giới Đêm Hoàn Thành", f"Đã hoàn thành toàn bộ hoạt động Dị Giới Đêm trên {tab_name}!"))
