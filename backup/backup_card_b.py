# -*- coding: utf-8 -*-
"""
========================================================================================
🔒 [BẢN BACKUP THAM CHIẾU ĐỘC LẬP & KHÓA NGUYÊN BẢN]: CARD B (PHỤ BẢN ĐƠN / ĐỘI)
========================================================================================
Ngày tạo: 2026-09-02
Mục đích:
- Lưu trữ độc lập toàn bộ giao diện và logic thực thi của Card B (Phụ Bản Đơn / Đội).
- Mã nguồn này đã được kiểm tra thực tế, tối ưu hóa các vùng ROI và thời gian trễ hoàn chỉnh.
- Độc lập 100% với các chỉnh sửa phát sinh sau này trên file main.py.

========================================================================================
📌 BẢNG TRA CỨU TỌA ĐỘ VÙNG QUÉT ROI & NGƯỠNG THRESHOLD CARD B
========================================================================================
1.  login_x.png   : (990, 50, 1165, 200)    - Threshold: 0.75 (75%)  [Đóng quảng cáo/thông báo]
2.  c_vitri.png   : (735, 405, 1280, 720)   - Threshold: 0.85 (85%)  [Nút Vị Trí về Safezone]
3.  a_co.png      : (275, 540, 1150, 670)   - Threshold: 0.85 (85%)  [Nút Có về Thành]
4.  b_doi.png     : (735, 405, 1280, 720)   - Threshold: 0.85 (85%)  [Nút Đội đổi tướng]
5.  b_pb.png      : (735, 405, 1280, 720)   - Threshold: 0.85 (85%)  [Nút Phụ Bản]
6.  b_lsknn.png    : (165, 170, 1110, 615)   - Threshold: 0.85 (85%)  [Tab Lịch Sử Kỹ Năng]
7.  b_pbdon.png   : (165, 170, 1110, 615)   - Threshold: 0.85 (85%)  [Mục Phụ Bản Đơn]
8.  b_pb20.png    : (165, 170, 1110, 615)   - Threshold: 0.85 (85%)  [Mốc PB 20]
9.  b_pb50.png    : (165, 170, 1110, 615)   - Threshold: 0.85 (85%)  [Mốc PB 50]
10. b_pb80.png    : (165, 170, 1110, 615)   - Threshold: 0.85 (85%)  [Mốc PB 80]
11. b_pb110.png   : (165, 170, 1110, 615)   - Threshold: 0.85 (85%)  [Mốc PB 110]
12. b_pb140.png   : (165, 170, 1110, 615)   - Threshold: 0.85 (85%)  [Mốc PB 140]
13. b_matkhau.png : (165, 170, 1110, 615)   - Threshold: 0.85 (85%)  [Khóa Mật Khẩu phòng]
14. b_batdau.png  : (165, 170, 1110, 615)   - Threshold: 0.85 (85%)  [Nút Bắt Đầu vào trận]
15. b_xn.png      : (165, 170, 1110, 615)   - Threshold: 0.85 (85%)  [Nút Xác Nhận thắng trận]
16. b_pb20map.png : (1060, 0, 1280, 40)     - Threshold: 0.80 (80%)  [Nhận diện map PB 20 - 60s]
17. b_pb50map.png : (1060, 0, 1280, 40)     - Threshold: 0.80 (80%)  [Nhận diện map PB 50 - 120s]
18. b_pb80map.png : (1060, 0, 1280, 40)     - Threshold: 0.80 (80%)  [Nhận diện map PB 80 - 180s]
19. b_pb110map.png: (1060, 0, 1280, 40)     - Threshold: 0.80 (80%)  [Nhận diện map PB 110 - 240s]
20. b_pb140map.png: (1060, 0, 1280, 40)     - Threshold: 0.80 (80%)  [Nhận diện map PB 140 - 300s]
========================================================================================
"""

import time
import customtkinter as ctk

