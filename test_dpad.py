"""
===================================================================
BẢNG ĐIỀU KHIỂN D-PAD THỬ NGHIỆM TRỰC TIẾP (GUI TEST D-PAD)
===================================================================
"""

import os
import sys
import json
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess

def exec_adb_cmd(dnconsole_path: str, tab_index: str, cmd_list: list) -> str:
    if isinstance(cmd_list, list):
        adb_str = " ".join(cmd_list)
    else:
        adb_str = str(cmd_list)
    full_cmd = [dnconsole_path, "adb", "--index", str(tab_index), "--command", adb_str]
    try:
        res = subprocess.run(full_cmd, capture_output=True, text=True, timeout=10)
        return res.stdout.strip() if res.stdout else ""
    except Exception as e:
        return str(e)

def load_ld_path():
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
                path = cfg.get("ld_path", "")
                if path and os.path.exists(path):
                    return path
        except Exception:
            pass

    default_paths = [
        r"C:\LDPlayer\LDPlayer9",
        r"D:\LDPlayer\LDPlayer9",
        r"E:\LDPlayer\LDPlayer9",
        r"C:\XuanZhi\LDPlayer9"
    ]
    for p in default_paths:
        if os.path.exists(p):
            return p
    return r"C:\LDPlayer\LDPlayer9"

