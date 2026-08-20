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

# Thử import ppadb nếu có sẵn trong hệ thống
try:
    from ppadb.client import Client as AdbClient
    HAS_PPADB = True
except ImportError:
    HAS_PPADB = False

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
        self.geometry("850x685")
        self.minsize(800, 600)
        self._center_window(850, 685)

        # Đăng ký sự kiện nút X (Thu nhỏ xuống khay hệ thống)
        self.tray_icon = None
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)

        # --- BIẾN TRẠNG THÁI & CẤU HÌNH ---
        self.ld_path = r"C:\Program Files\LDPlayer\LDPlayer9"
        self.dict_name_to_index = {}
        self.is_scanning = False
        self.game_icon_path = None
        self.game_ctk_image = None

        # Biến trạng thái Công tắc tổng ON/OFF & Nút Dừng các Card
        self.var_switch_B = ctk.BooleanVar(value=False)
        self.var_pause_B = ctk.BooleanVar(value=False)
        self.var_switch_C = ctk.BooleanVar(value=False)
        self.var_pause_C = ctk.BooleanVar(value=False)
        self.var_switch_D = ctk.BooleanVar(value=False)
        self.var_pause_D = ctk.BooleanVar(value=False)
        self.var_switch_E = ctk.BooleanVar(value=False)
        self.var_pause_E = ctk.BooleanVar(value=False)
        self.var_switch_F = ctk.BooleanVar(value=False)
        self.var_pause_F = ctk.BooleanVar(value=False)
        self.var_switch_G = ctk.BooleanVar(value=False)

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
        self.var_D_chuyen_khu = ctk.BooleanVar(value=False)

        # Biến trạng thái các ô Checkbox Cấu hình E (PHỤ BẢN ĐƠN / ĐỘI)
        self.var_E_don = ctk.BooleanVar(value=False)
        self.var_E_canhan = ctk.BooleanVar(value=False)
        self.var_E_doi = ctk.BooleanVar(value=False)
        self.var_E1 = ctk.BooleanVar(value=False)
        self.var_E2 = ctk.BooleanVar(value=False)
        self.var_E3 = ctk.BooleanVar(value=False)
        self.var_E4 = ctk.BooleanVar(value=False)
        self.var_E5 = ctk.BooleanVar(value=False)

        # Biến trạng thái các ô Checkbox Cấu hình F (NHỊ KIỀU - Chuẩn giao diện như 40 NPC)
        self.var_F1 = ctk.BooleanVar(value=False)
        self.var_F2 = ctk.BooleanVar(value=False)
        self.var_F3 = ctk.BooleanVar(value=False)
        self.var_F4 = ctk.BooleanVar(value=False)
        self.var_F_chuyen_khu = ctk.BooleanVar(value=False)

        # Biến trạng thái trong Card Tổ Đội:
        self.selected_G_list_A_char = ""
        self.selected_G_list_B_char = ""
        self.list_G_B = []  # List tên nhân vật đã add sang Danh Sách B
        self.btn_G_list_A_dict = {}  # Các button bên Danh Sách A
        self.btn_G_list_B_dict = {}  # Các button bên Danh Sách B

        # Biến trạng thái Dừng khẩn cấp
        self.stop_requested = False

        # --- TẠO HỆ THỐNG GIAO DIỆN ---
        self._setup_grid()
        self._create_ld_selection_card()
        self._create_game_action_card()
        self._create_unified_config_card()
        self._create_status_bar()

        # Nạp cấu hình đã lưu
        self.load_config()

        # Căn giữa cửa sổ ứng dụng trên màn hình Desktop
        self._center_window(850, 685)

        # Quét danh sách LDPlayer lần đầu tiên
        self.refresh_ld_tabs_async()

    def _center_window(self, width: int = 850, height: int = 685):
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
        """Danh sách tên nhân vật quét động từ các file ảnh thực tế trong folder assets/nhanvat"""
        names = []
        for base in [get_bundle_dir(), get_app_dir()]:
            assets_dir = os.path.join(base, "assets")
            nhanvat_dir = os.path.join(assets_dir, "nhanvat")
            if os.path.exists(nhanvat_dir):
                try:
                    for f in sorted(os.listdir(nhanvat_dir)):
                        if f.lower().endswith(".png"):
                            char_name = f[:-4]
                            if char_name not in names:
                                names.append(char_name)
                except Exception:
                    pass
        return names

        if not os.path.exists(nhanvat_dir):
            try:
                os.makedirs(nhanvat_dir, exist_ok=True)
            except Exception:
                pass

        if os.path.exists(nhanvat_dir):
            try:
                valid_exts = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
                for f in sorted(os.listdir(nhanvat_dir)):
                    if f.lower().endswith(valid_exts):
                        name_without_ext = os.path.splitext(f)[0]
                        if name_without_ext and name_without_ext not in names:
                            names.append(name_without_ext)
            except Exception:
                pass

        return names

    def _select_G_list_A_item(self, char_name: str):
        """Chọn tên nhân vật bên [Danh Sách A] (đồng bộ folder ảnh)"""
        self.selected_G_list_A_char = char_name
        self._update_G_list_A_ui()

    def _update_G_list_A_ui(self):
        """Cập nhật màu sắc highlight tên được chọn trong [Danh Sách A] bên trái"""
        if not hasattr(self, 'btn_G_list_A_dict'):
            return
        selected = getattr(self, 'selected_G_list_A_char', "")
        for name, btn in self.btn_G_list_A_dict.items():
            if name == selected:
                btn.configure(fg_color="#EA580C", text_color="#FFFFFF", hover_color="#C2410C")
            else:
                btn.configure(fg_color="#374151", text_color="#FFFFFF", hover_color="#4B5563")

    def _add_A_to_B_G(self):
        """Thêm nhân vật đang chọn từ [Danh Sách A] sang [Danh Sách B] (Danh sách chạy thao tác)"""
        if not hasattr(self, 'list_G_B'):
            self.list_G_B = []

        char_name = getattr(self, 'selected_G_list_A_char', "")
        if not char_name:
            opts_A = self._get_nhanvat_options()
            if opts_A:
                char_name = opts_A[0]
                self.selected_G_list_A_char = char_name

        if not char_name:
            return

        if char_name not in self.list_G_B:
            self.list_G_B.append(char_name)
            self._render_G_list_B_ui()
            self.save_config()

    def _remove_B_item_G(self, char_name: str):
        """Xóa nhân vật khỏi [Danh Sách B] bên phải"""
        if hasattr(self, 'list_G_B') and char_name in self.list_G_B:
            self.list_G_B.remove(char_name)
            self._render_G_list_B_ui()
            self.save_config()

    def _select_G_list_B_item(self, char_name: str):
        """Chọn tên nhân vật trong [Danh Sách B]"""
        self.selected_G_list_B_char = char_name
        self._update_G_list_B_ui()

    def _update_G_list_B_ui(self):
        """Cập nhật màu sắc highlight nút đại diện cho tên trong [Danh Sách B]"""
        if not hasattr(self, 'btn_G_list_B_dict'):
            return
        selected = getattr(self, 'selected_G_list_B_char', "")
        for name, btn in self.btn_G_list_B_dict.items():
            if name == selected:
                btn.configure(fg_color="#EA580C", text_color="#FFFFFF", hover_color="#C2410C")
            else:
                btn.configure(fg_color="#374151", text_color="#FFFFFF", hover_color="#4B5563")

    def _render_G_list_B_ui(self):
        """Vẽ lại các phần tử trong [Danh Sách B] bên phải (giao diện CTkButton 100% y hệt chữ, nền, hình dáng của Danh Sách A)"""
        if not hasattr(self, 'scroll_G_list_B'):
            return

        for w in self.scroll_G_list_B.winfo_children():
            w.destroy()

        self.btn_G_list_B_dict = {}

        if not getattr(self, 'list_G_B', []):
            lbl_empty = ctk.CTkLabel(
                self.scroll_G_list_B,
                text="(Bấm ➔ để thêm)",
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="normal"),
                text_color="#FFFFFF"
            )
            lbl_empty.pack(pady=10)
            return

        selected_B = getattr(self, 'selected_G_list_B_char', "")
        if not selected_B and self.list_G_B:
            selected_B = self.list_G_B[0]
            self.selected_G_list_B_char = selected_B

        for char_name in list(self.list_G_B):
            row_frame = ctk.CTkFrame(self.scroll_G_list_B, fg_color="transparent")
            row_frame.pack(fill="x", padx=1, pady=2)
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=0)

            btn = ctk.CTkButton(
                row_frame,
                text=char_name,
                height=22,
                font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
                anchor="w",
                fg_color="#EA580C" if char_name == selected_B else "#374151",
                text_color="#FFFFFF",
                hover_color="#C2410C" if char_name == selected_B else "#4B5563",
                command=lambda n=char_name: self._select_G_list_B_item(n)
            )
            btn.grid(row=0, column=0, sticky="ew", padx=(0, 1))

            btn_del = ctk.CTkButton(
                row_frame,
                text="✕",
                width=16,
                height=22,
                font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                fg_color="transparent",
                text_color="#FFFFFF",
                hover_color=("#E5E7EB", "#374151"),
                command=lambda n=char_name: self._remove_B_item_G(n)
            )
            btn_del.grid(row=0, column=1, sticky="e")
            self.btn_G_list_B_dict[char_name] = btn

    def _update_card_G_visibility(self):
        """Cập nhật trạng thái sáng/tối & khóa tùy chỉnh của Card Tổ Đội theo ô check 'Tổ Đội' ở Card E, Card D (40 NPC), hoặc Card F (Nhị Kiều)"""
        if not hasattr(self, 'card_G'):
            return

        is_doi_checked = (hasattr(self, 'var_E_doi') and self.var_E_doi.get()) or \
                         (hasattr(self, 'var_D2') and self.var_D2.get()) or \
                         (hasattr(self, 'var_F2') and self.var_F2.get())
        if is_doi_checked:
            # SÁNG LÊN: Bật trạng thái tùy chỉnh và khôi phục màu tiêu đề sáng
            if hasattr(self, 'lbl_G'): self.lbl_G.configure(text_color="#38BDF8")
            if hasattr(self, 'switch_G'): self.switch_G.configure(state="normal")
            if hasattr(self, 'btn_G_add'): self.btn_G_add.configure(state="normal", fg_color="#EA580C", text_color="#FFFFFF")
            if hasattr(self, 'btn_G_list_A_dict'):
                for name, btn in self.btn_G_list_A_dict.items():
                    btn.configure(state="normal")
                self._update_G_list_A_ui()
            if hasattr(self, 'btn_G_list_B_dict'):
                for name, btn in self.btn_G_list_B_dict.items():
                    btn.configure(state="normal")
                self._update_G_list_B_ui()
            self._render_G_list_B_ui()
        else:
            # TỐI ĐI / KHÓA: Đổi màu tiêu đề mờ, tắt công tắc về OFF, khóa click
            if hasattr(self, 'lbl_G'): self.lbl_G.configure(text_color="#9CA3AF")
            if hasattr(self, 'var_switch_G'): self.var_switch_G.set(False)
            if hasattr(self, 'switch_G'): self.switch_G.configure(state="disabled")
            if hasattr(self, 'btn_G_add'): self.btn_G_add.configure(state="disabled", fg_color="#374151", text_color="#FFFFFF")
            if hasattr(self, 'btn_G_list_A_dict'):
                for name, btn in self.btn_G_list_A_dict.items():
                    btn.configure(state="disabled", fg_color="#27272A", text_color="#FFFFFF")
            if hasattr(self, 'btn_G_list_B_dict'):
                for name, btn in self.btn_G_list_B_dict.items():
                    btn.configure(state="disabled", fg_color="#27272A", text_color="#FFFFFF")
            self._render_G_list_B_ui()

    def _on_switch_G_toggled(self):
        """Callback công tắc Card TỔ ĐỘI (G): Gạt ON/OFF"""
        self._on_checkbox_toggled()
        if not self.var_switch_G.get():
            self.save_config()
            self.log_info("🛑 [CARD TỔ ĐỘI] Công tắc gạt về OFF.")
        else:
            self.save_config()
            self.log_info("⚡ [CARD TỔ ĐỘI] Công tắc gạt sang ON ➔ Sẵn sàng thực thi khi ô 'Tổ Đội' được tích.")

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
            if hasattr(self, 'combo_D_khu'):
                config["D_khu"] = self.combo_D_khu.get()
            if hasattr(self, 'combo_D_team_char'):
                config["D_team_char"] = self.combo_D_team_char.get()
            if hasattr(self, 'combo_D_chien_dau'):
                config["D_chien_dau"] = self.combo_D_chien_dau.get()
            if hasattr(self, 'var_pause_D'):
                config["pause_D"] = False  # Nút Tạm Dừng luôn lưu OFF

            if hasattr(self, 'combo_F_khu'):
                config["F_khu"] = self.combo_F_khu.get()
            if hasattr(self, 'combo_F_team_char'):
                config["F_team_char"] = self.combo_F_team_char.get()
            if hasattr(self, 'combo_F_tang'):
                config["F_tang"] = self.combo_F_tang.get()
            if hasattr(self, 'var_F_chuyen_khu'):
                config["F_chuyen_khu"] = self.var_F_chuyen_khu.get()

            for prefix in ["B", "C", "D", "E", "F", "G"]:
                switch_attr = f"var_switch_{prefix}"
                if hasattr(self, switch_attr):
                    config[f"switch_{prefix}"] = False  # Luôn lưu công tắc các card ở trạng thái OFF
                pause_attr = f"var_pause_{prefix}"
                if hasattr(self, pause_attr):
                    config[f"pause_{prefix}"] = False  # Nút Tạm Dừng luôn lưu ở trạng thái OFF

                for num in range(1, 6):
                    key = f"{prefix}{num}"
                    var_attr = f"var_{key}"
                    if hasattr(self, var_attr):
                        config[key] = getattr(self, var_attr).get()

            if hasattr(self, 'list_G_B'):
                config["G_list_B"] = list(self.list_G_B)
            if hasattr(self, 'selected_G_list_A_char'):
                config["G_selected_left"] = self.selected_G_list_A_char

            if hasattr(self, 'combo_ld_tabs'):
                config["selected_tab"] = self.combo_ld_tabs.get()

            config_path = os.path.join(get_app_dir(), "config.json")
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            pass

    def load_config(self):
        """Khôi phục toàn bộ cấu hình máy chủ & checkbox từ config.json (Các công tắc & nút Tạm Dừng bắt buộc giữ OFF khi mở lại)"""
        config_path = os.path.join(get_app_dir(), "config.json")
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
                if "D_khu" in config and hasattr(self, 'combo_D_khu'):
                    val = config["D_khu"]
                    self.combo_D_khu.set(val if val in ["Cố Định"] + [f"Khu {i}" for i in range(1, 11)] else "Cố Định")
                if "D_team_char" in config and hasattr(self, 'combo_D_team_char'):
                    val = config["D_team_char"]
                    self.combo_D_team_char.set(val if val in opts else "Xuất Chiến")
                if "D_chien_dau" in config and hasattr(self, 'combo_D_chien_dau'):
                    val = config["D_chien_dau"]
                    self.combo_D_chien_dau.set(val if val in ["Auto", "Click"] else "Auto")
                if hasattr(self, 'var_pause_D'):
                    self.var_pause_D.set(False)  # Nút Tạm Dừng luôn OFF khi mở tool

                if "F_khu" in config and hasattr(self, 'combo_F_khu'):
                    val = config["F_khu"]
                    self.combo_F_khu.set(val if val in ["Cố Định"] + [f"Khu {i}" for i in range(1, 11)] else "Cố Định")
                if "F_team_char" in config and hasattr(self, 'combo_F_team_char'):
                    val = config["F_team_char"]
                    self.combo_F_team_char.set(val if val in opts else "Xuất Chiến")
                tang_F_opts = ["Trệt", "1 - 10", "Đài QS", "11 - 14", "Đài Rồng", "15 - 18", "Đài Hổ"]
                if "F_tang" in config and hasattr(self, 'combo_F_tang'):
                    val = config["F_tang"]
                    self.combo_F_tang.set(val if val in tang_F_opts else "Trệt")
                if "F_chuyen_khu" in config and hasattr(self, 'var_F_chuyen_khu'):
                    self.var_F_chuyen_khu.set(config["F_chuyen_khu"])

                for prefix in ["B", "C", "D", "E", "F", "G"]:
                    switch_attr = f"var_switch_{prefix}"
                    if hasattr(self, switch_attr):
                        getattr(self, switch_attr).set(False)  # Bắt buộc công tắc về OFF khi mở tool
                    pause_attr = f"var_pause_{prefix}"
                    if hasattr(self, pause_attr):
                        getattr(self, pause_attr).set(False)  # Bắt buộc nút Tạm Dừng về OFF khi mở tool

                    for num in range(1, 6):
                        key = f"{prefix}{num}"
                        var_attr = f"var_{key}"
                        if key in config and hasattr(self, var_attr):
                            getattr(self, var_attr).set(config[key])

                if "G_selected_left" in config:
                    self.selected_G_list_A_char = config["G_selected_left"]

                if "G_list_B" in config and isinstance(config["G_list_B"], list):
                    self.list_G_B = list(config["G_list_B"])
                    self._render_G_list_B_ui()
                self._update_G_list_A_ui()

                if "selected_tab" in config and hasattr(self, 'combo_ld_tabs'):
                    self.saved_selected_tab = config["selected_tab"]
                self._update_card_G_visibility()
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
        """Thiết lập Grid Layout 1 cột (Đã loại bỏ Card Log)"""
        self.grid_rowconfigure(0, weight=0)  # Card chọn LD Tab
        self.grid_rowconfigure(1, weight=0)  # Card Game Action
        self.grid_rowconfigure(2, weight=1)  # Khung chứa 6 Card Cấu hình co giãn
        self.grid_rowconfigure(3, weight=0)  # Status bar cố định bên dưới

        self.grid_columnconfigure(0, weight=1)  # Cột duy nhất chứa toàn bộ các Card

    def _create_header(self):
        """Khung Header (Đã loại bỏ để thu gọn tool)"""
        pass

    def _create_ld_selection_card(self):
        """Khung Card Chọn Tab LDPlayer & Server & Khởi Động"""
        self.card_ld = ctk.CTkFrame(self, corner_radius=8)
        self.card_ld.grid(row=0, column=0, padx=10, pady=(8, 4), sticky="nsew")
        self.card_ld.grid_columnconfigure(0, weight=1)
        self.card_ld.grid_rowconfigure((0, 1), weight=1)

        # Header Card LD: Tiêu đề & Nút đổi Dark / Light Theme
        hdr_ld = ctk.CTkFrame(self.card_ld, fg_color="transparent")
        hdr_ld.grid(row=0, column=0, padx=10, pady=(6, 2), sticky="ew")
        hdr_ld.grid_columnconfigure(0, weight=1)
        hdr_ld.grid_columnconfigure(1, weight=0)

        # Label tiêu đề
        lbl_card_title = ctk.CTkLabel(
            hdr_ld,
            text="TAB LDPLAYER & SERVER",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#38BDF8"
        )
        lbl_card_title.grid(row=0, column=0, sticky="w")

        # Nút đổi Dark / Light Theme chuyển xuống kế tiêu đề bên phải chữ Khởi Động
        self.switch_theme = ctk.CTkSwitch(
            hdr_ld, 
            text="Tối", 
            command=self._toggle_theme,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            progress_color="#EA580C"
        )
        self.switch_theme.select()
        self.switch_theme.grid(row=0, column=1, sticky="e")

        # Khung chứa 3 mục: Menu Tab - Menu Server - Nút Ts origin (Chia tỉ lệ kích thước cân đối 1:1:1)
        select_row = ctk.CTkFrame(self.card_ld, fg_color="transparent")
        select_row.grid(row=1, column=0, padx=10, pady=(0, 6), sticky="nsew")
        select_row.grid_columnconfigure((0, 1, 2), weight=1)
        select_row.grid_rowconfigure(0, weight=1)

        # 1. Menu Tab LDPlayer
        self.combo_ld_tabs = ctk.CTkComboBox(
            select_row,
            values=["Đang quét tab..."],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            height=34,
            command=self._on_ld_tab_selected
        )
        self.combo_ld_tabs.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        # 2. Menu Server (OptionMenu)
        self.combo_server = ctk.CTkOptionMenu(
            select_row,
            values=self._get_server_options(),
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            height=34,
            dynamic_resizing=False,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=self._on_server_changed
        )
        self.combo_server.set("Điêu Thuyền")
        self.combo_server.grid(row=0, column=1, padx=4, sticky="ew")

        # 3. Nút "TS Origin"
        self.btn_enter_game = ctk.CTkButton(
            select_row,
            text="TS Origin",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            text_color="#FFFFFF",
            height=34,
            fg_color="#059669",
            hover_color="#047857",
            command=self.xu_ly_ts_origin
        )
        self.btn_enter_game.grid(row=0, column=2, padx=(4, 0), sticky="ew")

    def _on_ld_tab_selected(self, choice: str):
        """Tự động ghi nhớ tab LDPlayer được chọn vào config.json"""
        self.saved_selected_tab = choice
        self.save_config()
        self.log_info(f"💾 Đã ghi nhớ tab LDPlayer: '{choice}'")

    def _create_game_action_card(self):
        """Khung Card KHỞI ĐỘNG (PHỤ BẢN ĐƠN / ĐỘI & BOSS THẾ GIỚI & DỊ GIỚI)"""
        self.card_game = ctk.CTkFrame(self, corner_radius=8)
        self.card_game.grid(row=1, column=0, padx=10, pady=4, sticky="nsew")
        self.card_game.grid_columnconfigure((0, 1), weight=1)
        self.card_game.grid_rowconfigure((0, 1), weight=1)

        # Container chứa tiêu đề (màu vàng hệ Địa #FBBF24)
        title_box = ctk.CTkFrame(self.card_game, fg_color="transparent")
        title_box.grid(row=0, column=0, columnspan=2, padx=10, pady=(6, 4), sticky="w")

        f_hdr = ctk.CTkFont(family="Segoe UI", size=12, weight="bold")

        lbl_game_title = ctk.CTkLabel(
            title_box,
            text="KHỞI ĐỘNG ( PB ĐƠN/ĐỘI - BOSS TG - DỊ GIỚI )",
            font=f_hdr,
            text_color="#38BDF8"
        )
        lbl_game_title.pack(side="left")

        # Nút "Chạy" (Column 0)
        self.btn_run = ctk.CTkButton(
            self.card_game,
            text="Chạy",
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            text_color="#FFFFFF",
            fg_color="#059669",
            hover_color="#047857",
            command=self.xu_ly_nut_chay
        )
        self.btn_run.grid(row=1, column=0, padx=(10, 4), pady=(0, 8), sticky="ew")

        # Nút "Dừng" (Column 1 - Chỉ cho phép dừng 3 card Phụ Bản Đơn/Đội, Boss Thế Giới, Dị Giới)
        self.btn_stop = ctk.CTkButton(
            self.card_game, 
            text="Dừng", 
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            text_color="#FFFFFF",
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=self.dung_tat_ca_hoat_dong
        )
        self.btn_stop.grid(row=1, column=1, padx=(4, 10), pady=(0, 8), sticky="ew")

    def _on_server_changed(self, choice: str):
        """Tự động ghi nhớ vị trí máy chủ được chọn để khôi phục cho lần mở tool sau"""
        self.save_config()
        self.log_info(f"💾 Đã ghi nhớ máy chủ: '{choice}'")

    def _create_log_card(self):
        """Card Log đã được loại bỏ để thu gọn kích thước tool"""
        pass

    def _clear_log(self):
        """Xóa log (giữ nguyên để tránh lỗi gọi hàm)"""
        pass

    def _create_status_bar(self):
        """Thanh trạng thái bên dưới cùng"""
        self.status_bar = ctk.CTkFrame(self, height=26, corner_radius=0, fg_color=("gray85", "gray15"))
        self.status_bar.grid(row=3, column=0, columnspan=1, sticky="ew")
        self.status_bar.grid_columnconfigure(0, weight=1)

        self.lbl_status = ctk.CTkLabel(
            self.status_bar,
            text="Sẵn sàng",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF"
        )
        self.lbl_status.grid(row=0, column=0, padx=12, sticky="w")

        self.lbl_tab_count = ctk.CTkLabel(
            self.status_bar,
            text="Tab LD: 0",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF"
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
        """Callback công tắc Card DỊ GIỚI: Gạt ON ➔ Sẵn sàng chờ nút Chạy; Gạt OFF ➔ Dừng tiến trình card này & nhả ô Tạm Dừng"""
        self._on_checkbox_toggled()
        if not self.var_switch_B.get():
            if hasattr(self, 'var_pause_B'):
                self.var_pause_B.set(False)
            self.save_config()
            self.log_info("🛑 [CARD DỊ GIỚI] Công tắc gạt về OFF ➔ Đã ngắt tiến trình & nhả ô Tạm Dừng Card Dị Giới!")
        else:
            self.save_config()
            self.log_info("⚡ [CARD DỊ GIỚI] Công tắc gạt sang ON ➔ Sẵn sàng thực thi khi bấm nút 'Chạy'.")

    def _on_pause_B_toggled(self):
        """Callback nút Dừng ở Card Dị Giới"""
        self._on_checkbox_toggled()
        if self.var_pause_B.get():
            self.log_info("⏸️ [DỊ GIỚI] Tích ô Dừng ➔ Tạm dừng hoạt động Dị Giới (nhả ô Dừng sẽ chạy tiếp)!")
        else:
            self.log_info("▶️ [DỊ GIỚI] Nhả ô Dừng ➔ Khôi phục chạy tiếp Dị Giới!")
        self.save_config()

    def _on_switch_E_toggled(self):
        """Callback công tắc Card PHỤ BẢN ĐƠN / ĐỘI: Gạt ON ➔ Sẵn sàng chờ nút Chạy; Gạt OFF ➔ Dừng tiến trình card này & nhả ô Tạm Dừng"""
        self._on_checkbox_toggled()
        if not self.var_switch_E.get():
            if hasattr(self, 'var_pause_E'):
                self.var_pause_E.set(False)
            self._update_card_G_visibility()
            self.save_config()
            self.log_info("🛑 [CARD PHỤ BẢN ĐƠN / ĐỘI] Công tắc gạt về OFF ➔ Đã ngắt tiến trình & nhả ô Tạm Dừng Card Phụ Bản!")
        else:
            self._update_card_G_visibility()
            self.save_config()
            self.log_info("⚡ [CARD PHỤ BẢN ĐƠN / ĐỘI] Công tắc gạt sang ON ➔ Sẵn sàng thực thi khi bấm nút 'Chạy'.")

    def _on_pause_E_toggled(self):
        """Callback nút Dừng ở Card Phụ Bản Đơn/Đội"""
        self._on_checkbox_toggled()
        if self.var_pause_E.get():
            self.log_info("⏸️ [PHỤ BẢN] Tích ô Dừng ➔ Tạm dừng hoạt động Phụ Bản (nhả ô Dừng sẽ chạy tiếp)!")
        else:
            self.log_info("▶️ [PHỤ BẢN] Nhả ô Dừng ➔ Khôi phục chạy tiếp Phụ Bản!")
        self.save_config()

    def _on_switch_C_toggled(self):
        """Callback công tắc Card BOSS THẾ GIỚI: Gạt ON ➔ Sẵn sàng chờ nút Chạy; Gạt OFF ➔ Dừng tiến trình card này & nhả ô Tạm Dừng"""
        self._on_checkbox_toggled()
        if not self.var_switch_C.get():
            if hasattr(self, 'var_pause_C'):
                self.var_pause_C.set(False)
            self.save_config()
            self.log_info("🛑 [CARD BOSS THẾ GIỚI] Công tắc gạt về OFF ➔ Đã ngắt tiến trình & nhả ô Tạm Dừng Card Boss Thế Giới!")
        else:
            self.save_config()
            self.log_info("⚡ [CARD BOSS THẾ GIỚI] Công tắc gạt sang ON ➔ Sẵn sàng thực thi khi bấm nút 'Chạy'.")

    def _on_pause_C_toggled(self):
        """Callback nút Dừng ở Card Boss Thế Giới"""
        self._on_checkbox_toggled()
        if self.var_pause_C.get():
            self.log_info("⏸️ [BOSS THẾ GIỚI] Tích ô Dừng ➔ Tạm dừng hoạt động Boss Thế Giới (nhả ô Dừng sẽ chạy tiếp)!")
        else:
            self.log_info("▶️ [BOSS THẾ GIỚI] Nhả ô Dừng ➔ Khôi phục chạy tiếp Boss Thế Giới!")
        self.save_config()

    def _on_switch_D_toggled(self):
        """Callback riêng cho công tắc Card E (40 NPC): Khi trượt sang OFF -> Ngắt tiến trình & nhả ô Tạm Dừng, giữ nguyên các ô check"""
        self._on_checkbox_toggled()
        if not self.var_switch_D.get():
            if hasattr(self, 'var_pause_D'):
                self.var_pause_D.set(False)
            self.save_config()
            self.log_info("🛑 [CARD E: 40 NPC] Công tắc gạt về OFF ➔ Đã ngắt tiến trình & nhả ô Tạm Dừng Card E!")
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

            dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")

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

    def _on_chk_F_chuyen_khu_toggled(self):
        """Callback công tắc Chuyển Khu ở Card Nhị Kiều"""
        self._on_checkbox_toggled()
        if hasattr(self, 'var_F_chuyen_khu') and self.var_F_chuyen_khu.get():
            self.log_info("⚡ [NHỊ KIỀU] Đã bật công tắc 'Chuyển Khu'!")
        else:
            self.log_info("ℹ️ [NHỊ KIỀU] Đã tắt công tắc 'Chuyển Khu'.")
        self.save_config()

    def _on_pause_F_toggled(self):
        """Callback nút Dừng ở Card Nhị Kiều"""
        self._on_checkbox_toggled()
        if self.var_pause_F.get():
            self.log_info("⏸️ [NHỊ KIỀU] Tích ô Dừng ➔ Tạm dừng hoạt động Nhị Kiều (nhả ô Dừng sẽ chạy tiếp)!")
        else:
            self.log_info("▶️ [NHỊ KIỀU] Nhả ô Dừng ➔ Khôi phục chạy tiếp Nhị Kiều!")
        self.save_config()

    def _on_switch_F_toggled(self):
        """Callback riêng cho công tắc Card F (NHỊ KIỀU): Khi trượt sang OFF -> Ngắt tiến trình & nhả ô Tạm Dừng, giữ nguyên các ô check"""
        self._on_checkbox_toggled()
        if not self.var_switch_F.get():
            if hasattr(self, 'var_pause_F'):
                self.var_pause_F.set(False)
            self.save_config()
            self.log_info("🛑 [CARD F: NHỊ KIỀU] Công tắc gạt về OFF ➔ Đã ngắt tiến trình & nhả ô Tạm Dừng Card F!")
        else:
            self.stop_requested = False
            tab_name, tab_index = self._get_selected_ld_info()
            if tab_index is None:
                self.log_error("Vui lòng chọn một Tab LDPlayer trước khi bật công tắc Nhị Kiều!")
                self.var_switch_F.set(False)
                if hasattr(self, 'var_pause_F'):
                    self.var_pause_F.set(False)
                self.save_config()
                return

            dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")

            if not os.path.exists(dnconsole_path):
                self.log_error(f"Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
                self.var_switch_F.set(False)
                if hasattr(self, 'var_pause_F'):
                    self.var_pause_F.set(False)
                self.save_config()
                return

            self.log_info(f"⚡ [NHỊ KIỀU] Công tắc vừa trượt ON ➔ Khởi chạy ngay thao tác trên Tab: {tab_name} (Index: {tab_index})...")
            threading.Thread(target=self._execute_card_F_nhi_kieu, args=(dnconsole_path, tab_name, tab_index), daemon=True).start()

    def _create_unified_config_card(self):
        """Khung chứa 6 Card Cấu hình (Layout 2 hàng x 3 cột)"""
        self.container_cfg = ctk.CTkFrame(self, fg_color="transparent")
        self.container_cfg.grid(row=2, column=0, padx=10, pady=4, sticky="nsew")
        self.container_cfg.grid_columnconfigure(0, weight=320, minsize=320)  # Tăng kích thước Card Đơn/Đội & Card Tổ Đội (320px)
        self.container_cfg.grid_columnconfigure(1, weight=255, minsize=255)  # Kích thước vừa vặn Card Boss TG & Card 40 NPC (255px)
        self.container_cfg.grid_columnconfigure(2, weight=245, minsize=245)  # Giảm kích thước Card Dị Giới & Card 2K (245px)
        self.container_cfg.grid_rowconfigure((0, 1), weight=1, uniform="card_rows")  # Chia đều 1/2 chiều cao cho cả 2 hàng Card

        # ------------------- CARD 1: PHỤ BẢN ĐƠN / ĐỘI (Cột 0, Row 0) -------------------
        self.card_E = ctk.CTkFrame(self.container_cfg, corner_radius=10)
        self.card_E.grid(row=0, column=0, padx=(0, 2), pady=(0, 4), sticky="nsew")
        self.card_E.grid_columnconfigure(0, weight=1)
        self.card_E.grid_rowconfigure(0, weight=0)
        self.card_E.grid_rowconfigure((1, 2, 3, 4), weight=1)

        hdr_E = ctk.CTkFrame(self.card_E, fg_color="transparent")
        hdr_E.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="ew")
        hdr_E.grid_columnconfigure(0, weight=1)
        hdr_E.grid_columnconfigure(1, weight=0)
        hdr_E.grid_columnconfigure(2, weight=0)

        lbl_E = ctk.CTkLabel(hdr_E, text="PHỤ BẢN ĐƠN / ĐỘI", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color="#38BDF8")
        lbl_E.grid(row=0, column=0, sticky="w")

        self.chk_pause_E = ctk.CTkCheckBox(
            hdr_E, text="Tạm Dừng", variable=self.var_pause_E, command=self._on_pause_E_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=8
        )
        self.chk_pause_E.grid(row=0, column=1, sticky="e", padx=(0, 2))

        self.switch_E = ctk.CTkSwitch(
            hdr_E, text="", variable=self.var_switch_E, command=self._on_switch_E_toggled,
            width=36, height=18, switch_width=36, switch_height=18, fg_color="#374151", progress_color="#EA580C", text_color="#FFFFFF"
        )
        self.switch_E.grid(row=0, column=2, sticky="e")

        char_options = self._get_character_options()

        # Bảng Cấu hình chế độ Phụ Bản Đơn / Đội
        grid_modes = ctk.CTkFrame(self.card_E, fg_color="transparent")
        grid_modes.grid(row=1, column=0, padx=4, pady=1, sticky="ew")
        grid_modes.grid_columnconfigure(0, weight=0)
        grid_modes.grid_columnconfigure(1, weight=1)

        # Tiêu đề Phụ Bản Đơn
        lbl_pb_don = ctk.CTkLabel(
            grid_modes, text="Phụ Bản Đơn",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#FFFFFF"
        )
        lbl_pb_don.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 1))

        # Hàng 1 (Phụ Bản Đơn): [ ] Cá Nhân | [ Menu NV Đơn ]
        box_don_check = ctk.CTkFrame(grid_modes, fg_color="transparent")
        box_don_check.grid(row=1, column=0, sticky="w", padx=(0, 1))

        self.chk_E_don = ctk.CTkCheckBox(
            box_don_check, text="Cá Nhân", variable=self.var_E_don, command=self._on_checkbox_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
        )
        self.chk_E_don.pack(side="left", padx=(0, 1))

        self.combo_E_don_char = ctk.CTkOptionMenu(
            grid_modes,
            values=char_options,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            height=24,
            width=100,
            dynamic_resizing=False,
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
            text_color="#FFFFFF"
        )
        lbl_pb_doi.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(2, 1))

        # Hàng 2 (Phụ Bản Đội): [ ] Cá Nhân | [ ] Tổ Đội | [ Menu NV Team ]
        box_checks_team = ctk.CTkFrame(grid_modes, fg_color="transparent")
        box_checks_team.grid(row=3, column=0, sticky="w", padx=(0, 1))

        self.chk_E_canhan = ctk.CTkCheckBox(
            box_checks_team, text="Cá Nhân", variable=self.var_E_canhan, command=self._on_E_canhan_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
        )
        self.chk_E_canhan.pack(side="left", padx=(0, 0))

        divider_E_team = ctk.CTkFrame(box_checks_team, width=2, height=14, fg_color="#38BDF8")
        divider_E_team.pack(side="left", padx=(2, 5))

        self.chk_E_doi = ctk.CTkCheckBox(
            box_checks_team, text="Tổ Đội", variable=self.var_E_doi, command=self._on_E_doi_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
        )
        self.chk_E_doi.pack(side="left", padx=(0, 0))

        self.combo_E_team_char = ctk.CTkOptionMenu(
            grid_modes,
            values=char_options,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            height=24,
            width=100,
            dynamic_resizing=False,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=lambda choice: self._on_checkbox_toggled()
        )
        self.combo_E_team_char.set(char_options[0] if char_options else "Xuất Chiến")
        self.combo_E_team_char.grid(row=3, column=1, sticky="w")

        # Đường gạch ngang phân cách giữa phần Chế độ/Menu (trên) và 4 Phụ bản (dưới)
        divider_horiz_E = ctk.CTkFrame(self.card_E, height=1, fg_color="#EA580C")
        divider_horiz_E.grid(row=2, column=0, padx=6, pady=(2, 2), sticky="ew")

        # 5 Mục Phụ Bản xếp trong CÙNG 1 FRAME GRID ĐỒNG NHẤT (Đảm bảo gióng cột thẳng tuyệt đối):
        # Hàng 0: PB 20 (Cột 0) | PB 50 (Cột 1) | PB 80 (Cột 2)
        # Hàng 1: PB 110 (Cột 0) | Click (Cột 1)
        frame_pb_grid = ctk.CTkFrame(self.card_E, fg_color="transparent")
        frame_pb_grid.grid(row=3, column=0, padx=6, pady=(1, 3), sticky="ew")
        frame_pb_grid.grid_columnconfigure(0, weight=1, uniform="pb_col")
        frame_pb_grid.grid_columnconfigure(1, weight=1, uniform="pb_col")
        frame_pb_grid.grid_columnconfigure(2, weight=1, uniform="pb_col")

        self.chk_E1 = ctk.CTkCheckBox(frame_pb_grid, text="PB 20", variable=self.var_E1, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_E1.grid(row=0, column=0, sticky="w", pady=2)

        self.chk_E2 = ctk.CTkCheckBox(frame_pb_grid, text="PB 50", variable=self.var_E2, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_E2.grid(row=0, column=1, sticky="w", pady=2)

        self.chk_E3 = ctk.CTkCheckBox(frame_pb_grid, text="PB 80", variable=self.var_E3, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_E3.grid(row=0, column=2, sticky="w", pady=2)

        self.chk_E4 = ctk.CTkCheckBox(frame_pb_grid, text="PB 110", variable=self.var_E4, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_E4.grid(row=1, column=0, sticky="w", pady=2)

        self.chk_E5 = ctk.CTkCheckBox(frame_pb_grid, text="Click", variable=self.var_E5, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_E5.grid(row=1, column=1, sticky="w", pady=2)

        # ------------------- CARD 2: BOSS THẾ GIỚI (Cột 1, Row 0) -------------------
        self.card_C = ctk.CTkFrame(self.container_cfg, corner_radius=10)
        self.card_C.grid(row=0, column=1, padx=2, pady=(0, 4), sticky="nsew")
        self.card_C.grid_columnconfigure(0, weight=1)
        self.card_C.grid_rowconfigure(0, weight=0)
        self.card_C.grid_rowconfigure(1, weight=1)
        self.card_C.grid_rowconfigure(2, weight=0)

        hdr_C = ctk.CTkFrame(self.card_C, fg_color="transparent")
        hdr_C.grid(row=0, column=0, padx=4, pady=(6, 2), sticky="ew")
        hdr_C.grid_columnconfigure(0, weight=1)
        hdr_C.grid_columnconfigure(1, weight=0)
        hdr_C.grid_columnconfigure(2, weight=0)

        lbl_C = ctk.CTkLabel(hdr_C, text="BOSS TG", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color="#38BDF8")
        lbl_C.grid(row=0, column=0, sticky="w")

        self.chk_pause_C = ctk.CTkCheckBox(
            hdr_C, text="Tạm Dừng", variable=self.var_pause_C, command=self._on_pause_C_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=8
        )
        self.chk_pause_C.grid(row=0, column=1, sticky="e", padx=(0, 2))

        self.switch_C = ctk.CTkSwitch(
            hdr_C, text="", variable=self.var_switch_C, command=self._on_switch_C_toggled,
            width=36, height=18, switch_width=36, switch_height=18, fg_color="#374151", progress_color="#EA580C", text_color="#FFFFFF"
        )
        self.switch_C.grid(row=0, column=2, sticky="e")

        # Bảng chứa Boss & Vé được sắp xếp cân đối
        grid_C_body = ctk.CTkFrame(self.card_C, fg_color="transparent")
        grid_C_body.grid(row=1, column=0, padx=8, pady=(4, 4), sticky="nsew")
        grid_C_body.grid_columnconfigure(0, weight=0, minsize=52)
        grid_C_body.grid_columnconfigure(1, weight=1)
        grid_C_body.grid_rowconfigure((0, 1), weight=1)

        # Hàng 0: Boss + Menu Vị trí xuất chiến
        self.chk_C1 = ctk.CTkCheckBox(
            grid_C_body, text="Boss", variable=self.var_C1, command=self._on_checkbox_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
        )
        self.chk_C1.grid(row=0, column=0, sticky="w", pady=2)

        self.combo_C_char = ctk.CTkOptionMenu(
            grid_C_body,
            values=char_options,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            height=24,
            width=100,
            dynamic_resizing=False,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=lambda choice: self._on_checkbox_toggled()
        )
        self.combo_C_char.set(char_options[0] if char_options else "Xuất Chiến")
        self.combo_C_char.grid(row=0, column=1, sticky="w", pady=2)

        # Hàng 1: Vé + Menu số
        self.chk_C3 = ctk.CTkCheckBox(
            grid_C_body, text="Vé", variable=self.var_C3, command=self._on_checkbox_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
        )
        self.chk_C3.grid(row=1, column=0, sticky="w", pady=2)

        self.combo_C_ve = ctk.CTkOptionMenu(
            grid_C_body,
            values=["1", "2", "3", "4", "5"],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            height=24,
            width=100,
            dynamic_resizing=False,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=lambda choice: self._on_checkbox_toggled()
        )
        self.combo_C_ve.set("1")
        self.combo_C_ve.grid(row=1, column=1, sticky="w", pady=2)

        # Lịch hệ Boss Thế Giới 7 ngày chia đều theo 100% chiều ngang Card Boss
        schedule_C = ctk.CTkFrame(self.card_C, fg_color="transparent")
        schedule_C.grid(row=2, column=0, padx=6, pady=(6, 8), sticky="ew")
        schedule_C.grid_columnconfigure((0, 1, 2, 3, 4, 5, 6), weight=1)

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
            box = ctk.CTkFrame(schedule_C, fg_color="transparent")
            box.grid(row=0, column=col_idx, sticky="nsew")
            lbl_d = ctk.CTkLabel(box, text=day, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color="gray70", height=16)
            lbl_d.pack(side="top", anchor="center")
            lbl_e = ctk.CTkLabel(box, text=elem, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color=color, height=16)
            lbl_e.pack(side="top", anchor="center", pady=(3, 0))

        # ------------------- CARD 3: DỊ GIỚI (Cột 2, Row 0) -------------------
        self.card_B = ctk.CTkFrame(self.container_cfg, corner_radius=10)
        self.card_B.grid(row=0, column=2, padx=(2, 0), pady=(0, 4), sticky="nsew")
        self.card_B.grid_columnconfigure(0, weight=1)
        self.card_B.grid_rowconfigure(0, weight=0)
        self.card_B.grid_rowconfigure((1, 2, 3, 4), weight=1)

        hdr_B = ctk.CTkFrame(self.card_B, fg_color="transparent")
        hdr_B.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="ew")
        hdr_B.grid_columnconfigure(0, weight=1)
        hdr_B.grid_columnconfigure(1, weight=0)
        hdr_B.grid_columnconfigure(2, weight=0)

        lbl_B = ctk.CTkLabel(hdr_B, text="DỊ GIỚI", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color="#38BDF8")
        lbl_B.grid(row=0, column=0, sticky="w")

        self.chk_pause_B = ctk.CTkCheckBox(
            hdr_B, text="Tạm Dừng", variable=self.var_pause_B, command=self._on_pause_B_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=8
        )
        self.chk_pause_B.grid(row=0, column=1, sticky="e", padx=(0, 2))

        self.switch_B = ctk.CTkSwitch(
            hdr_B, text="", variable=self.var_switch_B, command=self._on_switch_B_toggled,
            width=36, height=18, switch_width=36, switch_height=18, fg_color="#374151", progress_color="#EA580C", text_color="#FFFFFF"
        )
        self.switch_B.grid(row=0, column=2, sticky="e")

        # Row 1: Phúc Thần + ( OFF / ON )
        row_B1 = ctk.CTkFrame(self.card_B, fg_color="transparent")
        row_B1.grid(row=1, column=0, padx=6, pady=2, sticky="ew")

        self.chk_B1 = ctk.CTkCheckBox(row_B1, text="Phúc Thần", variable=self.var_B1, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_B1.pack(side="left")

        lbl_B1_tag = ctk.CTkLabel(row_B1, text="( OFF / ON )", font=ctk.CTkFont(family="Segoe UI", size=8, weight="normal"), text_color="#FFFFFF")
        lbl_B1_tag.pack(side="right", padx=(0, 10))

        # Row 2: Ký Lục + ( OFF / ON )
        row_B2 = ctk.CTkFrame(self.card_B, fg_color="transparent")
        row_B2.grid(row=2, column=0, padx=6, pady=2, sticky="ew")

        self.chk_B2 = ctk.CTkCheckBox(row_B2, text="Ký Lục", variable=self.var_B2, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_B2.pack(side="left")

        lbl_B2_tag = ctk.CTkLabel(row_B2, text="( OFF / ON )", font=ctk.CTkFont(family="Segoe UI", size=8, weight="normal"), text_color="#FFFFFF")
        lbl_B2_tag.pack(side="right", padx=(0, 10))

        # Row 3: Rút Gọn + ( OFF / ON )
        row_B3 = ctk.CTkFrame(self.card_B, fg_color="transparent")
        row_B3.grid(row=3, column=0, padx=6, pady=2, sticky="ew")

        self.chk_B3 = ctk.CTkCheckBox(row_B3, text="Rút Gọn", variable=self.var_B3, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_B3.pack(side="left")

        lbl_B3_tag = ctk.CTkLabel(row_B3, text="( OFF / ON )", font=ctk.CTkFont(family="Segoe UI", size=8, weight="normal"), text_color="#FFFFFF")
        lbl_B3_tag.pack(side="right", padx=(0, 10))

        # Row 4: Dị Giới Đêm
        row_B4 = ctk.CTkFrame(self.card_B, fg_color="transparent")
        row_B4.grid(row=4, column=0, padx=6, pady=(2, 6), sticky="ew")

        self.chk_B4 = ctk.CTkCheckBox(row_B4, text="Dị Giới Đêm", variable=self.var_B4, command=self._on_checkbox_toggled, font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"), fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5)
        self.chk_B4.pack(side="left")

        # ------------------- CARD 4: TỔ ĐỘI (Cột 0, Row 1) -------------------
        self.card_G = ctk.CTkFrame(self.container_cfg, corner_radius=10)
        self.card_G.grid(row=1, column=0, padx=(0, 2), pady=(4, 0), sticky="nsew")
        self.card_G.grid_columnconfigure(0, weight=1)
        self.card_G.grid_rowconfigure(0, weight=0)
        self.card_G.grid_rowconfigure(1, weight=1)

        hdr_G = ctk.CTkFrame(self.card_G, fg_color="transparent")
        hdr_G.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="ew")
        hdr_G.grid_columnconfigure(0, weight=1)

        self.lbl_G = ctk.CTkLabel(hdr_G, text="TỔ ĐỘI", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color="#38BDF8")
        self.lbl_G.grid(row=0, column=0, sticky="w")

        # Khung chứa 2 Bảng danh sách và Nút Mũi Tên ➔ ở giữa (40px)
        body_G = ctk.CTkFrame(self.card_G, fg_color="transparent")
        body_G.grid(row=1, column=0, padx=4, pady=(2, 6), sticky="nsew")
        body_G.grid_columnconfigure(0, weight=0, minsize=105)
        body_G.grid_columnconfigure(1, weight=0, minsize=40)
        body_G.grid_columnconfigure(2, weight=0, minsize=115)
        body_G.grid_rowconfigure(0, weight=1)

        # 1. Bảng [Danh Sách A] đồng bộ từ folder ảnh (Bên trái, 100px)
        self.scroll_G_list_A = ctk.CTkScrollableFrame(
            body_G,
            width=100,
            fg_color="#1F2937",
            corner_radius=6,
            scrollbar_button_color="#4B5563",
            scrollbar_button_hover_color="#6B7280"
        )
        self.scroll_G_list_A.grid(row=0, column=0, sticky="nsew")
        self.scroll_G_list_A.grid_columnconfigure(0, weight=1)

        # 2. Khung ở giữa chứa Nút Mũi Tên ➔ (40px, height=24px)
        frame_mid_G = ctk.CTkFrame(body_G, fg_color="transparent")
        frame_mid_G.grid(row=0, column=1, sticky="ns", padx=1)

        self.btn_G_add = ctk.CTkButton(
            frame_mid_G,
            text="➔",
            width=32,
            height=24,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#FFFFFF",
            fg_color="#EA580C",
            hover_color="#C2410C",
            command=self._add_A_to_B_G
        )
        self.btn_G_add.pack(expand=True)

        # 3. Bảng [Danh Sách B] bên phải (Bảng B 110px, không ô check, add tên qua là tự động chạy thao tác)
        self.scroll_G_list_B = ctk.CTkScrollableFrame(
            body_G,
            width=110,
            fg_color="#1F2937",
            corner_radius=6,
            scrollbar_button_color="#4B5563",
            scrollbar_button_hover_color="#6B7280"
        )
        self.scroll_G_list_B.grid(row=0, column=2, sticky="nsew")
        self.scroll_G_list_B.grid_columnconfigure(0, weight=1)

        # Nạp dữ liệu ban đầu cho Danh Sách A
        nhanvat_opts = self._get_nhanvat_options()
        if nhanvat_opts and not getattr(self, 'selected_G_list_A_char', ""):
            self.selected_G_list_A_char = nhanvat_opts[0]

        self.btn_G_list_A_dict = {}

        if not nhanvat_opts:
            lbl_empty = ctk.CTkLabel(
                self.scroll_G_list_A,
                text="(Chưa có ảnh)",
                font=ctk.CTkFont(family="Segoe UI", size=10, weight="normal"),
                text_color="#FFFFFF"
            )
            lbl_empty.pack(pady=6)
        else:
            for char_name in nhanvat_opts:
                btn = ctk.CTkButton(
                    self.scroll_G_list_A,
                    text=char_name,
                    height=22,
                    font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
                    anchor="w",
                    fg_color="#EA580C" if char_name == self.selected_G_list_A_char else "#374151",
                    text_color="#FFFFFF",
                    hover_color="#C2410C" if char_name == self.selected_G_list_A_char else "#4B5563",
                    command=lambda n=char_name: self._select_G_list_A_item(n)
                )
                btn.pack(fill="x", padx=1, pady=2)
                self.btn_G_list_A_dict[char_name] = btn

        self._render_G_list_B_ui()

        # ------------------- CARD 5: 40 NPC (Cột 1, Row 1) -------------------
        self.card_D = ctk.CTkFrame(self.container_cfg, corner_radius=10)
        self.card_D.grid(row=1, column=1, padx=2, pady=(4, 0), sticky="nsew")
        self.card_D.grid_columnconfigure(0, weight=1)
        self.card_D.grid_rowconfigure(0, weight=0)
        self.card_D.grid_rowconfigure(1, weight=1)

        hdr_D = ctk.CTkFrame(self.card_D, fg_color="transparent")
        hdr_D.grid(row=0, column=0, padx=4, pady=(6, 2), sticky="ew")
        hdr_D.grid_columnconfigure(0, weight=1)
        hdr_D.grid_columnconfigure(1, weight=0)
        hdr_D.grid_columnconfigure(2, weight=0)

        lbl_D = ctk.CTkLabel(hdr_D, text="40 NPC", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color="#38BDF8")
        lbl_D.grid(row=0, column=0, sticky="w")

        # Nút/ô tích Dừng hoạt động kế bên công tắc (tích vào thì dừng, nhả ra chạy tiếp)
        self.chk_pause_D = ctk.CTkCheckBox(
            hdr_D, text="Tạm Dừng", variable=self.var_pause_D, command=self._on_pause_D_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=8
        )
        self.chk_pause_D.grid(row=0, column=1, sticky="e", padx=(0, 2))

        self.switch_D = ctk.CTkSwitch(
            hdr_D, text="", variable=self.var_switch_D, command=self._on_switch_D_toggled,
            width=36, height=18, switch_width=36, switch_height=18, fg_color="#374151", progress_color="#EA580C", text_color="#FFFFFF"
        )
        self.switch_D.grid(row=0, column=2, sticky="e")

        grid_D_body = ctk.CTkFrame(self.card_D, fg_color="transparent")
        grid_D_body.grid(row=1, column=0, padx=4, pady=(4, 6), sticky="nsew")
        grid_D_body.grid_columnconfigure(0, weight=0, minsize=58)
        grid_D_body.grid_columnconfigure(1, weight=1)
        grid_D_body.grid_rowconfigure((0, 1, 2), weight=1)

        # 1. Di Chuyển - menu drop Số Thứ Tự (Cố Định, Khu 1..Khu 10)
        self.chk_D1 = ctk.CTkCheckBox(
            grid_D_body, text="Di Chuyển", variable=self.var_D1, command=self._on_checkbox_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
        )
        self.chk_D1.grid(row=0, column=0, sticky="w", pady=4)

        box_D_khu = ctk.CTkFrame(grid_D_body, fg_color="transparent")
        box_D_khu.grid(row=0, column=1, sticky="ew", pady=4)

        khu_options = ["Cố Định"] + [f"Khu {i}" for i in range(1, 11)]
        self.combo_D_khu = ctk.CTkOptionMenu(
            box_D_khu,
            values=khu_options,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            height=24,
            width=100,
            dynamic_resizing=False,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=lambda choice: self._on_checkbox_toggled()
        )
        self.combo_D_khu.set("Cố Định")
        self.combo_D_khu.pack(side="left")

        self.chk_D_chuyen_khu = ctk.CTkCheckBox(
            box_D_khu, text="", variable=self.var_D_chuyen_khu, command=self._on_chk_D_chuyen_khu_toggled,
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=8
        )
        self.chk_D_chuyen_khu.pack(side="left", padx=(2, 0))

        # 2. Tổ Đội - menu vị trí Xuất Chiến
        self.chk_D2 = ctk.CTkCheckBox(
            grid_D_body, text="Tổ Đội", variable=self.var_D2, command=self._on_checkbox_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
        )
        self.chk_D2.grid(row=1, column=0, sticky="w", pady=4)

        self.combo_D_team_char = ctk.CTkOptionMenu(
            grid_D_body,
            values=char_options,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            height=24,
            width=100,
            dynamic_resizing=False,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=lambda choice: self._on_checkbox_toggled()
        )
        self.combo_D_team_char.set(char_options[0] if char_options else "Xuất Chiến")
        self.combo_D_team_char.grid(row=1, column=1, sticky="w", pady=4)

        # 3. Chiến Đấu - Ô tích Chiến Đấu & Menu thả xuống (Auto - Click)
        self.chk_D3 = ctk.CTkCheckBox(
            grid_D_body, text="Chiến Đấu", variable=self.var_D3, command=self._on_checkbox_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
        )
        self.chk_D3.grid(row=2, column=0, sticky="w", pady=4)

        self.combo_D_chien_dau = ctk.CTkOptionMenu(
            grid_D_body,
            values=["Auto", "Click"],
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            height=24,
            width=100,
            dynamic_resizing=False,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=lambda choice: self._on_checkbox_toggled()
        )
        self.combo_D_chien_dau.set("Auto")
        self.combo_D_chien_dau.grid(row=2, column=1, sticky="w", pady=4)

        # ------------------- CARD 6: NHỊ KIỀU (Cột 2, Row 1 - Giao diện chuẩn như Card 40 NPC) -------------------
        self.card_F = ctk.CTkFrame(self.container_cfg, corner_radius=10)
        self.card_F.grid(row=1, column=2, padx=(2, 0), pady=(4, 0), sticky="nsew")
        self.card_F.grid_columnconfigure(0, weight=1)
        self.card_F.grid_rowconfigure(0, weight=0)
        self.card_F.grid_rowconfigure(1, weight=1)

        hdr_F = ctk.CTkFrame(self.card_F, fg_color="transparent")
        hdr_F.grid(row=0, column=0, padx=8, pady=(6, 2), sticky="ew")
        hdr_F.grid_columnconfigure(0, weight=1)
        hdr_F.grid_columnconfigure(1, weight=0)
        hdr_F.grid_columnconfigure(2, weight=0)

        lbl_F = ctk.CTkLabel(hdr_F, text="2K", font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color="#38BDF8")
        lbl_F.grid(row=0, column=0, sticky="w")

        # Nút/ô tích Dừng hoạt động kế bên công tắc
        self.chk_pause_F = ctk.CTkCheckBox(
            hdr_F, text="Tạm Dừng", variable=self.var_pause_F, command=self._on_pause_F_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=8
        )
        self.chk_pause_F.grid(row=0, column=1, sticky="e", padx=(0, 2))

        self.switch_F = ctk.CTkSwitch(
            hdr_F, text="", variable=self.var_switch_F, command=self._on_switch_F_toggled,
            width=36, height=18, switch_width=36, switch_height=18, fg_color="#374151", progress_color="#EA580C", text_color="#FFFFFF"
        )
        self.switch_F.grid(row=0, column=2, sticky="e")

        grid_F_body = ctk.CTkFrame(self.card_F, fg_color="transparent")
        grid_F_body.grid(row=1, column=0, padx=6, pady=(4, 6), sticky="nsew")
        grid_F_body.grid_columnconfigure(0, weight=0, minsize=65)
        grid_F_body.grid_columnconfigure(1, weight=1)
        grid_F_body.grid_rowconfigure((0, 1, 2), weight=1)

        # 1. Di Chuyển - Chỉ giữ lại ô check Di Chuyển (bỏ menu & bỏ nút trượt)
        self.chk_F1 = ctk.CTkCheckBox(
            grid_F_body, text="Di Chuyển", variable=self.var_F1, command=self._on_checkbox_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
        )
        self.chk_F1.grid(row=0, column=0, columnspan=2, sticky="w", pady=4)

        # 2. Tổ Đội - menu vị trí Xuất Chiến (giữ nguyên không thay đổi)
        self.chk_F2 = ctk.CTkCheckBox(
            grid_F_body, text="Tổ Đội", variable=self.var_F2, command=self._on_checkbox_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
        )
        self.chk_F2.grid(row=1, column=0, sticky="w", pady=4)

        self.combo_F_team_char = ctk.CTkOptionMenu(
            grid_F_body,
            values=char_options,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            height=24,
            width=100,
            dynamic_resizing=False,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=lambda choice: self._on_checkbox_toggled()
        )
        self.combo_F_team_char.set(char_options[0] if char_options else "Xuất Chiến")
        self.combo_F_team_char.grid(row=1, column=1, sticky="w", pady=4)

        # 3. Tầng - menu drop Tầng (đổi tên các tầng thành Đài 1, Đài 2, Đài 3)
        self.chk_F3 = ctk.CTkCheckBox(
            grid_F_body, text="Tầng", variable=self.var_F3, command=self._on_checkbox_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            fg_color="#EA580C", hover_color="#C2410C", checkmark_color="#FFFFFF", text_color="#FFFFFF", checkbox_width=16, checkbox_height=16, border_width=2, corner_radius=5
        )
        self.chk_F3.grid(row=2, column=0, sticky="w", pady=4)

        tang_options = ["Trệt", "1 - 10", "Đài QS", "11 - 14", "Đài Rồng", "15 - 18", "Đài Hổ"]
        self.combo_F_tang = ctk.CTkOptionMenu(
            grid_F_body,
            values=tang_options,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            height=24,
            width=100,
            dynamic_resizing=False,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            command=lambda choice: self._on_checkbox_toggled()
        )
        self.combo_F_tang.set("Trệt")
        self.combo_F_tang.grid(row=2, column=1, sticky="w", pady=4)

    # --- HÀM CẬP NHẬT TRẠNG THÁI ---
    def log_info(self, message: str):
        """Cập nhật thông tin lên thanh trạng thái & ô ghi Log"""
        if hasattr(self, 'lbl_status'):
            self.lbl_status.configure(text=f"Thông báo: {message}")
        if hasattr(self, 'txt_log'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.txt_log.configure(state="normal")
            self.txt_log.insert("end", f"[{timestamp}] ℹ️ {message}\n")
            self.txt_log.see("end")
            self.txt_log.configure(state="disabled")

    def log_error(self, message: str):
        """Cập nhật lỗi lên thanh trạng thái & ô ghi Log"""
        if hasattr(self, 'lbl_status'):
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

    # --- QUÉT VÀ CẬP NHẬT DỮ LIỆU LDPLAYER (ASYNC) ---
    def refresh_ld_tabs_async(self):
        """Kích hoạt quét LDPlayer trong Thread riêng biệt tránh đơ UI"""
        if self.is_scanning:
            return

        self.is_scanning = True
        if hasattr(self, 'btn_refresh'):
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
        if hasattr(self, 'btn_refresh'):
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
            self.after(0, self.log_info, "👁️ [Bước 4/4] Mắt thần OpenCV bắt đầu quét theo dõi màn hình Chọn Máy Chủ TS Origin...")
            
            icon_server_detected = False
            start_wait = time.time()
            consecutive_matches = 0
            
            # Quét tìm ảnh login_server.png / login_redorb.png với ngưỡng 88%, yêu cầu 3 lần khớp liên tiếp (cách nhau 1 giây) để đảm bảo hình ảnh đã hiện ổn định
            while time.time() - start_wait < 60.0:
                if self.stop_requested:
                    self.stop_requested = False
                    self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                    return

                is_x, is_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_server.png", threshold=0.88)
                if is_x is None:
                    is_x, is_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_redorb.png", threshold=0.88)

                if is_x is not None and is_y is not None:
                    consecutive_matches += 1
                    if consecutive_matches >= 3:
                        icon_server_detected = True
                        elapsed = round(time.time() - start_wait, 1)
                        self.after(0, self.log_info, f"✅ Mắt thần đã xác nhận Bảng Máy Chủ hiển thị đầy đủ ổn định (khớp 3 lần liên tiếp) sau {elapsed}s!")
                        break
                else:
                    consecutive_matches = 0
                time.sleep(1.0)

            # Tọa độ neo chuẩn đo đạc trực tiếp từ ảnh thật (Nút tròn đỏ X=312, Tâm khung cuộn X=380, Y=420)
            panel_x, panel_y = 380, 420
            red_orb_x = 312 # Tọa độ X chuẩn của cột ô tròn màu đỏ

            # Tạm hoãn 1.0s sau khi nhận diện màn hình Bảng Chọn Máy Chủ
            self.after(0, self.log_info, "⏳ Mắt thần đã nhận diện Bảng Máy Chủ! Tạm hoãn 1.0s nạp hiệu ứng...")
            time.sleep(1.0)

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

            # Giai đoạn 3: Nếu cuộn hết 20 lần mà vẫn không kết nối thành công -> DỪNG LẠI
            if not found_server:
                msg = f"❌ Đã cuộn 20 lần (10 xuống, 10 lên) nhưng máy chủ '{server_name}' vẫn báo 'login_nkn.png' không vào được. Đã dừng lại!"
                self.after(0, self._finish_launch_ts_origin, False, msg)
            else:
                self.after(0, self.log_info, f"🚀 👁️ Đã chọn Máy chủ '{server_name}' trên Tab: {tab_name} (Index: {tab_index})")
                
                # 📌 Bước 5: Hoãn 3 giây khi vào màn hình game
                self.after(0, self.log_info, "⏳ [Màn hình game] Hoãn 3 giây trước khi quét giao diện...")
                time.sleep(3.0)

                if self.stop_requested:
                    self.stop_requested = False
                    self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                    return

                # 📌 Bước 6: Quét Mắt Thần OpenCV & Click nút 'login_x.png' (Nếu khớp nhấp click, không khớp chuyển bước 7)
                self.after(0, self.log_info, "👁️ [Bước 6] Mắt thần đang quét tìm nút 'login_x.png'...")
                x_x, x_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
                if x_x is not None and x_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần đã tìm thấy 'login_x.png' tại ({x_x}, {x_y})! Đang nhấp chọn...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {x_x} {x_y}"])
                    time.sleep(1.0)
                else:
                    self.after(0, self.log_info, "ℹ️ Không phát hiện nút 'login_x.png' -> Chuyển xuống Bước 7.")

                if self.stop_requested:
                    self.stop_requested = False
                    self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                    return

                # 📌 Bước 7: Quét Mắt Thần OpenCV & Click nút 'login_auto.png'
                self.after(0, self.log_info, "👁️ [Bước 7] Mắt thần đang quét tìm nút 'login_auto.png'...")
                auto_x, auto_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_auto.png", threshold=0.75)
                if auto_x is not None and auto_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần đã tìm thấy 'login_auto.png' tại ({auto_x}, {auto_y})! Đang nhấp chọn...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {auto_x} {auto_y}"])
                    time.sleep(1.0)
                else:
                    self.after(0, self.log_info, "ℹ️ Không tìm thấy ảnh 'login_auto.png' trên màn hình game.")

                # 📌 Bước 8: Hoàn tất quá trình mở game & trả lại trạng thái nút bấm
                msg = f"✅ [Hoàn thành] Đã vào game & hoàn tất quy trình khởi chạy trên Tab: {tab_name} (Index: {tab_index})"
                self.after(0, self._finish_launch_ts_origin, True, msg)

        except Exception as e:
            self.after(0, self._finish_launch_ts_origin, False, f"Lỗi khởi chạy game: {str(e)}")

    def _finish_launch_ts_origin(self, success: bool, message: str):
        """Hoàn tất quá trình mở game, trả lại trạng thái nút bấm TS Origin"""
        self.btn_enter_game.configure(state="normal", text="TS Origin")
        if success:
            self.log_info(message)
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

    # ---- HÀM XỬ LÝ NÚT CHẠY (THỰC THI 3 CARD THEO THỨ TỰ: 1. PHỤ BẢN ĐƠN/ĐỘI -> 2. BOSS TG -> 3. DỊ GIỚI) ----
    def xu_ly_nut_chay(self):
        """Khi bấm nút Chạy: Thực thi các ô check trong 3 Card (Phụ Bản Đơn/Đội, Boss TG, Dị Giới) nếu công tắc đang ON"""
        tab_name, tab_index = self._get_selected_ld_info()
        if tab_index is None:
            self.log_error("Vui lòng chọn một Tab LDPlayer trước khi bấm Chạy!")
            return

        has_active_switch = self.var_switch_E.get() or self.var_switch_C.get() or self.var_switch_B.get()
        if not has_active_switch:
            self.log_error("Vui lòng bật công tắc ON cho ít nhất 1 trong 3 Card (Phụ Bản Đơn/Đội, Boss TG, Dị Giới) trước khi bấm Chạy!")
            return

        self.stop_requested = False
        self.btn_run.configure(state="disabled", text="Đang chạy...")
        self.log_info(f"▶️ [NÚT CHẠY] Bắt đầu thực thi các Card đang bật ON theo thứ tự trên Tab: {tab_name} (Index: {tab_index})...")

        threading.Thread(target=self._worker_run_3_cards, args=(tab_name, tab_index), daemon=True).start()

    def _worker_run_3_cards(self, tab_name: str, tab_index: str):
        """Worker thread thực thi thứ tự 3 Card: 1. Phụ Bản Đơn/Đội -> 2. Boss Thế Giới -> 3. Dị Giới"""
        try:
            dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")

            if not os.path.exists(dnconsole_path):
                self.after(0, self._finish_run_3_cards, False, f"Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
                return

            # 📌 1/3: CARD PHỤ BẢN ĐƠN / ĐỘI (Card E)
            if self.var_switch_E.get() and not self.stop_requested:
                self.after(0, self.log_info, f"📌 [1/3] Đang thực thi Card Phụ Bản Đơn / Đội trên Tab: {tab_name}...")
                self._execute_card_E_phu_ban_doi(dnconsole_path, tab_name, tab_index)
                
                if not self.stop_requested:
                    if not self.var_switch_E.get():
                        self.after(0, self.log_info, "🛑 [1/3] Công tắc Card Phụ Bản Đơn / Đội gạt về OFF ➔ Đã dừng thao tác Card này!")
                    else:
                        # Thao tác xong các ô check -> Tự động nhả công tắc E & ô Tạm Dừng về OFF
                        self.var_switch_E.set(False)
                        if hasattr(self, 'var_pause_E'):
                            self.var_pause_E.set(False)
                        self.after(0, self._update_card_G_visibility)
                        self.after(0, self.save_config)
                        self.after(0, self.log_info, "✅ [1/3] Đã hoàn thành Card Phụ Bản Đơn / Đội ➔ Tự động nhả công tắc E về OFF!")

                    # Nếu có Card tiếp theo đang mở công tắc -> Hoãn 5 giây trước khi chuyển sang Card tiếp theo
                    if (self.var_switch_C.get() or self.var_switch_B.get()) and not self.stop_requested:
                        self.after(0, self.log_info, "⏳ Hoãn 5 giây trước khi chuyển sang Card tiếp theo...")
                        time.sleep(5.0)

            # 📌 2/3: CARD BOSS THẾ GIỚI (Card C)
            if self.var_switch_C.get() and not self.stop_requested:
                self.after(0, self.log_info, f"📌 [2/3] Đang thực thi Card Boss Thế Giới trên Tab: {tab_name}...")
                self._execute_card_C_boss_tg(dnconsole_path, tab_name, tab_index)
                
                if not self.stop_requested:
                    if not self.var_switch_C.get():
                        self.after(0, self.log_info, "🛑 [2/3] Công tắc Card Boss Thế Giới gạt về OFF ➔ Đã dừng thao tác Card này!")
                    else:
                        # Thao tác xong các ô check -> Tự động nhả công tắc C & ô Tạm Dừng về OFF
                        self.var_switch_C.set(False)
                        if hasattr(self, 'var_pause_C'):
                            self.var_pause_C.set(False)
                        self.after(0, self.save_config)
                        self.after(0, self.log_info, "✅ [2/3] Đã hoàn thành Card Boss Thế Giới ➔ Tự động nhả công tắc C về OFF!")

                    # Nếu có Card tiếp theo đang mở công tắc -> Hoãn 5 giây trước khi chuyển sang Card tiếp theo
                    if self.var_switch_B.get() and not self.stop_requested:
                        self.after(0, self.log_info, "⏳ Hoãn 5 giây trước khi chuyển sang Card tiếp theo...")
                        time.sleep(5.0)

            # 📌 3/3: CARD DỊ GIỚI (Card B)
            if self.var_switch_B.get() and not self.stop_requested:
                self.after(0, self.log_info, f"📌 [3/3] Đang thực thi Card Dị Giới trên Tab: {tab_name}...")
                self._execute_card_B_di_gioi(dnconsole_path, tab_name, tab_index)
                
                if not self.stop_requested:
                    if not self.var_switch_B.get():
                        self.after(0, self.log_info, "🛑 [3/3] Công tắc Card Dị Giới Đêm gạt về OFF ➔ Đã dừng thao tác Card này!")
                    else:
                        # Thao tác xong các ô check -> Tự động nhả công tắc B & ô Tạm Dừng về OFF
                        self.var_switch_B.set(False)
                        if hasattr(self, 'var_pause_B'):
                            self.var_pause_B.set(False)
                        self.after(0, self.save_config)
                        self.after(0, self.log_info, "✅ [3/3] Đã hoàn thành Card Dị Giới ➔ Tự động nhả công tắc B về OFF!")

            if self.stop_requested:
                self.after(0, self._finish_run_3_cards, False, "🛑 Tiến trình Nút Chạy đã dừng theo yêu cầu!")
            else:
                self.after(0, self._finish_run_3_cards, True, f"🎉 [HOÀN THÀNH] Nút Chạy đã hoàn tất các Card hoạt động theo thứ tự trên Tab: {tab_name}")

        except Exception as e:
            self.after(0, self._finish_run_3_cards, False, f"Lỗi tiến trình Nút Chạy: {str(e)}")

    def _finish_run_3_cards(self, success: bool, message: str):
        """Hoàn tất tiến trình nút Chạy, phục hồi nút Chạy sáng lên"""
        if hasattr(self, 'btn_run'):
            self.btn_run.configure(state="normal", text="Chạy")
        if success:
            self.log_info(message)
        else:
            self.log_error(message)

    def dung_tat_ca_hoat_dong(self):
        """Nút Dừng trong card Khởi Động: Chỉ cho phép dừng 3 card (Phụ Bản Đơn / Đội, Boss Thế Giới, Dị Giới)"""
        self.stop_requested = True
        for prefix in ["E", "C", "B"]:
            switch_attr = f"var_switch_{prefix}"
            if hasattr(self, switch_attr):
                getattr(self, switch_attr).set(False)
            pause_attr = f"var_pause_{prefix}"
            if hasattr(self, pause_attr):
                getattr(self, pause_attr).set(False)
        self.save_config()
        if hasattr(self, 'btn_run'):
            self.btn_run.configure(state="normal", text="Chạy")
        self.after(0, self.log_info, "🛑 [DỪNG KHỞI ĐỘNG] Đã bấm nút Dừng ➔ Dừng nút Chạy, ngắt tiến trình 3 card (Phụ Bản Đơn/Đội, Boss TG, Dị Giới) & trả công tắc 3 card này về OFF!")

    def _is_any_pause_active(self) -> bool:
        """Kiểm tra nếu có bất kỳ nút Tạm Dừng nào của tất cả các Card đang bật, hoặc bấm Dừng tổng"""
        if self.stop_requested:
            return True
        for prefix in ["B", "C", "D", "E", "F"]:
            pause_var = getattr(self, f"var_pause_{prefix}", None)
            if pause_var and pause_var.get():
                return True
        return False



    def _should_stop_di_gioi(self) -> bool:
        """Kiểm tra điều kiện dừng / tạm dừng cho Card 1 Dị Giới (bấm Dừng tổng, gạt công tắc B về OFF, hoặc tích ô Dừng)"""
        if self.stop_requested or not self.var_switch_B.get():
            return True
        if hasattr(self, 'var_pause_B') and self.var_pause_B.get():
            self.after(0, self.log_info, "⏸️ [DỊ GIỚI] Ô Dừng đang tích ➔ Tạm dừng tiến trình (nhả ô Dừng để chạy tiếp)...")
            while self.var_pause_B.get() and not self.stop_requested and self.var_switch_B.get():
                time.sleep(0.5)
            if not self.stop_requested and self.var_switch_B.get():
                self.after(0, self.log_info, "▶️ [DỊ GIỚI] Đã nhả ô Dừng ➔ Khôi phục chạy tiếp Dị Giới!")
        return self.stop_requested or not self.var_switch_B.get()

    def _should_stop_card_E(self) -> bool:
        """Kiểm tra điều kiện dừng / tạm dừng cho Card 2 Phụ Bản Đơn/Đội (bấm Dừng tổng, gạt công tắc E về OFF, hoặc tích ô Dừng)"""
        if self.stop_requested or not self.var_switch_E.get():
            return True
        if hasattr(self, 'var_pause_E') and self.var_pause_E.get():
            self.after(0, self.log_info, "⏸️ [PHỤ BẢN] Ô Dừng đang tích ➔ Tạm dừng tiến trình (nhả ô Dừng để chạy tiếp)...")
            while self.var_pause_E.get() and not self.stop_requested and self.var_switch_E.get():
                time.sleep(0.5)
            if not self.stop_requested and self.var_switch_E.get():
                self.after(0, self.log_info, "▶️ [PHỤ BẢN] Đã nhả ô Dừng ➔ Khôi phục chạy tiếp Phụ Bản!")
        return self.stop_requested or not self.var_switch_E.get()

    def _should_stop_card_C(self) -> bool:
        """Kiểm tra điều kiện dừng / tạm dừng cho Card 4 Boss Thế Giới (bấm Dừng tổng, gạt công tắc C về OFF, hoặc tích ô Dừng)"""
        if self.stop_requested or not self.var_switch_C.get():
            return True
        if hasattr(self, 'var_pause_C') and self.var_pause_C.get():
            self.after(0, self.log_info, "⏸️ [BOSS THẾ GIỚI] Ô Dừng đang tích ➔ Tạm dừng tiến trình (nhả ô Dừng để chạy tiếp)...")
            while self.var_pause_C.get() and not self.stop_requested and self.var_switch_C.get():
                time.sleep(0.5)
            if not self.stop_requested and self.var_switch_C.get():
                self.after(0, self.log_info, "▶️ [BOSS THẾ GIỚI] Đã nhả ô Dừng ➔ Khôi phục chạy tiếp Boss Thế Giới!")
        return self.stop_requested or not self.var_switch_C.get()

    def _on_chk_D_chuyen_khu_toggled(self):
        """Callback ô check Chuyển Khu độc lập trong Card 40 NPC"""
        self._on_checkbox_toggled()
        if self.var_D_chuyen_khu.get():
            self.after(0, self.log_info, "⚡ [40 NPC - CHUYỂN KHU] Tích ô Chuyển ➔ Thực thi thao tác chuyển khu không phụ thuộc công tắc chính!")
            threading.Thread(target=self._run_independent_chuyen_khu_worker, daemon=True).start()
        self.save_config()

    def _run_independent_chuyen_khu_worker(self):
        """Luồng độc lập thực thi chuyển khu theo Menu Khu & tự động nhả ô tích khi xong"""
        try:
            tab_info = self._get_selected_ld_info()
            if not tab_info or tab_info[0] is None:
                self.after(0, self.log_error, "⚠️ Chưa chọn Giả lập LDPlayer để Chuyển Khu!")
                return

            tab_name, tab_index = tab_info
            dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")

            if not os.path.exists(dnconsole_path):
                self.after(0, self.log_error, f"⚠️ Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
                return

            selected_khu = self.combo_D_khu.get() if hasattr(self, 'combo_D_khu') else "Cố Định"
            if selected_khu == "Cố Định":
                self.after(0, self.log_info, "ℹ️ [40 NPC - CHUYỂN KHU] Menu Khu đang chọn 'Cố Định' ➔ Bỏ qua thao tác chuyển khu.")
                return

            self.after(0, self.log_info, f"🚀 [40 NPC - CHUYỂN KHU] Kích hoạt chuyển sang '{selected_khu}' trên Tab '{tab_name}'...")
            self._run_40_npc_select_khu(dnconsole_path, str(tab_index), selected_khu, ignore_main_switch=True)
            self.after(0, self.log_info, "✅ [40 NPC - CHUYỂN KHU] Đã hoàn thành thao tác chuyển khu ➔ Tự động nhả ô tích!")
        except Exception as e:
            self.after(0, self.log_error, f"❌ Lỗi khi Chuyển Khu độc lập: {e}")
        finally:
            self.var_D_chuyen_khu.set(False)
            self.after(0, self.save_config)

    def _should_stop_card_D(self, ignore_main_switch: bool = False) -> bool:
        """Kiểm tra điều kiện dừng / tạm dừng cho Card 5 40 NPC (độc lập với nút Dừng Khởi Động)"""
        if ignore_main_switch:
            if hasattr(self, 'var_D_chuyen_khu') and not self.var_D_chuyen_khu.get():
                return True
        else:
            if not self.var_switch_D.get():
                return True

        if hasattr(self, 'var_pause_D') and self.var_pause_D.get():
            self.after(0, self.log_info, "⏸️ [40 NPC] Ô Dừng đang tích ➔ Tạm dừng tiến trình (nhả ô Dừng để chạy tiếp)...")
            while self.var_pause_D.get() and (ignore_main_switch or self.var_switch_D.get()):
                time.sleep(0.5)
            if ignore_main_switch or self.var_switch_D.get():
                self.after(0, self.log_info, "▶️ [40 NPC] Đã nhả ô Dừng ➔ Khôi phục chạy tiếp 40 NPC!")

        if ignore_main_switch:
            return hasattr(self, 'var_D_chuyen_khu') and not self.var_D_chuyen_khu.get()
        return not self.var_switch_D.get()

    def _should_stop_card_F(self) -> bool:
        """Kiểm tra điều kiện dừng / tạm dừng cho Card 6 Nhị Kiều (độc lập với nút Dừng Khởi Động)"""
        if not self.var_switch_F.get():
            return True
        if hasattr(self, 'var_pause_F') and self.var_pause_F.get():
            self.after(0, self.log_info, "⏸️ [NHỊ KIỀU] Ô Dừng đang tích ➔ Tạm dừng tiến trình (nhả ô Dừng để chạy tiếp)...")
            while self.var_pause_F.get() and self.var_switch_F.get():
                time.sleep(0.5)
            if self.var_switch_F.get():
                self.after(0, self.log_info, "▶️ [NHỊ KIỀU] Đã nhả ô Dừng ➔ Khôi phục chạy tiếp Nhị Kiều!")
        return not self.var_switch_F.get()

    def _handle_pipeline_stop(self):
        """Xử lý dừng luồng an toàn khi bấm nút Dừng"""
        self.stop_requested = False
        self.after(0, self.log_info, "🛑 Đã dừng tiến trình tuần tự các hoạt động theo yêu cầu!")

    def _run_safezone_di_gioi(self, dnconsole_path: str, tab_index: str, px_x: int, px_y: int):
        """QUY TRÌNH VỀ KHU AN TOÀN CHO CARD DỊ GIỚI (Cập nhật thao tác chuẩn theo Card Boss TG)"""
        if self._should_stop_di_gioi(): return
        self.after(0, self.log_info, "👁️ Quét tìm nút 'login_x.png' để đóng bảng quảng cáo/thông báo...")
        lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
        if lx_x is not None and lx_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'login_x.png' tại ({lx_x}, {lx_y})! Click chọn ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
            time.sleep(0.4)

        if self._should_stop_di_gioi(): return
        self.after(0, self.log_info, "👁️ [Dị Giới - Về Khu An Toàn] Quét tìm nút Vị Trí 'a_vitri.png' (85%)...")
        v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
        if v_x is not None and v_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_vitri.png' tại ({v_x}, {v_y})! Tap click trực tiếp ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, f"👉 Chưa thấy 'a_vitri.png' ➔ Click nút xanh lá góc dưới phải ({px_x}, {px_y}) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
            time.sleep(0.4)
            if self._should_stop_di_gioi(): return
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y})! Tap click trực tiếp ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'a_vitri.png' trong bảng menu.")

        if self._should_stop_di_gioi(): return
        self.after(0, self.log_info, "👉 Click liên tục (435, 250) mỗi 0.5s cho đến khi xuất hiện nút Có 'card_c/c_co.png' (85%)...")
        while not self._should_stop_di_gioi():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_co.png", threshold=0.85)
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút Có 'card_c/c_co.png' tại ({co_x}, {co_y})! Dừng click (435, 250).")
                break
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 435 250"])
            time.sleep(0.5)

        if self._should_stop_di_gioi(): return
        self.after(0, self.log_info, "👁️ Click liên tục nút Có 'card_c/c_co.png' (0.5s mỗi lần) cho tới khi hết ảnh...")
        while not self._should_stop_di_gioi():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_co.png", threshold=0.85)
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút Có 'card_c/c_co.png' tại ({co_x}, {co_y}) ➔ Click vào vị trí ảnh...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {co_x} {co_y}"])
                time.sleep(0.5)
            else:
                self.after(0, self.log_info, "ℹ️ Không còn thấy ảnh nút Có 'card_c/c_co.png' ➔ Hoàn thành Về Khu An Toàn!")
                break

        if self._should_stop_di_gioi(): return
        self.after(0, self.log_info, "⏳ [Dị Giới - Về Khu An Toàn] Hoãn 3.0s trước khi quét kiểm tra lại nút 'a_vitri.png'...")
        time.sleep(3.0)

        if self._should_stop_di_gioi(): return
        self.after(0, self.log_info, "👁️ [Dị Giới - Về Khu An Toàn] Quét kiểm tra lại nút 'a_vitri.png' (85%)...")
        v_check_x, v_check_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
        if v_check_x is not None and v_check_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_vitri.png' vẫn còn tại ({v_check_x}, {v_check_y}) ➔ Click ({px_x}, {px_y}) để thu gọn menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "ℹ️ Không thấy nút 'a_vitri.png' ➔ Bỏ qua thu gọn menu.")

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
            self.after(0, self.log_info, "👉 Chưa thấy map 'a_digioi.png' ➔ Thực hiện thao tác Về Vùng An Toàn trước khi vào Dị Giới...")
            self._run_safezone_di_gioi(dnconsole_path, tab_index, px_x, px_y)

            if self._should_stop_di_gioi(): return
            self.after(0, self.log_info, "👉 Tiến hành quét nút Vị Trí 'a_vitri.png' để vào Dị Giới...")
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y})! Nhấp chọn ngay ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, f"👉 Chưa thấy 'a_vitri.png' ➔ Click nút xanh lá góc dưới phải tại ({px_x}, {px_y}) để mở menu ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
                time.sleep(0.4)
                if self._should_stop_di_gioi(): return
                v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
                if v_x is not None and v_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y})! Đang nhấp chọn ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                    time.sleep(0.4)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'a_vitri.png' trong bảng menu.")

            if self._should_stop_di_gioi(): return

            self.after(0, self.log_info, f"👉 Click chọn tọa độ ({v1_x}, {v1_y}) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v1_x} {v1_y}"])
            time.sleep(0.4)

            if self._should_stop_di_gioi(): return

            self.after(0, self.log_info, f"👉 Click chọn tọa độ ({v2_x}, {v2_y}) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v2_x} {v2_y}"])
            time.sleep(0.4)

            if self._should_stop_di_gioi(): return
            self.after(0, self.log_info, "⏳ [DỊ GIỚI] Hoãn 3 giây sau khi đưa nhân vật vào map Dị Giới...")
            for _ in range(3):
                if self._should_stop_di_gioi(): return
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
                    time.sleep(1.0)

            if self._should_stop_di_gioi(): return

            self.after(0, self.log_info, "▶️ [DỊ GIỚI - 22H50] Đã đến 22H50! Bắt đầu thao tác tắt Ký Lục...")

            # Quét tìm biểu tượng a_ai.png (độ chính xác 85%)
            ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
            if ai_x is not None and ai_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Nhấp chọn ngay ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, f"👉 Chưa thấy 'a_ai.png' ➔ Click nút xanh lá góc dưới phải tại ({px_x}, {px_y}) để mở menu ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
                time.sleep(0.4)
                if self._should_stop_di_gioi(): return
                ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
                if ai_x is not None and ai_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Đang nhấp chọn ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
                    time.sleep(0.4)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'a_ai.png' trong bảng menu.")

            if self._should_stop_di_gioi(): return

            self.after(0, self.log_info, f"👉 Click tọa độ Cài Đặt AI ({c_x}, {c_y}) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {c_x} {c_y}"])
            time.sleep(0.4)

            if self._should_stop_di_gioi(): return

            # Quét ảnh mẫu a_kyluc.png (độ chính xác 95%)
            self.after(0, self.log_info, "👁️ Quét kiểm tra ảnh mẫu 'a_kyluc.png' (độ chính xác 95%)...")
            kl_x, kl_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_kyluc.png", threshold=0.95)
            if kl_x is None:
                self.after(0, self.log_info, f"🎯 Giao diện KHÔNG KHỚP ảnh 'a_kyluc.png' (Đang Bật) ➔ Click vị trí Ký Lục tại ({kl_tap_x}, {kl_tap_y}) để Tắt ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {kl_tap_x} {kl_tap_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "ℹ️ Giao diện ĐÃ KHỚP ảnh mẫu 'a_kyluc.png' (Đã Tắt sẵn) ➔ Bỏ qua.")

            if self._should_stop_di_gioi(): return

            self.after(0, self.log_info, f"👉 Click tọa độ xác nhận/đóng ({end_x}, {end_y}) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {end_x} {end_y}"])
            time.sleep(0.4)

            self.after(0, self.log_info, f"👉 Click lại nút xanh lá ({px_x}, {px_y}) để thu gọn bảng menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
            time.sleep(0.4)

            # 2. Tiếp tục đếm đến 00H05 (qua ngày mới)
            now = datetime.now()
            target_0005 = now.replace(hour=0, minute=5, second=0, microsecond=0)
            if now >= target_0005:
                target_0005 += timedelta(days=1)

            self.after(0, self.log_info, f"⏳ [DỊ GIỚI] Tiếp tục đếm giờ chờ đến 00H05 ngày mới (Hiện tại: {now.strftime('%H:%M:%S')})...")
            while datetime.now() < target_0005:
                if self._should_stop_di_gioi():
                    return
                time.sleep(1.0)

        if self._should_stop_di_gioi(): return

        # =========================================================================
        # 📌 4. VÀO DỊ GIỚI (LÚC 00H05) & BẬT KÝ LỤC (Nếu TÍCH ô Dị Giới Đêm)
        # =========================================================================
        if has_di_gioi:
            self.after(0, self.log_info, "🚀 [DỊ GIỚI - 00H05] Kích hoạt quy trình Vào Dị Giới (00H05) của Card Dị Giới Đêm...")

            # 📌 Quét nhận diện map Dị Giới 'a_digioi.png' (85%)
            if self._should_stop_di_gioi(): return
            self.after(0, self.log_info, "👁️ [DỊ GIỚI - 00H05] Quét nhận diện map Dị Giới 'a_digioi.png' (85%)...")
            dg_x00, dg_y00 = self._find_template_on_screen(dnconsole_path, tab_index, "a_digioi.png", threshold=0.85)
            if dg_x00 is not None and dg_y00 is not None:
                self.after(0, self.log_info, f"🎯 Đã phát hiện map Dị Giới 'a_digioi.png' tại ({dg_x00}, {dg_y00}) ➔ Bỏ qua các bước từ 4.1 đến 4.4.")
            else:
                self.after(0, self.log_info, "👉 Chưa thấy map 'a_digioi.png' ➔ Thực hiện các bước 4.1 đến 4.4 để vào lại Dị Giới...")
                # 4.1: Quét tìm biểu tượng a_vitri.png (85%)
                v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
                if v_x is not None and v_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y})! Nhấp chọn ngay ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                    time.sleep(0.4)
                else:
                    self.after(0, self.log_info, f"👉 Chưa thấy 'a_vitri.png' ➔ Click nút xanh lá góc dưới phải tại ({px_x}, {px_y}) để mở menu ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
                    time.sleep(0.4)
                    if self._should_stop_di_gioi(): return
                    v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
                    if v_x is not None and v_y is not None:
                        self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y})! Đang nhấp chọn ➔ Hoãn 0.4s...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                        time.sleep(0.4)
                    else:
                        self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'a_vitri.png' trong bảng menu.")

                if self._should_stop_di_gioi(): return
                # 4.2: Tap điểm 1
                self.after(0, self.log_info, f"👉 [4.2] Click chọn tọa độ ({v1_x}, {v1_y}) ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v1_x} {v1_y}"])
                time.sleep(0.4)

                if self._should_stop_di_gioi(): return
                # 4.3: Tap điểm 2
                self.after(0, self.log_info, f"👉 [4.3] Click chọn tọa độ ({v2_x}, {v2_y}) ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v2_x} {v2_y}"])
                time.sleep(0.4)

                if self._should_stop_di_gioi(): return
                # 4.4: Hoãn 3s vào lại map
                self.after(0, self.log_info, "⏳ [4.4] Hoãn 3 giây sau khi vào lại map Dị Giới...")
                for _ in range(3):
                    if self._should_stop_di_gioi(): return
                    time.sleep(1.0)

            # Tự động Bật Ký Lục dù ô check Ký Lục có đang Mở hay Tắt (4.5 đến 4.9)
            if self._should_stop_di_gioi(): return
            self.after(0, self.log_info, "▶️ [DỊ GIỚI - 00H05 - 4.5] Tự động kích hoạt BẬT KÝ LỤC...")
            ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
            if ai_x is not None and ai_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Nhấp chọn ngay ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, f"👉 Chưa thấy 'a_ai.png' ➔ Click nút xanh lá góc dưới phải tại ({px_x}, {px_y}) để mở menu ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
                time.sleep(0.4)
                if self._should_stop_di_gioi(): return
                ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
                if ai_x is not None and ai_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Đang nhấp chọn ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
                    time.sleep(0.4)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'a_ai.png' trong bảng menu.")

            if self._should_stop_di_gioi(): return
            self.after(0, self.log_info, f"👉 [4.6] Click tọa độ Cài đặt ({c_x}, {c_y}) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {c_x} {c_y}"])
            time.sleep(0.4)

            if self._should_stop_di_gioi(): return
            self.after(0, self.log_info, "👁️ [4.7] Quét kiểm tra ảnh mẫu 'a_kyluc.png' (ngưỡng 95%)...")
            kl_x, kl_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_kyluc.png", threshold=0.95)
            if kl_x is not None and kl_y is not None:
                self.after(0, self.log_info, f"🎯 Giao diện ĐÃ KHỚP ảnh mẫu 'a_kyluc.png' (Đang Tắt) ➔ Click vào ({kl_tap_x}, {kl_tap_y}) để Bật Ký Lục ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {kl_tap_x} {kl_tap_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "ℹ️ Giao diện KHÔNG KHỚP ảnh mẫu 'a_kyluc.png' (Đã Bật sẵn) ➔ Bỏ qua.")

            if self._should_stop_di_gioi(): return
            self.after(0, self.log_info, f"👉 [4.8] Click tọa độ đóng ({end_x}, {end_y}) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {end_x} {end_y}"])
            time.sleep(0.4)

            self.after(0, self.log_info, f"👉 [4.9] Click nút xanh lá ({px_x}, {px_y}) để thu gọn menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
            time.sleep(0.4)

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
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Nhấp chọn ngay ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, f"1. Click mở lại bảng menu tại ({px_x}, {px_y}) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
            time.sleep(0.4)
            if self._should_stop_di_gioi(): return
            ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
            if ai_x is not None and ai_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Đang nhấp chọn ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
                time.sleep(0.4)

        self.after(0, self.log_info, "3. Quét kiểm tra ảnh mẫu 'a_phucthan.png' (ngưỡng 95%)...")
        pt_x, pt_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_phucthan.png", threshold=0.95)
        if has_phuc_than:
            if pt_x is not None and pt_y is not None:
                self.after(0, self.log_info, f"🎯 [BẬT] Giao diện ĐÃ KHỚP ảnh mẫu 'a_phucthan.png' (Đang Tắt) ➔ Click vào ({pt_tap_x}, {pt_tap_y}) để Bật Phúc Thần ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {pt_tap_x} {pt_tap_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "ℹ️ [BẬT] Giao diện KHÔNG KHỚP ảnh mẫu 'a_phucthan.png' (Đã Bật sẵn) ➔ Bỏ qua.")
        else:
            if pt_x is not None and pt_y is not None:
                self.after(0, self.log_info, "ℹ️ [TẮT] Giao diện ĐÃ KHỚP ảnh mẫu 'a_phucthan.png' (Đã Tắt sẵn) ➔ Bỏ qua để Tắt Phúc Thần.")
            else:
                self.after(0, self.log_info, f"🎯 [TẮT] Giao diện KHÔNG KHỚP ảnh mẫu 'a_phucthan.png' (Đang Bật) ➔ Click vào ({pt_tap_x}, {pt_tap_y}) để Tắt Phúc Thần ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {pt_tap_x} {pt_tap_y}"])
                time.sleep(0.4)

        self.after(0, self.log_info, f"5. Click vào tọa độ ({end_x}, {end_y}) đóng bảng ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {end_x} {end_y}"])
        time.sleep(0.4)

        self.after(0, self.log_info, f"6. Click lại nút xanh lá ({px_x}, {px_y}) để thu gọn menu ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
        time.sleep(0.4)

        if has_phuc_than:
            self.after(0, self.log_info, "7. Hoàn thành thao tác Phúc Thần (giữ nguyên ô tích).")

        # Ô Ký Lục:
        if self._should_stop_di_gioi(): return
        self.after(0, self.log_info, f"▶️ [KÝ LỤC] Kiểm tra ô Ký Lục (Trạng thái: {'ĐƯỢC TÍCH' if has_ky_luc else 'KHÔNG TÍCH'})...")
        ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
        if ai_x is not None and ai_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Nhấp chọn ngay ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, f"1. Click mở lại bảng menu tại ({px_x}, {px_y}) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
            time.sleep(0.4)
            if self._should_stop_di_gioi(): return
            ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
            if ai_x is not None and ai_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Đang nhấp chọn ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
                time.sleep(0.4)

        self.after(0, self.log_info, f"3. Click tiếp vào tọa độ Cài đặt ({c_x}, {c_y}) ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {c_x} {c_y}"])
        time.sleep(0.4)

        self.after(0, self.log_info, "4. Quét kiểm tra ảnh mẫu 'a_kyluc.png' (ngưỡng 95%)...")
        kl_x, kl_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_kyluc.png", threshold=0.95)
        if has_ky_luc:
            if kl_x is not None and kl_y is not None:
                self.after(0, self.log_info, f"🎯 [BẬT] Giao diện ĐÃ KHỚP ảnh mẫu 'a_kyluc.png' (Đang Tắt) ➔ Click vào ({kl_tap_x}, {kl_tap_y}) để Bật Ký Lục ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {kl_tap_x} {kl_tap_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "ℹ️ [BẬT] Giao diện KHÔNG KHỚP ảnh mẫu 'a_kyluc.png' (Đã Bật sẵn) ➔ Bỏ qua.")
        else:
            if kl_x is not None and kl_y is not None:
                self.after(0, self.log_info, "ℹ️ [TẮT] Giao diện ĐÃ KHỚP ảnh mẫu 'a_kyluc.png' (Đã Tắt sẵn) ➔ Bỏ qua để Tắt Ký Lục.")
            else:
                self.after(0, self.log_info, f"🎯 [TẮT] Giao diện KHÔNG KHỚP ảnh mẫu 'a_kyluc.png' (Đang Bật) ➔ Click vào ({kl_tap_x}, {kl_tap_y}) để Tắt Ký Lục ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {kl_tap_x} {kl_tap_y}"])
                time.sleep(0.4)

        self.after(0, self.log_info, f"5. Click vào tọa độ ({end_x}, {end_y}) đóng bảng Cài Đặt ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {end_x} {end_y}"])
        time.sleep(0.4)

        self.after(0, self.log_info, f"6. Click lại nút xanh lá ({px_x}, {px_y}) để thu gọn menu ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
        time.sleep(0.4)

        if has_ky_luc:
            self.after(0, self.log_info, "7. Hoàn thành thao tác Ký Lục (giữ nguyên ô tích).")

        # Ô Rút Gọn:
        if self._should_stop_di_gioi(): return
        self.after(0, self.log_info, f"▶️ [RÚT GỌN] Kiểm tra ô Rút Gọn (Trạng thái: {'ĐƯỢC TÍCH' if has_rut_gon else 'KHÔNG TÍCH'})...")
        ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
        if ai_x is not None and ai_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Nhấp chọn ngay ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, f"1. Click mở lại bảng menu tại ({px_x}, {px_y}) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
            time.sleep(0.4)
            if self._should_stop_di_gioi(): return
            ai_x, ai_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_ai.png", threshold=0.85)
            if ai_x is not None and ai_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút 'a_ai.png' tại ({ai_x}, {ai_y})! Đang nhấp chọn ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {ai_x} {ai_y}"])
                time.sleep(0.4)

        if self._should_stop_di_gioi(): return
        self.after(0, self.log_info, f"2. Click Cài đặt tại ({c_x}, {c_y}) ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {c_x} {c_y}"])
        time.sleep(0.4)

        self.after(0, self.log_info, "3. Quét kiểm tra ảnh mẫu 'a_rutgon.png' (ngưỡng 95%)...")
        rg_x, rg_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_rutgon.png", threshold=0.95)
        if has_rut_gon:
            if rg_x is not None and rg_y is not None:
                self.after(0, self.log_info, f"🎯 [BẬT] Giao diện ĐÃ KHỚP ảnh mẫu 'a_rutgon.png' (Đang Tắt) ➔ Click vào ({rg_tap_x}, {rg_tap_y}) để Bật Rút Gọn ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {rg_tap_x} {rg_tap_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "ℹ️ [BẬT] Giao diện KHÔNG KHỚP ảnh mẫu 'a_rutgon.png' (Đã Bật sẵn) ➔ Bỏ qua.")
        else:
            if rg_x is not None and rg_y is not None:
                self.after(0, self.log_info, "ℹ️ [TẮT] Giao diện ĐÃ KHỚP ảnh mẫu 'a_rutgon.png' (Đã Tắt sẵn) ➔ Bỏ qua để Tắt Rút Gọn.")
            else:
                self.after(0, self.log_info, f"🎯 [TẮT] Giao diện KHÔNG KHỚP ảnh mẫu 'a_rutgon.png' (Đang Bật) ➔ Click vào ({rg_tap_x}, {rg_tap_y}) để Tắt Rút Gọn ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {rg_tap_x} {rg_tap_y}"])
                time.sleep(0.4)

        self.after(0, self.log_info, f"5. Click vào tọa độ ({end_x}, {end_y}) đóng bảng Cài Đặt ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {end_x} {end_y}"])
        time.sleep(0.4)

        self.after(0, self.log_info, f"6. Click lại nút xanh lá ({px_x}, {px_y}) để thu gọn menu ➔ Hoãn 0.4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px_x} {px_y}"])
        time.sleep(0.4)

        if has_rut_gon:
            self.after(0, self.log_info, "7. Hoàn thành thao tác Rút Gọn (giữ nguyên ô tích).")

        # =========================================================================
        # 📌 6. QUÉT CLICK NÚT AI TÌM ('a_aitim.png') SAU KHI HOÀN THÀNH BƯỚC 5
        # =========================================================================
        if self._should_stop_di_gioi(): return
        self.after(0, self.log_info, "▶️ [DỊ GIỚI - Bước 6] Quét kiểm tra nút AI Tìm 'a_aitim.png' (75%) liên tục trong 5.0s...")
        aitim_x, aitim_y = None, None
        for _ in range(10):
            if self._should_stop_di_gioi(): return
            aitim_x, aitim_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_aitim.png", threshold=0.75)
            if aitim_x is not None and aitim_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút AI Tìm 'a_aitim.png' tại ({aitim_x}, {aitim_y})! Click chọn ngay ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {aitim_x} {aitim_y}"])
                time.sleep(0.4)
                break
            time.sleep(0.5)

        if aitim_x is None or aitim_y is None:
            if self._should_stop_di_gioi(): return
            self.after(0, self.log_info, "⚠️ Không phát hiện thấy ảnh 'a_aitim.png' sau 5.0s ➔ Tiến hành Thoát Game...")
            # Đóng ứng dụng game trên LDPlayer (Bỏ hoãn 1s dư thừa)
            self._exec_cmd([dnconsole_path, "killapp", "--index", str(tab_index)])
            for pkg in ["com.chinesegamer.tsotw", "com.chinesegamer.tsorigin", "com.vng.tsorigin", "com.vtc.tsorigin"]:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell am force-stop {pkg}"])
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input keyevent 3"])

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

        is_doi_direct_mode = self.var_E_doi.get() and not self.var_switch_G.get()

        # =========================================================================
        # 📌 VỀ KHU AN TOÀN (SAFE ZONE RETURN)
        # =========================================================================
        if not (is_doi_direct_mode and not don_active):
            # 1. Quét tìm nút Vị Trí (a_vitri.png):
            # Mắt Thần quét ảnh nút login_x.png, nếu thấy sẽ nhấp chọn để đóng bảng quảng cáo/thông báo
            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "👁️ Quét tìm nút 'login_x.png' để đóng bảng quảng cáo/thông báo...")
            lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
            if lx_x is not None and lx_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'login_x.png' tại ({lx_x}, {lx_y})! Click chọn để đóng quảng cáo/thông báo ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                time.sleep(0.4)

            # Quét Mắt Thần OpenCV tìm a_vitri.png (độ chính xác 85%)
            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "👁️ [Phụ Bản - Về Khu An Toàn] Quét tìm nút Vị Trí 'a_vitri.png' (85%)...")
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_vitri.png' tại ({v_x}, {v_y})! Tap click trực tiếp ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "👉 Chưa thấy 'a_vitri.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(0.4)
                if self._should_stop_card_E(): return
                v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
                if v_x is not None and v_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y})! Tap click trực tiếp ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                    time.sleep(0.4)
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

            # Quét Mắt Thần nút a_vitri.png (85%): Hoãn 3.0s trước khi kiểm tra lại
            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "⏳ [Về Khu An Toàn] Hoãn 3.0s trước khi quét kiểm tra lại nút 'a_vitri.png'...")
            time.sleep(3.0)

            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "👁️ Quét Mắt Thần kiểm tra nút 'a_vitri.png' (85%)...")
            v_check_x, v_check_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
            if v_check_x is not None and v_check_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_vitri.png' tại ({v_check_x}, {v_check_y}) ➔ Click (1213, 648) thu gọn/mở menu ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "ℹ️ Không thấy nút 'a_vitri.png' ➔ Bỏ qua.")

        # ---------------- 1. XỬ LÝ MỤC PHỤ BẢN ĐƠN (CÁ NHÂN) ----------------
        if don_active:
            if self._should_stop_card_E(): return
            selected_char_don = self.combo_E_don_char.get() if hasattr(self, 'combo_E_don_char') else "Xuất Chiến"
            self.after(0, self.log_info, f"⚙️ [Phụ Bản Đơn] Bắt đầu quy trình ô Cá Nhân - Vị trí: '{selected_char_don}' ➔ Hoãn 0.4s...")
            time.sleep(0.4)

            # --- Bước 1: Tìm ảnh b_doi.png (Nếu 'Xuất Chiến' được chọn -> BỎ QUA Bước 1) ---
            if selected_char_don != "Xuất Chiến":
                if self._should_stop_card_E(): return
                self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 1] Quét tìm ảnh 'b_doi.png' trong folder 'card_b'...")
                b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
                if b_doi_x is not None and b_doi_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                    time.sleep(0.4)
                else:
                    self.after(0, self.log_info, "👉 Chưa thấy 'b_doi.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                    time.sleep(0.4)
                    if self._should_stop_card_E(): return
                    b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
                    if b_doi_x is not None and b_doi_y is not None:
                        self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                        time.sleep(0.4)
                    else:
                        self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_doi.png' trong bảng menu.")
            else:
                self.after(0, self.log_info, "ℹ️ Vị trí 'Xuất Chiến' được chọn ➔ Bỏ qua Bước 1 (không click 'b_doi.png').")

            # --- Bước 2: Thao tác theo từng vị trí trong Menu thả xuống ---
            if self._should_stop_card_E(): return
            self.after(0, self.log_info, f"⚙️ [Phụ Bản Đơn - Bước 2] Chế độ vị trí chọn: '{selected_char_don}'")
            if selected_char_don == "Xuất Chiến":
                self.after(0, self.log_info, "ℹ️ Vị trí 'Xuất Chiến': Không có hành động ở Bước 2, chuyển tiếp xuống Bước 3.")
            elif selected_char_don == "Vị Trí 1":
                self.after(0, self.log_info, "👉 [Vị Trí 1] Click (560, 520) ➔ (560, 255) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.5)
            elif selected_char_don == "Vị Trí 2":
                self.after(0, self.log_info, "👉 [Vị Trí 2] Click (560, 520) ➔ (560, 340) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.5)
            elif selected_char_don == "Vị Trí 3":
                self.after(0, self.log_info, "👉 [Vị Trí 3] Click (560, 520) ➔ (560, 430) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
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
            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 3] Quét tìm ảnh 'b_pb.png' trong folder 'card_b'...")
            b_pb_x, b_pb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85)
            if b_pb_x is not None and b_pb_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_pb.png' tại ({b_pb_x}, {b_pb_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x} {b_pb_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "👉 Chưa thấy 'b_pb.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(0.4)
                if self._should_stop_card_E(): return
                b_pb_x, b_pb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85)
                if b_pb_x is not None and b_pb_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_pb.png' tại ({b_pb_x}, {b_pb_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x} {b_pb_y}"])
                    time.sleep(0.4)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_pb.png' trong bảng menu.")

            # --- Quét card_b/b_lsknn.png khi hoàn thành các thao tác Quét card_b/b_pb.png ---
            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 3] Quét kiểm tra ảnh 'card_b/b_lsknn.png'...")
            lsknn_x, lsknn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_lsknn.png", threshold=0.85)
            if lsknn_x is not None and lsknn_y is not None:
                self.after(0, self.log_info, f"🎯 Khớp ảnh 'b_lsknn.png' tại ({lsknn_x}, {lsknn_y}) ➔ Click tọa độ (350, 585) ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 350 585"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "ℹ️ Không khớp ảnh 'b_lsknn.png' ➔ Bỏ qua.")

            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "👉 Click tọa độ (240, 500) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 240 500"])
            time.sleep(0.4)

            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "👉 Click tiếp tọa độ (775, 575) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 775 575"])
            time.sleep(0.4)

            # --- Quét nhận diện Xác Nhận: card_b/b_xn.png (Chờ 5s & Quét liên tục tới khi thấy) ---
            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "⏳ [Phụ Bản Đơn - Bước 3] Chờ 5 giây trước khi quét tìm nút Xác Nhận...")
            for _ in range(5):
                if self._should_stop_card_E(): return
                time.sleep(1.0)

            self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 3] Quét tìm ảnh mẫu 'card_b/b_xn.png' (Lặp lại cho tới khi phát hiện)...")
            xn_x, xn_y = None, None
            while not self._should_stop_card_E():
                xn_x, xn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_xn.png", threshold=0.85)
                if xn_x is not None and xn_y is not None:
                    break
                self.after(0, self.log_info, "⏳ Chưa phát hiện 'card_b/b_xn.png' ➔ Tiếp tục quét lại sau 1.5s...")
                time.sleep(1.5)

            if self._should_stop_card_E(): return

            if xn_x is not None and xn_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_xn.png' tại ({xn_x}, {xn_y}) ➔ Click 2 lần (cách nhau 0.8s) vào ảnh 'b_xn.png' ➔ Tạm dừng 3.0s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x} {xn_y}"])
                time.sleep(0.8)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x} {xn_y}"])
                time.sleep(3.0)

            # --- Bước 4: Quy trình Bước 4 (Bỏ 4.1 và 4.2) ---
            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "🚀 [Phụ Bản Đơn - Bước 4] Khởi chạy Bước 4...")

            # 4.3: Quét nhận diện Phụ Bản & Vào màn
            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 4.3] Quét tìm ảnh 'b_pb.png'...")
            b_pb_x4, b_pb_y4 = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85)
            if b_pb_x4 is not None and b_pb_y4 is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_pb.png' tại ({b_pb_x4}, {b_pb_y4})! Click vào ảnh ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x4} {b_pb_y4}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "👉 Chưa thấy 'b_pb.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(0.4)
                if self._should_stop_card_E(): return
                b_pb_x4, b_pb_y4 = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85)
                if b_pb_x4 is not None and b_pb_y4 is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_pb.png' tại ({b_pb_x4}, {b_pb_y4})! Click vào ảnh ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x4} {b_pb_y4}"])
                    time.sleep(0.4)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_pb.png' trong bảng menu.")

            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "👉 Click tiếp tọa độ (240, 500) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 240 500"])
            time.sleep(0.4)

            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "👉 Click tiếp tọa độ (640, 575) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 640 575"])
            time.sleep(0.4)

            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "👉 Click nút thực thi tại tọa độ (775, 575) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 775 575"])
            time.sleep(0.4)

            # 4.4: Chờ 5 giây (có kiểm tra trạng thái dừng)
            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "⏳ [Phụ Bản Đơn - Bước 4.4] Chờ 5 giây nạp trận đánh...")
            for _ in range(5):
                if self._should_stop_card_E(): return
                time.sleep(1.0)

            # 4.5: Vòng lặp quét liên tục ảnh card_b/b_xn.png cho tới khi tìm thấy (mỗi 1.5s)
            if self._should_stop_card_E(): return
            self.after(0, self.log_info, "👁️ [Phụ Bản Đơn - Bước 4.5] Quét tìm ảnh mẫu 'card_b/b_xn.png' (mỗi 1.5s)...")
            xn_x4, xn_y4 = None, None
            while not self._should_stop_card_E():
                xn_x4, xn_y4 = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_xn.png", threshold=0.85)
                if xn_x4 is not None and xn_y4 is not None:
                    break
                self.after(0, self.log_info, "⏳ Chưa phát hiện 'card_b/b_xn.png' ➔ Tiếp tục quét lại sau 1.5s...")
                time.sleep(1.5)

            if self._should_stop_card_E(): return

            if xn_x4 is not None and xn_y4 is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện ảnh 'b_xn.png' tại ({xn_x4}, {xn_y4}) ➔ Click 2 lần (cách nhau 0.5s) vào ảnh 'b_xn.png'...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x4} {xn_y4}"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x4} {xn_y4}"])
                time.sleep(3.0)
        else:
            self.after(0, self.log_info, "ℹ️ [Phụ Bản Đơn] Ô check 'Đơn' KHÔNG ĐƯỢC TÍCH (OFF) -> Bỏ qua không chạy Phụ Bản Đơn.")

        # ---------------- 2. XỬ LÝ MỤC PHỤ BẢN ĐỘI (PB 20 - PB 110 & CLICK) ----------------
        dungeons_to_run = [
            ("PB 20", self.var_E1, (240, 275), 55),
            ("PB 50", self.var_E2, (240, 330), 85),
            ("PB 80", self.var_E3, (240, 380), 115),
            ("PB 110", self.var_E4, (240, 435), 265)
        ]

        any_pb_checked = any(var_pb.get() for _, var_pb, _, _ in dungeons_to_run)
        is_click_checked = self.var_E5.get()
        team_mode_active = self.var_E_canhan.get() or self.var_E_doi.get()

        if team_mode_active and (any_pb_checked or is_click_checked):
            if self._should_stop_card_E(): return
            selected_char_team = self.combo_E_team_char.get() if hasattr(self, 'combo_E_team_char') else "Xuất Chiến"
            mode_label = "Cá Nhân" if self.var_E_canhan.get() else "Tổ Đội"
            self.after(0, self.log_info, f"⚙️ [Phụ Bản Đội - {mode_label}] Kích hoạt quy trình Phụ Bản Đội (Vị trí: '{selected_char_team}')...")

            # --- Bước 1: Mở Menu & Quét chọn Đội (Nếu 'Xuất Chiến' được chọn -> BỎ QUA Bước 1) ---
            if selected_char_team != "Xuất Chiến":
                if self._should_stop_card_E(): return
                self.after(0, self.log_info, "👁️ [Phụ Bản Đội - Bước 1] Quét tìm ảnh 'b_doi.png' trong folder 'card_b'...")
                b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
                if b_doi_x is not None and b_doi_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện 'b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                    time.sleep(0.4)
                else:
                    self.after(0, self.log_info, "👉 Chưa thấy 'b_doi.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                    time.sleep(0.4)
                    if self._should_stop_card_E(): return
                    b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
                    if b_doi_x is not None and b_doi_y is not None:
                        self.after(0, self.log_info, f"🎯 Phát hiện 'b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                        time.sleep(0.4)
                    else:
                        self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_doi.png' trong bảng menu.")
            else:
                self.after(0, self.log_info, "ℹ️ Vị trí 'Xuất Chiến' được chọn ➔ Bỏ qua Bước 1 (không click 'b_doi.png').")

            # --- Bước 2: Chuyển đổi Vị Trí Nhân Vật ---
            if self._should_stop_card_E(): return
            self.after(0, self.log_info, f"⚙️ [Phụ Bản Đội - Bước 2] Chế độ vị trí chọn: '{selected_char_team}'")
            if selected_char_team == "Xuất Chiến":
                self.after(0, self.log_info, "ℹ️ Vị trí 'Xuất Chiến': Không có hành động ở Bước 2, chuyển tiếp xuống Bước 3.")
            elif selected_char_team == "Vị Trí 1":
                self.after(0, self.log_info, "👉 [Vị Trí 1] Click (560, 520) ➔ (560, 255) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.5)
            elif selected_char_team == "Vị Trí 2":
                self.after(0, self.log_info, "👉 [Vị Trí 2] Click (560, 520) ➔ (560, 340) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.5)
            elif selected_char_team == "Vị Trí 3":
                self.after(0, self.log_info, "👉 [Vị Trí 3] Click (560, 520) ➔ (560, 430) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
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

            # --- Bước 3: Mở Phụ Bản & Vào Phụ Bản cho từng ô tích PB 20..110 ---
            if any_pb_checked:
                for pb_name, var_pb, (pb_x, pb_y), delay_sec in dungeons_to_run:
                    if var_pb.get():
                        if self._should_stop_card_E(): return
                        self.after(0, self.log_info, f"🚀 [Phụ Bản Đội - {pb_name}] Kích hoạt quy trình cho ô tích '{pb_name}'...")

                        # 1. Quét tìm card_b/b_pb.png
                        b_pb_x, b_pb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85)
                        if b_pb_x is not None and b_pb_y is not None:
                            self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_pb.png' tại ({b_pb_x}, {b_pb_y})! Click chọn ➔ Hoãn 0.4s...")
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x} {b_pb_y}"])
                            time.sleep(0.4)
                        else:
                            self.after(0, self.log_info, "👉 Chưa thấy 'b_pb.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                            time.sleep(0.4)
                            if self._should_stop_card_E(): return
                            b_pb_x, b_pb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_pb.png", threshold=0.85)
                            if b_pb_x is not None and b_pb_y is not None:
                                self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_pb.png' tại ({b_pb_x}, {b_pb_y})! Click chọn ➔ Hoãn 0.4s...")
                                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_pb_x} {b_pb_y}"])
                                time.sleep(0.4)
                            else:
                                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'b_pb.png' trong bảng menu.")

                        if self._should_stop_card_E(): return
                        # 2. Click chọn PB (240, pb_y) ➔ (735, 575)
                        self.after(0, self.log_info, f"👉 Click chọn {pb_name} tại ({pb_x}, {pb_y}) ➔ Click (735, 575) (Hoãn 0.4s mỗi tap)...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {pb_x} {pb_y}"])
                        time.sleep(0.4)
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 735 575"])
                        time.sleep(0.4)
                        # 4. Xử lý Mật Khẩu phòng (Dùng thao tác của ô Cá Nhân làm chuẩn cho cả ô Tổ Đội)
                        if self._should_stop_card_E(): return
                        self.after(0, self.log_info, "👁️ Quét tìm ảnh mẫu 'card_b/b_matkhau.png' (85%)...")
                        mk_x, mk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_matkhau.png", threshold=0.85)
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

                        # --- PHÂN LUỒNG CÁ NHÂN HOẶC TỔ ĐỘI ---
                        if hasattr(self, 'var_E_doi') and self.var_E_doi.get():
                            if self._should_stop_card_E(): return
                            self.after(0, self.log_info, "👥 [Phụ Bản Đội - Ô Tổ Đội] Gọi thao tác Card Tổ Đội (_run_card_G_action_2) & ĐỢI HOÀN THÀNH 100%...")
                            self._execute_card_G_for_mode(dnconsole_path, tab_name, tab_index, mode=2)
                        else:
                            self.after(0, self.log_info, "👤 [Phụ Bản Đội - Ô Cá Nhân] Đã hoàn tất tạo phòng ➔ Chuyển trực tiếp sang Bước 4 (Vào Trận).")

                        # --- BƯỚC 4: VÀO TRẬN & ĐÁNH TRẬN PHỤ BẢN ĐỘI ---
                        if self._should_stop_card_E(): return
                        self.after(0, self.log_info, "👁️ Quét tìm & tap liên tục 0.5s nút Bắt Đầu 'card_b/b_batdau.png' (85%) cho đến khi mất ảnh...")
                        while not self._should_stop_card_E():
                            bd_x, bd_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_batdau.png", threshold=0.85)
                            if bd_x is None or bd_y is None:
                                self.after(0, self.log_info, "ℹ️ Đã mất ảnh 'card_b/b_batdau.png' (Vào trận thành công) ➔ Tiếp tục thao tác tiếp theo.")
                                break
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {bd_x} {bd_y}"])
                            time.sleep(0.5)

                        if self._should_stop_card_E(): return
                        self.after(0, self.log_info, f"⏳ [{pb_name}] Chờ 3.5s nạp trận...")
                        for _ in range(7):
                            if self._should_stop_card_E(): return
                            time.sleep(0.5)

                        if self._should_stop_card_E(): return
                        self.after(0, self.log_info, f"⏳ [{pb_name}] Chờ thời gian nạp {delay_sec}s & click Auto Đánh (1165, 210) mỗi 0.3s...")
                        start_wait = time.time()
                        while time.time() - start_wait < delay_sec:
                            if self._should_stop_card_E(): return
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1165 210"])
                            time.sleep(0.3)

                        if self._should_stop_card_E(): return
                        self.after(0, self.log_info, f"👁️ [{pb_name}] Hết {delay_sec}s chờ nạp ➔ Quét tìm nút Xác Nhận 'card_b/b_xn.png' & tiếp tục click Auto (1165, 210) mỗi 0.3s...")
                        xn_x, xn_y = None, None
                        while not self._should_stop_card_E():
                            xn_x, xn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_xn.png", threshold=0.85)
                            if xn_x is not None and xn_y is not None:
                                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện ảnh 'card_b/b_xn.png' tại ({xn_x}, {xn_y})!")
                                break

                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1165 210"])
                            time.sleep(0.3)

                        if self._should_stop_card_E(): return
                        if xn_x is not None and xn_y is not None:
                            self.after(0, self.log_info, f"👉 Tap nhấp chọn ảnh Xác Nhận 'card_b/b_xn.png' tại ({xn_x}, {xn_y}) để hoàn thành {pb_name}...")
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x} {xn_y}"])

                        # Khi hoàn thành 1 mốc Phụ Bản -> hoãn 3.0s để tiếp tục mốc Phụ Bản tiếp theo
                        if self._should_stop_card_E(): return
                        self.after(0, self.log_info, f"⏳ [{pb_name}] Hoàn thành mốc {pb_name}! Hoãn 3.0s để tiếp tục mốc Phụ Bản tiếp theo...")
                        time.sleep(3.0)

            # --- Bước 4: XỬ LÝ RIÊNG LẺ MỐC CHECK "CLICK" ---
            if is_click_checked:
                if self._should_stop_card_E(): return
                self.after(0, self.log_info, "🚀 [Phụ Bản Đội - Mốc Click] Kích hoạt quy trình riêng lẻ cho ô 'Click'...")
                self.after(0, self.log_info, "👁️ [Click] Quét tìm & tap liên tục 0.5s nút Bắt Đầu 'card_b/b_batdau.png' (85%) cho đến khi mất ảnh...")
                while not self._should_stop_card_E():
                    bd_x, bd_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_batdau.png", threshold=0.85)
                    if bd_x is None or bd_y is None:
                        self.after(0, self.log_info, "ℹ️ Đã mất ảnh 'card_b/b_batdau.png' (Vào trận thành công) ➔ Tiếp tục thao tác tiếp theo.")
                        break
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {bd_x} {bd_y}"])
                    time.sleep(0.5)

                if self._should_stop_card_E(): return
                self.after(0, self.log_info, "⏳ [Click] Tạm nghỉ 3.5s nạp trận ban đầu...")
                for _ in range(7):
                    if self._should_stop_card_E(): return
                    time.sleep(0.5)

                if self._should_stop_card_E(): return
                self.after(0, self.log_info, "👁️ [Click] Click Auto Đánh (1165, 210) mỗi 0.3s kết hợp Mắt thần quét nhận diện 'card_b/b_xn.png' (85%)...")
                xn_x, xn_y = None, None
                while not self._should_stop_card_E():
                    xn_x, xn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_xn.png", threshold=0.85)
                    if xn_x is not None and xn_y is not None:
                        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện ảnh 'card_b/b_xn.png' tại ({xn_x}, {xn_y})!")
                        break

                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1165 210"])
                    time.sleep(0.3)

                if not self._should_stop_card_E() and xn_x is not None and xn_y is not None:
                    self.after(0, self.log_info, f"👉 Tap nhấp chọn ảnh Xác Nhận 'card_b/b_xn.png' tại ({xn_x}, {xn_y}) để hoàn tất...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xn_x} {xn_y}"])

                if self._should_stop_card_E(): return
                self.after(0, self.log_info, "⏳ [Click] Hoàn thành mốc Click! Hoãn 3.0s...")
                time.sleep(3.0)

        # ---------------- 3. TỰ ĐỘNG TẮT CÔNG TẮC & LƯU CẤU HÌNH (GIỮ NGUYÊN Ô TÍCH) ----------------
        self.var_switch_E.set(False)
        self.after(0, self.save_config)
        self.after(0, self.log_info, "✅ [1/6: PHỤ BẢN ĐƠN / ĐỘI] Đã thực thi hoàn tất! (Tự động tắt công tắc ON/OFF & giữ nguyên các ô tích)")

    def _should_stop_card_G(self) -> bool:
        """
        Kiểm tra điều kiện dừng & tạm dừng cho Card 4 Tổ Đội (G):
        - Ngắt ngay nếu bấm Dừng Tổng hoặc công tắc Card đang chạy (var_switch_E/D/F) bị tắt.
        - Tạm dừng (vòng lặp chờ nhả ô) nếu bất kỳ ô Tạm Dừng nào của Card đang chạy (var_pause_E, var_pause_D, var_pause_F) đang được tích.
        """
        if self.stop_requested:
            return True

        # Kiểm tra nếu ô Tạm Dừng của Card đang liên quan (E, D, F) đang tích
        def is_any_pause_active() -> bool:
            if hasattr(self, 'var_switch_E') and self.var_switch_E.get() and hasattr(self, 'var_pause_E') and self.var_pause_E.get():
                return True
            if hasattr(self, 'var_switch_D') and self.var_switch_D.get() and hasattr(self, 'var_pause_D') and self.var_pause_D.get():
                return True
            if hasattr(self, 'var_switch_F') and self.var_switch_F.get() and hasattr(self, 'var_pause_F') and self.var_pause_F.get():
                return True
            return False

        def is_no_active_switch_on() -> bool:
            e_active = hasattr(self, 'var_switch_E') and hasattr(self, 'var_E_doi') and self.var_E_doi.get() and self.var_switch_E.get()
            d_active = hasattr(self, 'var_switch_D') and hasattr(self, 'var_D2') and self.var_D2.get() and self.var_switch_D.get()
            f_active = hasattr(self, 'var_switch_F') and hasattr(self, 'var_F2') and self.var_F2.get() and self.var_switch_F.get()
            return not (e_active or d_active or f_active)

        # Vòng lặp tạm dừng thông minh
        if is_any_pause_active():
            self.after(0, self.log_info, "⏸️ [CARD TỔ ĐỘI] Phát hiện ô Tạm Dừng của Card đang chạy được tích ➔ Tạm dừng hoạt động Tổ Đội (Chờ nhả ô Tạm Dừng)...")
            while is_any_pause_active() and not self.stop_requested:
                if is_no_active_switch_on():
                    return True
                time.sleep(0.5)
            self.after(0, self.log_info, "▶️ [CARD TỔ ĐỘI] Ô Tạm Dừng đã được nhả ➔ Khôi phục chạy tiếp hoạt động Tổ Đội!")

        return is_no_active_switch_on()

    def _run_card_G_action_1(self, dnconsole_path: str, tab_index: str, list_B: list):
        """
        THAO TÁC 1 CỦA CARD TỔ ĐỘI:
        Kích hoạt khi ô 'Tổ Đội' ở Card 40 NPC (var_D2) hoặc Card 2K (var_F2) được tích.
        Bổ sung tính năng quản lý danh sách đã mời (already_invited) thông minh.
        """
        if self._should_stop_card_G() or not list_B: return

        self.after(0, self.log_info, f"🚀 [CARD TỔ ĐỘI - Thao Tác 1] Khởi chạy quy trình mời {len(list_B)} nhân vật trong Danh Sách B: {', '.join(list_B)}...")
        already_invited = set()

        # ---------------- GIAI ĐOẠN 1: MỞ GIAO DIỆN TỔ ĐỘI ----------------
        if self._should_stop_card_G(): return
        # 1. Đóng Quảng Cáo / Thông Báo Nổi
        lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
        if lx_x is not None and lx_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'login_x.png' tại ({lx_x}, {lx_y})! Tap click ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
            time.sleep(0.4)

        # 2. Quét Mở Giao Diện Đội
        if self._should_stop_card_G(): return
        self.after(0, self.log_info, "👁️ [Thao Tác 1] Quét tìm ảnh 'card_b/b_doi.png' (85%)...")
        b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
        if b_doi_x is not None and b_doi_y is not None:
            self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_doi.png' tại ({b_doi_x}, {b_doi_y})! Tap click vào ảnh ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "👉 Chưa thấy 'card_b/b_doi.png' ➔ Tap nút xanh (1213, 648) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
            if self._should_stop_card_G(): return
            b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
            if b_doi_x is not None and b_doi_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_doi.png' tại ({b_doi_x}, {b_doi_y})! Tap click vào ảnh ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                time.sleep(0.4)

        # ---------------- VÒNG LẶP MỜI & KIỂM TRA TỔ ĐỘI ----------------
        while not self._should_stop_card_G():
            # 3. Nhận Diện Người Trong Tổ Đội
            if self._should_stop_card_G(): return
            self.after(0, self.log_info, "👁️ [Thao Tác 1] Quét kiểm tra độ đầy đủ của các nhân vật trong Danh Sách B...")
            all_present = True
            missing_list = []

            for char_name in list_B:
                if self._should_stop_card_G(): return
                chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/40npc2k/{char_name}.png", threshold=0.80)
                if chk_x is None or chk_y is None:
                    chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/{char_name}.png", threshold=0.80)

                if chk_x is None or chk_y is None:
                    all_present = False
                    missing_list.append(char_name)
                else:
                    if char_name in already_invited:
                        already_invited.remove(char_name)

            # 4. Xử Lý Kết Quả Kiểm Tra
            if all_present:
                self.after(0, self.log_info, f"✅ [Thao Tác 1] Tổ đội đã ĐỦ 100% thành viên ({', '.join(list_B)})!")
                # Quét tìm ảnh / tap login_x.png (75%) nghỉ 0.4s
                if self._should_stop_card_G(): return
                lx2_x, lx2_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
                if lx2_x is not None and lx2_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'login_x.png' tại ({lx2_x}, {lx2_y})! Tap click ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx2_x} {lx2_y}"])
                    time.sleep(0.4)

                # Mắt thần quét tìm ảnh icon Đội card_b/b_doi.png (85%). Nếu thấy ngay ➔ Tap nút xanh (1213, 648) đóng menu (hoãn 0.4s)
                if self._should_stop_card_G(): return
                b_doi2_x, b_doi2_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
                if b_doi2_x is not None and b_doi2_y is not None:
                    self.after(0, self.log_info, "🎯 Thấy 'card_b/b_doi.png' ➔ Tap nút xanh lá (1213, 648) đóng bảng Menu (hoãn 0.4s)...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                    time.sleep(0.4)

                self.after(0, self.log_info, "🚀 [Thao Tác 1] Hoàn tất quy trình Tổ Đội ➔ Chuyển qua hành động tiếp theo.")
                break

            else:
                uninvited_missing = [c for c in missing_list if c not in already_invited]
                if not uninvited_missing:
                    self.after(0, self.log_info, f"ℹ️ Tất cả thành viên thiếu ({', '.join(missing_list)}) đã được bấm Mời ➔ Reset danh sách đã mời để tuần tự kiểm tra/mời lại...")
                    already_invited.clear()
                    uninvited_missing = list(missing_list)

                self.after(0, self.log_info, f"⚠️ [Thao Tác 1] Đội chưa đủ người (Thiếu: {', '.join(missing_list)} | Cần mời tiếp: {', '.join(uninvited_missing)}) ➔ Thực hiện thao tác Mời...")

                # Mắt thần quét tìm ảnh / tap card_f/f_nguoi.png (85%) nghỉ 0.4s
                if self._should_stop_card_G(): return
                nguoi_x, nguoi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_nguoi.png", threshold=0.85)
                if nguoi_x is not None and nguoi_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_f/f_nguoi.png' tại ({nguoi_x}, {nguoi_y})! Tap click vào ảnh ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {nguoi_x} {nguoi_y}"])
                    time.sleep(0.4)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy ảnh 'card_f/f_nguoi.png' trên màn hình.")
                    time.sleep(0.4)

                # Dò Tìm Tất Cả Nhân Vật Bị Thiếu Cùng Lúc Trực Tiếp Trên Màn Hình (Chỉ vuốt 1 chu kỳ cho cả danh sách)
                still_missing = list(uninvited_missing)
                
                def scan_and_invite_current_screen(missing_tracker: list) -> list:
                    """Mắt thần quét tìm kiếm đồng thời tất cả các nhân vật còn thiếu chưa mời trên màn hình hiện tại"""
                    invited_chars = []
                    for char_name in list(missing_tracker):
                        if self._should_stop_card_G(): break
                        found_char_x, found_char_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/40npc2k/{char_name}.png", threshold=0.80)
                        if found_char_x is None or found_char_y is None:
                            found_char_x, found_char_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/{char_name}.png", threshold=0.80)

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
                        if self._should_stop_card_G() or not still_missing: break
                        self.after(0, self.log_info, f"📜 [Vuốt xuống {swipe_down_cnt+1}/4] Quét tìm các nhân vật chưa mời: {', '.join(still_missing)}...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 795 400 795 205 1500"])
                        time.sleep(1.0)
                        still_missing = scan_and_invite_current_screen(still_missing)

                # 3. Chiều Vuốt LÊN thông minh (Nếu sau 4 lần vuốt xuống vẫn còn acc chưa thấy): input swipe 795 205 795 575 3000 (Thời gian vuốt 3s), tối đa 2 lần
                if still_missing:
                    for swipe_up_cnt in range(2):
                        if self._should_stop_card_G() or not still_missing: break
                        self.after(0, self.log_info, f"📜 [Vuốt lên {swipe_up_cnt+1}/2] Quét tìm các nhân vật chưa mời: {', '.join(still_missing)}...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 795 205 795 575 3000"])
                        time.sleep(1.0)
                        still_missing = scan_and_invite_current_screen(still_missing)

                # Kiểm tra nếu sau 4 lượt vuốt xuống & 2 lượt vuốt lên vẫn còn nhân vật chưa mời được
                if still_missing:
                    self.after(0, self.log_info, f"⚠️ [Hành Động Thông Minh] Sau 4 lượt vuốt xuống & 2 lượt vuốt lên vẫn chưa mời được: {', '.join(still_missing)} ➔ Quét tap 'card_f/f_doingu.png' (85%) hoãn 0.4s & quay lại bước Nhận Diện!")
                    dn_x, dn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_doingu.png", threshold=0.85)
                    if dn_x is not None and dn_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {dn_x} {dn_y}"])
                    time.sleep(0.4)
                    continue

                # Sau khi đã mời thành công tất cả các acc bị thiếu: Nghỉ 5s chờ đồng ý
                if self._should_stop_card_G(): return
                self.after(0, self.log_info, "⏳ [Thao Tác 1] Đã bấm Mời toàn bộ danh sách bị thiếu ➔ Nghỉ 5.0s chờ các thành viên đồng ý...")
                for _ in range(5):
                    if self._should_stop_card_G(): return
                    time.sleep(1.0)

                # Mắt thần quét tìm ảnh / tap card_f/f_doingu.png (85%) hoãn 0.4s
                if self._should_stop_card_G(): return
                self.after(0, self.log_info, "👁️ Quét tìm & tap ảnh 'card_f/f_doingu.png' (85%) hoãn 0.4s...")
                dn_x, dn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_doingu.png", threshold=0.85)
                if dn_x is not None and dn_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_f/f_doingu.png' tại ({dn_x}, {dn_y})! Tap click...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {dn_x} {dn_y}"])
                time.sleep(0.4)

    def _run_card_G_action_2(self, dnconsole_path: str, tab_index: str, list_B: list):
        """
        THAO TÁC 2 CỦA CARD TỔ ĐỘI:
        Kích hoạt khi ô tích 'Tổ Đội' của Card Phụ Bản Đơn / Đội (var_E_doi) được tích.
        """
        if self._should_stop_card_G() or not list_B: return

        self.after(0, self.log_info, f"🚀 [CARD TỔ ĐỘI - Thao Tác 2] Bắt đầu quy trình mời {len(list_B)} nhân vật trong Danh Sách B: {', '.join(list_B)}...")
        already_invited = set()

        # VÒNG LẶP MỜI VÀ KIỂM TRA ĐỘI HÌNH (Lặp cho tới khi đủ 100% người)
        while not self._should_stop_card_G():
            # --- BƯỚC 1: NHẬN DIỆN THÀNH VIÊN TRONG ĐỘI ---
            if self._should_stop_card_G(): return
            self.after(0, self.log_info, "👁️ [Thao Tác 2 - Bước 1] Quét kiểm tra các nhân vật trong Danh Sách B...")
            all_present = True
            missing_list = []

            for char_name in list_B:
                if self._should_stop_card_G(): return
                chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/pbdoi/{char_name}.png", threshold=0.80)
                if chk_x is None or chk_y is None:
                    chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/{char_name}.png", threshold=0.80)

                if chk_x is None or chk_y is None:
                    all_present = False
                    missing_list.append(char_name)
                else:
                    if char_name in already_invited:
                        already_invited.remove(char_name)

            # --- BƯỚC 2: ĐÁNH GIÁ KẾT QUẢ KIỂM TRA ---
            if all_present:
                self.after(0, self.log_info, f"✅ [Thao Tác 2 - Bước 2: Trường hợp A] Đội hình đã ĐỦ 100% thành viên ({', '.join(list_B)})! Thoát vòng lặp & trả thao tác về Phụ Bản Đội.")
                break

            # Lọc danh sách những thành viên thiếu chưa được gửi lời mời ở lượt trước
            uninvited_missing = [c for c in missing_list if c not in already_invited]
            if not uninvited_missing:
                self.after(0, self.log_info, f"ℹ️ Tất cả thành viên thiếu ({', '.join(missing_list)}) đã được bấm Mời ➔ Reset danh sách đã mời để tuần tự kiểm tra/mời lại...")
                already_invited.clear()
                uninvited_missing = list(missing_list)

            # 🔴 TRƯỜNG HỢP B: CÒN THIẾU THÀNH VIÊN
            self.after(0, self.log_info, f"⚠️ [Thao Tác 2 - Bước 2: Trường hợp B] Đội chưa đủ người (Thiếu: {', '.join(missing_list)} | Cần mời tiếp: {', '.join(uninvited_missing)}) ➔ Quét tìm nút Mời 'card_f/f_moi.png'...")
            
            # Quét Mắt thần tìm nút Mời card_f/f_moi.png (85%)
            if self._should_stop_card_G(): return
            f_moi_x, f_moi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_moi.png", threshold=0.85)
            if f_moi_x is not None and f_moi_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_f/f_moi.png' tại ({f_moi_x}, {f_moi_y})! Tap click ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {f_moi_x} {f_moi_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy ảnh 'card_f/f_moi.png' trên màn hình ➔ Thử lại sau 1.0s...")
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
                    if self._should_stop_card_G(): break
                    found_x, found_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/pbdoi/{char_name}.png", threshold=0.80)
                    if found_x is None or found_y is None:
                        found_x, found_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/{char_name}.png", threshold=0.80)

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

            # 2. Chiều Vuốt XUỐNG thông minh: input swipe 625 410 625 260 1500 (Tối đa 10 lần)
            if not invited_any and still_missing:
                for swipe_down_cnt in range(10):
                    if self._should_stop_card_G() or not still_missing: break
                    self.after(0, self.log_info, f"📜 [Vuốt xuống {swipe_down_cnt+1}/10] Swipe (625, 410 ➔ 625, 260)...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 625 410 625 260 1500"])
                    time.sleep(1.0)
                    invited_any, char_done = scan_and_invite_mode2(still_missing)
                    if invited_any: break

            # 3. Chiều Vuốt LÊN thông minh: input swipe 625 260 625 410 3000 (Tối đa 8 lần)
            if not invited_any and still_missing:
                for swipe_up_cnt in range(8):
                    if self._should_stop_card_G() or not still_missing: break
                    self.after(0, self.log_info, f"📜 [Vuốt lên {swipe_up_cnt+1}/8] Swipe (625, 260 ➔ 625, 410)...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 625 260 625 410 3000"])
                    time.sleep(1.0)
                    invited_any, char_done = scan_and_invite_mode2(still_missing)
                    if invited_any: break

            # 4. Tự Động Sửa Lỗi Nếu Không Tìm Thấy
            if not invited_any:
                self.after(0, self.log_info, "⚠️ [Thao Tác 2 - Sửa Lỗi] Sau 10 lượt vuốt xuống & 8 lượt vuốt lên không tìm thấy acc ➔ Tap (330, 25) tắt bảng Mời ➔ Hoãn 0.4s & quay lại Bước 2.1...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 330 25"])
                time.sleep(0.4)
                continue

            # Sau khi bấm Mời acc thành công: Tạm nghỉ 5.0s chờ đồng ý & quay lại Bước 2.1
            if self._should_stop_card_G(): return
            self.after(0, self.log_info, "⏳ [Thao Tác 2] Đã tap nút Mời ➔ Tạm nghỉ 5.0s chờ các thành viên nhận & đồng ý lời mời...")
            for _ in range(5):
                if self._should_stop_card_G(): return
                time.sleep(1.0)

    def _execute_card_G_for_mode(self, dnconsole_path: str, tab_name: str, tab_index: str, mode: int):
        """
        Khung thực thi phân luồng Card Tổ Đội (G):
        - mode=1: Thao tác 1 (Kích hoạt khi ô Tổ Đội 40 NPC var_D2 hoặc Card 2K var_F2 được tích)
        - mode=2: Thao tác 2 (Kích hoạt khi ô Tổ Đội Phụ Bản Đội var_E_doi được tích)
        """
        list_B = list(getattr(self, 'list_G_B', []))
        if not list_B:
            self.after(0, self.log_info, f"ℹ️ [TỔ ĐỘI - Thao Tác {mode}] [Danh Sách B] chưa có nhân vật nào -> Bỏ qua.")
            return

        self.after(0, self.log_info, f"▶️ [TỔ ĐỘI - Thao Tác {mode}] Bắt đầu thực thi {len(list_B)} nhân vật từ [Danh Sách B]: {', '.join(list_B)}...")
        if mode == 1:
            self._run_card_G_action_1(dnconsole_path, tab_index, list_B)
        elif mode == 2:
            self._run_card_G_action_2(dnconsole_path, tab_index, list_B)

    def _execute_card_G_phu_ban_don(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """Tương thích hàm gọi cũ -> Gọi sang mode 2 của Card Tổ Đội (Phụ Bản Đội)"""
        self._execute_card_G_for_mode(dnconsole_path, tab_name, tab_index, mode=2)

    def _run_boss_check_pos(self, dnconsole_path: str, tab_index: str) -> bool:
        """PHẦN 0: QUÉT TÌM BOSS CỦA BOSS THẾ GIỚI. Trả về True nếu tìm thấy c_vitriboss.png (bỏ qua Về SafeZone & Di Chuyển)"""
        if self._should_stop_card_C(): return False
        self.after(0, self.log_info, "👁️ [Boss Thế Giới - Phần 0: Quét Tìm Boss] Quét tìm ảnh 'card_c/c_vitriboss.png' (75%) liên tục trong 3.0s...")
        for _ in range(6):
            if self._should_stop_card_C(): return False
            vb_x, vb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitriboss.png", threshold=0.75)
            if vb_x is not None and vb_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'card_c/c_vitriboss.png' tại ({vb_x}, {vb_y})! Đã ở vị trí Boss ➔ Chuyển thẳng xuống PHẦN 4: ĐÁNH BOSS THẾ GIỚI.")
                return True
            time.sleep(0.5)

        self.after(0, self.log_info, "ℹ️ Không thấy 'card_c/c_vitriboss.png' ➔ Tiếp tục thao tác PHẦN 1: QUY TRÌNH VỀ KHU AN TOÀN.")
        return False

    def _run_boss_safezone(self, dnconsole_path: str, tab_index: str):
        """PHẦN 1: QUY TRÌNH VỀ KHU AN TOÀN CỦA BOSS THẾ GIỚI"""
        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "👁️ Quét tìm nút 'login_x.png' để đóng bảng quảng cáo/thông báo...")
        lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
        if lx_x is not None and lx_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'login_x.png' tại ({lx_x}, {lx_y})! Click chọn ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
            time.sleep(0.4)

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "👁️ [Boss Thế Giới - Bước 1.1] Quét tìm nút Vị Trí 'a_vitri.png' (85%)...")
        v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
        if v_x is not None and v_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_vitri.png' tại ({v_x}, {v_y})! Tap click trực tiếp ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "👉 Chưa thấy 'a_vitri.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
            if self._should_stop_card_C(): return
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y})! Tap click trực tiếp ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'a_vitri.png' trong bảng menu.")

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "👉 [Boss Thế Giới - Bước 1.2] Click liên tục (435, 250) mỗi 0.5s cho đến khi xuất hiện nút Có 'card_c/c_co.png' (85%)...")
        while not self._should_stop_card_C():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_co.png", threshold=0.85)
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút Có 'card_c/c_co.png' tại ({co_x}, {co_y})! Dừng click (435, 250).")
                break
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 435 250"])
            time.sleep(0.5)

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

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "⏳ [Boss Thế Giới - Bước 1.4] Hoãn 3.0s trước khi quét kiểm tra lại nút 'a_vitri.png'...")
        time.sleep(3.0)

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "👁️ [Boss Thế Giới - Bước 1.4] Quét kiểm tra lại nút 'a_vitri.png' (85%)...")
        v_check_x, v_check_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
        if v_check_x is not None and v_check_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_vitri.png' vẫn còn tại ({v_check_x}, {v_check_y}) ➔ Click (1213, 648) để thu gọn menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "ℹ️ Không thấy nút 'a_vitri.png' ➔ Bỏ qua thu gọn menu.")

    def _run_boss_pre_move(self, dnconsole_path: str, tab_index: str) -> bool:
        """PHẦN THÊM: THAO TÁC TRƯỚC PHẦN 3 DI CHUYỂN CỦA BOSS THẾ GIỚI. Trả về True nếu tìm thấy c_dichuyen.png (bỏ qua di chuyển)"""
        if self._should_stop_card_C(): return False

        self.after(0, self.log_info, "👁️ [Boss - Thao Tác Trước Di Chuyển] 1. Quét nút Sự Kiện 'card_c/c_sukien.png'...")
        sk_x, sk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_sukien.png", threshold=0.85)
        if sk_x is not None and sk_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_sukien.png' tại ({sk_x}, {sk_y})! Tap click chọn ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {sk_x} {sk_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "👉 Chưa thấy 'c_sukien.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
            if self._should_stop_card_C(): return False
            sk_x, sk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_sukien.png", threshold=0.85)
            if sk_x is not None and sk_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_sukien.png' tại ({sk_x}, {sk_y})! Tap click chọn ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {sk_x} {sk_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'card_c/c_sukien.png' trong bảng menu.")

        if self._should_stop_card_C(): return False
        self.after(0, self.log_info, "👁️ [Boss - Thao Tác Trước Di Chuyển] 2. Quét nút Boss TG 'card_c/c_skboss.png'...")
        skb_x, skb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_skboss.png", threshold=0.85)
        if skb_x is not None and skb_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_skboss.png' tại ({skb_x}, {skb_y})! Tap click chọn ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {skb_x} {skb_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "ℹ️ Không tìm thấy 'card_c/c_skboss.png' ➔ Bỏ qua.")

        if self._should_stop_card_C(): return False
        self.after(0, self.log_info, "👁️ [Boss - Thao Tác Trước Di Chuyển] 3. Quét nút Dịch Chuyển 'card_c/c_dichuyen.png'...")
        dc_x, dc_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_dichuyen.png", threshold=0.85)
        if dc_x is not None and dc_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_dichuyen.png' tại ({dc_x}, {dc_y})! Tap click ➔ Hoãn 3.0s ➔ Chuyển thẳng qua PHẦN 4: ĐÁNH BOSS...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {dc_x} {dc_y}"])
            time.sleep(3.0)
            return True
        else:
            self.after(0, self.log_info, "ℹ️ Không thấy 'c_dichuyen.png' (hoặc nút bị Tối/Mờ) ➔ Quét tìm nút 'login_x.png' (75%)...")
            lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
            if lx_x is not None and lx_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'login_x.png' tại ({lx_x}, {lx_y})! Tap click đóng cửa sổ ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                time.sleep(0.4)

            if self._should_stop_card_C(): return False
            self.after(0, self.log_info, "👁️ Quét tìm nút Vị Trí 'a_vitri.png' (85%)...")
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y}) ➔ Click nút xanh lá góc dưới phải (1213, 648) ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "ℹ️ Chưa thấy nút 'a_vitri.png' ➔ Bỏ qua.")

            self.after(0, self.log_info, "ℹ️ Chuyển qua PHẦN 3: DI CHUYỂN.")
            return False

    def _run_boss_move_manual(self, dnconsole_path: str, tab_index: str):
        """PHẦN 3: DI CHUYỂN BỘ CỦA BOSS THẾ GIỚI"""
        self.after(0, self.log_info, "🚀 [Boss - Di Chuyển] Nghỉ 0.4s ➔ (1115, 87) ➔ (1223, 227) ➔ (1235, 551) ➔ (1178, 405) ➔ (704, 196) ➔ (1115, 87)...")
        if self._should_stop_card_C(): return
        time.sleep(0.4)

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "👉 [Boss - Di Chuyển] Click (1115, 87)...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1115 87"])
        time.sleep(1.0)

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "👉 [Boss - Di Chuyển] Click (1223, 227) ➔ Nghỉ 5s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1223 227"])
        for _ in range(5):
            if self._should_stop_card_C(): return
            time.sleep(1.0)

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "👉 [Boss - Di Chuyển] Click (1235, 551) ➔ Nghỉ 4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1235 551"])
        for _ in range(4):
            if self._should_stop_card_C(): return
            time.sleep(1.0)

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "👉 [Boss - Di Chuyển] Click (1178, 405) ➔ Nghỉ 4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1178 405"])
        for _ in range(4):
            if self._should_stop_card_C(): return
            time.sleep(1.0)

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "👉 [Boss - Di Chuyển] Click (704, 196) ➔ Nghỉ 2s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 704 196"])
        for _ in range(2):
            if self._should_stop_card_C(): return
            time.sleep(1.0)

        if self._should_stop_card_C(): return
        self.after(0, self.log_info, "👉 [Boss - Di Chuyển] Click (1115, 87)...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1115 87"])
        time.sleep(1.0)

    def _run_boss_workflow(self, dnconsole_path: str, tab_name: str, tab_index: str, max_turns: int = 5, skip_move: bool = False):
        """QUY TRÌNH THỰC THI THAO TÁC ĐÁNH BOSS THẾ GIỚI (PHẦN 0 -> PHẦN 1 -> PHẦN THÊM -> PHẦN 3 -> PHẦN 4 với số lượt max_turns)"""
        if self._should_stop_card_C(): return

        if not skip_move:
            # 📌 PHẦN 0: QUÉT TÌM BOSS (TRƯỚC PHẦN 1 VỀ KHU AN TOÀN)
            is_at_boss = self._run_boss_check_pos(dnconsole_path, tab_index)
            if not is_at_boss:
                self._run_boss_safezone(dnconsole_path, tab_index)
                skip_di_chuyen = self._run_boss_pre_move(dnconsole_path, tab_index)

                if not skip_di_chuyen:
                    self._run_boss_move_manual(dnconsole_path, tab_index)
        else:
            self.after(0, self.log_info, "ℹ️ [Boss] Đã ở vị trí Boss / Đã hoàn thành di chuyển ➔ Tiến thẳng vào quy trình Đánh Boss...")

        # 📌 PHẦN 4: ĐÁNH BOSS THẾ GIỚI - QUY TRÌNH "BOSS"
        self.after(0, self.log_info, f"🔄 [Boss] Bắt đầu thực thi {max_turns} lượt đánh...")
        for turn in range(1, max_turns + 1):
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, f"🔄 [Boss - Lượt {turn}/{max_turns}] Đang thực thi lượt {turn}...")

            # [Bước 2 của Lượt] - Tìm Boss:
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, f"👁️ [Lượt {turn} - Bước 2] Click liên tục (1240, 605) tìm ảnh Boss 'card_c/c_boss.png' (85%)...")
            boss_x, boss_y = None, None
            for click_idx in range(20):
                if self._should_stop_card_C(): break
                boss_x, boss_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_boss.png", threshold=0.85)
                if boss_x is not None and boss_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần phát hiện ảnh 'card_c/c_boss.png' tại ({boss_x}, {boss_y})! Dừng click (1240, 605).")
                    break
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 605"])
                time.sleep(0.4)

            if self._should_stop_card_C(): return
            if boss_x is None or boss_y is None:
                self.after(0, self.log_info, f"⚠️ [Lượt {turn} - Bước 2] Sau 20 lần click không thấy 'card_c/c_boss.png' ➔ Chạy lại PHẦN 1 (SAFE ZONE) & PHẦN THÊM...")
                self._run_boss_safezone(dnconsole_path, tab_index)
                self._run_boss_pre_move(dnconsole_path, tab_index)

            if self._should_stop_card_C(): return

            # [Bước 3 của Lượt] - Đặt vị trí đánh:
            self.after(0, self.log_info, f"👉 [Lượt {turn} - Bước 3] Click (1160, 570) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1160 570"])
            time.sleep(0.4)

            if self._should_stop_card_C(): return
            hl_x, hl_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_hetluot.png", threshold=0.85)
            if hl_x is not None and hl_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_hetluot.png' tại ({hl_x}, {hl_y})! Đã HẾT LƯỢT ➔ Chuyển thẳng xuống PHẦN 5: KẾT THÚC CARD C.")
                break
            else:
                self.after(0, self.log_info, "ℹ️ Không thấy 'card_c/c_hetluot.png' ➔ Tap (500, 635) ➔ Hoãn 0.4s...")
                if self._should_stop_card_C(): return
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 500 635"])
                time.sleep(0.4)

            # [Bước 4 của Lượt] - Bắt đầu chiến đấu:
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, f"⏳ [Lượt {turn}/{max_turns} - Bước 4] Đợi 2.0 giây trước khi click (185, 145)...")
            for _ in range(2):
                if self._should_stop_card_C(): return
                time.sleep(1.0)

            if self._should_stop_card_C(): return
            self.after(0, self.log_info, f"👉 [Lượt {turn}/{max_turns} - Bước 4] Click (185, 145) vào trận ➔ Hoãn 60s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 185 145"])
            for _ in range(60):
                if self._should_stop_card_C(): return
                time.sleep(1.0)

            if self._should_stop_card_C(): return
            self.after(0, self.log_info, f"👁️ [Lượt {turn}/{max_turns} - Bước 4] Quét tìm ảnh 'card_c/c_dung.png' (70%) mỗi 0.5s cho đến khi thấy...")
            while not self._should_stop_card_C():
                d_x, d_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_dung.png", threshold=0.70)
                if d_x is not None and d_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_dung.png' tại ({d_x}, {d_y})! Kết thúc lượt {turn}.")
                    break
                time.sleep(0.5)

    def _run_boss_ve_process(self, dnconsole_path: str, tab_name: str, tab_index: str, num_ve: int):
        """THAO TÁC Ô CHECK VÉ (var_C3)"""
        for ve_idx in range(1, num_ve + 1):
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, f"🎫 [Vé - Lượt {ve_idx}/{num_ve}] Bắt đầu quy trình dùng Vé thứ {ve_idx}...")

            # 1. Quét nút login_x.png (75%)
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "👁️ [Vé - Bước 1] Quét tìm nút 'login_x.png'...")
            lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
            if lx_x is not None and lx_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'login_x.png' tại ({lx_x}, {lx_y})! Click chọn ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                time.sleep(0.4)

            # 2. Quét nút Túi (card_c/c_tui.png) (85%)
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "👁️ [Vé - Bước 2] Quét nút Túi 'card_c/c_tui.png' (85%)...")
            tui_x, tui_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_tui.png", threshold=0.85)
            if tui_x is not None and tui_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện Túi tại ({tui_x}, {tui_y})! Tap click ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {tui_x} {tui_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa thấy ảnh 'card_c/c_tui.png' trên màn hình.")

            # 3. Cuộn tìm Vé Boss (tại tọa độ 920, 270)
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "📜 [Vé - Bước 3] Cuộn tìm ảnh Vé Boss 'card_c/c_veboss.png' (70%)...")
            veboss_x, veboss_y = None, None
            
            # Thao tác cuộn xuống từ từ tại (920, 270)
            for swipe_down_cnt in range(5):
                if self._should_stop_card_C(): break
                veboss_x, veboss_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_veboss.png", threshold=0.70)
                if veboss_x is not None and veboss_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_veboss.png' tại ({veboss_x}, {veboss_y})!")
                    break
                # Kiểm tra xem có gặp c_khoa.png hay không
                khoa_x, khoa_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_khoa.png", threshold=0.85)
                if khoa_x is not None and khoa_y is not None:
                    self.after(0, self.log_info, f"🔒 Phát hiện 'card_c/c_khoa.png' tại ({khoa_x}, {khoa_y}) nhưng chưa thấy Vé Boss ➔ Dừng cuộn xuống, chuyển sang cuộn ngược lên...")
                    break
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 920 400 920 180 1000"])
                time.sleep(1.0)

            # Nếu gặp c_khoa hoặc chưa thấy veboss -> Cuộn ngược lên lại 5 lần tại tọa độ điểm (920, 535) cho đến khi thấy card_c/c_veboss.png
            if veboss_x is None or veboss_y is None:
                for swipe_up_cnt in range(5):
                    if self._should_stop_card_C(): break
                    veboss_x, veboss_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_veboss.png", threshold=0.70)
                    if veboss_x is not None and veboss_y is not None:
                        self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_c/c_veboss.png' tại ({veboss_x}, {veboss_y})!")
                        break
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 920 180 920 535 1000"])
                    time.sleep(1.0)

            if veboss_x is not None and veboss_y is not None:
                self.after(0, self.log_info, f"👉 Click vào ảnh Vé Boss tại ({veboss_x}, {veboss_y}) ➔ Click (755, 460) ➔ Click (320, 25) (Hoãn 0.4s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {veboss_x} {veboss_y}"])
                time.sleep(0.4)
                if self._should_stop_card_C(): return
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 755 460"])
                time.sleep(0.4)
                if self._should_stop_card_C(): return
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 320 25"])
                time.sleep(0.4)

            # Quét nút login_x.png (75%)
            if self._should_stop_card_C(): return
            lx_x2, lx_y2 = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
            if lx_x2 is not None and lx_y2 is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'login_x.png' tại ({lx_x2}, {lx_y2})! Click đóng ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x2} {lx_y2}"])
                time.sleep(0.4)

            # Từ lượt vé thứ 2 trở đi (ve_idx >= 2), bỏ qua quy trình dịch chuyển / di chuyển đến Boss
            skip_move = (ve_idx >= 2)
            if skip_move:
                self.after(0, self.log_info, f"🚀 [Vé - Lượt {ve_idx}/{num_ve}] Bỏ qua di chuyển (từ lượt 2 trở đi) ➔ Khởi chạy thẳng quy trình Đánh Boss...")
            else:
                self.after(0, self.log_info, f"🚀 [Vé - Lượt {ve_idx}/{num_ve}] Khởi chạy quy trình Boss (Thực thi PHẦN 0: QUÉT TÌM BOSS (ƯU TIÊN HÀNG ĐẦU) ➔ Kiểm tra vị trí/di chuyển)...")
            self._run_boss_workflow(dnconsole_path, tab_name, tab_index, max_turns=1, skip_move=skip_move)

    def _execute_card_C_boss_tg(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """Thực thi Card 2: BOSS THẾ GIỚI (C) theo thứ tự thiết lập mới"""
        if self._should_stop_card_C():
            self.after(0, self.log_info, "ℹ️ [2/6: BOSS THẾ GIỚI] Công tắc ON/OFF đang TẮT -> Bỏ qua.")
            return

        checked = [
            ("Boss", self.var_C1),
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

        # =========================================================================
        # 📌 2. QUÉT TÌM BOSS (L4196-L4199)
        # =========================================================================
        is_already_at_boss = self._run_boss_check_pos(dnconsole_path, tab_index)

        # =========================================================================
        # 📌 3. VỀ KHU AN TOÀN (_run_boss_safezone)
        # =========================================================================
        if not is_already_at_boss:
            if self._should_stop_card_C(): return
            self._run_boss_safezone(dnconsole_path, tab_index)

        # =========================================================================
        # 📌 4. CHUYỂN ĐỔI VỊ TRÍ NHÂN VẬT (L4202-L4273)
        # =========================================================================
        if self._should_stop_card_C(): return
        self.after(0, self.log_info, f"⚙️ [Boss Thế Giới - Bước 2] Vị trí nhân vật: '{selected_char}'")

        if selected_char == "Xuất Chiến":
            self.after(0, self.log_info, "ℹ️ Vị trí 'Xuất Chiến': Bỏ qua Bước 2, chuyển thẳng xuống Phần Tiếp Theo.")
        else:
            # Nghỉ 0.4s trước khi khởi động Bước 2
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "⏳ [Boss Thế Giới - Bước 2] Nghỉ 0.4s trước khi khởi động...")
            time.sleep(0.4)

            # Quét ảnh icon Đội 'card_b/b_doi.png' (85%)
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "👁️ [Boss Thế Giới - Bước 2] Quét tìm ảnh 'card_b/b_doi.png' (85%)...")
            b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
            if b_doi_x is not None and b_doi_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "👉 Chưa thấy 'b_doi.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(0.4)
                if self._should_stop_card_C(): return
                b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
                if b_doi_x is not None and b_doi_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện 'card_b/b_doi.png' tại ({b_doi_x}, {b_doi_y})! Click vào ảnh ➔ Hoãn 0.4s...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                    time.sleep(0.4)
                else:
                    self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'card_b/b_doi.png' trong bảng menu.")

            if selected_char == "Vị Trí 1":
                self.after(0, self.log_info, "👉 [Vị Trí 1] Click (560, 520) ➔ (560, 255) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.5)
            elif selected_char == "Vị Trí 2":
                self.after(0, self.log_info, "👉 [Vị Trí 2] Click (560, 520) ➔ (560, 340) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
                time.sleep(0.5)
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
                time.sleep(0.5)
            elif selected_char == "Vị Trí 3":
                self.after(0, self.log_info, "👉 [Vị Trí 3] Click (560, 520) ➔ (560, 430) ➔ (1090, 110) (Hoãn 0.5s mỗi tap)...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
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

            # Click (1213, 648) đóng menu
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "👉 [Boss Thế Giới - Bước 2] Click (1213, 648) đóng menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)

        # =========================================================================
        # 📌 5. SỰ KIỆN BOSS & 6. DI CHUYỂN BỘ (Nếu chưa ở vị trí Boss)
        # =========================================================================
        if not is_already_at_boss:
            if self._should_stop_card_C(): return
            skip_di_chuyen = self._run_boss_pre_move(dnconsole_path, tab_index)
            if not skip_di_chuyen:
                # 📌 6. DI CHUYỂN BỘ
                self._run_boss_move_manual(dnconsole_path, tab_index)

        # =========================================================================
        # 📌 Ô CHECK 1: BOSS (Khi var_C1 được tích)
        # =========================================================================
        if self.var_C1.get():
            if self._should_stop_card_C(): return
            self.after(0, self.log_info, "🚀 [Ô Check 1: BOSS] Khởi chạy quy trình Boss (5 lượt)...")
            self._run_boss_workflow(dnconsole_path, tab_name, tab_index, max_turns=5, skip_move=True)

        # =========================================================================
        # 📌 Ô CHECK 2: VÉ (Khi var_C3 được tích)
        # =========================================================================
        if self.var_C3.get():
            if self._should_stop_card_C(): return
            now_dt = datetime.now()
            if now_dt.hour < 12:
                self.after(0, self.log_info, f"ℹ️ [Ô Check 2: VÉ] Hiện tại là {now_dt.strftime('%H:%M:%S')} (trước 12h trưa) ➔ Ô 'Vé' chỉ hoạt động sau 12h trưa ➔ Bỏ qua.")
            else:
                try:
                    num_ve = int(selected_ve)
                except ValueError:
                    num_ve = 1
                self.after(0, self.log_info, f"🚀 [Ô Check 2: VÉ] Khởi chạy quy trình Vé (Số lượng: {num_ve})...")
                self._run_boss_ve_process(dnconsole_path, tab_name, tab_index, num_ve=num_ve)

        # ---------------- 3. TỰ ĐỘNG TẮT CÔNG TẮC & LƯU CẤU HÌNH (GIỮ NGUYÊN Ô TÍCH) ----------------
        self.var_switch_C.set(False)
        self.after(0, self.save_config)
        self.after(0, self.log_info, "✅ [2/6: BOSS THẾ GIỚI] Đã thực thi hoàn tất quy trình! (Tự động tắt công tắc ON/OFF & giữ nguyên các ô tích)")

    def _run_40_npc_safezone(self, dnconsole_path: str, tab_index: str) -> bool:
        """PHẦN 1: QUY TRÌNH VỀ KHU AN TOÀN CỦA 40 NPC. Trả về True nếu khớp card_d/d_quangtruong.png"""
        if self._should_stop_card_D(): return False

        # 1. Đóng quảng cáo/thông báo
        self.after(0, self.log_info, "👁️ [40 NPC - Phần 1.1] Quét tìm nút 'login_x.png' (75%)...")
        lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
        if lx_x is not None and lx_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'login_x.png' tại ({lx_x}, {lx_y})! Click chọn ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
            time.sleep(0.4)

        # 2. Quét ảnh card_d/d_quangtruong.png (ngưỡng 75%)
        if self._should_stop_card_D(): return False
        self.after(0, self.log_info, "👁️ [40 NPC - Phần 1.2] Quét nhận diện ảnh Quảng Trường 'card_d/d_quangtruong.png' (75%)...")
        qt_x, qt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_quangtruong.png", threshold=0.75)
        if qt_x is not None and qt_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_d/d_quangtruong.png' tại ({qt_x}, {qt_y}) (Đã ở Quảng Trường) ➔ Bỏ qua thao tác Di Chuyển & chuyển thẳng đến menu chọn Khu!")
            return True

        # 3. Mở bảng Vị Trí
        if self._should_stop_card_D(): return False
        self.after(0, self.log_info, "👁️ [40 NPC - Phần 1.3] Quét tìm nút Vị Trí 'a_vitri.png' (85%)...")
        v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
        if v_x is not None and v_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_vitri.png' tại ({v_x}, {v_y})! Tap click chọn ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "👉 Chưa thấy 'a_vitri.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
            if self._should_stop_card_D(): return False
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_vitri.png' tại ({v_x}, {v_y})! Tap click chọn ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'a_vitri.png' trong bảng menu.")

        # 4. Về Khu An Toàn
        if self._should_stop_card_D(): return False
        self.after(0, self.log_info, "👉 [40 NPC - Phần 1.4] Click liên tục (435, 250) mỗi 0.5s cho tới khi xuất hiện nút Có 'card_c/c_co.png' (85%)...")
        while not self._should_stop_card_D():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_co.png", threshold=0.85)
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút Có 'card_c/c_co.png' tại ({co_x}, {co_y})! Dừng click (435, 250).")
                break
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 435 250"])
            time.sleep(0.5)

        if self._should_stop_card_D(): return False
        self.after(0, self.log_info, "👁️ [40 NPC - Phần 1.4] Click liên tục nút Có 'card_c/c_co.png' (0.5s mỗi lần) cho tới khi hết ảnh...")
        while not self._should_stop_card_D():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_co.png", threshold=0.85)
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút Có 'card_c/c_co.png' tại ({co_x}, {co_y}) ➔ Click vào vị trí ảnh...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {co_x} {co_y}"])
                time.sleep(0.5)
            else:
                self.after(0, self.log_info, "ℹ️ Không còn thấy ảnh nút Có 'card_c/c_co.png' ➔ Hoàn thành Về Khu An Toàn!")
                break

        if self._should_stop_card_D(): return False
        self.after(0, self.log_info, "⏳ [40 NPC - Bước 1.5] Hoãn 3.0s trước khi quét kiểm tra lại nút 'a_vitri.png'...")
        time.sleep(3.0)

        # 5. Thu gọn menu
        if self._should_stop_card_D(): return False
        self.after(0, self.log_info, "👁️ [40 NPC - Phần 1.5] Quét kiểm tra lại nút 'a_vitri.png' (85%)...")
        v_check_x, v_check_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
        if v_check_x is not None and v_check_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_vitri.png' vẫn còn tại ({v_check_x}, {v_check_y}) ➔ Click (1213, 648) để thu gọn menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "ℹ️ Không thấy nút 'a_vitri.png' ➔ Bỏ qua thu gọn menu.")

        return False

    def _run_40_npc_move_quang_truong(self, dnconsole_path: str, tab_index: str):
        """PHẦN 2: DI CHUYỂN ĐẾN QUẢNG TRƯỜNG (KHI Ô DI CHUYỂN ĐƯỢC TÍCH)"""
        if self._should_stop_card_D(): return

        self.after(0, self.log_info, "🚀 [40 NPC - Phần 2] Bắt đầu quy trình di chuyển đến Quảng Trường...")

        # 1. Tap (1000, 130) nghỉ 5s
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👉 1. Tap (1000, 130) ➔ Nghỉ 5s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1000 130"])
        for _ in range(5):
            if self._should_stop_card_D(): return
            time.sleep(1.0)

        # 2. Tap (120, 230) nghỉ 3s
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👉 2. Tap (120, 230) ➔ Nghỉ 3s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 120 230"])
        for _ in range(3):
            if self._should_stop_card_D(): return
            time.sleep(1.0)

        # 3. Tap (275, 125) nghỉ 2s
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👉 3. Tap (275, 125) ➔ Nghỉ 2s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 275 125"])
        for _ in range(2):
            if self._should_stop_card_D(): return
            time.sleep(1.0)

        # 4. Quét nhận diện ảnh card_d/d_cong.png và click vào ảnh (threshold=0.7) nghỉ 3s
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👁️ 4. Quét nhận diện ảnh 'card_d/d_cong.png' (70%)...")
        cg_x, cg_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_cong.png", threshold=0.70)
        if cg_x is not None and cg_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_d/d_cong.png' tại ({cg_x}, {cg_y})! Click chọn ➔ Nghỉ 3s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {cg_x} {cg_y}"])
        else:
            self.after(0, self.log_info, "ℹ️ Chưa thấy ảnh 'card_d/d_cong.png' ➔ Nghỉ 3s...")
        for _ in range(3):
            if self._should_stop_card_D(): return
            time.sleep(1.0)

        # 5. Tap (560, 455) nghỉ 4s
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👉 5. Tap (560, 455) ➔ Nghỉ 4s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 455"])
        for _ in range(4):
            if self._should_stop_card_D(): return
            time.sleep(1.0)

        # 6. Tap (135, 295) nghỉ 3s
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👉 6. Tap (135, 295) ➔ Nghỉ 3s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 135 295"])
        for _ in range(3):
            if self._should_stop_card_D(): return
            time.sleep(1.0)

        # 7. Quét nhận diện ảnh card_d/d_cong.png và click vào ảnh (threshold=0.7) nghỉ 5s
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👁️ 7. Quét nhận diện ảnh 'card_d/d_cong.png' lần 2 (70%)...")
        cg_x2, cg_y2 = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_cong.png", threshold=0.70)
        if cg_x2 is not None and cg_y2 is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_d/d_cong.png' tại ({cg_x2}, {cg_y2})! Click chọn ➔ Nghỉ 5s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {cg_x2} {cg_y2}"])
        else:
            self.after(0, self.log_info, "ℹ️ Chưa thấy ảnh 'card_d/d_cong.png' ➔ Nghỉ 5s...")
        for _ in range(5):
            if self._should_stop_card_D(): return
            time.sleep(1.0)

        # 8. Tap (215, 505) nghỉ 5s
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👉 8. Tap (215, 505) ➔ Nghỉ 5s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 215 505"])
        for _ in range(5):
            if self._should_stop_card_D(): return
            time.sleep(1.0)

    def _run_40_npc_select_khu(self, dnconsole_path: str, tab_index: str, selected_khu: str = "Cố Định", ignore_main_switch: bool = False):
        """PHẦN 3: CHỌN VỊ TRÍ THEO MENU KHU (Hỗ trợ thay đổi động Menu Khu khi đang Tạm Dừng)"""
        if self._should_stop_card_D(ignore_main_switch): return

        def get_current_target_khu_info() -> tuple:
            """Đọc động Menu Khu hiện tại (phòng trường hợp người dùng đổi Khu khi đang Tạm Dừng)"""
            curr_selected = self.combo_D_khu.get() if hasattr(self, 'combo_D_khu') else selected_khu
            if curr_selected == "Cố Định":
                return "Cố Định", None
            match = re.search(r'\d+', curr_selected)
            num = match.group(0) if match else "1"
            return curr_selected, f"khu/khu_{num}.png"

        def is_khu_panel_visible() -> bool:
            """Kiểm tra giao diện chọn khu có còn mở hay không"""
            chuyen_x, chuyen_y = self._find_template_on_screen(dnconsole_path, tab_index, "d_chuyenkhu.png", threshold=0.75)
            if chuyen_x is not None and chuyen_y is not None:
                return True
            qt_x, _ = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_quangtruong.png", threshold=0.75)
            if qt_x is not None:
                return True
            for test_k in ["khu/khu_10.png", "khu/khu_1.png", "khu/khu_5.png", "khu/khu_2.png"]:
                kx, _ = self._find_template_on_screen(dnconsole_path, tab_index, test_k, threshold=0.75)
                if kx is not None:
                    return True
            return False

        curr_khu_name, target_khu_img = get_current_target_khu_info()
        if curr_khu_name == "Cố Định" or target_khu_img is None:
            self.after(0, self.log_info, "ℹ️ [40 NPC - Phần 3] Menu Khu chọn 'Cố Định' ➔ Chuyển thẳng xuống Phần 4.")
            return

        self.after(0, self.log_info, f"🚀 [40 NPC - Phần 3] Bắt đầu quy trình chọn khu '{curr_khu_name}'...")

        # 1. Quét nhận diện ảnh card_d/d_quangtruong.png và click vào ảnh (threshold=0.85) nghỉ 0.4s
        if self._should_stop_card_D(ignore_main_switch): return
        self.after(0, self.log_info, "👁️ [40 NPC - Phần 3] Quét ảnh Quảng Trường 'card_d/d_quangtruong.png' (85%)...")
        qt_x, qt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_quangtruong.png", threshold=0.85)
        if qt_x is not None and qt_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_d/d_quangtruong.png' tại ({qt_x}, {qt_y})! Tap click ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {qt_x} {qt_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "ℹ️ Không tìm thấy ảnh 'card_d/d_quangtruong.png' trên màn hình.")

        def is_khu_panel_visible() -> bool:
            """Kiểm tra giao diện chọn khu có còn mở hay không"""
            chuyen_x, chuyen_y = self._find_template_on_screen(dnconsole_path, tab_index, "d_chuyenkhu.png", threshold=0.75)
            if chuyen_x is not None and chuyen_y is not None:
                return True
            k1_x, k1_y = self._find_template_on_screen(dnconsole_path, tab_index, "khu/khu_1.png", threshold=0.75)
            if k1_x is not None and k1_y is not None:
                return True
            k10_x, k10_y = self._find_template_on_screen(dnconsole_path, tab_index, "khu/khu_10.png", threshold=0.75)
            if k10_x is not None and k10_y is not None:
                return True
            return False

        def get_current_target_khu_info():
            """Lấy thông tin khu mục tiêu hiện tại"""
            curr = getattr(self, 'combo_D_khu', None)
            val = curr.get().strip() if curr else selected_khu
            if val.isdigit():
                return f"Khu {val}", f"khu/khu_{val}.png"
            return "Cố Định", None

        curr_khu_name, target_khu_img = get_current_target_khu_info()
        if target_khu_img is None:
            self.after(0, self.log_info, f"ℹ️ [40 NPC - Chọn Khu] Tùy chọn khu là '{curr_khu_name}' ➔ Bỏ qua bước cuộn đổi khu.")
            return

        self.after(0, self.log_info, f"🚀 [40 NPC - Chọn Khu] Bắt đầu quét & cuộn tìm khu mục tiêu '{curr_khu_name}' ('{target_khu_img}')...")

        found_khu_x, found_khu_y = None, None
        khu_success = False

        # 1. Quét tìm khu mục tiêu (Cuộn xuống tối đa 3 lần ➔ Cuộn lên tối đa 2 lần)
        for cycle in range(3):
            if self._should_stop_card_D(ignore_main_switch): break

            # a. Cuộn xuống (635, 400) -> (635, 195) tối đa 3 lần
            for swipe_down_cnt in range(3):
                if self._should_stop_card_D(ignore_main_switch): break
                if not is_khu_panel_visible():
                    self.after(0, self.log_info, "ℹ️ Giao diện chọn khu không còn mở ➔ Bỏ qua chọn khu.")
                    return

                curr_khu_name, target_khu_img = get_current_target_khu_info()
                if target_khu_img is None: return

                self.after(0, self.log_info, f"📜 [Cuộn xuống {swipe_down_cnt+1}/3] Quét tìm '{target_khu_img}' ({curr_khu_name})...")
                found_khu_x, found_khu_y = self._find_template_on_screen(dnconsole_path, tab_index, target_khu_img, threshold=0.85)
                if found_khu_x is not None and found_khu_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện ảnh khu mục tiêu '{target_khu_img}' tại ({found_khu_x}, {found_khu_y})!")
                    break

                k10_x, k10_y = self._find_template_on_screen(dnconsole_path, tab_index, "khu/khu_10.png", threshold=0.85)
                if k10_x is not None and k10_y is not None:
                    self.after(0, self.log_info, f"📍 Phát hiện 'khu/khu_10.png' tại ({k10_x}, {k10_y}) ➔ Dừng cuộn xuống...")
                    break

                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 635 400 635 195 1000"])
                time.sleep(1.0)

            if found_khu_x is not None and found_khu_y is not None:
                break

            # b. Cuộn lên (635, 195) -> (635, 525) tối đa 2 lần
            if self._should_stop_card_D(ignore_main_switch): break
            for swipe_up_cnt in range(2):
                if self._should_stop_card_D(ignore_main_switch): break
                if not is_khu_panel_visible():
                    self.after(0, self.log_info, "ℹ️ Giao diện chọn khu không còn mở ➔ Bỏ qua chọn khu.")
                    return

                curr_khu_name, target_khu_img = get_current_target_khu_info()
                if target_khu_img is None: return

                self.after(0, self.log_info, f"📜 [Cuộn lên {swipe_up_cnt+1}/2] Quét tìm '{target_khu_img}' ({curr_khu_name})...")
                found_khu_x, found_khu_y = self._find_template_on_screen(dnconsole_path, tab_index, target_khu_img, threshold=0.85)
                if found_khu_x is not None and found_khu_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện ảnh khu mục tiêu '{target_khu_img}' tại ({found_khu_x}, {found_khu_y})!")
                    break

                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 635 195 635 525 1000"])
                time.sleep(1.0)

            if found_khu_x is not None and found_khu_y is not None:
                break

        # 2. Xử lý khi TÌM THẤY Khu mục tiêu
        if found_khu_x is not None and found_khu_y is not None:
            curr_khu_name, target_khu_img = get_current_target_khu_info()
            self.after(0, self.log_info, f"👉 Tap click ảnh khu mục tiêu '{target_khu_img}' ({curr_khu_name}) tại ({found_khu_x}, {found_khu_y}) ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {found_khu_x} {found_khu_y}"])
            time.sleep(0.4)

            # Quét kiểm tra nghẽn khu (khu_sndd.png ngưỡng 45%)
            sndd_x, sndd_y = self._find_template_on_screen(dnconsole_path, tab_index, "khu/khu_sndd.png", threshold=0.45)
            if sndd_x is not None and sndd_y is not None:
                self.after(0, self.log_info, f"⚠️ Phát hiện 'khu/khu_sndd.png'! Thử tap lại vị trí ảnh khu tối đa 10 lần cho tới khi ảnh '{target_khu_img}' biến mất...")
                for retry in range(10):
                    if self._should_stop_card_D(ignore_main_switch): break
                    self.after(0, self.log_info, f"👉 [Thử lại nghẽn {retry+1}/10] Tap lại vị trí khu mục tiêu ({found_khu_x}, {found_khu_y})...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {found_khu_x} {found_khu_y}"])
                    time.sleep(1.0)

                    target_check_x, target_check_y = self._find_template_on_screen(dnconsole_path, tab_index, target_khu_img, threshold=0.85)
                    sndd_check_x, sndd_check_y = self._find_template_on_screen(dnconsole_path, tab_index, "khu/khu_sndd.png", threshold=0.45)

                    if target_check_x is None or sndd_check_x is None:
                        self.after(0, self.log_info, f"✅ Đã chuyển sang khu '{curr_khu_name}' thành công (ảnh khu mục tiêu đã biến mất khỏi giao diện)!")
                        khu_success = True
                        break

                if not khu_success:
                    self.after(0, self.log_info, f"⚠️ Sau 10 lần tap, khu mục tiêu '{target_khu_img}' vẫn không biến mất ➔ Dừng xử lý nghẽn khu mục tiêu, chuyển sang quét chọn khu ưu tiên (khu_xanh.png ➔ khu_vang.png)...")
            else:
                self.after(0, self.log_info, f"✅ Đã kết nối chuyển khu '{curr_khu_name}' thành công (không dính nghẽn)!")
                khu_success = True

            if khu_success:
                self.after(0, self.log_info, "⏳ Hoãn 3.0s hoàn tất chuyển khu...")
                time.sleep(3.0)
                return

        # 3. Khi KHÔNG THẤY Khu mục tiêu HOẶC sau 10 lần tap nghẽn khu không thành công:
        # Cuộn xuống - Cuộn lên quét tìm ảnh / tap ưu tiên theo thứ tự ảnh: (1. khu_xanh.png - 2. khu_vang.png)
        self.after(0, self.log_info, "🔍 [Chọn Khu Dự Phòng] Bắt đầu cuộn xuống - cuộn lên quét tìm khu ưu tiên (1. khu_xanh.png ➔ 2. khu_vang.png)...")
        priority_imgs = ["khu/khu_xanh.png", "khu/khu_vang.png"]

        for cycle in range(2):
            if self._should_stop_card_D(ignore_main_switch): break

            # a. Cuộn xuống quét tìm khu ưu tiên (tối đa 3 lần)
            for swipe_down_cnt in range(3):
                if self._should_stop_card_D(ignore_main_switch): break
                if not is_khu_panel_visible(): return

                for p_img in priority_imgs:
                    px, py = self._find_template_on_screen(dnconsole_path, tab_index, p_img, threshold=0.80)
                    if px is not None and py is not None:
                        self.after(0, self.log_info, f"🎯 Phát hiện ảnh khu ưu tiên '{p_img}' tại ({px}, {py})! Tap click...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px} {py}"])
                        time.sleep(3.0)
                        return

                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 635 400 635 195 1000"])
                time.sleep(1.0)

            # b. Cuộn lên quét tìm khu ưu tiên (tối đa 2 lần)
            for swipe_up_cnt in range(2):
                if self._should_stop_card_D(ignore_main_switch): break
                if not is_khu_panel_visible(): return

                for p_img in priority_imgs:
                    px, py = self._find_template_on_screen(dnconsole_path, tab_index, p_img, threshold=0.80)
                    if px is not None and py is not None:
                        self.after(0, self.log_info, f"🎯 Phát hiện ảnh khu ưu tiên '{p_img}' tại ({px}, {py})! Tap click...")
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {px} {py}"])
                        time.sleep(3.0)
                        return

                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 635 195 635 525 1000"])
                time.sleep(1.0)

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
            self.after(0, self.log_info, "👉 Chưa thấy 'card_b/b_doi.png' ➔ Tap nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
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
            self.after(0, self.log_info, "👉 [Vị Trí 1] Tap (560, 520) ➔ (560, 255) ➔ (1090, 110) (Hoãn 0.5s)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
            time.sleep(0.5)
        elif selected_team_char == "Vị Trí 2":
            self.after(0, self.log_info, "👉 [Vị Trí 2] Tap (560, 520) ➔ (560, 340) ➔ (1090, 110) (Hoãn 0.5s)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
            time.sleep(0.5)
        elif selected_team_char == "Vị Trí 3":
            self.after(0, self.log_info, "👉 [Vị Trí 3] Tap (560, 520) ➔ (560, 430) ➔ (1090, 110) (Hoãn 0.5s)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
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

        # Tap (1213, 648) ➔ Hoãn 0.4s để đóng menu giao diện Đội
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, "👉 Tap (1213, 648) ➔ Hoãn 0.4s để đóng menu giao diện Đội...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
        time.sleep(0.4)

    def _run_40_npc_su_kien_tang(self, dnconsole_path: str, tab_index: str, selected_tang: str, selected_team_char: str, selected_chien_dau: str = "Auto"):
        """THAO TÁC 3: CHIẾN ĐẤU (CHỈ THỰC THI KHỊ Ô CHIẾN ĐẤU VAR_D3 ĐƯỢC TÍCH)"""
        if self._should_stop_card_D(): return

        if not self.var_D3.get():
            self.after(0, self.log_info, "ℹ️ [40 NPC - Chiến Đấu] Ô 'Chiến Đấu' KHÔNG được tích -> Bỏ qua.")
            return

        self.after(0, self.log_info, f"🚀 [40 NPC - Chiến Đấu] Khởi chạy ô Chiến Đấu (Chế độ menu: '{selected_chien_dau}', Tầng: '{selected_tang}')...")

        if selected_chien_dau == "Auto":
            # =========================================================================
            # 📌 QUY TRÌNH 1: CHẾ ĐỘ MENU: AUTO
            # =========================================================================
            # 1. Đợi đến mốc thời gian sự kiện bắt đầu lúc 20H01 (20:01:00) - Đếm lặp mỗi 1s
            if self._should_stop_card_D(): return
            now = datetime.now()
            target_time = now.replace(hour=20, minute=1, second=0, microsecond=0)
            if now < target_time:
                self.after(0, self.log_info, f"⏳ [40 NPC - Auto] Đang chờ đến mốc 20:01:00 (Hiện tại: {now.strftime('%H:%M:%S')})...")
                while datetime.now() < target_time:
                    if self._should_stop_card_D(): return
                    time.sleep(1.0)

            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "🎯 [40 NPC - Auto] Đã đến mốc 20:01:00! Tiến hành kiểm tra tổ đội (Lần 1)...")

            # 2. Kiểm Tra Đủ Thành Viên Tổ Đội (Lần 1)
            if self._should_stop_card_D(): return
            list_B = list(getattr(self, 'list_G_B', []))
            if list_B:
                self.after(0, self.log_info, f"👁️ [40 NPC - Auto] Kiểm tra độ đầy đủ tổ đội Lần 1 ({len(list_B)} thành viên: {', '.join(list_B)})...")
                while not self._should_stop_card_D():
                    if self._should_stop_card_D(): return
                    lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
                    if lx_x is not None and lx_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                        time.sleep(0.4)

                    if self._should_stop_card_D(): return
                    b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
                    if b_doi_x is not None and b_doi_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                        time.sleep(0.4)
                    else:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
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
                            chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/{char_name}.png", threshold=0.80)
                        if chk_x is None or chk_y is None:
                            all_present = False
                            missing_list.append(char_name)

                    if all_present:
                        self.after(0, self.log_info, f"✅ [40 NPC - Auto] Lần 1: Tổ đội đã ĐỦ {len(list_B)} thành viên!")
                        lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
                        if lx_x is not None and lx_y is not None:
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                            time.sleep(0.4)
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                        time.sleep(0.4)
                        break
                    else:
                        self.after(0, self.log_info, f"⚠️ [40 NPC - Auto] Lần 1: Đội thiếu: {', '.join(missing_list)} ➔ Gọi Thao tác 1 Tổ Đội...")
                        lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
                        if lx_x is not None and lx_y is not None:
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                            time.sleep(0.4)
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                        time.sleep(0.4)
                        self._execute_card_G_for_mode(dnconsole_path, "", tab_index, mode=1)

            # 3. Vào Lôi Đài: Quét & tap Cổng Lôi Đài card_d/d_conglt.png (70%, hoãn 3s) ➔ Tap (505, 635) (hoãn 3s)
            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "👁️ [40 NPC - Auto] Quét tìm & tap ảnh 'card_d/d_conglt.png' (70%)...")
            clt_x, clt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_conglt.png", threshold=0.70)
            if clt_x is not None and clt_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'card_d/d_conglt.png' tại ({clt_x}, {clt_y})! Tap click ➔ Hoãn 3.0s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {clt_x} {clt_y}"])
                time.sleep(3.0)

            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "👉 [40 NPC - Auto] Tap (505, 635) ➔ Hoãn 3.0s bước vào Lôi Đài...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 505 635"])
            time.sleep(3.0)

            # 4. Kiểm tra lại độ đầy đủ của tổ đội lần 2 sau khi đã vào Lôi Đài
            if self._should_stop_card_D(): return
            if list_B:
                self.after(0, self.log_info, f"👁️ [40 NPC - Auto] Kiểm tra độ đầy đủ tổ đội Lần 2 khi đã vào Lôi Đài ({len(list_B)} thành viên)...")
                while not self._should_stop_card_D():
                    if self._should_stop_card_D(): return
                    lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
                    if lx_x is not None and lx_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                        time.sleep(0.4)

                    if self._should_stop_card_D(): return
                    b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
                    if b_doi_x is not None and b_doi_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                        time.sleep(0.4)
                    else:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
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
                            chk_x, chk_y = self._find_template_on_screen(dnconsole_path, tab_index, f"nhanvat/{char_name}.png", threshold=0.80)
                        if chk_x is None or chk_y is None:
                            all_present = False
                            missing_list.append(char_name)

                    if all_present:
                        self.after(0, self.log_info, f"✅ [40 NPC - Auto] Lần 2: Tổ đội đã ĐỦ {len(list_B)} thành viên!")
                        lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
                        if lx_x is not None and lx_y is not None:
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                            time.sleep(0.4)
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                        time.sleep(0.4)
                        break
                    else:
                        self.after(0, self.log_info, f"⚠️ [40 NPC - Auto] Lần 2: Đội thiếu: {', '.join(missing_list)} ➔ Gọi Thao tác 1 Tổ Đội...")
                        lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
                        if lx_x is not None and lx_y is not None:
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                            time.sleep(0.4)
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                        time.sleep(0.4)
                        self._execute_card_G_for_mode(dnconsole_path, "", tab_index, mode=1)

            # 5. Vào Trận Đánh (Quét di chuyển d_buoc1, d_buoc2 & quét d_chien)
            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "👉 [40 NPC - Auto] Tap (1110, 90) ➔ Hoãn 0.3s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1110 90"])
            time.sleep(0.3)

            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "👁️ [40 NPC - Auto] Quét & tap 'card_d/d_buoc1.png' (70%) ➔ Hoãn 6.0s...")
            b1_x, b1_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_buoc1.png", threshold=0.70)
            if b1_x is not None and b1_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b1_x} {b1_y}"])
                time.sleep(6.0)

            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "👁️ [40 NPC - Auto] Quét & tap 'card_d/d_buoc2.png' (70%) ➔ Hoãn 7.0s...")
            b2_x, b2_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_buoc2.png", threshold=0.70)
            if b2_x is not None and b2_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b2_x} {b2_y}"])
                time.sleep(7.0)

            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "👉 [40 NPC - Auto] Tap (1110, 90) ➔ Hoãn 0.3s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1110 90"])
            time.sleep(0.3)

            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "👉 [40 NPC - Auto] Tap liên tục (1240, 605) mỗi 0.4s (tối đa 20 lần) tìm ảnh 'card_d/d_chien.png' (70%)...")
            for retry in range(20):
                if self._should_stop_card_D(): return
                ch_x, ch_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_chien.png", threshold=0.70)
                if ch_x is not None and ch_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện 'card_d/d_chien.png' tại ({ch_x}, {ch_y})! Dừng click.")
                    break
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 605"])
                time.sleep(0.4)

            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "👉 [40 NPC - Auto] Tap (1135, 565) chọn trận ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1135 565"])
            time.sleep(0.4)

            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "👁️ [40 NPC - Auto] Quét & tap 'card_d/d_tieptheo.png' (70%) ➔ Hoãn 0.4s...")
            while not self._should_stop_card_D():
                tt1_x, tt1_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_tieptheo.png", threshold=0.70)
                if tt1_x is not None and tt1_y is not None:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {tt1_x} {tt1_y}"])
                    time.sleep(0.4)
                    break
                time.sleep(0.4)

            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "👁️ [40 NPC - Auto] Quét & tap 'card_d/d_vaotran.png' (75%) ➔ Hoãn 0.4s...")
            while not self._should_stop_card_D():
                vt_x, vt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_vaotran.png", threshold=0.75)
                if vt_x is not None and vt_y is not None:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {vt_x} {vt_y}"])
                    time.sleep(0.4)
                    break
                time.sleep(0.4)

            if self._should_stop_card_D(): return
            while not self._should_stop_card_D():
                tt2_x, tt2_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_tieptheo.png", threshold=0.70)
                if tt2_x is not None and tt2_y is not None:
                    while not self._should_stop_card_D():
                        tt_curr_x, tt_curr_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_tieptheo.png", threshold=0.70)
                        if tt_curr_x is None or tt_curr_y is None: break
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {tt_curr_x} {tt_curr_y}"])
                        time.sleep(0.4)
                    break
                time.sleep(0.4)

            # 6. Vòng Lặp Đánh Lôi Đài 35 Lượt
            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "🚀 [40 NPC - Auto] Bắt đầu vòng lặp Lôi Đài 35 lượt...")
            for loidai_round in range(1, 36):
                if self._should_stop_card_D(): return
                self.after(0, self.log_info, f"🔄 [40 NPC - Auto - Lượt {loidai_round}/35] Quét ảnh 'card_d/d_loidai.png' (80%) mỗi 1.0s...")
                while not self._should_stop_card_D():
                    ld_x, ld_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_loidai.png", threshold=0.80)
                    if ld_x is not None and ld_y is not None: break
                    time.sleep(1.0)

                if self._should_stop_card_D(): return
                time.sleep(0.3)

                if self._should_stop_card_D(): return
                self.after(0, self.log_info, f"👁️ [40 NPC - Auto - Lượt {loidai_round}/35] Quét & tap 'card_d/d_xacdinh.png' (80%) đến khi mất ảnh...")
                while not self._should_stop_card_D():
                    xd_x, xd_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_xacdinh.png", threshold=0.80)
                    if xd_x is not None and xd_y is not None:
                        while not self._should_stop_card_D():
                            xd_curr_x, xd_curr_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_xacdinh.png", threshold=0.80)
                            if xd_curr_x is None or xd_curr_y is None: break
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xd_curr_x} {xd_curr_y}"])
                            time.sleep(0.4)
                        break
                    time.sleep(0.4)

        elif selected_chien_dau == "Click":
            # =========================================================================
            # 📌 QUY TRÌNH 2: CHẾ ĐỘ MENU: CLICK
            # =========================================================================
            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "🚀 [40 NPC - Click] Bắt đầu Quy Trình 2: Chế độ Click...")

            # 2. Vào Trận Đánh
            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "👉 [40 NPC - Click] Tap liên tục (1240, 605) mỗi 0.4s (tối đa 20 lần) tìm 'card_d/d_chien.png' (70%)...")
            for retry in range(20):
                if self._should_stop_card_D(): return
                ch_x, ch_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_chien.png", threshold=0.70)
                if ch_x is not None and ch_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện 'card_d/d_chien.png' tại ({ch_x}, {ch_y})! Dừng click.")
                    break
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 605"])
                time.sleep(0.4)

            # Quét tìm nút Tiếp Theo card_d/d_tieptheo.png (70%, hoãn 0.4s). Nếu thấy tap đến khi mất ảnh, nếu không thấy bỏ qua
            if self._should_stop_card_D(): return
            tt_x, tt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_tieptheo.png", threshold=0.70)
            if tt_x is not None and tt_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện 'card_d/d_tieptheo.png' tại ({tt_x}, {tt_y})! Tap click đến khi mất ảnh...")
                while not self._should_stop_card_D():
                    tt_curr_x, tt_curr_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_tieptheo.png", threshold=0.70)
                    if tt_curr_x is None or tt_curr_y is None: break
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {tt_curr_x} {tt_curr_y}"])
                    time.sleep(0.4)
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "ℹ️ Không thấy 'card_d/d_tieptheo.png' ➔ Bỏ qua.")

            # Quét & tap nút Xác Định card_d/d_xacdinh.png (80%, 0.4s/lần) cho đến khi ảnh mất hoàn toàn để vào lượt
            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "👁️ [40 NPC - Click] Quét & tap 'card_d/d_xacdinh.png' (80%) mỗi 0.4s cho đến khi mất ảnh...")
            while not self._should_stop_card_D():
                xd_x, xd_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_xacdinh.png", threshold=0.80)
                if xd_x is not None and xd_y is not None:
                    while not self._should_stop_card_D():
                        xd_curr_x, xd_curr_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_xacdinh.png", threshold=0.80)
                        if xd_curr_x is None or xd_curr_y is None: break
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xd_curr_x} {xd_curr_y}"])
                        time.sleep(0.4)
                    break
                time.sleep(0.4)

            # 3. Vòng Lặp Đánh Lôi Đài 35 Lượt
            if self._should_stop_card_D(): return
            self.after(0, self.log_info, "🚀 [40 NPC - Click] Bắt đầu vòng lặp Lôi Đài 35 lượt...")
            for loidai_round in range(1, 36):
                if self._should_stop_card_D(): return
                self.after(0, self.log_info, f"🔄 [40 NPC - Click - Lượt {loidai_round}/35] Quét ảnh 'card_d/d_loidai.png' (80%) mỗi 1.0s...")
                while not self._should_stop_card_D():
                    ld_x, ld_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_loidai.png", threshold=0.80)
                    if ld_x is not None and ld_y is not None: break
                    time.sleep(1.0)

                if self._should_stop_card_D(): return
                time.sleep(0.3)

                if self._should_stop_card_D(): return
                self.after(0, self.log_info, f"👁️ [40 NPC - Click - Lượt {loidai_round}/35] Quét & tap 'card_d/d_xacdinh.png' (80%) đến khi mất ảnh...")
                while not self._should_stop_card_D():
                    xd_x, xd_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_xacdinh.png", threshold=0.80)
                    if xd_x is not None and xd_y is not None:
                        while not self._should_stop_card_D():
                            xd_curr_x, xd_curr_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_d/d_xacdinh.png", threshold=0.80)
                            if xd_curr_x is None or xd_curr_y is None: break
                            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {xd_curr_x} {xd_curr_y}"])
                            time.sleep(0.4)
                        break
                    time.sleep(0.4)


        # 7. BƯỚC 7: THỰC THI THAO TÁC THEO TẦNG SELECTED
        if self._should_stop_card_D(): return
        self.after(0, self.log_info, f"🚀 [Sự Kiện Tầng - Bước 7] Bắt đầu thực thi thao tác theo Tầng đã chọn: '{selected_tang}'...")
        if selected_tang == "Auto":
            self.after(0, self.log_info, "ℹ️ [Tầng - Auto] Lựa chọn 'Auto' ➔ Không có thao tác bổ sung trong mục Auto.")
        elif selected_tang == "38":
            self.after(0, self.log_info, "🚀 [Tầng 38] Khởi chạy khung thực thi Tầng 38 (Đang chờ cập nhật chi tiết thao tác từ người dùng)...")
            # KHUNG THỰC THI TẦNG 38 (Sẽ cập nhật thao tác sau)
            pass
        elif selected_tang == "39":
            self.after(0, self.log_info, "🚀 [Tầng 39] Khởi chạy khung thực thi Tầng 39 (Đang chờ cập nhật chi tiết thao tác từ người dùng)...")
            # KHUNG THỰC THI TẦNG 39 (Sẽ cập nhật thao tác sau)
            pass
        elif selected_tang == "40":
            self.after(0, self.log_info, "🚀 [Tầng 40] Khởi chạy khung thực thi Tầng 40 (Đang chờ cập nhật chi tiết thao tác từ người dùng)...")
            # KHUNG THỰC THI TẦNG 40 (Sẽ cập nhật thao tác sau)
            pass

    def _execute_card_D_40_npc(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """Thực thi Card 5: 40 NPC (D)"""
        if self._should_stop_card_D():
            self.after(0, self.log_info, "ℹ️ [5/6: 40 NPC] Công tắc ON/OFF đang TẮT -> Bỏ qua.")
            return

        checked = [
            ("Di Chuyển", self.var_D1),
            ("Tổ Đội", self.var_D2),
            ("Chiến Đấu", self.var_D3)
        ]
        active_items = [(name, var) for name, var in checked if var.get()]
        if not active_items:
            self.after(0, self.log_info, "ℹ️ [5/6: 40 NPC] Công tắc ON nhưng không có mục nào được chọn -> Tắt công tắc & Bỏ qua.")
            self.var_switch_D.set(False)
            self.after(0, self.save_config)
            return

        selected_khu = self.combo_D_khu.get() if hasattr(self, 'combo_D_khu') else "Cố Định"
        selected_team_char = self.combo_D_team_char.get() if hasattr(self, 'combo_D_team_char') else "Xuất Chiến"
        selected_chien_dau = self.combo_D_chien_dau.get() if hasattr(self, 'combo_D_chien_dau') else "Auto"
        selected_tang = selected_khu

        info_details = []
        if self.var_D1.get():
            info_details.append(f"Di Chuyển (STT: '{selected_khu}')")
        if self.var_D2.get():
            info_details.append(f"Tổ Đội (Vị trí: '{selected_team_char}')")
        if self.var_D3.get():
            info_details.append(f"Chiến Đấu (Chế độ: '{selected_chien_dau}')")

        self.after(0, self.log_info, f"▶️ [5/6: 40 NPC] Đang thực thi {len(info_details)} mục đã chọn: {', '.join(info_details)}...")

        # =========================================================================
        # 📌 THAO TÁC 1: DI CHUYỂN & CHỌN KHU (KHI Ô VAR_D1 ĐƯỢC TÍCH)
        # =========================================================================
        if self.var_D1.get():
            self.after(0, self.log_info, f"🚀 [40 NPC - 1. Di Chuyển] Khởi chạy ô Di Chuyển (Menu Khu: '{selected_khu}')...")
            is_already_at_quangtruong = self._run_40_npc_safezone(dnconsole_path, tab_index)
            if not is_already_at_quangtruong:
                self._run_40_npc_move_quang_truong(dnconsole_path, tab_index)
            self._run_40_npc_select_khu(dnconsole_path, tab_index, selected_khu)
        else:
            self.after(0, self.log_info, "ℹ️ [40 NPC - 1. Di Chuyển] Ô 'Di Chuyển' KHÔNG được tích ➔ Bỏ qua.")

        # =========================================================================
        # 📌 THAO TÁC 2: TỔ ĐỘI & ĐỔI VỊ TRÍ TƯỚNG (KHI Ô VAR_D2 ĐƯỢC TÍCH)
        # =========================================================================
        if self.var_D2.get():
            self.after(0, self.log_info, f"🚀 [40 NPC - 2. Tổ Đội] Khởi chạy ô Tổ Đội (Vị trí: '{selected_team_char}')...")
            self._run_40_npc_team_and_char_position(dnconsole_path, tab_index, selected_team_char)
            self._execute_card_G_for_mode(dnconsole_path, tab_name, tab_index, mode=1)
        else:
            self.after(0, self.log_info, "ℹ️ [40 NPC - 2. Tổ Đội] Ô 'Tổ Đội' KHÔNG được tích ➔ Bỏ qua.")

        # =========================================================================
        # 📌 THAO TÁC 3: CHIẾN ĐẤU (KHI Ô VAR_D3 ĐƯỢC TÍCH)
        # =========================================================================
        if self.var_D3.get():
            self.after(0, self.log_info, f"🚀 [40 NPC - 3. Chiến Đấu] Khởi chạy ô Chiến Đấu (Chế độ: '{selected_chien_dau}', Tầng: '{selected_tang}')...")
            self._run_40_npc_su_kien_tang(dnconsole_path, tab_index, selected_tang, selected_team_char, selected_chien_dau)
        else:
            self.after(0, self.log_info, "ℹ️ [40 NPC - 3. Chiến Đấu] Ô 'Chiến Đấu' KHÔNG được tích ➔ Bỏ qua.")

        # Tự động tắt công tắc ON/OFF (False) & nhả ô Tạm Dừng sau khi hoàn thành, giữ nguyên các ô check
        self.var_switch_D.set(False)
        if hasattr(self, 'var_pause_D'):
            self.var_pause_D.set(False)
        self.after(0, self.save_config)
        self.after(0, self.log_info, "✅ [5/6: 40 NPC] Đã thực thi hoàn tất dứt điểm! (Đã tự động tắt công tắc ON/OFF & giữ nguyên các ô tích)")

    def _run_nhi_kieu_safezone(self, dnconsole_path: str, tab_index: str):
        """PHẦN 1: QUY TRÌNH VỀ KHU AN TOÀN CỦA NHỊ KIỀU (CARD F / 2K)"""
        if self._should_stop_card_F(): return
        self.after(0, self.log_info, "👁️ [Nhị Kiều - SafeZone] Quét tìm nút 'login_x.png'...")
        lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "login_x.png", threshold=0.75)
        if lx_x is not None and lx_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'login_x.png' tại ({lx_x}, {lx_y})! Click chọn ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
            time.sleep(0.4)

        if self._should_stop_card_F(): return
        self.after(0, self.log_info, "👁️ [Nhị Kiều - SafeZone] Quét tìm nút Vị Trí 'a_vitri.png' (85%)...")
        v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
        if v_x is not None and v_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_vitri.png' tại ({v_x}, {v_y})! Tap click trực tiếp ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "👉 Chưa thấy 'a_vitri.png' ➔ Click nút xanh lá góc dưới phải (1213, 648) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
            if self._should_stop_card_F(): return
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
            if v_x is not None and v_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút 'a_vitri.png' tại ({v_x}, {v_y})! Tap click trực tiếp ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'a_vitri.png' trong bảng menu.")

        if self._should_stop_card_F(): return
        self.after(0, self.log_info, "👉 [Nhị Kiều - SafeZone] Click liên tục (435, 250) mỗi 0.5s cho đến khi xuất hiện nút Có 'card_c/c_co.png' (85%)...")
        while not self._should_stop_card_F():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_co.png", threshold=0.85)
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện nút Có 'card_c/c_co.png' tại ({co_x}, {co_y})! Dừng click (435, 250).")
                break
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 435 250"])
            time.sleep(0.5)

        if self._should_stop_card_F(): return
        self.after(0, self.log_info, "👁️ [Nhị Kiều - SafeZone] Click liên tục nút Có 'card_c/c_co.png' (0.5s mỗi lần) cho tới khi hết ảnh...")
        while not self._should_stop_card_F():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_co.png", threshold=0.85)
            if co_x is not None and co_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút Có 'card_c/c_co.png' tại ({co_x}, {co_y}) ➔ Click vào vị trí ảnh...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {co_x} {co_y}"])
                time.sleep(0.5)
            else:
                self.after(0, self.log_info, "ℹ️ Không còn thấy ảnh nút Có 'card_c/c_co.png' ➔ Hoàn thành Về Khu An Toàn!")
                break

        if self._should_stop_card_F(): return
        self.after(0, self.log_info, "⏳ [Nhị Kiều - SafeZone] Hoãn 3.0s trước khi quét kiểm tra lại nút 'a_vitri.png'...")
        time.sleep(3.0)

        if self._should_stop_card_F(): return
        self.after(0, self.log_info, "👁️ [Nhị Kiều - SafeZone] Quét kiểm tra lại nút 'a_vitri.png' (85%)...")
        v_check_x, v_check_y = self._find_template_on_screen(dnconsole_path, tab_index, "a_vitri.png", threshold=0.85)
        if v_check_x is not None and v_check_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'a_vitri.png' vẫn còn tại ({v_check_x}, {v_check_y}) ➔ Click (1213, 648) để thu gọn menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "ℹ️ Không thấy nút 'a_vitri.png' ➔ Bỏ qua thu gọn menu.")

    def _run_nhi_kieu_di_chuyen(self, dnconsole_path: str, tab_index: str):
        """THAO TÁC 1: DI CHUYỂN CỦA NHỊ KIỀU (CARD F / 2K)"""
        if self._should_stop_card_F(): return

        self.after(0, self.log_info, "🚀 [Nhị Kiều - Thao Tác Di Chuyển] Bắt đầu quy trình Di Chuyển...")

        # 1. Mở menu Sự Kiện , Tap ảnh ➔ Hoãn 0.4s
        self.after(0, self.log_info, "👁️ [Nhị Kiều - Di Chuyển] Quét tìm ảnh 'card_e/e_sukien.png' (85%)...")
        sk_x, sk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_e/e_sukien.png", threshold=0.85)
        if sk_x is not None and sk_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_e/e_sukien.png' tại ({sk_x}, {sk_y})! Tap click ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {sk_x} {sk_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "👉 Chưa thấy 'e_sukien.png' ➔ Tap tọa độ (1240, 680) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
            time.sleep(0.4)
            if self._should_stop_card_F(): return
            sk_x, sk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_e/e_sukien.png", threshold=0.85)
            if sk_x is not None and sk_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_e/e_sukien.png' tại ({sk_x}, {sk_y})! Tap click ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {sk_x} {sk_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy 'card_e/e_sukien.png' trong bảng menu.")

        # 2. Chọn Nhị Kiều , Tap ảnh ➔ Hoãn 0.4s
        if self._should_stop_card_F(): return
        self.after(0, self.log_info, "👁️ [Nhị Kiều - Di Chuyển] Quét tìm ảnh 'card_e/e_nhikieu.png' (85%)...")
        nk_x, nk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_e/e_nhikieu.png", threshold=0.85)
        if nk_x is not None and nk_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_e/e_nhikieu.png' tại ({nk_x}, {nk_y})! Tap click ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {nk_x} {nk_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "ℹ️ Không tìm thấy 'card_e/e_nhikieu.png' ➔ Bỏ qua.")

        # 3. Thu gọn menu Sự Kiện , Nếu ảnh vẫn còn ➔ Tap (1240, 680) để thu gọn ➔ Hoãn 0.4s
        if self._should_stop_card_F(): return
        self.after(0, self.log_info, "👁️ [Nhị Kiều - Di Chuyển] Quét kiểm tra ảnh 'card_e/e_sukien.png' (85%)...")
        sk_check_x, sk_check_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_e/e_sukien.png", threshold=0.85)
        if sk_check_x is not None and sk_check_y is not None:
            self.after(0, self.log_info, "🎯 Ảnh 'card_e/e_sukien.png' vẫn còn ➔ Tap tọa độ (1240, 680) để thu gọn ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "ℹ️ Không thấy 'card_e/e_sukien.png' ➔ Bỏ qua.")

        # 4. Tap bước 5 , tap (665, 60) ➔ Hoãn 3.0s
        if self._should_stop_card_F(): return
        self.after(0, self.log_info, "👉 [Nhị Kiều - Di Chuyển] Tap tọa độ (665, 60) ➔ Hoãn 3.0s...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 665 60"])
        for _ in range(3):
            if self._should_stop_card_F(): return
            time.sleep(1.0)

        # 5. Mở Cổng , Quét tìm cho đến khi thấy ➔ Tap ảnh ➔ Hoãn 3.0s
        if self._should_stop_card_F(): return
        self.after(0, self.log_info, "👁️ [Nhị Kiều - Di Chuyển] Quét tìm ảnh 'card_e/e_cong.png' (85%) cho đến khi thấy...")
        cg_x, cg_y = None, None
        while not self._should_stop_card_F():
            cg_x, cg_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_e/e_cong.png", threshold=0.85)
            if cg_x is not None and cg_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_e/e_cong.png' tại ({cg_x}, {cg_y})! Tap click vào ảnh ➔ Hoãn 3.0s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {cg_x} {cg_y}"])
                break
            self.after(0, self.log_info, "⏳ Chưa phát hiện 'card_e/e_cong.png' ➔ Thử lại sau 1.0s...")
            time.sleep(1.0)

        for _ in range(3):
            if self._should_stop_card_F(): return
            time.sleep(1.0)

        # 6. Quét liên tục mỗi 0.3s tìm ảnh card_e/e_tieptheo.png (80%) cho đến khi thấy thì tap vào ảnh
        # đợi 0.5s nếu còn xuất hiện thì nhấp tiếp cho đến khi mất hoàn toàn ảnh, hoãn 3s
        if self._should_stop_card_F(): return
        self.after(0, self.log_info, "👁️ [Nhị Kiều - Di Chuyển] Quét liên tục mỗi 0.3s tìm ảnh 'card_e/e_tieptheo.png' (80%)...")
        
        tt_x, tt_y = None, None
        while not self._should_stop_card_F():
            tt_x, tt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_e/e_tieptheo.png", threshold=0.80)
            if tt_x is not None and tt_y is not None:
                self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_e/e_tieptheo.png' tại ({tt_x}, {tt_y})!")
                break
            time.sleep(0.3)

        if self._should_stop_card_F(): return

        self.after(0, self.log_info, "👉 Tap nhấp liên tục vào ảnh 'card_e/e_tieptheo.png' (đợi 0.5s mỗi lần) cho tới khi mất hoàn toàn...")
        while not self._should_stop_card_F():
            tt_x, tt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_e/e_tieptheo.png", threshold=0.80)
            if tt_x is not None and tt_y is not None:
                self.after(0, self.log_info, f"👉 Tap nhấp 'card_e/e_tieptheo.png' tại ({tt_x}, {tt_y}) ➔ Hoãn 0.5s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {tt_x} {tt_y}"])
                time.sleep(0.5)
            else:
                self.after(0, self.log_info, "✅ Ảnh 'card_e/e_tieptheo.png' đã mất hoàn toàn!")
                break

        if self._should_stop_card_F(): return
        self.after(0, self.log_info, "⏳ [Nhị Kiều - Di Chuyển] Hoãn 3.0s hoàn tất thao tác Di Chuyển!")
        for _ in range(3):
            if self._should_stop_card_F(): return
            time.sleep(1.0)

    def _run_nhi_kieu_to_doi(self, dnconsole_path: str, tab_index: str, selected_team_char: str):
        """THAO TÁC 2: TỔ ĐỘI VÀ CHUYỂN ĐỔI VỊ TRÍ NHÂN VẬT (NHỊ KIỀU / CARD 2K)"""
        if self._should_stop_card_F(): return

        self.after(0, self.log_info, f"🚀 [Nhị Kiều - 2. Tổ Đội] Kích hoạt Tổ Đội (Vị trí: '{selected_team_char}')...")

        if selected_team_char == "Xuất Chiến":
            self.after(0, self.log_info, "ℹ️ Vị trí 'Xuất Chiến': Giữ nguyên vị trí hiện tại ➔ Bỏ qua bước đổi đội hình.")
            return

        # Quét nút Đội card_b/b_doi.png (85%) (Đã xóa hoãn 3s ban đầu)
        if self._should_stop_card_F(): return
        self.after(0, self.log_info, "👁️ [Nhị Kiều - Tổ Đội] Quét tìm ảnh 'card_b/b_doi.png' (85%)...")
        b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
        if b_doi_x is not None and b_doi_y is not None:
            self.after(0, self.log_info, f"🎯 Mắt thần phát hiện 'card_b/b_doi.png' tại ({b_doi_x}, {b_doi_y})! Tap click ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
            time.sleep(0.4)
        else:
            self.after(0, self.log_info, "👉 Chưa thấy 'card_b/b_doi.png' ➔ Tap nút xanh (1240, 680) mở menu ➔ Hoãn 0.4s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
            time.sleep(0.4)
            if self._should_stop_card_F(): return
            b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85)
            if b_doi_x is not None and b_doi_y is not None:
                self.after(0, self.log_info, f"🎯 Phát hiện nút 'card_b/b_doi.png' tại ({b_doi_x}, {b_doi_y})! Tap click ➔ Hoãn 0.4s...")
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                time.sleep(0.4)
            else:
                self.after(0, self.log_info, "⚠️ Chưa quét thấy biểu tượng 'card_b/b_doi.png' trong bảng menu.")

        # Thao tác đổi vị trí nhân vật (Mỗi lượt tap hoãn 0.5s)
        if self._should_stop_card_F(): return
        if selected_team_char == "Vị Trí 1":
            self.after(0, self.log_info, "👉 [Vị Trí 1] Tap (560, 520) ➔ (560, 255) ➔ (1090, 110) (Hoãn 0.5s)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 255"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
            time.sleep(0.5)
        elif selected_team_char == "Vị Trí 2":
            self.after(0, self.log_info, "👉 [Vị Trí 2] Tap (560, 520) ➔ (560, 340) ➔ (1090, 110) (Hoãn 0.5s)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 340"])
            time.sleep(0.5)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1090 110"])
            time.sleep(0.5)
        elif selected_team_char == "Vị Trí 3":
            self.after(0, self.log_info, "👉 [Vị Trí 3] Tap (560, 520) ➔ (560, 430) ➔ (1090, 110) (Hoãn 0.5s)...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 520"])
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

        if self._should_stop_card_F(): return
        self.after(0, self.log_info, "👉 Tap (1240, 680) ➔ Hoãn 0.4s để đóng menu giao diện Đội...")
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 680"])
        time.sleep(0.4)

    def _run_nhi_kieu_tang_tret_10(self, dnconsole_path: str, tab_index: str, loop_count: int = 10, mode_name: str = "1 - 10", run_stages_1_to_3: bool = True, only_stages_1_to_3: bool = False):
        """THAO TÁC CHI TIẾT MỐC ĐÀI: Trệt (Giai đoạn 1-3), 1 - 10 (Giai đoạn 4-7 x10) & 11 - 14 (Giai đoạn 4-7 x4)"""
        # Helper 1: Lặp tìm và tap ảnh cho đến khi xuất hiện
        def tap_image_until_found(img_path: str, threshold: float, sleep_after: float):
            if self._should_stop_card_F(): return
            is_nhanvat = "nhanvat" in img_path.lower()
            current_threshold = 0.60 if is_nhanvat else threshold
            self.after(0, self.log_info, f"👁️ [{mode_name}] Quét tìm ảnh '{img_path}' ({int(current_threshold*100)}%)...")
            while not self._should_stop_card_F():
                x, y = self._find_template_on_screen(dnconsole_path, tab_index, img_path, threshold=current_threshold)
                if x is not None and y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần phát hiện '{img_path}' tại ({x}, {y})! Tap click vào ảnh...")
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {x} {y}"])
                    for _ in range(int(sleep_after)):
                        if self._should_stop_card_F(): return
                        time.sleep(1.0)
                    break
                time.sleep(1.0)

        # Helper 2: Quét 0.3s tìm card_e/e_tieptheo.png (75%) -> Tap & nhấp cho đến khi mất hoàn toàn ảnh
        def process_tieptheo_sequence():
            if self._should_stop_card_F(): return
            self.after(0, self.log_info, f"👁️ [{mode_name}] Quét liên tục 0.3s tìm ảnh 'card_e/e_tieptheo.png' (75%)...")
            while not self._should_stop_card_F():
                tt_x, tt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_e/e_tieptheo.png", threshold=0.75)
                if tt_x is not None and tt_y is not None:
                    self.after(0, self.log_info, f"🎯 Phát hiện 'card_e/e_tieptheo.png' tại ({tt_x}, {tt_y})!")
                    break
                time.sleep(0.3)

            if self._should_stop_card_F(): return
            self.after(0, self.log_info, "👉 Tap nhấp 'card_e/e_tieptheo.png' (đợi 0.5s mỗi lần) cho tới khi mất hoàn toàn...")
            while not self._should_stop_card_F():
                tt_x, tt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_e/e_tieptheo.png", threshold=0.75)
                if tt_x is not None and tt_y is not None:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {tt_x} {tt_y}"])
                    time.sleep(0.5)
                else:
                    self.after(0, self.log_info, "✅ 'card_e/e_tieptheo.png' đã mất hoàn toàn!")
                    break

        # Helper 3: Quét 1s tìm ảnh chỉ định (85%) (KHÔNG tap) -> Sau đó tìm 0.3s card_e/e_tieptheo.png & tap đến khi mất
        def wait_check_image_and_process_tieptheo(check_img_path: str, sleep_after: float = 2.0):
            if self._should_stop_card_F(): return
            self.after(0, self.log_info, f"👁️ [{mode_name}] Quét liên tục 1s tìm ảnh '{check_img_path}' (85%) (không tap)...")
            while not self._should_stop_card_F():
                tr_x, tr_y = self._find_template_on_screen(dnconsole_path, tab_index, check_img_path, threshold=0.85)
                if tr_x is not None and tr_y is not None:
                    self.after(0, self.log_info, f"🎯 Mắt thần phát hiện '{check_img_path}' tại ({tr_x}, {tr_y})! (Không tap, chuyển quét e_tieptheo)")
                    break
                time.sleep(1.0)

            if self._should_stop_card_F(): return
            process_tieptheo_sequence()

            if self._should_stop_card_F(): return
            self.after(0, self.log_info, f"⏳ Hoãn {sleep_after}s...")
            for _ in range(int(sleep_after)):
                if self._should_stop_card_F(): return
                time.sleep(1.0)

        # -------------------------------------------------------------
        # THỰC THI GIAI ĐOẠN 1 -> 3 (NẾU CÓ)
        if run_stages_1_to_3:
            tap_image_until_found("card_e/e_buoc1.png", threshold=0.85, sleep_after=2.0)
            process_tieptheo_sequence()
            wait_check_image_and_process_tieptheo("card_e/e_tret.png", sleep_after=2.0)
            tap_image_until_found("card_e/e_buoc1.png", threshold=0.85, sleep_after=2.0)

            tap_image_until_found("card_e/e_buoc2.png", threshold=0.80, sleep_after=2.0)
            process_tieptheo_sequence()
            wait_check_image_and_process_tieptheo("card_e/e_tret.png", sleep_after=2.0)
            tap_image_until_found("card_e/e_buoc2.png", threshold=0.80, sleep_after=4.0)

            if self._should_stop_card_F(): return
            self.after(0, self.log_info, "👉 Tap tọa độ (225, 220) ➔ Hoãn 2.0s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 225 220"])
            for _ in range(2):
                if self._should_stop_card_F(): return
                time.sleep(1.0)

            process_tieptheo_sequence()
            wait_check_image_and_process_tieptheo("card_e/e_tret.png", sleep_after=2.0)
            tap_image_until_found("card_e/e_buoc3.png", threshold=0.80, sleep_after=5.0)

            if only_stages_1_to_3:
                self.after(0, self.log_info, f"✅ Hoàn tất dứt điểm mốc '{mode_name}' (Giai đoạn 1 - 3)!")
                return
        else:
            self.after(0, self.log_info, f"ℹ️ [{mode_name}] Bỏ qua Giai đoạn 1, 2, 3 ➔ Bắt đầu thẳng Vòng lặp Giai đoạn 4, 5, 6, 7.")

        # --- LẶP GIAI ĐOẠN 4, 5, 6, 7 (TỔNG loop_count LẦN) ---
        for loop_idx in range(1, loop_count + 1):
            if self._should_stop_card_F(): return
            self.after(0, self.log_info, f"🔄 [{mode_name}] Bắt đầu Vòng lặp Giai đoạn 4, 5, 6, 7 (Lần {loop_idx}/{loop_count})...")

            # --- GIAI ĐOẠN 4: BƯỚC 4 ---
            if self._should_stop_card_F(): return
            self.after(0, self.log_info, f"👉 [Lần {loop_idx}/{loop_count} - Giai Đoạn 4] Tap (805, 160) ➔ Hoãn 3.0s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 805 160"])
            for _ in range(3):
                if self._should_stop_card_F(): return
                time.sleep(1.0)

            if self._should_stop_card_F(): return
            self.after(0, self.log_info, f"👉 [Lần {loop_idx}/{loop_count} - Giai Đoạn 4] Tap (1025, 150) ➔ Hoãn 1.0s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1025 150"])
            time.sleep(1.0)

            process_tieptheo_sequence()
            wait_check_image_and_process_tieptheo("card_e/e_tang.png", sleep_after=2.0)

            # --- GIAI ĐOẠN 5: BƯỚC 5 ---
            if self._should_stop_card_F(): return
            self.after(0, self.log_info, f"👉 [Lần {loop_idx}/{loop_count} - Giai Đoạn 5] Tap (670, 60) ➔ Hoãn 3.0s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 670 60"])
            for _ in range(3):
                if self._should_stop_card_F(): return
                time.sleep(1.0)

            if self._should_stop_card_F(): return
            self.after(0, self.log_info, f"👉 [Lần {loop_idx}/{loop_count} - Giai Đoạn 5] Tap (560, 50) ➔ Hoãn 3.0s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 560 50"])
            for _ in range(3):
                if self._should_stop_card_F(): return
                time.sleep(1.0)

            process_tieptheo_sequence()
            wait_check_image_and_process_tieptheo("card_e/e_tang.png", sleep_after=2.0)

            # --- GIAI ĐOẠN 6: BƯỚC 6 ---
            if self._should_stop_card_F(): return
            self.after(0, self.log_info, f"👉 [Lần {loop_idx}/{loop_count} - Giai Đoạn 6] Tap (200, 250) ➔ Hoãn 3.0s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 200 250"])
            for _ in range(3):
                if self._should_stop_card_F(): return
                time.sleep(1.0)

            if self._should_stop_card_F(): return
            self.after(0, self.log_info, f"👉 [Lần {loop_idx}/{loop_count} - Giai Đoạn 6] Tap (730, 50) ➔ Hoãn 3.0s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 730 50"])
            for _ in range(3):
                if self._should_stop_card_F(): return
                time.sleep(1.0)

            if self._should_stop_card_F(): return
            self.after(0, self.log_info, f"👉 [Lần {loop_idx}/{loop_count} - Giai Đoạn 6] Tap (1030, 160) ➔ Hoãn 2.0s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1030 160"])
            for _ in range(2):
                if self._should_stop_card_F(): return
                time.sleep(1.0)

            process_tieptheo_sequence()
            wait_check_image_and_process_tieptheo("card_e/e_tang.png", sleep_after=2.0)

            # --- GIAI ĐOẠN 7: BƯỚC 7 ---
            if self._should_stop_card_F(): return
            self.after(0, self.log_info, f"👉 [Lần {loop_idx}/{loop_count} - Giai Đoạn 7] Tap (1250, 170) ➔ Hoãn 4.0s...")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1250 170"])
            for _ in range(4):
                if self._should_stop_card_F(): return
                time.sleep(1.0)

        self.after(0, self.log_info, f"✅ Hoàn tất dứt điểm mốc '{mode_name}' (Vòng lặp Giai đoạn 4-7 x{loop_count} lần)!")

    def _run_nhi_kieu_tang(self, dnconsole_path: str, tab_index: str, selected_tang: str):
        """THAO TÁC 3: TẦNG / ĐÀI (NHỊ KIỀU)"""
        if self._should_stop_card_F(): return

        self.after(0, self.log_info, f"🚀 [Nhị Kiều - 3. Tầng] Khởi chạy ô Tầng (Mốc: '{selected_tang}')...")

        if selected_tang == "Trệt":
            self._run_nhi_kieu_tang_tret_10(dnconsole_path, tab_index, loop_count=0, mode_name="Trệt", run_stages_1_to_3=True, only_stages_1_to_3=True)
        elif selected_tang == "1 - 10":
            self._run_nhi_kieu_tang_tret_10(dnconsole_path, tab_index, loop_count=10, mode_name="1 - 10", run_stages_1_to_3=False, only_stages_1_to_3=False)
        elif selected_tang == "11 - 14":
            self._run_nhi_kieu_tang_tret_10(dnconsole_path, tab_index, loop_count=4, mode_name="11 - 14", run_stages_1_to_3=False, only_stages_1_to_3=False)
        else:
            self.after(0, self.log_info, f"ℹ️ Mốc '{selected_tang}' đang được cập nhật thao tác chi tiết...")

    def _execute_card_F_nhi_kieu(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """Thực thi Card 6: NHỊ KIỀU (F)"""
        if self._should_stop_card_F():
            self.after(0, self.log_info, "ℹ️ [6/6: NHỊ KIỀU] Công tắc ON/OFF đang TẮT -> Bỏ qua.")
            return

        checked = [
            ("Di Chuyển", self.var_F1),
            ("Tổ Đội", self.var_F2),
            ("Tầng", self.var_F3)
        ]
        active_items = [(name, var) for name, var in checked if var.get()]
        if not active_items:
            self.after(0, self.log_info, "ℹ️ [6/6: NHỊ KIỀU] Công tắc ON nhưng không có mục nào được chọn -> Tắt công tắc & Bỏ qua.")
            self.var_switch_F.set(False)
            self.after(0, self.save_config)
            return

        selected_team_char = self.combo_F_team_char.get() if hasattr(self, 'combo_F_team_char') else "Xuất Chiến"
        selected_tang = self.combo_F_tang.get() if hasattr(self, 'combo_F_tang') else "Trệt"

        item_names = [name for name, var in active_items]
        self.after(0, self.log_info, f"▶️ [6/6: NHỊ KIỀU] Đang thực thi {len(item_names)} mục đã chọn: {', '.join(item_names)}...")

        # 📌 1. THAO TÁC DI CHUYỂN & VỀ KHU AN TOÀN (KHI Ô VAR_F1 ĐƯỢC TÍCH)
        if self.var_F1.get():
            self._run_nhi_kieu_safezone(dnconsole_path, tab_index)
            self._run_nhi_kieu_di_chuyen(dnconsole_path, tab_index)
        else:
            self.after(0, self.log_info, "ℹ️ [Nhị Kiều - 1. Di Chuyển] Ô 'Di Chuyển' KHÔNG được tích ➔ Bỏ qua.")

        # 📌 2. THAO TÁC TỔ ĐỘI
        if self.var_F2.get():
            self._run_nhi_kieu_to_doi(dnconsole_path, tab_index, selected_team_char)
            self._execute_card_G_for_mode(dnconsole_path, tab_name, tab_index, mode=1)
        else:
            self.after(0, self.log_info, "ℹ️ [Nhị Kiều - 2. Tổ Đội] Ô 'Tổ Đội' KHÔNG được tích ➔ Bỏ qua.")

        # 📌 3. THAO TÁC TẦNG
        if self.var_F3.get():
            self._run_nhi_kieu_tang(dnconsole_path, tab_index, selected_tang)
        else:
            self.after(0, self.log_info, "ℹ️ [Nhị Kiều - 3. Tầng] Ô 'Tầng' KHÔNG được tích ➔ Bỏ qua.")

        # Tự động tắt công tắc ON/OFF (False) & nhả ô Tạm Dừng sau khi hoàn thành, giữ nguyên các ô check
        self.var_switch_F.set(False)
        if hasattr(self, 'var_pause_F'):
            self.var_pause_F.set(False)
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

    def _find_template_on_screen(self, dnconsole_path: str, tab_index: str, template_filename: str, threshold: float = 0.85, check_color: bool = False):
        """👁️ Mắt Thần OpenCV: Khớp vị trí hình ảnh mẫu .png trong thư mục con assets/ với độ chính xác cao & kiểm tra độ sáng màu sắc nút"""
        clean_name = os.path.basename(template_filename)
        possible_paths = []

        for base in [get_bundle_dir(), get_app_dir()]:
            assets_dir = os.path.join(base, "assets")
            possible_paths.extend([
                os.path.join(assets_dir, template_filename),
                os.path.join(assets_dir, "card_b", clean_name),
                os.path.join(assets_dir, "card_a", clean_name),
                os.path.join(assets_dir, "card_c", clean_name),
                os.path.join(assets_dir, "card_d", clean_name),
                os.path.join(assets_dir, "card_e", clean_name),
                os.path.join(assets_dir, "card_f", clean_name),
                os.path.join(assets_dir, "login", clean_name),
                os.path.join(assets_dir, "server", clean_name),
                os.path.join(base, template_filename)
            ])
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
        
        is_nkn = ("nkn" in template_filename.lower()) or ("diemdanh" in template_filename.lower()) or ("veboss" in template_filename.lower())
        max_attempts = 3 if is_nkn else 1

        for attempt in range(max_attempts):
            # Chụp ảnh màn hình LDPlayer qua ADB
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell screencap -p /sdcard/mat_than.png"])
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
                    template = _read_img_unicode(tmpl_path, cv2.IMREAD_UNCHANGED)

                    if screen is not None and template is not None:
                        # Nới lỏng ngưỡng mặc định cho file nkn.png hoặc c_veboss.png (do có hiệu ứng chuyển động nhẹ)
                        current_threshold = threshold
                        if "veboss" in template_filename.lower():
                            current_threshold = min(threshold, 0.65)
                        elif is_nkn:
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

                                        # Nếu ảnh thực tế trên màn hình bị tối/mờ hơn ảnh mẫu chuẩn tươi sáng -> Bỏ qua
                                        if (tmpl_v_mean - crop_v_mean) > 18 or abs(crop_v_mean - tmpl_v_mean) > 25:
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
