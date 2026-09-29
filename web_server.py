import os
import sys
import json
import time
import socket
import tempfile
import threading
import subprocess
import shutil
import urllib.request
import re
import cv2
import numpy as np
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

def get_local_ip():
    """Lấy địa chỉ IP mạng LAN nội bộ của máy tính"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


_last_shot_time = 0
_last_shot_bytes = None
_shot_lock = threading.Lock()

def get_screenshot_bytes(app):
    """Chụp màn hình giả lập LDPlayer đang chọn và trả về JPEG bytes (cache 0.3s giảm đơ/lag ADB mà vẫn mượt 0.5s)"""
    global _last_shot_time, _last_shot_bytes
    now = time.time()
    with _shot_lock:
        if _last_shot_bytes is not None and (now - _last_shot_time) < 0.3:
            return _last_shot_bytes

        try:
            tab_name, tab_index = app._get_selected_ld_info()
            if tab_index is None:
                return None

            dnconsole_path = os.path.join(app.ld_path, "ldconsole.exe")
            if not os.path.exists(dnconsole_path):
                dnconsole_path = os.path.join(app.ld_path, "dnconsole.exe")

            img = None

            # 1. Ưu tiên lấy từ bộ nhớ đệm frame gần nhất của app nếu bot đang chạy (Zero Disk & ADB latency)
            if hasattr(app, '_screen_cache'):
                cached = getattr(app, '_screen_cache', {}).get(str(tab_index))
                if cached and (now - cached.get("time", 0)) < 0.4 and cached.get("img") is not None:
                    img = cached["img"]

            # 2. Sử dụng cơ chế chụp In-Memory siêu tốc từ app._capture_screen_fast (Zero Disk I/O)
            if img is None and hasattr(app, '_capture_screen_fast'):
                img = app._capture_screen_fast(dnconsole_path, tab_index, max_cache_age=0.3)

            # 3. Dự phòng qua file tạm nếu cơ chế In-Memory chưa sẵn sàng
            if img is None:
                temp_dir = os.path.join(tempfile.gettempdir(), "ts_origin_web")
                os.makedirs(temp_dir, exist_ok=True)
                temp_screen = os.path.join(temp_dir, f"web_cap_{tab_index}.png")

                if os.path.exists(temp_screen):
                    try: os.remove(temp_screen)
                    except Exception: pass

                app._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", "shell screencap -p /sdcard/web_cap.png"])
                app._exec_cmd([dnconsole_path, "adb", "--index", str(tab_index), "--command", f"pull /sdcard/web_cap.png \"{temp_screen}\""])

                if os.path.exists(temp_screen) and os.path.getsize(temp_screen) > 0:
                    d = np.fromfile(temp_screen, dtype=np.uint8)
                    img = cv2.imdecode(d, cv2.IMREAD_COLOR)
                    try: os.remove(temp_screen)
                    except Exception: pass

            # 4. Resize và encode sang JPEG chất lượng tối ưu cho truyền tải Web từ xa (nhẹ và mượt)
            if img is not None and getattr(img, 'shape', None) and img.shape[0] > 0 and img.shape[1] > 0:
                h, w = img.shape[:2]
                if w > 850:
                    scale = 850.0 / w
                    img = cv2.resize(img, (850, int(h * scale)), interpolation=cv2.INTER_AREA)
                ok, buf = cv2.imencode('.jpg', img, [int(cv2.IMWRITE_JPEG_QUALITY), 72])
                if ok:
                    _last_shot_bytes = buf.tobytes()
                    _last_shot_time = now
                    return _last_shot_bytes
        except Exception:
            pass
        return None


HTML_PAGE = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="TS Origin">
    <title>TS Origin - Mobile Control</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #070a13;
            --surface: rgba(15, 23, 42, 0.78);
            --surface-card: rgba(18, 28, 50, 0.72);
            --border: rgba(255, 255, 255, 0.09);
            --border-active: rgba(56, 189, 248, 0.5);
            --primary: #38bdf8;
            --primary-glow: rgba(56, 189, 248, 0.35);
            --accent: #f97316;
            --accent-glow: rgba(249, 115, 22, 0.4);
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --text: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --font-main: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
            font-family: var(--font-main);
        }

        html {
            height: 100%;
            background-color: var(--bg);
        }

        body {
            background: radial-gradient(circle at 50% -10%, #172554 0%, #0b1120 45%, #030712 100%);
            background-attachment: fixed;
            color: var(--text);
            min-height: 100%;
            min-height: 100dvh;
            padding-bottom: calc(155px + env(safe-area-inset-bottom, 0px));
            overflow-x: hidden;
            user-select: none;
        }

        /* Top Header */
        .app-header {
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(9, 14, 26, 0.85);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding: calc(12px + env(safe-area-inset-top, 0px)) 16px 12px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 800;
            font-size: 1.18rem;
            letter-spacing: -0.4px;
            background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .status-pill {
            display: flex;
            align-items: center;
            gap: 7px;
            font-size: 0.78rem;
            font-weight: 700;
            padding: 5px 12px;
            border-radius: 9999px;
            background: rgba(16, 185, 129, 0.12);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.15);
            transition: all 0.3s ease;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--success);
            box-shadow: 0 0 8px var(--success);
        }

        .status-dot.running {
            background-color: var(--warning);
            box-shadow: 0 0 10px var(--warning);
            animation: pulse 1.4s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.45; transform: scale(1.3); }
        }

        /* Tab Content Container */
        .container {
            max-width: 580px;
            margin: 0 auto;
            padding: 14px 12px;
            display: flex;
            flex-direction: column;
            gap: 14px;
        }

        .tab-pane {
            display: none;
            flex-direction: column;
            gap: 14px;
            animation: fadeIn 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            min-height: calc(100dvh - 230px);
        }

        .tab-pane.active {
            display: flex;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* LDPlayer Carousel Header */
        .ld-carousel-wrapper {
            position: sticky;
            top: 55px;
            z-index: 99;
            background: rgba(10, 16, 30, 0.9);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border-bottom: 1px solid rgba(56, 189, 248, 0.15);
            padding: 9px 14px;
            overflow-x: auto;
            white-space: nowrap;
            scrollbar-width: none;
        }
        .ld-carousel-wrapper::-webkit-scrollbar { display: none; }
        .ld-carousel {
            display: inline-flex;
            gap: 8px;
        }
        .ld-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 7px 15px;
            border-radius: 999px;
            background: rgba(22, 33, 56, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 0.8rem;
            font-weight: 700;
            color: #94a3b8;
            cursor: pointer;
            transition: all 0.25s ease;
        }
        .ld-pill:active { transform: scale(0.95); }
        .ld-pill.active {
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.25), rgba(2, 132, 199, 0.35));
            border-color: #38bdf8;
            color: #38bdf8;
            box-shadow: 0 0 14px rgba(56, 189, 248, 0.4);
        }

        /* Cards */
        .card {
            background: linear-gradient(160deg, rgba(20, 31, 52, 0.75) 0%, rgba(11, 18, 33, 0.88) 100%);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.09);
            border-top: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 20px;
            padding: 16px;
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(56, 189, 248, 0.05);
            position: relative;
            overflow: hidden;
        }

        .card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 1px;
            background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.35), transparent);
            pointer-events: none;
        }

        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .card-title {
            font-size: 1.02rem;
            font-weight: 800;
            display: flex;
            align-items: center;
            gap: 7px;
            color: #38bdf8;
            text-shadow: 0 0 12px rgba(56, 189, 248, 0.3);
            letter-spacing: -0.2px;
        }

        /* Switch toggle (Modern Gaming Glow - Ergonomic & High Precision) */
        .switch {
            position: relative;
            display: inline-block;
            width: 52px;
            height: 28px;
            flex-shrink: 0;
            user-select: none;
        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(circle at 30% 30%, #1e293b, #0f172a);
            border: 1.5px solid #334155;
            transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
            border-radius: 28px;
            box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.6), 0 1px 2px rgba(255, 255, 255, 0.05);
        }

        .switch:hover .slider {
            border-color: #475569;
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 20px;
            width: 20px;
            left: 3px;
            bottom: 2.5px;
            background: linear-gradient(180deg, #ffffff 0%, #cbd5e1 100%);
            transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
            border-radius: 50%;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.9);
        }

        .switch:hover .slider:before {
            filter: brightness(1.1);
        }

        input:checked + .slider {
            background: linear-gradient(135deg, #fb923c 0%, #ea580c 50%, #c2410c 100%);
            border-color: #fdba74;
            box-shadow: 0 0 18px rgba(249, 115, 22, 0.65), 0 0 6px rgba(234, 88, 12, 0.9), inset 0 1px 2px rgba(255, 255, 255, 0.4);
        }

        input:checked + .slider:before {
            transform: translateX(23px) scale(1.03);
            background: linear-gradient(180deg, #ffffff 0%, #ffedd5 100%);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35), 0 0 8px rgba(255, 255, 255, 0.85);
        }

        /* Circular Checkbox Toggle (Đồng bộ nút tròn Tạm Dừng Card D với Desktop) */
        .chk-round {
            position: relative;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: radial-gradient(circle at 30% 30%, #1e293b, #0f172a);
            border: 1.5px solid #334155;
            cursor: pointer;
            transition: all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.6), 0 1px 2px rgba(255, 255, 255, 0.05);
            flex-shrink: 0;
            user-select: none;
        }

        .chk-round:hover {
            border-color: #475569;
            transform: scale(1.06);
        }

        .chk-round:active {
            transform: scale(0.94);
        }

        .chk-round input {
            opacity: 0;
            width: 0;
            height: 0;
            position: absolute;
            margin: 0;
            pointer-events: none;
        }

        .chk-round .chk-mark {
            opacity: 0;
            transform: scale(0.3);
            transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
            color: #ffffff;
            font-size: 13px;
            font-weight: 900;
            line-height: 1;
        }

        .chk-round:has(input:checked) {
            background: linear-gradient(135deg, #fb923c 0%, #ea580c 50%, #c2410c 100%);
            border-color: #fdba74;
            box-shadow: 0 0 16px rgba(249, 115, 22, 0.65), inset 0 1px 2px rgba(255, 255, 255, 0.4);
        }

        .chk-round:has(input:checked) .chk-mark {
            opacity: 1;
            transform: scale(1);
        }

        .form-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 5px;
        }

        label {
            font-size: 0.78rem;
            font-weight: 700;
            color: var(--text-muted);
            letter-spacing: 0.2px;
        }

        select {
            background: rgba(15, 23, 42, 0.85);
            color: #f8fafc;
            border: 1px solid rgba(255, 255, 255, 0.12);
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 0.88rem;
            font-weight: 600;
            outline: none;
            cursor: pointer;
            width: 100%;
            min-height: 44px;
            transition: all 0.2s ease;
        }

        select:focus {
            border-color: #38bdf8;
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.3);
        }

        select option {
            background: #0f172a;
            color: #f8fafc;
        }

        .checkbox-group {
            display: flex;
            flex-wrap: wrap;
            gap: 9px;
            margin-top: 10px;
        }

        .chk-label {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 7px;
            background: rgba(22, 33, 56, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 8px 13px;
            border-radius: 12px;
            font-size: 0.82rem;
            font-weight: 700;
            color: #94a3b8;
            cursor: pointer;
            user-select: none;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            white-space: nowrap;
            box-sizing: border-box;
            flex-shrink: 0;
            min-height: 40px;
        }

        .chk-label:active {
            transform: scale(0.96);
        }

        .chk-label:has(input:checked) {
            background: linear-gradient(135deg, rgba(234, 88, 12, 0.25), rgba(249, 115, 22, 0.15));
            border-color: #f97316;
            color: #ffffff;
            box-shadow: 0 0 12px rgba(249, 115, 22, 0.3);
        }

        .chk-label input {
            accent-color: var(--accent);
            width: 17px;
            height: 17px;
            margin: 0;
            flex-shrink: 0;
            cursor: pointer;
        }

        /* Screen Preview & Fullscreen Theater Mode */
        .preview-box {
            width: 100%;
            border-radius: 12px;
            overflow: hidden;
            background: #000;
            border: 1px solid var(--border);
            position: relative;
            min-height: 220px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 6px 20px rgba(0,0,0,0.5);
            cursor: crosshair;
        }

        .preview-img {
            width: 100%;
            height: auto;
            display: block;
            object-fit: contain;
            user-select: none;
            -webkit-user-drag: none;
        }

        .btn-mini {
            background: rgba(255, 255, 255, 0.08);
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255,255,255,0.15);
            color: #fff;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            transition: 0.2s;
        }

        .btn-mini:active {
            transform: scale(0.95);
        }


        /* Đồng bộ kích thước cố định đều nhau cho 2 hàng Card F Chiến Đấu */
        .combat-col-left {
            width: 157px;
            min-width: 157px;
            max-width: 157px;
            display: flex;
            align-items: center;
            gap: 6px;
            flex-shrink: 0;
        }

        .combat-btn-ctrl {
            width: 128px;
            min-width: 128px;
            max-width: 128px;
            height: 28px;
            min-height: 28px;
            max-height: 28px;
            font-size: 0.78rem;
            font-weight: 600;
            color: #ffffff;
            background: #1F2937;
            border: 1px solid var(--border);
            border-radius: 6px;
            cursor: pointer;
            box-sizing: border-box;
            display: inline-flex;
            align-items: center;
            justify-content: flex-start;
            padding: 0 10px;
            line-height: 1;
            white-space: nowrap;
            outline: none;
            -webkit-tap-highlight-color: transparent;
            transition: background 0.15s ease, border-color 0.15s ease;
        }
        button.combat-btn-ctrl:hover {
            background: #374151;
            border-color: rgba(255, 255, 255, 0.25);
        }
        button.combat-btn-ctrl:active {
            transform: scale(0.97);
        }

        select.combat-btn-ctrl {
            padding: 0 4px 0 8px;
            font-size: 0.78rem;
            color: #ffffff;
            background-color: #1F2937;
            text-align: left;
            text-align-last: left;
            cursor: pointer;
        }
        select.combat-btn-ctrl:hover {
            background: #374151;
            border-color: rgba(255, 255, 255, 0.25);
        }
        select.combat-btn-ctrl:active {
            transform: none !important;
        }
        select.combat-btn-ctrl:focus {
            outline: none !important;
            border-color: #38bdf8 !important;
            box-shadow: none !important;
        }

        .chk-combat-sub {
            font-size: 0.68rem;
            color: #9CA3AF;
            white-space: nowrap;
            padding-left: 0;
            margin-left: 0;
            flex-shrink: 0;
        }
        .combat-select-right {
            width: 114px;
            min-width: 100px;
            max-width: 114px;
            height: 28px;
            min-height: 28px;
            max-height: 28px;
            font-size: 0.78rem;
            padding: 0 6px;
            border-radius: 6px;
            box-sizing: border-box;
            background: #1F2937;
            border: 1px solid var(--border);
            color: #ffffff;
            outline: none;
            cursor: pointer;
            -webkit-tap-highlight-color: transparent;
            flex-shrink: 0;
        }
        select.combat-select-right:active {
            transform: none !important;
        }
        select.combat-select-right:focus {
            outline: none !important;
            border-color: #38bdf8 !important;
            box-shadow: none !important;
        }

        @media (max-width: 400px) {
            .combat-select-right {
                width: 104px;
                min-width: 95px;
                max-width: 104px;
                font-size: 0.74rem;
            }
            .chk-combat-sub {
                font-size: 0.62rem;
            }
        }

        /* Boss Element Colors & Badge Styles */
        .elem-dia {
            color: #FDE047;
            text-shadow: 0 0 8px #FACC15, 0 0 16px rgba(250, 204, 21, 0.6);
        }
        .elem-thuy {
            color: #38BDF8;
            text-shadow: 0 0 8px #38BDF8, 0 0 16px rgba(56, 189, 248, 0.6);
        }
        .elem-hoa {
            color: #FF5252;
            text-shadow: 0 0 8px #FF5252, 0 0 16px rgba(255, 82, 82, 0.6);
        }
        .elem-phong {
            color: #4ADE80;
            text-shadow: 0 0 8px #4ADE80, 0 0 16px rgba(74, 222, 128, 0.6);
        }
        .boss-elem-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 3px 12px;
            font-size: 1.05rem;
            font-weight: 900;
            border-radius: 7px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.18);
            letter-spacing: 0.5px;
            user-select: none;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
        }

        .btn-fs {
            background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(2, 132, 199, 0.35));
            border: 1px solid #38bdf8;
            color: #38bdf8;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.75rem;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 5px;
            transition: all 0.2s ease;
        }

        .btn-fs:hover {
            background: #38bdf8;
            color: #090d16;
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.5);
        }

        .btn-fs:active {
            transform: scale(0.95);
        }

        /* Stream Controls (Speed selector & Live indicator) */
        .stream-ctrl-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            margin-top: 10px;
            padding-top: 8px;
            border-top: 1px solid rgba(255, 255, 255, 0.06);
            flex-wrap: wrap;
        }

        .speed-group {
            display: inline-flex;
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 2px;
            gap: 2px;
        }

        .speed-btn {
            background: transparent;
            border: none;
            color: #94a3b8;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .speed-btn:hover {
            color: #fff;
        }

        .speed-btn.active {
            background: var(--accent);
            color: #fff;
            box-shadow: 0 2px 8px rgba(234, 88, 12, 0.4);
        }

        .stream-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.73rem;
            color: #94a3b8;
        }

        .stream-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: #64748b;
            transition: 0.3s;
        }

        .stream-dot.live {
            background-color: #10b981;
            box-shadow: 0 0 8px #10b981;
            animation: pulse 1.2s infinite;
        }

        /* Fullscreen Theater Mode */
        .screen-card.fullscreen-active {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            right: 0 !important;
            bottom: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            height: 100dvh !important;
            max-width: 100vw !important;
            margin: 0 !important;
            padding: 0 !important;
            border-radius: 0 !important;
            border: none !important;
            background: #000 !important;
            z-index: 99999 !important;
            display: flex !important;
            flex-direction: column !important;
        }

        .screen-card.fullscreen-active .card-header,
        .screen-card.fullscreen-active .stream-ctrl-bar {
            display: none !important;
        }

        .screen-card.fullscreen-active .preview-box {
            flex: 1;
            width: 100%;
            height: 100%;
            min-height: 0;
            border-radius: 0;
            border: none;
            box-shadow: none;
            background: #000;
        }

        .screen-card.fullscreen-active .preview-img {
            width: 100%;
            height: 100%;
            object-fit: contain;
        }

        .fs-overlay-bar {
            display: none;
            position: absolute;
            top: calc(8px + env(safe-area-inset-top, 0px));
            left: 10px;
            right: 10px;
            z-index: 1000;
            padding: 6px 12px;
            background: rgba(15, 23, 42, 0.88);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border-radius: 12px;
            border: 1px solid rgba(56, 189, 248, 0.25);
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            transition: opacity 0.3s ease;
        }

        .screen-card.fullscreen-active .fs-overlay-bar {
            display: flex;
        }

        .fs-overlay-bar.dimmed {
            opacity: 0.18;
        }

        .fs-overlay-bar.dimmed:hover,
        .fs-overlay-bar.dimmed:active {
            opacity: 1;
        }

        .fs-info {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.8rem;
            font-weight: 700;
            color: #f8fafc;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .fs-btn-close {
            background: rgba(239, 68, 68, 0.2);
            border: 1px solid #ef4444;
            color: #fca5a5;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            transition: 0.2s;
        }

        .fs-btn-close:active {
            transform: scale(0.95);
            background: #ef4444;
            color: #fff;
        }

        .fs-quick-actions {
            display: flex;
            gap: 6px;
        }

        .fs-btn-action {
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 600;
            border: none;
            cursor: pointer;
            color: #fff;
        }

        .fs-rotate-hint {
            display: none;
            position: absolute;
            bottom: calc(14px + env(safe-area-inset-bottom, 0px));
            left: 50%;
            transform: translateX(-50%);
            background: rgba(15, 23, 42, 0.82);
            border: 1px solid rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(8px);
            color: #94a3b8;
            font-size: 0.72rem;
            padding: 5px 14px;
            border-radius: 20px;
            pointer-events: none;
            white-space: nowrap;
            z-index: 500;
        }

        @media (orientation: portrait) and (max-width: 900px) {
            .screen-card.fullscreen-active .fs-rotate-hint {
                display: block;
            }
        }

        /* Interactive Touch Ripple & Coordinates */
        .touch-ripple {
            position: absolute;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: rgba(56, 189, 248, 0.45);
            border: 2px solid #38bdf8;
            pointer-events: none;
            animation: rippleAnim 0.6s ease-out forwards;
            z-index: 100;
        }

        .touch-coord {
            position: absolute;
            background: rgba(15, 23, 42, 0.88);
            border: 1px solid #38bdf8;
            color: #38bdf8;
            font-size: 0.68rem;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 4px;
            pointer-events: none;
            transform: translate(-50%, -130%);
            animation: coordAnim 0.8s ease-out forwards;
            z-index: 101;
            white-space: nowrap;
            box-shadow: 0 2px 8px rgba(0,0,0,0.5);
        }

        @keyframes rippleAnim {
            0% { transform: scale(0.3); opacity: 1; }
            100% { transform: scale(2.5); opacity: 0; }
        }

        @keyframes coordAnim {
            0% { opacity: 1; transform: translate(-50%, -100%); }
            80% { opacity: 0.9; transform: translate(-50%, -140%); }
            100% { opacity: 0; transform: translate(-50%, -160%); }
        }

        /* Team Card */
        .team-list-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-top: 12px;
        }

        .team-box {
            background: rgba(8, 13, 24, 0.75);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 10px;
            height: 300px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4);
        }

        .team-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            border-radius: 12px;
            background: rgba(22, 33, 56, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.08);
            font-size: 0.85rem;
            font-weight: 600;
            color: #f1f5f9;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            min-height: 44px;
        }

        .team-item:active {
            transform: scale(0.97);
            border-color: var(--accent);
            background: rgba(249, 115, 22, 0.15);
        }

        .btn-del-member {
            background: linear-gradient(135deg, #dc2626, #ef4444);
            color: white;
            border: none;
            width: 32px;
            height: 32px;
            border-radius: 8px;
            font-size: 0.9rem;
            font-weight: 800;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 8px rgba(239, 68, 68, 0.35);
            transition: 0.2s transform;
            flex-shrink: 0;
        }

        .btn-del-member:active {
            transform: scale(0.9);
        }

        /* Log Console */
        .log-box {
            background: #040711;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 12px;
            font-family: var(--font-mono);
            font-size: 0.82rem;
            height: 330px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 5px;
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.6);
        }

        .log-entry {
            line-height: 1.45;
            color: #cbd5e1;
            word-break: break-word;
            font-family: var(--font-mono);
        }

        .log-filter-btn {
            min-height: 34px;
            padding: 6px 12px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 0.75rem;
            transition: all 0.2s ease;
        }

        /* Unified Floating Mobile Control Dock (Island Design) */
        .bottom-fixed-dock {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 100;
            max-width: 580px;
            margin: 0 auto;
            padding: 0 10px calc(8px + env(safe-area-inset-bottom, 0px)) 10px;
            pointer-events: none;
            transform: translateZ(0);
            -webkit-transform: translateZ(0);
        }

        .dock-glass-shell {
            background: rgba(10, 16, 30, 0.88);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-top: 1px solid rgba(255, 255, 255, 0.22);
            border-radius: 24px;
            box-shadow: 0 -8px 36px rgba(0, 0, 0, 0.7), 0 0 24px rgba(56, 189, 248, 0.1);
            overflow: hidden;
            pointer-events: auto;
        }

        .action-bar {
            padding: 8px 10px;
            display: flex;
            gap: 7px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.07);
        }

        .btn-action {
            flex: 1;
            padding: 11px 8px;
            border: none;
            border-radius: 12px;
            font-weight: 800;
            font-size: 0.84rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 5px;
            letter-spacing: 0.3px;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            min-height: 46px;
        }

        .btn-action:active {
            transform: scale(0.95);
        }

        .btn-launch {
            flex: 1.3;
            background: linear-gradient(135deg, #059669 0%, #10b981 100%);
            color: #ffffff;
            box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4);
            border: 1px solid rgba(52, 211, 153, 0.4);
        }

        .btn-stop {
            flex: 1.3;
            background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
            color: #ffffff;
            box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4);
            border: 1px solid rgba(248, 113, 113, 0.4);
        }

        .btn-exit {
            flex: 1;
            background: linear-gradient(135deg, #334155 0%, #475569 100%);
            color: #f1f5f9;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* Bottom Tab Navigation Bar */
        .tab-bar {
            padding: 4px 6px 6px 6px;
            display: flex;
            justify-content: space-around;
            align-items: center;
        }

        .tab-button {
            background: transparent;
            border: none;
            color: #94a3b8;
            padding: 6px 4px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 3px;
            font-size: 0.72rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 12px;
            flex: 1;
            position: relative;
            min-height: 52px;
        }

        .tab-button .tab-icon {
            font-size: 1.3rem;
            line-height: 1;
            transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .tab-button.active {
            color: #38bdf8;
        }

        .tab-button.active .tab-icon {
            transform: scale(1.18) translateY(-2px);
            filter: drop-shadow(0 0 8px rgba(56, 189, 248, 0.6));
        }

        .tab-button.active::after {
            content: '';
            position: absolute;
            bottom: 2px;
            width: 16px;
            height: 3px;
            background: #38bdf8;
            border-radius: 3px;
            box-shadow: 0 0 8px #38bdf8;
        }

        .tab-button:active {
            transform: scale(0.92);
        }

        .toast {
            position: fixed;
            top: 70px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(15, 23, 42, 0.92);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            color: #fff;
            padding: 10px 20px;
            border-radius: 12px;
            border: 1px solid rgba(56, 189, 248, 0.3);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5), 0 0 12px rgba(56, 189, 248, 0.25);
            font-size: 0.82rem;
            font-weight: 600;
            z-index: 200;
            opacity: 0;
            pointer-events: none;
            transition: 0.3s opacity, 0.3s transform;
        }
        .toast.show { opacity: 1; transform: translateX(-50%) translateY(4px); }
    </style>
</head>
<body>

    <!-- Header -->
    <header class="app-header">
        <div class="brand">
            <span>⚡ TS Origin</span>
        </div>
        <div class="status-pill" id="statusPill">
            <span class="status-dot" id="statusDot"></span>
            <span id="statusText">Sẵn sàng</span>
        </div>
    </header>

    <!-- LDPlayer Carousel Header -->
    <div class="ld-carousel-wrapper">
        <div class="ld-carousel" id="ldCarousel"></div>
    </div>

    <div class="container">

        <!-- TAB 1: 👁️ MÀN HÌNH GAME -->
        <div class="tab-pane active" id="tabPane_screen">
            <div class="card screen-card" id="screenCard">
                <div class="card-header">
                    <span class="card-title">👁️ Màn Hình Trực Tiếp</span>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <button class="btn-mini" onclick="refreshScreenshot()">📸 Chụp Ảnh</button>
                        <button class="btn-fs" onclick="toggleFullscreen(true)">⛶ Toàn Màn Hình</button>
                    </div>
                </div>

                <!-- Floating Toolbar in Fullscreen Mode -->
                <div class="fs-overlay-bar" id="fsOverlayBar">
                    <div class="fs-info">
                        <span class="status-dot" id="fsStatusDot"></span>
                        <span id="fsTabTitle">🖥️ Tab LDPlayer</span>
                        <span class="stream-badge" id="fsStreamBadge" style="margin-left:4px;">⚡ 0.5s</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <div class="speed-group">
                            <button class="speed-btn" data-speed="500" onclick="setStreamSpeed(500)">0.5s</button>
                            <button class="speed-btn" data-speed="1000" onclick="setStreamSpeed(1000)">1.0s</button>
                            <button class="speed-btn" data-speed="2000" onclick="setStreamSpeed(2000)">2.0s</button>
                        </div>
                        <div class="fs-quick-actions">
                            <button class="fs-btn-action btn-stop" onclick="sendAction('stop')">🛑 Dừng</button>
                        </div>
                        <button class="fs-btn-close" onclick="toggleFullscreen(false)">✕ Thoát</button>
                    </div>
                </div>

                <div class="preview-box" id="screenPreviewBox">
                    <img id="screenImg" class="preview-img" src="/api/screenshot" alt="Màn hình giả lập">
                    <div class="fs-rotate-hint">📱 Xoay ngang điện thoại để xem cực đại</div>
                </div>

                <div class="stream-ctrl-bar">
                    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                        <label style="font-size:0.75rem; font-weight:600; color:var(--text-muted); display:inline-flex; align-items:center; white-space:nowrap; cursor:pointer;">
                            <input type="checkbox" id="autoStream" onchange="toggleAutoStream(this.checked)" checked style="accent-color:var(--accent); margin-right:5px;"> Tự truyền ảnh
                        </label>
                        <div class="speed-group">
                            <button class="speed-btn" data-speed="500" onclick="setStreamSpeed(500)">⚡ 0.5s (Mượt)</button>
                            <button class="speed-btn" data-speed="1000" onclick="setStreamSpeed(1000)">⏱️ 1.0s</button>
                            <button class="speed-btn" data-speed="2000" onclick="setStreamSpeed(2000)">🌱 2.0s</button>
                        </div>
                    </div>
                    <span class="stream-badge" id="lblStreamStatus">
                        <span class="stream-dot live" id="streamDot"></span>
                        <span id="streamSpeedText">Đang truyền (0.5s)</span>
                    </span>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span class="card-title">🖥️ Giả Lập & Máy Chủ</span>
                    <button class="btn-mini" onclick="refreshTabs()">🔄 Quét Lại</button>
                </div>
                <div class="form-grid">
                    <div class="form-group">
                        <label>Tab LDPlayer</label>
                        <select id="selectTab" onchange="onTabChanged(this.value)">
                            <option>Đang nạp tab...</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Máy Chủ</label>
                        <select id="selectServer" onchange="onServerChanged(this.value)">
                            <option>Điêu Thuyền</option>
                        </select>
                    </div>
                </div>

                <div style="margin-top:10px; display:flex; align-items:center; justify-content:space-between; background:rgba(255,255,255,0.02); padding:8px 12px; border-radius:8px; border:1px solid var(--border);">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-size:1.1rem;">✈️</span>
                        <div>
                            <div style="font-size:0.82rem; font-weight:700; color:var(--text);">Cảnh Báo Telegram</div>
                            <div style="font-size:0.70rem; color:var(--text-muted);">Gửi ảnh chụp và thông báo về bot</div>
                        </div>
                    </div>
                    <label class="switch">
                        <input type="checkbox" id="chk_enable_telegram" onchange="onCheckboxChanged('enable_telegram', this.checked)">
                        <span class="slider"></span>
                    </label>
                </div>
            </div>

            <!-- Card Hẹn Giờ Hoạt Động (A, B, C, D) -->
            <div class="card" style="margin-top:12px;">
                <div class="card-header">
                    <span class="card-title">⏰ Hẹn Giờ Hoạt Động (A, B, C, D)</span>
                </div>
                <div style="display:flex; align-items:center; justify-content:space-between; background:rgba(255,255,255,0.02); padding:8px 12px; border-radius:8px; border:1px solid var(--border);">
                    <div class="combat-col-left">
                        <input type="checkbox" id="chk_hen_gio" onchange="onCheckboxChanged('hen_gio', this.checked)">
                        <button type="button" class="combat-btn-ctrl" onclick="document.getElementById('chk_hen_gio').click()" style="justify-content:center; text-align:center;">Hẹn Giờ</button>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <input type="text" id="entry_hen_gio_time" value="05:00" placeholder="05:00" maxlength="5" class="combat-select-right" style="width:75px; text-align:center; font-weight:700; color:#fff; background:#1e293b; border:1px solid #475569;" onchange="onTextChanged('hen_gio_time', this.value)" onkeyup="if(event.key==='Enter') this.blur()">
                        <span id="lbl_realtime_clock" style="font-family:monospace, 'Segoe UI'; font-size:0.82rem; font-weight:700; color:#38bdf8; background:#1e293b; border:1px solid #475569; padding:4px 10px; border-radius:6px; min-width:70px; text-align:center;">--:--:--</span>
                    </div>
                </div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-top:6px; padding:0 4px; line-height:1.4;">
                    💡 Khi tích Hẹn Giờ, các Card (A, B, C, D) gạt ON sẽ chờ đến đúng mốc giờ mới chạy tuần tự. Chạy xong tự động nhả về OFF.
                </div>
            </div>
        </div>

        <!-- TAB 2: ⚙️ HOẠT ĐỘNG -->
        <div class="tab-pane" id="tabPane_activity">
            <!-- Boss Thế Giới -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">🔥 Boss Thế Giới</span>
                    <label class="switch">
                        <input type="checkbox" id="switch_A" onchange="onSwitchChanged('A', this.checked)">
                        <span class="slider"></span>
                    </label>
                </div>
                <div style="display:flex; align-items:center; gap:8px; background:rgba(255,255,255,0.02); padding:8px 10px; border-radius:8px; border:1px solid var(--border);">
                    <div style="flex:1; min-width:0; display:flex; align-items:center; gap:8px;">
                        <label class="chk-label" style="font-size:0.78rem;">
                            <input type="checkbox" id="chk_A1" onchange="onCheckboxChanged('A1', this.checked)"> 👑 Boss
                        </label>
                        <span id="boss_elem_badge" class="boss-elem-badge elem-dia">Địa</span>
                    </div>
                    <div style="flex:1; min-width:0;">
                        <select id="combo_A_char" style="width:100%; font-size:0.82rem; padding:5px 8px; text-align:center;" onchange="onComboChanged('A_char', this.value)"></select>
                    </div>
                </div>
            </div>

            <!-- Phụ Bản Đơn / Đội -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">⚔️ Phụ Bản Đơn / Đội</span>
                    <label class="switch">
                        <input type="checkbox" id="switch_B" onchange="onSwitchChanged('B', this.checked)">
                        <span class="slider"></span>
                    </label>
                </div>

                <!-- Hàng 1: Split Đơn và Đội -->
                <div style="display:flex; align-items:stretch; gap:8px; position:relative; background:rgba(255,255,255,0.02); padding:8px 10px; border-radius:8px; border:1px solid var(--border); margin-bottom:10px;">
                    <!-- Đơn (Cá nhân) -->
                    <div style="flex:1; min-width:0; display:flex; flex-direction:column; gap:6px;">
                        <label class="chk-label" style="font-size:0.75rem; padding:5px 6px; width:100%; justify-content:center;">
                            <input type="checkbox" id="chk_B_don" onchange="onCheckboxChanged('B_don', this.checked)"> 👤 Đơn (Cá Nhân)
                        </label>
                        <select id="combo_B_don_char" style="width:100%; font-size:0.82rem; padding:5px 8px; text-align:center;" onchange="onComboChanged('B_don_char', this.value)"></select>
                    </div>

                    <!-- Vạch đứng mờ -->
                    <div style="width:1px; background:rgba(255,255,255,0.12); border-radius:1px;"></div>

                    <!-- Đội (Tổ đội) -->
                    <div style="flex:1; min-width:0; display:flex; flex-direction:column; gap:6px;">
                        <label class="chk-label" style="font-size:0.75rem; padding:5px 6px; width:100%; justify-content:center;">
                            <input type="checkbox" id="chk_B_doi" onchange="onCheckboxChanged('B_doi', this.checked)"> 👥 Đội (Tổ Đội)
                        </label>
                        <select id="combo_B_team_char" style="width:100%; font-size:0.82rem; padding:5px 8px; text-align:center;" onchange="onComboChanged('B_team_char', this.value)"></select>
                    </div>
                </div>

                <!-- Hàng 2: Các mốc Phụ Bản (PB 20 - PB 140) -->
                <div style="display:flex; flex-wrap:nowrap; gap:5px; justify-content:space-between; background:rgba(0,0,0,0.2); padding:6px 8px; border-radius:8px; border:1px solid var(--border); overflow-x:auto;">
                    <label class="chk-label" style="font-size:0.74rem; padding:5px 4px; flex:1; justify-content:center;"><input type="checkbox" id="chk_B1" onchange="onCheckboxChanged('B1', this.checked)"> PB 20</label>
                    <label class="chk-label" style="font-size:0.74rem; padding:5px 4px; flex:1; justify-content:center;"><input type="checkbox" id="chk_B2" onchange="onCheckboxChanged('B2', this.checked)"> PB 50</label>
                    <label class="chk-label" style="font-size:0.74rem; padding:5px 4px; flex:1; justify-content:center;"><input type="checkbox" id="chk_B3" onchange="onCheckboxChanged('B3', this.checked)"> PB 80</label>
                    <label class="chk-label" style="font-size:0.74rem; padding:5px 4px; flex:1; justify-content:center;"><input type="checkbox" id="chk_B4" onchange="onCheckboxChanged('B4', this.checked)"> PB 110</label>
                    <label class="chk-label" style="font-size:0.74rem; padding:5px 4px; flex:1; justify-content:center;"><input type="checkbox" id="chk_B5" onchange="onCheckboxChanged('B5', this.checked)"> PB 140</label>
                </div>
            </div>

            <!-- Dị Giới Đêm -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">🌌 Dị Giới Đêm</span>
                    <label class="switch">
                        <input type="checkbox" id="switch_C" onchange="onSwitchChanged('C', this.checked)">
                        <span class="slider"></span>
                    </label>
                </div>
                <div style="display:flex; align-items:center; justify-content:space-between; gap:6px; background:rgba(255,255,255,0.02); padding:8px 10px; border-radius:8px; border:1px solid var(--border);">
                    <label class="chk-label" style="font-size:0.76rem; padding:6px 8px; flex:1; justify-content:center;"><input type="checkbox" id="chk_C1" onchange="onCheckboxChanged('C1', this.checked)"> Phúc Thần</label>
                    <div style="width:1px; height:18px; background:rgba(255,255,255,0.12);"></div>
                    <label class="chk-label" style="font-size:0.76rem; padding:6px 8px; flex:1; justify-content:center;"><input type="checkbox" id="chk_C2" onchange="onCheckboxChanged('C2', this.checked)"> Ký Lục</label>
                    <div style="width:1px; height:18px; background:rgba(255,255,255,0.12);"></div>
                    <label class="chk-label" style="font-size:0.76rem; padding:6px 8px; flex:1; justify-content:center;"><input type="checkbox" id="chk_C3" onchange="onCheckboxChanged('C3', this.checked)"> Rút Gọn</label>
                </div>
            </div>
        </div>

        <!-- TAB 3: 🏆 SỰ KIỆN (40 NPC, NHỊ KIỀU & QUẢN LÝ TỔ ĐỘI) -->
        <div class="tab-pane" id="tabPane_team">
            <!-- 40 NPC / 2K - Nhị Kiều -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">🏛️ 40 NPC / 2K - Nhị Kiều</span>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <label class="chk-round" title="Tạm Dừng Card D">
                            <input type="checkbox" id="chk_pause_D" onchange="onCheckboxChanged('pause_D', this.checked)">
                            <span class="chk-mark">✓</span>
                        </label>
                        <label class="switch">
                            <input type="checkbox" id="switch_D" onchange="onSwitchChanged('D', this.checked)">
                            <span class="slider"></span>
                        </label>
                    </div>
                </div>

                <!-- Hàng 1: Tổ Đội + Dropdown Vị Trí (Đồng bộ tỷ lệ 50-50 với Card A & Card B) -->
                <div style="display:flex; align-items:center; gap:8px; background:rgba(255,255,255,0.02); padding:8px 10px; border-radius:8px; border:1px solid var(--border); margin-bottom:12px;">
                    <div style="flex:1; min-width:0;">
                        <label class="chk-label" style="font-size:0.78rem;">
                            <input type="checkbox" id="chk_D2" onchange="onCheckboxChanged('D2', this.checked)"> 👥 Tổ Đội
                        </label>
                    </div>
                    <div style="flex:1; min-width:0;">
                        <select id="combo_D_team_char" style="width:100%; font-size:0.82rem; padding:5px 8px; text-align:center;" onchange="onComboChanged('D_team_char', this.value)"></select>
                    </div>
                </div>

                <!-- Hàng 2 & 3: Bố cục 2 Cột song song -->
                <div style="display:flex; align-items:stretch; gap:10px;">
                    <!-- Cột Trái: 40 NPC -->
                    <div style="flex:1; min-width:0; background:rgba(255,255,255,0.02); padding:8px 10px; border-radius:8px; border:1px solid var(--border); display:flex; flex-direction:column; justify-content:space-between;">
                        <label class="chk-label" style="font-size:0.76rem; width:100%; justify-content:center;">
                            <input type="checkbox" id="chk_D3" onchange="onCheckboxChanged('D3', this.checked)"> ⚔️ 40 NPC
                        </label>
                        <div style="margin-top:6px;">
                            <label style="display:block; font-size:0.72rem; color:#9CA3AF; margin-bottom:4px; white-space:nowrap;">Chế độ:</label>
                            <select id="combo_D_chien_dau" style="width:100%; font-size:0.78rem; padding:4px 4px;" onchange="onComboChanged('D_chien_dau', this.value)">
                                <option value="Auto">Auto</option><option value="Click">Click</option>
                            </select>
                        </div>
                    </div>

                    <!-- Cột Phải: Nhị Kiều -->
                    <div style="flex:1; min-width:0; background:rgba(255,255,255,0.02); padding:8px 10px; border-radius:8px; border:1px solid var(--border); display:flex; flex-direction:column; justify-content:space-between;">
                        <label class="chk-label" style="font-size:0.76rem; width:100%; justify-content:center;">
                            <input type="checkbox" id="chk_D4" onchange="onCheckboxChanged('D4', this.checked)"> 🗼 Nhị Kiều
                        </label>
                        <div style="margin-top:6px;">
                            <label style="display:block; font-size:0.72rem; color:#9CA3AF; margin-bottom:4px; white-space:nowrap;">Mốc tầng:</label>
                            <select id="combo_D_tang" style="width:100%; font-size:0.78rem; padding:4px 4px;" onchange="onComboChanged('D_tang', this.value)">
                                <option value="Auto" selected>Auto</option>
                                <option value="1 - 14">1 - 14</option>
                                <option value="Trệt - 10">Trệt - 10</option><option value="11 - 14">11 - 14</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Quản Lý Tổ Đội -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">👥 Quản Lý Tổ Đội</span>
                </div>
                <div style="background:rgba(255,255,255,0.02); padding:8px 8px; border-radius:8px; border:1px solid var(--border); margin-bottom:12px;">
                    <!-- HÀNG 1: [x] Mời Đội - Menu Số Lượng (gọn 48px) - Menu Map (mở rộng) -->
                    <div style="display:grid; grid-template-columns: auto 48px 1fr; gap:6px; align-items:center; margin-bottom:8px;">
                        <label class="chk-label" style="font-size:0.8rem; font-weight:600; white-space:nowrap;">
                            <input type="checkbox" id="chk_E_moi_doi" onchange="onCheckboxChanged('E_moi_doi', this.checked)"> 👥 Mời Đội
                        </label>
                        <select id="combo_E_so_luong" style="width:100%; font-size:0.78rem; padding:4px 2px; font-weight:bold; text-align:center;" onchange="onComboChanged('E_so_luong', this.value)">
                            <option value="1">1</option>
                            <option value="2">2</option>
                            <option value="3">3</option>
                            <option value="4">4</option>
                        </select>
                        <select id="combo_E_map" style="width:100%; font-size:0.78rem; padding:4px 6px; font-weight:bold;" onchange="onComboChanged('E_map', this.value)">
                            <option value="(Chưa có map)">(Chưa có map)</option>
                        </select>
                    </div>
                    <!-- HÀNG 2: Quân Sư - Menu Tên Quân Sư -->
                    <div style="display:grid; grid-template-columns: auto 1fr; gap:8px; align-items:center;">
                        <span style="font-size:0.8rem; font-weight:bold; color:#F59E0B; white-space:nowrap;">Quân Sư:</span>
                        <select id="combo_E_quan_su" style="width:100%; font-size:0.78rem; padding:4px 6px;" onchange="onComboChanged('E_quan_su', this.value)"></select>
                    </div>
                </div>

                <div class="team-list-container">
                    <div>
                        <label style="display:block; margin-bottom:4px; font-size:0.75rem; color:var(--text-muted); font-weight:600;">Tướng Có Sẵn (Chạm ➔ thêm)</label>
                        <div class="team-box" id="list_E_A_box">
                            <div style="color:#64748b; font-size:0.75rem; padding:4px;">Đang nạp...</div>
                        </div>
                    </div>
                    <div>
                        <label style="display:block; margin-bottom:4px; font-size:0.75rem; color:var(--text-muted); font-weight:600;">Đội Hình (Chạm ✕ xóa)</label>
                        <div class="team-box" id="list_E_B_box">
                            <div style="color:#64748b; font-size:0.75rem; padding:4px;">(Trống)</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- TAB 4: 📅 HOẠT ĐỘNG NGÀY -->
        <div class="tab-pane" id="tabPane_daily">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">📅 Hoạt Động Ngày</span>
                </div>
                <!-- Hàng 1: [ ] Nhận Thư | [ Menu Mốc Giờ ] -->
                <div style="display:flex; align-items:center; justify-content:space-between; background:rgba(255,255,255,0.02); padding:8px 10px; border-radius:8px; border:1px solid var(--border);">
                    <label class="chk-label" style="font-size:0.8rem; font-weight:600;">
                        <input type="checkbox" id="chk_nhan_thu" onchange="onCheckboxChanged('nhan_thu', this.checked)"> 📬 Nhận Thư
                    </label>
                    <select id="combo_nhan_thu_time" class="combat-select-right" style="width:114px; min-width:100px; max-width:114px;" onchange="onComboChanged('nhan_thu_time', this.value)">
                        <option value="Tất Cả" selected>Tất Cả</option>
                        <option value="12H01">12H01</option>
                        <option value="18H01">18H01</option>
                        <option value="22H01">22H01</option>
                    </select>
                </div>
            </div>
        </div>

        <!-- TAB 5: ⚔️ CHIẾN ĐẤU -->
        <div class="tab-pane" id="tabPane_combat">
            <div class="card">
                <div class="card-header">
                    <span class="card-title">⚔️ Cấu Hình Chiến Đấu</span>
                </div>
                <!-- Hàng 1: HP / SP -->
                <div style="display:flex; align-items:center; justify-content:space-between; background:rgba(255,255,255,0.02); padding:8px 10px; border-radius:8px; border:1px solid var(--border);">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <div class="combat-col-left">
                            <input type="checkbox" id="chk_buff" onchange="onCheckboxChanged('buff', this.checked)">
                            <button type="button" class="combat-btn-ctrl" onclick="document.getElementById('chk_buff').click()">⚡ HP / SP</button>
                        </div>
                        <span class="chk-combat-sub">(Tắt Auto)</span>
                    </div>
                    <select id="combo_buff" class="combat-select-right" onchange="onComboChanged('buff', this.value)">
                        <option value="Buff HP">Buff HP</option>
                        <option value="Buff SP">Buff SP</option>
                        <option value="Buff 3HP / 1SP">Buff 3HP / 1SP</option>
                        <option value="HP / SP / HS">HP / SP / HS</option>
                    </select>
                </div>
                <!-- Hàng 2: [ ] [ Kỹ Năng ▼ ] (Tắt Auto) | [ Mục Tiêu ▼ ] -->
                <div style="display:flex; align-items:center; justify-content:space-between; background:rgba(255,255,255,0.02); padding:8px 10px; border-radius:8px; border:1px solid var(--border); margin-top:8px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <div class="combat-col-left">
                            <input type="checkbox" id="chk_phong_thu" onchange="onCheckboxChanged('phong_thu', this.checked)">
                            <select id="combo_phong_thu_skill" class="combat-btn-ctrl" onchange="onComboChanged('phong_thu_skill', this.value)">
                                <option value="Kết Giới">Kết Giới</option>
                                <option value="Linh Kính">Linh Kính</option>
                                <option value="Băng Tường">Băng Tường</option>
                            </select>
                        </div>
                        <span class="chk-combat-sub">(Tắt Auto)</span>
                    </div>
                    <select id="combo_phong_thu_target" class="combat-select-right" onchange="onComboChanged('phong_thu_target', this.value)">
                        <option value="Chart">Chart</option>
                        <option value="Chart / Pet">Chart / Pet</option>
                        <option value="Team">Team</option>
                    </select>
                </div>
            </div>
        </div>

        <!-- TAB 6: 📜 NHẬT KÝ HOẠT ĐỘNG -->
        <div class="tab-pane" id="tabPane_logs">
            <div class="card">
                <div class="card-header" style="flex-wrap: wrap; gap: 6px;">
                    <span class="card-title">📜 Nhật Ký Hoạt Động</span>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <button class="btn-mini" style="background:#374151;" onclick="scrollLogsToBottom()">⬇️ Xuống Dưới</button>
                        <button class="btn-mini" onclick="refreshLogs()">🔄 Làm Mới</button>
                    </div>
                </div>
                <!-- Filter Bar -->
                <div style="display:flex; gap:6px; margin-bottom:8px; overflow-x:auto; padding-bottom:2px;">
                    <button class="btn-mini log-filter-btn" id="btnFilterAll" style="background:#2563EB; font-weight:600;" onclick="setLogFilter('all')">Tất cả</button>
                    <button class="btn-mini log-filter-btn" id="btnFilterSuccess" style="background:#374151;" onclick="setLogFilter('success')">✅ Thành công</button>
                    <button class="btn-mini log-filter-btn" id="btnFilterWarn" style="background:#374151;" onclick="setLogFilter('warn')">⚠️ Cảnh báo</button>
                    <button class="btn-mini log-filter-btn" id="btnFilterAction" style="background:#374151;" onclick="setLogFilter('action')">🎯 Nhận diện/ADB</button>
                </div>
                <div class="log-box" id="logConsole">
                    <div class="log-entry">Đang nạp nhật ký...</div>
                </div>
            </div>
        </div>

    </div>

    <!-- Thanh Cố Định Đáy Màn Hình (Floating Island Dock) -->
    <div class="bottom-fixed-dock">
        <div class="dock-glass-shell">
            <div class="action-bar">
                <button class="btn-action btn-launch" onclick="sendAction('launch_game')">🎮 GAME</button>
                <button class="btn-action btn-stop" onclick="sendAction('stop')">🛑 STOP</button>
                <button class="btn-action btn-exit" onclick="sendAction('exit_game')">🚪 EXIT</button>
            </div>

            <nav class="tab-bar">
                <button class="tab-button active" onclick="switchTab('screen', this)">
                    <span class="tab-icon">👁️</span>
                    <span>Màn Hình</span>
                </button>
                <button class="tab-button" onclick="switchTab('activity', this)">
                    <span class="tab-icon">⚙️</span>
                    <span>Hoạt Động</span>
                </button>
                <button class="tab-button" onclick="switchTab('team', this)">
                    <span class="tab-icon">🏆</span>
                    <span>Sự Kiện</span>
                </button>
                <button class="tab-button" onclick="switchTab('daily', this)">
                    <span class="tab-icon">📅</span>
                    <span>Ngày</span>
                </button>
                <button class="tab-button" onclick="switchTab('combat', this)">
                    <span class="tab-icon">⚔️</span>
                    <span>Chiến Đấu</span>
                </button>
                <button class="tab-button" onclick="switchTab('logs', this)">
                    <span class="tab-icon">📜</span>
                    <span>Nhật Ký</span>
                </button>
            </nav>
        </div>
    </div>

    <div class="toast" id="toast">Thông báo</div>

    <script>
        let streamTimer = null;

        function switchTab(tabId, btn) {
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
            
            const activePane = document.getElementById('tabPane_' + tabId);
            if (activePane) activePane.classList.add('active');
            if (btn) btn.classList.add('active');

            window.scrollTo({ top: 0, behavior: 'instant' });
            
            if (tabId === 'screen') refreshScreenshot();
            if (tabId === 'logs') fetchStatus();
        }

        function showToast(msg) {
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 2000);
        }

        async function refreshLogs() {
            await fetchStatus();
            showToast('🔄 Đã làm mới nhật ký!');
        }

        let currentLogFilter = 'all';
        let cachedLogsList = [];

        function setLogFilter(filterType) {
            currentLogFilter = filterType;
            ['btnFilterAll', 'btnFilterSuccess', 'btnFilterWarn', 'btnFilterAction'].forEach(id => {
                const b = document.getElementById(id);
                if (b) b.style.background = '#374151';
            });
            const activeMap = { 'all': 'btnFilterAll', 'success': 'btnFilterSuccess', 'warn': 'btnFilterWarn', 'action': 'btnFilterAction' };
            const activeBtn = document.getElementById(activeMap[filterType]);
            if (activeBtn) activeBtn.style.background = '#2563EB';
            renderFilteredLogs(cachedLogsList);
        }

        function scrollLogsToBottom() {
            const logConsole = document.getElementById('logConsole');
            if (logConsole) {
                logConsole.scrollTop = logConsole.scrollHeight;
                showToast('⬇️ Đã cuộn xuống nhật ký mới nhất');
            }
        }

        function renderFilteredLogs(logs) {
            const logConsole = document.getElementById('logConsole');
            if (!logConsole || !logs) return;
            cachedLogsList = logs;

            let filtered = logs;
            if (currentLogFilter === 'success') {
                filtered = logs.filter(l => l.includes('✅') || l.includes('🎉'));
            } else if (currentLogFilter === 'warn') {
                filtered = logs.filter(l => l.includes('⚠️') || l.includes('❌') || l.includes('🛑') || l.includes('Lỗi') || l.includes('Fallback'));
            } else if (currentLogFilter === 'action') {
                filtered = logs.filter(l => l.includes('🎯') || l.includes('👁️') || l.includes('📜') || l.includes('🕹️') || l.includes('👑') || l.includes('Tap') || l.includes('Swipe'));
            }

            if (filtered.length === 0) {
                logConsole.innerHTML = '<div class="log-entry" style="color:#64748b; font-style:italic; padding:8px;">(Không có bản ghi phù hợp với bộ lọc này)</div>';
                return;
            }

            const newHtml = filtered.map(l => {
                let color = '#cbd5e1';
                if (l.includes('✅') || l.includes('🎉')) color = '#4ade80';
                else if (l.includes('⚠️') || l.includes('⏸️')) color = '#fbbf24';
                else if (l.includes('❌') || l.includes('🛑') || l.includes('Lỗi')) color = '#f87171';
                else if (l.includes('🎯') || l.includes('👁️') || l.includes('👑')) color = '#38bdf8';
                else if (l.includes('📜') || l.includes('🕹️')) color = '#c084fc';
                else if (l.includes('⏳') || l.includes('▶️')) color = '#93c5fd';
                return `<div class="log-entry" style="color:${color};">${l}</div>`;
            }).join('');

            const isNearBottom = (logConsole.scrollHeight - logConsole.scrollTop - logConsole.clientHeight) < 60;
            if (logConsole.innerHTML !== newHtml) {
                logConsole.innerHTML = newHtml;
                if (isNearBottom) {
                    logConsole.scrollTop = logConsole.scrollHeight;
                }
            }
        }

        let isDisconnected = false;
        async function fetchStatus() {
            try {
                const res = await fetch('/api/status');
                if (!res.ok) throw new Error('HTTP ' + res.status);
                const data = await res.json();
                if (isDisconnected) {
                    isDisconnected = false;
                    showToast('Đã khôi phục kết nối!');
                }
                renderUI(data);
            } catch (e) {
                if (!isDisconnected) {
                    isDisconnected = true;
                    const statusDot = document.getElementById('statusDot');
                    const statusText = document.getElementById('statusText');
                    if (statusDot) statusDot.className = 'status-dot';
                    if (statusText) statusText.innerText = 'Mất kết nối - đang thử lại...';
                }
            }
        }

        let lastServerData = null;

        function renderUI(data) {
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');

            if (data.is_running) {
                statusDot.className = 'status-dot running';
                statusText.innerText = 'Đang chạy Auto...';
            } else {
                statusDot.className = 'status-dot';
                statusText.innerText = 'Sẵn sàng';
            }

            const selectTab = document.getElementById('selectTab');
            const newTabs = data.tabs || [];
            if (selectTab) {
                const curTabValues = Array.from(selectTab.options).map(o => o.value);
                const isTabListDiff = newTabs.length !== curTabValues.length || newTabs.some((t, i) => t !== curTabValues[i]);
                if (isTabListDiff) {
                    if (newTabs.length > 0) {
                        selectTab.innerHTML = '';
                        newTabs.forEach(t => {
                            const opt = document.createElement('option');
                            opt.value = t;
                            opt.innerText = t;
                            if (t === data.selected_tab) opt.selected = true;
                            selectTab.appendChild(opt);
                        });
                    } else {
                        selectTab.innerHTML = '<option value="">(Chưa phát hiện Tab LD nào mở)</option>';
                    }
                } else if (data.selected_tab && document.activeElement !== selectTab) {
                    selectTab.value = data.selected_tab;
                }
            }

            const fsTabTitle = document.getElementById('fsTabTitle');
            if (fsTabTitle) fsTabTitle.innerText = data.selected_tab ? `🖥️ ${data.selected_tab}` : '🖥️ Tab LDPlayer';

            const fsStatusDot = document.getElementById('fsStatusDot');
            if (fsStatusDot) {
                fsStatusDot.className = data.is_running ? 'status-dot running' : 'status-dot';
            }

            const carousel = document.getElementById('ldCarousel');
            if (carousel) {
                const curTabPills = Array.from(carousel.querySelectorAll('.ld-pill span:last-child')).map(s => s.innerText);
                const isCarouselDiff = newTabs.length !== curTabPills.length || newTabs.some((t, i) => t !== curTabPills[i]);
                if (isCarouselDiff) {
                    if (newTabs.length > 0) {
                        carousel.innerHTML = newTabs.map(t => {
                            const isActive = (t === data.selected_tab);
                            return `<div class="ld-pill ${isActive ? 'active' : ''}" onclick="onTabChanged('${t}')">
                                <span>📱</span><span>${t}</span>
                            </div>`;
                        }).join('');
                    } else {
                        carousel.innerHTML = '<div class="ld-pill"><span>⚠️</span><span>Chưa kết nối Tab LD</span></div>';
                    }
                } else {
                    carousel.querySelectorAll('.ld-pill').forEach((pill, idx) => {
                        const t = newTabs[idx];
                        if (t === data.selected_tab) {
                            pill.classList.add('active');
                        } else {
                            pill.classList.remove('active');
                        }
                    });
                }
            }

            const selectServer = document.getElementById('selectServer');
            if (selectServer.children.length <= 1) {
                selectServer.innerHTML = '';
                (data.servers || []).forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s;
                    opt.innerText = s;
                    if (s === data.server) opt.selected = true;
                    selectServer.appendChild(opt);
                });
            } else {
                selectServer.value = data.server;
            }

            const charCombos = ['combo_A_char', 'combo_B_don_char', 'combo_B_team_char', 'combo_D_team_char'];
            charCombos.forEach(cid => {
                const c = document.getElementById(cid);
                if (c && c.children.length === 0) {
                    (data.char_options || []).forEach(co => {
                        const opt = document.createElement('option');
                        opt.value = co; opt.innerText = co;
                        c.appendChild(opt);
                    });
                }
            });

            // Quân sư options (Chỉ tái tạo DOM khi danh sách thay đổi thực sự để tránh lag/giật dropdown)
            const comboQS = document.getElementById('combo_E_quan_su');
            if (comboQS) {
                const newOpts = data.quan_su_options || ['(Trống)'];
                const curOpts = Array.from(comboQS.options).map(o => o.value);
                const isDiff = newOpts.length !== curOpts.length || newOpts.some((v, i) => v !== curOpts[i]);
                if (isDiff) {
                    comboQS.innerHTML = '';
                    newOpts.forEach(qs => {
                        const opt = document.createElement('option');
                        opt.value = qs; opt.innerText = qs;
                        comboQS.appendChild(opt);
                    });
                }
                const nowQS = Date.now();
                if (!userLocks['combo_E_quan_su'] || nowQS >= userLocks['combo_E_quan_su']) {
                    if (document.activeElement !== comboQS) {
                        comboQS.value = data.selected_quan_su || '(Trống)';
                    }
                }
            }

            // Map options (Tái tạo DOM khi danh sách map thay đổi)
            const comboMap = document.getElementById('combo_E_map');
            if (comboMap) {
                const newMapOpts = data.map_options || ['(Chưa có map)'];
                const curMapOpts = Array.from(comboMap.options).map(o => o.value);
                const isMapDiff = newMapOpts.length !== curMapOpts.length || newMapOpts.some((v, i) => v !== curMapOpts[i]);
                if (isMapDiff) {
                    comboMap.innerHTML = '';
                    newMapOpts.forEach(m => {
                        const opt = document.createElement('option');
                        opt.value = m; opt.innerText = m;
                        comboMap.appendChild(opt);
                    });
                }
                const nowMap = Date.now();
                if (!userLocks['combo_E_map'] || nowMap >= userLocks['combo_E_map']) {
                    if (document.activeElement !== comboMap && data.combos && data.combos.E_map) {
                        comboMap.value = data.combos.E_map;
                    }
                }
            }

            lastServerData = data;
            renderTeamLists(data);

            const now = Date.now();

            for (const [k, v] of Object.entries(data.switches || {})) {
                const id = 'switch_' + k;
                if (userLocks[id] && now < userLocks[id]) continue;
                const el = document.getElementById(id);
                if (el) el.checked = !!v;
            }

            for (const [k, v] of Object.entries(data.checkboxes || {})) {
                const id = 'chk_' + k;
                if (userLocks[id] && now < userLocks[id]) continue;
                const el = document.getElementById(id);
                if (el) el.checked = !!v;
            }

            for (const [k, v] of Object.entries(data.combos || {})) {
                const id = 'combo_' + k;
                if (userLocks[id] && now < userLocks[id]) continue;
                const el = document.getElementById(id);
                if (el && document.activeElement !== el) el.value = v;
            }

            // Cập nhật nhãn hệ Boss Thế Giới (Card A)
            if (typeof updateBossElementBadge === 'function') {
                updateBossElementBadge(data.boss_elem ? data.boss_elem.name : null);
            }

            for (const [k, v] of Object.entries(data.inputs || {})) {
                const id = 'entry_' + k;
                if (userLocks[id] && now < userLocks[id]) continue;
                const el = document.getElementById(id);
                if (el && document.activeElement !== el) el.value = v;
            }

            applyDynamicUIRules();

            if (data.logs && data.logs.length > 0) {
                renderFilteredLogs(data.logs);
            }
        }

        const pendingAdds = new Set();
        const pendingRemoves = new Set();

        function renderTeamLists(data) {
            if (!data) return;
            const serverListB = data.list_E_B || [];

            // Auto reconcile confirmed pending actions
            pendingAdds.forEach(name => {
                if (serverListB.includes(name)) pendingAdds.delete(name);
            });
            pendingRemoves.forEach(name => {
                if (!serverListB.includes(name)) pendingRemoves.delete(name);
            });

            // Calculate effective List B
            let effectiveTeamB = [...serverListB];
            pendingAdds.forEach(name => {
                if (!effectiveTeamB.includes(name)) effectiveTeamB.push(name);
            });
            pendingRemoves.forEach(name => {
                effectiveTeamB = effectiveTeamB.filter(c => c !== name);
            });

            const listABox = document.getElementById('list_E_A_box');
            if (listABox) {
                const availA = (data.list_E_A || []).filter(name => !effectiveTeamB.includes(name));
                if (availA.length === 0) {
                    listABox.innerHTML = '<div style="color:#64748b; font-size:0.75rem; padding:6px; text-align:center;">(Đã thêm hết)</div>';
                } else {
                    listABox.innerHTML = availA.map(name => `
                        <div class="team-item" onclick="addMemberOptimistic('${name}')">
                            <span>${name}</span>
                            <span style="color:var(--accent); font-weight:700; font-size:0.95rem;">➔</span>
                        </div>
                    `).join('');
                }
            }

            const listBBox = document.getElementById('list_E_B_box');
            if (listBBox) {
                if (effectiveTeamB.length === 0) {
                    listBBox.innerHTML = '<div style="color:#64748b; font-size:0.75rem; padding:6px; text-align:center;">(Trống - bấm ➔ để thêm)</div>';
                } else {
                    listBBox.innerHTML = effectiveTeamB.map(name => `
                        <div class="team-item">
                            <span>${name}</span>
                            <button class="btn-del-member" onclick="event.stopPropagation(); removeMemberOptimistic('${name}')">✕</button>
                        </div>
                    `).join('');
                }
            }
        }

        function addMemberOptimistic(name) {
            pendingRemoves.delete(name);
            pendingAdds.add(name);
            renderTeamLists(lastServerData || {});
            sendAction('add_to_team', {char_name: name}, false);
            setTimeout(fetchStatus, 600);
        }

        function removeMemberOptimistic(name) {
            pendingAdds.delete(name);
            pendingRemoves.add(name);
            renderTeamLists(lastServerData || {});
            sendAction('remove_from_team', {char_name: name}, false);
            setTimeout(fetchStatus, 600);
        }

        const userLocks = {};

        function applyDynamicUIRules() {
            const chkD2 = document.getElementById('chk_D2');
            const chkD3 = document.getElementById('chk_D3');
            const chkD4 = document.getElementById('chk_D4');
            const chkBdoi = document.getElementById('chk_B_doi');
            const comboEQS = document.getElementById('combo_E_quan_su');
            const comboDChienDau = document.getElementById('combo_D_chien_dau');
            const comboDTang = document.getElementById('combo_D_tang');
            const listABox = document.getElementById('list_E_A_box');
            const listBBox = document.getElementById('list_E_B_box');

            // 1. Quy tắc 40 NPC (D3) và Nhị Kiều (D4) loại trừ nhau tức thì (giữ 2 ô luôn sáng để chuyển đổi 1-click)
            if (chkD3 && chkD4) {
                const labelD3 = chkD3.closest('.chk-label');
                const labelD4 = chkD4.closest('.chk-label');

                chkD3.disabled = false;
                chkD4.disabled = false;
                if (labelD3) { labelD3.style.opacity = '1'; labelD3.style.pointerEvents = 'auto'; }
                if (labelD4) { labelD4.style.opacity = '1'; labelD4.style.pointerEvents = 'auto'; }

                if (chkD3.checked) {
                    chkD4.checked = false;
                    if (comboDChienDau) { comboDChienDau.disabled = false; comboDChienDau.style.opacity = '1'; }
                    if (comboDTang) { comboDTang.disabled = true; comboDTang.style.opacity = '0.35'; }
                } else if (chkD4.checked) {
                    chkD3.checked = false;
                    if (comboDTang) { comboDTang.disabled = false; comboDTang.style.opacity = '1'; }
                    if (comboDChienDau) { comboDChienDau.disabled = true; comboDChienDau.style.opacity = '0.35'; }
                } else {
                    if (comboDChienDau) { comboDChienDau.disabled = true; comboDChienDau.style.opacity = '0.35'; }
                    if (comboDTang) { comboDTang.disabled = true; comboDTang.style.opacity = '0.35'; }
                }
            }

            // 2. Card E luôn mở sáng hoàn toàn 24/7 (kể cả Hàng 1 và Danh Sách A/B)
            const chkEMoiDoi = document.getElementById('chk_E_moi_doi');
            if (chkEMoiDoi) chkEMoiDoi.disabled = false;
            const comboEMap = document.getElementById('combo_E_map');
            if (comboEMap) comboEMap.disabled = false;
            const comboESoLuong = document.getElementById('combo_E_so_luong');
            if (comboESoLuong) comboESoLuong.disabled = false;
            if (comboEQS) { comboEQS.disabled = false; comboEQS.style.opacity = '1'; }
            if (listABox && listBBox) {
                listABox.style.opacity = '1';
                listABox.style.pointerEvents = 'auto';
                listBBox.style.opacity = '1';
                listBBox.style.pointerEvents = 'auto';
            }
        }

        async function sendAction(action, payload = {}, showToastMsg = true) {
            if (action === 'stop') {
                // Nhả tức thì ô HP / SP, Kết Giới, Linh Kính, Băng Tường, Truy Kích và các công tắc trên giao diện Web ngay khi chạm Stop
                const chkBuff = document.getElementById('chk_buff');
                if (chkBuff) chkBuff.checked = false;
                delete userLocks['chk_buff'];
                const chkPhongThu = document.getElementById('chk_phong_thu');
                if (chkPhongThu) chkPhongThu.checked = false;
                delete userLocks['chk_phong_thu'];
                const chkEMoiDoi = document.getElementById('chk_E_moi_doi');
                if (chkEMoiDoi) chkEMoiDoi.checked = false;
                delete userLocks['chk_E_moi_doi'];
                ['A', 'B', 'C', 'D'].forEach(k => {
                    const sw = document.getElementById('switch_' + k);
                    if (sw) sw.checked = false;
                    delete userLocks['switch_' + k];
                    const p = document.getElementById('chk_pause_' + k);
                    if (p) p.checked = false;
                    delete userLocks['chk_pause_' + k];
                });
            }
            try {
                const res = await fetch('/api/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action, ...payload})
                });
                const r = await res.json();
                if (showToastMsg && r.msg) showToast(r.msg);
            } catch (e) {
                if (showToastMsg) showToast('Lỗi kết nối');
            }
        }

        function onSwitchChanged(name, value) {
            userLocks['switch_' + name] = Date.now() + 2500;
            sendAction('set_switch', {name, value}, false);
            applyDynamicUIRules();
        }

        function onCheckboxChanged(name, value) {
            userLocks['chk_' + name] = Date.now() + 2500;
            if (name === 'D3' && value) {
                userLocks['chk_D4'] = Date.now() + 2500;
                const chkD4 = document.getElementById('chk_D4');
                if (chkD4) chkD4.checked = false;
            } else if (name === 'D4' && value) {
                userLocks['chk_D3'] = Date.now() + 2500;
                const chkD3 = document.getElementById('chk_D3');
                if (chkD3) chkD3.checked = false;
            } else if (['buff', 'phong_thu'].includes(name) && value) {
                const combatCbs = ['buff', 'phong_thu'];
                combatCbs.filter(k => k !== name).forEach(k => {
                    userLocks['chk_' + k] = Date.now() + 2500;
                    const el = document.getElementById('chk_' + k);
                    if (el) el.checked = false;
                });
            } else if (name === 'hen_gio' && !value) {
                ['A', 'B', 'C', 'D'].forEach(k => {
                    userLocks['switch_' + k] = Date.now() + 2500;
                    const sw = document.getElementById('switch_' + k);
                    if (sw) sw.checked = false;
                });
            }
            sendAction('set_checkbox', {name, value}, false);
            applyDynamicUIRules();
        }

        function onComboChanged(name, value) {
            userLocks['combo_' + name] = Date.now() + 2500;
            sendAction('set_combo', {name, value}, false);
        }

        function onTextChanged(name, value) {
            userLocks['entry_' + name] = Date.now() + 2500;
            sendAction('set_text', {name, value}, false);
        }

        async function triggerCaptureMap() {
            try {
                const res = await fetch('/api/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: 'capture_map'})
                });
                const data = await res.json();
                showToast(data.msg || "📸 Đã mở công cụ cắt ảnh Map trên màn hình Tool!");
            } catch(e) {
                showToast("❌ Không thể kích hoạt chụp map", true);
            }
        }

        async function triggerDeleteMap() {
            const comboMap = document.getElementById('combo_E_map');
            const mapName = comboMap ? comboMap.value : '';
            if (!mapName || mapName === '(Chưa có map)') {
                showToast("⚠️ Vui lòng chọn một map hợp lệ để xóa!", true);
                return;
            }
            if (!confirm(`Bạn có chắc chắn muốn xóa ảnh mẫu map "${mapName}" không?`)) {
                return;
            }
            try {
                const res = await fetch('/api/action', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: 'delete_map', map_name: mapName})
                });
                const data = await res.json();
                showToast(data.msg || `Đã xóa map ${mapName}`);
            } catch(e) {
                showToast("❌ Không thể xóa map", true);
            }
        }

        function onTabChanged(tab) {
            sendAction('set_tab', {tab}, true);
            setTimeout(fetchStatus, 150);
        }

        function onServerChanged(server) {
            sendAction('set_server', {server}, true);
            setTimeout(fetchStatus, 150);
        }

        function refreshTabs() {
            sendAction('refresh_tabs', {}, true);
            showToast('Đang quét lại tab...');
            setTimeout(fetchStatus, 600);
        }

        let currentStreamInterval = parseInt(localStorage.getItem('ts_stream_interval') || '500', 10);
        if (![500, 1000, 2000].includes(currentStreamInterval)) currentStreamInterval = 500;
        let isFetchingImg = false;
        let lastFetchStartTime = 0;
        let isFullscreenActive = false;
        let overlayHideTimer = null;

        function setStreamSpeed(intervalMs) {
            currentStreamInterval = intervalMs;
            try { localStorage.setItem('ts_stream_interval', intervalMs); } catch(e) {}
            
            document.querySelectorAll('.speed-btn').forEach(btn => {
                const speed = parseInt(btn.getAttribute('data-speed'), 10);
                if (speed === intervalMs) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });

            const speedLabel = intervalMs === 500 ? '0.5s (Mượt)' : (intervalMs === 1000 ? '1.0s (Chuẩn)' : '2.0s (Tiết kiệm)');
            const fsBadge = document.getElementById('fsStreamBadge');
            if (fsBadge) fsBadge.innerText = intervalMs === 500 ? '⚡ 0.5s' : (intervalMs === 1000 ? '⏱️ 1.0s' : '🌱 2.0s');
            
            const lbl = document.getElementById('streamSpeedText');
            if (lbl) lbl.innerText = 'Đang truyền (' + speedLabel + ')';

            const autoChk = document.getElementById('autoStream');
            if (autoChk && autoChk.checked) {
                if (streamTimer) clearInterval(streamTimer);
                streamTimer = setInterval(refreshScreenshot, currentStreamInterval);
            }
        }

        function refreshScreenshot() {
            const now = Date.now();
            // Nếu request cũ bị treo quá 3.5s (do điện thoại khóa màn hình hoặc ẩn tab), tự động giải phóng khóa
            if (isFetchingImg && (now - lastFetchStartTime) < 3500) return;
            
            const img = document.getElementById('screenImg');
            if (!img) return;
            isFetchingImg = true;
            lastFetchStartTime = now;

            const newImg = new Image();
            newImg.onload = function() {
                img.src = newImg.src;
                isFetchingImg = false;
            };
            newImg.onerror = function() {
                isFetchingImg = false;
            };
            newImg.src = '/api/screenshot?t=' + now;
        }

        // Tự động khôi phục luồng truyền ảnh ngay khi người dùng mở lại tab hoặc bật sáng màn hình điện thoại
        function resumeLiveStream() {
            isFetchingImg = false;
            lastFetchStartTime = 0;
            if (streamTimer) clearInterval(streamTimer);
            const autoChk = document.getElementById('autoStream');
            if (autoChk && autoChk.checked) {
                streamTimer = setInterval(refreshScreenshot, currentStreamInterval);
            }
            refreshScreenshot();
            fetchStatus();
        }

        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'visible') {
                resumeLiveStream();
            }
        });

        window.addEventListener('pageshow', resumeLiveStream);
        window.addEventListener('focus', resumeLiveStream);

        function toggleAutoStream(enable) {
            if (streamTimer) clearInterval(streamTimer);
            const dot = document.getElementById('streamDot');
            const lbl = document.getElementById('streamSpeedText');
            if (enable) {
                streamTimer = setInterval(refreshScreenshot, currentStreamInterval);
                if (dot) dot.classList.add('live');
                const speedLabel = currentStreamInterval === 500 ? '0.5s (Mượt)' : (currentStreamInterval === 1000 ? '1.0s' : '2.0s');
                if (lbl) lbl.innerText = 'Đang truyền (' + speedLabel + ')';
            } else {
                if (dot) dot.classList.remove('live');
                if (lbl) lbl.innerText = 'Đã tạm dừng truyền';
            }
        }

        function toggleFullscreen(enable) {
            const card = document.getElementById('screenCard');
            if (!card) return;
            if (enable === undefined) {
                enable = !card.classList.contains('fullscreen-active');
            }
            isFullscreenActive = enable;
            if (enable) {
                card.classList.add('fullscreen-active');
                document.body.style.overflow = 'hidden';
                if (document.documentElement.requestFullscreen) {
                    document.documentElement.requestFullscreen().catch(() => {});
                }
                resetOverlayHideTimer();
                showToast('⛶ Đã mở Toàn màn hình');
            } else {
                card.classList.remove('fullscreen-active');
                document.body.style.overflow = '';
                if (document.fullscreenElement && document.exitFullscreen) {
                    document.exitFullscreen().catch(() => {});
                }
                if (overlayHideTimer) clearTimeout(overlayHideTimer);
            }
        }

        function resetOverlayHideTimer() {
            const bar = document.getElementById('fsOverlayBar');
            if (!bar) return;
            bar.classList.remove('dimmed');
            if (overlayHideTimer) clearTimeout(overlayHideTimer);
            overlayHideTimer = setTimeout(() => {
                if (isFullscreenActive) bar.classList.add('dimmed');
            }, 4000);
        }

        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement && isFullscreenActive) {
                toggleFullscreen(false);
            }
        });

        function handleScreenTap(e) {
            if (e.target.closest && (e.target.closest('.fs-overlay-bar') || e.target.closest('button') || e.target.closest('.stream-ctrl-bar'))) {
                return;
            }

            const img = document.getElementById('screenImg');
            const box = document.getElementById('screenPreviewBox');
            if (!img || !box) return;

            if (isFullscreenActive) {
                resetOverlayHideTimer();
            }

            const rect = img.getBoundingClientRect();
            const nativeAR = 1280.0 / 720.0;
            const elemW = rect.width;
            const elemH = rect.height;
            if (elemW <= 0 || elemH <= 0) return;

            const elemAR = elemW / elemH;
            let renderW = elemW;
            let renderH = elemH;
            let offsetLeft = 0;
            let offsetTop = 0;

            if (elemAR > nativeAR) {
                // Pillarbox: dải đen hai bên trái - phải
                renderH = elemH;
                renderW = renderH * nativeAR;
                offsetLeft = (elemW - renderW) / 2;
            } else {
                // Letterbox: dải đen trên - dưới
                renderW = elemW;
                renderH = renderW / nativeAR;
                offsetTop = (elemH - renderH) / 2;
            }

            const clientX = e.clientX !== undefined ? e.clientX : (e.touches && e.touches[0] ? e.touches[0].clientX : null);
            const clientY = e.clientY !== undefined ? e.clientY : (e.touches && e.touches[0] ? e.touches[0].clientY : null);
            if (clientX === null || clientY === null) return;

            const clickX = (clientX - rect.left) - offsetLeft;
            const clickY = (clientY - rect.top) - offsetTop;

            if (clickX >= 0 && clickX <= renderW && clickY >= 0 && clickY <= renderH) {
                const realX = Math.round((clickX / renderW) * 1280);
                const realY = Math.round((clickY / renderH) * 720);

                sendAction('tap', { x: realX, y: realY }, false);

                const boxRect = box.getBoundingClientRect();
                const ripX = clientX - boxRect.left;
                const ripY = clientY - boxRect.top;

                const ripple = document.createElement('div');
                ripple.className = 'touch-ripple';
                ripple.style.left = (ripX - 16) + 'px';
                ripple.style.top = (ripY - 16) + 'px';
                box.appendChild(ripple);

                const coord = document.createElement('div');
                coord.className = 'touch-coord';
                coord.innerText = `${realX}, ${realY}`;
                coord.style.left = ripX + 'px';
                coord.style.top = ripY + 'px';
                box.appendChild(coord);

                setTimeout(() => {
                    ripple.remove();
                    coord.remove();
                }, 750);
            }
        }

        // Khởi động
        fetchStatus();
        setInterval(fetchStatus, 3000);
        setStreamSpeed(currentStreamInterval);

        function updateBossElementBadge(elemName) {
            const badge = document.getElementById('boss_elem_badge');
            if (!badge) return;
            if (!elemName) {
                const d = new Date().getDay();
                const m = {1:'Địa', 2:'Thủy', 3:'Hỏa', 4:'Phong', 5:'Hỏa', 6:'Thủy', 0:'Phong'};
                elemName = m[d] || 'Địa';
            }
            badge.textContent = elemName;
            const clsMap = {'Địa': 'elem-dia', 'Thủy': 'elem-thuy', 'Hỏa': 'elem-hoa', 'Phong': 'elem-phong'};
            badge.className = `boss-elem-badge ${clsMap[elemName] || 'elem-dia'}`;
        }

        function updateRealtimeClock() {
            const badge = document.getElementById('lbl_realtime_clock');
            if (!badge) return;
            const now = new Date();
            const pad = (n) => String(n).padStart(2, '0');
            badge.textContent = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
        }
        setInterval(updateRealtimeClock, 1000);

        document.addEventListener('DOMContentLoaded', () => {
            const box = document.getElementById('screenPreviewBox');
            if (box) {
                box.addEventListener('click', handleScreenTap);
            }
            updateBossElementBadge();
            updateRealtimeClock();
        });
    </script>
</body>
</html>
"""


class SilentThreadingHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        ex = sys.exc_info()[1]
        if isinstance(ex, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)


class ToolWebRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        pass

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            self.close_connection = True

    def handle(self):
        try:
            super().handle()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def finish(self):
        try:
            super().finish()
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_GET(self):
        app = getattr(self.server, "app", None)
        if not app:
            self.send_error(500, "App not ready")
            return

        parsed = self.path.split('?')[0]

        if parsed == "/" or parsed == "/index.html":
            body = HTML_PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            return

        elif parsed == "/api/status":
            tabs = []
            if hasattr(app, 'combo_ld_tabs'):
                tabs = list(app.combo_ld_tabs.cget("values"))
                tabs = [t for t in tabs if t not in ["Đang quét tab...", "Lỗi quét dữ liệu", "Không tìm thấy tab LD nào"]]

            selected_tab, _ = app._get_selected_ld_info() if hasattr(app, '_get_selected_ld_info') else (None, None)

            switches = {
                "A": app.var_switch_A.get() if hasattr(app, 'var_switch_A') else False,
                "B": app.var_switch_B.get() if hasattr(app, 'var_switch_B') else False,
                "C": app.var_switch_C.get() if hasattr(app, 'var_switch_C') else False,
                "D": app.var_switch_D.get() if hasattr(app, 'var_switch_D') else False
            }

            checkboxes = {
                "A1": app.var_A1.get() if hasattr(app, 'var_A1') else False,
                "B_don": app.var_B_don.get() if hasattr(app, 'var_B_don') else False,
                "B_doi": app.var_B_doi.get() if hasattr(app, 'var_B_doi') else False,
                "B1": app.var_B1.get() if hasattr(app, 'var_B1') else False,
                "B2": app.var_B2.get() if hasattr(app, 'var_B2') else False,
                "B3": app.var_B3.get() if hasattr(app, 'var_B3') else False,
                "B4": app.var_B4.get() if hasattr(app, 'var_B4') else False,
                "B5": app.var_B5.get() if hasattr(app, 'var_B5') else False,
                "C1": app.var_C1.get() if hasattr(app, 'var_C1') else False,
                "C2": app.var_C2.get() if hasattr(app, 'var_C2') else False,
                "C3": app.var_C3.get() if hasattr(app, 'var_C3') else False,
                "D2": app.var_D2.get() if hasattr(app, 'var_D2') else False,
                "D3": app.var_D3.get() if hasattr(app, 'var_D3') else False,
                "D4": app.var_D4.get() if hasattr(app, 'var_D4') else False,
                "E_moi_doi": app.var_E_moi_doi.get() if hasattr(app, 'var_E_moi_doi') else False,
                "E_quan_su": app.var_E_quan_su.get() if hasattr(app, 'var_E_quan_su') else False,
                "pause_D": app.var_pause_D.get() if hasattr(app, 'var_pause_D') else False,
                "buff": app.var_buff.get() if hasattr(app, 'var_buff') else False,
                "phong_thu": app.var_phong_thu.get() if hasattr(app, 'var_phong_thu') else False,
                "ket_gioi": app.var_phong_thu.get() if hasattr(app, 'var_phong_thu') else False,
                "linh_kinh": app.var_phong_thu.get() if hasattr(app, 'var_phong_thu') else False,
                "bang_tuong": app.var_phong_thu.get() if hasattr(app, 'var_phong_thu') else False,
                "truy_kich": app.var_truy_kich.get() if hasattr(app, 'var_truy_kich') else False,
                "nhan_thu": app.var_nhan_thu.get() if hasattr(app, 'var_nhan_thu') else False,
                "hen_gio": app.var_hen_gio.get() if hasattr(app, 'var_hen_gio') else False,
                "enable_notify": app.var_enable_notify.get() if hasattr(app, 'var_enable_notify') else True,
                "enable_telegram": app.var_enable_telegram.get() if hasattr(app, 'var_enable_telegram') else True
            }

            combos = {
                "A_char": app.combo_A_char.get() if hasattr(app, 'combo_A_char') else "Xuất Chiến",
                "B_don_char": app.combo_B_don_char.get() if hasattr(app, 'combo_B_don_char') else "Xuất Chiến",
                "B_team_char": app.combo_B_team_char.get() if hasattr(app, 'combo_B_team_char') else "Xuất Chiến",
                "D_team_char": app.combo_D_team_char.get() if hasattr(app, 'combo_D_team_char') else "Xuất Chiến",
                "D_chien_dau": app.combo_D_chien_dau.get() if hasattr(app, 'combo_D_chien_dau') else "Auto",
                "D_tang": app.combo_D_tang.get() if hasattr(app, 'combo_D_tang') else "Auto",
                "E_map": app.combo_E_map.get() if hasattr(app, 'combo_E_map') else "Map 1",
                "E_so_luong": app.combo_E_so_luong.get() if hasattr(app, 'combo_E_so_luong') else "4",
                "E_quan_su": app.combo_E_quan_su.get() if hasattr(app, 'combo_E_quan_su') else "(Trống)",
                "buff": app.combo_buff.get() if hasattr(app, 'combo_buff') else "Buff HP",
                "phong_thu_skill": app.combo_phong_thu_skill.get() if hasattr(app, 'combo_phong_thu_skill') else "Kết Giới",
                "phong_thu_target": app.combo_phong_thu_target.get() if hasattr(app, 'combo_phong_thu_target') else "Chart",
                "ket_gioi": app.combo_phong_thu_target.get() if hasattr(app, 'combo_phong_thu_target') else "Chart",
                "linh_kinh": app.combo_phong_thu_target.get() if hasattr(app, 'combo_phong_thu_target') else "Chart",
                "bang_tuong": app.combo_phong_thu_target.get() if hasattr(app, 'combo_phong_thu_target') else "Chart",
                "truy_kich_quai": app.combo_truy_kich_quai.get() if hasattr(app, 'combo_truy_kich_quai') else "(Chưa có quái)",
                "nhan_thu_time": app.combo_nhan_thu_time.get() if hasattr(app, 'combo_nhan_thu_time') else "Tất Cả",
                "hen_gio_time": app.var_hen_gio_time.get() if hasattr(app, 'var_hen_gio_time') else "05:00"
            }

            inputs = {
                "hen_gio_time": app.var_hen_gio_time.get() if hasattr(app, 'var_hen_gio_time') else "05:00"
            }

            is_running = bool(
                getattr(app, '_card_AB_coordinator_running', False)
                or (getattr(app, '_thread_card_E_standalone', None) is not None and app._thread_card_E_standalone.is_alive())
                or (getattr(app, '_thread_buff', None) is not None and app._thread_buff.is_alive())
                or (getattr(app, '_thread_phong_thu', None) is not None and app._thread_phong_thu.is_alive())
                or (getattr(app, '_thread_truy_kich', None) is not None and app._thread_truy_kich.is_alive())
                or (hasattr(app, 'var_switch_A') and app.var_switch_A.get())
                or (hasattr(app, 'var_switch_B') and app.var_switch_B.get())
                or (hasattr(app, 'var_switch_C') and app.var_switch_C.get())
                or (hasattr(app, 'var_switch_D') and app.var_switch_D.get())
                or (hasattr(app, 'var_buff') and app.var_buff.get())
                or (hasattr(app, 'var_phong_thu') and app.var_phong_thu.get())
                or (hasattr(app, 'var_truy_kich') and app.var_truy_kich.get())
            )

            list_E_A = app._get_nhanvat_options() if hasattr(app, '_get_nhanvat_options') else []
            list_E_B = list(getattr(app, 'list_E_B', []))
            quan_su_options = app._get_quan_su_options() if hasattr(app, '_get_quan_su_options') else ["(Trống)"]
            selected_quan_su = app.combo_E_quan_su.get() if hasattr(app, 'combo_E_quan_su') else "(Trống)"
            map_options = app._get_map_options() if hasattr(app, '_get_map_options') else ["(Chưa có map)"]
            quai_options = app._get_quai_options() if hasattr(app, '_get_quai_options') else ["(Chưa có quái)"]

            day_str, elem_name, elem_color = app._get_boss_element_info() if hasattr(app, '_get_boss_element_info') else ("--", "Địa", "#FDE047")

            data = {
                "is_running": is_running,
                "selected_tab": selected_tab or (tabs[0] if tabs else ""),
                "tabs": tabs,
                "server": app.combo_server.get() if hasattr(app, 'combo_server') else "Điêu Thuyền",
                "servers": app._get_server_options() if hasattr(app, '_get_server_options') else ["Điêu Thuyền"],
                "char_options": app._get_character_options() if hasattr(app, '_get_character_options') else ["Xuất Chiến"],
                "boss_elem": {
                    "day": day_str,
                    "name": elem_name,
                    "color": elem_color
                },
                "list_E_A": list_E_A,
                "list_E_B": list_E_B,
                "quan_su_options": quan_su_options,
                "selected_quan_su": selected_quan_su,
                "map_options": map_options,
                "quai_options": quai_options,
                "switches": switches,
                "checkboxes": checkboxes,
                "combos": combos,
                "inputs": inputs,
                "logs": getattr(app, 'recent_logs', [])[-150:],
                "local_ip": getattr(app, 'web_ip', get_local_ip()),
                "port": getattr(app, 'web_port', 8080)
            }
            body = json.dumps(data, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
            return

        elif parsed == "/api/screenshot":
            img_bytes = get_screenshot_bytes(app)
            try:
                if img_bytes:
                    self.send_response(200)
                    self.send_header("Content-Type", "image/jpeg")
                    self.send_header("Content-Length", str(len(img_bytes)))
                    self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    self.wfile.write(img_bytes)
                else:
                    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="400" height="225" viewBox="0 0 400 225">
                        <rect width="100%" height="100%" fill="#182238"/>
                        <text x="50%" y="50%" fill="#64748b" font-family="sans-serif" font-size="14" text-anchor="middle" dominant-baseline="middle">Chưa thể chụp màn hình (Tab chưa bật hoặc ADB bận)</text>
                    </svg>""".encode('utf-8')
                    self.send_response(200)
                    self.send_header("Content-Type", "image/svg+xml")
                    self.send_header("Content-Length", str(len(svg)))
                    self.send_header("Connection", "close")
                    self.end_headers()
                    self.wfile.write(svg)
            except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                pass
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        app = getattr(self.server, "app", None)
        if not app:
            self.send_error(500, "App not ready")
            return

        if self.path == "/api/action":
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            try:
                req = json.loads(body.decode('utf-8'))
            except Exception:
                req = {}

            action = req.get("action")
            msg = "Đã thực thi"

            if action == "run":
                app.after(0, app.xu_ly_nut_chay)
                msg = "▶️ Bắt đầu Run Tool!"

            elif action == "stop":
                app.after(0, app.dung_tat_ca_hoat_dong)
                msg = "🛑 Đã Stop khẩn cấp!"

            elif action == "launch_game":
                app.after(0, app.xu_ly_ts_origin)
                msg = "🎮 Đang mở TS Origin..."

            elif action == "exit_game":
                app.after(0, app.xu_ly_exit_game)
                msg = "🚪 Đang đóng game về màn hình chính LDPlayer..."

            elif action == "nhan_thu":
                tab_name, tab_index = app._get_selected_ld_info() if hasattr(app, '_get_selected_ld_info') else (None, None)
                if tab_index is None:
                    tab_index = "0"
                dnconsole_path = os.path.join(app.ld_path, "ldconsole.exe")
                if not os.path.exists(dnconsole_path):
                    dnconsole_path = os.path.join(app.ld_path, "dnconsole.exe")
                threading.Thread(target=app._execute_nhan_thu, args=(dnconsole_path, str(tab_index)), daemon=True).start()
                msg = "📬 Đang thực thi Nhận Thư..."

            elif action == "show_window":
                if hasattr(app, '_restore_window_ui'):
                    app.after(0, app._restore_window_ui)
                elif hasattr(app, '_show_window_from_tray'):
                    app.after(0, app._show_window_from_tray)
                msg = "📖 Đã mở lại giao diện Tool."

            elif action == "refresh_tabs":
                app.after(0, app.refresh_ld_tabs_async)
                msg = "🔄 Đang quét lại Tab..."

            elif action == "set_tab":
                tab = req.get("tab")
                if tab and hasattr(app, 'combo_ld_tabs'):
                    def _set_t():
                        app.combo_ld_tabs.set(tab)
                        app._on_ld_tab_selected(tab)
                    app.after(0, _set_t)
                    msg = f"Đã chọn tab: {tab}"

            elif action == "set_server":
                server = req.get("server")
                if server and hasattr(app, 'combo_server'):
                    def _set_s():
                        app.combo_server.set(server)
                        if hasattr(app, 'save_config'):
                            app.save_config()
                    app.after(0, _set_s)
                    msg = f"Đã chọn server: {server}"

            elif action == "tap":
                x = req.get("x")
                y = req.get("y")
                tab, idx = app._get_selected_ld_info() if hasattr(app, '_get_selected_ld_info') else (None, None)
                if idx is not None and x is not None and y is not None:
                    dnconsole_path = os.path.join(app.ld_path, "ldconsole.exe")
                    if not os.path.exists(dnconsole_path):
                        dnconsole_path = os.path.join(app.ld_path, "dnconsole.exe")
                    app._exec_cmd([dnconsole_path, "adb", "--index", str(idx), "--command", f"shell input tap {int(x)} {int(y)}"])
                    msg = f"👆 Đã chạm ({int(x)}, {int(y)})"
                else:
                    msg = "Vui lòng chọn tab LDPlayer trước"

            elif action == "set_switch":
                s_name = req.get("name")
                s_val = bool(req.get("value"))
                switch_var_name = f"var_switch_{s_name}"
                switch_cb_name = f"_on_switch_{s_name}_toggled"

                if hasattr(app, switch_var_name):
                    def _toggle_sw():
                        getattr(app, switch_var_name).set(s_val)
                        if hasattr(app, switch_cb_name):
                            getattr(app, switch_cb_name)()
                    app.after(0, _toggle_sw)
                    msg = f"Công tắc {s_name}: {'BẬT' if s_val else 'TẮT'}"

            elif action == "set_checkbox":
                cb_name = req.get("name")
                cb_val = bool(req.get("value"))
                if cb_name in ["buff", "var_buff"]:
                    var_name = "var_buff"
                elif cb_name in ["phong_thu", "var_phong_thu", "ket_gioi", "var_ket_gioi", "linh_kinh", "var_linh_kinh", "bang_tuong", "var_bang_tuong"]:
                    var_name = "var_phong_thu"
                elif cb_name in ["truy_kich", "var_truy_kich"]:
                    var_name = "var_truy_kich"
                elif cb_name.startswith("var_"):
                    var_name = cb_name
                else:
                    var_name = f"var_{cb_name}"

                if hasattr(app, var_name):
                    def _toggle_cb():
                        getattr(app, var_name).set(cb_val)
                        if cb_name in ["D2", "B_doi"] and hasattr(app, '_update_card_E_visibility'):
                            app._update_card_E_visibility()
                            app._on_checkbox_toggled()
                        elif cb_name in ["D3", "var_D3"] and hasattr(app, '_on_D3_toggled'):
                            app._on_D3_toggled()
                        elif cb_name in ["D4", "var_D4"] and hasattr(app, '_on_D4_toggled'):
                            app._on_D4_toggled()
                        elif cb_name in ["pause_D", "var_pause_D"] and hasattr(app, '_on_pause_D_toggled'):
                            app._on_pause_D_toggled()
                        elif cb_name in ["E_moi_doi", "var_E_moi_doi"]:
                            if hasattr(app, '_on_card_E_standalone_toggled'):
                                app._on_card_E_standalone_toggled()
                            else:
                                app._on_checkbox_toggled()
                        elif cb_name in ["E_quan_su", "var_E_quan_su"] and hasattr(app, '_on_checkbox_toggled'):
                            app._on_checkbox_toggled()
                        elif cb_name in ["buff", "var_buff"]:
                            if hasattr(app, '_on_hp_sp_toggled'):
                                app._on_hp_sp_toggled()
                            else:
                                app._on_checkbox_toggled()
                        elif cb_name in ["phong_thu", "var_phong_thu", "ket_gioi", "var_ket_gioi", "linh_kinh", "var_linh_kinh", "bang_tuong", "var_bang_tuong"]:
                            if hasattr(app, '_on_phong_thu_toggled'):
                                app._on_phong_thu_toggled()
                            else:
                                app._on_checkbox_toggled()
                        elif cb_name in ["truy_kich", "var_truy_kich"]:
                            if hasattr(app, '_on_truy_kich_toggled'):
                                app._on_truy_kich_toggled()
                            else:
                                app._on_checkbox_toggled()
                        elif cb_name in ["nhan_thu", "var_nhan_thu"]:
                            if hasattr(app, '_on_nhan_thu_toggled'):
                                app._on_nhan_thu_toggled()
                            else:
                                app.save_config()
                        elif cb_name in ["hen_gio", "var_hen_gio"]:
                            if hasattr(app, '_on_hen_gio_toggled'):
                                app._on_hen_gio_toggled()
                            else:
                                app.save_config()
                        elif cb_name in ["enable_telegram", "var_enable_telegram"]:
                            if hasattr(app, 'save_config'):
                                app.save_config()
                        else:
                            app._on_checkbox_toggled()
                    app.after(0, _toggle_cb)
                    msg = f"Ô {cb_name}: {'Tích' if cb_val else 'Bỏ'}"

            elif action == "set_combo":
                c_name = req.get("name")
                c_val = req.get("value")
                if c_name in ["buff", "combo_buff"]:
                    combo_widget_name = "combo_buff"
                elif c_name in ["phong_thu_skill", "combo_phong_thu_skill"]:
                    combo_widget_name = "combo_phong_thu_skill"
                elif c_name in ["phong_thu_target", "combo_phong_thu_target", "ket_gioi", "combo_ket_gioi", "linh_kinh", "combo_linh_kinh", "bang_tuong", "combo_bang_tuong"]:
                    combo_widget_name = "combo_phong_thu_target"
                elif c_name in ["truy_kich_quai", "combo_truy_kich_quai"]:
                    combo_widget_name = "combo_truy_kich_quai"
                elif c_name in ["nhan_thu_time", "combo_nhan_thu_time"]:
                    combo_widget_name = "combo_nhan_thu_time"
                elif c_name in ["hen_gio_time", "combo_hen_gio_time"]:
                    combo_widget_name = "combo_hen_gio_time"
                elif c_name.startswith("combo_"):
                    combo_widget_name = c_name
                else:
                    combo_widget_name = f"combo_{c_name}"

                if hasattr(app, combo_widget_name):
                    def _set_cmb():
                        getattr(app, combo_widget_name).set(c_val)
                        if c_name in ["E_so_luong", "E_map", "E_quan_su", "combo_E_so_luong", "combo_E_map", "combo_E_quan_su"] and hasattr(app, '_on_card_E_standalone_toggled'):
                            app._on_card_E_standalone_toggled()
                        elif c_name in ["nhan_thu_time", "combo_nhan_thu_time"]:
                            if hasattr(app, '_on_nhan_thu_toggled'):
                                app._on_nhan_thu_toggled()
                            else:
                                app.save_config()
                        elif c_name in ["hen_gio_time", "combo_hen_gio_time"]:
                            if hasattr(app, 'var_hen_gio_time'):
                                app.var_hen_gio_time.set(c_val)
                            if hasattr(app, '_on_hen_gio_time_changed'):
                                app._on_hen_gio_time_changed()
                            else:
                                app.save_config()
                        else:
                            app._on_checkbox_toggled()
                    app.after(0, _set_cmb)
                    msg = f"Đã đổi {c_name} sang {c_val}"

            elif action == "set_text":
                t_name = req.get("name")
                t_val = req.get("value")
                if t_name in ["hen_gio_time", "var_hen_gio_time", "entry_hen_gio_time"]:
                    def _set_txt():
                        if hasattr(app, 'var_hen_gio_time'):
                            app.var_hen_gio_time.set(t_val)
                        if hasattr(app, '_on_hen_gio_time_changed'):
                            app._on_hen_gio_time_changed()
                        else:
                            app.save_config()
                    app.after(0, _set_txt)
                    msg = f"Đã đặt {t_name} = {t_val}"
                else:
                    msg = f"Đã cập nhật {t_name}"

            elif action == "capture_map":
                if hasattr(app, '_open_map_snipping_tool'):
                    app.after(0, app._open_map_snipping_tool)
                    msg = "📸 Đã mở công cụ cắt ảnh Map trên màn hình máy tính!"
                else:
                    msg = "⚠️ Không tìm thấy công cụ chụp map"

            elif action == "delete_map":
                map_name = req.get("map_name")
                if map_name and hasattr(app, '_delete_map_by_name'):
                    def _del():
                        app._delete_map_by_name(map_name)
                    app.after(0, _del)
                    msg = f"🗑️ Đã xóa ảnh mẫu map: {map_name}"
                else:
                    msg = "⚠️ Không thể xóa map"

            elif action == "capture_quai":
                if hasattr(app, '_open_quai_snipping_tool'):
                    app.after(0, app._open_quai_snipping_tool)
                    msg = "📸 Đã mở công cụ cắt ảnh Quái trên màn hình máy tính!"
                else:
                    msg = "⚠️ Không tìm thấy công cụ chụp quái"

            elif action == "delete_quai":
                quai_name = req.get("quai_name")
                if quai_name and hasattr(app, '_delete_quai_by_name'):
                    def _del_q():
                        app._delete_quai_by_name(quai_name)
                    app.after(0, _del_q)
                    msg = f"🗑️ Đã xóa ảnh mẫu quái: {quai_name}"
                else:
                    msg = "⚠️ Không thể xóa mẫu quái"

            elif action == "add_to_team":
                char_name = req.get("char_name")
                if char_name and hasattr(app, '_add_A_to_B_E'):
                    def _add():
                        app.selected_E_list_A_char = char_name
                        app._add_A_to_B_E()
                    app.after(0, _add)
                    msg = f"➕ Đã thêm {char_name} vào Tổ Đội"

            elif action == "remove_from_team":
                char_name = req.get("char_name")
                if char_name and hasattr(app, '_remove_B_item_E'):
                    def _rem():
                        app._remove_B_item_E(char_name)
                    app.after(0, _rem)
                    msg = f"➖ Đã xóa {char_name} khỏi Tổ Đội"

            res_body = json.dumps({"success": True, "msg": msg}, ensure_ascii=False).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(res_body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(res_body)
            return

        self.send_error(404, "Not Found")


def start_web_server(app, port=8080):
    """Khởi động Web Server ngầm trên port 8080"""
    local_ip = get_local_ip()
    app.web_ip = local_ip
    app.web_port = port

    for attempt_port in [port, port + 1, port + 2, 5000, 8888]:
        try:
            server = SilentThreadingHTTPServer(('0.0.0.0', attempt_port), ToolWebRequestHandler)
            server.app = app
            app.web_port = attempt_port
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            local_url = f"http://{local_ip}:{attempt_port}"
            app.log_info(f"🌐 [WEB SERVER] Đang chạy tại: {local_url} (Mở link này trên điện thoại)")
            if hasattr(app, '_update_web_url_ui'):
                app.after(0, app._update_web_url_ui, local_url, False)
            return server
        except OSError:
            continue
        except Exception as e:
            app.log_error(f"Không thể khởi động Web Server: {e}")
            break

    return None


def stop_active_tunnel(app):
    """Dừng tiến trình tunnel cũ đang chạy nếu có"""
    setattr(app, 'stop_tunnel_requested', True)
    proc = getattr(app, 'cloudflared_proc', None)
    if proc:
        try:
            proc.terminate()
            time.sleep(0.3)
            if proc.poll() is None:
                proc.kill()
        except Exception:
            pass
        app.cloudflared_proc = None

    # Quét dọn triệt để các tiến trình ngrok và cloudflared mồ côi (tránh xung đột session đơn lẻ của Ngrok)
    try:
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creation_flags)
        subprocess.run(["taskkill", "/F", "/IM", "cloudflared.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creation_flags)
    except Exception:
        pass


def find_or_download_cloudflared(app):
    """Tìm hoặc tự động tải cloudflared.exe từ Cloudflare nếu chưa có"""
    app_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)

    local_bin = os.path.join(app_dir, "cloudflared.exe")
    if os.path.exists(local_bin) and os.path.getsize(local_bin) > 10000000:
        return local_bin

    sys_bin = shutil.which("cloudflared")
    if sys_bin:
        return sys_bin

    app.log_info("📥 Đang tự động tải cloudflared.exe chính chủ Cloudflare (khoảng 50MB, chỉ tải 1 lần)...")
    download_url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    temp_bin = local_bin + ".download"

    # 1. Thử tải bằng Python urllib (Native & an toàn nhất)
    try:
        req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as response, open(temp_bin, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        if os.path.exists(temp_bin) and os.path.getsize(temp_bin) > 10000000:
            if os.path.exists(local_bin):
                try: os.remove(local_bin)
                except Exception: pass
            os.rename(temp_bin, local_bin)
            app.log_info("✅ Đã tải xong cloudflared.exe thành công!")
            return local_bin
    except Exception as e:
        app.log_warning(f"Tải bằng urllib chưa thành công: {e}. Đang thử bằng Curl/PowerShell...")
        if os.path.exists(temp_bin):
            try: os.remove(temp_bin)
            except Exception: pass

    # 2. Thử tải bằng Curl nếu có
    try:
        curl_bin = shutil.which("curl")
        if curl_bin:
            creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.run([curl_bin, "-L", "-o", temp_bin, download_url], timeout=90, creationflags=creation_flags)
            if os.path.exists(temp_bin) and os.path.getsize(temp_bin) > 10000000:
                if os.path.exists(local_bin):
                    try: os.remove(local_bin)
                    except Exception: pass
                os.rename(temp_bin, local_bin)
                app.log_info("✅ Đã tải xong cloudflared.exe thành công!")
                return local_bin
    except Exception:
        if os.path.exists(temp_bin):
            try: os.remove(temp_bin)
            except Exception: pass

    # 3. Thử tải bằng PowerShell
    try:
        ps_cmd = f"[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('{download_url}', '{temp_bin}')"
        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], timeout=90, creationflags=creation_flags)
        if os.path.exists(temp_bin) and os.path.getsize(temp_bin) > 10000000:
            if os.path.exists(local_bin):
                try: os.remove(local_bin)
                except Exception: pass
            os.rename(temp_bin, local_bin)
            app.log_info("✅ Đã tải xong cloudflared.exe thành công!")
            return local_bin
    except Exception:
        if os.path.exists(temp_bin):
            try: os.remove(temp_bin)
            except Exception: pass

    app.log_error("Không thể tải cloudflared.exe tự động. Sẽ chuyển sang chế độ SSH Tunnel dự phòng.")
    return None


def find_or_download_ngrok(app):
    """Tìm hoặc tự động tải ngrok.exe nếu chưa có"""
    app_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    if getattr(sys, 'frozen', False):
        app_dir = os.path.dirname(sys.executable)

    local_bin = os.path.join(app_dir, "ngrok.exe")
    if os.path.exists(local_bin) and os.path.getsize(local_bin) > 5000000:
        return local_bin

    sys_bin = shutil.which("ngrok")
    if sys_bin:
        return sys_bin

    app.log_info("📥 Đang tự động tải ngrok.exe từ server chính chủ...")
    download_url = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"
    temp_zip = os.path.join(tempfile.gettempdir(), "ngrok.zip")

    try:
        req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=60) as response, open(temp_zip, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
        if os.path.exists(temp_zip):
            import zipfile
            with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                zip_ref.extract("ngrok.exe", app_dir)
            try: os.remove(temp_zip)
            except Exception: pass
            if os.path.exists(local_bin):
                app.log_info("✅ Đã tải xong ngrok.exe thành công!")
                return local_bin
    except Exception as e:
        if hasattr(app, 'log_warning'):
            app.log_warning(f"Lỗi tải ngrok.exe: {e}")
    return None


def get_app_dir():
    """Lấy đường dẫn thư mục thực tế chứa file .exe (hoặc script main.py)"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def start_cloudflare_tunnel(app):
    """Khởi động đường truyền Online HTTPS bảo mật truy cập từ xa (4G/Internet) - Tự động hỗ trợ Ngrok Static Domain hoặc Cloudflare"""
    def _tunnel_worker():
        stop_active_tunnel(app)
        setattr(app, 'stop_tunnel_requested', False)
        port = getattr(app, 'web_port', 8080)
        app.log_info(f"🌐 [4G / ONLINE] Đang khởi tạo đường truyền HTTPS qua cổng {port}...")

        creation_flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

        # Check configuration in config.json
        cf_token = ""
        cf_domain = ""
        ngrok_token = ""
        ngrok_domain = ""
        try:
            cfg_path = os.path.join(get_app_dir(), "config.json")
            if os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg_data = json.load(f)
                    cf_token = cfg_data.get("cloudflare_token", "").strip()
                    cf_domain = cfg_data.get("fixed_domain", "").strip()
                    ngrok_token = cfg_data.get("ngrok_authtoken", "").strip()
                    if not cf_domain and cfg_data.get("ngrok_domain"):
                        ngrok_domain = cfg_data.get("ngrok_domain", "").strip()
                    elif cf_domain and "ngrok" in cf_domain.lower():
                        ngrok_domain = cf_domain
        except Exception:
            pass

        # 0. ƯU TIÊN NGROK STATIC DOMAIN NẾU CÓ NGROK TOKEN & DOMAIN TRONG CONFIG.JSON
        if ngrok_token and (ngrok_domain or cf_domain):
            domain_target = ngrok_domain or cf_domain
            ngrok_bin = find_or_download_ngrok(app)
            if ngrok_bin and os.path.exists(ngrok_bin):
                try:
                    # Dọn dẹp mọi tiến trình ngrok cũ còn kẹt trước khi tạo session mới
                    try:
                        subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creation_flags)
                        time.sleep(0.3)
                    except Exception:
                        pass

                    subprocess.run([ngrok_bin, "config", "add-authtoken", ngrok_token], creationflags=creation_flags)
                    subprocess.run([ngrok_bin, "authtoken", ngrok_token], creationflags=creation_flags)

                    clean_dom = domain_target.replace("https://", "").replace("http://", "").strip("/")
                    found_url = f"https://{clean_dom}"
                    app.public_web_url = found_url
                    if hasattr(app, '_update_web_url_ui'):
                        app.after(0, app._update_web_url_ui, found_url, True)

                    cmd_options = [
                        [ngrok_bin, "http", f"--domain={clean_dom}", str(port), "--log=stdout", "--log-level=warn"],
                        [ngrok_bin, "http", str(port), "--domain", clean_dom, "--log=stdout", "--log-level=warn"],
                        [ngrok_bin, "http", str(port), "--url", clean_dom, "--log=stdout", "--log-level=warn"],
                        [ngrok_bin, "http", f"--domain={clean_dom}", str(port)]
                    ]

                    ngrok_success = False
                    retry_count = 0

                    def _start_ngrok_proc(ngrok_cmd):
                        p = subprocess.Popen(
                            ngrok_cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            encoding='utf-8',
                            errors='ignore',
                            creationflags=creation_flags
                        )
                        # Luồng đọc output liên tục (Draining Thread) để triệt tiêu lỗi đầy OS Pipe Buffer làm treo ngrok
                        def _drain_output(proc_to_drain):
                            try:
                                for line in iter(proc_to_drain.stdout.readline, ''):
                                    if not line or getattr(app, 'stop_tunnel_requested', False):
                                        break
                                    line_clean = line.strip()
                                    if any(k in line_clean for k in ["ERR_NGROK", "critical", "error", "failed"]):
                                        app.log_warning(f"⚠️ [NGROK] {line_clean[:130]}")
                            except Exception:
                                pass
                        threading.Thread(target=_drain_output, args=(p,), daemon=True).start()
                        return p

                    for cmd in cmd_options:
                        app.log_info(f"🚀 [4G / NGROK STATIC DOMAIN] Đang khởi chạy Tên Miền Cố Định: https://{clean_dom}")
                        proc = _start_ngrok_proc(cmd)
                        app.cloudflared_proc = proc
                        time.sleep(2.0)
                        if proc.poll() is None:
                            ngrok_success = True
                            while not getattr(app, 'stop_tunnel_requested', False):
                                proc.wait()
                                if getattr(app, 'stop_tunnel_requested', False):
                                    break
                                retry_count += 1
                                app.log_warning(f"⚠️ [4G / NGROK] Mất kết nối Ngrok. Đang tự động dọn session và kết nối lại (Lần {retry_count})...")
                                try:
                                    subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    time.sleep(1.0)
                                except Exception:
                                    pass
                                proc = _start_ngrok_proc(cmd)
                                app.cloudflared_proc = proc
                            break
                        else:
                            out_err = proc.stdout.read() if proc.stdout else ""
                            app.log_warning(f"Cú pháp câu lệnh Ngrok chưa tương thích, đang thử cú pháp khác... {out_err.strip()[:80]}")

                    if ngrok_success:
                        app.log_warning("⚠️ [4G / ONLINE] Đường truyền Ngrok đã dừng.")
                        return
                    else:
                        app.log_error("❌ Ngrok không thể khởi chạy. Tự động chuyển sang Cloudflare...")
                except Exception as e:
                    app.log_error(f"Lỗi khởi động Ngrok Tunnel: {e}")

        # 1. NẾU CÓ CLOUDFLARE TOKEN CỐ ĐỊNH -> CHẠY CLOUDFLARE STATIC TUNNEL
        bin_path = find_or_download_cloudflared(app)
        if cf_token and bin_path and os.path.exists(bin_path):
            try:
                cmd = [bin_path, "tunnel", "run", "--token", cf_token]
                app.log_info("🔑 [4G / ONLINE] Đang khởi chạy Cloudflare Tunnel với TOKEN CỐ ĐỊNH...")
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore', creationflags=creation_flags)
                app.cloudflared_proc = proc

                found_url = cf_domain if cf_domain.startswith("http") else f"https://{cf_domain}"
                app.public_web_url = found_url
                app.log_info(f"🚀 [4G / CLOUDFLARE STATIC LINK] Sẵn sàng: {found_url}")
                if hasattr(app, '_update_web_url_ui'):
                    app.after(0, app._update_web_url_ui, found_url, True)

                proc.wait()
                app.log_warning("⚠️ [4G / ONLINE] Đường truyền Cloudflare Tunnel đã dừng.")
                if hasattr(app, '_on_tunnel_failed'):
                    app.after(0, app._on_tunnel_failed)
                return
            except Exception as e:
                app.log_error(f"Lỗi khởi động Cloudflare Tunnel Token: {e}")

        # 2. CHẾ ĐỘ CLOUDFLARE QUICK TUNNEL (TÊN MIỀN RANDOM trycloudflare.com)
        if bin_path and os.path.exists(bin_path):
            try:
                app.log_info("🌐 [4G / ONLINE] Đang khởi tạo đường truyền Cloudflare Quick Tunnel (Tên miền ngẫu nhiên)...")
                cmd = [bin_path, "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"]
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    creationflags=creation_flags
                )
                app.cloudflared_proc = proc

                found_url = None
                for line in iter(proc.stdout.readline, ''):
                    if not line:
                        break
                    if not found_url:
                        match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
                        if match:
                            found_url = match.group(1)
                            app.public_web_url = found_url
                            app.log_info(f"🚀 [4G / CLOUDFLARE LINK] Sẵn sàng: {found_url}")
                            if hasattr(app, '_update_web_url_ui'):
                                app.after(0, app._update_web_url_ui, found_url, True)

                proc.poll()
                app.log_warning("⚠️ [4G / ONLINE] Đường truyền Cloudflare Tunnel đã dừng.")
                if hasattr(app, '_on_tunnel_failed'):
                    app.after(0, app._on_tunnel_failed)
                return
            except Exception as e:
                app.log_error(f"Lỗi khởi động Cloudflare Tunnel: {e}")

        # 3. DỰ PHÒNG CUỐI: SSH Tunnel (Localhost.run / Pinggy) nếu Cloudflared không khả dụng
        ssh_bin = shutil.which("ssh") or "ssh"
        ssh_configs = [
            (
                "Localhost.run",
                [ssh_bin, "-T", "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=6", "-o", "TCPKeepAlive=yes", "-R", f"80:127.0.0.1:{port}", "nokey@localhost.run"],
                r'(https://[a-zA-Z0-9-]+\.lhr\.life)'
            ),
            (
                "Pinggy",
                [ssh_bin, "-p", "443", "-R0:localhost:" + str(port), "-o", "StrictHostKeyChecking=no", "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=6", "-o", "TCPKeepAlive=yes", "a.pinggy.io"],
                r'(https://[a-zA-Z0-9-]+\.free\.pinggy\.link|https://[a-zA-Z0-9-]+\.a\.pinggy\.link)'
            )
        ]

        for s_name, cmd, regex_pattern in ssh_configs:
            try:
                app.log_info(f"🌐 [4G / ONLINE] Đang khởi tạo đường truyền {s_name}...")
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    creationflags=creation_flags
                )
                app.cloudflared_proc = proc
                found_url = None

                for line in iter(proc.stdout.readline, ''):
                    if not line:
                        break
                    if not found_url:
                        match = re.search(regex_pattern, line)
                        if match:
                            found_url = match.group(1)
                            app.public_web_url = found_url
                            app.log_info(f"🚀 [4G / {s_name.upper()} LINK] Sẵn sàng: {found_url}")
                            if hasattr(app, '_update_web_url_ui'):
                                app.after(0, app._update_web_url_ui, found_url, True)

                if found_url:
                    app.log_warning(f"⚠️ [4G / ONLINE] Đường truyền {s_name} đã ngắt kết nối.")
                    if hasattr(app, '_on_tunnel_failed'):
                        app.after(0, app._on_tunnel_failed)
                    return
            except Exception as e:
                app.log_error(f"Lỗi kết nối {s_name}: {e}")

        # 3. DỰ PHÒNG CUỐI: Cloudflare Quick Tunnel (cloudflared.exe)
        if bin_path and os.path.exists(bin_path):
            try:
                cmd = [bin_path, "tunnel", "--url", f"http://127.0.0.1:{port}", "--no-autoupdate"]
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    creationflags=creation_flags
                )
                app.cloudflared_proc = proc

                found_url = None
                for line in iter(proc.stdout.readline, ''):
                    if not line:
                        break
                    if not found_url:
                        match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
                        if match:
                            found_url = match.group(1)
                            app.public_web_url = found_url
                            app.log_info(f"🚀 [4G / CLOUDFLARE LINK] Sẵn sàng: {found_url}")
                            if hasattr(app, '_update_web_url_ui'):
                                app.after(0, app._update_web_url_ui, found_url, True)

                proc.poll()
                app.log_warning("⚠️ [4G / ONLINE] Đường truyền Cloudflare Tunnel đã dừng.")
                if hasattr(app, '_on_tunnel_failed'):
                    app.after(0, app._on_tunnel_failed)
                return
            except Exception as e:
                app.log_error(f"Lỗi khởi động Cloudflare Tunnel: {e}")

        if hasattr(app, '_on_tunnel_failed'):
            app.after(0, app._on_tunnel_failed)

    threading.Thread(target=_tunnel_worker, daemon=True).start()