class DPadTestPanel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🎮 Bảng Điều Khiển Test D-Pad Live")
        self.geometry("380x520")
        self.attributes('-topmost', True) # Luôn nổi trên cùng màn hình
        self.configure(bg="#1E1E2E")

        self.ld_dir = load_ld_path()
        self.dnconsole = os.path.join(self.ld_dir, "dnconsole.exe")
        if not os.path.exists(self.dnconsole):
            self.dnconsole = os.path.join(self.ld_dir, "ldconsole.exe")

        self._create_widgets()

    def _create_widgets(self):
        # Header
        hdr = tk.Label(self, text="🕹️ TEST DI CHUYỂN D-PAD LIVE", font=("Segoe UI", 12, "bold"), fg="#89B4FA", bg="#1E1E2E")
        hdr.pack(pady=(10, 5))

        # Controls frame
        ctrl_frame = tk.Frame(self, bg="#2A2A3C", padx=10, pady=10)
        ctrl_frame.pack(fill="x", padx=15, pady=5)

        tk.Label(ctrl_frame, text="Tab Index:", fg="#CDD6F4", bg="#2A2A3C", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w")
        self.ent_tab = tk.Entry(ctrl_frame, width=5, justify="center")
        self.ent_tab.insert(0, "0")
        self.ent_tab.grid(row=0, column=1, padx=5)

        tk.Label(ctrl_frame, text="Thời gian (s):", fg="#CDD6F4", bg="#2A2A3C", font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.ent_time = tk.Entry(ctrl_frame, width=6, justify="center")
        self.ent_time.insert(0, "3.0")
        self.ent_time.grid(row=0, column=3, padx=5)

        tk.Label(ctrl_frame, text="Tâm (X, Y):", fg="#CDD6F4", bg="#2A2A3C", font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=(8,0))
        self.ent_cx = tk.Entry(ctrl_frame, width=5, justify="center")
        self.ent_cx.insert(0, "640")
        self.ent_cx.grid(row=1, column=1, pady=(8,0))

        self.ent_cy = tk.Entry(ctrl_frame, width=5, justify="center")
        self.ent_cy.insert(0, "360")
        self.ent_cy.grid(row=1, column=2, pady=(8,0))

        # D-Pad Button Grid Frame
        dpad_frame = tk.Frame(self, bg="#1E1E2E", pady=10)
        dpad_frame.pack()

        btn_opts = {"font": ("Segoe UI", 10, "bold"), "width": 8, "height": 2, "bd": 0, "cursor": "hand2"}

        # Row 1: NW, N, NE
        tk.Button(dpad_frame, text="↖️ NW", bg="#45475A", fg="#A6E3A1", command=lambda: self.trigger_move("UP_LEFT"), **btn_opts).grid(row=0, column=0, padx=3, pady=3)
        tk.Button(dpad_frame, text="⬆️ LÊN", bg="#313244", fg="#89B4FA", command=lambda: self.trigger_move("UP"), **btn_opts).grid(row=0, column=1, padx=3, pady=3)
        tk.Button(dpad_frame, text="↗️ NE", bg="#45475A", fg="#A6E3A1", command=lambda: self.trigger_move("UP_RIGHT"), **btn_opts).grid(row=0, column=2, padx=3, pady=3)

        # Row 2: W, STOP, E
        tk.Button(dpad_frame, text="⬅️ TRÁI", bg="#313244", fg="#89B4FA", command=lambda: self.trigger_move("LEFT"), **btn_opts).grid(row=1, column=0, padx=3, pady=3)
        tk.Button(dpad_frame, text="🎯 TÂM", bg="#585B70", fg="#F9E2AF", command=lambda: self.trigger_move("CENTER"), **btn_opts).grid(row=1, column=1, padx=3, pady=3)
        tk.Button(dpad_frame, text="➡️ PHẢI", bg="#313244", fg="#89B4FA", command=lambda: self.trigger_move("RIGHT"), **btn_opts).grid(row=1, column=2, padx=3, pady=3)

        # Row 3: SW, S, SE
        tk.Button(dpad_frame, text="↙️ SW", bg="#45475A", fg="#A6E3A1", command=lambda: self.trigger_move("DOWN_LEFT"), **btn_opts).grid(row=2, column=0, padx=3, pady=3)
        tk.Button(dpad_frame, text="⬇️ XUỐNG", bg="#313244", fg="#89B4FA", command=lambda: self.trigger_move("DOWN"), **btn_opts).grid(row=2, column=1, padx=3, pady=3)
        tk.Button(dpad_frame, text="↘️ SE", bg="#45475A", fg="#A6E3A1", command=lambda: self.trigger_move("DOWN_RIGHT"), **btn_opts).grid(row=2, column=2, padx=3, pady=3)

        # Quick Preset Buttons
        preset_frame = tk.Frame(self, bg="#1E1E2E", pady=5)
        preset_frame.pack(fill="x", padx=15)

        tk.Button(preset_frame, text="🚀 5s CHÉO LÊN-PHẢI", font=("Segoe UI", 9, "bold"), bg="#A6E3A1", fg="#11111B", command=lambda: self.trigger_move("UP_RIGHT", override_time=5.0)).pack(fill="x", pady=2)
        tk.Button(preset_frame, text="🔄 TEST CHẠY VÒNG VUÔNG", font=("Segoe UI", 9, "bold"), bg="#FAB387", fg="#11111B", command=self.trigger_square_test).pack(fill="x", pady=2)

        # Status log
        self.lbl_status = tk.Label(self, text="Sẵn sàng test...", font=("Segoe UI", 9), fg="#A6ADC8", bg="#1E1E2E")
        self.lbl_status.pack(side="bottom", pady=8)

    def trigger_move(self, direction: str, override_time: float = None):
        tab_idx = self.ent_tab.get().strip() or "0"
        try:
            sec = override_time if override_time else float(self.ent_time.get().strip())
        except ValueError:
            sec = 2.0

        try:
            cx = int(self.ent_cx.get().strip())
            cy = int(self.ent_cy.get().strip())
        except ValueError:
            cx, cy = 640, 360

        def _worker():
            self.lbl_status.config(text=f"🔄 Đang phát lệnh '{direction}' trong {sec}s...")
            tx, ty = cx, cy
            dist = 250
            if "UP" in direction: ty -= dist
            if "DOWN" in direction: ty += dist
            if "LEFT" in direction: tx -= dist
            if "RIGHT" in direction: tx += dist

            total_ms = int(sec * 1000)
            exec_adb_cmd(self.dnconsole, tab_idx, ["shell", "input", "swipe", str(cx), str(cy), str(tx), str(ty), str(total_ms)])
            self.lbl_status.config(text=f"✅ Hoàn thành '{direction}' ({sec}s)")

        threading.Thread(target=_worker, daemon=True).start()

    def trigger_square_test(self):
        def _worker():
            self.lbl_status.config(text="🔄 Đang test chạy vòng vuông...")
            for d in ["UP", "RIGHT", "DOWN", "LEFT"]:
                self.trigger_move(d, override_time=1.2)
                time.sleep(1.5)
            self.lbl_status.config(text="✅ Hoàn thành test vòng vuông!")
        threading.Thread(target=_worker, daemon=True).start()

if __name__ == "__main__":
    app = DPadTestPanel()
    app.mainloop()
