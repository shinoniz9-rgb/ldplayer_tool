# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import threading
import subprocess
import tempfile
import cv2
import numpy as np
import customtkinter as ctk

# Thử import pystray & PIL cho tính năng khay hệ thống (System Tray / thanh mini)
try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_PYSTRAY = True
except ImportError:
    HAS_PYSTRAY = False

# Thiết lập theme tối hiện đại
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
CONFIG_FILE = os.path.join(BASE_DIR, "config_danh_thuong.json")
MAIN_CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

def get_resource_path(relative_path: str):
    """Tìm file tài nguyên trong sys._MEIPASS (PyInstaller đóng gói) hoặc thư mục dự án"""
    if hasattr(sys, '_MEIPASS'):
        p = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(p):
            return p
    p = os.path.join(BASE_DIR, relative_path)
    if os.path.exists(p):
        return p
    return None

# Bảng tọa độ 10 mốc mục tiêu
DANH_THUONG_TARGET_COORDS = {
    "Sau 1": (560, 170),
    "Sau 2": (480, 205),
    "Sau 3": (390, 250),
    "Sau 4": (320, 290),
    "Sau 5": (240, 330),
    "Trước 1": (640, 215),
    "Trước 2": (560, 250),
    "Trước 3": (470, 290),
    "Trước 4": (395, 335),
    "Trước 5": (320, 375),
}

TARGET_OPTIONS = list(DANH_THUONG_TARGET_COORDS.keys())


