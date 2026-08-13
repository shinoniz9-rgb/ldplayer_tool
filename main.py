import customtkinter as ctk
import subprocess
import os
import threading
import time
import json
from datetime import datetime, timedelta
import cv2
import numpy as np
import unicodedata
import re

# Thử import ppadb nếu có sẵn trong hệ thống
try:
    from ppadb.client import Client as AdbClient
    HAS_PPADB = True
except ImportError:
    HAS_PPADB = False

# Cấu hình giao diện CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ToolLDPlayerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- CẤU HÌNH CỬA SỔ CHÍNH ---
        self.title("TS Origin-Control")
        self.geometry("944x640")
        self.minsize(780, 540)
        self._center_window(944, 640)

    def _center_window(self, width: int = 944, height: int = 640):
        """Căn giữa cửa sổ ứng dụng trên màn hình Desktop"""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")

        # --- BIẾN TRẠNG THÁI & CẤU HÌNH ---
        self.ld_path = r"C:\Program Files\LDPlayer\LDPlayer9"
        self.dict_name_to_index = {}
        self.is_scanning = False
        self.game_icon_path = None
        self.game_ctk_image = None

        # Biến trạng thái Công tắc tổng ON/OFF các Card
        self.var_switch_B = ctk.BooleanVar(value=False)
        self.var_switch_C = ctk.BooleanVar(value=False)
        self.var_switch_D = ctk.BooleanVar(value=False)
        self.var_switch_E = ctk.BooleanVar(value=False)
        self.var_switch_F = ctk.BooleanVar(value=False)

        # Biến trạng thái các ô Checkbox Cấu hình B (DỊ GIỚI ĐÊM)
        self.var_B1 = ctk.BooleanVar(value=False)
        self.var_B2 = ctk.BooleanVar(value=False)
        self.var_B3 = ctk.BooleanVar(value=False)
        self.var_B4 = ctk.BooleanVar(value=False)

        # Biến trạng thái các ô Checkbox Cấu hình C
        self.var_C1 = ctk.BooleanVar(value=False)
        self.var_C2 = ctk.BooleanVar(value=False)
        self.var_C3 = ctk.BooleanVar(value=False)
        self.var_C4 = ctk.BooleanVar(value=False)

        # Biến trạng thái các ô Checkbox Cấu hình D
        self.var_D1 = ctk.BooleanVar(value=False)
        self.var_D2 = ctk.BooleanVar(value=False)
        self.var_D3 = ctk.BooleanVar(value=False)
        self.var_D4 = ctk.BooleanVar(value=False)

        # Biến trạng thái các ô Checkbox Cấu hình E (PHỤ BẢN ĐƠN / ĐỘI)
        self.var_E_don = ctk.BooleanVar(value=False)
        self.var_E_canhan = ctk.BooleanVar(value=False)
        self.var_E_doi = ctk.BooleanVar(value=False)
        self.var_E1 = ctk.BooleanVar(value=False)
        self.var_E2 = ctk.BooleanVar(value=False)
        self.var_E3 = ctk.BooleanVar(value=False)
        self.var_E4 = ctk.BooleanVar(value=False)

        # Biến trạng thái các ô Checkbox Cấu hình F
        self.var_F1 = ctk.BooleanVar(value=False)
        self.var_F2 = ctk.BooleanVar(value=False)
        self.var_F3 = ctk.BooleanVar(value=False)
        self.var_F4 = ctk.BooleanVar(value=False)

        # Biến trạng thái các ô Checkbox Cấu hình G (PHỤ BẢN ĐƠN)
        self.var_G1 = ctk.BooleanVar(value=False)
        self.var_G2 = ctk.BooleanVar(value=False)
        self.var_G3 = ctk.BooleanVar(value=False)
        self.var_G4 = ctk.BooleanVar(value=False)
        self.var_G_nv1 = ctk.BooleanVar(value=False)
        self.var_G_nv2 = ctk.BooleanVar(value=False)
        self.var_G_nv3 = ctk.BooleanVar(value=False)
        self.var_G_nv4 = ctk.BooleanVar(value=False)

        # Biến trạng thái Dừng khẩn cấp
        self.stop_requested = False

        # --- TẠO HỆ THỐNG GIAO DIỆN ---
        self._setup_grid()
        self._create_header()
        self._create_ld_selection_card()
        self._create_game_action_card()
        self._create_unified_config_card()
        self._create_log_card()
        self._create_status_bar()

        # Nạp cấu hình đã lưu
        self.load_config()

        # Đăng ký sự kiện tắt ứng dụng
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Quét danh sách LDPlayer lần đầu tiên
        self.refresh_ld_tabs_async()


    def _get_character_options(self) -> list:
        """Danh sách các tùy chọn vị trí / chế độ xuất chiến trong menu thả xuống"""
        return ["Xuất Chiến", "Vị Trí 1", "Vị Trí 2", "Vị Trí 3", "Vị Trí 4"]

    def _get_server_options(self) -> list:
        """Danh sách tùy chọn các máy chủ (Điêu Thuyền, Triệu Vân...) và tự động quét các file server_*.png mới"""
        servers = ["Điêu Thuyền", "Triệu Vân"]
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "assets")
        server_dir = os.path.join(assets_dir, "server")
        
        for search_dir in [server_dir, assets_dir]:
            if os.path.exists(search_dir):
                try:
                    for f in sorted(os.listdir(search_dir)):
                        if f.lower().startswith("server_") and f.lower().endswith(".png"):
                            raw_name = f[7:-4]
                            if raw_name not in ["dieuthuyen", "trieuvan"]:
                                title_name = raw_name.replace("_", " ").title()
                                if title_name not in servers:
                                    servers.append(title_name)
                except Exception:
                    pass
        return servers


    def _update_card_G_visibility(self):
        """Cập nhật trạng thái sáng/tối & khóa tùy chỉnh của Card 3 (TỔ ĐỘI) theo ô check 'Tổ Đội' ở Card E"""
        if not hasattr(self, 'card_G') or not hasattr(self, 'var_E_doi'):
            return

        is_doi_checked = self.var_E_doi.get()
        if is_doi_checked:
            # SÁNG LÊN: Bật trạng thái tùy chỉnh và khôi phục màu tiêu đề sáng
            if hasattr(self, 'lbl_G'): self.lbl_G.configure(text_color="#FB923C")
            if hasattr(self, 'lbl_tuong'): self.lbl_tuong.configure(text_color="#38BDF8")
            if hasattr(self, 'lbl_nhanvat'): self.lbl_nhanvat.configure(text_color="#38BDF8")
            for num in range(1, 5):
                chk = getattr(self, f"chk_G{num}", None)
                if chk: chk.configure(state="normal", text_color=("gray10", "gray90"))
                chk_nv = getattr(self, f"chk_G_nv{num}", None)
                if chk_nv: chk_nv.configure(state="normal", text_color=("gray10", "gray90"))
        else:
            # TỐI ĐI / KHÓA: Đổi màu tiêu đề mờ, khóa click & reset các ô check
            if hasattr(self, 'lbl_G'): self.lbl_G.configure(text_color="#9CA3AF")
            if hasattr(self, 'lbl_tuong'): self.lbl_tuong.configure(text_color="#9CA3AF")
            if hasattr(self, 'lbl_nhanvat'): self.lbl_tuong.configure(text_color="#9CA3AF")
            for num in range(1, 5):
                var = getattr(self, f"var_G{num}", None)
                if var: var.set(False)
                chk = getattr(self, f"chk_G{num}", None)
                if chk: chk.configure(state="disabled", text_color="gray50")
                var_nv = getattr(self, f"var_G_nv{num}", None)
                if var_nv: var_nv.set(False)
                chk_nv = getattr(self, f"chk_G_nv{num}", None)
                if chk_nv: chk_nv.configure(state="disabled", text_color="gray50")

    def save_config(self):
        """Lưu toàn bộ cấu hình máy chủ & checkbox vào config.json một cách an toàn"""
        try:
            config = {}
            if hasattr(self, 'combo_server'):
                config["server"] = self.combo_server.get()

            if hasattr(self, 'var_E_don'):
                config["E_don"] = self.var_E_don.get()
            if hasattr(self, 'var_E_canhan'):
                config["E_canhan"] = self.var_E_canhan.get()
            if hasattr(self, 'var_E_doi'):
                config["E_doi"] = self.var_E_doi.get()

            if hasattr(self, 'combo_E_don_char'):
                config["E_don_char"] = self.combo_E_don_char.get()
            if hasattr(self, 'combo_E_team_char'):
                config["E_team_char"] = self.combo_E_team_char.get()
            if hasattr(self, 'combo_C_char'):
                config["C_char"] = self.combo_C_char.get()
            if hasattr(self, 'combo_C_ve'):
                config["C_ve"] = self.combo_C_ve.get()

            for prefix in ["B", "C", "D", "E", "F"]:
                switch_attr = f"var_switch_{prefix}"
                if hasattr(self, switch_attr):
                    config[f"switch_{prefix}"] = False  # Luôn lưu công tắc các card ở trạng thái OFF

                for num in range(1, 5):
                    key = f"{prefix}{num}"
                    var_attr = f"var_{key}"
                    if hasattr(self, var_attr):
                        config[key] = getattr(self, var_attr).get()

            for num in range(1, 5):
                key = f"G{num}"
                var_attr = f"var_{key}"
                if hasattr(self, var_attr):
                    config[key] = getattr(self, var_attr).get()
                if hasattr(self, f"var_G_nv{num}"):
                    config[f"G_nv{num}"] = getattr(self, f"var_G_nv{num}").get()

            if hasattr(self, 'combo_ld_tabs'):
                config["selected_tab"] = self.combo_ld_tabs.get()

            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            pass

    def load_config(self):
        """Khôi phục toàn bộ cấu hình máy chủ & checkbox từ config.json (Các công tắc card bắt buộc giữ OFF)"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                if "server" in config and hasattr(self, 'combo_server'):
                    self.combo_server.set(config["server"])

                if "E_don" in config and hasattr(self, 'var_E_don'):
                    self.var_E_don.set(config["E_don"])
                if "E_canhan" in config and hasattr(self, 'var_E_canhan'):
                    self.var_E_canhan.set(config["E_canhan"])
                if "E_doi" in config and hasattr(self, 'var_E_doi'):
                    self.var_E_doi.set(config["E_doi"])

                opts = self._get_character_options()
                if "E_don_char" in config and hasattr(self, 'combo_E_don_char'):
                    val = config["E_don_char"]
                    self.combo_E_don_char.set(val if val in opts else "Xuất Chiến")
                if "E_team_char" in config and hasattr(self, 'combo_E_team_char'):
                    val = config["E_team_char"]
                    self.combo_E_team_char.set(val if val in opts else "Xuất Chiến")
                if "C_char" in config and hasattr(self, 'combo_C_char'):
                    val = config["C_char"]
                    self.combo_C_char.set(val if val in opts else "Xuất Chiến")
                if "C_ve" in config and hasattr(self, 'combo_C_ve'):
                    val = config["C_ve"]
                    self.combo_C_ve.set(val if val in ["1", "2", "3", "4", "5"] else "1")

                for prefix in ["B", "C", "D", "E", "F"]:
                    switch_attr = f"var_switch_{prefix}"
                    if hasattr(self, switch_attr):
                        getattr(self, switch_attr).set(False)  # Bắt buộc công tắc về OFF khi mở tool

                    for num in range(1, 5):
                        key = f"{prefix}{num}"
                        var_attr = f"var_{key}"
                        if key in config and hasattr(self, var_attr):
                            getattr(self, var_attr).set(config[key])

                for num in range(1, 5):
                    key = f"G{num}"
                    var_attr = f"var_{key}"
                    if key in config and hasattr(self, var_attr):
                        getattr(self, var_attr).set(config[key])

                if "selected_tab" in config and hasattr(self, 'combo_ld_tabs'):
                    self.saved_selected_tab = config["selected_tab"]
            except Exception as e:
                pass

    def _on_closing(self):
        # Tắt các công tắc trước khi đóng và lưu cấu hình
        for prefix in ["B", "C", "D", "E", "F"]:
            switch_attr = f"var_switch_{prefix}"
            if hasattr(self, switch_attr):
                getattr(self, switch_attr).set(False)
        self.save_config()
        self.destroy()

    def _setup_grid(self):
        """Thiết lập Grid Layout 2 cột: Cột Trái (Bảng điều khiển & 6 Card), Cột Phải (Ô Log Nhật Ký)"""
        self.grid_rowconfigure(0, weight=0)  # Header cố định
        self.grid_rowconfigure(1, weight=0)  # Card chọn LD Tab
        self.grid_rowconfigure(2, weight=0)  # Card Game Action
        self.grid_rowconfigure(3, weight=1)  # Khung chứa 6 Card Cấu hình co giãn
        self.grid_rowconfigure(4, weight=0)  # Status bar cố định bên dưới

        self.grid_columnconfigure(0, weight=6)  # Cột Trái: Bảng điều khiển & 6 Card
        self.grid_columnconfigure(1, weight=4)  # Cột Phải: Ô Log Nhật Ký Hoạt Động

    def _create_header(self):
        """Khung Header hiển thị tiêu đề và nút chuyển Theme"""
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 4), sticky="ew")
        self.header_frame.grid_columnconfigure(0, weight=1)

        # Title & Subtitle
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.grid(row=0, column=0, sticky="w")

        lbl_title = ctk.CTkLabel(
            title_box, 
            text="HỆ THỐNG ĐIỀU KHIỂN TỰ ĐỘNG", 
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="normal")
        )
        lbl_title.pack(anchor="w")

        lbl_subtitle = ctk.CTkLabel(
            title_box, 
            text="TS Origin-Control • LDPlayer Manager", 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="gray60"
        )
        lbl_subtitle.pack(anchor="w")

        # Nút đổi Dark / Light Theme
        self.switch_theme = ctk.CTkSwitch(
            self.header_frame, 
            text="Tối", 
            command=self._toggle_theme,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal")
        )
        self.switch_theme.select()
        self.switch_theme.grid(row=0, column=1, sticky="e")

    def _create_ld_selection_card(self):
        """Khung Card chọn Tab LDPlayer đang chạy (Nằm ở Cột 0 - Bên trái)"""
        self.card_ld = ctk.CTkFrame(self, corner_radius=8)
        self.card_ld.grid(row=1, column=0, padx=(15, 4), pady=4, sticky="nsew")
        self.card_ld.grid_columnconfigure(0, weight=1)
        self.card_ld.grid_rowconfigure((0, 1), weight=1)

        # Label tiêu đề khung
        lbl_card_title = ctk.CTkLabel(
            self.card_ld,
            text="CHỌN TAB LDPLAYER",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            text_color="#3B82F6"
        )
        lbl_card_title.grid(row=0, column=0, padx=10, pady=(6, 2), sticky="w")

        # Khung chứa ComboBox & Nút Refresh
        select_row = ctk.CTkFrame(self.card_ld, fg_color="transparent")
        select_row.grid(row=1, column=0, padx=10, pady=(0, 6), sticky="nsew")
        select_row.grid_columnconfigure(0, weight=1)
        select_row.grid_rowconfigure(0, weight=1)

        self.combo_ld_tabs = ctk.CTkComboBox(
            select_row,
            values=["Đang quét tab..."],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            height=34,
            command=self._on_ld_tab_selected
        )
        self.combo_ld_tabs.grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        self.btn_refresh = ctk.CTkButton(
            select_row,
            text="Làm Mới",
            width=85,
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            fg_color="#1E40AF",
            hover_color="#1D4ED8",
            command=self.refresh_ld_tabs_async
        )
        self.btn_refresh.grid(row=0, column=1, sticky="nsew")

    def _on_ld_tab_selected(self, choice: str):
        """Tự động ghi nhớ tab LDPlayer được chọn vào config.json"""
        self.saved_selected_tab = choice
        self.save_config()
        self.log_info(f"💾 Đã ghi nhớ tab LDPlayer: '{choice}'")

    def _create_game_action_card(self):
        """Khung Card Khởi Động & Máy Chủ (Nằm ở Cột 0 - Bên trái)"""
        self.card_game = ctk.CTkFrame(self, corner_radius=8)
        self.card_game.grid(row=2, column=0, padx=(15, 4), pady=4, sticky="nsew")
        self.card_game.grid_columnconfigure((0, 1), weight=1)
        self.card_game.grid_columnconfigure(2, weight=0)
        self.card_game.grid_rowconfigure((0, 1), weight=1)

        # Label tiêu đề card
        lbl_card_title = ctk.CTkLabel(
            self.card_game,
            text="KHỞI ĐỘNG & SERVER",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            text_color="#10B981"
        )
        lbl_card_title.grid(row=0, column=0, columnspan=3, padx=10, pady=(6, 4), sticky="w")

        # Nút "TS Origin" (Nằm bên trái - Column 0)
        self.btn_enter_game = ctk.CTkButton(
            self.card_game,
            text="TS Origin",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            height=34,
            fg_color="#059669",
            hover_color="#047857",
            command=self.xu_ly_ts_origin
        )
        self.btn_enter_game.grid(row=1, column=0, padx=(10, 4), pady=(0, 8), sticky="nsew")

        # Nút chọn Server thả xuống (OptionMenu - Column 1)
        self.combo_server = ctk.CTkOptionMenu(
            self.card_game,
            values=self._get_server_options(),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            height=34,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=self._on_server_changed
        )
        self.combo_server.set("Điêu Thuyền")
        self.combo_server.grid(row=1, column=1, padx=4, pady=(0, 8), sticky="nsew")

        # Nút "Dừng" (Kích thước width=85 bằng nút Làm mới - Column 2)
        self.btn_stop = ctk.CTkButton(
            self.card_game, 
            text="Dừng", 
            width=85,
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=self.dung_tat_ca_hoat_dong
        )
        self.btn_stop.grid(row=1, column=2, padx=(4, 10), pady=(0, 8), sticky="ns")

    def _on_server_changed(self, choice: str):
        """Tự động ghi nhớ vị trí máy chủ được chọn để khôi phục cho lần mở tool sau"""
        self.save_config()
        self.log_info(f"💾 Đã ghi nhớ máy chủ: '{choice}'")

    def _create_log_card(self):
        """Khung ô ghi Log hiển thị nhật ký lịch sử hoạt động chi tiết (Nằm ở Cột 1 - Bên Phải full chiều cao)"""
        self.card_log = ctk.CTkFrame(self, corner_radius=8)
        self.card_log.grid(row=1, column=1, rowspan=3, padx=(4, 15), pady=4, sticky="nsew")
        self.card_log.grid_columnconfigure(0, weight=1)
        self.card_log.grid_rowconfigure(0, weight=0)
        self.card_log.grid_rowconfigure(1, weight=1)

        # Header ô Log (Tiêu đề + Nút Xóa Log)
        hdr_log = ctk.CTkFrame(self.card_log, fg_color="transparent")
        hdr_log.grid(row=0, column=0, padx=8, pady=(6, 4), sticky="ew")
        hdr_log.grid_columnconfigure(0, weight=1)

        lbl_log_title = ctk.CTkLabel(
            hdr_log,
            text="NHẬT KÝ HOẠT ĐỘNG (LOG)",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#38BDF8"
        )
        lbl_log_title.grid(row=0, column=0, sticky="w")

        btn_clear_log = ctk.CTkButton(
            hdr_log,
            text="Xóa Log",
            width=65,
            height=22,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#374151",
            hover_color="#4B5563",
            command=self._clear_log
        )
        btn_clear_log.grid(row=0, column=1, sticky="e")

        # Ô Textbox hiển thị dòng Log cuộn được (Kéo giãn full chiều cao khung bên phải)
        self.txt_log = ctk.CTkTextbox(
            self.card_log,
            font=ctk.CTkFont(family="Consolas", size=11, weight="normal"),
            fg_color=("gray90", "#111827"),
            text_color=("gray10", "#F3F4F6"),
            wrap="word",
            corner_radius=6
        )
        self.txt_log.grid(row=1, column=0, padx=8, pady=(0, 6), sticky="nsew")
        self.txt_log.configure(state="disabled")

    def _clear_log(self):
        """Xóa toàn bộ nội dung ô log"""
        if hasattr(self, 'txt_log'):
            self.txt_log.configure(state="normal")
            self.txt_log.delete("1.0", "end")
            self.txt_log.configure(state="disabled")

    def _create_status_bar(self):
        """Thanh trạng thái bên dưới cùng (Trải dài 2 cột)"""
        self.status_bar = ctk.CTkFrame(self, height=26, corner_radius=0, fg_color=("gray85", "gray15"))
        self.status_bar.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.status_bar.grid_columnconfigure(0, weight=1)

        self.lbl_status = ctk.CTkLabel(
            self.status_bar,
            text="Sẵn sàng",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="gray60"
        )
        self.lbl_status.grid(row=0, column=0, padx=12, sticky="w")

        self.lbl_tab_count = ctk.CTkLabel(
            self.status_bar,
            text="Tab LD: 0",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#3B82F6"
        )
        self.lbl_tab_count.grid(row=0, column=1, padx=12, sticky="e")

    def _get_selected_ld_info(self):
        """Lấy tên tab và index tab LDPlayer đang chọn"""
        tab_name = self.combo_ld_tabs.get()
        if tab_name in ["Đang quét tab...", "Không tìm thấy tab LD nào", "Sai đường dẫn LDPlayer", "Lỗi quét dữ liệu"]:
            return None, None
        dict_map = getattr(self, "dict_name_to_index", {})
        index_tab = dict_map.get(tab_name)
        if index_tab is None:
            # Dò tìm con số trong tên tab (VD: "LDPlayer-1" -> "1")
            nums = re.findall(r'\d+', tab_name)
            index_tab = nums[0] if nums else "0"
        return tab_name, index_tab

    def _on_checkbox_toggled(self):
        """Callback khi bất kỳ ô checkbox nào được tích chọn/bỏ chọn"""
        self._update_card_G_visibility()
        self.save_config()

    def _on_E_doi_toggled(self):
        """Khi tích ô Tổ Đội -> tự động bỏ tích ô Cá Nhân trong Phụ Bản Đội"""
        if self.var_E_doi.get():
            self.var_E_canhan.set(False)
        self._on_checkbox_toggled()

    def _on_E_canhan_toggled(self):
        """Khi tích ô Cá Nhân -> tự động bỏ tích ô Tổ Đội trong Phụ Bản Đội"""
        if self.var_E_canhan.get():
            self.var_E_doi.set(False)
        self._on_checkbox_toggled()

    def _on_switch_B_toggled(self):
        """Callback riêng cho công tắc Card C (DỊ GIỚI ĐÊM): Khi trượt sang OFF -> Ngắt tiến trình & giữ nguyên ô tích"""
        self._on_checkbox_toggled()
        if not self.var_switch_B.get():
            self.save_config()
            self.log_info("🛑 [CARD C: DỊ GIỚI ĐÊM] Công tắc gạt về OFF ➔ Đã ngắt tiến trình Card C (giữ nguyên các ô tích)!")
        else:
            self.stop_requested = False
            tab_name, tab_index = self._get_selected_ld_info()
            if tab_index is None:
                self.log_error("Vui lòng chọn một Tab LDPlayer trước khi bật công tắc Dị Giới!")
                self.var_switch_B.set(False)
                self.save_config()
                return

            dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")

            if not os.path.exists(dnconsole_path):
                self.log_error(f"Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
                self.var_switch_B.set(False)
                self.save_config()
                return

            self.log_info(f"⚡ [DỊ GIỚI ĐÊM] Công tắc vừa trượt ON ➔ Khởi chạy ngay thao tác trên Tab: {tab_name} (Index: {tab_index})...")
            threading.Thread(target=self._execute_card_B_di_gioi, args=(dnconsole_path, tab_name, tab_index), daemon=True).start()

    def _on_switch_E_toggled(self):
        """Callback riêng cho công tắc Card A (PHỤ BẢN ĐƠN / ĐỘI): Khi trượt sang OFF -> Ngắt tiến trình & giữ nguyên ô tích"""
        self._on_checkbox_toggled()
        if not self.var_switch_E.get():
            self._update_card_G_visibility()
            self.save_config()
            self.log_info("🛑 [CARD A: PHỤ BẢN ĐƠN / ĐỘI] Công tắc gạt về OFF ➔ Đã ngắt tiến trình Card A (giữ nguyên các ô tích)!")
        else:
            self.stop_requested = False
            tab_name, tab_index = self._get_selected_ld_info()
            if tab_index is None:
                self.log_error("Vui lòng chọn một Tab LDPlayer trước khi bật công tắc Phụ Bản Đơn / Đội!")
                self.var_switch_E.set(False)
                self.save_config()
                return

            dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")

            if not os.path.exists(dnconsole_path):
                self.log_error(f"Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
                self.var_switch_E.set(False)
                self.save_config()
                return

            self.log_info(f"⚡ [PHỤ BẢN ĐƠN / ĐỘI] Công tắc vừa trượt ON ➔ Khởi chạy ngay thao tác trên Tab: {tab_name} (Index: {tab_index})...")
            threading.Thread(target=self._execute_card_E_phu_ban_doi, args=(dnconsole_path, tab_name, tab_index), daemon=True).start()

    def _on_switch_C_toggled(self):
        """Callback riêng cho công tắc Card B (BOSS THẾ GIỚI): Khi trượt sang OFF -> Ngắt tiến trình & giữ nguyên ô tích"""
        self._on_checkbox_toggled()
        if not self.var_switch_C.get():
            self.save_config()
            self.log_info("🛑 [CARD B: BOSS THẾ GIỚI] Công tắc gạt về OFF ➔ Đã ngắt tiến trình Card B (giữ nguyên các ô tích)!")
        else:
            self.stop_requested = False
            tab_name, tab_index = self._get_selected_ld_info()
            if tab_index is None:
                self.log_error("Vui lòng chọn một Tab LDPlayer trước khi bật công tắc Boss Thế Giới!")
                self.var_switch_C.set(False)
                self.save_config()
                return

            dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")

            if not os.path.exists(dnconsole_path):
                self.log_error(f"Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
                self.var_switch_C.set(False)
                self.save_config()
                return

            self.log_info(f"⚡ [BOSS THẾ GIỚI] Công tắc vừa trượt ON ➔ Khởi chạy ngay thao tác trên Tab: {tab_name} (Index: {tab_index})...")
            threading.Thread(target=self._execute_card_C_boss_tg, args=(dnconsole_path, tab_name, tab_index), daemon=True).start()

    def _on_switch_D_toggled(self):
        """Callback riêng cho công tắc Card E (40 NPC): Khi trượt sang OFF -> Ngắt tiến trình & giữ nguyên ô tích"""
        self._on_checkbox_toggled()
        if not self.var_switch_D.get():
            self.save_config()
            self.log_info("🛑 [CARD E: 40 NPC] Công tắc gạt về OFF ➔ Đã ngắt tiến trình Card E (giữ nguyên các ô tích)!")
        else:
            self.stop_requested = False
            tab_name, tab_index = self._get_selected_ld_info()
            if tab_index is None:
                self.log_error("Vui lòng chọn một Tab LDPlayer trước khi bật công tắc 40 NPC!")
                self.var_switch_D.set(False)
                self.save_config()
                return

            dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")

            if not os.path.exists(dnconsole_path):
                self.log_error(f"Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
                self.var_switch_D.set(False)
                self.save_config()
                return

            self.log_info(f"⚡ [40 NPC] Công tắc vừa trượt ON ➔ Khởi chạy ngay thao tác trên Tab: {tab_name} (Index: {tab_index})...")
            threading.Thread(target=self._execute_card_D_40_npc, args=(dnconsole_path, tab_name, tab_index), daemon=True).start()

    def _on_switch_F_toggled(self):
        """Callback riêng cho công tắc Card F (NHỊ KIỀU): Khi trượt sang OFF -> Ngắt tiến trình & giữ nguyên ô tích"""
        self._on_checkbox_toggled()
        if not self.var_switch_F.get():
            self.save_config()
            self.log_info("🛑 [CARD F: NHỊ KIỀU] Công tắc gạt về OFF ➔ Đã ngắt tiến trình Card F (giữ nguyên các ô tích)!")
        else:
            self.stop_requested = False
            tab_name, tab_index = self._get_selected_ld_info()
            if tab_index is None:
                self.log_error("Vui lòng chọn một Tab LDPlayer trước khi bật công tắc Nhị Kiều!")
                self.var_switch_F.set(False)
                self.save_config()
                return

            dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")

            if not os.path.exists(dnconsole_path):
                self.log_error(f"Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
                self.var_switch_F.set(False)
                self.save_config()
                return

            self.log_info(f"⚡ [NHỊ KIỀU] Công tắc vừa trượt ON ➔ Khởi chạy ngay thao tác trên Tab: {tab_name} (Index: {tab_index})...")
            threading.Thread(target=self._execute_card_F_nhi_kieu, args=(dnconsole_path, tab_name, tab_index), daemon=True).start()

    def _create_unified_config_card(self):
        """Khung chứa 6 Card Cấu hình (Layout 2 hàng x 3 cột)"""
        self.container_cfg = ctk.CTkFrame(self, fg_color="transparent")
        self.container_cfg.grid(row=3, column=0, padx=(15, 4), pady=4, sticky="nsew")
        self.container_cfg.grid_columnconfigure((0, 2), weight=10)
        self.container_cfg.grid_columnconfigure(1, weight=8)
        self.container_cfg.grid_rowconfigure((0, 1), weight=1)

        # ------------------- CARD 1: PHỤ BẢN ĐƠN / ĐỘI (Cột 0, Row 0) -------------------
        self.card_E = ctk.CTkFrame(self.container_cfg, corner_radius=10)
        self.card_E.grid(row=0, column=0, padx=(0, 2), pady=(0, 4), sticky="nsew")
        self.card_E.grid_columnconfigure(0, weight=1)
        self.card_E.grid_rowconfigure((0, 1, 2, 3, 4, 5), weight=1)

        hdr_E = ctk.CTkFrame(self.card_E, fg_color="transparent")
        hdr_E.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="ew")
        hdr_E.grid_columnconfigure(0, weight=1)

        lbl_E = ctk.CTkLabel(hdr_E, text="PHỤ BẢN ĐƠN / ĐỘI", font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), text_color="#C084FC")
        lbl_E.grid(row=0, column=0, sticky="w")

        self.switch_E = ctk.CTkSwitch(
            hdr_E, text="", variable=self.var_switch_E, command=self._on_switch_E_toggled,
            width=36, height=18, switch_width=36, switch_height=18, fg_color="#374151", progress_color="#0284C7"
        )
        self.switch_E.grid(row=0, column=1, sticky="e")

        char_options = self._get_character_options()

        # Bảng Cấu hình chế độ Phụ Bản Đơn / Đội
        grid_modes = ctk.CTkFrame(self.card_E, fg_color="transparent")
        grid_modes.grid(row=1, column=0, padx=6, pady=2, sticky="ew")
        grid_modes.grid_columnconfigure(0, weight=0)
        grid_modes.grid_columnconfigure(1, weight=1)

        # Tiêu đề Phụ Bản Đơn
        lbl_pb_don = ctk.CTkLabel(
            grid_modes, text="Phụ Bản Đơn",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#38BDF8"
        )
        lbl_pb_don.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 2))

        # Hàng 1 (Phụ Bản Đơn): [ ] Cá Nhân | [ Menu NV Đơn ]
        box_don_check = ctk.CTkFrame(grid_modes, fg_color="transparent")
        box_don_check.grid(row=1, column=0, sticky="w", padx=(0, 4))

        self.chk_E_don = ctk.CTkCheckBox(
            box_don_check, text="Cá Nhân", variable=self.var_E_don, command=self._on_checkbox_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#0284C7", hover_color="#0369A1", checkbox_width=14, checkbox_height=14, border_width=2, corner_radius=5
        )
        self.chk_E_don.pack(side="left", padx=(0, 2))

        self.combo_E_don_char = ctk.CTkOptionMenu(
            grid_modes,
            values=char_options,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            height=24,
            width=75,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=lambda choice: self._on_checkbox_toggled()
        )
        self.combo_E_don_char.set(char_options[0] if char_options else "Xuất Chiến")
        self.combo_E_don_char.grid(row=1, column=1, sticky="w")

        # Tiêu đề Phụ Bản Đội
        lbl_pb_doi = ctk.CTkLabel(
            grid_modes, text="Phụ Bản Đội",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#38BDF8"
        )
        lbl_pb_doi.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(4, 2))

        # Hàng 2 (Phụ Bản Đội): [ ] Cá Nhân | [ ] Tổ Đội | [ Menu NV Team ]
        box_checks_team = ctk.CTkFrame(grid_modes, fg_color="transparent")
        box_checks_team.grid(row=3, column=0, sticky="w", padx=(0, 4))

        self.chk_E_canhan = ctk.CTkCheckBox(
            box_checks_team, text="Cá Nhân", variable=self.var_E_canhan, command=self._on_E_canhan_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#0284C7", hover_color="#0369A1", checkbox_width=14, checkbox_height=14, border_width=2, corner_radius=5
        )
        self.chk_E_canhan.pack(side="left", padx=(0, 2))

        divider_E_team = ctk.CTkFrame(box_checks_team, width=2, height=14, fg_color="#38BDF8")
        divider_E_team.pack(side="left", padx=2)

        self.chk_E_doi = ctk.CTkCheckBox(
            box_checks_team, text="Tổ Đội", variable=self.var_E_doi, command=self._on_E_doi_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#0284C7", hover_color="#0369A1", checkbox_width=14, checkbox_height=14, border_width=2, corner_radius=5
        )
        self.chk_E_doi.pack(side="left", padx=(2, 0))

        self.combo_E_team_char = ctk.CTkOptionMenu(
            grid_modes,
            values=char_options,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            height=24,
            width=75,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=lambda choice: self._on_checkbox_toggled()
        )
        self.combo_E_team_char.set(char_options[0] if char_options else "Xuất Chiến")
        self.combo_E_team_char.grid(row=3, column=1, sticky="w")

        # Đường gạch ngang phân cách giữa phần Chế độ/Menu (trên) và 4 Phụ bản (dưới)
        divider_horiz_E = ctk.CTkFrame(self.card_E, height=1, fg_color="#0284C7")
        divider_horiz_E.grid(row=2, column=0, padx=8, pady=(4, 4), sticky="ew")

        # 4 Mục Phụ Bản xếp hàng ngang (2 mục mỗi bên, 2 hàng)
        row_pb1 = ctk.CTkFrame(self.card_E, fg_color="transparent")
        row_pb1.grid(row=3, column=0, padx=8, pady=2, sticky="ew")
        row_pb1.grid_columnconfigure(0, weight=0, minsize=70)
        row_pb1.grid_columnconfigure(1, weight=1)

        self.chk_E1 = ctk.CTkCheckBox(row_pb1, text="PB 20", variable=self.var_E1, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#0284C7", hover_color="#0369A1", checkbox_width=14, checkbox_height=14, border_width=2, corner_radius=5)
        self.chk_E1.grid(row=0, column=0, sticky="w")

        self.chk_E2 = ctk.CTkCheckBox(row_pb1, text="PB 50", variable=self.var_E2, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#0284C7", hover_color="#0369A1", checkbox_width=14, checkbox_height=14, border_width=2, corner_radius=5)
        self.chk_E2.grid(row=0, column=1, sticky="w")

        row_pb2 = ctk.CTkFrame(self.card_E, fg_color="transparent")
        row_pb2.grid(row=4, column=0, padx=8, pady=(2, 6), sticky="ew")
        row_pb2.grid_columnconfigure(0, weight=0, minsize=70)
        row_pb2.grid_columnconfigure(1, weight=1)

        self.chk_E3 = ctk.CTkCheckBox(row_pb2, text="PB 80", variable=self.var_E3, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#0284C7", hover_color="#0369A1", checkbox_width=14, checkbox_height=14, border_width=2, corner_radius=5)
        self.chk_E3.grid(row=0, column=0, sticky="w")

        self.chk_E4 = ctk.CTkCheckBox(row_pb2, text="PB 110", variable=self.var_E4, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#0284C7", hover_color="#0369A1", checkbox_width=14, checkbox_height=14, border_width=2, corner_radius=5)
        self.chk_E4.grid(row=0, column=1, sticky="w")

        # ------------------- CARD 2: BOSS THẾ GIỚI (Cột 1, Row 0) -------------------
        self.card_C = ctk.CTkFrame(self.container_cfg, corner_radius=10)
        self.card_C.grid(row=0, column=1, padx=2, pady=(0, 4), sticky="nsew")
        self.card_C.grid_columnconfigure(0, weight=1)
        self.card_C.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

        hdr_C = ctk.CTkFrame(self.card_C, fg_color="transparent")
        hdr_C.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="ew")
        hdr_C.grid_columnconfigure(0, weight=1)

        lbl_C = ctk.CTkLabel(hdr_C, text="BOSS THẾ GIỚI", font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), text_color="#FBBF24")
        lbl_C.grid(row=0, column=0, sticky="w")

        self.switch_C = ctk.CTkSwitch(
            hdr_C, text="", variable=self.var_switch_C, command=self._on_switch_C_toggled,
            width=36, height=18, switch_width=36, switch_height=18, fg_color="#374151", progress_color="#D97706"
        )
        self.switch_C.grid(row=0, column=1, sticky="e")

        # Hàng 1: Menu Xuất Chiến (Đồng nhất với Card 1)
        self.combo_C_char = ctk.CTkOptionMenu(
            self.card_C,
            values=char_options,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            height=24,
            width=75,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=lambda choice: self._on_checkbox_toggled()
        )
        self.combo_C_char.set(char_options[0] if char_options else "Xuất Chiến")
        self.combo_C_char.grid(row=1, column=0, padx=12, pady=1, sticky="w")

        # Hàng 2: Boss Sáng
        self.chk_C1 = ctk.CTkCheckBox(self.card_C, text="Boss Sáng", variable=self.var_C1, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#D97706", hover_color="#B45309", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_C1.grid(row=2, column=0, padx=12, pady=1, sticky="w")

        # Hàng 3: Boss Trưa
        self.chk_C2 = ctk.CTkCheckBox(self.card_C, text="Boss Trưa", variable=self.var_C2, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#D97706", hover_color="#B45309", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_C2.grid(row=3, column=0, padx=12, pady=1, sticky="w")

        # Hàng 4: Vé + Menu thả xuất số thứ tự 1,2,3,4,5
        row_C_ve = ctk.CTkFrame(self.card_C, fg_color="transparent")
        row_C_ve.grid(row=4, column=0, padx=12, pady=(0, 6), sticky="w")

        self.chk_C3 = ctk.CTkCheckBox(
            row_C_ve, text="Vé", variable=self.var_C3, command=self._on_checkbox_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            fg_color="#D97706", hover_color="#B45309", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
        )
        self.chk_C3.pack(side="left", padx=(0, 6))

        self.combo_C_ve = ctk.CTkOptionMenu(
            row_C_ve,
            values=["1", "2", "3", "4", "5"],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            height=24,
            width=50,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=lambda choice: self._on_checkbox_toggled()
        )
        self.combo_C_ve.set("1")
        self.combo_C_ve.pack(side="left")

        # ------------------- CARD 3: DỊ GIỚI (Cột 2, Row 0) -------------------
        self.card_B = ctk.CTkFrame(self.container_cfg, corner_radius=10)
        self.card_B.grid(row=0, column=2, padx=(2, 0), pady=(0, 4), sticky="nsew")
        self.card_B.grid_columnconfigure(0, weight=1)
        self.card_B.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

        hdr_B = ctk.CTkFrame(self.card_B, fg_color="transparent")
        hdr_B.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="ew")
        hdr_B.grid_columnconfigure(0, weight=1)

        lbl_B = ctk.CTkLabel(hdr_B, text="DỊ GIỚI", font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), text_color="#34D399")
        lbl_B.grid(row=0, column=0, sticky="w")

        self.switch_B = ctk.CTkSwitch(
            hdr_B, text="", variable=self.var_switch_B, command=self._on_switch_B_toggled,
            width=36, height=18, switch_width=36, switch_height=18, fg_color="#374151", progress_color="#059669"
        )
        self.switch_B.grid(row=0, column=1, sticky="e")

        # Row 1: Phúc Thần + ( OFF / ON )
        row_B1 = ctk.CTkFrame(self.card_B, fg_color="transparent")
        row_B1.grid(row=1, column=0, padx=12, pady=1, sticky="ew")

        self.chk_B1 = ctk.CTkCheckBox(row_B1, text="Phúc Thần", variable=self.var_B1, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#059669", hover_color="#047857", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_B1.pack(side="left")

        lbl_B1_tag = ctk.CTkLabel(row_B1, text="( OFF / ON )", font=ctk.CTkFont(family="Segoe UI", size=10, weight="normal"), text_color="gray60")
        lbl_B1_tag.pack(side="right")

        # Row 2: Ký Lục + ( OFF / ON )
        row_B2 = ctk.CTkFrame(self.card_B, fg_color="transparent")
        row_B2.grid(row=2, column=0, padx=12, pady=1, sticky="ew")

        self.chk_B2 = ctk.CTkCheckBox(row_B2, text="Ký Lục", variable=self.var_B2, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#059669", hover_color="#047857", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_B2.pack(side="left")

        lbl_B2_tag = ctk.CTkLabel(row_B2, text="( OFF / ON )", font=ctk.CTkFont(family="Segoe UI", size=10, weight="normal"), text_color="gray60")
        lbl_B2_tag.pack(side="right")

        # Row 3: Rút Gọn + ( OFF / ON )
        row_B3 = ctk.CTkFrame(self.card_B, fg_color="transparent")
        row_B3.grid(row=3, column=0, padx=12, pady=1, sticky="ew")

        self.chk_B3 = ctk.CTkCheckBox(row_B3, text="Rút Gọn", variable=self.var_B3, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#059669", hover_color="#047857", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_B3.pack(side="left")

        lbl_B3_tag = ctk.CTkLabel(row_B3, text="( OFF / ON )", font=ctk.CTkFont(family="Segoe UI", size=10, weight="normal"), text_color="gray60")
        lbl_B3_tag.pack(side="right")

        # Row 4: Dị Giới Đêm
        row_B4 = ctk.CTkFrame(self.card_B, fg_color="transparent")
        row_B4.grid(row=4, column=0, padx=12, pady=(0, 6), sticky="ew")

        self.chk_B4 = ctk.CTkCheckBox(row_B4, text="Dị Giới Đêm", variable=self.var_B4, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#059669", hover_color="#047857", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_B4.pack(side="left")

        # ------------------- CARD 4: TỔ ĐỘI (Cột 0, Row 1) -------------------
        self.card_G = ctk.CTkFrame(self.container_cfg, corner_radius=10)
        self.card_G.grid(row=1, column=0, padx=(0, 2), pady=(4, 0), sticky="nsew")
        self.card_G.grid_columnconfigure(0, weight=1)
        self.card_G.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

        hdr_G = ctk.CTkFrame(self.card_G, fg_color="transparent")
        hdr_G.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="ew")
        hdr_G.grid_columnconfigure(0, weight=1)

        self.lbl_G = ctk.CTkLabel(hdr_G, text="TỔ ĐỘI", font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), text_color="#FB923C")
        self.lbl_G.grid(row=0, column=0, sticky="w")

        self.chk_G1 = ctk.CTkCheckBox(self.card_G, text="G1", variable=self.var_G1, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_G1.grid(row=1, column=0, padx=12, pady=2, sticky="w")

        self.chk_G2 = ctk.CTkCheckBox(self.card_G, text="G2", variable=self.var_G2, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_G2.grid(row=2, column=0, padx=12, pady=2, sticky="w")

        self.chk_G3 = ctk.CTkCheckBox(self.card_G, text="G3", variable=self.var_G3, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_G3.grid(row=3, column=0, padx=12, pady=2, sticky="w")

        self.chk_G4 = ctk.CTkCheckBox(self.card_G, text="G4", variable=self.var_G4, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_G4.grid(row=4, column=0, padx=12, pady=(0, 6), sticky="w")

        # ------------------- CARD 5: 40 NPC (Cột 1, Row 1) -------------------
        self.card_D = ctk.CTkFrame(self.container_cfg, corner_radius=10)
        self.card_D.grid(row=1, column=1, padx=2, pady=(4, 0), sticky="nsew")
        self.card_D.grid_columnconfigure(0, weight=1)
        self.card_D.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

        hdr_D = ctk.CTkFrame(self.card_D, fg_color="transparent")
        hdr_D.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="ew")
        hdr_D.grid_columnconfigure(0, weight=1)

        lbl_D = ctk.CTkLabel(hdr_D, text="40 NPC", font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), text_color="#F87171")
        lbl_D.grid(row=0, column=0, sticky="w")

        self.switch_D = ctk.CTkSwitch(
            hdr_D, text="", variable=self.var_switch_D, command=self._on_switch_D_toggled,
            width=36, height=18, switch_width=36, switch_height=18, fg_color="#374151", progress_color="#DC2626"
        )
        self.switch_D.grid(row=0, column=1, sticky="e")

        self.chk_D1 = ctk.CTkCheckBox(self.card_D, text="D1", variable=self.var_D1, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#DC2626", hover_color="#B91C1C", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_D1.grid(row=1, column=0, padx=12, pady=2, sticky="w")

        self.chk_D2 = ctk.CTkCheckBox(self.card_D, text="D2", variable=self.var_D2, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#DC2626", hover_color="#B91C1C", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_D2.grid(row=2, column=0, padx=12, pady=2, sticky="w")

        self.chk_D3 = ctk.CTkCheckBox(self.card_D, text="D3", variable=self.var_D3, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#DC2626", hover_color="#B91C1C", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_D3.grid(row=3, column=0, padx=12, pady=2, sticky="w")

        self.chk_D4 = ctk.CTkCheckBox(self.card_D, text="D4", variable=self.var_D4, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#DC2626", hover_color="#B91C1C", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_D4.grid(row=4, column=0, padx=12, pady=(0, 6), sticky="w")

        # ------------------- CARD 6: NHỊ KIỀU (Cột 2, Row 1) -------------------
        self.card_F = ctk.CTkFrame(self.container_cfg, corner_radius=10)
        self.card_F.grid(row=1, column=2, padx=(2, 0), pady=(4, 0), sticky="nsew")
        self.card_F.grid_columnconfigure(0, weight=1)
        self.card_F.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

        hdr_F = ctk.CTkFrame(self.card_F, fg_color="transparent")
        hdr_F.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="ew")
        hdr_F.grid_columnconfigure(0, weight=1)

        lbl_F = ctk.CTkLabel(hdr_F, text="NHỊ KIỀU", font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), text_color="#22D3EE")
        lbl_F.grid(row=0, column=0, sticky="w")

        self.switch_F = ctk.CTkSwitch(
            hdr_F, text="", variable=self.var_switch_F, command=self._on_switch_F_toggled,
            width=36, height=18, switch_width=36, switch_height=18, fg_color="#374151", progress_color="#0891B2"
        )
        self.switch_F.grid(row=0, column=1, sticky="e")

        self.chk_F1 = ctk.CTkCheckBox(self.card_F, text="F1", variable=self.var_F1, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#0891B2", hover_color="#0E7490", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_F1.grid(row=1, column=0, padx=12, pady=2, sticky="w")

        self.chk_F2 = ctk.CTkCheckBox(self.card_F, text="F2", variable=self.var_F2, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#0891B2", hover_color="#0E7490", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_F2.grid(row=2, column=0, padx=12, pady=2, sticky="w")

        self.chk_F3 = ctk.CTkCheckBox(self.card_F, text="F3", variable=self.var_F3, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#0891B2", hover_color="#0E7490", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_F3.grid(row=3, column=0, padx=12, pady=2, sticky="w")

        self.chk_F4 = ctk.CTkCheckBox(self.card_F, text="F4", variable=self.var_F4, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"), fg_color="#0891B2", hover_color="#0E7490", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_F4.grid(row=4, column=0, padx=12, pady=(0, 6), sticky="w")

    # --- HÀM CẬP NHẬT TRẠNG THÁI ---
    def log_info(self, message: str):
        """Cập nhật thông tin lên thanh trạng thái & ô ghi Log"""
        self.lbl_status.configure(text=f"Thông báo: {message}")
        if hasattr(self, 'txt_log'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", f"[{timestamp}] ℹ️ {message}\n")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")

    def log_error(self, message: str):
        """Cập nhật lỗi lên thanh trạng thái & ô ghi Log"""
        self.lbl_status.configure(text=f"Lỗi: {message}")
        if hasattr(self, 'txt_log'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", f"[{timestamp}] ❌ {message}\n")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")

    def _toggle_theme(self):
        if self.switch_theme.get() == 1:
            ctk.set_appearance_mode("Dark")
            self.switch_theme.configure(text="Tối")
        else:
            ctk.set_appearance_mode("Light")
            self.switch_theme.configure(text="Sáng")

    def _exec_cmd(self, cmd_list, text=False):
        """Thực thi lệnh ADB/LDConsole an toàn, tự động chuyển hướng trực tiếp sang adb.exe để vượt lỗi WinError 740/Admin elevation"""
        # Kiểm tra nếu đây là lệnh ADB gọi qua dnconsole/ldconsole (VD: [dnconsole, 'adb', '--index', '1', '--command', '...'])
        if len(cmd_list) >= 6 and cmd_list[1] == "adb" and "--index" in cmd_list and "--command" in cmd_list:
            try:
                idx_pos = cmd_list.index("--index") + 1
                cmd_pos = cmd_list.index("--command") + 1
                tab_idx = int(cmd_list[idx_pos])
                raw_subcmd = str(cmd_list[cmd_pos]).strip()

                device_id = f"emulator-{5554 + (tab_idx * 2)}"
                adb_path = os.path.join(self.ld_path, "adb.exe")

                if os.path.exists(adb_path):
                    if raw_subcmd.lower().startswith("pull "):
                        parts = raw_subcmd.split(maxsplit=2)
                        if len(parts) >= 3:
                            remote_p = parts[1].strip('"')
                            local_p = parts[2].strip('"')
                            direct_adb_cmd = [adb_path, "-s", device_id, "pull", remote_p, local_p]
                        else:
                            direct_adb_cmd = [adb_path, "-s", device_id] + raw_subcmd.split()
                    else:
                        subcmd_parts = raw_subcmd.split()
                        if subcmd_parts and subcmd_parts[0].lower() == "shell":
                            subcmd_parts = subcmd_parts[1:]
                        direct_adb_cmd = [adb_path, "-s", device_id, "shell"] + subcmd_parts
                        
                    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "creationflags": creation_flags}
                    if text:
                        kwargs["text"] = True
                        kwargs["encoding"] = "utf-8"
                        kwargs["errors"] = "ignore"
                    
                    res = subprocess.run(direct_adb_cmd, **kwargs)
                    if res.returncode == 0:
                        return res
            except Exception:
                pass

        # Fallback chạy lệnh trực tiếp thông thường
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "creationflags": creation_flags
        }
        if text:
            kwargs["text"] = True
            kwargs["encoding"] = "utf-8"
            kwargs["errors"] = "ignore"

        try:
            return subprocess.run(cmd_list, **kwargs)
        except OSError as e:
            if getattr(e, 'winerror', None) == 740 or "740" in str(e):
                cmd_str = " ".join([f'"{arg}"' if " " in str(arg) else str(arg) for arg in cmd_list])
                return subprocess.run(f'cmd /c {cmd_str}', shell=True, **kwargs)
            raise e

    def _is_ld_loaded_100(self, dnconsole_path: str, tab_index: str) -> bool:
        """Kiểm tra nhanh trạng thái nạp 100% của giả lập LDPlayer qua list2 (không bị đứng/treo ADB)"""
        try:
            res = self._exec_cmd([dnconsole_path, "list2"], text=True)
            if res and res.stdout:
                for line in res.stdout.strip().splitlines():
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) >= 5 and parts[0] == str(tab_index):
                        # Cột 4 (phần tử thứ 5) chính là android_started (1 = Đã nạp xong 100%, 0 = Đang nạp/Tắt)
                        if parts[4] == "1":
                            return True
        except Exception:
            pass
        return False

    def dung_tat_ca_hoat_dong(self):
        """Dừng khẩn cấp toàn bộ các tiến trình, luồng chạy ngầm của Tool"""
        self.stop_requested = True
        if hasattr(self, 'var_switch_B'):
            self.var_switch_B.set(False)
        self.after(0, self.save_config)
        self.log_error("🛑 Đã bấm DỪNG KHẨN CẤP! Đang hủy tất cả hoạt động và khôi phục nút bấm...")
        
        # Khôi phục trạng thái giao diện lập tức
        if hasattr(self, 'btn_enter_game'):
            self.btn_enter_game.configure(state="normal", text="TS Origin")
        if hasattr(self, 'btn_refresh'):
            self.btn_refresh.configure(state="normal", text="Làm Mới")

    def _should_stop_di_gioi(self) -> bool:
        """Kiểm tra nếu người dùng đã bấm nút Dừng hoặc công tắc Card Dị Giới bị tắt"""
        if self.stop_requested or not self.var_switch_B.get():
            self.stop_requested = False
            self.var_switch_B.set(False)
            self.after(0, self.save_config)
            self.after(0, self.log_info, "🛑 [DỊ GIỚI ĐÊM] Đã dừng toàn bộ hoạt động Card Dị Giới Đêm theo yêu cầu của nút Dừng!")
            return True
        return False

    # --- QUÉT VÀ CẬP NHẬT DỮ LIỆU LDPLAYER (ASYNC) ---
    def refresh_ld_tabs_async(self):
        """Kích hoạt quét LDPlayer trong Thread riêng biệt tránh đơ UI"""
        if self.is_scanning:
            return

        self.is_scanning = True
        self.btn_refresh.configure(state="disabled", text="Đang quét...")
        self.lbl_status.configure(text="Đang tìm kiếm các tab LDPlayer...")

        threading.Thread(target=self._worker_scan_ld, daemon=True).start()

    def _worker_scan_ld(self):
        """Worker thread chạy quét console"""
        try:
            dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")

            if not os.path.exists(dnconsole_path):
                self.after(0, self._update_ui_ld_scan_result, [], f"Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
                return

            result = self._exec_cmd([dnconsole_path, "list2"], text=True)

            lines = result.stdout.strip().split('\n')
            new_tabs = []
            dict_temp = {}

            for line in lines:
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 2:
                        idx = parts[0].strip()
                        name = parts[1].strip()
                        new_tabs.append(name)
                        dict_temp[name] = idx

            self.after(0, self._update_ui_ld_scan_result, new_tabs, None, dict_temp)

        except Exception as e:
            self.after(0, self._update_ui_ld_scan_result, [], str(e))

    def _update_ui_ld_scan_result(self, tab_names: list, error_msg: str = None, dict_map: dict = None):
        """Cập nhật giao diện sau khi kết thúc quét"""
        self.is_scanning = False
        self.btn_refresh.configure(state="normal", text="Làm Mới")

        if error_msg:
            self.combo_ld_tabs.configure(values=["Lỗi quét dữ liệu"])
            self.combo_ld_tabs.set("Lỗi quét dữ liệu")
            self.lbl_status.configure(text="Lỗi quét LDPlayer")
            self.lbl_tab_count.configure(text="Tab LD: 0")
            self.log_error(f"Quét tab thất bại: {error_msg}")
            return

        if dict_map is not None:
            self.dict_name_to_index = dict_map

        if tab_names:
            current_selection = self.combo_ld_tabs.get()
            self.combo_ld_tabs.configure(values=tab_names)

            saved_tab = getattr(self, 'saved_selected_tab', None)
            if current_selection in tab_names and current_selection not in ["Đang quét tab...", "Lỗi quét dữ liệu", "Không tìm thấy tab LD nào"]:
                self.combo_ld_tabs.set(current_selection)
            elif saved_tab and saved_tab in tab_names:
                self.combo_ld_tabs.set(saved_tab)
            else:
                self.combo_ld_tabs.set(tab_names[0])

            count = len(tab_names)
            self.lbl_status.configure(text="Quét danh sách thành công.")
            self.lbl_tab_count.configure(text=f"Tab LD: {count}")
            self.log_info(f"Đã phát hiện {count} tab LDPlayer: {', '.join(tab_names)}")
        else:
            self.combo_ld_tabs.configure(values=["Không tìm thấy tab LD nào"])
            self.combo_ld_tabs.set("Không tìm thấy tab LD nào")
            self.lbl_status.configure(text="Không tìm thấy giả lập LDPlayer đang khởi tạo.")
            self.lbl_tab_count.configure(text="Tab LD: 0")
            self.log_info("Không tìm thấy tab LDPlayer nào.")

    # ---- HÀM XỬ LÝ SỰ KIỆN TS ORIGIN (TỰ ĐỘNG BẤM ICON MỞ GAME) ----
    def xu_ly_ts_origin(self):
        tab, idx = self._get_selected_ld_info()
        if idx is None:
            self.log_error("Vui lòng chọn một Tab LDPlayer trước khi bấm mở game!")
            return

        server = self.combo_server.get()
        self.log_info(f"Bắt đầu quy trình: Bật Giả lập LDPlayer (Tab {tab}) ➔ Chờ Load 100% ➔ Mở App Game ➔ Tự động chọn Máy Chủ '{server}'...")
        self.btn_enter_game.configure(state="disabled", text="Đang mở Game...")

        # Chạy lệnh mở app trong Thread riêng để không làm treo giao diện
        threading.Thread(target=self._worker_launch_ts_origin, args=(tab, idx, server), daemon=True).start()

    def _worker_launch_ts_origin(self, tab_name: str, tab_index: str, server_name: str):
        """Worker thread tự động quét và khởi chạy ứng dụng TS Origin trên giả lập LDPlayer"""
        try:
            dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")

            if not os.path.exists(dnconsole_path):
                self.after(0, self._finish_launch_ts_origin, False, f"Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
                return

            # Bước 1: Gửi lệnh mở/kích hoạt giả lập LDPlayer từ màn hình (Nếu chưa nạp mới khởi chạy, nếu đã chạy sẵn thì giữ nguyên vị trí)
            if not self._is_ld_loaded_100(dnconsole_path, tab_index):
                self.after(0, self.log_info, f"🖥️ [Bước 1/4] Đang khởi động Giả lập LDPlayer Tab: {tab_name} (Index: {tab_index})...")
                self._exec_cmd([dnconsole_path, "launch", "--index", str(tab_index)])
            else:
                self.after(0, self.log_info, f"🖥️ Tab LDPlayer {tab_name} (Index: {tab_index}) đã mở sẵn, giữ nguyên vị trí cửa sổ màn hình...")

            # Bước 2: Theo dõi tiến trình chờ nạp 100% qua console list2 (nhanh, tức thì, không bị đơ/treo ADB)
            self.after(0, self.log_info, f"⏳ [Bước 2/4] Đang chờ giả lập LDPlayer Tab: {tab_name} (Index: {tab_index}) load 100%...")
            boot_start = time.time()
            emulator_ready = False

            for check_idx in range(40):
                if self.stop_requested:
                    self.stop_requested = False
                    self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                    return

                if self._is_ld_loaded_100(dnconsole_path, tab_index):
                    emulator_ready = True
                    boot_time = round(time.time() - boot_start, 1)
                    self.after(0, self.log_info, f"✅ Giả lập LDPlayer đã load 100% thành công sau {boot_time}s! Đang tiến hành mở Game...")
                    break

                elapsed = int(time.time() - boot_start)
                if elapsed > 0 and elapsed % 3 == 0:
                    self.after(0, self.log_info, f"⏳ [Bước 2/4] Giả lập LDPlayer đang nạp màn hình chính... ({elapsed}s)")
                time.sleep(2.5)

            if self.stop_requested:
                self.stop_requested = False
                self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                return

            if not emulator_ready:
                self.after(0, self.log_info, "ℹ️ Tiếp tục tiến trình mở ứng dụng Game...")
            else:
                self.after(0, self.log_info, "⏳ Đang hoãn 6 giây cho màn hình giả lập ổn định hoàn toàn...")
                time.sleep(6.0) # Tạm dừng 6s cho màn hình desktop giả lập ổn định hẳn

            # Bước 3: Dùng ADB để quét danh sách các app/game cài trên giả lập LDPlayer này
            self.after(0, self.log_info, f"🎮 [Bước 3/4] Đang quét danh sách Ứng Dụng trên Tab {tab_name}...")
            
            target_pkg = None
            installed_packages = []
            
            # Thử 5 lần quét package qua ADB (đề phòng Package Manager của Android vừa boot xong đang bận)
            for pkg_attempt in range(5):
                if self.stop_requested:
                    self.stop_requested = False
                    self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                    return

                res = self._exec_cmd(
                    [dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell pm list packages -3"],
                    text=True
                )
                stdout_text = res.stdout.strip() if res else ""
                
                # Nếu quét package -3 rỗng, thử quét toàn bộ package hệ thống
                if not stdout_text:
                    res = self._exec_cmd(
                        [dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell pm list packages"],
                        text=True
                    )
                    stdout_text = res.stdout.strip() if res else ""

                installed_packages = []
                for line in stdout_text.splitlines():
                    line = line.strip()
                    if line.startswith("package:"):
                        pkg_name = line.replace("package:", "").strip()
                        if pkg_name:
                            installed_packages.append(pkg_name)

                # Dò tìm package phù hợp theo danh sách từ khóa rộng của TS Origin
                ts_keywords = ["ts", "origin", "chinesegamer", "vng", "vtc", "tso"]
                for pkg in installed_packages:
                    for kw in ts_keywords:
                        if kw in pkg.lower():
                            target_pkg = pkg
                            break
                    if target_pkg:
                        break

                if target_pkg:
                    break
                time.sleep(1.5)

            # Danh sách fallback nếu không dò tìm thấy package
            fallback_pkgs = ["com.chinesegamer.tsotw", "com.chinesegamer.tsorigin", "com.vng.tsorigin", "com.vtc.tsorigin"]

            if target_pkg:
                self.after(0, self.log_info, f"🎯 Đã phát hiện Package Game: '{target_pkg}'! Đang mở ứng dụng...")
            else:
                target_pkg = installed_packages[0] if installed_packages else fallback_pkgs[0]
                self.after(0, self.log_info, f"ℹ️ Khởi chạy Package Game mặc định: '{target_pkg}'...")

            # Khởi chạy Game qua ADB ngầm để giữ nguyên vị trí cửa sổ LDPlayer
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell monkey -p {target_pkg} -c android.intent.category.LAUNCHER 1"])
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell am start -W -n {target_pkg}"])
            
            # Khởi chạy bổ sung các package fallback nếu không tìm thấy package bằng từ khóa
            if not installed_packages or not target_pkg:
                for fb_pkg in fallback_pkgs:
                    self._exec_cmd([dnconsole_path, "runapp", "--index", str(tab_index), "--packagename", fb_pkg])
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell monkey -p {fb_pkg} -c android.intent.category.LAUNCHER 1"])

            # 4. Kích hoạt "Mắt Thần" OpenCV quét nhận biết Bảng Chọn Máy Chủ qua ảnh mẫu 'login_server.png' / 'login_redorb.png'
            self.after(0, self.log_info, "⏳ [Bước 4/4] Hoãn 20 giây trước khi Mắt Thần OpenCV quét Bảng Máy Chủ...")
            time.sleep(20.0)
            self.after(0, self.log_info, "👁️ [Bước 4/4] Mắt thần OpenCV đang quét theo dõi màn hình Chọn Máy Chủ TS Origin...")
            
            icon_server_detected = False
            start_wait = time.time()
            consecutive_matches = 0
            
            # Quét tìm ảnh login_server.png / login_redorb.png với ngưỡng 88%, yêu cầu 2 lần khớp liên tiếp (cách nhau 2s) để đảm bảo hình ảnh đã hiện ổn định
            while time.time() - start_wait < 30.0:
                if self.stop_requested:
                    self.stop_requested = False
                    self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                    return

                is_x, is_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_server.png", threshold=0.88)
                if is_x is None:
                    is_x, is_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_redorb.png", threshold=0.88)

                if is_x is not None and is_y is not None:
                    consecutive_matches += 1
                    if consecutive_matches >= 2:
                        icon_server_detected = True
                        elapsed = round(time.time() - start_wait, 1)
                        self.after(0, self.log_info, f"✅ Mắt thần đã xác nhận Bảng Máy Chủ hiển thị đầy đủ ổn định sau {elapsed}s!")
                        break
                else:
                    consecutive_matches = 0
                time.sleep(2.0)

            # Tọa độ neo chuẩn đo đạc trực tiếp từ ảnh thật (Nút tròn đỏ X=312, Tâm khung cuộn X=380, Y=420)
            panel_x, panel_y = 380, 420
            red_orb_x = 312 # Tọa độ X chuẩn của cột ô tròn màu đỏ

            # Tạm hoãn 2.0s sau khi nhận diện màn hình Bảng Chọn Máy Chủ
            self.after(0, self.log_info, "⏳ Mắt thần đã nhận diện Bảng Máy Chủ! Tạm hoãn 2.0s nạp hiệu ứng...")
            time.sleep(2.0)

            # Quét kiểm tra file ảnh login_co.png, nếu phát hiện thì nhấp chọn nút login_co.png
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_co.png", threshold=0.75)
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"👁️ Mắt thần phát hiện nút 'login_co.png' tại ({co_x}, {co_y})! Đang nhấp chọn...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {co_x} {co_y}"])
                time.sleep(1.0)

            # Tạo tên file ảnh mẫu linh hoạt theo tên máy chủ được chọn trong Tool (VD: "Điêu Thuyền" -> "server_dieuthuyen.png")
            def to_snake_case(text: str) -> str:
                text = text.replace('Đ', 'D').replace('đ', 'd')
                nfkd = unicodedata.normalize('NFKD', text)
                no_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])
                clean = re.sub(r'[^a-zA-Z0-9]', '_', no_accent).lower()
                return re.sub(r'_+', '_', clean).strip('_')

            server_img_name = f"server_{to_snake_case(server_name).replace('_', '')}.png"

            # 5. THAO TÁC CUỘN VÀ TÌM MÁY CHỦ SỬ DỤNG MẮT THẦN
            self.after(0, self.log_info, f"📜 Bắt đầu cuộn tìm máy chủ '{server_name}'...")
            
            # Tọa độ vùng cuộn danh sách đo đạc chính xác từ ảnh thật (X=350, Y nằm trong dải 380 đến 620)
            scroll_x = 350
            swipe_ms = 700  # Vuốt chậm 700ms giúp danh sách di chuyển từ từ mượt mà, không bị trôi quá nhanh
            
            # Cuộn XUỐNG: Vuốt từ dưới danh sách (Y=580) lên trên (Y=400) với tốc độ vừa phải (700ms)
            y_start_down = 580
            y_end_down = 400

            # Cuộn LÊN: Vuốt từ trên danh sách (Y=400) xuống dưới (Y=580) với tốc độ vừa phải (700ms)
            y_start_up = 400
            y_end_up = 580
            
            found_server = False

            # Giai đoạn 1: Cuộn XUỐNG dưới tối đa 10 lần
            for step in range(10):
                if self.stop_requested:
                    self.stop_requested = False
                    self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                    return
                # Quét tìm ảnh mẫu của máy chủ mục tiêu (ngưỡng 75%)
                click_x, click_y = self._find_template_on_screen(dnconsole_path, tab_index, server_img_name, threshold=0.75)

                if click_x is not None and click_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần đã tìm thấy máy chủ '{server_name}' tại ({click_x}, {click_y})! Đang nhấp chọn...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {click_x} {click_y}"])
                    time.sleep(1.5)

                    # 🔍 Kiểm tra xem sau khi nhấp chọn có xuất hiện ảnh thông báo 'login_nkn.png' không
                    nkn_x, nkn_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_nkn.png", threshold=0.45)
                    if nkn_x is not None and nkn_y is not None:
                        self.after(0, self.log_info, f"⚠️ Nhấp chọn máy chủ '{server_name}' bị hiện 'login_nkn.png'! Tiếp tục cuộn tìm nhấp lại máy chủ '{server_name}'...")
                        # Không gán found_server = True, tiếp tục cuộn tìm nhấp lại máy chủ này!
                    else:
                        self.after(0, self.log_info, f"✅ Đã kết nối thành công máy chủ '{server_name}' (không bị dính login_nkn.png)!")
                        found_server = True
                        break

                # 🛑 Kiểm tra xem có xuất hiện máy chủ đầu tiên 'server_trieuvan.png' không (chỉ dừng cuộn khi đang tìm máy chủ khác)
                if server_img_name != "server_trieuvan.png":
                    tv_x, tv_y = self._find_template_on_screen(dnconsole_path, tab_index, "server_trieuvan.png", threshold=0.75)
                    if tv_x is not None and tv_y is not None:
                        self.after(0, self.log_info, "🛑 Mắt thần phát hiện máy chủ đầu tiên 'server_trieuvan.png'! Dừng cuộn xuống và chuẩn bị cuộn ngược lên lại...")
                        break

                # Thực hiện vuốt cuộn XUỐNG chầm chậm
                self.after(0, self.log_info, f"📜 [Cuộn xuống {step + 1}/10] Đang cuộn tìm máy chủ '{server_name}'...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input swipe {scroll_x} {y_start_down} {scroll_x} {y_end_down} {swipe_ms}"])
                time.sleep(1.5)

            # Giai đoạn 2: Nếu chưa kết nối thành công sau 10 lần cuộn xuống, cuộn NGƯỢC LÊN 10 lần để tìm nhấp lại
            if not found_server:
                self.after(0, self.log_info, f"🔄 Chưa vào được máy chủ '{server_name}'! Bắt đầu cuộn NGƯỢC LÊN 10 lần để tìm nhấp lại...")
                
                for step in range(10):
                    click_x, click_y = self._find_template_on_screen(dnconsole_path, tab_index, server_img_name, threshold=0.75)

                    if click_x is not None and click_y is not None:
                        self.after(0, self.log_info, f"🎯 Mắt thần tìm thấy máy chủ '{server_name}' tại ({click_x}, {click_y})! Đang nhấp chọn lại...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {click_x} {click_y}"])
                        time.sleep(1.5)

                        # 🔍 Kiểm tra xem sau khi nhấp chọn có xuất hiện 'login_nkn.png' không
                        nkn_x, nkn_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_nkn.png", threshold=0.45)
                        if nkn_x is not None and nkn_y is not None:
                            self.after(0, self.log_info, f"⚠️ Nhấp chọn máy chủ '{server_name}' bị hiện 'login_nkn.png'! Tiếp tục cuộn tìm nhấp lại...")
                        else:
                            self.after(0, self.log_info, f"✅ Đã kết nối thành công máy chủ '{server_name}' (không bị dính login_nkn.png)!")
                            found_server = True
                            break

                    # Vuốt cuộn NGƯỢC LÊN từ từ (700ms)
                    self.after(0, self.log_info, f"📜 [Cuộn ngược lên {step + 1}/10] Đang cuộn ngược lên tìm '{server_name}'...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input swipe {scroll_x} {y_start_up} {scroll_x} {y_end_up} {swipe_ms}"])
                    time.sleep(1.5)
                    time.sleep(1.5)

            # Giai đoạn 3: Nếu cuộn hết 20 lần mà vẫn không kết nối thành công -> DỪNG LẠI
            if not found_server:
                msg = f"❌ Đã cuộn 20 lần (10 xuống, 10 lên) nhưng máy chủ '{server_name}' vẫn báo 'login_nkn.png' không vào được. Đã dừng lại!"
                self.after(0, self._finish_launch_ts_origin, False, msg)
            else:
                msg = f"🚀 👁️ Đã chọn Máy chủ '{server_name}' & Đăng nhập thành công trên Tab: {tab_name} (Index: {tab_index})"
                self.after(0, self._finish_launch_ts_origin, True, msg)

        except Exception as e:
            self.after(0, self._finish_launch_ts_origin, False, f"Lỗi khởi chạy game: {str(e)}")

    def _finish_launch_ts_origin(self, success: bool, message: str):
        """Hoàn tất quá trình mở game, trả lại trạng thái nút bấm và kích hoạt luồng hoạt động tuần tự"""
        self.btn_enter_game.configure(state="normal", text="TS Origin")
        if success:
            self.log_info(message)
            tab_name, tab_index = self._get_selected_ld_info()
            if tab_index is not None:
                self._run_sequential_pipeline_async(tab_name, tab_index)
        else:
            self.log_error(message)

    # --- QUẢN LÝ LUỒNG CHẠY TUẦN TỰ 6 CARD HOẠT ĐỘNG (DỨT ĐIỂM TỪNG CARD) ---
    def _run_sequential_pipeline_async(self, tab_name: str, tab_index: str):
        """Kích hoạt luồng chạy ngầm 6 Card hoạt động tuần tự"""
        threading.Thread(target=self._worker_run_sequential_cards, args=(tab_name, tab_index), daemon=True).start()

    def _worker_run_sequential_cards(self, tab_name: str, tab_index: str):
        """Thực thi tuần tự 6 Card hoạt động: Phụ Bản Đơn/Đội (Card A) -> Boss TG (Card B) -> Dị Giới Đêm (Card C) -> Tổ Đội (Card D) -> 40 NPC (Card E) -> Nhị Kiều (Card F)"""
        try:
            dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")

            self.after(0, self.log_info, f"🚀 [TUẦN TỰ HOẠT ĐỘNG] Bắt đầu quét & thực thi 6 Card theo thứ tự trên Tab: {tab_name} (Index: {tab_index})...")

            # 📌 1/6: CARD PHỤ BẢN ĐƠN / ĐỘI (Card A)
            if self.stop_requested:
                self._handle_pipeline_stop()
                return
            self._execute_card_E_phu_ban_doi(dnconsole_path, tab_name, tab_index)

            # 📌 2/6: CARD BOSS THẾ GIỚI (Card B)
            if self.stop_requested:
                self._handle_pipeline_stop()
                return
            self._execute_card_C_boss_tg(dnconsole_path, tab_name, tab_index)

            # 📌 3/6: CARD DỊ GIỚI ĐÊM (Card C)
            if self.stop_requested:
                self._handle_pipeline_stop()
                return
            self._execute_card_B_di_gioi(dnconsole_path, tab_name, tab_index)

            # 📌 4/6: CARD TỔ ĐỘI (Card D)
            if self.stop_requested:
                self._handle_pipeline_stop()
                return
            self._execute_card_G_phu_ban_don(dnconsole_path, tab_name, tab_index)

            # 📌 5/6: CARD 40 NPC (Card E)
            if self.stop_requested:
                self._handle_pipeline_stop()
                return
            self._execute_card_D_40_npc(dnconsole_path, tab_name, tab_index)

            # 📌 6/6: CARD NHỊ KIỀU (Card F)
            if self.stop_requested:
                self._handle_pipeline_stop()
                return
            self._execute_card_F_nhi_kieu(dnconsole_path, tab_name, tab_index)

            self.after(0, self.log_info, f"🎉 [HOÀN THÀNH] Đã hoàn tất toàn bộ 6 Card hoạt động tuần tự dứt điểm trên Tab: {tab_name}")

        except Exception as e:
            self.after(0, self.log_error, f"❌ Lỗi luồng hoạt động tuần tự: {str(e)}")

    def dung_tat_ca_hoat_dong(self):
        """Nút Dừng ở hàng KHỞI ĐỘNG & SERVER: Dừng toàn bộ 6 card hoạt động và chuyển 6 công tắc về OFF"""
        self.stop_requested = True
        for prefix in ["B", "C", "D", "E", "F", "G"]:
            switch_attr = f"var_switch_{prefix}"
            if hasattr(self, switch_attr):
                getattr(self, switch_attr).set(False)
        self.save_config()
        self.after(0, self.log_info, "🛑 [DỪNG KHẨN CẤP] Đã bấm nút Dừng ➔ Dừng toàn bộ 6 card hoạt động và trả các công tắc về OFF!")

    def _should_stop_di_gioi(self) -> bool:
        """Kiểm tra điều kiện dừng cho Card 1 Dị Giới (bấm Dừng tổng hoặc gạt công tắc B về OFF)"""
        return self.stop_requested or not self.var_switch_B.get()

    def _should_stop_card_E(self) -> bool:
        """Kiểm tra điều kiện dừng cho Card 2 Phụ Bản Đơn/Đội (bấm Dừng tổng hoặc gạt công tắc E về OFF)"""
        return self.stop_requested or not self.var_switch_E.get()

    def _should_stop_card_C(self) -> bool:
        """Kiểm tra điều kiện dừng cho Card 4 Boss Thế Giới (bấm Dừng tổng hoặc gạt công tắc C về OFF)"""
        return self.stop_requested or not self.var_switch_C.get()

    def _should_stop_card_D(self) -> bool:
        """Kiểm tra điều kiện dừng cho Card 5 40 NPC (bấm Dừng tổng hoặc gạt công tắc D về OFF)"""
        return self.stop_requested or not self.var_switch_D.get()

    def _should_stop_card_F(self) -> bool:
        """Kiểm tra điều kiện dừng cho Card 6 Nhị Kiều (bấm Dừng tổng hoặc gạt công tắc F về OFF)"""
        return self.stop_requested or not self.var_switch_F.get()

    def _handle_pipeline_stop(self):
        """Xử lý dừng luồng an toàn khi bấm nút Dừng"""
        self.stop_requested = False
        self.after(0, self.log_info, "🛑 Đã dừng tiến trình tuần tự các hoạt động theo yêu cầu!")

    def _execute_card_B_di_gioi(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """Thực thi Card 1: DỊ GIỚI ĐÊM (B) dưới sự kiểm soát của công tắc gạt ON"""
        if self._should_stop_di_gioi():
            return

        screen_w, screen_h = self._get_emulator_screen_size(dnconsole_path, tab_index)

        # Tính toán tọa độ theo tỉ lệ màn hình (chuẩn 1280x720)
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

        self.after(0, self.log_info, f"🖥️ LDPlayer Tab '{tab_name}' ({screen_w}x{screen_h})")

        has_di_gioi = self.var_B4.get()

        # =========================================================================
        # 📌 2. VÀO DỊ GIỚI
        # =========================================================================
        self.after(0, self.log_info, "👁️ [DỊ GIỚI - Bước 2] Quét nhận diện map Dị Giới 'a_digioi.png' (85%)...")
        dg_x, dg_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_digioi.png", threshold=0.85)
        if dg_x is not None and dg_y is not None:
            self.after(0, self.log_info, f"🎯 Đã phát hiện map Dị Giới 'a_digioi.png' tại ({dg_x}, {dg_y}) ➔ Bỏ qua các thao tác trong Bước 2: Vào Dị Giới.")
        else:
            self.after(0, self.log_info, "👉 Chưa thấy map 'a_digioi.png' ➔ Tiến hành quét nút Vị Trí 'a_vitri.png' để vào Dị Giới...")
            if self._should_stop_di_gioi(): return
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y})! Nhấp chọn ngay...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                time.sleep(1.0)
            else:
                self.after(0, self.log_info, f"👉 Chưa thấy 'a_vitri.png' ➔ Click nút xanh lá góc dưới phải tại ({px_x}, {px_y}) để mở menu...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
                time.sleep(1.2)
                if self._should_stop_di_gioi(): return
                v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
                if v_x is not None and v_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y})! Đang nhấp chọn...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                    time.sleep(1.0)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'a_vitri.png' trong bảng menu.")

            if self._should_stop_di_gioi(): return

            self.after(0, self.log_info, f"👉 Click chọn tọa độ ({v1_x}, {v1_y})...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v1_x} {v1_y}"])
            time.sleep(1.0)

            if self._should_stop_di_gioi(): return

            self.after(0, self.log_info, f"👉 Click chọn tọa độ ({v2_x}, {v2_y})...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v2_x} {v2_y}"])
            time.sleep(1.0)

        # =========================================================================
        # 📌 3. ĐẾM GIỜ & TẮT KÝ LỤC (Nếu TÍCH ô Dị Giới Đêm)
        # =========================================================================
        if has_di_gioi:
            # 1. Đếm giờ đến 22H50 (đêm hôm nay)
            now = datetime.now()
            target_2250 = now.replace(hour=22, minute=50, second=0, microsecond=0)

            if now < target_2250:
                self.after(0, self.log_info, f"⏳ [DỊ GIỚI] Ô Dị Giới Đêm được tích chọn ➔ Nhường ưu tiên chạy trước: Đang đếm giờ chờ đến 22H50 (Hiện tại: {now.strftime('%H:%M:%S')})...")
                while datetime.now() < target_2250:
                    if self._should_stop_di_gioi():
                        return
                    time.sleep(0.5)

            if self._should_stop_di_gioi(): return

            self.after(0, self.log_info, "▶️ [DỊ GIỚI - 22H50] Đã đến 22H50! Bắt đầu thao tác tắt Ký Lục...")

            # Quét tìm biểu tượng a_ai.png (độ chính xác 85%)
            ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
            if ai_x is not None and ai_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Nhấp chọn ngay...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
                time.sleep(1.0)
            else:
                self.after(0, self.log_info, f"👉 Chưa thấy 'a_ai.png' ➔ Click nút xanh lá góc dưới phải tại ({px_x}, {px_y}) để mở menu...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
                time.sleep(1.2)
                if self._should_stop_di_gioi(): return
                ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
                if ai_x is not None and ai_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Đang nhấp chọn...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
                    time.sleep(1.0)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'a_ai.png' trong bảng menu.")

            if self._should_stop_di_gioi(): return

            self.after(0, self.log_info, f"👉 Click tọa độ ({c_x}, {c_y})...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {c_x} {c_y}"])
            time.sleep(1.0)

            if self._should_stop_di_gioi(): return

            # Quét ảnh mẫu a_kyluc.png (độ chính xác 95%)
            self.after(0, self.log_info, "👁️ Quét kiểm tra ảnh mẫu 'a_kyluc.png' (độ chính xác 95%)...")
            kl_x, kl_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_kyluc.png", threshold=0.95)
            if kl_x is None:
                self.after(0, self.log_info, f"🎯 Giao diện KHÔNG KHỚP ảnh 'a_kyluc.png' ➔ Click vị trí Ký Lục tại ({kl_tap_x}, {kl_tap_y})...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {kl_tap_x} {kl_tap_y}"])
                time.sleep(1.0)
            else:
                self.after(0, self.log_info, "ℹ️ Giao diện ĐÃ KHỚP ảnh mẫu 'a_kyluc.png' ➔ Bỏ qua.")

            if self._should_stop_di_gioi(): return

            self.after(0, self.log_info, f"👉 Click tọa độ xác nhận/đóng ({end_x}, {end_y})...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {end_x} {end_y}"])
            time.sleep(1.0)

            self.after(0, self.log_info, f"👉 Click lại nút xanh lá ({px_x}, {px_y}) để thu gọn bảng menu...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
            time.sleep(1.0)

            # 2. Tiếp tục đếm đến 00H05 (qua ngày mới)
            now = datetime.now()
            target_0005 = now.replace(hour=0, minute=5, second=0, microsecond=0)
            if now >= target_0005:
                target_0005 += timedelta(days=1)

            self.after(0, self.log_info, f"⏳ [DỊ GIỚI] Tiếp tục đếm giờ chờ đến 00H05 ngày mới (Hiện tại: {now.strftime('%H:%M:%S')})...")
            while datetime.now() < target_0005:
                if self._should_stop_di_gioi():
                    return
                time.sleep(0.5)

        if self._should_stop_di_gioi(): return

        # =========================================================================
        # 📌 4. VÀO DỊ GIỚI (LÚC 00H05) (Nếu TÍCH ô Dị Giới Đêm)
        # =========================================================================
        if has_di_gioi:
            self.after(0, self.log_info, "🚀 [DỊ GIỚI - 00H05] Kích hoạt quy trình Vào Dị Giới (00H05) của Card Dị Giới Đêm...")

            # Quét tìm biểu tượng a_vitri.png (độ chính xác 85%)
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y})! Nhấp chọn ngay...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                time.sleep(1.0)
            else:
                self.after(0, self.log_info, f"👉 Chưa thấy 'a_vitri.png' ➔ Click nút xanh lá góc dưới phải tại ({px_x}, {px_y}) để mở menu...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
                time.sleep(1.2)
                if self._should_stop_di_gioi(): return
                v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
                if v_x is not None and v_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y})! Đang nhấp chọn...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                    time.sleep(1.0)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'a_vitri.png' trong bảng menu.")

            if self._should_stop_di_gioi(): return

            self.after(0, self.log_info, f"👉 Click chọn tọa độ ({v1_x}, {v1_y})...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v1_x} {v1_y}"])
            time.sleep(1.0)

            if self._should_stop_di_gioi(): return

            self.after(0, self.log_info, f"👉 Click chọn tọa độ ({v2_x}, {v2_y})...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v2_x} {v2_y}"])
            time.sleep(1.0)

            self.after(0, self.log_info, "⚙️ [DỊ GIỚI] Hoàn thành thao tác Dị Giới Đêm (giữ nguyên ô tích).")

        # =========================================================================
        # 📌 5. CHẠY CÁC Ô CHECK PHÚC THẦN / KÝ LỤC / RÚT GỌN (ĐƯỢC TÍCH & KHÔNG TÍCH)
        # =========================================================================
        has_phuc_than = self.var_B1.get()
        has_ky_luc = self.var_B2.get()
        has_rut_gon = self.var_B3.get()

        # Ô Phúc Thần:
        if self._should_stop_di_gioi(): return
        self.after(0, self.log_info, f"▶️ [PHÚC THẦN] Kiểm tra ô Phúc Thần (Trạng thái: {'ĐƯỢC TÍCH' if has_phuc_than else 'KHÔNG TÍCH'})...")
        ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
        if ai_x is not None and ai_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Nhấp chọn ngay...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
            time.sleep(1.0)
        else:
            self.after(0, self.log_info, f"1. Click mở lại bảng menu tại ({px_x}, {px_y})...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
            time.sleep(1.2)
            if self._should_stop_di_gioi(): return
            ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
            if ai_x is not None and ai_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Đang nhấp chọn...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
                time.sleep(1.0)

        self.after(0, self.log_info, "3. Quét kiểm tra ảnh mẫu 'a_phucthan.png' (ngưỡng 95%)...")
        pt_x, pt_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_phucthan.png", threshold=0.95)
        if has_phuc_than:
            if pt_x is not None and pt_y is not None:
                self.after(0, self.log_info, f"🎯 [BẬT] Giao diện ĐÃ KHỚP ảnh mẫu 'a_phucthan.png' ➔ Click vào ({pt_tap_x}, {pt_tap_y}) để Bật Phúc Thần...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {pt_tap_x} {pt_tap_y}"])
                time.sleep(1.0)
            else:
                self.after(0, self.log_info, "ℹ️ [BẬT] Giao diện KHÔNG KHỚP ảnh mẫu 'a_phucthan.png' (Đã Bật sẵn) ➔ Bỏ qua.")
        else:
            if pt_x is not None and pt_y is not None:
                self.after(0, self.log_info, "ℹ️ [TẮT] Giao diện ĐÃ KHỚP ảnh mẫu 'a_phucthan.png' (Đã Tắt sẵn) ➔ Bỏ qua để Tắt Phúc Thần.")
            else:
                self.after(0, self.log_info, f"🎯 [TẮT] Giao diện KHÔNG KHỚP ảnh mẫu 'a_phucthan.png' ➔ Click vào ({pt_tap_x}, {pt_tap_y}) để Tắt Phúc Thần...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {pt_tap_x} {pt_tap_y}"])
                time.sleep(1.0)

        self.after(0, self.log_info, f"5. Click vào tọa độ ({end_x}, {end_y})...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {end_x} {end_y}"])
        time.sleep(1.0)

        self.after(0, self.log_info, f"6. Click lại nút xanh lá ({px_x}, {px_y}) để thu gọn menu...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
        time.sleep(1.0)

        if has_phuc_than:
            self.after(0, self.log_info, "7. Hoàn thành thao tác Phúc Thần (giữ nguyên ô tích).")

        # Ô Ký Lục:
        if self._should_stop_di_gioi(): return
        self.after(0, self.log_info, f"▶️ [KÝ LỤC] Kiểm tra ô Ký Lục (Trạng thái: {'ĐƯỢC TÍCH' if has_ky_luc else 'KHÔNG TÍCH'})...")
        ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
        if ai_x is not None and ai_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Nhấp chọn ngay...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
            time.sleep(1.0)
        else:
            self.after(0, self.log_info, f"1. Click mở lại bảng menu tại ({px_x}, {px_y})...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
            time.sleep(1.2)
            if self._should_stop_di_gioi(): return
            ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
            if ai_x is not None and ai_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Đang nhấp chọn...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
                time.sleep(1.0)

        self.after(0, self.log_info, f"3. Click tiếp vào tọa độ ({c_x}, {c_y})...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {c_x} {c_y}"])
        time.sleep(1.0)

        self.after(0, self.log_info, "4. Quét kiểm tra ảnh mẫu 'a_kyluc.png' (ngưỡng 95%)...")
        kl_x, kl_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_kyluc.png", threshold=0.95)
        if has_ky_luc:
            if kl_x is not None and kl_y is not None:
                self.after(0, self.log_info, f"🎯 [BẬT] Giao diện ĐÃ KHỚP ảnh mẫu 'a_kyluc.png' ➔ Click vào ({kl_tap_x}, {kl_tap_y}) để Bật Ký Lục...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {kl_tap_x} {kl_tap_y}"])
                time.sleep(1.0)
            else:
                self.after(0, self.log_info, "ℹ️ [BẬT] Giao diện KHÔNG KHỚP ảnh mẫu 'a_kyluc.png' (Đã Bật sẵn) ➔ Bỏ qua.")
        else:
            if kl_x is not None and kl_y is not None:
                self.after(0, self.log_info, "ℹ️ [TẮT] Giao diện ĐÃ KHỚP ảnh mẫu 'a_kyluc.png' (Đã Tắt sẵn) ➔ Bỏ qua để Tắt Ký Lục.")
            else:
                self.after(0, self.log_info, f"🎯 [TẮT] Giao diện KHÔNG KHỚP ảnh mẫu 'a_kyluc.png' ➔ Click vào ({kl_tap_x}, {kl_tap_y}) để Tắt Ký Lục...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {kl_tap_x} {kl_tap_y}"])
                time.sleep(1.0)

        self.after(0, self.log_info, f"5. Click vào tọa độ ({end_x}, {end_y})...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {end_x} {end_y}"])
        time.sleep(1.0)

        self.after(0, self.log_info, f"6. Click lại nút xanh lá ({px_x}, {px_y}) để thu gọn menu...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
        time.sleep(1.0)

        if has_ky_luc:
            self.after(0, self.log_info, "7. Hoàn thành thao tác Ký Lục (giữ nguyên ô tích).")

        # Ô Rút Gọn:
        if self._should_stop_di_gioi(): return
        self.after(0, self.log_info, f"▶️ [RÚT GỌN] Kiểm tra ô Rút Gọn (Trạng thái: {'ĐƯỢC TÍCH' if has_rut_gon else 'KHÔNG TÍCH'})...")
        ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
        if ai_x is not None and ai_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Nhấp chọn ngay...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
            time.sleep(1.0)
        else:
            self.after(0, self.log_info, f"1. Click mở lại bảng menu tại ({px_x}, {px_y})...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
            time.sleep(1.2)
            if self._should_stop_di_gioi(): return
            ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
            if ai_x is not None and ai_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Đang nhấp chọn...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
                time.sleep(1.0)

        self.after(0, self.log_info, f"3. Click tiếp vào tọa độ ({c_x}, {c_y})...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {c_x} {c_y}"])
        time.sleep(1.0)

        self.after(0, self.log_info, "4. Quét kiểm tra ảnh mẫu 'a_rutgon.png' (ngưỡng 95%)...")
        rg_x, rg_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_rutgon.png", threshold=0.95)
        if has_rut_gon:
            if rg_x is not None and rg_y is not None:
                self.after(0, self.log_info, f"🎯 [BẬT] Giao diện ĐÃ KHỚP ảnh mẫu 'a_rutgon.png' ➔ Click vào ({rg_tap_x}, {rg_tap_y}) để Bật Rút Gọn...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {rg_tap_x} {rg_tap_y}"])
                time.sleep(1.0)
            else:
                self.after(0, self.log_info, "ℹ️ [BẬT] Giao diện KHÔNG KHỚP ảnh mẫu 'a_rutgon.png' (Đã Bật sẵn) ➔ Bỏ qua.")
        else:
            if rg_x is not None and rg_y is not None:
                self.after(0, self.log_info, "ℹ️ [TẮT] Giao diện ĐÃ KHỚP ảnh mẫu 'a_rutgon.png' (Đã Tắt sẵn) ➔ Bỏ qua để Tắt Rút Gọn.")
            else:
                self.after(0, self.log_info, f"🎯 [TẮT] Giao diện KHÔNG KHỚP ảnh mẫu 'a_rutgon.png' ➔ Click vào ({rg_tap_x}, {rg_tap_y}) để Tắt Rút Gọn...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {rg_tap_x} {rg_tap_y}"])
                time.sleep(1.0)

        self.after(0, self.log_info, f"5. Click vào tọa độ ({end_x}, {end_y})...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {end_x} {end_y}"])
        time.sleep(1.0)

        self.after(0, self.log_info, f"6. Click lại nút xanh lá ({px_x}, {px_y}) để thu gọn menu...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
        time.sleep(1.0)

        if has_rut_gon:
            self.after(0, self.log_info, "7. Hoàn thành thao tác Rút Gọn (giữ nguyên ô tích).")

        # =========================================================================
        # 📌 6. BẬT AI TIM DỊ GIỚI ĐÊM (a_aitim.png)
        # =========================================================================
        if self._should_stop_di_gioi(): return
        self.after(0, self.log_info, "👁️ [DỊ GIỚI - Bước 6] Quét tìm biểu tượng 'a_aitim.png' (độ chính xác 85%)...")
        aitim_x, aitim_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_aitim.png", threshold=0.85)
        if aitim_x is not None and aitim_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_aitim.png' tại ({aitim_x}, {aitim_y})! Nhấp chọn ngay...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {aitim_x} {aitim_y}"])
            time.sleep(1.0)
        else:
            self.after(0, self.log_info, f"👉 Chưa thấy 'a_aitim.png' ➔ Click nút xanh lá ({px_x}, {px_y}) để mở menu...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
            time.sleep(1.2)
            if self._should_stop_di_gioi(): return
            aitim_x, aitim_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_aitim.png", threshold=0.85)
            if aitim_x is not None and aitim_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_aitim.png' tại ({aitim_x}, {aitim_y})! Nhấp chọn...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {aitim_x} {aitim_y}"])
                time.sleep(1.0)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'a_aitim.png' trong bảng menu.")

        # =========================================================================
        # 📌 7. HOÀN TẤT CARD DỊ GIỚI
        # =========================================================================
        self.var_switch_B.set(False)
        self.after(0, self.save_config)
        self.after(0, self.log_info, "✅ [1/6: DỊ GIỚI] Đã hoàn thành toàn bộ quy trình Card Dị Giới!")

    def _execute_card_E_phu_ban_doi(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """Thực thi Card 2: PHỤ BẢN ĐƠN / ĐỘI (E)"""
        if not self.var_switch_E.get():
            self.after(0, self.log_info, "ℹ️ [2/6: PHỤ BẢN ĐƠN / ĐỘI] Công tắc ON/OFF đang TẮT -> Bỏ qua.")
            return

        don_active = self.var_E_don.get()
        team_active = self.var_E_canhan.get() or self.var_E_doi.get()
        dungeon_checked = [
            ("PB 20", self.var_E1),
            ("PB 50", self.var_E2),
            ("PB 80", self.var_E3),
            ("PB 110", self.var_E4)
        ]
        active_dungeons = [name for name, var in dungeon_checked if var.get()]

        if not don_active and not team_active:
            self.after(0, self.log_info, "ℹ️ [2/6: PHỤ BẢN ĐƠN / ĐỘI] Không có mục Đơn/Cá Nhân/Tổ Đội nào được chọn -> Tắt công tắc & Bỏ qua.")
            self.var_switch_E.set(False)
            self.after(0, self.save_config)
            return

        # =========================================================================
        # 📌 VỀ KHU AN TOÀN (SAFE ZONE RETURN)
        # =========================================================================
        if self._should_stop_card_E(): return
        self.after(0, self.log_info, "👁️ [Phụ Bản - Về Khu An Toàn] Quét tìm nút Vị Trí 'a_vitri.png' (85%)...")
        v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
        if v_x is not None and v_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_vitri.png' tại ({v_x}, {v_y})! Click chọn...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
            time.sleep(1.0)
        else:
            self.after(0, self.log_info, "👉 Chưa thấy 'a_vitri.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(1.2)
            if self._should_stop_card_E(): return
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y})! Click chọn...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                time.sleep(1.0)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'a_vitri.png' trong bảng menu.")

        if self._should_stop_card_E(): return
        self.after(0, self.log_info, "👉 Click liên tục (435, 250) mỗi 0.5s cho đến khi xuất hiện nút Có 'card_c/c_co.png' (85%)...")

        while not self._should_stop_card_E():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_co.png", threshold=0.85)
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút Có 'card_c/c_co.png' tại ({co_x}, {co_y})! Dừng click (435, 250).")
                break
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 435 250"])
            time.sleep(0.5)

        if self._should_stop_card_E(): return
        self.after(0, self.log_info, "👁️ Click liên tục nút Có 'card_c/c_co.png' (0.5s mỗi lần) cho tới khi hết ảnh...")
        while not self._should_stop_card_E():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_co.png", threshold=0.85)
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút Có 'card_c/c_co.png' tại ({co_x}, {co_y}) ➔ Click vào vị trí ảnh...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {co_x} {co_y}"])
                time.sleep(0.5)
            else:
                self.after(0, self.log_info, "ℹ️ Không còn thấy ảnh nút Có 'card_c/c_co.png' ➔ Hoàn thành Về Khu An Toàn!")
                break

        # Quét Mắt Thần nút a_vitri.png (85%): Nhấp menu 1213, 648 nếu thấy, bỏ qua nếu không thấy
        if self._should_stop_card_E(): return
        self.after(0, self.log_info, "👁️ Quét Mắt Thần kiểm tra nút 'a_vitri.png' (85%)...")
        v_check_x, v_check_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
        if v_check_x is not None and v_check_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_vitri.png' tại ({v_check_x}, {v_check_y}) ➔ Click (1213, 648) thu gọn/mở menu...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(1.0)
        else:
            self.after(0, self.log_info, "ℹ️ Không thấy nút 'a_vitri.png' ➔ Bỏ qua.")

        # ---------------- 1. XỬ LÝ MỤC PHỤ BẢN ĐƠN (CÁ NHÂN) ----------------
        if don_active:
            if self.stop_requested: return
            selected_char_don = self.combo_E_don_char.get() if hasattr(self, 'combo_E_don_char') else "Xuất Chiến"
            self.after(0, self.log_info, f"⚙️ [Phụ Bản Đơn] Bắt đầu quy trình ô Cá Nhân - Vị trí: '{selected_char_don}'...")
            time.sleep(0.8)

            # --- Bước 1: Tìm ảnh b_doi.png (trong folder card_b) ---
            if self.stop_requested: return
            self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 1] Quét tìm ảnh 'b_doi.png' trong folder 'card_b'...")
            b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
            if b_doi_x is not None and b_doi_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                time.sleep(1.0)
            else:
                self.after(0, self.log_info, "👉 Chưa thấy 'b_doi.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(1.2)
                if self.stop_requested: return
                b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
                if b_doi_x is not None and b_doi_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                    time.sleep(1.0)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_doi.png' trong bảng menu.")

            # --- Bước 2: Thao tác theo từng vị trí trong Menu thả xuống ---
            if self.stop_requested: return
            self.after(0, self.log_info, f"⚙️ [Phụ Bản Đơn - Bước 2] Chế độ vị trí chọn: '{selected_char_don}'")
            if selected_char_don == "Xuất Chiến":
                self.after(0, self.log_info, "ℹ️ Vị trí 'Xuất Chiến': Không có hành động ở Bước 2, chuyển tiếp xuống Bước 3.")
            elif selected_char_don == "Vị Trí 1":
                self.after(0, self.log_info, "👉 [Vị Trí 1] Click (560, 520) ➔ (560, 255) ➔ (1090, 110)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.8)
            elif selected_char_don == "Vị Trí 2":
                self.after(0, self.log_info, "👉 [Vị Trí 2] Click (560, 520) ➔ (560, 340) ➔ (1090, 110)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.8)
            elif selected_char_don == "Vị Trí 3":
                self.after(0, self.log_info, "👉 [Vị Trí 3] Click (560, 520) ➔ (560, 430) ➔ (1090, 110)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 430"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.8)
            elif selected_char_don == "Vị Trí 4":
                self.after(0, self.log_info, "👉 [Vị Trí 4] Click (560, 255) ➔ (560, 520) ➔ (1090, 110)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.8)

            # --- Bước 3: Tìm ảnh b_pb.png (trong folder card_b) & click tọa độ ---
            if self.stop_requested: return
            self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 3] Quét tìm ảnh 'b_pb.png' trong folder 'card_b'...")
            b_pb_x, b_pb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85)
            if b_pb_x is not None and b_pb_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_pb.png' tại ({b_pb_x}, {b_pb_y})! Click vào ảnh...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x} {b_pb_y}"])
                time.sleep(1.0)
            else:
                self.after(0, self.log_info, "👉 Chưa thấy 'b_pb.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(1.2)
                if self.stop_requested: return
                b_pb_x, b_pb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85)
                if b_pb_x is not None and b_pb_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_pb.png' tại ({b_pb_x}, {b_pb_y})! Click vào ảnh...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x} {b_pb_y}"])
                    time.sleep(1.0)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_pb.png' trong bảng menu.")

            # --- Quét card_b/b_lsknn.png khi hoàn thành các thao tác Quét card_b/b_pb.png ---
            if self.stop_requested: return
            self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 3] Quét kiểm tra ảnh 'card_b/b_lsknn.png'...")
            lsknn_x, lsknn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_lsknn.png", threshold=0.85)
            if lsknn_x is not None and lsknn_y is not None:
                self.after(0, self.log_info, f"🎯 Khớp ảnh 'b_lsknn.png' tại ({lsknn_x}, {lsknn_y}) ➔ Click tọa độ (350, 585)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 350 585"])
                time.sleep(0.8)
            else:
                self.after(0, self.log_info, "ℹ️ Không khớp ảnh 'b_lsknn.png' ➔ Bỏ qua.")

            if self.stop_requested: return
            self.after(0, self.log_info, "👉 Click tọa độ (240, 500)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 240 500"])
            time.sleep(0.8)

            if self.stop_requested: return
            self.after(0, self.log_info, "👉 Click tiếp tọa độ (775, 575)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 775 575"])
            time.sleep(0.8)

            # --- Quét nhận diện Xác Nhận: card_b/b_xn.png (Chờ 3s & Quét liên tục tới khi thấy) ---
            if self.stop_requested: return
            self.after(0, self.log_info, "⏳ [Phụ Bản Đơn - Bước 3] Chờ 3 giây trước khi quét tìm nút Xác Nhận...")
            for _ in range(3):
                if self.stop_requested: return
                time.sleep(1.0)

            self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 3] Quét tìm ảnh mẫu 'card_b/b_xn.png' (Lặp lại cho tới khi phát hiện)...")
            xn_x, xn_y = None, None
            while not self.stop_requested:
                xn_x, xn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_xn.png", threshold=0.85)
                if xn_x is not None and xn_y is not None:
                    break
                self.after(0, self.log_info, "⏳ Chưa phát hiện 'card_b/b_xn.png' ➔ Tiếp tục quét lại sau 1.5s...")
                time.sleep(1.5)

            if self.stop_requested: return

            if xn_x is not None and xn_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_xn.png' tại ({xn_x}, {xn_y}) ➔ Click 2 lần (cách nhau 0.8s) vào ảnh 'b_xn.png'...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x} {xn_y}"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x} {xn_y}"])
                time.sleep(0.8)

            # --- Bước 4: Quy trình Bước 4 (Bỏ 4.1 và 4.2) ---
            if self.stop_requested: return
            self.after(0, self.log_info, "🚀 [Phụ Bản Đơn - Bước 4] Khởi chạy Bước 4...")

            # 4.3: Quét nhận diện Phụ Bản & Vào màn
            if self.stop_requested: return
            self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 4.3] Quét tìm ảnh 'b_pb.png'...")
            b_pb_x4, b_pb_y4 = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85)
            if b_pb_x4 is not None and b_pb_y4 is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_pb.png' tại ({b_pb_x4}, {b_pb_y4})! Click vào ảnh...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x4} {b_pb_y4}"])
                time.sleep(1.0)
            else:
                self.after(0, self.log_info, "👉 Chưa thấy 'b_pb.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(1.2)
                if self.stop_requested: return
                b_pb_x4, b_pb_y4 = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85)
                if b_pb_x4 is not None and b_pb_y4 is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_pb.png' tại ({b_pb_x4}, {b_pb_y4})! Click vào ảnh...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x4} {b_pb_y4}"])
                    time.sleep(1.0)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_pb.png' trong bảng menu.")

            if self.stop_requested: return
            self.after(0, self.log_info, "👉 Click tiếp tọa độ (240, 500)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 240 500"])
            time.sleep(0.8)

            if self.stop_requested: return
            self.after(0, self.log_info, "👉 Click tiếp tọa độ (640, 575)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 640 575"])
            time.sleep(0.8)

            if self.stop_requested: return
            self.after(0, self.log_info, "👉 Click nút thực thi tại tọa độ (775, 575)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 775 575"])
            time.sleep(0.8)

            # 4.4: Chờ 5 giây (có kiểm tra trạng thái dừng)
            if self.stop_requested: return
            self.after(0, self.log_info, "⏳ [Phụ Bản Đơn - Bước 4.4] Chờ 5 giây nạp trận đánh...")
            for _ in range(5):
                if self.stop_requested: return
                time.sleep(1.0)

            # 4.5: Vòng lặp quét liên tục ảnh card_b/b_xn.png cho tới khi tìm thấy (mỗi 1.5s)
            if self.stop_requested: return
            self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 4.5] Quét tìm ảnh mẫu 'card_b/b_xn.png' (mỗi 1.5s)...")
            xn_x4, xn_y4 = None, None
            while not self.stop_requested:
                xn_x4, xn_y4 = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_xn.png", threshold=0.85)
                if xn_x4 is not None and xn_y4 is not None:
                    break
                self.after(0, self.log_info, "⏳ Chưa phát hiện 'card_b/b_xn.png' ➔ Tiếp tục quét lại sau 1.5s...")
                time.sleep(1.5)

            if self.stop_requested: return

            if xn_x4 is not None and xn_y4 is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_xn.png' tại ({xn_x4}, {xn_y4}) ➔ Click 2 lần (cách nhau 0.5s) vào ảnh 'b_xn.png'...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x4} {xn_y4}"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x4} {xn_y4}"])
                time.sleep(3.0)
        else:
            self.after(0, self.log_info, "ℹ️ [Phụ Bản Đơn] Ô check 'Cá Nhân' KHÔNG ĐƯỢC TÍCH (OFF) -> Bỏ qua không chạy Phụ Bản Đơn.")

        # ---------------- 2. XỬ LÝ MỤC PHỤ BẢN ĐỘI (NẾU TÍCH Ô CÁ NHÂN) ----------------
        if self.var_E_canhan.get():
            if self.stop_requested: return
            selected_char_team = self.combo_E_team_char.get() if hasattr(self, 'combo_E_team_char') else "Xuất Chiến"

            dungeons_to_run = [
                ("PB 20", self.var_E1, (240, 275)),
                ("PB 50", self.var_E2, (240, 330)),
                ("PB 80", self.var_E3, (240, 380)),
                ("PB 110", self.var_E4, (240, 435))
            ]

            any_pb_checked = any(var_pb.get() for _, var_pb, _ in dungeons_to_run)

            if any_pb_checked:
                self.after(0, self.log_info, f"⚙️ [Phụ Bản Đội - Cá Nhân] Có ô PB được tích ➔ Bắt đầu Bước 1 & Bước 2 (Vị trí: '{selected_char_team}')...")

                # --- Bước 1: Mở Menu & Quét chọn Đội ---
                if self.stop_requested: return
                self.after(0, self.log_info, "👁️ [Phụ Bản Đội - Bước 1] Quét tìm ảnh 'b_doi.png' trong folder 'card_b'...")
                b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
                if b_doi_x is not None and b_doi_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện 'b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                    time.sleep(1.0)
                else:
                    self.after(0, self.log_info, "👉 Chưa thấy 'b_doi.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                    time.sleep(1.2)
                    if self.stop_requested: return
                    b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
                    if b_doi_x is not None and b_doi_y is not None:
                        self.after(0, self.log_info, f"🎯 Phát hiện 'b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                        time.sleep(1.0)
                    else:
                        self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_doi.png' trong bảng menu.")

                # --- Bước 2: Chuyển đổi Vị Trí Nhân Vật ---
                if self.stop_requested: return
                self.after(0, self.log_info, f"⚙️ [Phụ Bản Đội - Bước 2] Chế độ vị trí chọn: '{selected_char_team}'")
                if selected_char_team == "Xuất Chiến":
                    self.after(0, self.log_info, "ℹ️ Vị trí 'Xuất Chiến': Không có hành động ở Bước 2, chuyển tiếp xuống Bước 3.")
                elif selected_char_team == "Vị Trí 1":
                    self.after(0, self.log_info, "👉 [Vị Trí 1] Click (560, 520) ➔ (560, 255) ➔ (1090, 110)...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                    time.sleep(0.8)
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                    time.sleep(0.8)
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                    time.sleep(0.8)
                elif selected_char_team == "Vị Trí 2":
                    self.after(0, self.log_info, "👉 [Vị Trí 2] Click (560, 520) ➔ (560, 340) ➔ (1090, 110)...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                    time.sleep(0.8)
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
                    time.sleep(0.8)
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                    time.sleep(0.8)
                elif selected_char_team == "Vị Trí 3":
                    self.after(0, self.log_info, "👉 [Vị Trí 3] Click (560, 520) ➔ (560, 430) ➔ (1090, 110)...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                    time.sleep(0.8)
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 430"])
                    time.sleep(0.8)
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                    time.sleep(0.8)
                elif selected_char_team == "Vị Trí 4":
                    self.after(0, self.log_info, "👉 [Vị Trí 4] Click (560, 255) ➔ (560, 520) ➔ (1090, 110)...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                    time.sleep(0.8)
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                    time.sleep(0.8)
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                    time.sleep(0.8)

                # --- Bước 3: Mở Phụ Bản & Vào Phụ Bản cho từng ô tích PB ---
                for pb_name, var_pb, (pb_x, pb_y) in dungeons_to_run:
                    if var_pb.get():
                        if self.stop_requested: return
                        self.after(0, self.log_info, f"🚀 [Phụ Bản Đội - {pb_name}] Kích hoạt quy trình cho ô tích '{pb_name}'...")

                        # 1. Quét tìm card_b/b_pb.png
                        b_pb_x, b_pb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85)
                        if b_pb_x is not None and b_pb_y is not None:
                            self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_pb.png' tại ({b_pb_x}, {b_pb_y})! Click chọn...")
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x} {b_pb_y}"])
                            time.sleep(1.0)
                        else:
                            self.after(0, self.log_info, "👉 Chưa thấy 'b_pb.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu...")
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                            time.sleep(1.2)
                            if self.stop_requested: return
                            b_pb_x, b_pb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85)
                            if b_pb_x is not None and b_pb_y is not None:
                                self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_pb.png' tại ({b_pb_x}, {b_pb_y})! Click chọn...")
                                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x} {b_pb_y}"])
                                time.sleep(1.0)
                            else:
                                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_pb.png' trong bảng menu.")

                        if self.stop_requested: return
                        # 2. Click tọa độ chọn PB (240, pb_y) ➔ (735, 575)
                        self.after(0, self.log_info, f"👉 Click chọn {pb_name} tại ({pb_x}, {pb_y}) ➔ Click (735, 575)...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {pb_x} {pb_y}"])
                        time.sleep(0.8)
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 735 575"])
                        time.sleep(0.8)

                        if self.stop_requested: return
                        # 3. Quét tìm card_b/b_matkhau.png (85%)
                        self.after(0, self.log_info, "👁️ Quét tìm ảnh mẫu 'card_b/b_matkhau.png' (85%)...")
                        mk_x, mk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_matkhau.png", threshold=0.85)
                        if mk_x is not None and mk_y is not None:
                            self.after(0, self.log_info, f"🎯 Khớp ảnh 'b_matkhau.png' tại ({mk_x}, {mk_y}) ➔ Click chọn ảnh...")
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {mk_x} {mk_y}"])
                            time.sleep(0.8)
                        else:
                            self.after(0, self.log_info, "ℹ️ Không khớp 'b_matkhau.png' ➔ Bỏ qua.")

                        if self.stop_requested: return
                        # 4. Click tọa độ (640, 435) ➔ (885, 575)
                        self.after(0, self.log_info, "👉 Click (640, 435) ➔ Click (885, 575)...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 640 435"])
                        time.sleep(0.8)
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 885 575"])
                        time.sleep(0.8)

                        if self.stop_requested: return
                        # 5. Chờ 5 giây
                        self.after(0, self.log_info, f"⏳ [{pb_name}] Chờ 5 giây...")
                        for _ in range(5):
                            if self.stop_requested: return
                            time.sleep(1.0)

                        if self.stop_requested: return
                        # 6. Hoãn 40 giây & Click (1165, 210) mỗi 0.5s
                        self.after(0, self.log_info, f"⏳ [{pb_name}] Hoãn 40 giây & click liên tục (1165, 210) mỗi 0.5s...")
                        for _ in range(80):
                            if self.stop_requested: return
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1165 210"])
                            time.sleep(0.5)

                        if self.stop_requested: return
                        # 7. Quét b_xn.png mỗi 5s & Click (1165, 210) mỗi 0.5s đến khi tìm thấy
                        self.after(0, self.log_info, f"👁️ [{pb_name}] Bắt đầu quét 'b_xn.png' mỗi 5s & click (1165, 210) mỗi 0.5s...")
                        xn_x, xn_y = None, None
                        while not self.stop_requested:
                            xn_x, xn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_xn.png", threshold=0.85)
                            if xn_x is not None and xn_y is not None:
                                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_b/b_xn.png' tại ({xn_x}, {xn_y})! Dừng click liên tiếp.")
                                break

                            # Click liên tục trong 5s (10 lần x 0.5s)
                            for _ in range(10):
                                if self.stop_requested: break
                                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1165 210"])
                                time.sleep(0.5)

                        if self.stop_requested: return
                        # 8. Click vào ảnh b_xn.png
                        if xn_x is not None and xn_y is not None:
                            self.after(0, self.log_info, f"👉 Click vào ảnh 'b_xn.png' tại ({xn_x}, {xn_y})...")
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x} {xn_y}"])
                            time.sleep(1.0)
            else:
                # --- KHÔNG TÍCH BẤT KỲ Ô PB NÀO (20, 50, 80, 110) ➔ BỎ QUA BƯỚC 1 VÀ BƯỚC 2 ---
                if self.stop_requested: return
                self.after(0, self.log_info, "⚡ [Phụ Bản Đội - Cá Nhân] KHÔNG TÍCH ô PB nào (20, 50, 80, 110) ➔ Bỏ qua Bước 1 & Bước 2, thực thi trực tiếp...")

                # 1. Click tiếp (885, 575) (nghỉ 0.8s)
                self.after(0, self.log_info, "👉 1. Click (885, 575)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 885 575"])
                time.sleep(0.8)

                if self.stop_requested: return
                # 2. Chờ 5 giây
                self.after(0, self.log_info, "⏳ 2. Chờ 5 giây...")
                for _ in range(5):
                    if self.stop_requested: return
                    time.sleep(1.0)

                if self.stop_requested: return
                # 3. Hoãn 40 giây & Click (1165, 210) mỗi 0.5s
                self.after(0, self.log_info, "⏳ 3. Hoãn 40 giây & click liên tục (1165, 210) mỗi 0.5s...")
                for _ in range(80):
                    if self.stop_requested: return
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1165 210"])
                    time.sleep(0.5)

                if self.stop_requested: return
                # 4. Quét b_xn.png mỗi 5s & Click (1165, 210) mỗi 0.5s
                self.after(0, self.log_info, "👁️ 4. Bắt đầu quét 'b_xn.png' mỗi 5s & click liên tục (1165, 210) mỗi 0.5s...")
                xn_x, xn_y = None, None
                while not self.stop_requested:
                    xn_x, xn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_xn.png", threshold=0.85)
                    if xn_x is not None and xn_y is not None:
                        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_b/b_xn.png' tại ({xn_x}, {xn_y})! Dừng click liên tiếp.")
                        break

                    # Click liên tục trong 5s (10 lần x 0.5s)
                    for _ in range(10):
                        if self.stop_requested: break
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1165 210"])
                        time.sleep(0.5)

                if self.stop_requested: return
                # 5. Click vào ảnh b_xn.png
                if xn_x is not None and xn_y is not None:
                    self.after(0, self.log_info, f"👉 5. Click vào ảnh 'b_xn.png' tại ({xn_x}, {xn_y})...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x} {xn_y}"])
                    time.sleep(1.0)

        # ---------------- 3. TỰ ĐỘNG TẮT CÔNG TẮC & LƯU CẤU HÌNH (GIỮ NGUYÊN Ô TÍCH) ----------------
        self.var_switch_E.set(False)
        self.after(0, self.save_config)
        self.after(0, self.log_info, "✅ [1/6: PHỤ BẢN ĐƠN / ĐỘI] Đã thực thi hoàn tất! (Tự động tắt công tắc ON/OFF & giữ nguyên các ô tích)")

    def _execute_card_G_phu_ban_don(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """Thực thi Card 3: TỔ ĐỘI (G) - Quản lý bởi ô check 'Tổ Đội' ở Card Phụ Bản Đội/Đơn"""
        if not self.var_E_doi.get():
            self.after(0, self.log_info, "ℹ️ [3/6: TỔ ĐỘI] Ô check 'Tổ Đội' ở Card Phụ Bản Đội/Đơn đang TẮT (OFF) -> Bỏ qua Card 3.")
            return

        checked = [
            ("G1", self.var_G1),
            ("G2", self.var_G2),
            ("G3", self.var_G3),
            ("G4", self.var_G4)
        ]
        active_items = [(name, var) for name, var in checked if var.get()]
        if not active_items:
            self.after(0, self.log_info, "ℹ️ [3/6: TỔ ĐỘI] Ô check 'Tổ Đội' được tích nhưng không có mục T1-T4 nào được chọn -> Bỏ qua.")
            self.after(0, self.save_config)
            return

        item_names = [name for name, var in active_items]
        self.after(0, self.log_info, f"▶️ [3/6: TỔ ĐỘI] Đang thực thi {len(item_names)} mục đã chọn: {', '.join(item_names)}...")
        time.sleep(1.0)

        # Giữ nguyên trạng thái các ô check sau khi hoàn thành
        self.after(0, self.save_config)
        self.after(0, self.log_info, "✅ [4/6: TỔ ĐỘI] Đã thực thi hoàn tất dứt điểm! (Giữ nguyên các ô tích)")

    def _execute_card_C_boss_tg(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """Thực thi Card 2: BOSS THẾ GIỚI (C)"""
        if self._should_stop_card_C():
            self.after(0, self.log_info, "ℹ️ [2/6: BOSS THẾ GIỚI] Công tắc ON/OFF đang TẮT -> Bỏ qua.")
            return

        checked = [
            ("Boss Sáng", self.var_C1),
            ("Boss Trưa", self.var_C2),
            ("Vé", self.var_C3)
        ]
        active_items = [(name, var) for name, var in checked if var.get()]
        if not active_items:
            self.after(0, self.log_info, "ℹ️ [2/6: BOSS THẾ GIỚI] Công tắc ON nhưng không có mục nào được chọn -> Tắt công tắc & Bỏ qua.")
            self.var_switch_C.set(False)
            self.after(0, self.save_config)
            return

        selected_char = self.combo_C_char.get() if hasattr(self, 'combo_C_char') else "Xuất Chiến"
        selected_ve = self.combo_C_ve.get() if hasattr(self, 'combo_C_ve') else "1"

        self.after(0, self.log_info, f"🚀 [2/6: BOSS THẾ GIỚI] Khởi chạy - Vị trí: '{selected_char}' • Số Vé: '{selected_ve}'...")

        # =========================================================================
        # 📌 1. VỀ KHU AN TOÀN
        # =========================================================================
        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "👁️ [Boss Thế Giới - Bước 1.1] Quét tìm nút Vị Trí 'a_vitri.png' (85%)...")
        v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
        if v_x is not None and v_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_vitri.png' tại ({v_x}, {v_y})! Click chọn...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
            time.sleep(1.0)
        else:
            self.after(0, self.log_info, "👉 Chưa thấy 'a_vitri.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(1.2)
            if self._should_stop_card_C(): return
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y})! Click chọn...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                time.sleep(1.0)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'a_vitri.png' trong bảng menu.")

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "👉 [Boss Thế Giới - Bước 1.2] Click liên tục (435, 250) mỗi 0.5s cho đến khi xuất hiện nút Có 'card_c/c_co.png' (85%)...")

        # Click liên tục (435, 250) (cách nhau 0.5s) đến khi hiện ảnh card_c/c_co.png (85%)
        while not self._should_stop_card_C():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_co.png", threshold=0.85)
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút Có 'card_c/c_co.png' tại ({co_x}, {co_y})! Dừng click (435, 250).")
                break
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 435 250"])
            time.sleep(0.5)

        # 1.3. Quét nhận diện nút Có card_c/c_co.png (85%): Nếu phát hiện ➔ Click vào ảnh (0.5s mỗi lần) đến khi hết ảnh
        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "👁️ [Boss Thế Giới - Bước 1.3] Click liên tục nút Có 'card_c/c_co.png' (0.5s mỗi lần) cho tới khi hết ảnh...")
        while not self._should_stop_card_C():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_co.png", threshold=0.85)
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút Có 'card_c/c_co.png' tại ({co_x}, {co_y}) ➔ Click vào vị trí ảnh...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {co_x} {co_y}"])
                time.sleep(0.5)
            else:
                self.after(0, self.log_info, "ℹ️ Không còn thấy ảnh nút Có 'card_c/c_co.png' ➔ Hoàn thành Bước 1 (Về Khu An Toàn)!")
                break

        # =========================================================================
        # 📌 2. CHUYỂN ĐỔI VỊ TRÍ NHÂN VẬT (THEO DROPDOWN)
        # =========================================================================
        if self._should_stop_card_C(): return
        self.after(0, self.log_info, f"⚙️ [Boss Thế Giới - Bước 2] Vị trí nhân vật: '{selected_char}'")

        if selected_char == "Xuất Chiến":
            self.after(0, self.log_info, "ℹ️ Vị trí 'Xuất Chiến': Bỏ qua Bước 2, chuyển thẳng xuống các ô Check.")
        else:
            # Nghỉ 3 giây trước khi khởi động Bước 2
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "⏳ [Boss Thế Giới - Bước 2] Nghỉ 3 giây trước khi khởi động...")
            for _ in range(3):
                if self._should_stop_card_C(): return
                time.sleep(1.0)

            # Quét ảnh icon Đội 'card_b/b_doi.png' (85%)
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "👁️ [Boss Thế Giới - Bước 2] Quét tìm ảnh 'card_b/b_doi.png' (85%)...")
            b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
            if b_doi_x is not None and b_doi_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                time.sleep(1.0)
            else:
                self.after(0, self.log_info, "👉 Chưa thấy 'b_doi.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(1.2)
                if self._should_stop_card_C(): return
                b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
                if b_doi_x is not None and b_doi_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                    time.sleep(1.0)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'card_b/b_doi.png' trong bảng menu.")

            if selected_char == "Vị Trí 1":
                self.after(0, self.log_info, "👉 [Vị Trí 1] Click (560, 520) ➔ (560, 255) ➔ (1090, 110)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.8)
            elif selected_char == "Vị Trí 2":
                self.after(0, self.log_info, "👉 [Vị Trí 2] Click (560, 520) ➔ (560, 340) ➔ (1090, 110)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.8)
            elif selected_char == "Vị Trí 3":
                self.after(0, self.log_info, "👉 [Vị Trí 3] Click (560, 520) ➔ (560, 430) ➔ (1090, 110)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 430"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.8)
            elif selected_char == "Vị Trí 4":
                self.after(0, self.log_info, "👉 [Vị Trí 4] Click (560, 255) ➔ (560, 520) ➔ (1090, 110)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.8)

            # Click (1213, 648) đóng menu
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "👉 [Boss Thế Giới - Bước 2] Click (1213, 648) đóng menu...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(1.0)

        # =========================================================================
        # 📌 Ô CHECK 1: BOSS SÁNG (Khi var_C1 được tích)
        # =========================================================================
        if self.var_C1.get():
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "🚀 [Ô Check 1: BOSS SÁNG] Khởi chạy quy trình Boss Sáng...")

            # 1. Khởi động trận đánh (Click tọa độ):
            # Nghỉ 3s ➔ Click (1115, 87) ➔ Nghỉ 1s ➔ Click (1223, 227) ➔ Nghỉ 5s ➔ Click (1235, 551) ➔ Nghỉ 4s ➔ Click (1178, 405) ➔ Nghỉ 4s ➔ Click (704, 196) ➔ Nghỉ 2s ➔ Click (1115, 87) ➔ Nghỉ 1s
            self.after(0, self.log_info, "👉 [Boss Sáng - Khởi động] Nghỉ 3s ➔ (1115, 87) ➔ (1223, 227) ➔ (1235, 551) ➔ (1178, 405) ➔ (704, 196) ➔ (1115, 87)...")
            
            # Nghỉ 3s trước khi bắt đầu
            for _ in range(3):
                if self._should_stop_card_C(): return
                time.sleep(1.0)

            # Click (1115, 87) - Nghỉ 1s
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "👉 [Boss Sáng - Khởi động] Click (1115, 87)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1115 87"])
            time.sleep(1.0)

            # Click (1223, 227) - Nghỉ 5s
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "👉 [Boss Sáng - Khởi động] Click (1223, 227) ➔ Nghỉ 5s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1223 227"])
            for _ in range(5):
                if self._should_stop_card_C(): return
                time.sleep(1.0)

            # Click (1235, 551) - Nghỉ 4s
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "👉 [Boss Sáng - Khởi động] Click (1235, 551) ➔ Nghỉ 4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1235 551"])
            for _ in range(4):
                if self._should_stop_card_C(): return
                time.sleep(1.0)

            # Click (1178, 405) - Nghỉ 4s
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "👉 [Boss Sáng - Khởi động] Click (1178, 405) ➔ Nghỉ 4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1178 405"])
            for _ in range(4):
                if self._should_stop_card_C(): return
                time.sleep(1.0)

            # Click (704, 196) - Nghỉ 2s
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "👉 [Boss Sáng - Khởi động] Click (704, 196) ➔ Nghỉ 2s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 704 196"])
            for _ in range(2):
                if self._should_stop_card_C(): return
                time.sleep(1.0)

            # Click (1115, 87) - Nghỉ 1s
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "👉 [Boss Sáng - Khởi động] Click (1115, 87)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1115 87"])
            time.sleep(1.0)

            # Lặp lại đúng 5 lượt đánh (mỗi lượt gồm các bước từ 2 đến 5)
            self.after(0, self.log_info, "🔄 [Boss Sáng] Bắt đầu lặp lại đúng 5 lượt đánh (từ Bước 2 đến Bước 5)...")
            for turn in range(1, 6):
                if self._should_stop_card_C(): return
                self.after(0, self.log_info, f"🔄 [Boss Sáng - Lượt {turn}/5] Đang thực thi lượt {turn}...")

                # 2. Click (1240, 605) đến khi quét thấy ảnh Boss card_c/c_boss.png (85%) thì dừng lại
                if self._should_stop_card_C(): return
                self.after(0, self.log_info, f"👁️ [Lượt {turn} - Bước 2] Click liên tục (1240, 605) cho tới khi phát hiện ảnh Boss 'card_c/c_boss.png' (85%)...")
                boss_x, boss_y = None, None
                while not self._should_stop_card_C():
                    boss_x, boss_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_boss.png", threshold=0.85)
                    if boss_x is not None and boss_y is not None:
                        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện ảnh 'card_c/c_boss.png' tại ({boss_x}, {boss_y})! Dừng click (1240, 605).")
                        break
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 605"])
                    time.sleep(0.8)

                if self._should_stop_card_C(): return

                # 3. Click (1160, 570) ➔ (500, 635)
                self.after(0, self.log_info, f"👉 [Lượt {turn} - Bước 3] Click (1160, 570) ➔ (500, 635)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1160 570"])
                time.sleep(0.8)
                if self._should_stop_card_C(): return
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 500 635"])
                time.sleep(0.8)

                # 4. Đợi 3 giây ➔ Click (185, 145)
                if self._should_stop_card_C(): return
                self.after(0, self.log_info, f"⏳ [Lượt {turn} - Bước 4] Đợi 3 giây trước khi click (185, 145)...")
                for _ in range(3):
                    if self._should_stop_card_C(): return
                    time.sleep(1.0)

                if self._should_stop_card_C(): return
                self.after(0, self.log_info, f"👉 [Lượt {turn} - Bước 4] Click (185, 145)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 185 145"])
                time.sleep(0.8)

                # 5. Bắt đầu quét ảnh card_c/c_dung.png (70%) (5 giây 1 lần)
                if self._should_stop_card_C(): return
                self.after(0, self.log_info, f"👁️ [Lượt {turn} - Bước 5] Quét tìm ảnh 'card_c/c_dung.png' (70%, 5 giây 1 lần)...")
                while not self._should_stop_card_C():
                    dung_x, dung_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_dung.png", threshold=0.70)
                    if dung_x is not None and dung_y is not None:
                        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_dung.png' tại ({dung_x}, {dung_y}) ➔ Hoàn thành lượt đánh {turn}/5! Nghỉ 5 giây...")
                        for _ in range(5):
                            if self._should_stop_card_C(): break
                            time.sleep(1.0)
                        break
                    for _ in range(5):
                        if self._should_stop_card_C(): break
                        time.sleep(1.0)

            # Hoàn thành 5 lượt đánh Boss Sáng (giữ nguyên ô tích)
            self.after(0, self.log_info, "✅ [Boss Sáng] Đã hoàn thành 5 lượt đánh (giữ nguyên ô tích).")

        # ---------------- 3. TỰ ĐỘNG TẮT CÔNG TẮC & LƯU CẤU HÌNH (GIỮ NGUYÊN Ô TÍCH) ----------------
        self.var_switch_C.set(False)
        self.after(0, self.save_config)
        self.after(0, self.log_info, "✅ [2/6: BOSS THẾ GIỚI] Đã thực thi hoàn tất quy trình! (Tự động tắt công tắc ON/OFF & giữ nguyên các ô tích)")

    def _execute_card_D_40_npc(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """Thực thi Card 5: 40 NPC (D)"""
        if self._should_stop_card_D():
            self.after(0, self.log_info, "ℹ️ [5/6: 40 NPC] Công tắc ON/OFF đang TẮT -> Bỏ qua.")
            return

        checked = [
            ("D1", self.var_D1),
            ("D2", self.var_D2),
            ("D3", self.var_D3),
            ("D4", self.var_D4)
        ]
        active_items = [(name, var) for name, var in checked if var.get()]
        if not active_items:
            self.after(0, self.log_info, "ℹ️ [5/6: 40 NPC] Công tắc ON nhưng không có mục nào được chọn -> Tắt công tắc & Bỏ qua.")
            self.var_switch_D.set(False)
            self.after(0, self.save_config)
            return

        item_names = [name for name, var in active_items]
        self.after(0, self.log_info, f"▶️ [5/6: 40 NPC] Đang thực thi {len(item_names)} mục đã chọn: {', '.join(item_names)}...")
        time.sleep(1.0)

        # Tự động tắt công tắc ON/OFF (False) sau khi hoàn thành, giữ nguyên các ô check
        self.var_switch_D.set(False)
        self.after(0, self.save_config)
        self.after(0, self.log_info, "✅ [5/6: 40 NPC] Đã thực thi hoàn tất dứt điểm! (Đã tự động tắt công tắc ON/OFF & giữ nguyên các ô tích)")

    def _execute_card_F_nhi_kieu(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """Thực thi Card 6: NHỊ KIỀU (F)"""
        if self._should_stop_card_F():
            self.after(0, self.log_info, "ℹ️ [6/6: NHỊ KIỀU] Công tắc ON/OFF đang TẮT -> Bỏ qua.")
            return

        checked = [
            ("F1", self.var_F1),
            ("F2", self.var_F2),
            ("F3", self.var_F3),
            ("F4", self.var_F4)
        ]
        active_items = [(name, var) for name, var in checked if var.get()]
        if not active_items:
            self.after(0, self.log_info, "ℹ️ [6/6: NHỊ KIỀU] Công tắc ON nhưng không có mục nào được chọn -> Tắt công tắc & Bỏ qua.")
            self.var_switch_F.set(False)
            self.after(0, self.save_config)
            return

        item_names = [name for name, var in active_items]
        self.after(0, self.log_info, f"▶️ [6/6: NHỊ KIỀU] Đang thực thi {len(item_names)} mục đã chọn: {', '.join(item_names)}...")
        time.sleep(1.0)

        # Tự động tắt công tắc ON/OFF (False) sau khi hoàn thành, giữ nguyên các ô check
        self.var_switch_F.set(False)
        self.after(0, self.save_config)
        self.after(0, self.log_info, "✅ [6/6: NHỊ KIỀU] Đã thực thi hoàn tất dứt điểm! (Đã tự động tắt công tắc ON/OFF & giữ nguyên các ô tích)")



    def _get_emulator_screen_size(self, dnconsole_path: str, tab_index: str) -> tuple:
        """Tự động quét đo độ phân giải thực tế (Width, Height) của giả lập LDPlayer qua ADB wm size"""
        try:
            res = self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell wm size"], text=True)
            if res and res.stdout:
                match = re.search(r'(\d+)x(\d+)', res.stdout)
                if match:
                    w, h = int(match.group(1)), int(match.group(2))
                    if w < h:
                        w, h = h, w
                    return w, h
        except Exception:
            pass
        return 1280, 720

    def _convert_emulator_coords(self, raw_x: float, raw_y: float, target_w: int = 1280, target_h: int = 720) -> tuple:
        """Quy đổi tọa độ thô cảm ứng từ giả lập LDPlayer (VD: PutMultiTouch 18630, 10200) sang Pixel màn hình thực tế (1280x720)"""
        if raw_x > target_w or raw_y > target_h:
            if raw_x <= 10000 and raw_y <= 10000:
                # Quy đổi từ dải cảm ứng thô 0..10000 của giả lập LDPlayer sang 1280x720
                px_x = int(round((raw_x / 10000.0) * target_w))
                px_y = int(round((raw_y / 10000.0) * target_h))
            elif raw_x <= 19200 and raw_y <= 10800:
                # Quy đổi từ dải cảm ứng 19200x10800 của LDPlayer PutMultiTouch
                px_x = int(round((raw_x / 19200.0) * target_w))
                px_y = int(round((raw_y / 10800.0) * target_h))
            else:
                # Quy đổi tỉ lệ 10x
                px_x = int(round(raw_x / 10.0))
                px_y = int(round(raw_y / 10.0))
        else:
            px_x = int(raw_x)
            px_y = int(raw_y)
        return px_x, px_y

    def _find_template_on_screen(self, dnconsole_path: str, tab_index: str, template_filename: str, threshold: float = 0.85):
        """👁️ Mắt Thần OpenCV: Khớp vị trí hình ảnh mẫu .png trong thư mục con assets/ với độ chính xác cao"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "assets")
        os.makedirs(assets_dir, exist_ok=True)
        
        clean_name = os.path.basename(template_filename)
        # Đường dẫn file ảnh mẫu (.png) - Tìm kiếm linh hoạt trong assets/, card_b, card_a..f, login, server...
        possible_paths = [
            os.path.join(assets_dir, template_filename),
            os.path.join(assets_dir, "card_b", clean_name),
            os.path.join(assets_dir, "card_a", clean_name),
            os.path.join(assets_dir, "card_c", clean_name),
            os.path.join(assets_dir, "card_d", clean_name),
            os.path.join(assets_dir, "card_e", clean_name),
            os.path.join(assets_dir, "card_f", clean_name),
            os.path.join(assets_dir, "login", clean_name),
            os.path.join(assets_dir, "server", clean_name),
            os.path.join(base_dir, template_filename)
        ]
        # Tự động quét thêm bất kỳ thư mục con nào khác trong assets/ nếu có
        try:
            if os.path.exists(assets_dir):
                for sub in os.listdir(assets_dir):
                    sub_dir = os.path.join(assets_dir, sub)
                    if os.path.isdir(sub_dir):
                        p = os.path.join(sub_dir, template_filename)
                        if p not in possible_paths:
                            possible_paths.append(p)
        except Exception:
            pass

        tmpl_path = None
        for p in possible_paths:
            if os.path.exists(p):
                tmpl_path = p
                break

        if tmpl_path is None or not os.path.exists(tmpl_path):
            self.after(0, self.log_error, f"⚠️ Chưa có file ảnh mẫu '{template_filename}' trong các thư mục assets/ (card_a..f, login, server...)!")
            return None, None  # Chưa có file ảnh mẫu trong assets/

        # File ảnh tạm thời chụp màn hình lưu gọn gàng trong thư mục assets/
        temp_local = os.path.join(assets_dir, f"temp_cap_{tab_index}.png")
        
        is_nkn = ("nkn" in template_filename.lower()) or ("diemdanh" in template_filename.lower())
        max_attempts = 3 if is_nkn else 1

        for attempt in range(max_attempts):
            # Chụp ảnh màn hình LDPlayer qua ADB
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell screencap -p /sdcard/mat_than.png"])
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"pull /sdcard/mat_than.png \"{temp_local}\""])

            if os.path.exists(temp_local) and os.path.getsize(temp_local) > 0:
                try:
                    screen = cv2.imread(temp_local)
                    template = cv2.imread(tmpl_path, cv2.IMREAD_UNCHANGED)

                    if screen is not None and template is not None:
                        # Nới lỏng ngưỡng mặc định cho file nkn.png (do dòng chữ bên trong di chuyển/chuyển động)
                        current_threshold = threshold
                        if is_nkn:
                            current_threshold = min(threshold, 0.45)

                        # Xử lý Alpha Mask (trong suốt) chuẩn xác cho file PNG 4 kênh
                        if len(template.shape) == 3 and template.shape[2] == 4:
                            alpha_mask = template[:, :, 3]
                            template_bgr = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
                            if np.any(alpha_mask < 255):
                                res = cv2.matchTemplate(screen, template_bgr, cv2.TM_CCOEFF_NORMED, mask=alpha_mask)
                            else:
                                res = cv2.matchTemplate(screen, template_bgr, cv2.TM_CCOEFF_NORMED)
                        else:
                            res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)

                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                        # 2. Nếu là file nkn.png có chữ di chuyển: Quét bổ sung theo Grayscale & Canny Edge để bắt khung viền cố định
                        if is_nkn:
                            try:
                                gray_screen = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
                                gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                                res_gray = cv2.matchTemplate(gray_screen, gray_template, cv2.TM_CCOEFF_NORMED)
                                _, max_v_g, _, max_l_g = cv2.minMaxLoc(res_gray)
                                if max_v_g > max_val:
                                    max_val = max_v_g
                                    max_loc = max_l_g

                                # Quét theo đường nét khung viền Canny Edge (loại bỏ hoàn toàn ảnh hưởng của dòng chữ di chuyển)
                                edge_screen = cv2.Canny(gray_screen, 50, 150)
                                edge_template = cv2.Canny(gray_template, 50, 150)
                                res_edge = cv2.matchTemplate(edge_screen, edge_template, cv2.TM_CCOEFF_NORMED)
                                _, max_v_e, _, max_l_e = cv2.minMaxLoc(res_edge)
                                if max_v_e > max_val:
                                    max_val = max_v_e
                                    max_loc = max_l_e
                            except Exception:
                                pass

                        match_pct = round(max_val * 100, 1)

                        # Chấp nhận khi độ tương đồng đạt ngưỡng current_threshold
                        if max_val >= current_threshold:
                            h, w = template.shape[:2]
                            center_x = max_loc[0] + w // 2
                            center_y = max_loc[1] + h // 2
                            self.after(0, self.log_info, f"👁️ Mắt thần khớp thành công '{template_filename}' ({match_pct}%) tại ({center_x}, {center_y})")
                            try: os.remove(temp_local)
                            except: pass
                            return center_x, center_y
                        else:
                            self.after(0, self.log_info, f"👁️ Mắt thần đang quét '{template_filename}' (Độ khớp: {match_pct}% / Cần: {int(current_threshold*100)}%)")
                except Exception:
                    pass
                finally:
                    try: os.remove(temp_local)
                    except: pass

            # Nếu chưa khớp và còn lượt thử với nkn.png, tạm dừng 0.3s để bắt khoảnh khắc ảnh xuất hiện
            if attempt < max_attempts - 1:
                time.sleep(0.3)

        return None, None

    def _wait_for_server_screen_vision(self, dnconsole_path: str, tab_index: str, max_wait_sec: float = 15.0) -> bool:
        """👁️ Mắt Thần nhận biết hình ảnh màn hình Chọn Máy Chủ qua OpenCV & ADB screencap"""
        start_time = time.time()
        while time.time() - start_time < max_wait_sec:
            x1, y1 = self._find_template_on_screen(dnconsole_path, tab_index, "login_server.png", threshold=0.85)
            if x1 is not None:
                return True
            x2, y2 = self._find_template_on_screen(dnconsole_path, tab_index, "login_redorb.png", threshold=0.85)
            if x2 is not None:
                return True
            time.sleep(0.8)
        return False



    def xu_ly_mo_phuc_than(self):
        status = "BẬT" if self.var_B1.get() else "TẮT"
        self.log_info(f"Dị Giới Đêm - Phúc Thần: {status}")

    def xu_ly_mo_di_gioi(self):
        status = "BẬT" if self.var_B2.get() else "TẮT"
        self.log_info(f"Dị Giới Đêm - Ký Lục: {status}")

    def xu_ly_chien_dau_rut_gon(self):
        status = "BẬT" if self.var_B3.get() else "TẮT"
        self.log_info(f"Dị Giới Đêm - Rút Gọn: {status}")

    def xu_ly_vao_di_gioi_12h(self):
        status = "BẬT" if self.var_B4.get() else "TẮT"
        self.log_info(f"Dị Giới Đêm - Dị Giới: {status}")

    def xu_ly_cau_hinh_E1(self):
        status = "BẬT" if self.var_E1.get() else "TẮT"
        self.log_info(f"Phụ Bản Đội - E1: {status}")

    def xu_ly_cau_hinh_E2(self):
        status = "BẬT" if self.var_E2.get() else "TẮT"
        self.log_info(f"Phụ Bản Đội - E2: {status}")

    def xu_ly_cau_hinh_E3(self):
        status = "BẬT" if self.var_E3.get() else "TẮT"
        self.log_info(f"Phụ Bản Đội - E3: {status}")

    def xu_ly_cau_hinh_E4(self):
        status = "BẬT" if self.var_E4.get() else "TẮT"
        self.log_info(f"Phụ Bản Đội - E4: {status}")

    def xu_ly_cau_hinh_G1(self):
        status = "BẬT" if self.var_G1.get() else "TẮT"
        self.log_info(f"Phụ Bản Đơn - G1: {status}")

    def xu_ly_cau_hinh_G2(self):
        status = "BẬT" if self.var_G2.get() else "TẮT"
        self.log_info(f"Phụ Bản Đơn - G2: {status}")

    def xu_ly_cau_hinh_G3(self):
        status = "BẬT" if self.var_G3.get() else "TẮT"
        self.log_info(f"Phụ Bản Đơn - G3: {status}")

    def xu_ly_cau_hinh_G4(self):
        status = "BẬT" if self.var_G4.get() else "TẮT"
        self.log_info(f"Phụ Bản Đơn - G4: {status}")

    def xu_ly_cau_hinh_C1(self):
        status = "BẬT" if self.var_C1.get() else "TẮT"
        self.log_info(f"Cấu hình C - C1: {status}")

    def xu_ly_cau_hinh_C2(self):
        status = "BẬT" if self.var_C2.get() else "TẮT"
        self.log_info(f"Cấu hình C - C2: {status}")

    def xu_ly_cau_hinh_C3(self):
        status = "BẬT" if self.var_C3.get() else "TẮT"
        self.log_info(f"Cấu hình C - C3: {status}")

    def xu_ly_cau_hinh_C4(self):
        status = "BẬT" if self.var_C4.get() else "TẮT"
        self.log_info(f"Cấu hình C - C4: {status}")

    def xu_ly_cau_hinh_D1(self):
        status = "BẬT" if self.var_D1.get() else "TẮT"
        self.log_info(f"Cấu hình D - D1: {status}")

    def xu_ly_cau_hinh_D2(self):
        status = "BẬT" if self.var_D2.get() else "TẮT"
        self.log_info(f"Cấu hình D - D2: {status}")

    def xu_ly_cau_hinh_D3(self):
        status = "BẬT" if self.var_D3.get() else "TẮT"
        self.log_info(f"Cấu hình D - D3: {status}")

    def xu_ly_cau_hinh_D4(self):
        status = "BẬT" if self.var_D4.get() else "TẮT"
        self.log_info(f"Cấu hình D - D4: {status}")

    def xu_ly_cau_hinh_F1(self):
        status = "BẬT" if self.var_F1.get() else "TẮT"
        self.log_info(f"Cấu hình F - F1: {status}")

    def xu_ly_cau_hinh_F2(self):
        status = "BẬT" if self.var_F2.get() else "TẮT"
        self.log_info(f"Cấu hình F - F2: {status}")

    def xu_ly_cau_hinh_F3(self):
        status = "BẬT" if self.var_F3.get() else "TẮT"
        self.log_info(f"Cấu hình F - F3: {status}")

    def xu_ly_cau_hinh_F4(self):
        status = "BẬT" if self.var_F4.get() else "TẮT"
        self.log_info(f"Cấu hình F - F4: {status}")


if __name__ == "__main__":
    app = ToolLDPlayerGUI()
    app.mainloop()
