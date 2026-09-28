import re
import os

workspace_dir = r"c:\Users\Phat\Downloads\ldplayer_tool"
main_py = os.path.join(workspace_dir, "main.py")
assets_dir = os.path.join(workspace_dir, "assets")

with open(main_py, "r", encoding="utf-8") as f:
    lines = f.readlines()

content = "".join(lines)

# 1. Find all image references (*.png)
png_matches = set(re.findall(r'["\']([^"\']+\.png)["\']', content))
print(f"Total unique PNG paths found: {len(png_matches)}")

missing_images = []
for p in sorted(png_matches):
    # Check if absolute or relative to assets
    if os.path.isabs(p):
        full_path = p
    else:
        full_path = os.path.join(assets_dir, p)
    
    if not os.path.exists(full_path):
        # Maybe relative to workspace?
        ws_path = os.path.join(workspace_dir, p)
        if not os.path.exists(ws_path):
            missing_images.append(p)

print("\n--- MISSING ASSET IMAGES REFERENCED IN CODE ---")
if missing_images:
    for m in missing_images:
        print(f"MISSING: {m}")
else:
    print("None! All PNGs exist.")

# 2. Check for stub/empty/pass functions
print("\n--- CHECKING FUNCTIONS WITH PASS OR RETURN EARLY ---")
def_matches = re.finditer(r'def\s+([a-zA-Z0-9_]+)\s*\([^)]*\):', content)
for m in def_matches:
    func_name = m.group(1)
    start_pos = m.end()
    # Find next def or class or end
    next_def = re.search(r'\n    def |\nclass ', content[start_pos:])
    end_pos = start_pos + next_def.start() if next_def else len(content)
    func_body = content[start_pos:end_pos].strip()
    
    # Check if body is just pass or return
    cleaned_body = re.sub(r'#[^\n]*', '', func_body).strip()
    cleaned_body = re.sub(r'"""[\s\S]*?"""', '', cleaned_body).strip()
    cleaned_body = re.sub(r"'''[\s\S]*?'''", '', cleaned_body).strip()
    
    if cleaned_body in ['pass', 'return', 'pass\nreturn', 'return None']:
        print(f"Stub function: {func_name}")

# 3. Check for specific Card operations that might be skipped or have conditions that never trigger
print("\n--- AUDIT CARD BY CARD FLOWS ---")
