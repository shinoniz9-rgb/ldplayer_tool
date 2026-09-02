# -*- coding: utf-8 -*-
"""
========================================================================================
🔒 [BẢN BACKUP THAM CHIẾU ĐỘC LẬP & KHÓA NGUYÊN BẢN]: CARD E (QUẢN LÝ TỔ ĐỘI)
========================================================================================
Ngày tạo: 2026-09-02
Mục đích:
- Lưu trữ độc lập toàn bộ giao diện và logic thực thi của Card E (Quản Lý Tổ Đội).
- Mã nguồn này đã được tối ưu hóa toàn bộ 100% vùng ROI cho ảnh nhân vật và ảnh điều khiển.
- Độc lập 100% với các chỉnh sửa phát sinh sau này trên file main.py.

========================================================================================
📌 BẢNG TRA CỨU TỌA ĐỘ VÙNG QUÉT ROI & NGƯỠNG THRESHOLD CARD E
========================================================================================
1. login_x.png                : (990, 50, 1165, 200)    - Threshold: 0.75 (75%) [Đóng quảng cáo/thông báo]
2. b_doi.png                  : (735, 405, 1280, 720)   - Threshold: 0.85 (85%) [Mở giao diện Đội ngoài bản đồ]
3. e_nguoi.png                : (175, 165, 295, 455)    - Threshold: 0.85 (85%) [Nút mở danh sách mời hảo hữu Thao tác 1]
4. e_doingu.png               : (175, 165, 295, 455)    - Threshold: 0.85 (85%) [Nút quay lại Đội Ngũ Thao tác 1]
5. e_moi.png                  : (175, 165, 1105, 605)   - Threshold: 0.85 (85%) [Nút Mời trong phòng Phụ Bản Đội Thao tác 2]
6. nhanvat/40npc2k/{char}.png : (305, 150, 1105, 625)   - Threshold: 0.80 (80%) [Nhận diện thành viên & Quân Sư Thao tác 1]
7. nhanvat/pbdoi/{char}.png   : (175, 165, 1105, 605)   - Threshold: 0.80 (80%) [Nhận diện thành viên Phụ Bản Đội Thao tác 2]
8. nhanvat/{char}.png         : (305, 150, 1105, 625) (40NPC) / (175, 165, 1105, 605) (PB Đội) - Threshold: 0.80 (80%)
========================================================================================
"""

import time
import customtkinter as ctk

