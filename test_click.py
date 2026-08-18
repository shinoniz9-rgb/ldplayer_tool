import subprocess
import time
import os
import sys
import cv2
import numpy as np

# Thiết lập UTF-8 cho console stdout/stderr trên Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
        sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
    except Exception:
        pass

LD_DIR = r"C:\Program Files\LDPlayer\LDPlayer9"
LDCONSOLE_PATH = os.path.join(LD_DIR, "ldconsole.exe")
if not os.path.exists(LDCONSOLE_PATH):
    LDCONSOLE_PATH = os.path.join(LD_DIR, "dnconsole.exe")

ADB_PATH = os.path.join(LD_DIR, "adb.exe")
INDEX = "1"  # Thực thi trên Index 1 (emulator-5556)

def run_cmd(cmd_args):
    """Thực thi lệnh an toàn"""
    try:
        return subprocess.run(cmd_args, capture_output=True, text=True)
    except OSError as e:
        if getattr(e, 'winerror', None) == 740 and "dnconsole" in cmd_args[0].lower():
            cmd_args[0] = LDCONSOLE_PATH
            return subprocess.run(cmd_args, capture_output=True, text=True)
        raise e

def get_adb_device_by_index(index_str):
    """Tính toán device_id ADB chính xác theo INDEX (Index 0 = emulator-5554, Index 1 = emulator-5556)"""
    try:
        idx = int(index_str)
        port = 5554 + idx * 2
        return f"emulator-{port}"
    except Exception:
        return "emulator-5556"

def tap(x, y):
    """Hàm tap (click) vào tọa độ (x, y) trên LDPlayer theo INDEX"""
    cmd = [
        LDCONSOLE_PATH,
        "adb",
        "--index", str(INDEX),
        "--command", f"shell input tap {x} {y}"
    ]
    print(f"--> Tap [Index {INDEX}]: ({x}, {y})")
    run_cmd(cmd)

def take_screenshot(filename="temp_screen.png"):
    """Chụp ảnh màn hình giả lập LDPlayer theo đúng INDEX"""
    abs_filename = os.path.abspath(filename)
    device_id = get_adb_device_by_index(INDEX)
    
    try:
        res = subprocess.run([ADB_PATH, "-s", device_id, "exec-out", "screencap", "-p"], capture_output=True)
        if res.returncode == 0 and len(res.stdout) > 1000:
            with open(abs_filename, "wb") as f:
                f.write(res.stdout)
            return
    except Exception:
        pass

    cmd_cap = [
        LDCONSOLE_PATH,
        "adb",
        "--index", str(INDEX),
        "--command", "shell screencap -p /sdcard/screen.png"
    ]
    run_cmd(cmd_cap)

    cmd_pull = [
        LDCONSOLE_PATH,
        "adb",
        "--index", str(INDEX),
        "--command", f'pull /sdcard/screen.png "{abs_filename}"'
    ]
    run_cmd(cmd_pull)

