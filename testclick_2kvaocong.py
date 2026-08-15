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

# Sử dụng ldconsole.exe hoặc dnconsole.exe
LD_DIR = r"C:\Program Files\LDPlayer\LDPlayer9"
LDCONSOLE_PATH = os.path.join(LD_DIR, "ldconsole.exe")
if not os.path.exists(LDCONSOLE_PATH):
    LDCONSOLE_PATH = os.path.join(LD_DIR, "dnconsole.exe")

ADB_PATH = os.path.join(LD_DIR, "adb.exe")
INDEX = "0"  # CHỈ THỰC THI TRÊN INDEX 0 (emulator-5554)

def run_cmd(cmd_args):
    """Thực thi lệnh an toàn, nếu dnconsole đòi quyền Admin (WinError 740) thì tự động dùng ldconsole"""
    try:
        return subprocess.run(cmd_args, capture_output=True, text=True)
    except OSError as e:
        if getattr(e, 'winerror', None) == 740 and "dnconsole" in cmd_args[0].lower():
            cmd_args[0] = LDCONSOLE_PATH
            return subprocess.run(cmd_args, capture_output=True, text=True)
        raise e

def get_adb_device_by_index(index_str):
    """Tính toán device_id ADB chính xác theo INDEX chỉ định (Index 0 = emulator-5554, Index 1 = emulator-5556, ...)"""
    try:
        idx = int(index_str)
        port = 5554 + idx * 2
        return f"emulator-{port}"
    except Exception:
        return "emulator-5556"

def tap(x, y):
    """Hàm tap (click) vào tọa độ (x, y) trên LDPlayer theo đúng INDEX"""
    cmd = [
        LDCONSOLE_PATH,
        "adb",
        "--index", str(INDEX),
        "--command", f"shell input tap {x} {y}"
    ]
    print(f"--> Tap [Index {INDEX}]: ({x}, {y})")
    run_cmd(cmd)

def take_screenshot(filename="temp_screen.png"):
    """Chụp ảnh màn hình giả lập LDPlayer theo đúng INDEX chuẩn xác"""
    abs_filename = os.path.abspath(filename)
    device_id = get_adb_device_by_index(INDEX)
    
    # 1. Chụp bằng ADB direct tới đúng thiết bị emulator của INDEX
    try:
        res = subprocess.run([ADB_PATH, "-s", device_id, "exec-out", "screencap", "-p"], capture_output=True)
        if res.returncode == 0 and len(res.stdout) > 1000:
            with open(abs_filename, "wb") as f:
                f.write(res.stdout)
            return
    except Exception:
        pass

    # 2. Fallback dùng ldconsole theo đúng --index INDEX
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
    """Hàm đọc ảnh OpenCV an toàn cho đường dẫn chứa ký tự tiếng Việt hoặc ký tự đặc biệt"""
    try:
        data = np.fromfile(path, dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return cv2.imread(path)

def find_and_click_image(template_path, threshold=0.85):
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

    screen_file = "temp_screen.png"
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

def click_until_disappear(template_path, threshold=0.85, interval=0.5):
    """
    Quét nhận diện ảnh mẫu trên màn hình LDPlayer và click vào ảnh.
    Lặp lại mỗi `interval` giây cho đến khi không còn tìm thấy ảnh (mất ảnh).
    """
    print(f"👁️ Bắt đầu quét ảnh '{template_path}' mỗi {interval}s đến khi mất ảnh...")
    while True:
        found = find_and_click_image(template_path, threshold=threshold)
        if not found:
            print(f"ℹ️ Không còn thấy ảnh '{template_path}' ➔ Đã mất ảnh, hoàn thành!")
            break
        time.sleep(interval)


# ================= SCRIPT THỰC THI =================
if __name__ == "__main__":
    print(f"🚀 Bắt đầu script test click tọa độ và quét ảnh Card E (Đang chọn Index: {INDEX})...")

    # 1. Tap tọa độ (665, 60)
    tap(665, 60)
    print("Nghỉ 1 giây...")
    time.sleep(1)

    # 2. Quét ảnh e_cong.png
    print("Đang quét ảnh e_cong.png...")
    find_and_click_image(r"C:\Users\Phat\Downloads\ldplayer_tool\assets\card_e\e_cong.png", threshold=0.85)
    print("Nghỉ 3 giây...")
    time.sleep(3)

    # 3. Quét ảnh e_tieptheo.png đến khi mất ảnh (mỗi 0.5s)
    print("👁️ [Bước 3] Quét ảnh e_tieptheo.png đến khi mất ảnh (mỗi 0.5s)...")
    click_until_disappear(r"C:\Users\Phat\Downloads\ldplayer_tool\assets\card_e\e_tieptheo.png", threshold=0.85, interval=0.5)

    print("✅ Hoàn thành script test!")