# =========================================================================
# PHẦN 1: MÃ NGUỒN GIAO DIỆN DESKTOP (GUI) CỦA CARD B
# =========================================================================
def build_card_B_ui(self, parent_container, char_options):
    """
    Xây dựng giao diện Card B (Phụ Bản Đơn / Đội) trên Desktop GUI
    Vị trí: Hàng 1 (hàng thứ 2 của Grid 2x2), Cột 0
    """
    # ------------------- CARD B: PHỤ BẢN ĐƠN / ĐỘI (Hàng 2, Cột 0) -------------------
    self.card_B = ctk.CTkFrame(parent_container, corner_radius=10)
    self.card_B.grid(row=1, column=0, padx=3, pady=3, sticky="nsew")
    self.card_B.grid_columnconfigure(0, weight=1)
    self.card_B.grid_rowconfigure(0, weight=0)
    self.card_B.grid_rowconfigure(1, weight=1)

    hdr_B = ctk.CTkFrame(self.card_B, fg_color="transparent")
    hdr_B.grid(row=0, column=0, padx=8, pady=(4, 1), sticky="ew")
    hdr_B.grid_columnconfigure(0, weight=1)
    hdr_B.grid_columnconfigure(1, weight=0)

    lbl_B = ctk.CTkLabel(hdr_B, text="PHỤ BẢN ĐƠN / ĐỘI", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color="#38BDF8")
    lbl_B.grid(row=0, column=0, sticky="w")

    self.switch_B = ctk.CTkSwitch(
        hdr_B, text="", variable=self.var_switch_B, command=self._on_switch_B_toggled,
        width=28, height=14, switch_width=28, switch_height=14, fg_color="#374151", progress_color="#EA580C", text_color="#FFFFFF"
    )
    self.switch_B.grid(row=0, column=1, sticky="e")

    # Thùng chứa thân Card B (gồm 4 Hàng nội dung đồng nhất + 1 đường gạch ngang)
    body_B = ctk.CTkFrame(self.card_B, fg_color="transparent")
    body_B.grid(row=1, column=0, padx=6, pady=(1, 4), sticky="nsew")
    body_B.grid_columnconfigure(0, weight=1)
    body_B.grid_rowconfigure((0, 2, 3, 4), weight=1, uniform="pb_row")
    body_B.grid_rowconfigure(1, weight=0)

    # HẰNG 1 (Phụ Bản Đơn): [ ] Đơn | [ Menu NV Đơn ]
    row1_frame = ctk.CTkFrame(body_B, fg_color="transparent")
    row1_frame.grid(row=0, column=0, sticky="ew")

    self.chk_B_don = ctk.CTkCheckBox(
        row1_frame, text="Đơn", variable=self.var_B_don, command=self._on_checkbox_toggled,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
        fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
    )
    self.chk_B_don.pack(side="left")

    self.combo_B_don_char = ctk.CTkOptionMenu(
        row1_frame,
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
    self.combo_B_don_char.set(char_options[0] if char_options else "Xuất Chiến")
    self.combo_B_don_char.pack(side="right", padx=(0, 2))

    # Đường gạch ngang phân cách ở Row 1 (Nằm giữa Hàng 1 và Hàng 2)
    divider_horiz_B = ctk.CTkFrame(body_B, height=2, corner_radius=0, fg_color="#EA580C", border_width=0)
    divider_horiz_B.grid(row=1, column=0, sticky="ew", padx=4, pady=(1, 3))

    # HẰNG 2 (Phụ Bản Đội): [ ] Đội | [ Menu NV Team ]
    row2_frame = ctk.CTkFrame(body_B, fg_color="transparent")
    row2_frame.grid(row=2, column=0, sticky="ew")

    self.chk_B_doi = ctk.CTkCheckBox(
        row2_frame, text="Đội", variable=self.var_B_doi, command=self._on_checkbox_toggled,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
        fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
    )
    self.chk_B_doi.pack(side="left")

    self.combo_B_team_char = ctk.CTkOptionMenu(
        row2_frame,
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
    self.combo_B_team_char.set(char_options[0] if char_options else "Xuất Chiến")
    self.combo_B_team_char.pack(side="right", padx=(0, 2))

    # HẰNG 3 (PB 20, PB 50, PB 80)
    row3_frame = ctk.CTkFrame(body_B, fg_color="transparent")
    row3_frame.grid(row=3, column=0, sticky="ew")
    row3_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="pb_cols")

    self.chk_B1 = ctk.CTkCheckBox(row3_frame, text="PB 20", variable=self.var_B1, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
    self.chk_B1.grid(row=0, column=0, sticky="w")

    self.chk_B2 = ctk.CTkCheckBox(row3_frame, text="PB 50", variable=self.var_B2, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
    self.chk_B2.grid(row=0, column=1, sticky="w")

    self.chk_B3 = ctk.CTkCheckBox(row3_frame, text="PB 80", variable=self.var_B3, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
    self.chk_B3.grid(row=0, column=2, sticky="w")

    # HẰNG 4 (PB 110, PB 140)
    row4_frame = ctk.CTkFrame(body_B, fg_color="transparent")
    row4_frame.grid(row=4, column=0, sticky="ew")
    row4_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="pb_cols")

    self.chk_B4 = ctk.CTkCheckBox(row4_frame, text="PB 110", variable=self.var_B4, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
    self.chk_B4.grid(row=0, column=0, sticky="w")

    self.chk_B5 = ctk.CTkCheckBox(row4_frame, text="PB 140", variable=self.var_B5, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
    self.chk_B5.grid(row=0, column=1, sticky="w")

    # Placeholder col 2 để cân đối độ rộng tuyệt đối 3 cột với Hàng 3
    ctk.CTkFrame(row4_frame, fg_color="transparent", width=1, height=1).grid(row=0, column=2, sticky="nsew")


# =========================================================================
# PHẦN 2: MÃ NGUỒN LOGIC THỰC THI CARD B (PHỤ BẢN ĐƠN / ĐỘI)
# =========================================================================
def execute_card_B_phu_ban_doi(self, dnconsole_path: str, tab_name: str, tab_index: str):
    """
    Thực thi toàn diện quy trình Card B: Phụ Bản Đơn / Đội
    """
    if not self.var_switch_B.get():
        self.after(0, self.log_info, "ℹ️ [2/6: PHỤ BẢN ĐƠN / ĐỘI] Công tắc ON/OFF đang TẮT -> Bỏ qua.")
        return

    don_active = self.var_B_don.get()
    team_active = self.var_B_doi.get()

    if not don_active and not team_active:
        self.after(0, self.log_info, "ℹ️ [2/6: PHỤ BẢN ĐƠN / ĐỘI] Không có mục Đơn / Tổ Đội nào được chọn -> Tắt công tắc & Bỏ qua.")
        self.after(0, lambda: self.var_switch_B.set(False))
        self.after(0, self.save_config)
        return

    is_doi_direct_mode = team_active and not don_active

    # =========================================================================
    # 📌 VỀ KHU AN TOÀN (SAFE ZONE RETURN)
    # =========================================================================
    if not (is_doi_direct_mode and not don_active):
        # 1. Quét tìm nút Vị Trí (c_vitri.png):
        # Mắt Thần quét ảnh nút login_x.png, nếu thấy sẽ nhấp chọn để đóng bảng quảng cáo/thông báo
        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "👁️ Quét tìm nút 'login_x.png' (ROI 990,50,1165,200) để đóng bảng quảng cáo/thông báo...")
        lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(990, 50, 1165, 200))
        if lx_x is not None and lx_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'login_x.png' tại ({lx_x}, {lx_y})! Click chọn để đóng quảng cáo/thông báo ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
            time.sleep(0.4)

        # Quét Mắt Thần OpenCV tìm c_vitri.png (độ chính xác 85%, ROI 735,405,1280,720)
        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "👁️ [Phụ Bản - Về Khu An Toàn] Quét tìm nút Vị Trí 'c_vitri.png' (85%, ROI 735,405,1280,720)...")
        v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
        if v_x is not None and v_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'c_vitri.png' tại ({v_x}, {v_y})! Tap click trực tiếp ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "👉 Chưa thấy 'c_vitri.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
            if self._should_stop_card_B(): return
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút 'c_vitri.png' tại ({v_x}, {v_y})! Tap click trực tiếp ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'c_vitri.png' trong bảng menu.")

        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "👉 Click liên tục (435, 250) mỗi 0.5s cho đến khi xuất hiện nút Có 'card_a/a_co.png' (85%, ROI 275,540,1150,670)...")

        while not self._should_stop_card_B():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_co.png", threshold=0.85, region=(275, 540, 1150, 670))
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút Có 'card_a/a_co.png' tại ({co_x}, {co_y})! Dừng click (435, 250).")
                break
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 435 250"])
            time.sleep(0.5)

        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "👁️ Click liên tục nút Có 'card_a/a_co.png' (0.5s mỗi lần) cho tới khi hết ảnh...")
        while not self._should_stop_card_B():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_co.png", threshold=0.85, region=(275, 540, 1150, 670))
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút Có 'card_a/a_co.png' tại ({co_x}, {co_y}) ➔ Click vào vị trí ảnh...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {co_x} {co_y}"])
                time.sleep(0.5)
            else:
                self.after(0, self.log_info, "ℹ️ Không còn thấy ảnh nút Có 'card_a/a_co.png' ➔ Hoàn thành Về Khu An Toàn!")
                break

        # Quét Mắt Thần nút c_vitri.png (85%): Hoãn 3.0s trước khi kiểm tra lại
        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "⏳ [Về Khu An Toàn] Hoãn 3.0s trước khi quét kiểm tra lại nút 'c_vitri.png'...")
        time.sleep(3.0)

        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "👁️ Quét Mắt Thần kiểm tra nút 'c_vitri.png' (85%, ROI 735,405,1280,720)...")
        v_check_x, v_check_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
        if v_check_x is not None and v_check_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'c_vitri.png' tại ({v_check_x}, {v_check_y}) ➔ Click (1213, 648) thu gọn/mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "ℹ️ Không thấy nút 'c_vitri.png' ➔ Bỏ qua.")

    # ---------------- 1. XỬ LÝ MỤC PHỤ BẢN ĐƠN (CÁ NHÂN) ----------------
    if don_active:
        if self._should_stop_card_B(): return
        selected_char_don = self.combo_B_don_char.get() if hasattr(self, 'combo_B_don_char') else "Xuất Chiến"
        self.after(0, self.log_info, f"⚙️ [Phụ Bản Đơn] Bắt đầu quy trình ô Cá Nhân - Vị trí: '{selected_char_don}' ➔ Hoãn 0.4s...")
        time.sleep(0.4)

        # --- Bước 1: Tìm ảnh b_doi.png (Nếu 'Xuất Chiến' được chọn -> BỎ QUA Bước 1) ---
        if selected_char_don != "Xuất Chiến":
            if self._should_stop_card_B(): return
            self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 1] Quét tìm ảnh 'b_doi.png' (ROI 735,405,1280,720)...")
            b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(735, 405, 1280, 720))
            if b_doi_x is not None and b_doi_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "👉 Chưa thấy 'b_doi.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(0.4)
                if self._should_stop_card_B(): return
                b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(735, 405, 1280, 720))
                if b_doi_x is not None and b_doi_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                    time.sleep(0.4)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_doi.png' trong bảng menu.")
        else:
            self.after(0, self.log_info, "ℹ️ Vị trí 'Xuất Chiến' được chọn ➔ Bỏ qua Bước 1 (không click 'b_doi.png').")

        # --- Bước 2: Thao tác theo từng vị trí trong Menu thả xuống ---
        if self._should_stop_card_B(): return
        self.after(0, self.log_info, f"⚙️ [Phụ Bản Đơn - Bước 2] Chế độ vị trí chọn: '{selected_char_don}'")
        if selected_char_don == "Xuất Chiến":
            self.after(0, self.log_info, "ℹ️ Vị trí 'Xuất Chiến': Không có hành động ở Bước 2, chuyển tiếp xuống Bước 3.")
        elif selected_char_don == "Vị Trí 1":
            self.after(0, self.log_info, "👉 [Vị Trí 1] Click (560, 340) ➔ (560, 255) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
            time.sleep(0.5)
        elif selected_char_don == "Vị Trí 2":
            self.after(0, self.log_info, "👉 [Vị Trí 2] Click (560, 255) ➔ (560, 340) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
            time.sleep(0.5)
        elif selected_char_don == "Vị Trí 3":
            self.after(0, self.log_info, "👉 [Vị Trí 3] Click (560, 255) ➔ (560, 430) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 430"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
            time.sleep(0.5)
        elif selected_char_don == "Vị Trí 4":
            self.after(0, self.log_info, "👉 [Vị Trí 4] Click (560, 255) ➔ (560, 520) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
            time.sleep(0.5)

        # --- Bước 3: Tìm ảnh b_pb.png (trong folder card_b) & click tọa độ ---
        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 3] Quét tìm ảnh 'b_pb.png' (ROI 735,405,1280,720)...")
        b_pb_x, b_pb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85, region=(735, 405, 1280, 720))
        if b_pb_x is not None and b_pb_y is not None:
            self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_pb.png' tại ({b_pb_x}, {b_pb_y})! Click vào ảnh ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x} {b_pb_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "👉 Chưa thấy 'b_pb.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
            if self._should_stop_card_B(): return
            b_pb_x, b_pb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85, region=(735, 405, 1280, 720))
            if b_pb_x is not None and b_pb_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_pb.png' tại ({b_pb_x}, {b_pb_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x} {b_pb_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_pb.png' trong bảng menu.")

        # --- Quét card_b/b_lsknn.png khi hoàn thành các thao tác Quét card_b/b_pb.png ---
        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 3] Quét kiểm tra ảnh 'card_b/b_lsknn.png' (ROI 165,170,1110,615)...")
        lsknn_x, lsknn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_lsknn.png", threshold=0.85, region=(165, 170, 1110, 615))
        if lsknn_x is not None and lsknn_y is not None:
            self.after(0, self.log_info, f"🎯 Khớp ảnh 'b_lsknn.png' tại ({lsknn_x}, {lsknn_y}) ➔ Click tọa độ (350, 585) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 350 585"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "ℹ️ Không khớp ảnh 'b_lsknn.png' ➔ Bỏ qua.")

        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 3] Quét & tap ảnh 'card_b/b_pbdon.png' (85%, ROI 165,170,1110,615) ➔ Hoãn 0.4s...")
        while not self._should_stop_card_B():
            pbdon_x, pbdon_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pbdon.png", threshold=0.85, region=(165, 170, 1110, 615))
            if pbdon_x is not None and pbdon_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_pbdon.png' tại ({pbdon_x}, {pbdon_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {pbdon_x} {pbdon_y}"])
                time.sleep(0.4)
                break
            time.sleep(0.3)

        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "👉 Click tiếp tọa độ (775, 575) ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 775 575"])
        time.sleep(0.4)

        # --- Quét nhận diện Xác Nhận: card_b/b_xn.png (Chờ 5s & Quét liên tục tới khi thấy) ---
        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "⏳ [Phụ Bản Đơn - Bước 3] Chờ 5 giây trước khi quét tìm nút Xác Nhận...")
        for _ in range(5):
            if self._should_stop_card_B(): return
            time.sleep(1.0)

        self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 3] Quét tìm ảnh mẫu 'card_b/b_xn.png' (ROI 165,170,1110,615)...")
        xn_x, xn_y = None, None
        while not self._should_stop_card_B():
            xn_x, xn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_xn.png", threshold=0.85, region=(165, 170, 1110, 615))
            if xn_x is not None and xn_y is not None:
                break
            self.after(0, self.log_info, "⏳ Chưa phát hiện 'card_b/b_xn.png' ➔ Tiếp tục quét lại sau 1.5s...")
            time.sleep(1.5)

        if self._should_stop_card_B(): return

        if xn_x is not None and xn_y is not None:
            self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_xn.png' tại ({xn_x}, {xn_y}) ➔ Click 2 lần (cách nhau 0.8s) vào ảnh 'b_xn.png' ➔ Tạm dừng 3.0s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x} {xn_y}"])
            time.sleep(0.8)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x} {xn_y}"])
            time.sleep(3.0)

        # --- Bước 4: Quy trình Bước 4 (Bỏ 4.1 và 4.2) ---
        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "🚀 [Phụ Bản Đơn - Bước 4] Khởi chạy Bước 4...")

        # 4.3: Quét nhận diện Phụ Bản & Vào màn
        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 4.3] Quét tìm ảnh 'b_pb.png' (ROI 735,405,1280,720)...")
        b_pb_x4, b_pb_y4 = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85, region=(735, 405, 1280, 720))
        if b_pb_x4 is not None and b_pb_y4 is not None:
            self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_pb.png' tại ({b_pb_x4}, {b_pb_y4})! Click vào ảnh ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x4} {b_pb_y4}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "👉 Chưa thấy 'b_pb.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
            if self._should_stop_card_B(): return
            b_pb_x4, b_pb_y4 = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85, region=(735, 405, 1280, 720))
            if b_pb_x4 is not None and b_pb_y4 is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_pb.png' tại ({b_pb_x4}, {b_pb_y4})! Click vào ảnh ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x4} {b_pb_y4}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_pb.png' trong bảng menu.")

        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 4] Quét & tap ảnh 'card_b/b_pbdon.png' (85%, ROI 165,170,1110,615) ➔ Hoãn 0.4s...")
        while not self._should_stop_card_B():
            pbdon4_x, pbdon4_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pbdon.png", threshold=0.85, region=(165, 170, 1110, 615))
            if pbdon4_x is not None and pbdon4_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_pbdon.png' tại ({pbdon4_x}, {pbdon4_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {pbdon4_x} {pbdon4_y}"])
                time.sleep(0.4)
                break
            time.sleep(0.3)

        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "👉 Click tiếp tọa độ (640, 575) ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 640 575"])
        time.sleep(0.4)

        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "👉 Click nút thực thi tại tọa độ (775, 575) ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 775 575"])
        time.sleep(0.4)

        # 4.4: Chờ 5 giây (có kiểm tra trạng thái dừng)
        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "⏳ [Phụ Bản Đơn - Bước 4.4] Chờ 5 giây nạp trận đánh...")
        for _ in range(5):
            if self._should_stop_card_B(): return
            time.sleep(1.0)

        # 4.5: Vòng lặp quét liên tục ảnh card_b/b_xn.png cho tới khi tìm thấy (mỗi 1.5s)
        if self._should_stop_card_B(): return
        self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 4.5] Quét tìm ảnh mẫu 'card_b/b_xn.png' (ROI 165,170,1110,615)...")
        xn_x4, xn_y4 = None, None
        while not self._should_stop_card_B():
            xn_x4, xn_y4 = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_xn.png", threshold=0.85, region=(165, 170, 1110, 615))
            if xn_x4 is not None and xn_y4 is not None:
                break
            self.after(0, self.log_info, "⏳ Chưa phát hiện 'card_b/b_xn.png' ➔ Tiếp tục quét lại sau 1.5s...")
            time.sleep(1.5)

        if self._should_stop_card_B(): return

        if xn_x4 is not None and xn_y4 is not None:
            self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_xn.png' tại ({xn_x4}, {xn_y4}) ➔ Click 2 lần (cách nhau 0.5s) vào ảnh 'b_xn.png'...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x4} {xn_y4}"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x4} {xn_y4}"])
            time.sleep(3.0)
    else:
        self.after(0, self.log_info, "ℹ️ [Phụ Bản Đơn] Ô check 'Đơn' KHÔNG ĐƯỢC TÍCH (OFF) -> Bỏ qua không chạy Phụ Bản Đơn.")

    # ---------------- 2. XỬ LÝ MỤC PHỤ BẢN ĐỘI (PB 20 - PB 140) ----------------
    dungeons_to_run = [
        ("PB 20", self.var_B1, "card_b/b_pb20.png", "card_b/b_pb20map.png", 60),
        ("PB 50", self.var_B2, "card_b/b_pb50.png", "card_b/b_pb50map.png", 120),
        ("PB 80", self.var_B3, "card_b/b_pb80.png", "card_b/b_pb80map.png", 180),
        ("PB 110", self.var_B4, "card_b/b_pb110.png", "card_b/b_pb110map.png", 240),
        ("PB 140", self.var_B5, "card_b/b_pb140.png", "card_b/b_pb140map.png", 300)
    ]

    any_pb_checked = any(var_pb.get() for _, var_pb, _, _, _ in dungeons_to_run)
    team_mode_active = self.var_B_doi.get()

    if team_mode_active:
        if any_pb_checked:
            if self._should_stop_card_B(): return
            selected_char_team = self.combo_B_team_char.get() if hasattr(self, 'combo_B_team_char') else "Xuất Chiến"
            self.after(0, self.log_info, f"⚙️ [Phụ Bản Đội - Tổ Đội] Kích hoạt quy trình Phụ Bản Đội (Vị trí: '{selected_char_team}')...")

            # --- Bước 1: Mở Menu & Quét chọn Đội (Nếu 'Xuất Chiến' được chọn -> BỎ QUA Bước 1) ---
            if selected_char_team != "Xuất Chiến":
                if self._should_stop_card_B(): return
                self.after(0, self.log_info, "👁️ [Phụ Bản Đội - Bước 1] Quét tìm ảnh 'b_doi.png' (ROI 735,405,1280,720)...")
                b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(735, 405, 1280, 720))
                if b_doi_x is not None and b_doi_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện 'b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                    time.sleep(0.4)
                else:
                    self.after(0, self.log_info, "👉 Chưa thấy 'b_doi.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                    time.sleep(0.4)
                    if self._should_stop_card_B(): return
                    b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(735, 405, 1280, 720))
                    if b_doi_x is not None and b_doi_y is not None:
                        self.after(0, self.log_info, f"🎯 Phát hiện 'b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                        time.sleep(0.4)
                    else:
                        self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_doi.png' trong bảng menu.")
            else:
                self.after(0, self.log_info, "ℹ️ Vị trí 'Xuất Chiến' được chọn ➔ Bỏ qua Bước 1 (không click 'b_doi.png').")

            # --- Bước 2: Chuyển đổi Vị Trí Nhân Vật ---
            if self._should_stop_card_B(): return
            self.after(0, self.log_info, f"⚙️ [Phụ Bản Đội - Bước 2] Chế độ vị trí chọn: '{selected_char_team}'")
            if selected_char_team == "Xuất Chiến":
                self.after(0, self.log_info, "ℹ️ Vị trí 'Xuất Chiến': Không có hành động ở Bước 2, chuyển tiếp xuống Bước 3.")
            elif selected_char_team == "Vị Trí 1":
                self.after(0, self.log_info, "👉 [Vị Trí 1] Click (560, 340) ➔ (560, 255) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.5)
            elif selected_char_team == "Vị Trí 2":
                self.after(0, self.log_info, "👉 [Vị Trí 2] Click (560, 255) ➔ (560, 340) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.5)
            elif selected_char_team == "Vị Trí 3":
                self.after(0, self.log_info, "👉 [Vị Trí 3] Click (560, 255) ➔ (560, 430) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 430"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.5)
            elif selected_char_team == "Vị Trí 4":
                self.after(0, self.log_info, "👉 [Vị Trí 4] Click (560, 255) ➔ (560, 520) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.5)

            # --- Bước 3: Mở Phụ Bản & Vào Phụ Bản cho từng ô tích PB 20..140 ---
            for pb_name, var_pb, pb_tmpl, pb_map_tmpl, delay_sec in dungeons_to_run:
                if var_pb.get():
                    if self._should_stop_card_B(): return
                    self.after(0, self.log_info, f"🚀 [Phụ Bản Đội - {pb_name}] Kích hoạt quy trình cho ô tích '{pb_name}'...")

                    # 1. Quét tìm card_b/b_pb.png (ROI 735,405,1280,720)
                    b_pb_x, b_pb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85, region=(735, 405, 1280, 720))
                    if b_pb_x is not None and b_pb_y is not None:
                        self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_pb.png' tại ({b_pb_x}, {b_pb_y})! Click chọn ➔ Hoãn 0.4s...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x} {b_pb_y}"])
                        time.sleep(0.4)
                    else:
                        self.after(0, self.log_info, "👉 Chưa thấy 'b_pb.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                        time.sleep(0.4)
                        if self._should_stop_card_B(): return
                        b_pb_x, b_pb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85, region=(735, 405, 1280, 720))
                        if b_pb_x is not None and b_pb_y is not None:
                            self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_pb.png' tại ({b_pb_x}, {b_pb_y})! Click chọn ➔ Hoãn 0.4s...")
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x} {b_pb_y}"])
                            time.sleep(0.4)
                        else:
                            self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_pb.png' trong bảng menu.")

                    if self._should_stop_card_B(): return
                    # 2. Quét / tap ảnh card_b/b_pbXX.png (85%, ROI 165,170,1110,615) ➔ Click (735, 575)
                    self.after(0, self.log_info, f"👁️ [Phụ Bản Đội - {pb_name}] Quét & tap ảnh '{pb_tmpl}' (85%, ROI 165,170,1110,615)...")
                    while not self._should_stop_card_B():
                        p_x, p_y = self._find_template_on_screen(dnconsole_path, tab_index, pb_tmpl, threshold=0.85, region=(165, 170, 1110, 615))
                        if p_x is not None and p_y is not None:
                            self.after(0, self.log_info, f"🎯 Phát hiện '{pb_tmpl}' tại ({p_x}, {p_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {p_x} {p_y}"])
                            time.sleep(0.4)
                            break
                        time.sleep(0.3)

                    if self._should_stop_card_B(): return
                    self.after(0, self.log_info, "👉 Click tiếp tọa độ (735, 575) ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 735 575"])
                    time.sleep(0.4)
                    # 4. Xử lý Mật Khẩu phòng (Dùng thao tác của ô Cá Nhân làm chuẩn cho cả ô Tổ Đội)
                    if self._should_stop_card_B(): return
                    self.after(0, self.log_info, "👁️ Quét tìm ảnh mẫu 'card_b/b_matkhau.png' (85%, ROI 165,170,1110,615)...")
                    mk_x, mk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_matkhau.png", threshold=0.85, region=(165, 170, 1110, 615))
                    if mk_x is not None and mk_y is not None:
                        self.after(0, self.log_info, f"🎯 Khớp ảnh 'b_matkhau.png' tại ({mk_x}, {mk_y}) ➔ Click chọn ảnh ➔ Click (640, 435) khóa mật khẩu (Hoãn 0.4s)...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {mk_x} {mk_y}"])
                        time.sleep(0.4)
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 640 435"])
                        time.sleep(0.4)
                    else:
                        self.after(0, self.log_info, "ℹ️ Không thấy 'b_matkhau.png' ➔ Tap (640, 435) để hoàn tất ➔ Hoãn 0.4s...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 640 435"])
                        time.sleep(0.4)

                    # --- GỌI THAO TÁC CARD TỔ ĐỘI ---
                    if hasattr(self, 'var_B_doi') and self.var_B_doi.get():
                        if self._should_stop_card_B(): return
                        self.after(0, self.log_info, "👥 [Phụ Bản Đội - Ô Tổ Đội] Gọi thao tác Card Tổ Đội (_run_card_B_action_2) & ĐỢI HOÀN THÀNH 100%...")
                        self._execute_card_E_for_mode(dnconsole_path, tab_name, tab_index, mode=2)

                    # --- BƯỚC 4: VÀO TRẬN & ĐÁNH TRẬN PHỤ BẢN ĐỘI ---
                    if self._should_stop_card_B(): return
                    self.after(0, self.log_info, "👁️ Quét chờ nút Bắt Đầu 'card_b/b_batdau.png' (85%, ROI 165,170,1110,615) xuất hiện...")
                    has_seen_bd = False
                    while not self._should_stop_card_B():
                        bd_x, bd_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_batdau.png", threshold=0.85, region=(165, 170, 1110, 615))
                        if bd_x is not None and bd_y is not None:
                            has_seen_bd = True
                            break
                        time.sleep(0.5)

                    if has_seen_bd and not self._should_stop_card_B():
                        self.after(0, self.log_info, "🎯 Đã thấy 'card_b/b_batdau.png' ➔ Tap liên tục 0.5s/lần cho đến khi mất ảnh (Vào trận)...")
                        while not self._should_stop_card_B():
                            bd_x, bd_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_batdau.png", threshold=0.85, region=(165, 170, 1110, 615))
                            if bd_x is None or bd_y is None:
                                self.after(0, self.log_info, "ℹ️ Đã mất ảnh 'card_b/b_batdau.png' (Vào trận thành công) ➔ Tiếp tục thao tác tiếp theo.")
                                break
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {bd_x} {bd_y}"])
                            time.sleep(0.5)

                    if self._should_stop_card_B(): return
                    self.after(0, self.log_info, f"⏳ [{pb_name}] Chờ 3.5s nạp trận...")
                    for _ in range(7):
                        if self._should_stop_card_B(): return
                        time.sleep(0.5)

                    if self._should_stop_card_B(): return
                    self.after(0, self.log_info, f"⏳ [{pb_name}] Chờ {delay_sec}s ➔ Tap liên tục nút Auto (1165, 210) mỗi 0.2s...")
                    start_wait = time.time()
                    while time.time() - start_wait < delay_sec:
                        if self._should_stop_card_B(): return
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1165 210"])
                        time.sleep(0.2)

                    if self._should_stop_card_B(): return
                    self.after(0, self.log_info, f"👁️ [{pb_name}] Hết {delay_sec}s ➔ Duy trì tap Auto (1165, 210) mỗi 0.2s & quét tìm nút Xác Nhận 'card_b/b_xn.png' (85%, ROI 165,170,1110,615) mỗi 3s...")
                    xn_x, xn_y = None, None
                    while not self._should_stop_card_B():
                        xn_x, xn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_xn.png", threshold=0.85, region=(165, 170, 1110, 615))
                        if xn_x is not None and xn_y is not None:
                            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện ảnh 'card_b/b_xn.png' tại ({xn_x}, {xn_y})!")
                            break

                        start_sub = time.time()
                        while time.time() - start_sub < 3.0:
                            if self._should_stop_card_B(): break
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1165 210"])
                            time.sleep(0.2)

                    if self._should_stop_card_B(): return
                    if xn_x is not None and xn_y is not None:
                        self.after(0, self.log_info, f"👉 Tap nhấp chọn ảnh Xác Nhận 'card_b/b_xn.png' tại ({xn_x}, {xn_y}) để hoàn thành {pb_name}...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x} {xn_y}"])

                    # Khi hoàn thành 1 mốc Phụ Bản -> hoãn 3.0s để tiếp tục mốc Phụ Bản tiếp theo
                    if self._should_stop_card_B(): return
                    self.after(0, self.log_info, f"⏳ [{pb_name}] Hoàn thành mốc {pb_name}! Hoãn 3.0s để tiếp tục mốc Phụ Bản tiếp theo...")
                    time.sleep(3.0)
        else:
            # --- TRƯỜNG HỢP: Ô ĐỘI ĐƯỢC TÍCH NHƯNG CÁC Ô PB KHÔNG ĐƯỢC TÍCH ---
            if self._should_stop_card_B(): return
            self.after(0, self.log_info, "⚙️ [Phụ Bản Đội - Hỗ Trợ] Ô Đội được tích nhưng các ô PB KHÔNG được tích ➔ Bỏ qua tạo phòng & mời đội, chạy riêng thao tác Bắt Đầu & Đánh Phụ Bản...")

            # 1. Vào trận: Quét chờ xuất hiện nút Bắt Đầu 'card_b/b_batdau.png' (85%, ROI 165,170,1110,615) xuất hiện...")
            has_seen_bd = False
            while not self._should_stop_card_B():
                bd_x, bd_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_batdau.png", threshold=0.85, region=(165, 170, 1110, 615))
                if bd_x is not None and bd_y is not None:
                    has_seen_bd = True
                    break
                time.sleep(0.5)

            if has_seen_bd and not self._should_stop_card_B():
                self.after(0, self.log_info, "🎯 Đã thấy 'card_b/b_batdau.png' ➔ Tap liên tục 0.5s/lần cho đến khi mất ảnh (Vào trận thành công)...")
                while not self._should_stop_card_B():
                    bd_x, bd_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_batdau.png", threshold=0.85, region=(165, 170, 1110, 615))
                    if bd_x is None or bd_y is None:
                        self.after(0, self.log_info, "ℹ️ Đã mất ảnh 'card_b/b_batdau.png' (Vào trận thành công) ➔ Tiếp tục thao tác tiếp theo.")
                        break
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {bd_x} {bd_y}"])
                    time.sleep(0.5)

            # 2. Đánh trận & Nạp thời gian: Chờ 3.5s nạp trận & quét nhận diện 1 trong 5 ảnh map PB
            if self._should_stop_card_B(): return
            self.after(0, self.log_info, "⏳ Chờ 3.5s nạp trận & quét nhận diện 1 trong 5 ảnh map Phụ Bản (PB 20 ➔ PB 140, ROI 1060,0,1280,40)...")

            detected_pb_name = None
            detected_delay_sec = 0

            map_to_dungeon_info = [
                ("card_b/b_pb20map.png", "PB 20", 60),
                ("card_b/b_pb50map.png", "PB 50", 120),
                ("card_b/b_pb80map.png", "PB 80", 180),
                ("card_b/b_pb110map.png", "PB 110", 240),
                ("card_b/b_pb140map.png", "PB 140", 300),
            ]

            start_wait_nap = time.time()
            while time.time() - start_wait_nap < 3.5:
                if self._should_stop_card_B(): return
                if detected_pb_name is None:
                    for map_tmpl, p_name, d_sec in map_to_dungeon_info:
                        mx, my = self._find_template_on_screen(dnconsole_path, tab_index, map_tmpl, threshold=0.80, region=(1060, 0, 1280, 40))
                        if mx is not None and my is not None:
                            detected_pb_name = p_name
                            detected_delay_sec = d_sec
                            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện map '{map_tmpl}' ➔ Nhận diện mốc: {detected_pb_name} (Thời gian chờ: {detected_delay_sec}s)!")
                            break
                time.sleep(0.5)

            if self._should_stop_card_B(): return

            # --- XỬ LÝ THEO 2 NHÁNH ---
            if detected_pb_name is not None:
                # NHÁNH 1: Phát hiện ra mốc PB cụ thể ➔ Kích hoạt thao tác Đánh trận & Duy trì Auto của mốc PB đó
                self.after(0, self.log_info, f"⏳ [Hỗ Trợ - {detected_pb_name}] Chờ {detected_delay_sec}s ➔ Tap liên tục nút Auto (1165, 210) mỗi 0.2s...")
                start_wait = time.time()
                while time.time() - start_wait < detected_delay_sec:
                    if self._should_stop_card_B(): return
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1165 210"])
                    time.sleep(0.2)

                if self._should_stop_card_B(): return
                self.after(0, self.log_info, f"👁️ [Hỗ Trợ - {detected_pb_name}] Hết {detected_delay_sec}s ➔ Duy trì tap Auto (1165, 210) mỗi 0.2s & quét tìm nút Xác Nhận 'card_b/b_xn.png' (85%, ROI 165,170,1110,615) mỗi 3s...")
                xn_x, xn_y = None, None
                while not self._should_stop_card_B():
                    xn_x, xn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_xn.png", threshold=0.85, region=(165, 170, 1110, 615))
                    if xn_x is not None and xn_y is not None:
                        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện ảnh 'card_b/b_xn.png' tại ({xn_x}, {xn_y})!")
                        break

                    start_sub = time.time()
                    while time.time() - start_sub < 3.0:
                        if self._should_stop_card_B(): break
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1165 210"])
                        time.sleep(0.2)

                if self._should_stop_card_B(): return
                if xn_x is not None and xn_y is not None:
                    self.after(0, self.log_info, f"👉 Tap nhấp chọn ảnh Xác Nhận 'card_b/b_xn.png' tại ({xn_x}, {xn_y}) để hoàn thành {detected_pb_name}...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x} {xn_y}"])
            else:
                # NHÁNH 2: KHÔNG phát hiện ra ảnh map nào ➔ Kích hoạt Tap Auto cố định mỗi 0.2s & quét b_xn.png mỗi 3s
                self.after(0, self.log_info, "ℹ️ [Hỗ Trợ] Không phát hiện ảnh map mốc PB nào ➔ Kích hoạt Tap Auto (1165, 210) mỗi 0.2s & quét nút Xác Nhận 'card_b/b_xn.png' (85%, ROI 165,170,1110,615) mỗi 3s...")
                xn_x, xn_y = None, None
                while not self._should_stop_card_B():
                    xn_x, xn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_xn.png", threshold=0.85, region=(165, 170, 1110, 615))
                    if xn_x is not None and xn_y is not None:
                        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện ảnh 'card_b/b_xn.png' tại ({xn_x}, {xn_y})!")
                        break

                    start_sub = time.time()
                    while time.time() - start_sub < 3.0:
                        if self._should_stop_card_B(): break
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1165 210"])
                        time.sleep(0.2)

                if self._should_stop_card_B(): return
                if xn_x is not None and xn_y is not None:
                    self.after(0, self.log_info, f"👉 Tap nhấp chọn ảnh Xác Nhận 'card_b/b_xn.png' tại ({xn_x}, {xn_y}) để hoàn thành...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x} {xn_y}"])

            if self._should_stop_card_B(): return
            self.after(0, self.log_info, "⏳ Hoàn thành Phụ Bản Đội Hỗ Trợ! Hoãn 3.0s...")
            time.sleep(3.0)

    # ---------------- 3. TỰ ĐỘNG TẮT CÔNG TẮC & LƯU CẤU HÌNH (GIỮ NGUYÊN Ô TÍCH) ----------------
    self.after(0, lambda: self.var_switch_B.set(False))
    self.after(0, self.save_config)
    self.after(0, self.log_info, "✅ [1/6: PHỤ BẢN ĐƠN / ĐỘI] Đã thực thi hoàn tất! (Tự động tắt công tắc ON/OFF & giữ nguyên các ô tích)")
