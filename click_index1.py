import subprocess
import time
import os
import cv2
import numpy as np

DNCONSOLE_PATH = r"C:\Program Files\LDPlayer\LDPlayer9\dnconsole.exe"
INDEX = "1"

def tap(x, y):
    """Hàm tap (click) vào tọa độ (x, y) trên LDPlayer"""
    cmd = [
        DNCONSOLE_PATH,
        "adb",
        "--index", str(INDEX),
        "--command", f"shell input tap {x} {y}"
    ]
    print(f"--> Tap: ({x}, {y})")
    subprocess.run(cmd, capture_output=True, text=True)

def take_screenshot(filename="temp_screen.png"):
    """Chụp ảnh màn hình giả lập LDPlayer và kéo về máy tính"""
    # 1. Chụp màn hình lưu vào bộ nhớ tạm của LDPlayer (/sdcard/screen.png)
    cmd_cap = [
        DNCONSOLE_PATH,
        "adb",
        "--index", str(INDEX),
        "--command", "shell screencap -p /sdcard/screen.png"
    ]
    subprocess.run(cmd_cap, capture_output=True, text=True)

    # 2. Pull file ảnh về máy tính
    cmd_pull = [
        DNCONSOLE_PATH,
        "adb",
        "--index", str(INDEX),
        "--command", f"pull /sdcard/screen.png {filename}"
    ]
    subprocess.run(cmd_pull, capture_output=True, text=True)

def cv2_imread_unicode(path):
    """Hàm đọc ảnh OpenCV an toàn cho đường dẫn chứa ký tự tiếng Việt hoặc ký tự đặc biệt"""
    try:
        data = np.fromfile(path, dtype=np.uint8)
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return cv2.imread(path)

def find_and_click_image(template_path, threshold=0.8):
    """
    Quét nhận diện ảnh mẫu trên màn hình LDPlayer và click vào tâm ảnh tìm thấy.
    :param template_path: Đường dẫn ảnh mẫu (ví dụ: 'card_d/d_cong1' hoặc 'assets/card_d/d_cong1.png')
    :param threshold: Độ chính xác nhận diện (0.8 = 80%)
    :return: True nếu tìm thấy và tap, False nếu không tìm thấy
    """
    # Tự động bổ sung phần mở rộng .png nếu chưa có
    if not template_path.endswith((".png", ".jpg", ".jpeg")):
        template_path += ".png"

    # Kiểm tra các vị trí thư mục (đường dẫn trực tiếp hoặc nằm trong thư mục 'assets')
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

    # Chụp màn hình hiện tại
    screen_file = "temp_screen.png"
    take_screenshot(screen_file)

    # Đọc ảnh màn hình và ảnh mẫu
    screen = cv2_imread_unicode(screen_file)
    template = cv2_imread_unicode(img_path)

    if screen is None:
        print("❌ Lỗi: Không thể đọc được ảnh chụp màn hình LDPlayer!")
        return False
    if template is None:
        print(f"❌ Lỗi: Không thể đọc được file ảnh mẫu: {img_path}")
        return False

    # Khớp ảnh mẫu (Template Matching)
    res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    if max_val >= threshold:
        h, w = template.shape[:2]
        # Tính tọa độ điểm chính giữa của ảnh tìm thấy
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        print(f"--> Tìm thấy ảnh '{img_path}' tại ({center_x}, {center_y}) với độ chính xác: {max_val*100:.1f}%")
        tap(center_x, center_y)
        return True
    else:
        print(f"❌ Không tìm thấy ảnh '{img_path}' (Độ khớp tối đa đạt được: {max_val*100:.1f}%)")
        return False


# ================= SCRIPT THỰC THI =================

# 1. Tap tọa độ (1000, 130)
tap(1000, 130)

# Nghỉ 5 giây
print("Nghỉ 5 giây...")
time.sleep(5)

# 2. Tap tọa độ (120, 230)
tap(120, 230)

# Nghỉ 3 giây
print("Nghỉ 3 giây...")
time.sleep(3)

# 3. Tap tọa độ (275, 125)
tap(275, 125)

# Nghỉ 2 giây
print("Nghỉ 2 giây...")
time.sleep(2)

# 4. Quét nhận diện ảnh card_d/d_cong1 và click vào ảnh
print("Đang quét nhận diện ảnh card_d/d_cong1...")
find_and_click_image("C:\\Users\\Phat\\Downloads\\ldplayer_tool\\assets\\card_d\\d_cong1.png", threshold=0.8)

# Nghỉ 4 giây
print("Nghỉ 4 giây...")
time.sleep(4)

# 5. Tap tọa độ (560, 455)
tap(560, 455)

# Nghỉ 4 giây
print("Nghỉ 4 giây...")
time.sleep(4)

# 6. Tap tọa độ (135, 295)
tap(135, 295)

# Nghỉ 3 giây
print("Nghỉ 3 giây...")
time.sleep(3)

# 7. Quét nhận diện ảnh card_d/d_cong1 và click vào ảnh
print("Đang quét nhận diện ảnh card_d/d_cong1...")
find_and_click_image("C:\\Users\\Phat\\Downloads\\ldplayer_tool\\assets\\card_d\\d_cong1.png", threshold=0.7)

# Nghỉ 3 giây
print("Nghỉ 3 giây...")
time.sleep(3)

# 8. Tap tọa độ (215, 505)
tap(215, 505)

# Nghỉ 5 giây
print("Nghỉ 5 giây...")
time.sleep(5)

# 9. Quét nhận diện ảnh card_d/d_cong1 và click vào ảnh
print("Đang quét nhận diện ảnh card_d/d_cong1...")
find_and_click_image("C:\\Users\\Phat\\Downloads\\ldplayer_tool\\assets\\card_d\\d_cong1.png", threshold=0.7)


print("Đã hoàn thành!")
