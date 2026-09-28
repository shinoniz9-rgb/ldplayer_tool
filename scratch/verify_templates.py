import os
import re

assets_dir = r"c:\Users\Phat\Downloads\ldplayer_tool\assets"
with open("main.py", "r", encoding="utf-8") as f:
    text = f.read()

calls = re.findall(r'_find_template_on_screen\([^,]+,\s*[^,]+,\s*["\']([^"\']+)["\']', text)
print(f"Total literal template calls found: {len(calls)}")

all_assets_files = {}
for root, dirs, files in os.walk(assets_dir):
    for f in files:
        all_assets_files[f] = os.path.join(root, f)

print(f"Total files in assets: {len(all_assets_files)}")

missing = []
found = []
for c in sorted(set(calls)):
    clean = os.path.basename(c)
    direct = os.path.join(assets_dir, c)
    if os.path.exists(direct) or clean in all_assets_files:
        found.append((c, all_assets_files.get(clean, direct)))
    else:
        missing.append(c)

print(f"\n--- FOUND TEMPLATES ({len(found)}) ---")
for c, p in found:
    rel = os.path.relpath(p, assets_dir)
    # print(f"  OK: {c} -> {rel}")

print(f"\n--- MISSING TEMPLATES ({len(missing)}) ---")
for m in missing:
    print(f"  MISSING: {m}")