# =========================================================================
# PHẦN 1: MÃ NGUỒN GIAO DIỆN DESKTOP (GUI) CỦA CARD E
# =========================================================================
def build_card_E_ui(self, tab_team):
    """
    Xây dựng giao diện Card E (Quản Lý Tổ Đội) trên Desktop GUI
    Đặt tại TAB: 👥 Quản Lý Tổ Đội
    """
    # ------------------- CARD E: TỔ ĐỘI (Đặt ở TAB: 👥 Quản Lý Tổ Đội) -------------------
    self.card_E = ctk.CTkFrame(tab_team, corner_radius=10)
    self.card_E.pack(fill="both", expand=True, padx=6, pady=6)
    self.card_E.grid_columnconfigure(0, weight=1)
    self.card_E.grid_rowconfigure(0, weight=0)
    self.card_E.grid_rowconfigure(1, weight=0)
    self.card_E.grid_rowconfigure(2, weight=1)

    hdr_E = ctk.CTkFrame(self.card_E, fg_color="transparent")
    hdr_E.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="ew")
    hdr_E.grid_columnconfigure(0, weight=1)

    self.lbl_E = ctk.CTkLabel(hdr_E, text="QUẢN LÝ TỔ ĐỘI", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#38BDF8")
    self.lbl_E.grid(row=0, column=0, sticky="w")

    # HÀNG 1: [ ] Quân Sư | [ Menu Dropdown Chọn Tên Thành Viên ]
    row_E1 = ctk.CTkFrame(self.card_E, fg_color="transparent")
    row_E1.grid(row=1, column=0, padx=6, pady=4, sticky="ew")

    self.chk_E_quan_su = ctk.CTkCheckBox(
        row_E1, text="Quân Sư", variable=self.var_E_quan_su, command=self._on_checkbox_toggled,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
        fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF",
        checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
    )
    self.chk_E_quan_su.pack(side="left", padx=(4, 0))

    qs_opts = self._get_quan_su_options()
    self.combo_E_quan_su = ctk.CTkOptionMenu(
        row_E1,
        values=qs_opts,
        font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
        dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
        text_color="#FFFFFF",
        dropdown_text_color="#FFFFFF",
        height=25,
        width=130,
        dynamic_resizing=False,
        fg_color="#374151",
        button_color="#4B5563",
        button_hover_color="#6B7280",
        command=lambda choice: self._on_checkbox_toggled()
    )
    self.combo_E_quan_su.set(qs_opts[0] if qs_opts else "(Trống)")
    self.combo_E_quan_su.pack(side="right", padx=(0, 4))

    # HÀNG 2: Khung chứa 2 Bảng danh sách A - B và Nút Mũi Tên ➔ ở giữa
    body_E = ctk.CTkFrame(self.card_E, fg_color="transparent")
    body_E.grid(row=2, column=0, padx=6, pady=(4, 8), sticky="nsew")
    body_E.grid_columnconfigure(0, weight=1)
    body_E.grid_columnconfigure(1, weight=0)
    body_E.grid_columnconfigure(2, weight=1)
    body_E.grid_rowconfigure(0, weight=1)

    # 1. Bảng [Danh Sách A] bên trái (Tướng Có Sẵn)
    self.scroll_E_list_A = ctk.CTkScrollableFrame(
        body_E,
        fg_color="#1F2937",
        corner_radius=8,
        scrollbar_button_color="#4B5563",
        scrollbar_button_hover_color="#6B7280"
    )
    self.scroll_E_list_A.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
    self.scroll_E_list_A.grid_columnconfigure(0, weight=1)

    # 2. Khung ở giữa chứa Nút Mũi Tên ➔
    frame_mid_E = ctk.CTkFrame(body_E, fg_color="transparent")
    frame_mid_E.grid(row=0, column=1, sticky="ns", padx=4)

    self.btn_E_add = ctk.CTkButton(
        frame_mid_E,
        text="➔",
        width=32,
        height=28,
        font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
        text_color="#FFFFFF",
        fg_color="#EA580C",
        hover_color="#C2410C",
        command=self._add_A_to_B_E
    )
    self.btn_E_add.pack(expand=True)

    # 3. Bảng [Danh Sách B] bên phải (Đội Hình)
    self.scroll_E_list_B = ctk.CTkScrollableFrame(
        body_E,
        fg_color="#1F2937",
        corner_radius=8,
        scrollbar_button_color="#4B5563",
        scrollbar_button_hover_color="#6B7280"
    )
    self.scroll_E_list_B.grid(row=0, column=2, sticky="nsew", padx=(4, 0))
    self.scroll_E_list_B.grid_columnconfigure(0, weight=1)

    # Nạp dữ liệu ban đầu cho Danh Sách A và Danh Sách B
    self._render_E_list_A_ui()
    self._render_E_list_B_ui()


# =========================================================================
# PHẦN 2: CÁC HÀM XỬ LÝ DANH SÁCH A & B VÀ QUÂN SƯ
# =========================================================================
def get_quan_su_options(self):
    """Lấy danh sách các nhân vật trong Danh Sách B để nạp vào Menu Quân Sư"""
    b_list = getattr(self, 'list_E_B', [])
    return list(b_list) if b_list else ["(Trống)"]

def update_E_quan_su_options(self):
    """Cập nhật lại danh sách lựa chọn trong Menu dropdown Quân Sư"""
    if not hasattr(self, 'combo_E_quan_su'):
        return
    opts = self._get_quan_su_options()
    self.combo_E_quan_su.configure(values=opts)
    current = self.combo_E_quan_su.get()
    if current not in opts:
        self.combo_E_quan_su.set(opts[0])

def add_A_to_B_E(self):
    """Thêm nhân vật đang chọn từ [Danh Sách A] sang [Danh Sách B] (Tự động ẩn khỏi Danh Sách A)"""
    if not hasattr(self, 'list_E_B'):
        self.list_E_B = []

    char_name = getattr(self, 'selected_E_list_A_char', "")
    if not char_name:
        all_opts = self._get_nhanvat_options()
        avail = [n for n in all_opts if n not in self.list_E_B]
        if avail:
            char_name = avail[0]
            self.selected_E_list_A_char = char_name

    if not char_name or char_name in self.list_E_B:
        return

    self.list_E_B.append(char_name)
    self._render_E_list_B_ui()
    self._render_E_list_A_ui()
    self.save_config()

def remove_B_item_E(self, char_name: str):
    """Xóa nhân vật khỏi [Danh Sách B] bên phải (Tự động hiện lại bên Danh Sách A)"""
    if hasattr(self, 'list_E_B') and char_name in self.list_E_B:
        self.list_E_B.remove(char_name)
        self._render_E_list_B_ui()
        self._render_E_list_A_ui()
        self.save_config()


# =========================================================================
# PHẦN 3: LOGIC KIỂM TRA DỪNG AN TOÀN & THỰC THI CHÍNH
# =========================================================================
def should_stop_card_E(self) -> bool:
    """
    Kiểm tra xem Card E có cần dừng lại hay không:
    - Bị dừng khẩn cấp bởi nút Dừng Tổng (stop_requested).
    - Cả 2 công tắc nguồn (var_D2 và var_B_doi) đều tắt.
    - Xử lý cơ chế Tạm Dừng thông minh khi ô var_pause_D được tích.
    """
    if self.stop_requested:
        return True

    is_d_active = getattr(self, 'var_D2', None) and self.var_D2.get() and getattr(self, 'var_switch_D', None) and self.var_switch_D.get()
    is_b_active = getattr(self, 'var_B_doi', None) and self.var_B_doi.get() and getattr(self, 'var_switch_B', None) and self.var_switch_B.get()

    if not (is_d_active or is_b_active):
        return True

    # Kiểm tra ô Tạm Dừng nếu đang chạy dưới quyền Card D
    if is_d_active and hasattr(self, 'var_pause_D') and self.var_pause_D.get():
        self.after(0, self.log_info, "⏸️ [TỔ ĐỘI] Phát hiện ô Tạm Dừng đang TÍCH ➔ Tạm dừng hoạt động Tổ Đội...")
        while self.var_pause_D.get() and not self.stop_requested and self.var_switch_D.get():
            time.sleep(0.5)
        if not self.stop_requested and self.var_switch_D.get():
            self.after(0, self.log_info, "▶️ [TỔ ĐỘI] Đã nhả ô Tạm Dừng ➔ Khôi phục chạy tiếp Tổ Đội!")
        return self.stop_requested or not self.var_switch_D.get()

    return False


def run_card_E_action_1(self, dnconsole_path: str, tab_index: str, list_B: list):
    """
    THAO TÁC 1 CỦA CARD TỔ ĐỘI:
    Kích hoạt khi ô 'Tổ Đội' ở Card 40NPC / 2K (var_D2) được tích.
    Bổ sung tính năng quản lý danh sách đã mời (already_invited) thông minh.
    """
    if self._should_stop_card_E() or not list_B: return

    self.after(0, self.log_info, f"🚀 [CARD TỔ ĐỘI - Thao Tác 1] Khởi chạy quy trình mời {len(list_B)} nhân vật trong Danh Sách B: {', '.join(list_B)}...")
    already_invited = set()

    # ---------------- GIAI ĐOẠN 1: MỞ GIAO DIỆN TỔ ĐỘI ----------------
    if self._should_stop_card_E(): return
    # 1. Đóng Quảng Cáo / Thông Báo Nổi
    lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(990, 50, 1165, 200))
    if lx_x is not None and lx_y is not None:
        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'login_x.png' tại ({lx_x}, {lx_y})! Tap click ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
        time.sleep(0.4)

    # 2. Quét Mở Giao Diện Đội
    if self._should_stop_card_E(): return
    self.after(0, self.log_info, "👁️ [Thao Tác 1] Quét tìm ảnh 'card_b/b_doi.png' (85%, ROI 735,405,1280,720)...")
    b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(735, 405, 1280, 720))
    if b_doi_x is not None and b_doi_y is not None:
        self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_doi.png' tại ({b_doi_x}, {b_doi_y})! Tap click vào ảnh ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
        time.sleep(0.4)
    else:
        self.after(0, self.log_info, "👉 Chưa thấy 'card_b/b_doi.png' ➔ Tap nút xanh (1213, 648) mở menu ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
        time.sleep(0.4)
        if self._should_stop_card_E(): return
        b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(735, 405, 1280, 720))
        if b_doi_x is not None and b_doi_y is not None:
            self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_doi.png' tại ({b_doi_x}, {b_doi_y})! Tap click vào ảnh ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
            time.sleep(0.4)

    # ---------------- VÒNG LẶP MỜI & KIỂM TRA TỔ ĐỘI ----------------
    while not self._should_stop_card_E():
        # 3. Nhận Diện Người Trong Tổ Đội
        if self._should_stop_card_E(): return
        self.after(0, self.log_info, "👁️ [Thao Tác 1] Quét kiểm tra độ đầy đủ của các nhân vật trong Danh Sách B...")
        all_present = True
        missing_list = []

        for char_name in list_B:
            if self._should_stop_card_E(): return
            chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/40npc2k/{char_name}.png", threshold=0.80, region=(305, 150, 1105, 625))
            if chk_x is None or chk_y is None:
                chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/{char_name}.png", threshold=0.80, region=(305, 150, 1105, 625))

            if chk_x is None or chk_y is None:
                all_present = False
                missing_list.append(char_name)
            else:
                if char_name in already_invited:
                    already_invited.remove(char_name)

        # 4. Xử Lý Kết Quả Kiểm Tra
        if all_present:
            self.after(0, self.log_info, f"✅ [Thao Tác 1] Tổ đội đã ĐỦ 100% thành viên ({', '.join(list_B)})!")

            # Chỉ định Quân Sư: Nếu ô [ ] Quân Sư được tích chọn ➔ Tự động gán nhân vật bạn chọn làm Quân Sư của đội
            if hasattr(self, 'var_E_quan_su') and self.var_E_quan_su.get():
                if self._should_stop_card_E(): return
                quan_su_char = self.combo_E_quan_su.get() if hasattr(self, 'combo_E_quan_su') else ""
                if quan_su_char and quan_su_char != "(Trống)":
                    self.after(0, self.log_info, f"👑 [Quân Sư] Đang quét nhận diện nhân vật Quân Sư '{quan_su_char}' (ROI 305,150,1105,625)...")
                    qs_x, qs_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/40npc2k/{quan_su_char}.png", threshold=0.80, region=(305, 150, 1105, 625))
                    if qs_x is None or qs_y is None:
                        qs_x, qs_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/{quan_su_char}.png", threshold=0.80, region=(305, 150, 1105, 625))

                    if qs_x is not None and qs_y is not None:
                        qs_btn_x = qs_x + 155
                        qs_btn_y = qs_y + 40
                        self.after(0, self.log_info, f"🎯 Phát hiện nhân vật Quân Sư '{quan_su_char}' tại ({qs_x}, {qs_y}) ➔ Click nút Quân Sư ({qs_btn_x}, {qs_btn_y}) ➔ Hoãn 0.5s...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {qs_btn_x} {qs_btn_y}"])
                        time.sleep(0.5)
                    else:
                        self.after(0, self.log_info, f"⚠️ Chưa quét thấy ảnh nhân vật Quân Sư '{quan_su_char}' trên màn hình Đội.")

            # Quét tìm và tap login_x.png (75%, hoãn 0.4s)
            if self._should_stop_card_E(): return
            lx2_x, lx2_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(990, 50, 1165, 200))
            if lx2_x is not None and lx2_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'login_x.png' tại ({lx2_x}, {lx2_y})! Tap click ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx2_x} {lx2_y}"])
                time.sleep(0.4)

            # Mắt thần quét tìm ảnh icon Đội card_b/b_doi.png (85%) ➔ Click nút xanh (1213, 648) thu gọn menu (hoãn 0.4s)
            if self._should_stop_card_E(): return
            b_doi2_x, b_doi2_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(735, 405, 1280, 720))
            if b_doi2_x is not None and b_doi2_y is not None:
                self.after(0, self.log_info, "🎯 Thấy 'card_b/b_doi.png' ➔ Tap nút xanh lá (1213, 648) đóng bảng Menu (hoãn 0.4s)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(0.4)

            self.after(0, self.log_info, "🚀 [Thao Tác 1] Hoàn tất dứt điểm quy trình Tổ Đội ➔ Trả quyền điều khiển cho 40NPC / 2K.")
            break

        else:
            uninvited_missing = list(missing_list)
            self.after(0, self.log_info, f"⚠️ [Thao Tác 1] Đội chưa đủ người (Thiếu: {', '.join(missing_list)}) ➔ Mời ngay toàn bộ thành viên còn thiếu...")

            # Mắt thần quét tìm ảnh / tap card_e/e_nguoi.png (85%, ROI 175,165,295,455) nghỉ 0.4s
            if self._should_stop_card_E(): return
            nguoi_x, nguoi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_e/e_nguoi.png", threshold=0.85, region=(175, 165, 295, 455))
            if nguoi_x is not None and nguoi_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_e/e_nguoi.png' tại ({nguoi_x}, {nguoi_y})! Tap click vào ảnh ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {nguoi_x} {nguoi_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy ảnh 'card_e/e_nguoi.png' trên màn hình.")
                time.sleep(0.4)

            # Dò Tìm Tất Cả Nhân Vật Bị Thiếu Cùng Lúc Trực Tiếp Trên Màn Hình (Chỉ vuốt 1 chu kỳ cho cả danh sách)
            still_missing = list(uninvited_missing)
            
            def scan_and_invite_current_screen(missing_tracker: list) -> list:
                """Mắt thần quét tìm kiếm đồng thời tất cả các nhân vật còn thiếu chưa mời trên màn hình hiện tại"""
                invited_chars = []
                for char_name in list(missing_tracker):
                    if self._should_stop_card_E(): break
                    found_char_x, found_char_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/40npc2k/{char_name}.png", threshold=0.80, region=(305, 150, 1105, 625))
                    if found_char_x is None or found_char_y is None:
                        found_char_x, found_char_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/{char_name}.png", threshold=0.80, region=(305, 150, 1105, 625))

                    if found_char_x is not None and found_char_y is not None:
                        invite_x = found_char_x + 585
                        invite_y = found_char_y
                        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nhân vật '{char_name}' tại ({found_char_x}, {found_char_y})! Tap nút Mời ({invite_x}, {invite_y}) ➔ Hoãn 0.5s...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {invite_x} {invite_y}"])
                        time.sleep(0.5)
                        already_invited.add(char_name)
                        invited_chars.append(char_name)
                for c in invited_chars:
                    if c in missing_tracker:
                        missing_tracker.remove(c)
                return missing_tracker

            # 1. Quét tìm ngay trên màn hình hiện tại (trước khi vuốt)
            self.after(0, self.log_info, f"👁️ [Thao Tác 1] Quét tìm đồng thời các nhân vật chưa mời: {', '.join(still_missing)}...")
            still_missing = scan_and_invite_current_screen(still_missing)

            # 2. Chiều Vuốt XUỐNG thông minh: input swipe 795 400 795 205 1500 (Thời gian vuốt 1.5s), tăng lên tối đa 4 lần
            if still_missing:
                for swipe_down_cnt in range(4):
                    if self._should_stop_card_E() or not still_missing: break
                    self.after(0, self.log_info, f"📜 [Vuốt xuống {swipe_down_cnt+1}/4] Quét tìm các nhân vật chưa mời: {', '.join(still_missing)}...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 795 400 795 205 1500"])
                    time.sleep(1.0)
                    still_missing = scan_and_invite_current_screen(still_missing)

            # 3. Chiều Vuốt LÊN thông minh (Nếu sau 4 lần vuốt xuống vẫn còn acc chưa thấy): input swipe 795 205 795 575 3000 (Thời gian vuốt 3s), tối đa 2 lần
            if still_missing:
                for swipe_up_cnt in range(2):
                    if self._should_stop_card_E() or not still_missing: break
                    self.after(0, self.log_info, f"📜 [Vuốt lên {swipe_up_cnt+1}/2] Quét tìm các nhân vật chưa mời: {', '.join(still_missing)}...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 795 205 795 575 3000"])
                    time.sleep(1.0)
                    still_missing = scan_and_invite_current_screen(still_missing)

            # Kiểm tra nếu sau 4 lượt vuốt xuống & 2 lượt vuốt lên vẫn còn nhân vật chưa mời được
            if still_missing:
                self.after(0, self.log_info, f"⚠️ [Hành Động Thông Minh] Sau 4 lượt vuốt xuống & 2 lượt vuốt lên vẫn chưa mời được: {', '.join(still_missing)} ➔ Quét tap 'card_e/e_doingu.png' (85%, ROI 175,165,295,455) hoãn 0.4s & quay lại bước Nhận Diện!")
                dn_x, dn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_e/e_doingu.png", threshold=0.85, region=(175, 165, 295, 455))
                if dn_x is not None and dn_y is not None:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {dn_x} {dn_y}"])
                time.sleep(0.4)
                continue

            # Sau khi đã mời thành công tất cả các acc bị thiếu: Nghỉ 3s chờ đồng ý
            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "⏳ [Thao Tác 1] Đã bấm Mời toàn bộ danh sách bị thiếu ➔ Nghỉ 3.0s chờ các thành viên đồng ý...")
            for _ in range(3):
                if self._should_stop_card_E(): return
                time.sleep(1.0)

            # Mắt thần quét tìm ảnh / tap card_e/e_doingu.png (85%, ROI 175,165,295,455) hoãn 0.4s
            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "👁️ Quét tìm & tap ảnh 'card_e/e_doingu.png' (85%, ROI 175,165,295,455) hoãn 0.4s...")
            dn_x, dn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_e/e_doingu.png", threshold=0.85, region=(175, 165, 295, 455))
            if dn_x is not None and dn_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_e/e_doingu.png' tại ({dn_x}, {dn_y})! Tap click...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {dn_x} {dn_y}"])
            time.sleep(0.4)


