# -*- coding: utf-8 -*-
"""
========================================================================================
🔒 BẢN SAO LƯU THƯ VIỆN ĐÃ KHÓA HOÀN TẤT (PERMANENT LOCKED BACKUP)
ÁP DỤNG CHO 2 MODULE:
  1. CARD CHỌN TAB LDPLAYER & KHỞI ĐỘNG (TOP BAR: GAME - RUN - STOP - EXIT)
  2. CARD A: BOSS THẾ GIỚI (SAFEZONE - ĐỔI TƯỚNG - D-PAD/DỊCH CHUYỂN - 5 LƯỢT CHÍNH - VÉ BOSS)

TRẠNG THÁI: ĐÃ HOÀN THIỆN 100% - KHÓA NGUYÊN BẢN - KHÔNG CHỈNH SỬA
========================================================================================
"""

import os
import time
import re
import unicodedata
from datetime import datetime

# ========================================================================================
# 📊 BẢNG TRA CỨU TỌA ĐỘ ROI & THRESHOLD CHUẨN XÁC CỦA 2 CARD
# ========================================================================================
"""
I. CARD CHỌN TAB LDPLAYER & MỞ GAME:
- Package Game: com.vtcmobile.gz06
- card_top/login/login_server.png : Ngưỡng 88%, Toàn màn hình (khớp 3 lần liên tiếp)
- card_top/login/login_redorb.png : Ngưỡng 88%, Toàn màn hình
- card_top/login/login_co.png     : Ngưỡng 75%, Toàn màn hình
- card_top/server/server_<ten>.png: Ngưỡng 75%, Toàn màn hình
- card_top/server/server_trieuvan.png: Ngưỡng 75%, Toàn màn hình (Mốc dừng cuộn xuống)
- card_top/login/login_nkn.png    : Ngưỡng 45%, Toàn màn hình (Kiểm tra mất kết nối)
- card_top/login/login_x.png      : Ngưỡng 75%, Toàn màn hình
- card_top/login/login_auto.png   : Ngưỡng 75%, Toàn màn hình
- Cuộn danh sách máy chủ:
  + Cuộn xuống: ADB swipe 350 580 350 400 700 (Tối đa 10 lần)
  + Cuộn ngược lên: ADB swipe 350 400 350 580 700 (Tối đa 10 lần)

II. CARD A: BOSS THẾ GIỚI:
- card_top/login/login_x.png : ROI (990, 50, 1165, 200), Ngưỡng 75%
- card_c/c_vitri.png         : ROI (735, 405, 1280, 720), Ngưỡng 85%
- card_a/a_co.png            : ROI (275, 540, 1150, 670), Ngưỡng 85%
- card_b/b_doi.png           : ROI (735, 405, 1280, 720), Ngưỡng 85%
- card_a/a_sukien.png        : ROI (735, 405, 1280, 720), Ngưỡng 85%
- card_a/a_skboss.png        : ROI (155, 95, 305, 625), Ngưỡng 85%
- card_a/a_dichuyen.png      : ROI (895, 435, 1065, 535), Ngưỡng 60%
- card_a/a_boss.png          : ROI (735, 405, 1280, 720), Ngưỡng 85%
- card_a/a_hetluot.png       : ROI (275, 540, 1150, 670), Ngưỡng 85%
- card_f/f_vaotran.png       : ROI (1215, 0, 1280, 45), Ngưỡng 80%
- card_a/a_tui.png           : ROI (735, 405, 1280, 720), Ngưỡng 85%
- card_a/a_veboss.png        : ROI (745, 230, 1095, 580), Ngưỡng 70%
- card_a/a_khoa.png          : ROI (745, 230, 1095, 580), Ngưỡng 85%

- Tọa độ thao tác D-Pad & Túi đồ:
  + D-Pad Chéo Phải - Trên (3.0s): ADB swipe 640 360 890 110 3000
  + D-Pad Phải (5.5s): ADB swipe 640 360 890 360 5500
  + Tìm Boss: Click (1240, 605) mỗi 0.4s (tối đa 20 lần)
  + Vào trận: Click (185, 145) -> Hoãn 60s -> Quét f_vaotran.png
  + Cuộn Túi xuống: ADB swipe 920 480 920 230 800 (tối đa 5 lần)
  + Cuộn Túi ngược lên: ADB swipe 920 330 920 580 1200 (tối đa 5 lần)
  + Dùng vé: Click a_veboss.png -> Click (755, 460) -> Click (320, 25)
"""


