import os
import sys
import subprocess
import time
import cv2
import numpy as np

# Đảm bảo in Tiếng Việt không bị lỗi font trên Windows CMD/Terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Đường dẫn cài đặt LDPlayer (mặc định)
LDPLAYER_DIR = r"C:\Program Files\LDPlayer\LDPlayer9"
ADB_PATH = os.path.join(LDPLAYER_DIR, "adb.exe")
LDCONSOLE_PATH = os.path.join(LDPLAYER_DIR, "ldconsole.exe")

def capture_emulator_index1_fast(output_path="screenshot_index1.png", index=1):
    """
    Chụp ảnh màn hình giả lập LDPlayer theo index trực tiếp vào RAM (không lưu file tạm trên Android).
    Nhanh và tối ưu nhất (< 0.2s).
    """
    # LDPlayer phân bổ cổng ADB cho index:
    # Index 0: 5555 (emulator-5554)
    # Index 1: 5557 (emulator-5556)
    # Index N: 5555 + N*2 (emulator-5554 + N*2)
    device_port = 5555 + (index * 2)
    device_serial = f"127.0.0.1:{device_port}"
    
    # Đảm bảo adb đã kết nối thiết bị
    subprocess.run([ADB_PATH, "connect", device_serial], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Lệnh chụp ảnh xuất trực tiếp luồng byte png
    cmd = [ADB_PATH, "-s", device_serial, "exec-out", "screencap", "-p"]
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True)
    
    if result.returncode == 0 and len(result.stdout) > 0:
        # Decode mảng byte png sang OpenCV Image
        img_np = np.frombuffer(result.stdout, np.uint8)
        img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
        
        if img is not None:
            cv2.imwrite(output_path, img)
            elapsed = time.time() - start_time
            print(f"[THÀNH CÔNG] Đã chụp ảnh index {index} (Phương pháp ADB Direct)!")
            print(f" -> Kích thước ảnh: {img.shape[1]}x{img.shape[0]}")
            print(f" -> Thời gian thực thi: {elapsed:.3f} giây")
            print(f" -> File đã lưu tại: {os.path.abspath(output_path)}")
            return img
            
    print(f"[CẢNH BÁO] Không thể chụp bằng ADB Direct cho {device_serial}. Đang thử bằng ldconsole...")
    return capture_emulator_index1_ldconsole(output_path, index)


def capture_emulator_index1_ldconsole(output_path="screenshot_index1.png", index=1):
    """
    Chụp ảnh màn hình giả lập LDPlayer sử dụng lệnh ldconsole.exe / dnconsole.exe
    (Giống phương pháp được dùng trong main.py)
    """
    start_time = time.time()
    remote_path = f"/sdcard/screen_idx{index}.png"
    
    # 1. Gọi screencap lưu vào thẻ nhớ giả lập
    cmd_cap = [LDCONSOLE_PATH, "adb", "--index", str(index), "--command", f"shell screencap -p {remote_path}"]
    subprocess.run(cmd_cap, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 2. Pull ảnh từ giả lập về máy tính
    cmd_pull = [LDCONSOLE_PATH, "adb", "--index", str(index), "--command", f"pull {remote_path} \"{output_path}\""]
    subprocess.run(cmd_pull, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        elapsed = time.time() - start_time
        img = cv2.imread(output_path)
        print(f"[THÀNH CÔNG] Đã chụp ảnh index {index} (Phương pháp ldconsole)!")
        if img is not None:
            print(f" -> Kích thước ảnh: {img.shape[1]}x{img.shape[0]}")
        print(f" -> Thời gian thực thi: {elapsed:.3f} giây")
        print(f" -> File đã lưu tại: {os.path.abspath(output_path)}")
        return img
    else:
        print(f"[THẤT BẠI] Không thể chụp ảnh màn hình giả lập index {index}.")
        return None


if __name__ == "__main__":
    print("=== CHƯƠNG TRÌNH CHỤP ẢNH MAN HÌNH GIẢ LẬP INDEX 1 ===")
    
    # Kiểm tra xem đường dẫn LDPlayer có tồn tại không
    if not os.path.exists(ADB_PATH):
        print(f"Không tìm thấy adb.exe tại: {ADB_PATH}")
        print("Vui lòng kiểm tra lại đường dẫn cài đặt LDPlayer!")
    else:
        # Chụp màn hình giả lập Index 1 và lưu vào screenshot_index1.png
        image = capture_emulator_index1_fast(output_path=r"C:\Users\Phat\Downloads\ldplayer_tool\assets\Screenshots\screenshot_index1.png", index=1)
