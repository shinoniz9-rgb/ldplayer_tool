# -*- coding: utf-8 -*-
import os
import sys
import time
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

# Tắt tiến trình cũ nếu đang mở để tránh lỗi PermissionError WinError 5 khóa file
try:
    subprocess.run(["taskkill", "/F", "/IM", "TS_Origin_Control.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0)
except Exception:
    pass

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconsole",
    "--onefile",
    "--clean",
    "--name", "TS_Origin_Control",
    "--collect-all", "customtkinter",
    "--collect-all", "rapidocr_onnxruntime",
    "--collect-all", "onnxruntime",
    "--collect-all", "pyclipper",
    "--collect-all", "shapely",
    "--hidden-import", "pystray",
    "--hidden-import", "PIL",
    "--hidden-import", "PIL.Image",
    "--hidden-import", "PIL.ImageDraw",
    "--hidden-import", "PIL.ImageTk",
    "--hidden-import", "cv2",
    "--hidden-import", "numpy",
    "--hidden-import", "web_server",
    "--add-data", "assets;assets",
    "main.py"
]

print(f"[CMD] {' '.join(cmd)}\n")
res = subprocess.run(cmd)

dist_exe = os.path.join(base_dir, "dist", "TS_Origin_Control.exe")
if res.returncode == 0 and os.path.exists(dist_exe):
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

    # Sao chép launch_app.vbs nếu có
    vbs_file = os.path.join(base_dir, "launch_app.vbs")
    if os.path.exists(vbs_file):
        shutil.copy2(vbs_file, os.path.join(base_dir, "dist", "launch_app.vbs"))
        print("  ✅ Đã sao chép launch_app.vbs!")

    # Sao chép Tao_Loi_Tat_Desktop.bat nếu có
    bat_file = os.path.join(base_dir, "Tao_Loi_Tat_Desktop.bat")
    if os.path.exists(bat_file):
        shutil.copy2(bat_file, os.path.join(base_dir, "dist", "Tao_Loi_Tat_Desktop.bat"))
        print("  ✅ Đã sao chép Tao_Loi_Tat_Desktop.bat!")

    # Tự động tạo bản Chia Sẻ (dist_share) - KHÔNG ngrok, chỉ Cloudflared random
    print("\n📦 Đang tạo bản Chia Sẻ (dist_share)...")
    share_dir = os.path.join(base_dir, "dist_share")
    if os.path.exists(share_dir):
        shutil.rmtree(share_dir)
    os.makedirs(share_dir, exist_ok=True)

    # 1. Copy TS_Origin_Control.exe & cloudflared.exe sang dist_share
    shutil.copy2(dist_exe, os.path.join(share_dir, "TS_Origin_Control.exe"))
    if os.path.exists(cf_exe):
        shutil.copy2(cf_exe, os.path.join(share_dir, "cloudflared.exe"))

    # 2. Copy assets sang dist_share
    if os.path.exists(src_assets):
        shutil.copytree(src_assets, os.path.join(share_dir, "assets"))

    # 3. Copy launch_app.vbs & Tao_Loi_Tat_Desktop.bat sang dist_share
    if os.path.exists(vbs_file):
        shutil.copy2(vbs_file, os.path.join(share_dir, "launch_app.vbs"))
    if os.path.exists(bat_file):
        shutil.copy2(bat_file, os.path.join(share_dir, "Tao_Loi_Tat_Desktop.bat"))
    print("  ✅ Đã sao chép launch_app.vbs và Tao_Loi_Tat_Desktop.bat vào dist_share!")

    # 4. Tạo config.json sạch cho dist_share (loại bỏ token/domain ngrok cá nhân)
    try:
        import json
        with open(cfg_file, "r", encoding="utf-8") as f:
            clean_cfg = json.load(f)
        for k in ["ngrok_authtoken", "fixed_domain", "ngrok_domain", "telegram_bot_token", "telegram_bot_token_2", "telegram_chat_id", "telegram_chat_id_2"]:
            if k in clean_cfg:
                del clean_cfg[k]
        clean_cfg["enable_telegram"] = False
        with open(os.path.join(share_dir, "config.json"), "w", encoding="utf-8") as f:
            json.dump(clean_cfg, f, indent=4, ensure_ascii=False)
        print("  ✅ Đã tạo config.json sạch (loại bỏ ngrok & telegram cá nhân) trong dist_share!")
    except Exception as e:
        print(f"  ⚠️ Lỗi tạo config.json sạch: {e}")

    # 5. Lưu ý: Không tự ý đồng bộ sang bản hoạt động (C:\LDPlayer\dist) theo yêu cầu người dùng (người dùng tự thay thế vào sau)

    # Tự động dọn dẹp các tệp và thư mục phát sinh không dùng đến
    print("\n🧹 Đang tự động dọn dẹp các tệp phát sinh (build/, *.spec)...")
    build_dir = os.path.join(base_dir, "build")
    if os.path.exists(build_dir):
        try:
            shutil.rmtree(build_dir, ignore_errors=True)
            print("  ✅ Đã xóa thư mục tạm build/ (giải phóng ~85MB dung lượng)!")
        except Exception as e:
            print(f"  ⚠️ Không thể xóa thư mục build/: {e}")

    spec_file = os.path.join(base_dir, "TS_Origin_Control.spec")
    if os.path.exists(spec_file):
        try:
            os.remove(spec_file)
            print("  ✅ Đã xóa file cấu hình tạm TS_Origin_Control.spec!")
        except Exception as e:
            print(f"  ⚠️ Không thể xóa file .spec: {e}")

    # Xóa file nén cũ nếu còn tồn tại
    zip_share_path = os.path.join(base_dir, "TS_Origin_Control_Share.zip")
    if os.path.exists(zip_share_path):
        try:
            os.remove(zip_share_path)
        except Exception:
            pass

    print("\n============================================================")
    print("  🎉 ĐÓNG GÓI THÀNH CÔNG!")
    print(f"  📁 Bản chạy: {dist_exe}")
    print("============================================================")
else:
    print(f"\n❌ Đóng gói thất bại với mã lỗi: {res.returncode}")
    sys.exit(res.returncode)