def cv2_imread_unicode(path):
    """Hàm đọc ảnh OpenCV an toàn cho đường dẫn chứa ký tự tiếng Việt"""
    try:
        data = np.fromfile(path, dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return cv2.imread(path)

def find_and_click_image(template_path, threshold=0.70):
    """
    Quét nhận diện ảnh mẫu trên màn hình LDPlayer và click vào tâm ảnh tìm thấy.
    """
    if not template_path.endswith((".png", ".jpg", ".jpeg")):
        template_path += ".png"

    possible_paths = [
        template_path,
        os.path.join("assets", template_path)
    ]
    
    img_path = None
    for p in possible_paths:
        if os.path.exists(p):
            img_path = p
            break

    if not img_path:
        print(f"❌ Không tìm thấy file ảnh mẫu tại: {template_path}")
        return False

    screen_file = f"temp_screen_idx{INDEX}.png"
    take_screenshot(screen_file)

    screen = cv2_imread_unicode(screen_file)
    template = cv2_imread_unicode(img_path)

    if screen is None:
        print("❌ Lỗi: Không thể đọc được ảnh chụp màn hình LDPlayer!")
        return False
    if template is None:
        print(f"❌ Lỗi: Không thể đọc được file ảnh mẫu: {img_path}")
        return False

    res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    if max_val >= threshold:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        print(f"--> Tìm thấy ảnh '{img_path}' tại ({center_x}, {center_y}) với độ chính xác: {max_val*100:.1f}%")
        tap(center_x, center_y)
        return True
    else:
        print(f"❌ Không tìm thấy ảnh '{img_path}' (Độ khớp tối đa đạt được: {max_val*100:.1f}%)")
        return False

# ================= SCRIPT THỰC THI =================
if __name__ == "__main__":
    # 1. Tap (1125, 175)
    print(f"🚀 [Bước 1] Tap tọa độ (1125, 175) trên LDPlayer Index {INDEX}...")
    tap(1115, 85)
    print("Nghỉ 0.5 giây...")
    time.sleep(0.5)

    # 2. Quét ảnh / tap card_d/d_buoc1.png
    print("👁️ [Bước 2] Quét nhận diện & tap ảnh card_d/d_buoc1.png...")
    find_and_click_image("card_d/d_buoc1.png", threshold=0.85)
    print("Nghỉ 6 giây...")
    time.sleep(6)

    # 3. Quét ảnh / tap card_d/d_buoc2.png
    print("👁️ [Bước 2] Quét nhận diện & tap ảnh card_d/d_buoc2.png...")
    find_and_click_image("card_d/d_buoc2.png", threshold=0.85)
    print("Nghỉ 6 giây...")
    time.sleep(6)

    # 4. Tap (1125, 175)
    print(f"🚀 [Bước 1] Tap tọa độ (1125, 175) trên LDPlayer Index {INDEX}...")
    tap(1115, 85)
    print("Nghỉ 0.5 giây...")
    time.sleep(0.5)

    # 4. Click liên tục vào tọa độ (1240, 605) mỗi 0.8s (tối đa 30 lần) để tìm xuất hiện ảnh card_d/d_chien.png (70%).
    # Khi quét phát hiện card_d/d_chien.png: Dừng click (1240, 605)
    print("👁️ [Bước 4] Click liên tục (1240, 605) mỗi 0.8s (tối đa 30 lần) tìm ảnh 'card_d/d_chien.png' (70%)...")
    for _ in range(30):
        found = find_and_click_image("card_d/d_chien.png", threshold=0.70)
        if found:
            print("🎯 Mắt thần phát hiện 'card_d/d_chien.png'! Dừng click (1240, 605).")
            break
        tap(1240, 605)
        time.sleep(0.8)

    # 5. Click (1135, 565) ➔ Hoãn 0.5s.
    print("👉 [Bước 5] Click (1135, 565) ➔ Hoãn 0.5s...")
    tap(1135, 565)
    time.sleep(0.5)

    # 6. Khi quét phát hiện ảnh / tap card_d/d_tieptheo.png 0.5s
    print("👁️ [Bước 6] Quét tìm & tap ảnh 'card_d/d_tieptheo.png' (70%) mỗi 0.5s...")
    for _ in range(20):
        if find_and_click_image("card_d/d_tieptheo.png", threshold=0.70):
            print("🎯 Đã phát hiện & tap ảnh 'card_d/d_tieptheo.png'!")
            break
        time.sleep(0.5)

    # 7. Khi quét phát hiện ảnh / tap card_d/d_vaotran.png 0.5s
    print("👁️ [Bước 7] Quét tìm & tap ảnh 'card_d/d_vaotran.png' (75%) mỗi 0.5s...")
    for _ in range(20):
        if find_and_click_image("card_d/d_vaotran.png", threshold=0.75):
            print("🎯 Đã phát hiện & tap ảnh 'card_d/d_vaotran.png'!")
            break
        time.sleep(0.5)

    # 8. Khi quét phát hiện ảnh / tap card_d/d_tieptheo.png (Ngưỡng 0.70) 0.5s nhấp đến kết thúc
    print("👁️ [Bước 8] Quét tìm & tap ảnh 'card_d/d_tieptheo.png' (70%) mỗi 0.5s...")
    for _ in range(20):
        if find_and_click_image("card_d/d_tieptheo.png", threshold=0.70):
            print("🎯 Đã phát hiện & tap ảnh 'card_d/d_tieptheo.png'!")
            break
        time.sleep(0.5)

    print("✅ Hoàn thành script test!")
