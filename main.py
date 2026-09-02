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
import sys
import tempfile
import multiprocessing
from tkinter import filedialog
import webbrowser
import web_server

def get_app_dir():
    """Lấy đường dẫn thư mục thực tế chứa file .exe (hoặc script main.py)"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_bundle_dir():
    """Lấy đường dẫn chứa tài nguyên nội bộ đóng gói bởi PyInstaller (_MEIPASS)"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

# Thử import pystray & PIL cho tính năng khay hệ thống (System Tray)
try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False

# Cấu hình giao diện CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ToolLDPlayerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- CẤU HÌNH CỬA SỔ CHÍNH ---
        self.title("TS Origin-Control")
        self.geometry("500x490")
        self.minsize(460, 380)

        # Đăng ký sự kiện nút X (Thu nhỏ xuống khay hệ thống)
        self.tray_icon = None
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)

        # --- BIẾN TRẠNG THÁI & CẤU HÌNH ---
        self.ld_path = r"C:\Program Files\LDPlayer\LDPlayer9"
        self.var_ld_path = ctk.StringVar(value=self.ld_path)
        self.dict_name_to_index = {}
        self.is_scanning = False
        self.game_icon_path = None
        self.get_app_dir = get_app_dir

        # Biến trạng thái Web Server & Cloudflare Tunnel (Truy cập từ xa)
        self.web_ip = "127.0.0.1"
        self.web_port = 8080
        self.cloudflared_proc = None
        self.public_web_url = ""
        self.current_web_url = ""

        # Biến trạng thái Công tắc tổng ON/OFF & Nút Dừng các Card
        self.var_switch_A = ctk.BooleanVar(value=False)  # Card A: BOSS THẾ GIỚI
        self.var_switch_B = ctk.BooleanVar(value=False)  # Card B: PHỤ BẢN ĐƠN / ĐỘI
        self.var_switch_C = ctk.BooleanVar(value=False)  # Card C: DỊ GIỚI ĐÊM
        self.var_switch_D = ctk.BooleanVar(value=False)  # Card D: 40NPC / 2K
        self.var_pause_D = ctk.BooleanVar(value=False)   # Nút Tạm Dừng ở Card D

        # Biến trạng thái các ô Checkbox Card A (BOSS THẾ GIỚI)
        self.var_A1 = ctk.BooleanVar(value=False)  # Boss
        self.var_A3 = ctk.BooleanVar(value=False)  # Vé

        # Biến trạng thái các ô Checkbox Card B (PHỤ BẢN ĐƠN / ĐỘI)
        self.var_B_don = ctk.BooleanVar(value=False)
        self.var_B_doi = ctk.BooleanVar(value=False)
        self.var_B1 = ctk.BooleanVar(value=False)  # PB 20
        self.var_B2 = ctk.BooleanVar(value=False)  # PB 50
        self.var_B3 = ctk.BooleanVar(value=False)  # PB 80
        self.var_B4 = ctk.BooleanVar(value=False)  # PB 110
        self.var_B5 = ctk.BooleanVar(value=False)  # PB 140

        # Biến trạng thái các ô Checkbox Card C (DỊ GIỚI ĐÊM)
        self.var_C1 = ctk.BooleanVar(value=False)  # Phúc Thần
        self.var_C2 = ctk.BooleanVar(value=False)  # Ký Lục
        self.var_C3 = ctk.BooleanVar(value=False)  # Rút Gọn

        # Biến trạng thái các ô Checkbox Card D (40NPC / 2K)
        self.var_D2 = ctk.BooleanVar(value=False)  # Tổ Đội
        self.var_D3 = ctk.BooleanVar(value=False)  # 40 NPC
        self.var_D4 = ctk.BooleanVar(value=False)  # Nhị Kiều

        # Biến trạng thái trong Card E (TỔ ĐỘI):
        self.var_E_quan_su = ctk.BooleanVar(value=False)
        self.selected_E_list_A_char = ""
        self.selected_E_list_B_char = ""
        self.list_E_B = []  # List tên nhân vật đã add sang Danh Sách B
        self.btn_E_list_A_dict = {}  # Các button bên Danh Sách A
        self.btn_E_list_B_dict = {}  # Các button bên Danh Sách B

        # Biến trạng thái Tab 3 CHIẾN ĐẤU:
        self.var_buff = ctk.BooleanVar(value=False)

        # Biến trạng thái Dừng khẩn cấp & Thông báo khay Taskbar
        self.stop_requested = False
        self.var_enable_notify = ctk.BooleanVar(value=True)

        # --- TẠO HỆ THỐNG GIAO DIỆN ---
        self._setup_grid()
        self._create_ld_selection_card()
        self._create_unified_config_card()
        self._create_ld_path_card()

        # Nạp cấu hình đã lưu
        self.load_config()

        # Căn giữa cửa sổ ứng dụng trên màn hình Desktop (Kích thước chuẩn 500x470)
        self._center_window(500, 470)

        # Quét danh sách LDPlayer lần đầu tiên
        self.refresh_ld_tabs_async()

        # Khởi tạo bộ nhớ log thời gian thực & Kích hoạt Web Server điều khiển từ xa
        self.recent_logs = []
        self.after(600, lambda: web_server.start_web_server(self, port=8080))

    def _center_window(self, width: int = 500, height: int = 470):
        """Căn giữa cửa sổ ứng dụng trên màn hình Desktop"""
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")

    # --- TÍNH NĂNG KHAY HỆ THỐNG (SYSTEM TRAY) ---
    def _create_tray_icon_image(self):
        """Tạo icon đại diện 64x64 cho khay hệ thống"""
        try:
            img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle([2, 2, 62, 62], radius=12, fill='#1F2937', outline='#EA580C', width=3)
            draw.ellipse([18, 18, 46, 46], fill='#EA580C')
            draw.rectangle([28, 22, 36, 42], fill='#FFFFFF')
            draw.rectangle([22, 28, 42, 36], fill='#FFFFFF')
            return img
        except Exception:
            return None

    def _setup_system_tray(self):
        """Khởi tạo Icon và Menu ngữ cảnh ở khay hệ thống Windows (System Tray)"""
        if not HAS_PYSTRAY or self.tray_icon is not None:
            return

        try:
            icon_img = self._create_tray_icon_image()
            if not icon_img:
                return

            menu = pystray.Menu(
                pystray.MenuItem("Mở Tool TS Origin", self._show_window_from_tray, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Thoát Ứng Dụng", self._exit_app_from_tray)
            )
            self.tray_icon = pystray.Icon("TS_Origin_Control", icon_img, "TS Origin-Control", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            print(f"Không thể khởi tạo khay hệ thống: {e}")

    def _on_close_window(self):
        """Sự kiện bấm nút X trên thanh tiêu đề: Thu nhỏ xuống khay hệ thống thay vì tắt hẳn"""
        if HAS_PYSTRAY:
            self.withdraw()  # Ẩn cửa sổ chính
            if self.tray_icon is None:
                self._setup_system_tray()
            self.log_info("📌 Tool đã được thu nhỏ xuống khay hệ thống (System Tray).")
        else:
            self.iconify()  # Thu nhỏ xuống Taskbar nếu không hỗ trợ khay hệ thống

    def _show_window_from_tray(self, icon=None, item=None):
        """Mở lại giao diện từ khay hệ thống"""
        self.after(0, self._restore_window_ui)

    def _restore_window_ui(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self.log_info("📖 Đã mở lại giao diện Tool từ khay hệ thống.")

    def _exit_app_from_tray(self, icon=None, item=None):
        """Thoát hoàn toàn ứng dụng từ menu khay hệ thống"""
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.after(0, self._destroy_app_completely)

    def _destroy_app_completely(self):
        try:
            web_server.stop_active_tunnel(self)
        except Exception:
            pass
        try:
            if hasattr(self, 'web_server') and self.web_server:
                self.web_server.shutdown()
        except Exception:
            pass
        try:
            self.save_config()
        except Exception:
            pass
        self.destroy()
        os._exit(0)


    def _get_character_options(self) -> list:
        """Danh sách các tùy chọn vị trí / chế độ xuất chiến trong menu thả xuống"""
        return ["Xuất Chiến", "Vị Trí 1", "Vị Trí 2", "Vị Trí 3", "Vị Trí 4"]

    def _get_server_options(self) -> list:
        """Danh sách tùy chọn các máy chủ (Điêu Thuyền, Triệu Vân...) và tự động quét các file server_*.png mới"""
        servers = ["Điêu Thuyền", "Triệu Vân"]
        for base in [get_bundle_dir(), get_app_dir()]:
            assets_dir = os.path.join(base, "assets")
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


    def _get_nhanvat_options(self) -> list:
        """Danh sách tên nhân vật cho Danh Sách A: CHỈ quét file trực tiếp trong folder assets/card_e/nhanvat (KHÔNG quét thư mục con 40npc2k và pbdoi)"""
        names = []
        valid_exts = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
        for base in [get_bundle_dir(), get_app_dir()]:
            assets_dir = os.path.join(base, "assets")
            possible_dirs = [
                os.path.join(assets_dir, "card_e", "nhanvat"),
                os.path.join(assets_dir, "nhanvat")
            ]
            for nhanvat_dir in possible_dirs:
                if os.path.exists(nhanvat_dir) and os.path.isdir(nhanvat_dir):
                    try:
                        for f in sorted(os.listdir(nhanvat_dir)):
                            full_f = os.path.join(nhanvat_dir, f)
                            # CHỈ lấy file nằm trực tiếp tại thư mục cha, KHÔNG lấy thư mục con
                            if os.path.isfile(full_f) and f.lower().endswith(valid_exts):
                                char_name = os.path.splitext(f)[0]
                                if char_name and char_name not in names:
                                    names.append(char_name)
                    except Exception:
                        pass
        return sorted(names)

    def _select_E_list_A_item(self, char_name: str):
        """Chọn tên nhân vật bên [Danh Sách A] (đồng bộ folder ảnh)"""
        self.selected_E_list_A_char = char_name
        self._update_E_list_A_ui()

    def _render_E_list_A_ui(self):
        """Vẽ lại các phần tử trong [Danh Sách A] bên trái (Ẩn đi những nhân vật đã được thêm sang Danh Sách B)"""
        if not hasattr(self, 'scroll_E_list_A'):
            return

        for w in self.scroll_E_list_A.winfo_children():
            w.destroy()

        self.btn_E_list_A_dict = {}
        all_nhanvat = self._get_nhanvat_options()
        b_set = set(getattr(self, 'list_E_B', []))
        available_A = [name for name in all_nhanvat if name not in b_set]

        if not available_A:
            lbl_empty = ctk.CTkLabel(
                self.scroll_E_list_A,
                text="(Đã thêm hết)" if all_nhanvat else "(Chưa có ảnh)",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
                text_color="#FFFFFF"
            )
            lbl_empty.pack(pady=10)
            self.selected_E_list_A_char = ""
            return

        selected = getattr(self, 'selected_E_list_A_char', "")
        if not selected or selected not in available_A:
            selected = available_A[0]
            self.selected_E_list_A_char = selected

        for char_name in available_A:
            btn = ctk.CTkButton(
                self.scroll_E_list_A,
                text=char_name,
                height=25,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
                anchor="w",
                fg_color="#EA580C" if char_name == selected else "#374151",
                text_color="#FFFFFF",
                hover_color="#C2410C" if char_name == selected else "#4B5563",
                command=lambda n=char_name: self._select_E_list_A_item(n)
            )
            btn.pack(fill="x", padx=1, pady=2)
            self.btn_E_list_A_dict[char_name] = btn

    def _update_E_list_A_ui(self):
        """Cập nhật màu sắc highlight tên được chọn trong [Danh Sách A] bên trái"""
        if not hasattr(self, 'btn_E_list_A_dict'):
            return
        selected = getattr(self, 'selected_E_list_A_char', "")
        for name, btn in self.btn_E_list_A_dict.items():
            if name == selected:
                btn.configure(fg_color="#EA580C", text_color="#FFFFFF", hover_color="#C2410C")
            else:
                btn.configure(fg_color="#374151", text_color="#FFFFFF", hover_color="#4B5563")

    def _add_A_to_B_E(self):
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

    def _remove_B_item_E(self, char_name: str):
        """Xóa nhân vật khỏi [Danh Sách B] bên phải (Tự động hiện lại bên Danh Sách A)"""
        if hasattr(self, 'list_E_B') and char_name in self.list_E_B:
            self.list_E_B.remove(char_name)
            self._render_E_list_B_ui()
            self._render_E_list_A_ui()
            self.save_config()

    def _select_E_list_B_item(self, char_name: str):
        """Chọn tên nhân vật trong [Danh Sách B]"""
        self.selected_E_list_B_char = char_name
        self._update_E_list_B_ui()

    def _update_E_list_B_ui(self):
        """Cập nhật màu sắc highlight nút đại diện cho tên trong [Danh Sách B]"""
        if not hasattr(self, 'btn_E_list_B_dict'):
            return
        selected = getattr(self, 'selected_E_list_B_char', "")
        for name, btn in self.btn_E_list_B_dict.items():
            if name == selected:
                btn.configure(fg_color="#EA580C", text_color="#FFFFFF", hover_color="#C2410C")
            else:
                btn.configure(fg_color="#374151", text_color="#FFFFFF", hover_color="#4B5563")

    def _get_quan_su_options(self):
        """Lấy danh sách các nhân vật trong Danh Sách B để nạp vào Menu Quân Sư"""
        b_list = getattr(self, 'list_E_B', [])
        return list(b_list) if b_list else ["(Trống)"]

    def _update_E_quan_su_options(self):
        """Cập nhật lại danh sách lựa chọn trong Menu dropdown Quân Sư"""
        if not hasattr(self, 'combo_E_quan_su'):
            return
        opts = self._get_quan_su_options()
        self.combo_E_quan_su.configure(values=opts)
        current = self.combo_E_quan_su.get()
        if current not in opts:
            self.combo_E_quan_su.set(opts[0])

    def _render_E_list_B_ui(self):
        """Vẽ lại các phần tử trong [Danh Sách B] bên phải (giao diện CTkButton 100% y hệt chữ, nền, hình dáng của Danh Sách A)"""
        if not hasattr(self, 'scroll_E_list_B'):
            return

        for w in self.scroll_E_list_B.winfo_children():
            w.destroy()

        self.btn_E_list_B_dict = {}

        if not getattr(self, 'list_E_B', []):
            lbl_empty = ctk.CTkLabel(
                self.scroll_E_list_B,
                text="(Bấm ➔ để thêm)",
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
                text_color="#FFFFFF"
            )
            lbl_empty.pack(pady=10)
            self._update_E_quan_su_options()
            return

        selected_B = getattr(self, 'selected_E_list_B_char', "")
        if not selected_B and self.list_E_B:
            selected_B = self.list_E_B[0]
            self.selected_E_list_B_char = selected_B

        for char_name in list(self.list_E_B):
            row_frame = ctk.CTkFrame(self.scroll_E_list_B, fg_color="transparent")
            row_frame.pack(fill="x", padx=1, pady=2)
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=0)

            btn = ctk.CTkButton(
                row_frame,
                text=char_name,
                height=25,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
                anchor="w",
                fg_color="#EA580C" if char_name == selected_B else "#374151",
                text_color="#FFFFFF",
                hover_color="#C2410C" if char_name == selected_B else "#4B5563",
                command=lambda n=char_name: self._select_E_list_B_item(n)
            )
            btn.grid(row=0, column=0, sticky="ew", padx=(0, 1))

            btn_del = ctk.CTkButton(
                row_frame,
                text="✕",
                width=18,
                height=25,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                fg_color="transparent",
                text_color="#FFFFFF",
                hover_color=("#E5E7EB", "#374151"),
                command=lambda n=char_name: self._remove_B_item_E(n)
            )
            btn_del.grid(row=0, column=1, sticky="e")
            self.btn_E_list_B_dict[char_name] = btn

        self._update_E_quan_su_options()

    def _update_card_E_visibility(self):
        """Cập nhật trạng thái sáng/tối & khóa tùy chỉnh của Card E (Tổ Đội) theo ô check 'Đội' ở Card B (Phụ Bản Đội) hoặc ô 'Tổ Đội' ở Card D (40NPC / 2K)"""
        if not hasattr(self, 'card_E'):
            return

        # Kiểm tra điều kiện mở Card E (Tổ Đội) (Áp dụng cho cả Phụ Bản Đội & 40NPC/2K)
        is_doi_checked = (hasattr(self, 'var_B_doi') and self.var_B_doi.get()) or \
                         (hasattr(self, 'var_D2') and self.var_D2.get())

        # Riêng mục "Quân Sư": Chỉ áp dụng cho Card 40NPC / 2K (var_D2)
        is_40npc_checked = (hasattr(self, 'var_D2') and self.var_D2.get())

        if is_doi_checked:
            # SÁNG LÊN: Bật trạng thái tùy chỉnh và khôi phục màu tiêu đề sáng
            if hasattr(self, 'lbl_E'): self.lbl_E.configure(text_color="#38BDF8")
            if hasattr(self, 'btn_E_add'): self.btn_E_add.configure(state="normal", fg_color="#EA580C", text_color="#FFFFFF")
            if hasattr(self, 'btn_E_list_A_dict'):
                for name, btn in self.btn_E_list_A_dict.items():
                    btn.configure(state="normal")
                self._update_E_list_A_ui()
            if hasattr(self, 'btn_E_list_B_dict'):
                for name, btn in self.btn_E_list_B_dict.items():
                    btn.configure(state="normal")
                self._update_E_list_B_ui()
            self._render_E_list_B_ui()
        else:
            # TỐI ĐI / KHÓA: Đổi màu tiêu đề mờ, tắt công tắc về OFF, khóa click
            if hasattr(self, 'lbl_E'): self.lbl_E.configure(text_color="#9CA3AF")
            if hasattr(self, 'btn_E_add'): self.btn_E_add.configure(state="disabled", fg_color="#374151", text_color="#FFFFFF")
            if hasattr(self, 'btn_E_list_A_dict'):
                for name, btn in self.btn_E_list_A_dict.items():
                    btn.configure(state="disabled", fg_color="#27272A", text_color="#FFFFFF")
            if hasattr(self, 'btn_E_list_B_dict'):
                for name, btn in self.btn_E_list_B_dict.items():
                    btn.configure(state="disabled", fg_color="#27272A", text_color="#FFFFFF")
            self._render_E_list_B_ui()

        # Cấu hình trạng thái riêng của hàng Quân Sư (Chỉ mở khi tích ô Tổ Đội ở 40NPC/2K)
        if is_40npc_checked:
            if hasattr(self, 'chk_E_quan_su'):
                self.chk_E_quan_su.configure(state="normal", text_color="#FFFFFF", border_color="#6B7280", fg_color="#EA580C")
            if hasattr(self, 'combo_E_quan_su'):
                self.combo_E_quan_su.configure(state="normal", text_color="#FFFFFF", fg_color="#374151", button_color="#4B5563", button_hover_color="#6B7280")
        else:
            if hasattr(self, 'chk_E_quan_su'):
                self.chk_E_quan_su.configure(state="disabled", text_color="#4B5563", border_color="#27272A", fg_color="#27272A")
            if hasattr(self, 'combo_E_quan_su'):
                self.combo_E_quan_su.configure(state="disabled", text_color="#4B5563", fg_color="#18181B", button_color="#18181B", button_hover_color="#18181B")

    def _send_notification(self, title: str, message: str):
        """Phát thông báo nổi (Notification Toast) ở góc Taskbar hệ thống nếu tính năng đang BẬT"""
        if not hasattr(self, 'var_enable_notify') or not self.var_enable_notify.get():
            return

        def _notify_worker():
            # 1. Thử phát thông báo qua Pystray Icon nếu đang chạy khay hệ thống
            if hasattr(self, 'tray_icon') and self.tray_icon is not None and getattr(self, 'is_tray_running', False):
                try:
                    self.tray_icon.notify(message, title)
                    return
                except Exception:
                    pass

            # 2. Phát thông báo nổi Toast Notification chuẩn Windows 10/11 qua PowerShell
            try:
                safe_title = title.replace('"', "'")
                safe_msg = message.replace('"', "'")
                ps_script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
$template = @"
<toast>
    <visual>
        <binding template="ToastGeneric">
            <text>{safe_title}</text>
            <text>{safe_msg}</text>
        </binding>
    </visual>
</toast>
"@
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("TS Origin Control").Show($toast)
'''
                subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
            except Exception:
                pass

        threading.Thread(target=_notify_worker, daemon=True).start()

    def _get_current_tab_name(self) -> str:
        """Lấy tên tab LDPlayer hiện tại đang được chọn"""
        if hasattr(self, 'combo_ld_tabs'):
            val = self.combo_ld_tabs.get().strip()
            if val and val not in ["Đang quét tab...", "Lỗi quét dữ liệu", "Không tìm thấy tab LD nào"]:
                return val
        if hasattr(self, 'saved_selected_tab') and self.saved_selected_tab:
            return self.saved_selected_tab
        return "default"

    def _extract_tab_config_from_ui(self) -> dict:
        """Trích xuất toàn bộ trạng thái cài đặt UI hiện tại thành dict cấu hình"""
        cfg = {}
        if hasattr(self, 'combo_server'):
            cfg["server"] = self.combo_server.get()

        if hasattr(self, 'var_B_don'):
            cfg["B_don"] = self.var_B_don.get()
        if hasattr(self, 'var_B_doi'):
            cfg["B_doi"] = self.var_B_doi.get()

        if hasattr(self, 'combo_B_don_char'):
            cfg["B_don_char"] = self.combo_B_don_char.get()
        if hasattr(self, 'combo_B_team_char'):
            cfg["B_team_char"] = self.combo_B_team_char.get()
        if hasattr(self, 'combo_A_char'):
            cfg["A_char"] = self.combo_A_char.get()
        if hasattr(self, 'combo_A_ve'):
            cfg["A_ve"] = self.combo_A_ve.get()

        if hasattr(self, 'combo_D_team_char'):
            cfg["D_team_char"] = self.combo_D_team_char.get()
        if hasattr(self, 'combo_D_chien_dau'):
            cfg["D_chien_dau"] = self.combo_D_chien_dau.get()
        if hasattr(self, 'combo_D_tang'):
            cfg["D_tang"] = self.combo_D_tang.get()
        if hasattr(self, 'var_pause_D'):
            cfg["pause_D"] = False

        for prefix in ["A", "B", "C", "D"]:
            switch_attr = f"var_switch_{prefix}"
            if hasattr(self, switch_attr):
                cfg[f"switch_{prefix}"] = False
            pause_attr = f"var_pause_{prefix}"
            if hasattr(self, pause_attr):
                cfg[f"pause_{prefix}"] = False

            for num in range(1, 6):
                key = f"{prefix}{num}"
                var_attr = f"var_{key}"
                if hasattr(self, var_attr):
                    cfg[key] = getattr(self, var_attr).get()

        if hasattr(self, 'list_E_B'):
            cfg["E_list_B"] = list(self.list_E_B)
        if hasattr(self, 'selected_E_list_A_char'):
            cfg["E_selected_left"] = self.selected_E_list_A_char
        if hasattr(self, 'var_E_quan_su'):
            cfg["E_quan_su"] = self.var_E_quan_su.get()
        if hasattr(self, 'combo_E_quan_su'):
            cfg["E_quan_su_char"] = self.combo_E_quan_su.get()

        if hasattr(self, 'var_buff'):
            cfg["var_buff"] = self.var_buff.get()
        if hasattr(self, 'combo_buff'):
            cfg["combo_buff"] = self.combo_buff.get()

        return cfg

    def _apply_tab_config_to_ui(self, cfg: dict):
        """Khôi phục toàn bộ trạng thái cài đặt UI từ dict cấu hình của tab"""
        if "server" in cfg and hasattr(self, 'combo_server'):
            self.combo_server.set(cfg["server"])

        # Phụ Bản Đơn / Đội (Card B - tương thích ngược key cũ E_don/E_doi)
        b_don_val = cfg.get("B_don", cfg.get("E_don"))
        if b_don_val is not None and hasattr(self, 'var_B_don'):
            self.var_B_don.set(bool(b_don_val))
        b_doi_val = cfg.get("B_doi", cfg.get("E_doi"))
        if b_doi_val is not None and hasattr(self, 'var_B_doi'):
            self.var_B_doi.set(bool(b_doi_val))

        opts = self._get_character_options()
        b_don_char = cfg.get("B_don_char", cfg.get("E_don_char"))
        if b_don_char and hasattr(self, 'combo_B_don_char'):
            self.combo_B_don_char.set(b_don_char if b_don_char in opts else "Xuất Chiến")
        b_team_char = cfg.get("B_team_char", cfg.get("E_team_char"))
        if b_team_char and hasattr(self, 'combo_B_team_char'):
            self.combo_B_team_char.set(b_team_char if b_team_char in opts else "Xuất Chiến")

        # Boss Thế Giới (Card A - tương thích ngược key cũ C_char/C_ve)
        a_char = cfg.get("A_char", cfg.get("C_char"))
        if a_char and hasattr(self, 'combo_A_char'):
            self.combo_A_char.set(a_char if a_char in opts else "Xuất Chiến")

        # 40 NPC / 2K (Card D)
        if "D_team_char" in cfg and hasattr(self, 'combo_D_team_char'):
            val = cfg["D_team_char"]
            self.combo_D_team_char.set(val if val in opts else "Xuất Chiến")
        if "D_chien_dau" in cfg and hasattr(self, 'combo_D_chien_dau'):
            val = cfg["D_chien_dau"]
            self.combo_D_chien_dau.set(val if val in ["Auto", "Click"] else "Auto")
        tang_D_opts = ["Trệt - 10", "11 - 14"]
        if "D_tang" in cfg and hasattr(self, 'combo_D_tang'):
            val = cfg["D_tang"]
            self.combo_D_tang.set(val if val in tang_D_opts else "Trệt - 10")
        if hasattr(self, 'var_pause_D'):
            self.var_pause_D.set(False)

        for prefix in ["A", "B", "C", "D"]:
            switch_attr = f"var_switch_{prefix}"
            if hasattr(self, switch_attr):
                getattr(self, switch_attr).set(False)  # Luôn công tắc OFF khi nạp
            pause_attr = f"var_pause_{prefix}"
            if hasattr(self, pause_attr):
                getattr(self, pause_attr).set(False)  # Luôn nút Tạm Dừng OFF khi nạp

            for num in range(1, 6):
                key = f"{prefix}{num}"
                var_attr = f"var_{key}"
                old_key = key
                if prefix == "A": old_key = f"C{num}"
                elif prefix == "B": old_key = f"E{num}"
                elif prefix == "C": old_key = f"B{num}"
                val = cfg.get(key, cfg.get(old_key))
                if val is not None and hasattr(self, var_attr):
                    getattr(self, var_attr).set(bool(val))

        # Tổ Đội (Card E - tương thích ngược key cũ G)
        sel_left = cfg.get("E_selected_left", cfg.get("G_selected_left"))
        if sel_left:
            self.selected_E_list_A_char = sel_left

        list_b = cfg.get("E_list_B", cfg.get("G_list_B"))
        if list_b and isinstance(list_b, list):
            self.list_E_B = list(list_b)
        else:
            self.list_E_B = []
        self._render_E_list_A_ui()
        self._render_E_list_B_ui()

        e_qs = cfg.get("E_quan_su", cfg.get("G_quan_su"))
        if e_qs is not None and hasattr(self, 'var_E_quan_su'):
            self.var_E_quan_su.set(bool(e_qs))
        e_qs_char = cfg.get("E_quan_su_char", cfg.get("G_quan_su_char"))
        if e_qs_char and hasattr(self, 'combo_E_quan_su'):
            if e_qs_char in self._get_quan_su_options():
                self.combo_E_quan_su.set(e_qs_char)

        # Tab 3: Chiến Đấu (Buff / Skill)
        if "var_buff" in cfg and hasattr(self, 'var_buff'):
            self.var_buff.set(bool(cfg["var_buff"]))
        buff_opts = ["Buff HP", "Buff SP", "Buff 3HP / 1SP"]
        if "combo_buff" in cfg and hasattr(self, 'combo_buff'):
            val = cfg["combo_buff"]
            if val in ["Buff 3HP / SP", "Buff 3HP / 1SP"]:
                val = "Buff 3HP / 1SP"
            self.combo_buff.set(val if val in buff_opts else "Buff HP")

        self._update_card_E_visibility()
        self._update_card_D_row2_state()
        self._update_buff_state()

    def save_config(self):
        """Lưu cấu hình máy chủ & checkbox theo từng tab LDPlayer vào config.json"""
        try:
            config_path = os.path.join(get_app_dir(), "config.json")
            config = {}
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                except Exception:
                    config = {}

            if "tab_configs" not in config or not isinstance(config["tab_configs"], dict):
                config["tab_configs"] = {}

            current_tab = self._get_current_tab_name()
            tab_cfg = self._extract_tab_config_from_ui()
            config["tab_configs"][current_tab] = tab_cfg

            if hasattr(self, 'var_enable_notify'):
                config["enable_notify"] = self.var_enable_notify.get()
            if hasattr(self, 'combo_ld_tabs'):
                config["selected_tab"] = self.combo_ld_tabs.get()
            if hasattr(self, 'var_ld_path'):
                config["ld_path"] = self.var_ld_path.get().strip()

            # Luôn bảo tồn 2 dòng cấu hình ngrok
            if "ngrok_authtoken" not in config:
                config["ngrok_authtoken"] = "3IR0jDxxFPLsNAP9UbnCxFpPXVJ_Mgs51iujUEfsCqJg4JTH"
            if "fixed_domain" not in config:
                config["fixed_domain"] = "https://crusader-visor-disparity.ngrok-free.dev"
            if "ngrok_domain" not in config:
                config["ngrok_domain"] = "https://crusader-visor-disparity.ngrok-free.dev"

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    def load_config(self, target_tab: str = None):
        """Khôi phục cấu hình riêng của tab LDPlayer được chọn từ config.json"""
        config_path = os.path.join(get_app_dir(), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                if "enable_notify" in config and hasattr(self, 'var_enable_notify'):
                    self.var_enable_notify.set(bool(config["enable_notify"]))

                if "ld_path" in config:
                    saved_path = config["ld_path"]
                    if os.path.exists(saved_path):
                        self.ld_path = saved_path
                        if hasattr(self, 'var_ld_path'):
                            self.var_ld_path.set(self.ld_path)

                if "selected_tab" in config and hasattr(self, 'combo_ld_tabs'):
                    self.saved_selected_tab = config["selected_tab"]

                tab_to_load = target_tab or self._get_current_tab_name()
                tab_configs = config.get("tab_configs", {})

                if tab_to_load in tab_configs and isinstance(tab_configs[tab_to_load], dict):
                    tab_cfg = tab_configs[tab_to_load]
                else:
                    # Fallback cho config cũ chưa phân tách tab_configs
                    tab_cfg = config

                self._apply_tab_config_to_ui(tab_cfg)
            except Exception:
                pass

    def _setup_grid(self):
        """Thiết lập Grid Layout 1 cột"""
        self.grid_rowconfigure(0, weight=0)  # Card gộp Tab LDPlayer & Khởi Động
        self.grid_rowconfigure(1, weight=1)  # Khung chứa 5 Card Cấu hình co giãn
        self.grid_rowconfigure(2, weight=0)  # Card chọn đường dẫn LDPlayer9 bên dưới

        self.grid_columnconfigure(0, weight=1)  # Cột duy nhất chứa toàn bộ các Card

    def _create_ld_selection_card(self):
        """Khung Card Bổ Chọn Tab LDPlayer, Server, Game, Run, Stop & Exit (1 Hàng 6 nút, Tỉ lệ 20%:30%:10%:20%:10%:10%)"""
        self.card_ld = ctk.CTkFrame(self, corner_radius=8)
        self.card_ld.grid(row=0, column=0, padx=10, pady=(6, 2), sticky="nsew")
        self.card_ld.grid_columnconfigure(0, weight=2, uniform="top_card_cols")  # Tỉ lệ 20% (Tab LDPlayer)
        self.card_ld.grid_columnconfigure(1, weight=3, uniform="top_card_cols")  # Tỉ lệ 30% (Server)
        self.card_ld.grid_columnconfigure(2, weight=1, uniform="top_card_cols")  # Tỉ lệ 10% (Game)
        self.card_ld.grid_columnconfigure(3, weight=2, uniform="top_card_cols")  # Tỉ lệ 20% (Run)
        self.card_ld.grid_columnconfigure(4, weight=1, uniform="top_card_cols")  # Tỉ lệ 10% (Stop)
        self.card_ld.grid_columnconfigure(5, weight=1, uniform="top_card_cols")  # Tỉ lệ 10% (Exit)
        self.card_ld.grid_rowconfigure(0, weight=1)

        # 1. Menu Tab LDPlayer (Kích thước nút 26px)
        self.combo_ld_tabs = ctk.CTkComboBox(
            self.card_ld,
            values=["Đang quét tab..."],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            height=26,
            command=self._on_ld_tab_selected
        )
        self.combo_ld_tabs.grid(row=0, column=0, padx=(6, 2), pady=4, sticky="ew")

        # 2. Menu Server (OptionMenu - Kích thước nút 26px)
        self.combo_server = ctk.CTkOptionMenu(
            self.card_ld,
            values=self._get_server_options(),
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            height=26,
            dynamic_resizing=False,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=self._on_server_changed
        )
        self.combo_server.set("Điêu Thuyền")
        self.combo_server.grid(row=0, column=1, padx=2, pady=4, sticky="ew")

        # 3. Nút "Game" (Kích thước nút 26px)
        self.btn_enter_game = ctk.CTkButton(
            self.card_ld,
            text="Game",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#FFFFFF",
            height=26,
            fg_color="#38BDF8",
            hover_color="#0284C7",
            command=self.xu_ly_ts_origin
        )
        self.btn_enter_game.grid(row=0, column=2, padx=2, pady=4, sticky="ew")

        # 4. Nút "Run" (Kích thước nút 26px)
        self.btn_run = ctk.CTkButton(
            self.card_ld,
            text="Run",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            height=26,
            fg_color="#059669",
            hover_color="#047857",
            command=self.xu_ly_nut_chay
        )
        self.btn_run.grid(row=0, column=3, padx=2, pady=4, sticky="ew")

        # 5. Nút "Stop" (Kích thước nút 26px)
        self.btn_stop = ctk.CTkButton(
            self.card_ld,
            text="Stop",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            height=26,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=self.dung_tat_ca_hoat_dong
        )
        self.btn_stop.grid(row=0, column=4, padx=2, pady=4, sticky="ew")

        # 6. Nút "Exit" (Màu xám #374151 giống nút Copy - Kích thước nút 26px)
        self.btn_exit_game = ctk.CTkButton(
            self.card_ld,
            text="Exit",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#FFFFFF",
            height=26,
            fg_color="#374151",
            hover_color="#4B5563",
            command=self.xu_ly_exit_game
        )
        self.btn_exit_game.grid(row=0, column=5, padx=(2, 6), pady=4, sticky="ew")

    def _on_ld_tab_selected(self, choice: str):
        """Tự động chuyển đổi cấu hình riêng khi người dùng chọn tab LDPlayer khác"""
        if not choice or choice in ["Đang quét tab...", "Lỗi quét dữ liệu", "Không tìm thấy tab LD nào"]:
            return

        prev_tab = getattr(self, 'current_active_tab', None)
        if prev_tab and prev_tab != choice:
            self.save_config()

        self.current_active_tab = choice
        self.saved_selected_tab = choice

        self.load_config(target_tab=choice)
        self.save_config()
        self.log_info(f"🔄 Đã nạp cấu hình riêng của tab LDPlayer: '{choice}'")

    def _on_server_changed(self, choice: str):
        """Tự động ghi nhớ vị trí máy chủ được chọn để khôi phục cho lần mở tool sau"""
        self.save_config()
        self.log_info(f"💾 Đã ghi nhớ máy chủ: '{choice}'")

    def _create_ld_path_card(self):
        """Card hiển thị đường dẫn thư mục LDPlayer9 & Nút Chọn Thư Mục bên dưới cùng"""
        self.card_path = ctk.CTkFrame(self, corner_radius=8)
        self.card_path.grid(row=2, column=0, padx=10, pady=(2, 6), sticky="nsew")
        self.card_path.grid_columnconfigure(0, weight=1)
        self.card_path.grid_columnconfigure(1, weight=0)

        self.entry_ld_path = ctk.CTkEntry(
            self.card_path,
            textvariable=self.var_ld_path,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            text_color="#FFFFFF",
            height=25,
            fg_color="#1F2937",
            border_width=1,
            border_color="#374151"
        )
        self.entry_ld_path.grid(row=0, column=0, padx=(8, 4), pady=5, sticky="ew")
        self.entry_ld_path.bind("<FocusOut>", lambda e: self._on_ld_path_entry_changed())
        self.entry_ld_path.bind("<Return>", lambda e: self._on_ld_path_entry_changed())

        self.btn_browse_ld = ctk.CTkButton(
            self.card_path,
            text="Folder Path",
            width=95,
            height=25,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#FFFFFF",
            fg_color="#38BDF8",
            hover_color="#0284C7",
            command=self._browse_ld_path
        )
        self.btn_browse_ld.grid(row=0, column=1, padx=(4, 8), pady=(5, 2), sticky="e")

        # Row 1: Khung Đường Link Web Server Điều Khiển Từ Xa
        self.frame_web_bar = ctk.CTkFrame(self.card_path, fg_color="#111827", corner_radius=6, border_width=1, border_color="#374151")
        self.frame_web_bar.grid(row=1, column=0, columnspan=2, padx=8, pady=(2, 6), sticky="ew")
        self.frame_web_bar.grid_columnconfigure(0, weight=1)
        self.frame_web_bar.grid_columnconfigure(1, weight=0)

        self.current_web_url = f"http://{getattr(self, 'web_ip', '127.0.0.1')}:{getattr(self, 'web_port', 8080)}"

        self.lbl_web_url = ctk.CTkLabel(
            self.frame_web_bar,
            text=f"🌐 Web: {self.current_web_url}",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#38BDF8",
            anchor="w"
        )
        self.lbl_web_url.grid(row=0, column=0, padx=(8, 4), pady=4, sticky="w")

        # Frame chứa các nút bấm bên phải (Sao Chép, Mở Web, 4G, Thông Báo) ép sát lề phải
        self.frame_right_btns = ctk.CTkFrame(self.frame_web_bar, fg_color="transparent")
        self.frame_right_btns.grid(row=0, column=1, padx=(2, 8), pady=2, sticky="e")

        self.btn_copy_url = ctk.CTkButton(
            self.frame_right_btns,
            text="Copy",
            width=46,
            height=22,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#FFFFFF",
            fg_color="#374151",
            hover_color="#4B5563",
            command=self._copy_web_url
        )
        self.btn_copy_url.pack(side="left", padx=2)

        self.btn_open_web = ctk.CTkButton(
            self.frame_right_btns,
            text="Open",
            width=46,
            height=22,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#FFFFFF",
            fg_color="#059669",
            hover_color="#047857",
            command=self._open_web_in_browser
        )
        self.btn_open_web.pack(side="left", padx=2)

        self.btn_online_tunnel = ctk.CTkButton(
            self.frame_right_btns,
            text="Create Online",
            width=95,
            height=22,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#FFFFFF",
            fg_color="#EA580C",
            hover_color="#C2410C",
            command=self._start_online_tunnel
        )
        self.btn_online_tunnel.pack(side="left", padx=(2, 0))

    def _copy_web_url(self):
        """Sao chép đường dẫn Web Server vào Clipboard"""
        url = getattr(self, 'current_web_url', '')
        if url:
            self.clipboard_clear()
            self.clipboard_append(url)
            self.log_info(f"📋 Đã sao chép đường link Web: {url}")

    def _open_web_in_browser(self):
        """Mở đường link Web trên trình duyệt mặc định của máy tính"""
        url = getattr(self, 'current_web_url', '')
        if url:
            webbrowser.open(url)
            self.log_info(f"🌐 Đang mở Web Dashboard trên trình duyệt: {url}")

    def _start_online_tunnel(self):
        """Khởi động Cloudflare Tunnel để tạo link truy cập từ xa (4G/Internet)"""
        self.btn_online_tunnel.configure(text="Đang kết nối...", state="disabled")
        web_server.start_cloudflare_tunnel(self)

    def _update_web_url_ui(self, url: str, is_public_4g: bool = False):
        """Cập nhật đường link Web lên thanh hiển thị trên GUI"""
        self.current_web_url = url
        is_4g = is_public_4g or url.startswith("https://")
        if hasattr(self, 'lbl_web_url'):
            prefix = "4G" if is_4g else "Wifi"
            self.lbl_web_url.configure(text=f"🌐 {prefix}: {url}")
        if hasattr(self, 'btn_online_tunnel'):
            if is_4g:
                self.btn_online_tunnel.configure(text="Online Ready", state="disabled", fg_color="#059669")
                try:
                    self.clipboard_clear()
                    self.clipboard_append(url)
                    self.log_info(f"📋 Đã tự động sao chép đường link 4G vào Clipboard: {url}")
                except Exception:
                    pass
            else:
                self.btn_online_tunnel.configure(text="Create Online", state="normal", fg_color="#EA580C")

    def _on_tunnel_failed(self):
        """Xử lý khi đường truyền 4G bị ngắt hoặc không thể tạo tunnel"""
        if hasattr(self, 'btn_online_tunnel'):
            self.btn_online_tunnel.configure(text="Retry Online", state="normal", fg_color="#EA580C")
        if hasattr(self, 'lbl_web_url'):
            local_url = f"http://{getattr(self, 'web_ip', '127.0.0.1')}:{getattr(self, 'web_port', 8080)}"
            self.lbl_web_url.configure(text=f"🌐 Wifi: {local_url}")
            self.current_web_url = local_url
        self.log_warning("⚠️ Đường truyền 4G đã dừng. Bấm 'Retry Online' nếu muốn kết nối lại.")

    def _browse_ld_path(self):
        """Mở hộp thoại chọn thư mục LDPlayer9"""
        curr_path = self.var_ld_path.get().strip()
        init_dir = curr_path if os.path.exists(curr_path) else r"C:\Program Files\LDPlayer"
        selected_dir = filedialog.askdirectory(initialdir=init_dir, title="Chọn thư mục cài đặt LDPlayer9")
        if selected_dir:
            self.ld_path = os.path.normpath(selected_dir)
            self.var_ld_path.set(self.ld_path)
            self.save_config()
            self.refresh_ld_tabs_async()

    def _on_ld_path_entry_changed(self):
        """Xử lý khi người dùng chỉnh sửa đường dẫn trực tiếp trong ô Entry"""
        new_path = self.var_ld_path.get().strip()
        if new_path and os.path.exists(new_path):
            self.ld_path = os.path.normpath(new_path)
            self.save_config()
            self.refresh_ld_tabs_async()

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
        self._update_card_E_visibility()
        self._update_buff_state()
        self.save_config()

    # =========================================================================
    # 🔓 [ĐÃ MỞ KHÓA TOÀN DIỆN - SẴN SÀNG SỬ DỤNG]: CARD F (CẤU HÌNH CHIẾN ĐẤU / SKILL BUFF)
    # =========================================================================
    def _update_buff_state(self):
        """Cập nhật trạng thái ô dropdown Skill (luôn luôn mở sáng để chọn trước chế độ)"""
        if not hasattr(self, 'combo_buff'):
            return
        self.combo_buff.configure(state="normal", fg_color="#374151", button_color="#4B5563", button_hover_color="#6B7280", text_color="#FFFFFF")

    def _on_skill_toggled(self):
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

    def _run_skill_standalone(self, dnconsole_path: str, tab_name: str, tab_index: str):
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

    def _tap_login_auto_twice(self, dnconsole_path: str, tab_index: str):
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

    def _check_and_tap_f_tieptheo(self, dnconsole_path: str, tab_index: str):
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

    def _handle_skill_buff_hp(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """
        Hành động 1 - Buff HP:
        1. Quét chờ xuất hiện: Quét tìm ảnh card_f/f_dung.png (80%) (0.5s/lần) cho tới khi xuất hiện (CHỈ QUÉT KHÔNG TAP)
           - Ngay khi thấy ➔ Quét tìm ảnh card_f/f_tieptheo.png (80%, ROI 1050,530,1165,680) nghỉ 0.25s/lần trong 0.5s.
           - Nếu thấy: tap vào ảnh card_f/f_tieptheo.png, hoãn 0.3s ➔ sang Bước 2.
           - Nếu không thấy: chuyển tiếp sang Bước 2.
        2. Bước 2: quét tìm ảnh card_f/skill/f_hp.png (85%) trong 0.5s
           - NHÁNH A (KHÔNG thấy f_hp.png): quét / tap 2 lần cách nhau 0.15s ảnh card_top/login/login_auto.png (85%) hoãn 5s, sau đó quay lại 1.
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

    def _handle_skill_buff_sp(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """
        Hành động 2 - Buff SP:
        1. Quét chờ xuất hiện: Quét tìm ảnh card_f/f_dung.png (80%) (0.5s/lần) cho tới khi xuất hiện (CHỈ QUÉT KHÔNG TAP)
           - Ngay khi thấy ➔ Quét tìm ảnh card_f/f_tieptheo.png (80%, ROI 1050,530,1165,680) nghỉ 0.25s/lần trong 0.5s.
           - Nếu thấy: tap vào ảnh card_f/f_tieptheo.png, hoãn 0.3s ➔ sang Bước 2.
           - Nếu không thấy: chuyển tiếp sang Bước 2.
        2. Bước 2: quét tìm ảnh card_f/skill/f_sp.png (85%) trong 0.5s
           - NHÁNH A (KHÔNG thấy f_sp.png): quét / tap 2 lần cách nhau 0.15s ảnh card_top/login/login_auto.png (85%) hoãn 5s, sau đó quay lại 1.
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

    def _handle_skill_buff_3hp_1sp(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """
        Hành động 5 - Buff 3HP / 1SP (Tự động luân phiên 3 Lượt HP ➔ 1 Lượt SP):
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



    def _on_switch_C_toggled(self):
        """Callback công tắc Card DỊ GIỚI: Gạt ON ➔ Khởi chạy độc lập ngay lập tức; Gạt OFF ➔ Dừng tiến trình card này"""
        self._on_checkbox_toggled()
        if not self.var_switch_C.get():
            self.save_config()
            self.log_info("🛑 [CARD DỊ GIỚI] Công tắc gạt về OFF ➔ Đã ngắt tiến trình Card Dị Giới!")
        else:
            self.stop_requested = False
            tab_name, tab_index = self._get_selected_ld_info()
            if tab_index is None:
                self.log_error("Vui lòng chọn một Tab LDPlayer trước khi bật công tắc Dị Giới!")
                self.var_switch_C.set(False)
                self.save_config()
                return

            dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")

            if not os.path.exists(dnconsole_path):
                self.log_error(f"Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
                self.var_switch_C.set(False)
                self.save_config()
                return

            self.save_config()
            self.log_info(f"⚡ [DỊ GIỚI] Công tắc vừa trượt ON ➔ Khởi chạy ngay thao tác Dị Giới trên Tab: {tab_name} (Index: {tab_index})...")
            threading.Thread(target=self._run_card_C_di_gioi_standalone, args=(dnconsole_path, tab_name, tab_index), daemon=True).start()

    def _run_card_C_di_gioi_standalone(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """Worker thread thực thi độc lập cho Card Dị Giới khi bật công tắc B"""
        try:
            self._execute_card_C_di_gioi(dnconsole_path, tab_name, tab_index)
            if not self.stop_requested:
                if not self.var_switch_C.get():
                    self.after(0, self.log_info, "🛑 [DỊ GIỚI] Công tắc Card Dị Giới gạt về OFF ➔ Đã dừng thao tác Card này!")
                else:
                    self.after(0, lambda: self.var_switch_C.set(False))
                    self.after(0, self.save_config)
                    self.after(0, self.log_info, "✅ [DỊ GIỚI] Đã hoàn thành Card Dị Giới ➔ Tự động nhả công tắc B về OFF!")
        except Exception as e:
            self.after(0, self.log_error, f"❌ Lỗi luồng Card Dị Giới: {str(e)}")

    def _on_switch_B_toggled(self):
        """Callback công tắc Card PHỤ BẢN ĐƠN / ĐỘI: Gạt ON ➔ Sẵn sàng chờ nút Chạy; Gạt OFF ➔ Dừng tiến trình card này"""
        self._on_checkbox_toggled()
        if not self.var_switch_B.get():
            self._update_card_E_visibility()
            self.save_config()
            self.log_info("🛑 [CARD PHỤ BẢN ĐƠN / ĐỘI] Công tắc gạt về OFF ➔ Đã ngắt tiến trình Card Phụ Bản!")
        else:
            self._update_card_E_visibility()
            self.save_config()
            self.log_info("⚡ [CARD PHỤ BẢN ĐƠN / ĐỘI] Công tắc gạt sang ON ➔ Sẵn sàng thực thi khi bấm nút 'Chạy'.")

    def _on_switch_A_toggled(self):
        """Callback công tắc Card BOSS THẾ GIỚI: Gạt ON ➔ Sẵn sàng chờ nút Chạy; Gạt OFF ➔ Dừng tiến trình card này"""
        self._on_checkbox_toggled()
        if not self.var_switch_A.get():
            self.save_config()
            self.log_info("🛑 [CARD BOSS THẾ GIỚI] Công tắc gạt về OFF ➔ Đã ngắt tiến trình Card Boss Thế Giới!")
        else:
            self.save_config()
            self.log_info("⚡ [CARD BOSS THẾ GIỚI] Công tắc gạt sang ON ➔ Sẵn sàng thực thi khi bấm nút 'Chạy'.")

    def _on_switch_D_toggled(self):
        """Callback riêng cho công tắc Card B (40 NPC): Khi trượt sang OFF -> Ngắt tiến trình & nhả ô Tạm Dừng, giữ nguyên các ô check"""
        self._on_checkbox_toggled()
        if not self.var_switch_D.get():
            if hasattr(self, 'var_pause_D'):
                self.var_pause_D.set(False)
            self.save_config()
            self.log_info("🛑 [CARD E: 40 NPC] Công tắc gạt về OFF ➔ Đã ngắt tiến trình & nhả ô Tạm Dừng Card B!")
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

    def _on_pause_D_toggled(self):
        """Callback nút Dừng ở Card 40 NPC: Tích vào thì tạm dừng, nhả ra chạy tiếp"""
        self._on_checkbox_toggled()
        if self.var_pause_D.get():
            self.log_info("⏸️ [40 NPC] Tích ô Dừng ➔ Tạm dừng hoạt động 40 NPC (nhả ô Dừng sẽ chạy tiếp)!")
        else:
            self.log_info("▶️ [40 NPC] Nhả ô Dừng ➔ Khôi phục chạy tiếp 40 NPC!")
        self.save_config()

    def _refresh_desktop_logs(self):
        """Làm mới danh sách nhật ký hiển thị trên Tab Nhật Ký của Desktop GUI"""
        if hasattr(self, 'txt_log') and hasattr(self, 'recent_logs'):
            self.txt_log.configure(state="normal")
            self.txt_log.delete("1.0", "end")
            for line in self.recent_logs:
                self.txt_log.insert("end", f"{line}\n")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")

    def _create_unified_config_card(self):
        """Tạo hệ thống phân Tab giao diện Desktop (Tab 1: Cards A-D, Tab 2: Tổ Đội, Tab 3: Chiến Đấu, Tab 4: Log)"""
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=12,
            fg_color="#0F172A",
            segmented_button_fg_color="#1E293B",
            segmented_button_selected_color="#0284C7",
            segmented_button_selected_hover_color="#0369A1",
            text_color="#FFFFFF"
        )
        self.tabview.grid(row=1, column=0, padx=10, pady=2, sticky="nsew")

        # Khởi tạo 4 Tab chính theo đúng thứ tự
        tab_ctrl = self.tabview.add("🎮 Hoạt Động")
        tab_team = self.tabview.add("👥 Tổ Đội")
        tab_combat = self.tabview.add("⚔️ Chiến Đấu")
        tab_logs = self.tabview.add("📜 Nhật Ký")

        # Cấu hình đồng bộ kích thước khung chữ bằng nhau 100% cho cả 4 nút Tab
        if hasattr(self.tabview, "_segmented_button"):
            self.tabview._segmented_button.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="equal_tabs")

        # ------------------- TAB 1: 🎮 HOẠT ĐỘNG (CARDS A, B, C, D) -------------------
        # Hàng 1: Card A (Boss TG) | Card C (Dị Giới)
        # Hàng 2: Card B (Phụ Bản) | Card D (40 NPC)
        self.container_cfg = ctk.CTkFrame(tab_ctrl, fg_color="transparent")
        self.container_cfg.pack(fill="both", expand=True, padx=2, pady=2)
        self.container_cfg.grid_columnconfigure(0, weight=1, uniform="card_cols")
        self.container_cfg.grid_columnconfigure(1, weight=1, uniform="card_cols")
        self.container_cfg.grid_rowconfigure(0, weight=148, uniform="card_rows")
        self.container_cfg.grid_rowconfigure(1, weight=178, uniform="card_rows")

        # ------------------- TAB 4: 📜 NHẬT KÝ HOẠT ĐỘNG -------------------
        hdr_log = ctk.CTkFrame(tab_logs, fg_color="transparent")
        hdr_log.pack(fill="x", padx=4, pady=(2, 4))
        lbl_log = ctk.CTkLabel(
            hdr_log,
            text="📜 Nhật Ký Hoạt Động Thời Gian Thực",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#38BDF8"
        )
        lbl_log.pack(side="left")

        btn_ref_log = ctk.CTkButton(
            hdr_log,
            text="🔄 Làm Mới",
            width=75,
            height=22,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#374151",
            hover_color="#4B5563",
            text_color="#FFFFFF",
            command=self._refresh_desktop_logs
        )
        btn_ref_log.pack(side="right")

        self.txt_log = ctk.CTkTextbox(
            tab_logs,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#050811",
            text_color="#CBD5E1",
            corner_radius=8
        )
        self.txt_log.pack(fill="both", expand=True, padx=4, pady=(0, 4))

        # ------------------- CARD A: BOSS THẾ GIỚI (Hàng 1, Cột 0) -------------------
        self.card_A = ctk.CTkFrame(self.container_cfg, corner_radius=10)
        self.card_A.grid(row=0, column=0, padx=3, pady=2, sticky="nsew")
        self.card_A.grid_columnconfigure(0, weight=1)
        self.card_A.grid_rowconfigure(0, weight=0)
        self.card_A.grid_rowconfigure((1, 3), weight=1)
        self.card_A.grid_rowconfigure(2, weight=0)

        hdr_A = ctk.CTkFrame(self.card_A, fg_color="transparent")
        hdr_A.grid(row=0, column=0, padx=8, pady=(2, 0), sticky="ew")
        hdr_A.grid_columnconfigure(0, weight=1)
        hdr_A.grid_columnconfigure(1, weight=0)

        lbl_A = ctk.CTkLabel(hdr_A, text="BOSS TG", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color="#38BDF8")
        lbl_A.grid(row=0, column=0, sticky="w")

        self.switch_A = ctk.CTkSwitch(
            hdr_A, text="", variable=self.var_switch_A, command=self._on_switch_A_toggled,
            width=28, height=14, switch_width=28, switch_height=14, fg_color="#374151", progress_color="#EA580C", text_color="#FFFFFF"
        )
        self.switch_A.grid(row=0, column=1, sticky="e")

        char_options = self._get_character_options()

        # Row 1: Boss + Menu Vị trí xuất chiến (Tương đương Row 1 của Card C)
        row_A1 = ctk.CTkFrame(self.card_A, fg_color="transparent")
        row_A1.grid(row=1, column=0, padx=6, pady=0, sticky="ew")

        self.chk_A1 = ctk.CTkCheckBox(
            row_A1, text="Boss", variable=self.var_A1, command=self._on_checkbox_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
        )
        self.chk_A1.pack(side="left")

        self.combo_A_char = ctk.CTkOptionMenu(
            row_A1,
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
        self.combo_A_char.set(char_options[0] if char_options else "Xuất Chiến")
        self.combo_A_char.pack(side="right", padx=(0, 2))

        # Đường gạch ngang phân cách màu cam #EA580C ở giữa Row 1 và Lịch Thứ, Hệ
        divider_horiz_A = ctk.CTkFrame(self.card_A, height=2, corner_radius=0, fg_color="#EA580C", border_width=0)
        divider_horiz_A.grid(row=2, column=0, sticky="ew", padx=4, pady=(1, 2))

        # Row 3: Lịch hệ Boss Thế Giới 7 ngày T2-CN (Thứ, Hệ)
        schedule_A = ctk.CTkFrame(self.card_A, fg_color="transparent")
        schedule_A.grid(row=3, column=0, padx=6, pady=(0, 2), sticky="ew")
        schedule_A.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

        all_days = [
            ("T2", "Địa", "#FBBF24"),
            ("T3", "Thủy", "#38BDF8"),
            ("T4", "Hỏa", "#F87171"),
            ("T5", "Phong", "#4ADE80"),
            ("T6", "Hỏa", "#F87171"),
            ("T7", "Thủy", "#38BDF8"),
            ("CN", "Phong", "#4ADE80"),
        ]
        for col_idx, (day, elem, color) in enumerate(all_days):
            box = ctk.CTkFrame(schedule_A, fg_color="transparent")
            box.grid(row=0, column=col_idx, sticky="nsew")
            lbl_d = ctk.CTkLabel(box, text=day, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color="gray70", height=16)
            lbl_d.pack(side="top", anchor="center")
            lbl_e = ctk.CTkLabel(box, text=elem, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=color, height=16)
            lbl_e.pack(side="top", anchor="center", pady=(3, 0))

        # =========================================================================
        # 🔓 [ĐÃ MỞ KHÓA TOÀN DIỆN - SẴN SÀNG SỬ DỤNG]: GIAO DIỆN CARD C (DỊ GIỚI ĐÊM)
        # =========================================================================
        self.card_C = ctk.CTkFrame(self.container_cfg, corner_radius=10)
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
        # 🔓 [ĐÃ MỞ KHÓA TOÀN DIỆN - SẴN SÀNG SỬ DỤNG]: GIAO DIỆN CARD B (PHỤ BẢN ĐƠN / ĐỘI)
        # =========================================================================
        self.card_B = ctk.CTkFrame(self.container_cfg, corner_radius=10)
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
        # 🔓 [ĐÃ MỞ KHÓA TOÀN DIỆN - SẴN SÀNG SỬ DỤNG]: GIAO DIỆN CARD D (40 NPC / 2K)
        # =========================================================================
        self.card_D = ctk.CTkFrame(self.container_cfg, corner_radius=10)
        self.card_D.grid(row=1, column=1, padx=3, pady=3, sticky="nsew")
        self.card_D.grid_columnconfigure(0, weight=1)
        self.card_D.grid_rowconfigure(0, weight=0)
        self.card_D.grid_rowconfigure(1, weight=1)

        hdr_D = ctk.CTkFrame(self.card_D, fg_color="transparent")
        hdr_D.grid(row=0, column=0, padx=8, pady=(4, 1), sticky="ew")
        hdr_D.grid_columnconfigure(0, weight=1)
        hdr_D.grid_columnconfigure(1, weight=0)
        hdr_D.grid_columnconfigure(2, weight=0)

        lbl_D = ctk.CTkLabel(hdr_D, text="40NPC / 2K", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color="#38BDF8")
        lbl_D.grid(row=0, column=0, sticky="w")

        self.chk_pause_D = ctk.CTkCheckBox(
            hdr_D, text="Tạm Dừng", variable=self.var_pause_D, command=self._on_pause_D_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=14, checkbox_height=14, border_width=2, corner_radius=7
        )
        self.chk_pause_D.grid(row=0, column=1, sticky="e", padx=(0, 2))

        self.switch_D = ctk.CTkSwitch(
            hdr_D, text="", variable=self.var_switch_D, command=self._on_switch_D_toggled,
            width=28, height=14, switch_width=28, switch_height=14, fg_color="#374151", progress_color="#EA580C", text_color="#FFFFFF"
        )
        self.switch_D.grid(row=0, column=2, sticky="e")

        # Thùng chứa toàn bộ thân Card D (Tổ Đội chiếm 1 phần, Khung Hoạt Động chiếm 2 phần)
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
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
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

        # Khung 2 Cột Hoạt Động (40 NPC & Nhị Kiều) với 1 VẠCH CAM ĐỨNG DUY NHẤT LIỀN MẠCH xuyên suốt Hàng 2 & 3
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

        # 1 Vạch gạch đứng màu cam #EA580C DUY NHẤT LIỀN MẠCH từ Hàng 2 xuống hết Hàng 3 (rowspan=2)
        divider_vert_D = ctk.CTkFrame(act_frame_D, width=2, corner_radius=0, fg_color="#EA580C", border_width=0)
        divider_vert_D.grid(row=0, column=1, rowspan=2, sticky="ns", padx=4, pady=2)

        self.chk_D4 = ctk.CTkCheckBox(
            act_frame_D, text="Nhị Kiều", variable=self.var_D4, command=self._on_D4_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5,
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF"
        )
        self.chk_D4.grid(row=0, column=2, sticky="w", padx=(4, 0))

        # Hàng 3: Menu Auto/Click (quản lý bởi 40 NPC)  |  Menu Tầng (quản lý bởi Nhị Kiều)
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
        # 🔓 [ĐÃ MỞ KHÓA TOÀN DIỆN - SẴN SÀNG SỬ DỤNG]: GIAO DIỆN CARD E (QUẢN LÝ TỔ ĐỘI)
        # =========================================================================
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
        # 🔓 [ĐÃ MỞ KHÓA TOÀN DIỆN - SẴN SÀNG SỬ DỤNG]: GIAO DIỆN CARD F (CẤU HÌNH CHIẾN ĐẤU)
        # =========================================================================
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

        # Hàng 1: [ ] Buff | [ Menu Dropdown Cố Định Kích Thước: Buff HP / Buff SP / Buff HP / SP ]
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

        # Cập nhật trạng thái khóa ban đầu
        self._update_card_D_row2_state()
        self._update_buff_state()

    def _on_D3_toggled(self):
        """Khi tích sự kiện 40 NPC -> Bỏ chọn sự kiện Nhị Kiều (2 sự kiện độc lập loại trừ nhau)"""
        if self.var_D3.get():
            self.var_D4.set(False)
        self._update_card_D_row2_state()
        self._on_checkbox_toggled()

    def _on_D4_toggled(self):
        """Khi tích sự kiện Nhị Kiều -> Bỏ chọn sự kiện 40 NPC (2 sự kiện độc lập loại trừ nhau)"""
        if self.var_D4.get():
            self.var_D3.set(False)
        self._update_card_D_row2_state()
        self._on_checkbox_toggled()

    def _update_card_D_row2_state(self):
        """
        Cập nhật trạng thái quản lý giữa Cột 40 NPC và Cột Nhị Kiều:
        - Ô menu Auto/Click thuộc quản lý trực tiếp của ô sự kiện 40 NPC (var_D3).
        - Ô menu Tầng thuộc quản lý trực tiếp của ô sự kiện Nhị Kiều (var_D4).
        - 2 sự kiện là 2 chế độ riêng biệt không liên quan nhau.
        """
        if not hasattr(self, 'chk_D3') or not hasattr(self, 'chk_D4'):
            return

        is_40npc = self.var_D3.get()
        is_2k = self.var_D4.get()

        if is_40npc:
            # 40 NPC được chọn: Mở menu Auto/Click, Khóa mờ cụm Nhị Kiều
            self.chk_D3.configure(state="normal", text_color="#FFFFFF")
            self.combo_D_chien_dau.configure(
                state="normal", text_color="#FFFFFF", fg_color="#374151",
                button_color="#4B5563", button_hover_color="#6B7280"
            )
            self.chk_D4.configure(state="disabled", text_color="#4B5563")
            self.combo_D_tang.configure(
                state="disabled", text_color="#4B5563", fg_color="#18181B",
                button_color="#18181B", button_hover_color="#18181B"
            )
        elif is_2k:
            # Nhị Kiều được chọn: Mở menu Tầng, Khóa mờ cụm 40 NPC
            self.chk_D4.configure(state="normal", text_color="#FFFFFF")
            self.combo_D_tang.configure(
                state="normal", text_color="#FFFFFF", fg_color="#374151",
                button_color="#4B5563", button_hover_color="#6B7280"
            )
            self.chk_D3.configure(state="disabled", text_color="#4B5563")
            self.combo_D_chien_dau.configure(
                state="disabled", text_color="#4B5563", fg_color="#18181B",
                button_color="#18181B", button_hover_color="#18181B"
            )
        else:
            # Cả 2 chưa được chọn: Cho phép chọn 1 trong 2 sự kiện, nhưng khóa cả 2 menu bên dưới
            self.chk_D3.configure(state="normal", text_color="#FFFFFF")
            self.chk_D4.configure(state="normal", text_color="#FFFFFF")
            self.combo_D_chien_dau.configure(
                state="disabled", text_color="#4B5563", fg_color="#18181B",
                button_color="#18181B", button_hover_color="#18181B"
            )
            self.combo_D_tang.configure(
                state="disabled", text_color="#4B5563", fg_color="#18181B",
                button_color="#18181B", button_hover_color="#18181B"
            )

        
    # --- HÀM CẬP NHẬT TRẠNG THÁI & XUẤT LOG ---
    def log_info(self, message: str):
        """Cập nhật thông tin lên thanh trạng thái & ô ghi Log trực tiếp trên GUI & Web UI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] ℹ️ {message}"
        if not hasattr(self, 'recent_logs'):
            self.recent_logs = []
        self.recent_logs.append(log_line)
        if len(self.recent_logs) > 60:
            self.recent_logs.pop(0)

        if hasattr(self, 'lbl_status'):
            self.lbl_status.configure(text=f"Thông báo: {message}")
        if hasattr(self, 'txt_log'):
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", f"{log_line}\n")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")

    def log_warning(self, message: str):
        """Cập nhật cảnh báo lên thanh trạng thái & ô ghi Log trực tiếp trên GUI & Web UI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] ⚠️ {message}"
        if not hasattr(self, 'recent_logs'):
            self.recent_logs = []
        self.recent_logs.append(log_line)
        if len(self.recent_logs) > 60:
            self.recent_logs.pop(0)

        if hasattr(self, 'lbl_status'):
            self.lbl_status.configure(text=f"Cảnh báo: {message}")
        if hasattr(self, 'txt_log'):
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", f"{log_line}\n")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")

    def log_error(self, message: str):
        """Cập nhật lỗi lên thanh trạng thái & ô ghi Log trực tiếp trên GUI & Web UI"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] ❌ {message}"
        if not hasattr(self, 'recent_logs'):
            self.recent_logs = []
        self.recent_logs.append(log_line)
        if len(self.recent_logs) > 60:
            self.recent_logs.pop(0)

        if hasattr(self, 'lbl_status'):
            self.lbl_status.configure(text=f"Lỗi: {message}")
        if hasattr(self, 'txt_log'):
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", f"{log_line}\n")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")

    def _exec_cmd(self, cmd_list, text=False):
        """Thực thi lệnh ADB/LDConsole an toàn và chính xác 100% trên mọi Tab LDPlayer"""
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

        # 1. Thử chạy trực tiếp lệnh dnconsole/ldconsole (Cơ chế chuẩn native 100% của LDPlayer)
        try:
            res = subprocess.run(cmd_list, timeout=15, **kwargs)
            if res is not None and res.returncode == 0:
                return res
            elif res is not None:
                # Nếu lệnh dnconsole chính chủ chạy xong (kể cả returncode != 0), vẫn ưu tiên kết quả chính chủ
                pass
        except OSError as e:
            if getattr(e, 'winerror', None) == 740 or "740" in str(e):
                try:
                    cmd_str = " ".join([f'"{arg}"' if " " in str(arg) else str(arg) for arg in cmd_list])
                    res_cmd = subprocess.run(f'cmd /c {cmd_str}', shell=True, timeout=15, **kwargs)
                    if res_cmd is not None:
                        return res_cmd
                except Exception:
                    pass
        except Exception:
            pass

        # 2. Nếu là lệnh ADB gọi qua dnconsole và gặp sự cố, mới chuyển hướng dự phòng qua adb.exe
        if len(cmd_list) >= 6 and cmd_list[1] == "adb" and "--index" in cmd_list and "--command" in cmd_list:
            try:
                idx_pos = cmd_list.index("--index") + 1
                cmd_pos = cmd_list.index("--command") + 1
                tab_idx = int(cmd_list[idx_pos])
                raw_subcmd = str(cmd_list[cmd_pos]).strip()

                adb_path = os.path.join(self.ld_path, "adb.exe")

                if os.path.exists(adb_path):
                    port_5555 = 5555 + (tab_idx * 2)
                    port_5554 = 5554 + (tab_idx * 2)
                    
                    # Kết nối tự động lại cổng ADB nếu bị rớt
                    try:
                        subprocess.run([adb_path, "connect", f"127.0.0.1:{port_5555}"], timeout=3, **kwargs)
                    except Exception:
                        pass

                    candidate_devices = [
                        f"127.0.0.1:{port_5555}",
                        f"emulator-{port_5554}"
                    ]

                    for device_id in candidate_devices:
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

                        res = subprocess.run(direct_adb_cmd, timeout=15, **kwargs)
                        if res.returncode == 0:
                            return res
            except Exception:
                pass

        # Fallback chạy lại lệnh gốc
        try:
            return subprocess.run(cmd_list, timeout=15, **kwargs)
        except Exception:
            return None

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

    # --- QUÉT VÀ CẬP NHẬT DỮ LIỆU LDPLAYER (ASYNC) ---
    def refresh_ld_tabs_async(self):
        """Kích hoạt quét LDPlayer trong Thread riêng biệt tránh đơ UI"""
        if self.is_scanning:
            return

        self.is_scanning = True
        if hasattr(self, 'btn_refresh'):
            self.btn_refresh.configure(state="disabled", text="Đang quét...")
        if hasattr(self, 'lbl_status'):
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
        if hasattr(self, 'btn_refresh'):
            self.btn_refresh.configure(state="normal", text="Làm Mới")

        if error_msg:
            self.combo_ld_tabs.configure(values=["Lỗi quét dữ liệu"])
            self.combo_ld_tabs.set("Lỗi quét dữ liệu")
            if hasattr(self, 'lbl_status'): self.lbl_status.configure(text="Lỗi quét LDPlayer")
            if hasattr(self, 'lbl_tab_count'): self.lbl_tab_count.configure(text="Tab LD: 0")
            self.log_error(f"Quét tab thất bại: {error_msg}")
            return

        if dict_map is not None:
            self.dict_name_to_index = dict_map

        if tab_names:
            current_selection = self.combo_ld_tabs.get()
            self.combo_ld_tabs.configure(values=tab_names)

            saved_tab = getattr(self, 'saved_selected_tab', None)
            if current_selection in tab_names and current_selection not in ["Đang quét tab...", "Lỗi quét dữ liệu", "Không tìm thấy tab LD nào"]:
                target_sel = current_selection
            elif saved_tab and saved_tab in tab_names:
                target_sel = saved_tab
            else:
                target_sel = tab_names[0]

            self.combo_ld_tabs.set(target_sel)
            self._on_ld_tab_selected(target_sel)

            count = len(tab_names)
            if hasattr(self, 'lbl_status'): self.lbl_status.configure(text="Quét danh sách thành công.")
            if hasattr(self, 'lbl_tab_count'): self.lbl_tab_count.configure(text=f"Tab LD: {count}")
            self.log_info(f"Đã phát hiện {count} tab LDPlayer: {', '.join(tab_names)}")
        else:
            self.combo_ld_tabs.configure(values=["Không tìm thấy tab LD nào"])
            self.combo_ld_tabs.set("Không tìm thấy tab LD nào")
            if hasattr(self, 'lbl_status'): self.lbl_status.configure(text="Không tìm thấy giả lập LDPlayer đang khởi tạo.")
            if hasattr(self, 'lbl_tab_count'): self.lbl_tab_count.configure(text="Tab LD: 0")
            self.log_info("Không tìm thấy tab LDPlayer nào.")

    def _minimize_ld_window(self, tab_index: str = None, tab_name: str = None):
        """Tự động thu nhỏ cửa sổ giả lập LDPlayer xuống thanh Taskbar bằng Win32 API native (Loại trừ cửa sổ Tool GUI)"""
        if os.name != 'nt':
            return
        try:
            import ctypes
            user32 = ctypes.windll.user32

            tool_hwnd = None
            try:
                tool_hwnd = self.winfo_id()
            except Exception:
                pass

            def enum_windows_callback(hwnd, extra):
                # Tuyệt đối không thu nhỏ cửa sổ của Tool GUI
                if tool_hwnd and hwnd == tool_hwnd:
                    return True

                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        title = buff.value
                        
                        # Bỏ qua cửa sổ Tool GUI (TS Origin-Control)
                        if "TS Origin-Control" in title or "TS Origin - Control" in title or "Control" in title:
                            return True

                        # Chỉ tìm cửa sổ giả lập LDPlayer thực sự
                        is_ld = "LDPlayer" in title or "dnplayer" in title.lower() or (tab_name and tab_name.lower() in title.lower())
                        if is_ld:
                            matched = False
                            if tab_name and tab_name.lower() in title.lower():
                                matched = True
                            elif tab_index is not None:
                                str_idx = str(tab_index)
                                if f"({str_idx})" in title or f"-{str_idx}" in title or f" {str_idx}" in title or title.endswith(str_idx):
                                    matched = True
                            elif "LDPlayer" in title:
                                matched = True

                            if matched:
                                user32.ShowWindow(hwnd, 6) # SW_MINIMIZE = 6
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
        except Exception:
            pass

    # =========================================================================
    # 🔓 [ĐÃ MỞ KHÓA TOÀN DIỆN - SẴN SÀNG SỬ DỤNG]: BỘ NÚT TOP (GAME, RUN, STOP, EXIT)
    # =========================================================================
    def xu_ly_exit_game(self):
        """Thoát ứng dụng game TS Origin về màn hình chính giả lập LDPlayer"""
        tab, idx = self._get_selected_ld_info()
        if idx is None:
            self.log_error("Vui lòng chọn một Tab LDPlayer trước khi bấm Exit!")
            return

        self.log_info(f"🚪 [Exit] Đang đóng game và về màn hình chính giả lập LDPlayer (Tab {tab})...")
        threading.Thread(target=self._worker_exit_game, args=(tab, idx), daemon=True).start()

    def _worker_exit_game(self, tab_name: str, tab_index: str):
        try:
            dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")

            target_pkg = "com.vtcmobile.gz06"
            if os.path.exists(dnconsole_path):
                # 1. Quét đóng ứng dụng game qua killapp
                self._exec_cmd([dnconsole_path, "killapp", "--index", str(tab_index), "--packagename", target_pkg])
                # 2. Force stop qua ADB
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell am force-stop {target_pkg}"])
                # 3. Gửi phím Home (keyevent 3) để về màn hình chính giả lập
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input keyevent 3"])

            self.after(0, self.log_info, f"✅ [Exit] Đã thoát game trên Tab {tab_name} thành công! (Về màn hình chính giả lập)")
        except Exception as e:
            self.after(0, self.log_error, f"❌ Lỗi khi đóng game trên Tab {tab_name}: {e}")

    # ---- HÀM XỬ LÝ SỰ KIỆN TS ORIGIN (TỰ ĐỘNG BẤM ICON MỞ GAME) ----
    def xu_ly_ts_origin(self):
        tab, idx = self._get_selected_ld_info()
        if idx is None:
            self.log_error("Vui lòng chọn một Tab LDPlayer trước khi bấm mở game!")
            return

        server = self.combo_server.get()
        self.log_info(f"Bắt đầu quy trình: Bật Giả lập LDPlayer (Tab {tab}) ➔ Chờ Load 100% ➔ Tự động thu nhỏ xuống Taskbar ➔ Mở App Game ➔ Chọn Máy Chủ '{server}'...")
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

            # Bước 1: Gửi lệnh mở/kích hoạt giả lập LDPlayer & TỰ ĐỘNG THU NHỎ NGAY LẬP TỨC
            if not self._is_ld_loaded_100(dnconsole_path, tab_index):
                self.after(0, self.log_info, f"🖥️ [Bước 1/4] Đang khởi động Giả lập LDPlayer Tab: {tab_name} (Index: {tab_index})...")
                self._exec_cmd([dnconsole_path, "launch", "--index", str(tab_index)])
                time.sleep(0.5)
                self._minimize_ld_window(tab_index, tab_name)
                self.after(0, self.log_info, f"📉 [Bước 1/4] Đã tự động thu nhỏ cửa sổ LDPlayer (Tab {tab_name}) xuống khay Taskbar ngay khi kích hoạt!")
            else:
                self.after(0, self.log_info, f"🖥️ Tab LDPlayer {tab_name} (Index: {tab_index}) đã mở sẵn ➔ Tự động thu nhỏ xuống khay Taskbar...")
                self._minimize_ld_window(tab_index, tab_name)

            # Bước 2: Theo dõi tiến trình chờ nạp 100% qua console list2
            self.after(0, self.log_info, f"⏳ [Bước 2/4] Đang chờ giả lập LDPlayer Tab: {tab_name} (Index: {tab_index}) load 100%...")
            boot_start = time.time()
            emulator_ready = False

            for check_idx in range(40):
                if self.stop_requested:
                    self.stop_requested = False
                    self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                    return

                # Thu nhỏ liên tục để đảm bảo cửa sổ không bị nảy lên màn hình
                self._minimize_ld_window(tab_index, tab_name)

                if self._is_ld_loaded_100(dnconsole_path, tab_index):
                    emulator_ready = True
                    boot_time = round(time.time() - boot_start, 1)
                    self.after(0, self.log_info, f"✅ Giả lập LDPlayer đã load 100% thành công sau {boot_time}s! Đang tiến hành mở Game...")
                    self._minimize_ld_window(tab_index, tab_name)
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
                self.after(0, self.log_info, "⏳ Đang hoãn 3 giây cho màn hình giả lập ổn định hoàn toàn...")
                if self._sleep_with_stop_check(3.0):
                    self.stop_requested = False
                    self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                    return

            # Bước 3: Dùng ADB để quét danh sách các app/game cài trên giả lập LDPlayer này
            self.after(0, self.log_info, f"🎮 [Bước 3/4] Đang quét danh sách Ứng Dụng trên Tab {tab_name}...")
            
            target_pkg = "com.vtcmobile.gz06"
            self.after(0, self.log_info, f"🎯 Đã phát hiện Package Game: '{target_pkg}'! Đang mở ứng dụng...")

            # Khởi chạy Game qua LDPlayer Native runapp & ADB monkey để luôn mở thành công 100% trên mọi Tab
            self._exec_cmd([dnconsole_path, "runapp", "--index", str(tab_index), "--packagename", target_pkg])
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell monkey -p {target_pkg} -c android.intent.category.LAUNCHER 1"])

            # 4. Kích hoạt "Mắt Thần" OpenCV quét nhận biết Bảng Chọn Máy Chủ qua ảnh mẫu 'login_server.png' / 'login_redorb.png'
            self.after(0, self.log_info, "👁️ [Bước 4/4] Mắt thần OpenCV bắt đầu quét theo dõi màn hình Chọn Máy Chủ TS Origin...")
            
            start_wait = time.time()
            consecutive_matches = 0
            
            # Quét tìm ảnh login_server.png / login_redorb.png với ngưỡng 88%, yêu cầu 3 lần khớp liên tiếp (cách nhau 1 giây) để đảm bảo hình ảnh đã hiện ổn định
            while time.time() - start_wait < 60.0:
                if self.stop_requested:
                    self.stop_requested = False
                    self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                    return

                is_x, is_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_server.png", threshold=0.88)
                if is_x is None:
                    is_x, is_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_redorb.png", threshold=0.88)

                if is_x is not None and is_y is not None:
                    consecutive_matches += 1
                    if consecutive_matches >= 3:
                        elapsed = round(time.time() - start_wait, 1)
                        self.after(0, self.log_info, f"✅ Mắt thần đã xác nhận Bảng Máy Chủ hiển thị đầy đủ ổn định (khớp 3 lần liên tiếp) sau {elapsed}s!")
                        break
                else:
                    consecutive_matches = 0
                time.sleep(1.0)

            # Tạm hoãn 1.0s sau khi nhận diện màn hình Bảng Chọn Máy Chủ
            self.after(0, self.log_info, "⏳ Mắt thần đã nhận diện Bảng Máy Chủ! Tạm hoãn 1.0s nạp hiệu ứng...")
            time.sleep(1.0)

            # Quét kiểm tra file ảnh card_top/login/login_co.png, nếu phát hiện thì nhấp chọn nút login_co.png
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_co.png", threshold=0.75)
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"👁️ Mắt thần phát hiện nút 'card_top/login/login_co.png' tại ({co_x}, {co_y})! Đang nhấp chọn...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {co_x} {co_y}"])
                time.sleep(1.0)

            # Tạo tên file ảnh mẫu linh hoạt theo tên máy chủ được chọn trong Tool (VD: "Điêu Thuyền" -> "card_top/server/server_dieuthuyen.png")
            def to_snake_case(text: str) -> str:
                text = text.replace('Đ', 'D').replace('đ', 'd')
                nfkd = unicodedata.normalize('NFKD', text)
                no_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])
                clean = re.sub(r'[^a-zA-Z0-9]', '_', no_accent).lower()
                return re.sub(r'_+', '_', clean).strip('_')

            server_img_name = f"card_top/server/server_{to_snake_case(server_name).replace('_', '')}.png"

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

                    # 🔍 Kiểm tra xem sau khi nhấp chọn có xuất hiện ảnh thông báo 'card_top/login/login_nkn.png' không
                    nkn_x, nkn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_nkn.png", threshold=0.45)
                    if nkn_x is not None and nkn_y is not None:
                        self.after(0, self.log_info, f"⚠️ Nhấp chọn máy chủ '{server_name}' bị hiện 'card_top/login/login_nkn.png'! Tiếp tục cuộn tìm nhấp lại máy chủ '{server_name}'...")
                        # Không gán found_server = True, tiếp tục cuộn tìm nhấp lại máy chủ này!
                    else:
                        self.after(0, self.log_info, f"✅ Đã kết nối thành công máy chủ '{server_name}' (không bị dính login_nkn.png)!")
                        found_server = True
                        break

                # 🛑 Kiểm tra xem có xuất hiện máy chủ đầu tiên 'card_top/server/server_trieuvan.png' không (chỉ dừng cuộn khi đang tìm máy chủ khác)
                if server_img_name != "card_top/server/server_trieuvan.png":
                    tv_x, tv_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/server/server_trieuvan.png", threshold=0.75)
                    if tv_x is not None and tv_y is not None:
                        self.after(0, self.log_info, "🛑 Mắt thần phát hiện máy chủ đầu tiên 'card_top/server/server_trieuvan.png'! Dừng cuộn xuống và chuẩn bị cuộn ngược lên lại...")
                        break

                # Thực hiện vuốt cuộn XUỐNG chầm chậm
                self.after(0, self.log_info, f"📜 [Cuộn xuống {step + 1}/10] Đang cuộn tìm máy chủ '{server_name}'...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input swipe {scroll_x} {y_start_down} {scroll_x} {y_end_down} {swipe_ms}"])
                time.sleep(1.5)

            # Giai đoạn 2: Nếu chưa kết nối thành công sau 10 lần cuộn xuống, cuộn NGƯỢC LÊN 10 lần để tìm nhấp lại
            if not found_server:
                self.after(0, self.log_info, f"🔄 Chưa vào được máy chủ '{server_name}'! Bắt đầu cuộn NGƯỢC LÊN 10 lần để tìm nhấp lại...")
                
                for step in range(10):
                    if self.stop_requested:
                        self.stop_requested = False
                        self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                        return
                    click_x, click_y = self._find_template_on_screen(dnconsole_path, tab_index, server_img_name, threshold=0.75)

                    if click_x is not None and click_y is not None:
                        self.after(0, self.log_info, f"🎯 Mắt thần tìm thấy máy chủ '{server_name}' tại ({click_x}, {click_y})! Đang nhấp chọn lại...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {click_x} {click_y}"])
                        time.sleep(1.5)

                        # 🔍 Kiểm tra xem sau khi nhấp chọn có xuất hiện 'card_top/login/login_nkn.png' không
                        nkn_x, nkn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_nkn.png", threshold=0.45)
                        if nkn_x is not None and nkn_y is not None:
                            self.after(0, self.log_info, f"⚠️ Nhấp chọn máy chủ '{server_name}' bị hiện 'card_top/login/login_nkn.png'! Tiếp tục cuộn tìm nhấp lại...")
                        else:
                            self.after(0, self.log_info, f"✅ Đã kết nối thành công máy chủ '{server_name}' (không bị dính login_nkn.png)!")
                            found_server = True
                            break

                    # Vuốt cuộn NGƯỢC LÊN từ từ (700ms)
                    self.after(0, self.log_info, f"📜 [Cuộn ngược lên {step + 1}/10] Đang cuộn ngược lên tìm '{server_name}'...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input swipe {scroll_x} {y_start_up} {scroll_x} {y_end_up} {swipe_ms}"])
                    time.sleep(1.5)

            # Giai đoạn 3: Nếu cuộn hết 20 lần mà vẫn không kết nối thành công -> DỪNG LẠI
            if not found_server:
                msg = f"❌ Đã cuộn 20 lần (10 xuống, 10 lên) nhưng máy chủ '{server_name}' vẫn báo 'card_top/login/login_nkn.png' không vào được. Đã dừng lại!"
                self.after(0, self._finish_launch_ts_origin, False, msg)
            else:
                self.after(0, self.log_info, f"🚀 👁️ Đã chọn Máy chủ '{server_name}' trên Tab: {tab_name} (Index: {tab_index})")
                
                # 📌 Bước 5: Hoãn 3 giây khi vào màn hình game
                self.after(0, self.log_info, "⏳ [Màn hình game] Hoãn 3 giây trước khi quét giao diện...")
                if self._sleep_with_stop_check(3.0):
                    self.stop_requested = False
                    self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                    return

                # 📌 Bước 6: Quét Mắt Thần OpenCV & Click nút 'card_top/login/login_x.png' (Nếu khớp nhấp click, không khớp chuyển bước 7)
                self.after(0, self.log_info, "👁️ [Bước 6] Mắt thần đang quét tìm nút 'card_top/login/login_x.png'...")
                x_x, x_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75)
                if x_x is not None and x_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần đã tìm thấy 'card_top/login/login_x.png' tại ({x_x}, {x_y})! Đang nhấp chọn...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {x_x} {x_y}"])
                    time.sleep(1.0)
                else:
                    self.after(0, self.log_info, "ℹ️ Không phát hiện nút 'card_top/login/login_x.png' -> Chuyển xuống Bước 7.")

                if self.stop_requested:
                    self.stop_requested = False
                    self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                    return

                # 📌 Bước 7: Quét Mắt Thần OpenCV & Click nút 'card_top/login/login_auto.png'
                self.after(0, self.log_info, "👁️ [Bước 7] Mắt thần đang quét tìm nút 'card_top/login/login_auto.png'...")
                auto_x, auto_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_auto.png", threshold=0.75)
                if auto_x is not None and auto_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần đã tìm thấy 'card_top/login/login_auto.png' tại ({auto_x}, {auto_y})! Đang nhấp chọn...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {auto_x} {auto_y}"])
                    time.sleep(1.0)
                else:
                    self.after(0, self.log_info, "ℹ️ Không tìm thấy ảnh 'card_top/login/login_auto.png' trên màn hình game.")

                # 📌 Bước 8: Hoàn tất quá trình mở game & tự động thu nhỏ cửa sổ xuống Taskbar
                self._minimize_ld_window(tab_index, tab_name)
                msg = f"✅ [Hoàn thành] Đã vào game & hoàn tất quy trình khởi chạy trên Tab: {tab_name} (Index: {tab_index})"
                self.after(0, self._finish_launch_ts_origin, True, msg)

        except Exception as e:
            self.after(0, self._finish_launch_ts_origin, False, f"Lỗi khởi chạy game: {str(e)}")

    def _finish_launch_ts_origin(self, success: bool, message: str):
        """Hoàn tất quá trình mở game, trả lại trạng thái nút bấm Game"""
        self.btn_enter_game.configure(state="normal", text="Game")
        if success:
            self.log_info(message)
        else:
            self.log_error(message)

    # ---- HÀM XỬ LÝ NÚT CHẠY (THỰC THI 2 CARD THEO THỨ TỰ: 1. BOSS TG -> 2. PHỤ BẢN ĐƠN/ĐỘI) ----
    def xu_ly_nut_chay(self):
        """Khi bấm nút Chạy: Thực thi các ô check trong 2 Card (Boss TG, Phụ Bản Đơn/Đội) nếu công tắc đang ON"""
        tab_name, tab_index = self._get_selected_ld_info()
        if tab_index is None:
            self.log_error("Vui lòng chọn một Tab LDPlayer trước khi bấm Chạy!")
            return

        has_active_switch = self.var_switch_A.get() or self.var_switch_B.get()
        if not has_active_switch:
            self.log_error("Vui lòng bật công tắc ON cho ít nhất 1 trong 2 Card (Boss TG, Phụ Bản Đơn/Đội) trước khi bấm Chạy!")
            return

        self.stop_requested = False
        self.btn_run.configure(state="disabled", text="Đang chạy...")
        self.log_info(f"▶️ [NÚT CHẠY] Bắt đầu thực thi các Card đang bật ON theo thứ tự trên Tab: {tab_name} (Index: {tab_index})...")

        threading.Thread(target=self._worker_run_3_cards, args=(tab_name, tab_index), daemon=True).start()

    def _worker_run_3_cards(self, tab_name: str, tab_index: str):
        """Worker thread thực thi thứ tự 2 Card: 1. Boss Thế Giới -> 2. Phụ Bản Đơn/Đội"""
        try:
            dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")

            if not os.path.exists(dnconsole_path):
                self.after(0, self._finish_run_3_cards, False, f"Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
                return

            # 📌 1/2: CARD BOSS THẾ GIỚI (Card A)
            if self.var_switch_A.get() and not self.stop_requested:
                self.after(0, self.log_info, f"📌 [1/2] Đang thực thi Card Boss Thế Giới trên Tab: {tab_name}...")
                self._execute_card_A_boss_tg(dnconsole_path, tab_name, tab_index)
                
                if not self.stop_requested:
                    if not self.var_switch_A.get():
                        self.after(0, self.log_info, "🛑 [1/2] Công tắc Card Boss Thế Giới gạt về OFF ➔ Đã dừng thao tác Card này!")
                    else:
                        # Thao tác xong các ô check -> Tự động nhả công tắc C về OFF
                        self.after(0, lambda: self.var_switch_A.set(False))
                        self.after(0, self.save_config)
                        self.after(0, self.log_info, "✅ [1/2] Đã hoàn thành Card Boss Thế Giới ➔ Tự động nhả công tắc C về OFF!")

                    # Nếu có Card tiếp theo đang mở công tắc -> Hoãn 5 giây trước khi chuyển sang Card tiếp theo
                    if self.var_switch_B.get() and not self.stop_requested:
                        self.after(0, self.log_info, "⏳ Hoãn 5 giây trước khi chuyển sang Card tiếp theo...")
                        time.sleep(5.0)

            # 📌 2/2: CARD PHỤ BẢN ĐƠN / ĐỘI (Card B)
            if self.var_switch_B.get() and not self.stop_requested:
                self.after(0, self.log_info, f"📌 [2/2] Đang thực thi Card Phụ Bản Đơn / Đội trên Tab: {tab_name}...")
                self._execute_card_B_phu_ban_doi(dnconsole_path, tab_name, tab_index)
                
                if not self.stop_requested:
                    if not self.var_switch_B.get():
                        self.after(0, self.log_info, "🛑 [2/2] Công tắc Card Phụ Bản Đơn / Đội gạt về OFF ➔ Đã dừng thao tác Card này!")
                    else:
                        # Thao tác xong các ô check -> Tự động nhả công tắc E về OFF
                        self.after(0, lambda: self.var_switch_B.set(False))
                        self.after(0, self._update_card_E_visibility)
                        self.after(0, self.save_config)
                        self.after(0, self.log_info, "✅ [2/2] Đã hoàn thành Card Phụ Bản Đơn / Đội ➔ Tự động nhả công tắc E về OFF!")

            if self.stop_requested:
                self.after(0, self._finish_run_3_cards, False, "🛑 Tiến trình Nút Chạy đã dừng theo yêu cầu!")
            else:
                self.after(0, self._finish_run_3_cards, True, f"🎉 [HOÀN THÀNH] Nút Chạy đã hoàn tất các Card hoạt động theo thứ tự trên Tab: {tab_name}")

        except Exception as e:
            self.after(0, self._finish_run_3_cards, False, f"Lỗi tiến trình Nút Chạy: {str(e)}")

    def _finish_run_3_cards(self, success: bool, message: str):
        """Hoàn tất tiến trình nút Run, phục hồi nút Run sáng lên"""
        if hasattr(self, 'btn_run'):
            self.btn_run.configure(state="normal", text="Run")
        if success:
            self.log_info(message)
        else:
            self.log_error(message)

    def _sleep_with_stop_check(self, seconds: float) -> bool:
        """Tạm dừng ngủ ngầm nhưng kiểm tra cờ Dừng khẩn cấp liên tục mỗi 0.1s. Trả về True nếu bấm Dừng."""
        start = time.time()
        while time.time() - start < seconds:
            if self.stop_requested:
                return True
            time.sleep(0.1)
        return False

    def dung_tat_ca_hoat_dong(self):
        """Nút Dừng tổng: Ngắt lập tức tất cả các card có trong tool & tiến trình mở game TS Origin"""
        self.stop_requested = True
        for prefix in ["A", "B", "C", "D"]:
            switch_attr = f"var_switch_{prefix}"
            if hasattr(self, switch_attr):
                getattr(self, switch_attr).set(False)
            pause_attr = f"var_pause_{prefix}"
            if hasattr(self, pause_attr):
                getattr(self, pause_attr).set(False)

        self._update_card_E_visibility()
        self.save_config()

        if hasattr(self, 'btn_run'):
            self.btn_run.configure(state="normal", text="Run")
        if hasattr(self, 'btn_enter_game'):
            self.btn_enter_game.configure(state="normal", text="Game")

        self.after(0, self.log_info, "🛑 [DỪNG KHẨN CẤP] Đã bấm nút Dừng ➔ Dừng lập tức tiến trình TS Origin & TOÀN BỘ các Card trong tool!")



    def _should_stop_card_C(self) -> bool:
        """Kiểm tra điều kiện dừng cho Card 1 Dị Giới (bấm Dừng tổng hoặc gạt công tắc B về OFF)"""
        return self.stop_requested or not self.var_switch_C.get()

    def _should_stop_card_B(self) -> bool:
        """Kiểm tra điều kiện dừng cho Card 2 Phụ Bản Đơn/Đội (bấm Dừng tổng hoặc gạt công tắc E về OFF)"""
        return self.stop_requested or not self.var_switch_B.get()

    def _should_stop_card_A(self) -> bool:
        """Kiểm tra điều kiện dừng cho Card 4 Boss Thế Giới (bấm Dừng tổng hoặc gạt công tắc C về OFF)"""
        return self.stop_requested or not self.var_switch_A.get()

    def _should_stop_card_D(self) -> bool:
        """Kiểm tra điều kiện dừng / tạm dừng cho Card 5 40 NPC (độc lập với nút Dừng Khởi Động)"""
        if self.stop_requested or not self.var_switch_D.get():
            return True
        if hasattr(self, 'var_pause_D') and self.var_pause_D.get():
            self.after(0, self.log_info, "⏸️ [40 NPC] Ô Tạm Dừng đang tích ➔ Tạm dừng tiến trình (nhả ô Tạm Dừng để chạy tiếp)...")
            while self.var_pause_D.get() and self.var_switch_D.get() and not self.stop_requested:
                time.sleep(0.5)
            if self.var_switch_D.get() and not self.stop_requested:
                self.after(0, self.log_info, "▶️ [40 NPC] Đã nhả ô Tạm Dừng ➔ Khôi phục chạy tiếp 40 NPC!")
        return self.stop_requested or not self.var_switch_D.get()

    # =========================================================================
    # 🔓 [ĐÃ MỞ KHÓA TOÀN DIỆN - SẴN SÀNG SỬ DỤNG]: CARD C (DỊ GIỚI ĐÊM)
    # =========================================================================
    def _run_safezone_di_gioi(self, dnconsole_path: str, tab_index: str, px_x: int, px_y: int):
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

    def _execute_card_C_di_gioi(self, dnconsole_path: str, tab_name: str, tab_index: str):
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

    # =========================================================================
    # 🔓 [ĐÃ MỞ KHÓA TOÀN DIỆN - SẴN SÀNG SỬ DỤNG]: CARD B (PHỤ BẢN ĐƠN / ĐỘI)
    # =========================================================================
    def _execute_card_B_phu_ban_doi(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """Thực thi Card 2: PHỤ BẢN ĐƠN / ĐỘI (E)"""
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
                self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 1] Quét tìm ảnh 'b_doi.png' trong folder 'card_b'...")
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

                # 1. Vào trận: Quét chờ xuất hiện nút Bắt Đầu 'card_b/b_batdau.png' (85%), sau đó tap liên tục 0.5s cho đến khi mất ảnh
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

    # =========================================================================
    # 🔓 [ĐÃ MỞ KHÓA TOÀN DIỆN - SẴN SÀNG SỬ DỤNG]: CARD E (QUẢN LÝ TỔ ĐỘI)
    # =========================================================================
    def _should_stop_card_E(self) -> bool:
        """
        Kiểm tra điều kiện dừng & tạm dừng cho Card E (Tổ Đội) (G):
        - Ngắt ngay nếu bấm Dừng Tổng hoặc công tắc Card đang chạy (var_switch_B/D) bị tắt.
        - Tạm dừng (vòng lặp chờ nhả ô) nếu ô Tạm Dừng của Card đang chạy (var_pause_D) đang được tích.
        """
        if self.stop_requested:
            return True

        # Kiểm tra nếu ô Tạm Dừng của Card đang liên quan (D) đang tích
        def is_any_pause_active() -> bool:
            if hasattr(self, 'var_switch_D') and self.var_switch_D.get() and hasattr(self, 'var_pause_D') and self.var_pause_D.get():
                return True
            return False

        def is_no_active_switch_on() -> bool:
            e_active = hasattr(self, 'var_switch_B') and hasattr(self, 'var_B_doi') and self.var_B_doi.get() and self.var_switch_B.get()
            d_active = hasattr(self, 'var_switch_D') and hasattr(self, 'var_D2') and self.var_D2.get() and self.var_switch_D.get()
            return not (e_active or d_active)

        # Vòng lặp tạm dừng thông minh
        if is_any_pause_active():
            self.after(0, self.log_info, "⏸️ [CARD TỔ ĐỘI] Phát hiện ô Tạm Dừng của Card đang chạy được tích ➔ Tạm dừng hoạt động Tổ Đội (Chờ nhả ô Tạm Dừng)...")
            while is_any_pause_active() and not self.stop_requested:
                if is_no_active_switch_on():
                    return True
                time.sleep(0.5)
            self.after(0, self.log_info, "▶️ [CARD TỔ ĐỘI] Ô Tạm Dừng đã được nhả ➔ Khôi phục chạy tiếp hoạt động Tổ Đội!")

        return is_no_active_switch_on()

    def _run_card_E_action_1(self, dnconsole_path: str, tab_index: str, list_B: list):
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

    def _run_card_E_action_2(self, dnconsole_path: str, tab_index: str, list_B: list):
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

    def _execute_card_E_for_mode(self, dnconsole_path: str, tab_name: str, tab_index: str, mode: int):
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

    # =========================================================================
    # 🔓 [ĐÃ MỞ KHÓA TOÀN DIỆN - SẴN SÀNG SỬ DỤNG]: CARD A (BOSS THẾ GIỚI)
    # =========================================================================
    def _run_boss_safezone(self, dnconsole_path: str, tab_index: str):
        """PHẦN 1: QUY TRÌNH VỀ KHU AN TOÀN CỦA BOSS THẾ GIỚI"""
        if self._should_stop_card_A(): return
        self.after(0, self.log_info, "👁️ Quét tìm nút 'card_top/login/login_x.png' (ROI 990,50,1165,200) để đóng bảng quảng cáo/thông báo...")
        lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(990, 50, 1165, 200))
        if lx_x is not None and lx_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_top/login/login_x.png' tại ({lx_x}, {lx_y})! Click chọn ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
            time.sleep(0.4)

        if self._should_stop_card_A(): return
        self.after(0, self.log_info, "👁️ [Boss Thế Giới - Bước 1.1] Quét tìm nút Vị Trí 'card_c/c_vitri.png' (85%, ROI 735,405,1280,720)...")
        v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
        if v_x is not None and v_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_vitri.png' tại ({v_x}, {v_y})! Tap click trực tiếp ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "👉 Chưa thấy 'card_c/c_vitri.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
            if self._should_stop_card_A(): return
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút 'card_c/c_vitri.png' tại ({v_x}, {v_y})! Tap click trực tiếp ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'card_c/c_vitri.png' trong bảng menu.")

        if self._should_stop_card_A(): return
        self.after(0, self.log_info, "👉 [Boss Thế Giới - Bước 1.2] Click liên tục (435, 250) mỗi 0.5s cho đến khi xuất hiện nút Có 'card_a/a_co.png' (85%, ROI 275,540,1150,670)...")
        while not self._should_stop_card_A():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_co.png", threshold=0.85, region=(275, 540, 1150, 670))
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút Có 'card_a/a_co.png' tại ({co_x}, {co_y})! Dừng click (435, 250).")
                break
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 435 250"])
            time.sleep(0.5)

        if self._should_stop_card_A(): return
        self.after(0, self.log_info, "👁️ [Boss Thế Giới - Bước 1.3] Click liên tục nút Có 'card_a/a_co.png' (0.5s mỗi lần) cho tới khi hết ảnh...")
        while not self._should_stop_card_A():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_co.png", threshold=0.85, region=(275, 540, 1150, 670))
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút Có 'card_a/a_co.png' tại ({co_x}, {co_y}) ➔ Click vào vị trí ảnh...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {co_x} {co_y}"])
                time.sleep(0.5)
            else:
                self.after(0, self.log_info, "ℹ️ Không còn thấy ảnh nút Có 'card_a/a_co.png' ➔ Hoàn thành Bước 1 (Về Khu An Toàn)!")
                break

        if self._should_stop_card_A(): return
        self.after(0, self.log_info, "⏳ [Boss Thế Giới - Bước 1.4] Hoãn 3.0s trước khi quét kiểm tra lại nút 'card_c/c_vitri.png'...")
        time.sleep(3.0)

        if self._should_stop_card_A(): return
        self.after(0, self.log_info, "👁️ [Boss Thế Giới - Bước 1.4] Quét kiểm tra lại nút 'card_c/c_vitri.png' (85%, ROI 735,405,1280,720)...")
        v_check_x, v_check_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
        if v_check_x is not None and v_check_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_vitri.png' vẫn còn tại ({v_check_x}, {v_check_y}) ➔ Click (1213, 648) để thu gọn menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "ℹ️ Không thấy nút 'card_c/c_vitri.png' ➔ Bỏ qua thu gọn menu.")

    def _run_boss_pre_move(self, dnconsole_path: str, tab_index: str) -> bool:
        """PHẦN THÊM: THAO TÁC TRƯỚC PHẦN 3 DI CHUYỂN CỦA BOSS THẾ GIỚI. Trả về True nếu tìm thấy a_dichuyen.png (bỏ qua di chuyển)"""
        if self._should_stop_card_A(): return False

        self.after(0, self.log_info, "👁️ [Boss - Thao Tác Trước Di Chuyển] 1. Quét nút Sự Kiện 'card_a/a_sukien.png' (ROI 735,405,1280,720)...")
        sk_x, sk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_sukien.png", threshold=0.85, region=(735, 405, 1280, 720))
        if sk_x is not None and sk_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_a/a_sukien.png' tại ({sk_x}, {sk_y})! Tap click chọn ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {sk_x} {sk_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "👉 Chưa thấy 'card_a/a_sukien.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
            if self._should_stop_card_A(): return False
            sk_x, sk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_sukien.png", threshold=0.85, region=(735, 405, 1280, 720))
            if sk_x is not None and sk_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_a/a_sukien.png' tại ({sk_x}, {sk_y})! Tap click chọn ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {sk_x} {sk_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'card_a/a_sukien.png' trong bảng menu.")

        if self._should_stop_card_A(): return False
        self.after(0, self.log_info, "👁️ [Boss - Thao Tác Trước Di Chuyển] 2. Quét nút Boss TG 'card_a/a_skboss.png' (ROI 155,95,305,625)...")
        skb_x, skb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_skboss.png", threshold=0.85, region=(155, 95, 305, 625))
        if skb_x is not None and skb_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_a/a_skboss.png' tại ({skb_x}, {skb_y})! Tap click chọn ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {skb_x} {skb_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "ℹ️ Không tìm thấy 'card_a/a_skboss.png' ➔ Bỏ qua.")

        if self._should_stop_card_A(): return False
        self.after(0, self.log_info, "👁️ [Boss - Thao Tác Trước Di Chuyển] 3. Quét nút Dịch Chuyển 'card_a/a_dichuyen.png' (60%, ROI 895,435,1065,535)...")
        dc_x, dc_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_dichuyen.png", threshold=0.60, region=(895, 435, 1065, 535))
        if dc_x is not None and dc_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_a/a_dichuyen.png' tại ({dc_x}, {dc_y})! Tap click ➔ Hoãn 3.0s ➔ Chuyển thẳng qua PHẦN 4: ĐÁNH BOSS...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {dc_x} {dc_y}"])
            time.sleep(3.0)
            return True
        else:
            self.after(0, self.log_info, "ℹ️ Không thấy 'card_a/a_dichuyen.png' (hoặc nút bị Tối/Mờ) ➔ Quét tìm nút 'card_top/login/login_x.png' (75%, ROI 990,50,1165,200)...")
            lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(990, 50, 1165, 200))
            if lx_x is not None and lx_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'card_top/login/login_x.png' tại ({lx_x}, {lx_y})! Tap click đóng cửa sổ ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                time.sleep(0.4)

            if self._should_stop_card_A(): return False
            self.after(0, self.log_info, "👁️ Quét tìm nút Vị Trí 'card_c/c_vitri.png' (85%, ROI 735,405,1280,720)...")
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút 'card_c/c_vitri.png' tại ({v_x}, {v_y}) ➔ Click nút xanh lá góc dưới phải (1213, 648) ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "ℹ️ Chưa thấy nút 'card_c/c_vitri.png' ➔ Bỏ qua.")

            self.after(0, self.log_info, "ℹ️ Chuyển qua PHẦN 3: DI CHUYỂN.")
            return False

    def _run_boss_move_manual(self, dnconsole_path: str, tab_index: str):
        """Giai Đoạn 3: Di chuyển bộ D-Pad (_run_boss_move_manual)"""
        if self._should_stop_card_A(): return
        self.after(0, self.log_info, "🚀 [Boss - Giai Đoạn 3] Bắt đầu Di chuyển bộ D-Pad...")

        # Bước 3.1: Kéo Joystick hướng Chéo Phải - Trên (UP_RIGHT / W+D) liên tục trong 3.0s (640,360 ➔ 890,110). Nghỉ 0.3s.
        if self._should_stop_card_A(): return
        self.after(0, self.log_info, "🕹️ [Boss - Bước 3.1] Kéo Joystick hướng Chéo Phải - Trên (UP_RIGHT / W+D) liên tục trong 3.0s (640,360 ➔ 890,110)...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 640 360 890 110 3000"])
        if self._should_stop_card_A(): return
        time.sleep(0.3)

        # Bước 3.2: Kéo Joystick hướng Phải (RIGHT / D) liên tục trong 5.5s (640,360 ➔ 890,360). Nghỉ 0.3s.
        if self._should_stop_card_A(): return
        self.after(0, self.log_info, "🕹️ [Boss - Bước 3.2] Kéo Joystick hướng Phải (RIGHT / D) liên tục trong 5.5s (640,360 ➔ 890,360)...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 640 360 890 360 5500"])
        if self._should_stop_card_A(): return
        time.sleep(0.3)

    def _run_boss_workflow(self, dnconsole_path: str, tab_name: str, tab_index: str, max_turns: int = 5, skip_move: bool = False):
        """QUY TRÌNH THỰC THI THAO TÁC ĐÁNH BOSS THẾ GIỚI (PHẦN 1 -> PHẦN THÊM -> PHẦN 3 -> PHẦN 4 với số lượt max_turns)"""
        if self._should_stop_card_A(): return

        if not skip_move:
            self._run_boss_safezone(dnconsole_path, tab_index)
            skip_di_chuyen = self._run_boss_pre_move(dnconsole_path, tab_index)

            if not skip_di_chuyen:
                self._run_boss_move_manual(dnconsole_path, tab_index)
        else:
            self.after(0, self.log_info, "ℹ️ [Boss] Đã ở vị trí Boss / Đã hoàn thành di chuyển ➔ Tiến thẳng vào quy trình Đánh Boss...")

        # 📌 PHẦN 4: ĐÁNH BOSS THẾ GIỚI - QUY TRÌNH "BOSS"
        self.after(0, self.log_info, f"🔄 [Boss] Bắt đầu thực thi {max_turns} lượt đánh...")
        for turn in range(1, max_turns + 1):
            if self._should_stop_card_A(): return
            self.after(0, self.log_info, f"🔄 [Boss - Lượt {turn}/{max_turns}] Đang thực thi lượt {turn}...")

            # [Bước 2 của Lượt] - Tìm Boss:
            if self._should_stop_card_A(): return
            self.after(0, self.log_info, f"👁️ [Lượt {turn} - Bước 2] Click liên tục (1240, 605) tìm ảnh Boss 'card_a/a_boss.png' (85%, ROI 735,405,1280,720)...")
            boss_x, boss_y = None, None
            for click_idx in range(20):
                if self._should_stop_card_A(): break
                boss_x, boss_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_boss.png", threshold=0.85, region=(735, 405, 1280, 720))
                if boss_x is not None and boss_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần phát hiện ảnh 'card_a/a_boss.png' tại ({boss_x}, {boss_y})! Dừng click (1240, 605).")
                    break
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 605"])
                time.sleep(0.4)

            if self._should_stop_card_A(): return
            if boss_x is None or boss_y is None:
                self.after(0, self.log_info, f"⚠️ [Lượt {turn} - Bước 2] Sau 20 lần click không thấy 'card_a/a_boss.png' ➔ Chạy lại PHẦN 1 (SAFE ZONE) & PHẦN THÊM...")
                self._run_boss_safezone(dnconsole_path, tab_index)
                self._run_boss_pre_move(dnconsole_path, tab_index)

            if self._should_stop_card_A(): return

            # [Bước 3 của Lượt] - Đặt vị trí đánh:
            self.after(0, self.log_info, f"👉 [Lượt {turn} - Bước 3] Click (1160, 570) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1160 570"])
            time.sleep(0.4)

            if self._should_stop_card_A(): return
            hl_x, hl_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_hetluot.png", threshold=0.85, region=(275, 540, 1150, 670))
            if hl_x is not None and hl_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_a/a_hetluot.png' tại ({hl_x}, {hl_y})! Đã HẾT LƯỢT ➔ Tap vào vị trí ảnh ➔ Hoãn 0.4s & Dừng quy trình đánh Boss.")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {hl_x} {hl_y}"])
                time.sleep(0.4)
                break
            else:
                self.after(0, self.log_info, "ℹ️ Không thấy 'card_a/a_hetluot.png' ➔ Tap (500, 635) ➔ Hoãn 0.4s...")
                if self._should_stop_card_A(): return
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 500 635"])
                time.sleep(0.4)

            # [Bước 4 của Lượt] - Bắt đầu chiến đấu & Quét card_f/f_vaotran.png:
            if self._should_stop_card_A(): return
            self.after(0, self.log_info, f"⏳ [Lượt {turn}/{max_turns} - Bước 4] Hoãn 2.0s trước khi click vào trận (185, 145)...")
            for _ in range(2):
                if self._should_stop_card_A(): return
                time.sleep(1.0)

            if self._should_stop_card_A(): return
            self.after(0, self.log_info, f"👉 [Lượt {turn}/{max_turns} - Bước 4] Click (185, 145) vào trận ➔ Hoãn 60s trước khi quét...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 185 145"])
            for _ in range(60):
                if self._should_stop_card_A(): return
                time.sleep(1.0)

            if self._should_stop_card_A(): return
            self.after(0, self.log_info, f"👁️ [Lượt {turn}/{max_turns} - Bước 4] Đã hoãn 60s ➔ Quét tìm ảnh 'card_f/f_vaotran.png' (80%, ROI: 1215, 0, 1280, 45) mỗi 0.5s cho đến khi xuất hiện...")
            while not self._should_stop_card_A():
                vt_x, vt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_vaotran.png", threshold=0.80, region=(1215, 0, 1280, 45))
                if vt_x is not None and vt_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_f/f_vaotran.png' tại ({vt_x}, {vt_y})! Hoàn thành lượt đánh {turn}.")
                    break
                time.sleep(0.5)

    def _run_boss_ve_process(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """THAO TÁC TÌM & DÙNG VÉ BOSS (CHỈ CHẠY SAU 12H TRƯA, TỰ ĐỘNG LẶP CHO TỚI KHÔNG CÒN VÉ)"""
        ve_count = 0
        while not self._should_stop_card_A():
            ve_count += 1
            self.after(0, self.log_info, f"🎫 [Vé Boss - Lượt {ve_count}] Bắt đầu quy trình kiểm tra & dùng Vé Boss...")

            # 1. Quét tap login_x.png (75%, ROI 990,50,1165,200) đóng thông báo
            if self._should_stop_card_A(): return
            self.after(0, self.log_info, "👁️ [Vé - Bước 1] Quét tìm nút 'card_top/login/login_x.png' (ROI 990,50,1165,200)...")
            lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(990, 50, 1165, 200))
            if lx_x is not None and lx_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_top/login/login_x.png' tại ({lx_x}, {lx_y})! Click chọn ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                time.sleep(0.4)

            # 2. Quét tap nút Túi card_a/a_tui.png (85%, ROI 735,405,1280,720) ➔ Hoãn 0.4s
            if self._should_stop_card_A(): return
            self.after(0, self.log_info, "👁️ [Vé - Bước 2] Quét nút Túi 'card_a/a_tui.png' (85%, ROI 735,405,1280,720)...")
            tui_x, tui_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_tui.png", threshold=0.85, region=(735, 405, 1280, 720))
            if tui_x is not None and tui_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện Túi tại ({tui_x}, {tui_y})! Tap click ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {tui_x} {tui_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa thấy ảnh 'card_a/a_tui.png' trên màn hình.")

            # 3. Cuộn tìm Vé Boss trong Túi:
            # - Vuốt xuống: Swipe (920, 480 ➔ 920, 230 800ms) tối đa 5 lần (dừng nếu tìm thấy a_veboss.png hoặc phát hiện a_khoa.png).
            # - Vuốt ngược lên: Swipe (920, 230 ➔ 920, 480 800ms) tối đa 5 lần đến khi thấy Vé Boss a_veboss.png.
            if self._should_stop_card_A(): return
            self.after(0, self.log_info, "📜 [Vé - Bước 3] Cuộn tìm ảnh Vé Boss 'card_a/a_veboss.png' (70%, ROI 745,230,1095,580)...")
            veboss_x, veboss_y = None, None

            for swipe_down_cnt in range(5):
                if self._should_stop_card_A(): break
                veboss_x, veboss_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_veboss.png", threshold=0.70, region=(745, 230, 1095, 580))
                if veboss_x is not None and veboss_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện 'card_a/a_veboss.png' tại ({veboss_x}, {veboss_y})!")
                    break
                khoa_x, khoa_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_khoa.png", threshold=0.85, region=(745, 230, 1095, 580))
                if khoa_x is not None and khoa_y is not None:
                    self.after(0, self.log_info, f"🔒 Phát hiện 'card_a/a_khoa.png' tại ({khoa_x}, {khoa_y}) nhưng chưa thấy Vé Boss ➔ Dừng cuộn xuống, chuyển sang cuộn ngược lên...")
                    break
                self.after(0, self.log_info, f"📜 [Vé - Vuốt xuống {swipe_down_cnt+1}/5] Swipe (920, 480 ➔ 920, 230 800ms)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 920 480 920 230 800"])
                time.sleep(1.0)

            if veboss_x is None or veboss_y is None:
                self.after(0, self.log_info, "📜 [Vé - Cuộn ngược lên] Bắt đầu cuộn ngược lên tìm Vé Boss...")
                for swipe_up_cnt in range(5):
                    if self._should_stop_card_A(): break
                    veboss_x, veboss_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_veboss.png", threshold=0.70, region=(745, 230, 1095, 580))
                    if veboss_x is not None and veboss_y is not None:
                        self.after(0, self.log_info, f"🎯 Phát hiện 'card_a/a_veboss.png' tại ({veboss_x}, {veboss_y})!")
                        break
                    self.after(0, self.log_info, f"📜 [Vé - Vuốt ngược lên {swipe_up_cnt+1}/5] Swipe (920, 330 ➔ 920, 580 1200ms)...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 920 330 920 580 1200"])
                    time.sleep(1.0)

            # Nếu không tìm thấy vé ➔ Đóng túi và kết thúc vòng lặp dùng vé
            if veboss_x is None or veboss_y is None:
                self.after(0, self.log_info, "ℹ️ [Vé] Đã cuộn tối đa số lần trong túi và không còn phát hiện Vé Boss ➔ Tap 'login_x.png' đóng Túi ➔ Hoàn thành quy trình Vé Boss!")
                if self._should_stop_card_A(): return
                lx_x2, lx_y2 = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(990, 50, 1165, 200))
                if lx_x2 is not None and lx_y2 is not None:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x2} {lx_y2}"])
                    time.sleep(0.4)
                break

            # 4. Tap ảnh Vé Boss a_veboss.png ➔ Tap (755, 460) ➔ Tap (320, 25) (Hoãn 0.4s mỗi tap).
            if self._should_stop_card_A(): return
            self.after(0, self.log_info, f"👉 Tap chọn Vé Boss tại ({veboss_x}, {veboss_y}) ➔ Tap (755, 460) ➔ Tap (320, 25) (Hoãn 0.4s)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {veboss_x} {veboss_y}"])
            time.sleep(0.4)
            if self._should_stop_card_A(): return
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 755 460"])
            time.sleep(0.4)
            if self._should_stop_card_A(): return
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 320 25"])
            time.sleep(0.4)

            # 5. Quét tap login_x.png đóng bảng Túi ➔ Hoãn 0.4s.
            if self._should_stop_card_A(): return
            lx_x2, lx_y2 = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(990, 50, 1165, 200))
            if lx_x2 is not None and lx_y2 is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_top/login/login_x.png' tại ({lx_x2}, {lx_y2})! Tap click đóng Túi ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x2} {lx_y2}"])
                time.sleep(0.4)

            # Thực thi đánh Boss bằng vé:
            # Lượt vé 1: Chạy đầy đủ quy trình di chuyển ➔ Đánh 1 lượt Boss.
            # Từ lượt vé 2 trở đi: Bỏ qua di chuyển, tiến thẳng vào trận đánh Boss 1 lượt.
            skip_move = (ve_count >= 2)
            if skip_move:
                self.after(0, self.log_info, f"🚀 [Vé - Lượt {ve_count}] Bỏ qua di chuyển (từ lượt 2 trở đi) ➔ Tiến thẳng vào trận đánh Boss 1 lượt...")
            else:
                self.after(0, self.log_info, f"🚀 [Vé - Lượt {ve_count}] Lượt vé thứ 1 ➔ Chạy đầy đủ quy trình di chuyển & đánh 1 lượt Boss...")

            self._run_boss_workflow(dnconsole_path, tab_name, tab_index, max_turns=1, skip_move=skip_move)

    def _execute_card_A_boss_tg(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """Thực thi Card A: BOSS THẾ GIỚI"""
        if self._should_stop_card_A():
            self.after(0, self.log_info, "ℹ️ [CARD BOSS THẾ GIỚI] Công tắc ON/OFF đang TẮT -> Bỏ qua.")
            return

        if not self.var_A1.get():
            self.after(0, self.log_info, "ℹ️ [CARD BOSS THẾ GIỚI] Ô 'Boss' KHÔNG được tích -> Bỏ qua.")
            self.after(0, lambda: self.var_switch_A.set(False))
            self.after(0, self.save_config)
            return

        selected_char = self.combo_A_char.get() if hasattr(self, 'combo_A_char') else "Xuất Chiến"

        # =========================================================================
        # 📌 1. VỀ KHU AN TOÀN (_run_boss_safezone)
        # =========================================================================
        if self._should_stop_card_A(): return
        self._run_boss_safezone(dnconsole_path, tab_index)

        # =========================================================================
        # 📌 2. CHUYỂN ĐỔI VỊ TRÍ NHÂN VẬT
        # =========================================================================
        if self._should_stop_card_A(): return
        self.after(0, self.log_info, f"⚙️ [Boss Thế Giới - Bước 2] Vị trí nhân vật: '{selected_char}'")

        if selected_char == "Xuất Chiến":
            self.after(0, self.log_info, "ℹ️ Vị trí 'Xuất Chiến': Bỏ qua Bước 2, chuyển thẳng xuống Phần Tiếp Theo.")
        else:
            if self._should_stop_card_A(): return
            self.after(0, self.log_info, "⏳ [Boss Thế Giới - Bước 2] Nghỉ 0.4s trước khi khởi động...")
            time.sleep(0.4)

            if self._should_stop_card_A(): return
            self.after(0, self.log_info, "👁️ [Boss Thế Giới - Bước 2] Quét tìm ảnh 'card_b/b_doi.png' (85%, ROI 735,405,1280,720)...")
            b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(735, 405, 1280, 720))
            if b_doi_x is not None and b_doi_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "👉 Chưa thấy 'b_doi.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(0.4)
                if self._should_stop_card_A(): return
                b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(735, 405, 1280, 720))
                if b_doi_x is not None and b_doi_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                    time.sleep(0.4)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'card_b/b_doi.png' trong bảng menu.")

            if selected_char == "Vị Trí 1":
                self.after(0, self.log_info, "👉 [Vị Trí 1] Click (560, 340) ➔ (560, 255) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.5)
            elif selected_char == "Vị Trí 2":
                self.after(0, self.log_info, "👉 [Vị Trí 2] Click (560, 255) ➔ (560, 340) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.5)
            elif selected_char == "Vị Trí 3":
                self.after(0, self.log_info, "👉 [Vị Trí 3] Click (560, 255) ➔ (560, 430) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 430"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.5)
            elif selected_char == "Vị Trí 4":
                self.after(0, self.log_info, "👉 [Vị Trí 4] Click (560, 255) ➔ (560, 520) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.5)

            if self._should_stop_card_A(): return
            self.after(0, self.log_info, "👉 [Boss Thế Giới - Bước 2] Click (1213, 648) đóng menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)

        # =========================================================================
        # 📌 3. SỰ KIỆN BOSS & DI CHUYỂN BỘ
        # =========================================================================
        if self._should_stop_card_A(): return
        skip_di_chuyen = self._run_boss_pre_move(dnconsole_path, tab_index)
        if not skip_di_chuyen:
            self._run_boss_move_manual(dnconsole_path, tab_index)

        # =========================================================================
        # 📌 4. ĐÁNH BOSS 5 LƯỢT CHÍNH (Khi ô Boss được tích)
        # =========================================================================
        if self._should_stop_card_A(): return
        self.after(0, self.log_info, "🚀 [Boss Thế Giới] Khởi chạy quy trình Boss (5 lượt chính)...")
        self._run_boss_workflow(dnconsole_path, tab_name, tab_index, max_turns=5, skip_move=True)

        # =========================================================================
        # 📌 5. THỰC THI VÉ BOSS (CHỈ CHẠY SAU 12H TRƯA)
        # =========================================================================
        if self._should_stop_card_A(): return
        now_dt = datetime.now()
        if now_dt.hour < 12:
            self.after(0, self.log_info, f"ℹ️ [Vé Boss] Hiện tại là {now_dt.strftime('%H:%M:%S')} (trước 12h trưa) ➔ Thao tác Vé Boss chỉ hoạt động sau 12h trưa ➔ Bỏ qua.")
        else:
            self.after(0, self.log_info, "🚀 [Vé Boss] Hiện tại đã sau 12h trưa ➔ Bắt đầu quy trình tự động quét & dùng Vé Boss...")
            self._run_boss_ve_process(dnconsole_path, tab_name, tab_index)

        # ---------------- 6. TỰ ĐỘNG TẮT CÔNG TẮC & LƯU CẤU HÌNH ----------------
        self.after(0, lambda: self.var_switch_A.set(False))
        self.after(0, self.save_config)
        self.after(0, self.log_info, "✅ [CARD BOSS THẾ GIỚI] Đã thực thi hoàn tất quy trình! (Tự động tắt công tắc ON/OFF & giữ nguyên các ô tích)")

    # =========================================================================
    # 🔓 [ĐÃ MỞ KHÓA TOÀN DIỆN - SẴN SÀNG SỬ DỤNG]: CARD D (40 NPC / 2K)
    # =========================================================================
    def _run_40_npc_team_and_char_position(self, dnconsole_path: str, tab_index: str, selected_team_char: str, skip_char_change: bool = False):
        """PHẦN 4: TỔ ĐỘI VÀ CHUYỂN ĐỔI VỊ TRÍ NHÂN VẬT (CHỈ THỰC THI KHỊ Ô TỔ ĐỘI VAR_D2 ĐƯỢC TÍCH HOẶC ĐƯỢC GỌI TỪ PHẦN TẦNG)"""
        if self._should_stop_card_D(): return

        if not skip_char_change and not self.var_D2.get():
            self.after(0, self.log_info, "ℹ️ [40 NPC - Phần 4] Ô 'Tổ Đội' KHÔNG được tích -> Bỏ qua Phần 4.")
            return

        self.after(0, self.log_info, f"🚀 [40 NPC - Phần 4] Kích hoạt Tổ Đội (Vị trí: '{selected_team_char}', Bỏ qua đổi vị trí: {skip_char_change})...")

        if skip_char_change or selected_team_char == "Xuất Chiến":
            self.after(0, self.log_info, "ℹ️ Giữ nguyên vị trí nhân vật hiện tại ➔ Bỏ qua bước đổi đội hình.")
            return

        # Quét mở giao diện Đội (Đã xóa hoãn 3s ban đầu)
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
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'card_b/b_doi.png' trong bảng menu.")

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

        # Tap (1240, 680) ➔ Hoãn 0.4s để đóng menu giao diện Đội
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👉 Tap (1240, 680) ➔ Hoãn 0.4s để đóng menu giao diện Đội...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
        time.sleep(0.4)

    def _execute_buff_skill_cycle(self, dnconsole_path: str, tab_index: str, log_tag: str = "40 NPC / 2K"):
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

    def _run_40_npc_su_kien_tang(self, dnconsole_path: str, tab_index: str, selected_tang: str, selected_team_char: str, selected_chien_dau: str = "Auto"):
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
            # BƯỚC 1 (Chờ 20H00): Vòng lặp chờ đồng hồ hệ thống chạm mốc 20:00:00.
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
                    if self._should_stop_card_D(): return
                    lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75)
                    if lx_x is not None and lx_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                        time.sleep(0.4)

                    if self._should_stop_card_D(): return
                    b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
                    if b_doi_x is not None and b_doi_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                        time.sleep(0.4)
                    else:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
                        time.sleep(0.4)
                        if self._should_stop_card_D(): return
                        b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
                        if b_doi_x is not None and b_doi_y is not None:
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                            time.sleep(0.4)

                    all_present = True
                    missing_list = []
                    for char_name in list_B:
                        if self._should_stop_card_D(): return
                        chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/40npc2k/{char_name}.png", threshold=0.80)
                        if chk_x is None or chk_y is None:
                            chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/{char_name}.png", threshold=0.80, region=(305, 150, 1105, 625))
                        if chk_x is None or chk_y is None:
                            all_present = False
                            missing_list.append(char_name)

                    if all_present:
                        self.after(0, self.log_info, f"✅ [40 NPC - Auto] Lần 1: Tổ đội đã ĐỦ {len(list_B)} thành viên!")
                        lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75)
                        if lx_x is not None and lx_y is not None:
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                            time.sleep(0.4)
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
                        time.sleep(0.4)
                        break
                    else:
                        self.after(0, self.log_info, f"⚠️ [40 NPC - Auto] Lần 1: Đội thiếu: {', '.join(missing_list)} ➔ Gọi Thao tác 1 Tổ Đội...")
                        lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75)
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



    def _execute_card_D_40_npc(self, dnconsole_path: str, tab_name: str, tab_index: str):
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

        # =========================================================================
        # 📌 THAO TÁC 1: TỔ ĐỘI & ĐỔI VỊ TRÍ TƯỚNG (KHI Ô VAR_D2 ĐƯỢC TÍCH)
        # =========================================================================
        if self.var_D2.get():
            self.after(0, self.log_info, f"🚀 [40 NPC / 2K - 1. Tổ Đội] Khởi chạy ô Tổ Đội (Vị trí: '{selected_team_char}')...")
            self._run_40_npc_team_and_char_position(dnconsole_path, tab_index, selected_team_char)
            self._execute_card_E_for_mode(dnconsole_path, tab_name, tab_index, mode=1)
        else:
            self.after(0, self.log_info, "ℹ️ [40 NPC / 2K - 1. Tổ Đội] Ô 'Tổ Đội' KHÔNG được tích ➔ Bỏ qua.")

        # =========================================================================
        # 📌 THAO TÁC 2: 40 NPC (KHI Ô VAR_D3 ĐƯỢC TÍCH)
        # =========================================================================
        if self.var_D3.get():
            self.after(0, self.log_info, f"🚀 [40 NPC / 2K - 2. 40 NPC] Khởi chạy ô 40 NPC (Chế độ: '{selected_chien_dau}')...")
            self._run_40_npc_su_kien_tang(dnconsole_path, tab_index, "Cố Định", selected_team_char, selected_chien_dau)
        else:
            self.after(0, self.log_info, "ℹ️ [40 NPC / 2K - 2. 40 NPC] Ô '40 NPC' KHÔNG được tích ➔ Bỏ qua.")

        # =========================================================================
        # 📌 THAO TÁC 3: NHỊ KIỀU (KHI Ô VAR_D4 ĐƯỢC TÍCH)
        # =========================================================================
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

    def _run_nhi_kieu_tang_tret_10(self, dnconsole_path: str, tab_index: str, loop_count: int = 10, mode_name: str = "Trệt - 10", run_stages_1_to_3: bool = True, only_stages_1_to_3: bool = False, check_until_dinh: bool = False, card_name: str = "40 NPC"):
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
            self.after(0, self.log_info, f"👁️ [{mode_name} - Bước 1.1] Quét 'card_d/nhikieu/d_buoc1.png' (80%)...")
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

            # 1.5: Quét & Tap card_d/nhikieu/d_buoc1.png (Threshold 80%) lần 2 ➔ Hoãn 2.0s
            self.after(0, self.log_info, f"👁️ [{mode_name} - Bước 1.5] Quét 'd_buoc1.png' lần 2 ➔ Hoãn 2.0s...")
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
            # 2.1: Quét & Tap card_d/nhikieu/d_buoc2.png (Threshold 75%)
            self.after(0, self.log_info, f"👁️ [{mode_name} - Bước 2.1] Quét 'd_buoc2.png' (75%)...")
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

            # 2.5: Tap card_d/nhikieu/d_buoc2.png (75%) mỗi 0.5s đến khi mất ➔ Hoãn 2.0s
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

            # 3.6: Tap d_buoc3.png (80%) mỗi 0.5s đến khi mất ➔ Hoãn 2.0s
            self.after(0, self.log_info, f"👉 [{mode_name} - Bước 3.6] Tap 'd_buoc3.png' mỗi 0.5s đến khi mất ➔ Hoãn 2.0s...")
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

    def _run_nhi_kieu_tang(self, dnconsole_path: str, tab_index: str, selected_tang: str, card_name: str = "40 NPC"):
        """THAO TÁC: TẦNG / ĐÀI (NHỊ KIỀU)"""
        if self._should_stop_card_D(): return

        prefix_tag = "[40 NPC / 2K - Tầng]"
        self.after(0, self.log_info, f"🚀 {prefix_tag} Khởi chạy ô Tầng (Mốc: '{selected_tang}')...")

        if selected_tang in ["Trệt - 10", "Trệt"]:
            # Gộp thao tác Trệt (Giai đoạn 1 -> 3) và 1-10 (Vòng lặp Giai đoạn 4 -> 7 đến khi thấy e_dinh.png)
            self._run_nhi_kieu_tang_tret_10(dnconsole_path, tab_index, loop_count=0, mode_name="Trệt - 10", run_stages_1_to_3=True, only_stages_1_to_3=False, check_until_dinh=True, card_name=card_name)
        elif selected_tang == "11 - 14":
            self._run_nhi_kieu_tang_tret_10(dnconsole_path, tab_index, loop_count=0, mode_name="11 - 14", run_stages_1_to_3=False, only_stages_1_to_3=False, check_until_dinh=True, card_name=card_name)
        else:
            self.after(0, self.log_info, f"ℹ️ Mốc '{selected_tang}' đang được cập nhật thao tác chi tiết...")

    # =========================================================================
    # 🔓 [KẾT THÚC KHỐI HOẠT ĐỘNG]: CARD D (40 NPC / 2K)
    # =========================================================================
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

    def _find_template_on_screen(self, dnconsole_path: str, tab_index: str, template_filename: str, threshold: float = 0.85, check_color: bool = False, region: tuple = None):
        """👁️ Mắt Thần OpenCV: Khớp vị trí hình ảnh mẫu .png trong thư mục con assets/ với độ chính xác cao & kiểm tra độ sáng màu sắc nút"""
        clean_name = os.path.basename(template_filename)
        possible_paths = []

        for base in [get_bundle_dir(), get_app_dir()]:
            assets_dir = os.path.join(base, "assets")
            possible_paths.append(os.path.join(assets_dir, template_filename))
            possible_paths.append(os.path.join(base, template_filename))
            try:
                if os.path.exists(assets_dir):
                    for root, dirs, files in os.walk(assets_dir):
                        if clean_name in files:
                            possible_paths.append(os.path.join(root, clean_name))
                        p = os.path.join(root, template_filename)
                        if os.path.exists(p) and p not in possible_paths:
                            possible_paths.append(p)
            except Exception:
                pass

        tmpl_path = None
        for p in possible_paths:
            if os.path.exists(p) and os.path.isfile(p):
                tmpl_path = p
                break

        if tmpl_path is None or not os.path.exists(tmpl_path):
            self.after(0, self.log_error, f"⚠️ Chưa có file ảnh mẫu '{template_filename}' trong các thư mục assets/ (card_a..f, login, server...)!")
            return None, None  # Chưa có file ảnh mẫu trong assets/

        # File ảnh tạm thời chụp màn hình lưu trong thư mục TEMP an toàn của hệ điều hành
        temp_dir = os.path.join(tempfile.gettempdir(), "ts_origin_temp")
        try:
            os.makedirs(temp_dir, exist_ok=True)
        except Exception:
            pass
        temp_local = os.path.join(temp_dir, f"temp_cap_{tab_index}.png")
        
        is_nkn = ("nkn" in template_filename.lower()) or ("diemdanh" in template_filename.lower()) or ("veboss" in template_filename.lower())
        max_attempts = 3 if is_nkn else 1

        for attempt in range(max_attempts):
            # Chụp ảnh màn hình LDPlayer qua ADB
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell screencap -p /sdcard/mat_than.png"])
            self._exec_cmd([dnconsole_path, "pull", "--index", str(tab_index), "--remote", "/sdcard/mat_than.png", "--local", temp_local])
            if not os.path.exists(temp_local) or os.path.getsize(temp_local) == 0:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"pull /sdcard/mat_than.png \"{temp_local}\""])

            if os.path.exists(temp_local) and os.path.getsize(temp_local) > 0:
                try:
                    def _read_img_unicode(fpath, flags=cv2.IMREAD_COLOR):
                        try:
                            d = np.fromfile(fpath, dtype=np.uint8)
                            return cv2.imdecode(d, flags)
                        except Exception:
                            return None

                    screen = _read_img_unicode(temp_local, cv2.IMREAD_COLOR)
                    
                    if not hasattr(self, '_template_cache'):
                        self._template_cache = {}

                    if tmpl_path in self._template_cache:
                        template = self._template_cache[tmpl_path]
                    else:
                        template = _read_img_unicode(tmpl_path, cv2.IMREAD_UNCHANGED)
                        if template is not None:
                            self._template_cache[tmpl_path] = template

                    if screen is not None and template is not None:
                        # Tự động gán khoanh vùng ROI theo loại ảnh
                        offset_x, offset_y = 0, 0
                        search_screen = screen
                        target_region = region
                        if target_region is None:
                            tmpl_lower = template_filename.lower()
                            if any(k in tmpl_lower for k in ["login_auto", "c_aitim"]):
                                target_region = (0, 100, 240, 190)
                            elif "login_x" in tmpl_lower:
                                target_region = (860, 70, 1170, 200)
                            elif "a_co" in tmpl_lower:
                                target_region = (925, 540, 1150, 670)
                            elif "a_dichuyen" in tmpl_lower:
                                target_region = (895, 435, 1065, 535)
                            elif "a_skboss" in tmpl_lower:
                                target_region = (155, 95, 305, 625)
                            elif any(k in tmpl_lower for k in ["a_boss", "a_hetluot"]):
                                target_region = (275, 540, 1280, 720)
                            elif any(k in tmpl_lower for k in ["a_dung", "c_digioi", "d_tret", "d_daidien", "d_dinh", "d_tang", "e_dinh", "pbmap", "pb20map", "pb50map", "pb80map", "pb110map", "pb140map", "d_loidai"]):
                                target_region = (1060, 0, 1280, 40)
                            elif any(k in tmpl_lower for k in ["a_veboss", "a_khoa"]):
                                target_region = (730, 165, 1105, 610)
                            elif "f_tieptheo" in tmpl_lower:
                                target_region = (1050, 530, 1165, 680)
                            elif "card_f" in tmpl_lower:
                                target_region = (640, 0, 1280, 145)
                            elif any(k in tmpl_lower for k in ["b_pbdon", "b_pb20", "b_pb50", "b_pb80", "b_pb110", "b_pb140", "b_lsknn", "b_xn", "b_matkhau", "b_batdau"]):
                                target_region = (165, 170, 1110, 615)
                            elif any(k in tmpl_lower for k in ["e_nguoi", "e_doingu"]):
                                target_region = (175, 165, 295, 455)
                            elif any(k in tmpl_lower for k in ["pbdoi", "e_moi"]):
                                target_region = (175, 165, 1105, 605)
                            elif "40npc2k" in tmpl_lower:
                                target_region = (305, 150, 1105, 625)
                            elif "d_35" in tmpl_lower:
                                target_region = (1020, 265, 1125, 295)
                            elif any(k in tmpl_lower for k in ["d_dichuyen", "d_conglt", "d_vaolt"]):
                                target_region = (0, 400, 980, 720)
                            elif any(k in tmpl_lower for k in ["d_chien", "d_tieptheo"]):
                                target_region = (280, 490, 1280, 720)
                            elif any(k in tmpl_lower for k in ["d_vaotran", "d_xacdinh"]):
                                target_region = (275, 540, 980, 670)
                            elif any(k in tmpl_lower for k in ["a_sukien", "a_tui", "b_doi", "b_pb", "c_ai", "c_vitri"]):
                                target_region = (730, 405, 1200, 720)

                        if target_region is not None:
                            rx1, ry1, rx2, ry2 = target_region
                            h_s, w_s = screen.shape[:2]
                            rx1 = max(0, min(rx1, w_s))
                            rx2 = max(rx1 + 1, min(rx2, w_s))
                            ry1 = max(0, min(ry1, h_s))
                            ry2 = max(ry1 + 1, min(ry2, h_s))
                            search_screen = screen[ry1:ry2, rx1:rx2]
                            offset_x, offset_y = rx1, ry1

                        # Nới lỏng ngưỡng mặc định cho file nkn.png hoặc c_veboss.png (do có hiệu ứng chuyển động nhẹ)
                        current_threshold = threshold
                        if "veboss" in template_filename.lower():
                            current_threshold = min(threshold, 0.65)
                        elif "f_dung" in template_filename.lower():
                            current_threshold = min(threshold, 0.65)
                        elif "a_dichuyen" in template_filename.lower():
                            current_threshold = min(threshold, 0.60)
                        elif is_nkn:
                            current_threshold = min(threshold, 0.45)

                        # Xử lý Alpha Mask (trong suốt) chuẩn xác cho file PNG 4 kênh
                        if len(template.shape) == 3 and template.shape[2] == 4:
                            alpha_mask = template[:, :, 3]
                            template_bgr = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
                            if np.any(alpha_mask < 255):
                                res = cv2.matchTemplate(search_screen, template_bgr, cv2.TM_CCOEFF_NORMED, mask=alpha_mask)
                            else:
                                res = cv2.matchTemplate(search_screen, template_bgr, cv2.TM_CCOEFF_NORMED)
                        else:
                            res = cv2.matchTemplate(search_screen, template, cv2.TM_CCOEFF_NORMED)

                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

                        # 2. Nếu là file nkn.png có chữ di chuyển: Quét bổ sung theo Grayscale & Canny Edge để bắt khung viền cố định
                        if is_nkn:
                            try:
                                gray_screen = cv2.cvtColor(search_screen, cv2.COLOR_BGR2GRAY)
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
                            center_x = offset_x + max_loc[0] + w // 2
                            center_y = offset_y + max_loc[1] + h // 2

                            # Kiểm tra độ tươi sáng/màu sắc (tránh nhận nhầm ảnh nút bị tối/mờ/vô hiệu hóa)
                            is_strict_color = check_color or ("dichuyen" in template_filename.lower())
                            if is_strict_color:
                                try:
                                    crop = screen[max_loc[1]:max_loc[1]+h, max_loc[0]:max_loc[0]+w]
                                    if crop.shape[0] == h and crop.shape[1] == w:
                                        if len(template.shape) == 3 and template.shape[2] == 4:
                                            alpha = template[:, :, 3]
                                            mask_valid = alpha > 50
                                            tmpl_bgr = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
                                            tmpl_hsv = cv2.cvtColor(tmpl_bgr, cv2.COLOR_BGR2HSV)
                                            crop_hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
                                            if np.any(mask_valid):
                                                tmpl_v_mean = float(np.mean(tmpl_hsv[:, :, 2][mask_valid]))
                                                crop_v_mean = float(np.mean(crop_hsv[:, :, 2][mask_valid]))
                                            else:
                                                tmpl_v_mean = float(np.mean(tmpl_hsv[:, :, 2]))
                                                crop_v_mean = float(np.mean(crop_hsv[:, :, 2]))
                                        else:
                                            tmpl_hsv = cv2.cvtColor(template, cv2.COLOR_BGR2HSV)
                                            crop_hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
                                            tmpl_v_mean = float(np.mean(tmpl_hsv[:, :, 2]))
                                            crop_v_mean = float(np.mean(crop_hsv[:, :, 2]))

                                        # Chỉ bỏ qua nếu ảnh thực tế trên màn hình bị TỐI/MỜ hơn hẳn mẫu chuẩn (nút bị vô hiệu hóa)
                                        # Cho phép nút phát sáng/sáng hơn mẫu chuẩn (crop_v_mean >= tmpl_v_mean)
                                        if (tmpl_v_mean - crop_v_mean) > 20:
                                            self.after(0, self.log_info, f"👁️ Mắt thần quét '{template_filename}' ({match_pct}%) nhưng bị TỐI/MỜ MÀU (Độ sáng: {round(crop_v_mean, 1)} / Mẫu chuẩn: {round(tmpl_v_mean, 1)}) ➔ Bỏ qua không nhận.")
                                            try: os.remove(temp_local)
                                            except: pass
                                            return None, None
                                except Exception:
                                    pass

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



if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = ToolLDPlayerGUI()
    app.mainloop()
