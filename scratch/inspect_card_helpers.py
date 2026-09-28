import re

with open("main.py", "r", encoding="utf-8") as f:
    text = f.read()

# Let's inspect Card A's helper functions
print("--- CARD A HELPERS ---")
for fn in ["_run_boss_safezone", "_run_boss_pre_move", "_run_boss_move_manual", "_run_boss_workflow", "_run_boss_ve_process"]:
    m = re.search(rf'def {fn}\([^)]*\):', text)
    print(f"{fn}: {'FOUND' if m else 'NOT FOUND'}")

# Let's inspect Card D's helper functions
print("\n--- CARD D HELPERS ---")
for fn in ["_run_40_npc_team_and_char_position", "_run_40_npc_su_kien_tang", "_run_nhi_kieu_tang"]:
    m = re.search(rf'def {fn}\([^)]*\):', text)
    print(f"{fn}: {'FOUND' if m else 'NOT FOUND'}")

# Let's check Card B's helper functions
print("\n--- CARD B HELPERS ---")
for fn in ["_execute_card_E_for_mode", "_execute_card_B_phu_ban_doi"]:
    m = re.search(rf'def {fn}\([^)]*\):', text)
    print(f"{fn}: {'FOUND' if m else 'NOT FOUND'}")