# ========================================================================================
# 🔒 MODULE 1: CARD CHỌN TAB LDPLAYER & HÀNG NÚT THAO TÁC (GAME, RUN, STOP, EXIT)
# ========================================================================================

class LockedCardTopModule:
    """Mã nguồn hoàn thiện của Card Top: Chọn Tab LDPlayer, Server và Bộ 4 nút"""

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
                self._exec_cmd([dnconsole_path, "killapp", "--index", str(tab_index), "--packagename", target_pkg])
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell am force-stop {target_pkg}"])
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input keyevent 3"])

            self.after(0, self.log_info, f"✅ [Exit] Đã thoát game trên Tab {tab_name} thành công! (Về màn hình chính giả lập)")
        except Exception as e:
            self.after(0, self.log_error, f"❌ Lỗi khi đóng game trên Tab {tab_name}: {e}")

    def xu_ly_ts_origin(self):
        """Bắt đầu quy trình tự động khởi động LDPlayer, mở game TS Origin và chọn Server"""
        tab, idx = self._get_selected_ld_info()
        if idx is None:
            self.log_error("Vui lòng chọn một Tab LDPlayer trước khi bấm mở game!")
            return

        server = self.combo_server.get()
        self.log_info(f"Bắt đầu quy trình: Bật Giả lập LDPlayer (Tab {tab}) ➔ Chờ Load 100% ➔ Tự động thu nhỏ xuống Taskbar ➔ Mở App Game ➔ Chọn Máy Chủ '{server}'...")
        self.btn_enter_game.configure(state="disabled", text="Đang mở Game...")
        threading.Thread(target=self._worker_launch_ts_origin, args=(tab, idx, server), daemon=True).start()

    def _worker_launch_ts_origin(self, tab_name: str, tab_index: str, server_name: str):
        try:
            dnconsole_path = os.path.join(self.ld_path, "ldconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(self.ld_path, "dnconsole.exe")

            if not os.path.exists(dnconsole_path):
                self.after(0, self._finish_launch_ts_origin, False, f"Không tìm thấy ldconsole/dnconsole tại: {self.ld_path}")
                return

            # Bước 1: Khởi động giả lập & Tự động thu nhỏ ngay
            if not self._is_ld_loaded_100(dnconsole_path, tab_index):
                self.after(0, self.log_info, f"🖥️ [Bước 1/4] Đang khởi động Giả lập LDPlayer Tab: {tab_name} (Index: {tab_index})...")
                self._exec_cmd([dnconsole_path, "launch", "--index", str(tab_index)])
                time.sleep(0.5)
                self._minimize_ld_window(tab_index, tab_name)
            else:
                self.after(0, self.log_info, f"🖥️ Tab LDPlayer {tab_name} (Index: {tab_index}) đã mở sẵn ➔ Tự động thu nhỏ xuống khay Taskbar...")
                self._minimize_ld_window(tab_index, tab_name)

            # Bước 2: Chờ nạp 100%
            boot_start = time.time()
            emulator_ready = False
            for check_idx in range(40):
                if self.stop_requested:
                    self.stop_requested = False
                    self.after(0, self._finish_launch_ts_origin, False, "🛑 Tiến trình đã dừng theo yêu cầu!")
                    return
                self._minimize_ld_window(tab_index, tab_name)
                if self._is_ld_loaded_100(dnconsole_path, tab_index):
                    emulator_ready = True
                    break
                time.sleep(2.5)

            if not emulator_ready:
                self.after(0, self.log_info, "ℹ️ Tiếp tục tiến trình mở ứng dụng Game...")
            else:
                time.sleep(3.0)

            # Bước 3: Mở App Game
            target_pkg = "com.vtcmobile.gz06"
            self._exec_cmd([dnconsole_path, "runapp", "--index", str(tab_index), "--packagename", target_pkg])
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell monkey -p {target_pkg} -c android.intent.category.LAUNCHER 1"])

            # Bước 4: Mắt thần quét Bảng Chọn Máy Chủ
            start_wait = time.time()
            consecutive_matches = 0
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
                        break
                else:
                    consecutive_matches = 0
                time.sleep(1.0)

            time.sleep(1.0)

            # Quét nút login_co.png nếu có
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_co.png", threshold=0.75)
            if co_x is not None and co_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {co_x} {co_y}"])
                time.sleep(1.0)

            def to_snake_case(text: str) -> str:
                text = text.replace('Đ', 'D').replace('đ', 'd')
                nfkd = unicodedata.normalize('NFKD', text)
                no_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])
                clean = re.sub(r'[^a-zA-Z0-9]', '_', no_accent).lower()
                return re.sub(r'_+', '_', clean).strip('_')

            server_img_name = f"card_top/server/server_{to_snake_case(server_name).replace('_', '')}.png"
            scroll_x = 350
            swipe_ms = 700
            y_start_down = 580
            y_end_down = 400
            y_start_up = 400
            y_end_up = 580
            found_server = False

            # Cuộn xuống 10 lần
            for step in range(10):
                if self.stop_requested: return
                click_x, click_y = self._find_template_on_screen(dnconsole_path, tab_index, server_img_name, threshold=0.75)
                if click_x is not None and click_y is not None:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {click_x} {click_y}"])
                    time.sleep(1.5)
                    nkn_x, nkn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_nkn.png", threshold=0.45)
                    if nkn_x is None:
                        found_server = True
                        break

                if server_img_name != "card_top/server/server_trieuvan.png":
                    tv_x, tv_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/server/server_trieuvan.png", threshold=0.75)
                    if tv_x is not None and tv_y is not None:
                        break

                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input swipe {scroll_x} {y_start_down} {scroll_x} {y_end_down} {swipe_ms}"])
                time.sleep(1.5)

            # Cuộn ngược lên 10 lần nếu chưa thấy
            if not found_server:
                for step in range(10):
                    if self.stop_requested: return
                    click_x, click_y = self._find_template_on_screen(dnconsole_path, tab_index, server_img_name, threshold=0.75)
                    if click_x is not None and click_y is not None:
                        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {click_x} {click_y}"])
                        time.sleep(1.5)
                        nkn_x, nkn_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_nkn.png", threshold=0.45)
                        if nkn_x is None:
                            found_server = True
                            break
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input swipe {scroll_x} {y_start_up} {scroll_x} {y_end_up} {swipe_ms}"])
                    time.sleep(1.5)

            if not found_server:
                self.after(0, self._finish_launch_ts_origin, False, f"❌ Không tìm thấy máy chủ '{server_name}'.")
            else:
                time.sleep(3.0)
                # Đóng nút X nếu có
                x_x, x_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75)
                if x_x is not None and x_y is not None:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {x_x} {x_y}"])
                    time.sleep(1.0)

                # Tap login_auto.png
                auto_x, auto_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_auto.png", threshold=0.75)
                if auto_x is not None and auto_y is not None:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {auto_x} {auto_y}"])
                    time.sleep(1.0)

                self._minimize_ld_window(tab_index, tab_name)
                self.after(0, self._finish_launch_ts_origin, True, "✅ Khởi chạy Game & Chọn Server thành công!")
        except Exception as e:
            self.after(0, self._finish_launch_ts_origin, False, f"Lỗi: {e}")

    def _finish_launch_ts_origin(self, success: bool, msg: str):
        self.btn_enter_game.configure(state="normal", text="Game")
        if success:
            self.log_info(msg)
        else:
            self.log_error(msg)

    def dung_tat_ca_hoat_dong(self):
        """Dừng khẩn cấp toàn bộ hoạt động của tất cả các Card"""
        self.stop_requested = True
        self.log_error("🛑 ĐÃ BẤM STOP - DỪNG KHẨN CẤP TOÀN BỘ HOẠT ĐỘNG!")
        self.var_switch_A.set(False)
        self.var_switch_B.set(False)
        self.var_switch_C.set(False)
        self.var_switch_D.set(False)
        self.save_config()
        self.btn_run.configure(state="normal", text="Run")
        self.btn_enter_game.configure(state="normal", text="Game")


