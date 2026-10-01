# -*- coding: utf-8 -*-
import os
import sys
import shutil
import subprocess

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

base_dir = r"c:\Users\Phat\Downloads\ldplayer_tool"
os.chdir(base_dir)

print("============================================================")
print("     ĐANG TIẾN HÀNH ĐÓNG GÓI TS_Danh_Thuong SANG .EXE       ")
print("============================================================")

# Tắt tiến trình cũ nếu đang mở
try:
    subprocess.run(["taskkill", "/F", "/IM", "TS_Danh_Thuong.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except Exception:
    pass

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconsole",
    "--onefile",
    "--clean",
    "--name", "TS_Danh_Thuong",
    "--collect-all", "customtkinter",
    "--hidden-import", "pystray",
    "--hidden-import", "PIL",
    "--hidden-import", "PIL.Image",
    "--hidden-import", "PIL.ImageDraw",
    "--hidden-import", "cv2",
    "--hidden-import", "numpy",
    "--add-data", "assets;assets",
    "danh_thuong_tool.py"
]

print(f"[CMD] {' '.join(cmd)}\n")
res = subprocess.run(cmd)

dist_exe = os.path.join(base_dir, "dist", "TS_Danh_Thuong.exe")
if res.returncode == 0 and os.path.exists(dist_exe):
    print("\n✅ Đã tạo file chạy TS_Danh_Thuong.exe thành công trong thư mục dist!")
    
    # Dọn dẹp thư mục tạm build/ và spec
    try:
        build_dir = os.path.join(base_dir, "build")
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir, ignore_errors=True)
        spec_file = os.path.join(base_dir, "TS_Danh_Thuong.spec")
        if os.path.exists(spec_file):
            os.remove(spec_file)
    except Exception:
        pass

    print("============================================================")
    print("  🎉 ĐÓNG GÓI THÀNH CÔNG TOOL ĐÁNH THƯỜNG SIÊU GỌN!")
    print(f"  📁 Bản chạy: {dist_exe}")
    print("============================================================")
else:
    print("\n❌ Đóng gói thất bại! Vui lòng kiểm tra lại log.")