def run_card_E_action_2(self, dnconsole_path: str, tab_index: str, list_B: list):
    """
    THAO TÁC 2 CỦA CARD TỔ ĐỘI:
    Kích hoạt khi ô tích 'Tổ Đội' của Card Phụ Bản Đơn / Đội (var_B_doi) được tích.
    """
    if self._should_stop_card_E() or not list_B: return

    self.after(0, self.log_info, f"🚀 [CARD TỔ ĐỘI - Thao Tác 2] Bắt đầu quy trình mời {len(list_B)} nhân vật trong Danh Sách B: {', '.join(list_B)}...")
    already_invited = set()

    # VÒNG LẶP MỜI VÀ KIỂM TRA ĐỘI HÌNH (Lặp cho tới khi đủ 100% người)
    while not self._should_stop_card_E():
        # --- BƯỚC 1: NHẬN DIỆN THÀNH VIÊN TRONG ĐỘI ---
        if self._should_stop_card_E(): return
        self.after(0, self.log_info, "👁️ [Thao Tác 2 - Bước 1] Quét kiểm tra các nhân vật trong Danh Sách B...")
        all_present = True
        missing_list = []

        for char_name in list_B:
            if self._should_stop_card_E(): return
            chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/pbdoi/{char_name}.png", threshold=0.80, region=(175, 165, 1105, 605))
            if chk_x is None or chk_y is None:
                chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/{char_name}.png", threshold=0.80, region=(175, 165, 1105, 605))

            if chk_x is None or chk_y is None:
                all_present = False
                missing_list.append(char_name)
            else:
                if char_name in already_invited:
                    already_invited.remove(char_name)

        # --- BƯỚC 2: ĐÁNH GIÁ KẾT QUẢ KIỂM TRA ---
        if all_present:
            self.after(0, self.log_info, f"✅ [Thao Tác 2 - Bước 2: Trường hợp A] Đội hình đã ĐỦ 100% thành viên ({', '.join(list_B)})! Thoát vòng lặp & trả thao tác về Phụ Bản Đội.")
            self.after(0, lambda: self._send_notification("🎉 Tổ Đội Hoàn Thành", f"Đội hình đã gom đủ 100% thành viên ({', '.join(list_B)})!"))
            break

        # Lọc danh sách những thành viên thiếu chưa được gửi lời mời ở lượt trước
        uninvited_missing = [c for c in missing_list if c not in already_invited]
        if not uninvited_missing:
            self.after(0, self.log_info, f"ℹ️ Tất cả thành viên thiếu ({', '.join(missing_list)}) đã được bấm Mời ➔ Reset danh sách đã mời để tuần tự kiểm tra/mời lại...")
            already_invited.clear()
            uninvited_missing = list(missing_list)

        # 🔴 TRƯỜNG HỢP B: CÒN THIẾU THÀNH VIÊN
        self.after(0, self.log_info, f"⚠️ [Thao Tác 2 - Bước 2: Trường hợp B] Đội chưa đủ người (Thiếu: {', '.join(missing_list)} | Cần mời tiếp: {', '.join(uninvited_missing)}) ➔ Quét tìm nút Mời 'card_e/e_moi.png'...")
        
        # Quét Mắt thần tìm nút Mời card_e/e_moi.png (85%, ROI 175,165,1105,605)
        if self._should_stop_card_E(): return
        f_moi_x, f_moi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_e/e_moi.png", threshold=0.85, region=(175, 165, 1105, 605))
        if f_moi_x is not None and f_moi_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_e/e_moi.png' tại ({f_moi_x}, {f_moi_y})! Tap click ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {f_moi_x} {f_moi_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "⚠️ Chưa quét thấy ảnh 'card_e/e_moi.png' trên màn hình ➔ Thử lại sau 1.0s...")
            time.sleep(1.0)
            continue

        # Dò Tìm Thành Viên Tiếp Theo Chưa Mời
        still_missing = list(uninvited_missing)
        invited_any = False

        def scan_and_invite_mode2(missing_tracker: list) -> tuple:
            """
            Quét tìm thành viên tiếp theo chưa mời.
            Mỗi khi bấm Mời offset (Found_X + 205, Found_Y), lưu vào already_invited và trả về (True, char_name).
            """
            for char_name in list(missing_tracker):
                if self._should_stop_card_E(): break
                found_x, found_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/pbdoi/{char_name}.png", threshold=0.80, region=(175, 165, 1105, 605))
                if found_x is None or found_y is None:
                    found_x, found_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/{char_name}.png", threshold=0.80, region=(175, 165, 1105, 605))

                if found_x is not None and found_y is not None:
                    invite_x = found_x + 205
                    invite_y = found_y
                    self.after(0, self.log_info, f"🎯 Phát hiện thành viên tiếp theo '{char_name}' tại ({found_x}, {found_y})! Tap nút Mời ({invite_x}, {invite_y}) ➔ Hoãn 0.5s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {invite_x} {invite_y}"])
                    time.sleep(0.5)
                    already_invited.add(char_name)
                    return True, char_name
            return False, None

        # 1. Quét tìm ngay trên màn hình hiện tại (trước khi vuốt)
        invited_any, char_done = scan_and_invite_mode2(still_missing)

        # 2. Chiều Vuốt XUỐNG thông minh: input swipe 625 410 625 260 1000 (Tối đa 10 lần)
        if not invited_any and still_missing:
            for swipe_down_cnt in range(10):
                if self._should_stop_card_E() or not still_missing: break
                self.after(0, self.log_info, f"📜 [Vuốt xuống {swipe_down_cnt+1}/10] Swipe (625, 410 ➔ 625, 260 1000ms)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 625 410 625 260 1000"])
                time.sleep(0.8)
                invited_any, char_done = scan_and_invite_mode2(still_missing)
                if invited_any: break

        # 3. Chiều Vuốt LÊN thông minh: input swipe 625 260 625 410 2200 (Tối đa 8 lần)
        if not invited_any and still_missing:
            for swipe_up_cnt in range(8):
                if self._should_stop_card_E() or not still_missing: break
                self.after(0, self.log_info, f"📜 [Vuốt lên {swipe_up_cnt+1}/8] Swipe (625, 260 ➔ 625, 410 2200ms)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 625 260 625 410 2200"])
                time.sleep(0.8)
                invited_any, char_done = scan_and_invite_mode2(still_missing)
                if invited_any: break

        # 4. Tự Động Sửa Lỗi Nếu Không Tìm Thấy
        if not invited_any:
            self.after(0, self.log_info, "⚠️ [Thao Tác 2 - Sửa Lỗi] Sau 10 lượt vuốt xuống & 8 lượt vuốt lên không tìm thấy acc ➔ Tap (330, 25) tắt bảng Mời ➔ Hoãn 0.4s & quay lại Bước 2.1...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 330 25"])
            time.sleep(0.4)
            continue

        # Sau khi bấm Mời acc thành công: Tạm nghỉ 2.0s chờ đồng ý & quay lại Bước 2.1
        if self._should_stop_card_E(): return
        self.after(0, self.log_info, "⏳ [Thao Tác 2] Đã tap nút Mời ➔ Tạm nghỉ 2.0s chờ các thành viên nhận & đồng ý lời mời...")
        for _ in range(2):
            if self._should_stop_card_E(): return
            time.sleep(1.0)


def execute_card_E_for_mode(self, dnconsole_path: str, tab_name: str, tab_index: str, mode: int):
    """
    Khung thực thi phân luồng Card Tổ Đội (G):
    - mode=1: Thao tác 1 (Kích hoạt khi ô Tổ Đội 40NPC / 2K var_D2 được tích)
    - mode=2: Thao tác 2 (Kích hoạt khi ô Tổ Đội Phụ Bản Đội var_B_doi được tích)
    """
    list_B = list(getattr(self, 'list_E_B', []))
    if not list_B:
        self.after(0, self.log_info, f"ℹ️ [TỔ ĐỘI - Thao Tác {mode}] [Danh Sách B] chưa có nhân vật nào -> Bỏ qua.")
        return

    self.after(0, self.log_info, f"▶️ [TỔ ĐỘI - Thao Tác {mode}] Bắt đầu thực thi {len(list_B)} nhân vật từ [Danh Sách B]: {', '.join(list_B)}...")
    if mode == 1:
        self._run_card_E_action_1(dnconsole_path, tab_index, list_B)
    elif mode == 2:
        self._run_card_E_action_2(dnconsole_path, tab_index, list_B)