# ========================================================================================
# 🔒 MODULE 2: CARD A - QUY TRÌNH BOSS THẾ GIỚI HOÀN CHỈNH
# ========================================================================================

class LockedCardAModule:
    """Mã nguồn hoàn thiện của Card A: Boss Thế Giới"""

    def _run_boss_safezone(self, dnconsole_path: str, tab_index: str):
        """PHẦN 1: QUY TRÌNH VỀ KHU AN TOÀN CỦA BOSS THẾ GIỚI"""
        if self._should_stop_card_A(): return
        lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(990, 50, 1165, 200))
        if lx_x is not None and lx_y is not None:
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
            time.sleep(0.4)

        if self._should_stop_card_A(): return
        v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
        if v_x is not None and v_y is not None:
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
            time.sleep(0.4)
        else:
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
            if self._should_stop_card_A(): return
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
            if v_x is not None and v_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {v_x} {v_y}"])
                time.sleep(0.4)

        if self._should_stop_card_A(): return
        while not self._should_stop_card_A():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_co.png", threshold=0.85, region=(275, 540, 1150, 670))
            if co_x is not None and co_y is not None:
                break
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 435 250"])
            time.sleep(0.5)

        if self._should_stop_card_A(): return
        while not self._should_stop_card_A():
            co_x, co_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_co.png", threshold=0.85, region=(275, 540, 1150, 670))
            if co_x is not None and co_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {co_x} {co_y}"])
                time.sleep(0.5)
            else:
                break

        if self._should_stop_card_A(): return
        time.sleep(3.0)
        v_check_x, v_check_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
        if v_check_x is not None and v_check_y is not None:
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)

    def _run_boss_pre_move(self, dnconsole_path: str, tab_index: str) -> bool:
        """PHẦN THÊM: THAO TÁC TRƯỚC PHẦN 3 DI CHUYỂN CỦA BOSS THẾ GIỚI. Trả về True nếu tìm thấy a_dichuyen.png"""
        if self._should_stop_card_A(): return False

        sk_x, sk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_sukien.png", threshold=0.85, region=(735, 405, 1280, 720))
        if sk_x is not None and sk_y is not None:
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {sk_x} {sk_y}"])
            time.sleep(0.4)
        else:
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)
            if self._should_stop_card_A(): return False
            sk_x, sk_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_sukien.png", threshold=0.85, region=(735, 405, 1280, 720))
            if sk_x is not None and sk_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {sk_x} {sk_y}"])
                time.sleep(0.4)

        if self._should_stop_card_A(): return False
        skb_x, skb_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_skboss.png", threshold=0.85, region=(155, 95, 305, 625))
        if skb_x is not None and skb_y is not None:
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {skb_x} {skb_y}"])
            time.sleep(0.4)

        if self._should_stop_card_A(): return False
        dc_x, dc_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_dichuyen.png", threshold=0.60, region=(895, 435, 1065, 535))
        if dc_x is not None and dc_y is not None:
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {dc_x} {dc_y}"])
            time.sleep(3.0)
            return True
        else:
            lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(990, 50, 1165, 200))
            if lx_x is not None and lx_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                time.sleep(0.4)

            if self._should_stop_card_A(): return False
            v_x, v_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_c/c_vitri.png", threshold=0.85, region=(735, 405, 1280, 720))
            if v_x is not None and v_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(0.4)
            return False

    def _run_boss_move_manual(self, dnconsole_path: str, tab_index: str):
        """Giai Đoạn 3: Di chuyển bộ D-Pad"""
        if self._should_stop_card_A(): return
        # Bước 3.1: Chéo Phải - Trên 3.0s
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 640 360 890 110 3000"])
        time.sleep(0.3)
        if self._should_stop_card_A(): return
        # Bước 3.2: Phải 5.5s
        self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 640 360 890 360 5500"])
        time.sleep(0.3)

    def _run_boss_workflow(self, dnconsole_path: str, tab_name: str, tab_index: str, max_turns: int = 5, skip_move: bool = False):
        """QUY TRÌNH ĐÁNH BOSS: Tìm Boss -> Check Hết Lượt -> Vào Trận -> Chờ 60s -> Quét f_vaotran.png"""
        if self._should_stop_card_A(): return

        if not skip_move:
            self._run_boss_safezone(dnconsole_path, tab_index)
            skip_di_chuyen = self._run_boss_pre_move(dnconsole_path, tab_index)
            if not skip_di_chuyen:
                self._run_boss_move_manual(dnconsole_path, tab_index)

        for turn in range(1, max_turns + 1):
            if self._should_stop_card_A(): return

            # Tìm Boss
            boss_x, boss_y = None, None
            for click_idx in range(20):
                if self._should_stop_card_A(): break
                boss_x, boss_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_boss.png", threshold=0.85, region=(735, 405, 1280, 720))
                if boss_x is not None and boss_y is not None:
                    break
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1240 605"])
                time.sleep(0.4)

            if self._should_stop_card_A(): return
            if boss_x is None or boss_y is None:
                self._run_boss_safezone(dnconsole_path, tab_index)
                self._run_boss_pre_move(dnconsole_path, tab_index)

            if self._should_stop_card_A(): return
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1160 570"])
            time.sleep(0.4)

            if self._should_stop_card_A(): return
            hl_x, hl_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_hetluot.png", threshold=0.85, region=(275, 540, 1150, 670))
            if hl_x is not None and hl_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {hl_x} {hl_y}"])
                time.sleep(0.4)
                break
            else:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 500 635"])
                time.sleep(0.4)

            if self._should_stop_card_A(): return
            time.sleep(2.0)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 185 145"])

            # Chờ 60s
            for _ in range(60):
                if self._should_stop_card_A(): return
                time.sleep(1.0)

            # Quét f_vaotran.png kết thúc trận
            while not self._should_stop_card_A():
                vt_x, vt_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_f/f_vaotran.png", threshold=0.80, region=(1215, 0, 1280, 45))
                if vt_x is not None and vt_y is not None:
                    break
                time.sleep(0.5)

    def _run_boss_ve_process(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """THAO TÁC TÌM & DÙNG VÉ BOSS (CHỈ CHẠY SAU 12H TRƯA)"""
        ve_count = 0
        while not self._should_stop_card_A():
            ve_count += 1
            if self._should_stop_card_A(): return
            lx_x, lx_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(990, 50, 1165, 200))
            if lx_x is not None and lx_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x} {lx_y}"])
                time.sleep(0.4)

            if self._should_stop_card_A(): return
            tui_x, tui_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_tui.png", threshold=0.85, region=(735, 405, 1280, 720))
            if tui_x is not None and tui_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {tui_x} {tui_y}"])
                time.sleep(0.4)

            # Cuộn tìm Vé
            veboss_x, veboss_y = None, None
            for swipe_down_cnt in range(5):
                if self._should_stop_card_A(): break
                veboss_x, veboss_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_veboss.png", threshold=0.70, region=(745, 230, 1095, 580))
                if veboss_x is not None and veboss_y is not None:
                    break
                khoa_x, khoa_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_khoa.png", threshold=0.85, region=(745, 230, 1095, 580))
                if khoa_x is not None and khoa_y is not None:
                    break
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 920 480 920 230 800"])
                time.sleep(1.0)

            if veboss_x is None or veboss_y is None:
                for swipe_up_cnt in range(5):
                    if self._should_stop_card_A(): break
                    veboss_x, veboss_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_a/a_veboss.png", threshold=0.70, region=(745, 230, 1095, 580))
                    if veboss_x is not None and veboss_y is not None:
                        break
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input swipe 920 330 920 580 1200"])
                    time.sleep(1.0)

            if veboss_x is None or veboss_y is None:
                if self._should_stop_card_A(): return
                lx_x2, lx_y2 = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(990, 50, 1165, 200))
                if lx_x2 is not None and lx_y2 is not None:
                    self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x2} {lx_y2}"])
                    time.sleep(0.4)
                break

            if self._should_stop_card_A(): return
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {veboss_x} {veboss_y}"])
            time.sleep(0.4)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 755 460"])
            time.sleep(0.4)
            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 320 25"])
            time.sleep(0.4)

            lx_x2, lx_y2 = self._find_template_on_screen(dnconsole_path, tab_index, "card_top/login/login_x.png", threshold=0.75, region=(990, 50, 1165, 200))
            if lx_x2 is not None and lx_y2 is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {lx_x2} {lx_y2}"])
                time.sleep(0.4)

            skip_move = (ve_count >= 2)
            self._run_boss_workflow(dnconsole_path, tab_name, tab_index, max_turns=1, skip_move=skip_move)

    def _execute_card_A_boss_tg(self, dnconsole_path: str, tab_name: str, tab_index: str):
        """Hàm chính điều phối toàn bộ Card A"""
        if self._should_stop_card_A() or not self.var_A1.get():
            self.after(0, lambda: self.var_switch_A.set(False))
            self.after(0, self.save_config)
            return

        selected_char = self.combo_A_char.get() if hasattr(self, 'combo_A_char') else "Xuất Chiến"

        # 1. Safezone
        if self._should_stop_card_A(): return
        self._run_boss_safezone(dnconsole_path, tab_index)

        # 2. Đổi vị trí tướng
        if selected_char != "Xuất Chiến":
            time.sleep(0.4)
            b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(735, 405, 1280, 720))
            if b_doi_x is None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
                time.sleep(0.4)
                b_doi_x, b_doi_y = self._find_template_on_screen(dnconsole_path, tab_index, "card_b/b_doi.png", threshold=0.85, region=(735, 405, 1280, 720))

            if b_doi_x is not None and b_doi_y is not None:
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {b_doi_x} {b_doi_y}"])
                time.sleep(0.4)

            coords = {
                "Vị Trí 1": [(560, 340), (560, 255), (1090, 110)],
                "Vị Trí 2": [(560, 255), (560, 340), (1090, 110)],
                "Vị Trí 3": [(560, 255), (560, 430), (1090, 110)],
                "Vị Trí 4": [(560, 255), (560, 520), (1090, 110)],
            }
            for pt in coords.get(selected_char, []):
                self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"shell input tap {pt[0]} {pt[1]}"])
                time.sleep(0.5)

            self._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell input tap 1213 648"])
            time.sleep(0.4)

        # 3. Sự Kiện & Di Chuyển
        if self._should_stop_card_A(): return
        skip_di_chuyen = self._run_boss_pre_move(dnconsole_path, tab_index)
        if not skip_di_chuyen:
            self._run_boss_move_manual(dnconsole_path, tab_index)

        # 4. Đánh 5 Lượt Chính
        if self._should_stop_card_A(): return
        self._run_boss_workflow(dnconsole_path, tab_name, tab_index, max_turns=5, skip_move=True)

        # 5. Vé Boss sau 12h
        if self._should_stop_card_A(): return
        now_dt = datetime.now()
        if now_dt.hour >= 12:
            self._run_boss_ve_process(dnconsole_path, tab_name, tab_index)

        # 6. Hoàn tất & Tắt công tắc
        self.after(0, lambda: self.var_switch_A.set(False))
        self.after(0, self.save_config)
