import os
import re

ui_files = [
    "modules/fund_flow_radar_ui.py",
    "modules/etf_weight_tracker_ui.py", 
    "modules/portfolio_health_ui.py",
    "modules/scenario_sandbox_ui.py",
    "modules/whale_correlation_ui.py",
    "modules/whale_investor_analytics_ui.py",
    "modules/whale_momentum_tracker_ui.py",
    "modules/etf_whale_linkage_ui.py",
    "modules/hedge_fund_activity_radar_ui.py",
    "modules/institutional_event_reaction_lab_ui.py"
]

key_counter = {}

for filepath in ui_files:
    if not os.path.exists(filepath):
        continue
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all st.button calls without key parameter
    pattern = r'(st\.button\([^)]*?)(\))'
    
    def add_key(match):
        button_call = match.group(1)
        if 'key=' in button_call:
            return match.group(0)  # Already has key
        
        # Extract button label
        label_match = re.search(r'"([^"]+)"', button_call)
        if label_match:
            label = label_match.group(1)
            # Create unique key from file and label
            file_name = os.path.basename(filepath).replace('.py', '').replace('_ui', '')
            key_base = f"{file_name}_{label}"
            
            # Make it unique
            if key_base not in key_counter:
                key_counter[key_base] = 0
            key_counter[key_base] += 1
            
            if key_counter[key_base] > 1:
                key = f"{key_base}_{key_counter[key_base]}"
            else:
                key = key_base
            
            key = re.sub(r'[^a-z0-9_]', '_', key.lower())
            return f'{button_call}, key="{key}")'
        
        return match.group(0)
    
    new_content = re.sub(pattern, add_key, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Fixed: {filepath}")

print("\n✅ All duplicate keys fixed!")
