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
print("  ĐANG TIẾN HÀNH ĐÓNG GÓI TS_Origin_Control SANG FILE .EXE  ")
print("============================================================")

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconsole",
    "--onefile",
    "--clean",
    "--name", "TS_Origin_Control",
    "--collect-all", "customtkinter",
    "--hidden-import", "pystray",
    "--hidden-import", "PIL",
    "--hidden-import", "PIL.Image",
    "--hidden-import", "PIL.ImageDraw",
    "--hidden-import", "cv2",
    "--hidden-import", "numpy",
    "--hidden-import", "web_server",
    "--add-data", "assets;assets",
    "main.py"
]

print(f"[CMD] {' '.join(cmd)}\n")
res = subprocess.run(cmd)

dist_exe = os.path.join(base_dir, "dist", "TS_Origin_Control.exe")
if os.path.exists(dist_exe):
    print("\n📥 Đang sao chép file cấu hình config.json (kèm 2 dòng ngrok) và tài nguyên...")
    
    # Sao chép config.json vào thư mục dist
    cfg_file = os.path.join(base_dir, "config.json")
    if os.path.exists(cfg_file):
        shutil.copy2(cfg_file, os.path.join(base_dir, "dist", "config.json"))
        print("  ✅ Đã sao chép config.json (chứa ngrok_authtoken & ngrok_domain) vào thư mục dist!")
        
    # Sao chép thư mục assets vào thư mục dist
    dist_assets = os.path.join(base_dir, "dist", "assets")
    src_assets = os.path.join(base_dir, "assets")
    if os.path.exists(src_assets):
        if os.path.exists(dist_assets):
            shutil.rmtree(dist_assets)
        shutil.copytree(src_assets, dist_assets)
        print("  ✅ Đã sao chép thư mục assets vào thư mục dist!")
        
    # Sao chép cloudflared.exe nếu có
    cf_exe = os.path.join(base_dir, "cloudflared.exe")
    if os.path.exists(cf_exe):
        shutil.copy2(cf_exe, os.path.join(base_dir, "dist", "cloudflared.exe"))
        print("  ✅ Đã sao chép cloudflared.exe!")
        
    # Sao chép ngrok.exe nếu có
    ng_exe = os.path.join(base_dir, "ngrok.exe")
    if os.path.exists(ng_exe):
        shutil.copy2(ng_exe, os.path.join(base_dir, "dist", "ngrok.exe"))
        print("  ✅ Đã sao chép ngrok.exe!")
        
    print("\n============================================================")
    print("  🎉 ĐÓNG GÓI THÀNH CÔNG!")
    print(f"  📁 File chạy: {dist_exe}")
    print("============================================================")
else:
    print(f"\n❌ Đóng gói thất bại với mã lỗi: {res.returncode}")
    sys.exit(res.returncode)