class DanhThuongTool(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Cấu hình cửa sổ siêu nhỏ gọn, ghim trên cùng màn hình
        self.title("TS Origin - Đánh Thường")
        self.geometry("305x88")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        # Đăng ký sự kiện nút X: Thu nhỏ xuống khay hệ thống (System Tray) thay vì tắt hẳn
        self.tray_icon = None
        self.protocol("WM_DELETE_WINDOW", self._on_close_window)
        self.bind("<Map>", self._on_window_mapped)

        # Thiết lập Icon nếu có
        icon_path = get_resource_path(os.path.join("assets", "app_icon.ico"))
        if icon_path and os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        # Biến trạng thái
        self.ld_path = self._load_ld_path()
        self.tab_map = {}  # { "LDPlayer-1": "0", ... }
        self.selected_tab_name = None
        self.selected_tab_index = None

        self.var_danh_thuong = ctk.BooleanVar(value=False)
        self.stop_requested = False
        self._stop_event = threading.Event()
        self._thread_worker = None

        # Bộ nhớ đệm mắt thần siêu tốc (In-Memory Cache)
        self._active_adb_device = {}
        self._screen_cache = {}
        self._template_cache = {}
        self._tmpl_path_cache = {}

        self._build_ui()
        self._load_config()
        self._start_tab_monitor()

    def _load_ld_path(self):
        """Đọc đường dẫn LDPlayer từ config.json hoặc fallback mặc định"""
        if os.path.exists(MAIN_CONFIG_FILE):
            try:
                with open(MAIN_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    p = data.get("ld_path")
                    if p and os.path.exists(p):
                        return p
            except Exception:
                pass
        for default_p in [r"C:\LDPlayer\LDPlayer9", r"D:\LDPlayer\LDPlayer9", r"C:\LDPlayer\LDPlayer4"]:
            if os.path.exists(default_p):
                return default_p
        return r"C:\LDPlayer\LDPlayer9"

    def _get_dnconsole_path(self):
        if not self.ld_path or not os.path.exists(self.ld_path):
            return None
        for name in ["ldconsole.exe", "dnconsole.exe"]:
            p = os.path.join(self.ld_path, name)
            if os.path.exists(p):
                return p
        return None

    def _exec_cmd(self, cmd_list, text=False):
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
            return subprocess.run(cmd_list, timeout=12, **kwargs)
        except Exception:
            return None

    # =========================================================================
    # GIAO DIỆN CHUẨN TOOL MINI (THIẾT KẾ CARD BO GÓC & NÚT ĐỒNG BỘ)
    # =========================================================================
    def _build_ui(self):
        # Khung Card bo góc 8px đồng bộ theo chuẩn Card của Tool chính
        self.card_main = ctk.CTkFrame(self, corner_radius=8)
        self.card_main.pack(fill="both", expand=True, padx=6, pady=6)

        # HÀNG 1: Menu chọn Tab LD | Nút Stop (Chuẩn màu xám ghi & đỏ)
        row1 = ctk.CTkFrame(self.card_main, fg_color="transparent", height=28)
        row1.pack(fill="x", padx=6, pady=(6, 4))
        row1.pack_propagate(False)

        self.combo_tabs = ctk.CTkOptionMenu(
            row1,
            values=["Đang quét Tab..."],
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            height=26,
            width=195,
            dynamic_resizing=False,
            command=self._on_tab_selected
        )
        self.combo_tabs.pack(side="left")

        self.btn_stop = ctk.CTkButton(
            row1,
            text="Stop",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#FFFFFF",
            fg_color="#DC2626",
            hover_color="#B91C1C",
            height=26,
            width=80,
            corner_radius=6,
            command=self.dung_hoat_dong
        )
        self.btn_stop.pack(side="right")

        # HÀNG 2: [ ] [ Sau 1 ▼ ] (Menu drop 10 mốc) | Nhãn trạng thái (không icon)
        row2 = ctk.CTkFrame(self.card_main, fg_color="transparent", height=28)
        row2.pack(fill="x", padx=6, pady=(0, 6))
        row2.pack_propagate(False)

        col_dt = ctk.CTkFrame(row2, fg_color="transparent", height=26)
        col_dt.pack(side="left")

        self.chk_dt = ctk.CTkCheckBox(
            col_dt,
            text="",
            variable=self.var_danh_thuong,
            command=self._on_danh_thuong_toggled,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            fg_color="#EA580C",
            hover_color="#C2410C",
            checkmark_color="#FFFFFF",
            checkbox_width=16,
            checkbox_height=16,
            border_width=2,
            corner_radius=5,
            width=16
        )
        self.chk_dt.pack(side="left", padx=(0, 4))

        self.combo_target = ctk.CTkOptionMenu(
            col_dt,
            values=TARGET_OPTIONS,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="normal"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
            text_color="#FFFFFF",
            dropdown_text_color="#FFFFFF",
            height=26,
            width=128,
            dynamic_resizing=False,
            fg_color="#374151",
            button_color="#4B5563",
            button_hover_color="#6B7280",
            corner_radius=6,
            command=self._on_target_changed
        )
        self.combo_target.set(TARGET_OPTIONS[0])
        self.combo_target.pack(side="left")

        # Nhãn trạng thái thuần text (không biểu tượng/emoji theo yêu cầu)
        self.lbl_status = ctk.CTkLabel(
            row2,
            text="Sẵn sàng",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="normal"),
            text_color="#9CA3AF",
            anchor="e"
        )
        self.lbl_status.pack(side="right", fill="x", expand=True, padx=(4, 0))

    def _on_target_changed(self, choice):
        self._save_config()

    def _set_status(self, text: str, color: str = "#9CA3AF"):
        """Cập nhật nhãn trạng thái trực tiếp trên luồng giao diện (thuần text không emoji)"""
        try:
            self.after(0, lambda: self.lbl_status.configure(text=text, text_color=color))
        except Exception:
            pass

    # =========================================================================
    # TÍNH NĂNG KHAY HỆ THỐNG (SYSTEM TRAY / THANH MINI)
    # =========================================================================
    def _create_tray_icon_image(self):
        """Tạo icon đại diện cho khay hệ thống"""
        icon_path = get_resource_path(os.path.join("assets", "app_icon.ico"))
        if icon_path and os.path.exists(icon_path):
            try:
                return Image.open(icon_path)
            except Exception:
                pass
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
                pystray.MenuItem("Mở Tool Đánh Thường", self._show_window_from_tray, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Thoát Ứng Dụng", self._exit_app_from_tray)
            )
            self.tray_icon = pystray.Icon("TS_Danh_Thuong", icon_img, "TS Origin - Đánh Thường", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception:
            pass

    def _on_close_window(self):
        """Sự kiện bấm nút X trên thanh tiêu đề: Lưu vị trí và thu nhỏ xuống khay hệ thống"""
        self._save_config()
        if HAS_PYSTRAY:
            self.withdraw()  # Ẩn cửa sổ chính
            if self.tray_icon is None:
                self._setup_system_tray()
        else:
            self.iconify()  # Thu nhỏ xuống Taskbar nếu không có thư viện tray

    def _on_window_mapped(self, event=None):
        """Đảm bảo đồng bộ khi cửa sổ được hệ thống unhide / restore"""
        try:
            if self.state() == "normal":
                self.attributes("-topmost", True)
        except Exception:
            pass

    def _show_window_from_tray(self, icon=None, item=None):
        """Mở lại giao diện từ khay hệ thống"""
        self.after(0, self._restore_window_ui)

    def _restore_window_ui(self):
        try:
            self.deiconify()
            self.lift()
            self.focus_force()
            self.attributes("-topmost", True)
        except Exception:
            pass

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
            self.stop_requested = True
            self._stop_event.set()
        except Exception:
            pass
        try:
            self._save_config()
        except Exception:
            pass
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass
        # Thoát sạch tiến trình và giải phóng Mutex lập tức
        os._exit(0)

    # =========================================================================
    # QUẢN LÝ TAB & CẤU HÌNH (TỰ ĐỘNG QUÉT KHI MỞ / ĐÓNG LDPLAYER)
    # =========================================================================
    def _start_tab_monitor(self):
        """Bắt đầu luồng kiểm tra Tab LD ngầm định kỳ khi rảnh rỗi"""
        threading.Thread(target=self._tab_monitor_loop, daemon=True).start()

    def _tab_monitor_loop(self):
        # Quét lần đầu
        self._scan_tabs_logic(first_run=True)
        while not self.stop_requested:
            # Ngủ 4 giây giữa các lần quét (ngắt ngay khi stop)
            for _ in range(40):
                if self.stop_requested:
                    return
                time.sleep(0.1)

            # Chỉ tự động quét khi Đánh Thường đang KHÔNG chạy để dùng 0% CPU và không can thiệp ADB
            if not self.var_danh_thuong.get():
                self._scan_tabs_logic(first_run=False)

    def _scan_tabs_logic(self, first_run: bool = False):
        dnconsole_path = self._get_dnconsole_path()
        if not dnconsole_path:
            if first_run:
                self.after(0, lambda: self.combo_tabs.configure(values=["Không thấy LD"]))
                self._set_status("Lỗi đường dẫn LD", "#EF4444")
            return

        res = self._exec_cmd([dnconsole_path, "list2"], text=True)
        if not res or not res.stdout:
            if first_run or not self.tab_map:
                self.after(0, lambda: self.combo_tabs.configure(values=["Chưa mở LD"]))
                self._set_status("Chưa mở LD", "#EF4444")
            return

        tab_names = []
        new_map = {}
        for line in res.stdout.strip().split("\n"):
            line = line.strip()
            if line:
                parts = line.split(",")
                if len(parts) >= 2:
                    idx = parts[0].strip()
                    name = parts[1].strip()
                    tab_names.append(name)
                    new_map[name] = idx

        # Nếu danh sách tab không đổi và không phải lần chạy đầu ➔ Bỏ qua, không tốn tài nguyên redraw
        if new_map == self.tab_map and not first_run:
            return

        self.tab_map = new_map
        if tab_names:
            saved_tab = self.selected_tab_name
            target_tab = saved_tab if saved_tab in tab_names else tab_names[0]
            self.selected_tab_name = target_tab
            self.selected_tab_index = self.tab_map.get(target_tab)

            self.after(0, lambda: self.combo_tabs.configure(values=tab_names))
            self.after(0, lambda: self.combo_tabs.set(target_tab))
            if first_run or self.lbl_status.cget("text") in ("Chưa mở LD", "Không thấy LD", "0 Tab LD"):
                self._set_status(f"Tab: {target_tab}", "#10B981")
        else:
            self.after(0, lambda: self.combo_tabs.configure(values=["Không có Tab"]))
            self._set_status("0 Tab LD", "#EF4444")

    def _on_tab_selected(self, choice):
        self.selected_tab_name = choice
        self.selected_tab_index = self.tab_map.get(choice)
        self._save_config()
        self._set_status(f"Chọn: {choice}", "#10B981")

    def _load_config(self):
        """Tải cấu hình tab, mốc và vị trí tọa độ cửa sổ trên màn hình"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.selected_tab_name = cfg.get("selected_tab")
                    target_val = cfg.get("selected_target")
                    if target_val and target_val in TARGET_OPTIONS and hasattr(self, 'combo_target'):
                        self.combo_target.set(target_val)
                    pos_x = cfg.get("window_x")
                    pos_y = cfg.get("window_y")
                    if pos_x is not None and pos_y is not None:
                        sw = self.winfo_screenwidth()
                        sh = self.winfo_screenheight()
                        if 0 <= pos_x <= sw - 80 and 0 <= pos_y <= sh - 50:
                            self.geometry(f"305x88+{pos_x}+{pos_y}")
            except Exception:
                pass

    def _save_config(self):
        """Lưu cấu hình và tọa độ cửa sổ hiện tại"""
        try:
            cfg_data = {}
            if os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                except Exception:
                    cfg_data = {}

            cfg_data["selected_tab"] = self.selected_tab_name
            if hasattr(self, 'combo_target'):
                cfg_data["selected_target"] = self.combo_target.get()
            # Chỉ ghi đè tọa độ khi cửa sổ đang mở bình thường
            if self.state() == "normal":
                x = self.winfo_x()
                y = self.winfo_y()
                if x >= 0 and y >= 0:
                    cfg_data["window_x"] = x
                    cfg_data["window_y"] = y

            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg_data, f, indent=4)
        except Exception:
            pass

    # =========================================================================
    # ĐIỀU KHIỂN BẬT / DỪNG
    # =========================================================================
    def _on_danh_thuong_toggled(self):
        self._save_config()
        if self.var_danh_thuong.get():
            self.stop_requested = False
            self._stop_event.clear()

            if not self.selected_tab_index:
                self._set_status("Chưa chọn Tab!", "#EF4444")
                self.var_danh_thuong.set(False)
                return

            dnconsole_path = self._get_dnconsole_path()
            if not dnconsole_path:
                self._set_status("Lỗi LDPlayer!", "#EF4444")
                self.var_danh_thuong.set(False)
                return

            # Khóa menu chọn Tab và menu chọn Mốc khi đang chạy để chống đổi nhầm
            try:
                self.combo_tabs.configure(state="disabled")
                self.combo_target.configure(state="disabled")
            except Exception:
                pass

            self._set_status("Đang khởi động...", "#F59E0B")
            if self._thread_worker and self._thread_worker.is_alive():
                return
            self._thread_worker = threading.Thread(
                target=self._run_danh_thuong_standalone,
                args=(dnconsole_path, self.selected_tab_name, self.selected_tab_index),
                daemon=True
            )
            self._thread_worker.start()
        else:
            self.stop_requested = True
            self._stop_event.set()
            try:
                self.combo_tabs.configure(state="normal")
                self.combo_target.configure(state="normal")
            except Exception:
                pass
            self._set_status("Đã dừng", "#EF4444")

    def dung_hoat_dong(self):
        """Nút Stop khẩn cấp: ngắt tức thì trong < 0.02s"""
        self.stop_requested = True
        self._stop_event.set()
        self.var_danh_thuong.set(False)
        try:
            self.combo_tabs.configure(state="normal")
            self.combo_target.configure(state="normal")
        except Exception:
            pass
        self._set_status("Đã dừng", "#EF4444")

    def _sleep_with_stop_check(self, seconds: float) -> bool:
        """Tạm dừng ngủ ngầm siêu tốc: Đánh thức tức thì (< 0.02s) khi dừng"""
        start = time.time()
        while time.time() - start < seconds:
            if self.stop_requested or self._stop_event.is_set() or not self.var_danh_thuong.get():
                return True
            time.sleep(0.02)
        return False

    # =========================================================================
    # MẮT THẦN OPENCV SIÊU TỐC & ADB DIRECT STREAM (ZERO DISK I/O)
    # =========================================================================
    def _capture_screen_fast(self, dnconsole_path: str, tab_index: str, max_cache_age: float = 0.35):
        tab_key = str(tab_index)
        cached = self._screen_cache.get(tab_key)
        now = time.time()

        if cached is not None and (now - cached["time"]) < max_cache_age:
            return cached["img"]

        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        adb_path = os.path.join(self.ld_path, "adb.exe")

        if os.path.exists(adb_path):
            try:
                tab_num = int(tab_index)
            except Exception:
                tab_num = 0
            port_5554 = 5554 + (tab_num * 2)
            port_5555 = 5555 + (tab_num * 2)
            candidate_devices = [f"emulator-{port_5554}", f"127.0.0.1:{port_5555}"]

            active_dev = self._active_adb_device.get(tab_key)
            devices_to_try = [active_dev] if active_dev in candidate_devices else candidate_devices

            for dev in devices_to_try:
                try:
                    res = subprocess.run(
                        [adb_path, "-s", dev, "exec-out", "screencap", "-p"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=3,
                        creationflags=creation_flags
                    )
                    if res.returncode == 0 and len(res.stdout) > 10000:
                        img = cv2.imdecode(np.frombuffer(res.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)
                        if img is not None and img.shape[0] > 0 and img.shape[1] > 0:
                            self._active_adb_device[tab_key] = dev
                            self._screen_cache[tab_key] = {"time": time.time(), "img": img}
                            self._capture_fail_count = 0
                            return img
                except Exception:
                    pass

            if active_dev in candidate_devices:
                for dev in candidate_devices:
                    if dev == active_dev:
                        continue
                    try:
                        res = subprocess.run(
                            [adb_path, "-s", dev, "exec-out", "screencap", "-p"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            timeout=3,
                            creationflags=creation_flags
                        )
                        if res.returncode == 0 and len(res.stdout) > 10000:
                            img = cv2.imdecode(np.frombuffer(res.stdout, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if img is not None and img.shape[0] > 0 and img.shape[1] > 0:
                                self._active_adb_device[tab_key] = dev
                                self._screen_cache[tab_key] = {"time": time.time(), "img": img}
                                self._capture_fail_count = 0
                                return img
                    except Exception:
                        pass

        # Fallback qua dnconsole screencap nếu direct ADB không sẵn sàng
        try:
            temp_local = os.path.join(tempfile.gettempdir(), f"ts_dt_cap_{tab_index}.png")
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell screencap -p /sdcard/ts_dt.png"])
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"pull /sdcard/ts_dt.png \"{temp_local}\""])
            if os.path.exists(temp_local) and os.path.getsize(temp_local) > 0:
                d = np.fromfile(temp_local, dtype=np.uint8)
                img = cv2.imdecode(d, cv2.IMREAD_COLOR)
                if os.path.exists(temp_local):
                    os.remove(temp_local)
                if img is not None and img.shape[0] > 0:
                    self._screen_cache[tab_key] = {"time": time.time(), "img": img}
                    self._capture_fail_count = 0
                    return img
        except Exception:
            pass

        self._capture_fail_count = getattr(self, '_capture_fail_count', 0) + 1
        if self._capture_fail_count >= 8:
            self._set_status("Mất kết nối LD!", "#EF4444")
        return None

    def _find_template_on_screen(self, dnconsole_path: str, tab_index: str, template_filename: str, threshold: float = 0.85, region: tuple = None):
        cached_path = self._tmpl_path_cache.get(template_filename)
        if cached_path is None:
            clean_name = os.path.basename(template_filename)
            candidates = [
                template_filename,
                os.path.join("assets", template_filename),
                os.path.join("assets", "card_f", clean_name),
                os.path.join("assets", "card_f", "skill", clean_name)
            ]
            for rel in candidates:
                res_p = get_resource_path(rel)
                if res_p and os.path.isfile(res_p):
                    cached_path = res_p
                    self._tmpl_path_cache[template_filename] = res_p
                    break
            if cached_path is None:
                return None, None

        tmpl_info = self._template_cache.get(cached_path)
        if tmpl_info is None:
            try:
                d = np.fromfile(cached_path, dtype=np.uint8)
                raw = cv2.imdecode(d, cv2.IMREAD_UNCHANGED)
                if raw is not None:
                    if len(raw.shape) == 3 and raw.shape[2] == 4:
                        bgr = cv2.cvtColor(raw, cv2.COLOR_BGRA2BGR)
                    else:
                        bgr = raw
                    tmpl_info = {"bgr": bgr, "shape": bgr.shape}
                    self._template_cache[cached_path] = tmpl_info
            except Exception:
                return None, None

        if tmpl_info is None:
            return None, None

        template_bgr = tmpl_info["bgr"]
        screen = self._capture_screen_fast(dnconsole_path, tab_index, max_cache_age=0.35)
        if screen is None:
            return None, None

        offset_x, offset_y = 0, 0
        search_screen = screen
        if region is not None:
            rx1, ry1, rx2, ry2 = region
            h, w = screen.shape[:2]
            rx1 = max(0, min(rx1, w - 1))
            ry1 = max(0, min(ry1, h - 1))
            rx2 = max(rx1 + 1, min(rx2, w))
            ry2 = max(ry1 + 1, min(ry2, h))
            search_screen = screen[ry1:ry2, rx1:rx2]
            offset_x, offset_y = rx1, ry1

        th, tw = template_bgr.shape[:2]
        sh, sw = search_screen.shape[:2]
        if sh < th or sw < tw:
            return None, None

        res = cv2.matchTemplate(search_screen, template_bgr, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val >= threshold:
            center_x = offset_x + max_loc[0] + tw // 2
            center_y = offset_y + max_loc[1] + th // 2
            return center_x, center_y

        return None, None

    def _tap(self, dnconsole_path: str, tab_index: str, x: int, y: int):
        """Thực hiện tap vào tọa độ (x, y) với ưu tiên Direct ADB siêu tốc, fallback qua dnconsole"""
        if self.stop_requested or self._stop_event.is_set() or not self.var_danh_thuong.get():
            return
        tab_key = str(tab_index)
        active_dev = self._active_adb_device.get(tab_key)
        adb_path = os.path.join(self.ld_path, "adb.exe")
        if active_dev and os.path.exists(adb_path):
            try:
                creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                res = subprocess.run(
                    [adb_path, "-s", active_dev, "shell", "input", "tap", str(x), str(y)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                    creationflags=creation_flags
                )
                if res.returncode == 0:
                    return
            except Exception:
                pass
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {x} {y}"])

    def _tap_login_auto_twice(self, dnconsole_path: str, tab_index: str):
        """Tap 2 lần cách nhau 0.15s vào tọa độ nút Auto (190, 140)"""
        for _ in range(2):
            if self.stop_requested or self._stop_event.is_set() or not self.var_danh_thuong.get():
                break
            self._tap(dnconsole_path, tab_index, 190, 140)
            time.sleep(0.15)

    def _execute_danh_thuong_sequence(self, dnconsole_path: str, tab_index: str, tx: int, ty: int):
        """Thực thi chuỗi 4 cú tap tuần tự hoãn 0s: (1160, 680) -> (tx, ty) -> (1160, 680) -> (tx, ty)
        Mỗi cú tap kiểm tra cờ dừng khẩn cấp ngay lập tức."""
        # 1. Tap tọa độ (1160, 680) hoãn 0s
        self._tap(dnconsole_path, tab_index, 1160, 680)
        if not self.var_danh_thuong.get() or self.stop_requested:
            return

        # 2. Tap tọa độ (theo mốc chọn ở menu drop Sau 1 > Sau 5 , Trước 1 > Trước 5) hoãn 0s
        self._tap(dnconsole_path, tab_index, tx, ty)
        if not self.var_danh_thuong.get() or self.stop_requested:
            return

        # 3. Tap tọa độ (1160, 680) hoãn 0s
        self._tap(dnconsole_path, tab_index, 1160, 680)
        if not self.var_danh_thuong.get() or self.stop_requested:
            return

        # 4. Tap tọa độ (theo mốc chọn ở menu drop Sau 1 > Sau 5 , Trước 1 > Trước 5) hoãn 0s
        self._tap(dnconsole_path, tab_index, tx, ty)

    # =========================================================================
    # CORE LOGIC CHẾ ĐỘ ĐÁNH THƯỜNG (KẾ THỪA 100% CƠ CHẾ BƯỚC 0 CỦA BUFF TRAIN)
    # =========================================================================
    def _run_danh_thuong_standalone(self, dnconsole_path: str, tab_name: str, tab_index: str):
        try:
            while self.var_danh_thuong.get() and not self.stop_requested:
                self._handle_danh_thuong_turn(dnconsole_path, tab_name, tab_index)
                if self._sleep_with_stop_check(0.1):
                    break
        except Exception:
            self._set_status("Lỗi tiến trình", "#EF4444")
        finally:
            self._thread_worker = None
            try:
                self.after(0, lambda: self.combo_tabs.configure(state="normal"))
                self.after(0, lambda: self.combo_target.configure(state="normal"))
            except Exception:
                pass
            if self.stop_requested or not self.var_danh_thuong.get():
                self._set_status("Đã dừng", "#EF4444")
            else:
                self._set_status("Sẵn sàng", "#9CA3AF")

    def _handle_danh_thuong_turn(self, dnconsole_path: str, tab_name: str, tab_index: str):
        if not self.var_danh_thuong.get() or self.stop_requested:
            return

        self._set_status("Chờ lượt đánh...", "#38BDF8")

        found_turn = False
        while not self.stop_requested and self.var_danh_thuong.get():
            # 1. Quét song song f_vaotran.png (ROI 1215, 0, 1280, 45, 80%) kiểm tra hết trận / ngoài trận
            vt_x, vt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_vaotran.png", threshold=0.80, region=(1215, 0, 1280, 45))
            if vt_x is not None and vt_y is not None:
                self._set_status("Hết trận ➔ Tap Auto", "#F59E0B")
                self._tap_login_auto_twice(dnconsole_path, tab_index)
                self._set_status("Chờ trận mới...", "#F59E0B")
                while not self.stop_requested and self.var_danh_thuong.get():
                    if self._sleep_with_stop_check(0.35):
                        return
                    # Kiểm tra f_dung.png xuất hiện (đã vào trận và đến lượt)
                    d_chk_x, d_chk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_dung.png", threshold=0.80, region=(640, 0, 1280, 145))
                    if d_chk_x is not None and d_chk_y is not None:
                        found_turn = True
                        break
                    # Kiểm tra f_vaotran.png đã biến mất chưa
                    vt_chk_x, vt_chk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_vaotran.png", threshold=0.80, region=(1215, 0, 1280, 45))
                    if vt_chk_x is None or vt_chk_y is None:
                        break

                # Hoãn 0.6s để màn hình load đủ giao diện trận đấu
                self._set_status("Vào trận ➔ Chờ load", "#38BDF8")
                if self._sleep_with_stop_check(0.6):
                    return

                if found_turn:
                    break
                else:
                    self._set_status("Chờ lượt đánh...", "#38BDF8")

            # 2. Quét f_dung.png (ROI 640, 0, 1280, 145, 80%) kiểm tra đến lượt đánh (CHỈ QUÉT, KHÔNG TAP)
            d_x, d_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_dung.png", threshold=0.80, region=(640, 0, 1280, 145))
            if d_x is not None and d_y is not None:
                found_turn = True
                break

            if self._sleep_with_stop_check(0.35):
                return

        if not found_turn or not self.var_danh_thuong.get() or self.stop_requested:
            return

        # =====================================================================
        # THAO TÁC MỚI KHI ĐẾN LƯỢT ĐÁNH (F_DUNG XUẤT HIỆN)
        # =====================================================================
        selected_target = self.combo_target.get() if hasattr(self, 'combo_target') else "Sau 1"
        target_coord = DANH_THUONG_TARGET_COORDS.get(selected_target, (560, 170))
        tx, ty = target_coord

        self._set_status(f"Đến lượt ➔ Tap {selected_target}", "#10B981")

        # 1. Tap tọa độ (1160, 680) hoãn 0s
        # 2. Tap tọa độ (theo mốc chọn ở menu drop Sau 1 > Sau 5 , Trước 1 > Trước 5) hoãn 0s
        # 3. Tap tọa độ (1160, 680) hoãn 0s
        # 4. Tap tọa độ (theo mốc chọn ở menu drop Sau 1 > Sau 5 , Trước 1 > Trước 5) hoãn 0s
        self._execute_danh_thuong_sequence(dnconsole_path, tab_index, tx, ty)

        if not self.var_danh_thuong.get() or self.stop_requested:
            return

        # 5. Hoãn (Sleep) 3.0s (sử dụng sleep ngắt quãng tức thì)
        self._set_status("Chờ 3.0s ➔ Lặp lại", "#38BDF8")
        if self._sleep_with_stop_check(3.0):
            return

        # 6. Lặp lại chu kỳ


def _ensure_single_instance():
    """Đảm bảo chỉ có duy nhất 1 phiên bản tool chạy cùng lúc trên Windows.
    Nếu phát hiện tool đã mở trước đó, khôi phục cửa sổ tool cũ lên đầu màn hình và thoát ngay."""
    if os.name != 'nt':
        return None

    import ctypes
    from ctypes import wintypes

    MUTEX_NAME = "Global\\TS_Origin_Danh_Thuong_SingleInstance_Mutex_Unique"
    WINDOW_TITLE = "TS Origin - Đánh Thường"

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32 = ctypes.WinDLL("user32", use_last_error=True)

    mutex = kernel32.CreateMutexW(None, True, MUTEX_NAME)
    last_error = kernel32.GetLastError()
    ERROR_ALREADY_EXISTS = 183

    if last_error == ERROR_ALREADY_EXISTS:
        # Cửa sổ cũ đã tồn tại -> Tìm và kích hoạt lên đầu
        hwnd = user32.FindWindowW(None, WINDOW_TITLE)
        if hwnd:
            SW_RESTORE = 9
            user32.ShowWindow(hwnd, SW_RESTORE)
            user32.SetForegroundWindow(hwnd)
        sys.exit(0)

    return mutex


if __name__ == "__main__":
    _mutex = _ensure_single_instance()
    app = DanhThuongTool()
    app.mainloop()
