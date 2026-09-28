import os
import re

assets_dir = r"c:\Users\Phat\Downloads\ldplayer_tool\assets"
with open("main.py", "r", encoding="utf-8") as f:
    text = f.read()

# Check dungeons_to_run
pb_images = [
    "card_b/b_pb20.png", "card_b/b_pb20map.png",
    "card_b/b_pb50.png", "card_b/b_pb50map.png",
    "card_b/b_pb80.png", "card_b/b_pb80map.png",
    "card_b/b_pb110.png", "card_b/b_pb110map.png",
    "card_b/b_pb140.png", "card_b/b_pb140map.png"
]
print("--- CHECK PB IMAGES ---")
for img in pb_images:
    p = os.path.join(assets_dir, img)
    print(f"{img}: {'EXISTS' if os.path.exists(p) else 'MISSING'}")

# Check HS / HT images
print("\n--- CHECK HS / HT IMAGES ---")
for i in range(1, 6):
    hs = f"team_hp/HS_{i}.png"
    ht = f"team_hp/HT_{i}.png"
    print(f"{hs}: {'EXISTS' if os.path.exists(os.path.join(assets_dir, hs)) else 'MISSING'}")
    print(f"{ht}: {'EXISTS' if os.path.exists(os.path.join(assets_dir, ht)) else 'MISSING'}")

# Check where HS_ and HT_ are referenced in main.py
hs_refs = re.findall(r'.{0,50}H[ST]_\d\.png.{0,50}', text)
print(f"\nReferences to HS_/HT_ in code ({len(hs_refs)}):")
for r in hs_refs[:5]:
    print("  ", r.strip())

# Check _find_nhanvat_template implementation
print("\n--- NHAN VAT TEMPLATE FUNCTION ---")
nv_func = re.search(r'def _find_nhanvat_template\([^)]*\):[\s\S]*?(?=\n    def )', text)
if nv_func:
    print(nv_func.group(0)[:500])
