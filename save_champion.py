import os
import shutil

src_path = r"C:\Users\yasser\Documents\NinjaTrader 8\bin\Custom\Strategies\FlowXAbsorptionReversal_ES.cs"
dst_path = r"C:\Users\yasser\Documents\NinjaTrader 8\bin\Custom\Strategies\FlowXAbsorptionReversal_ES_LowFreq.cs"

with open(src_path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("class FlowXAbsorptionReversal_ES :", "class FlowXAbsorptionReversal_ES_LowFreq :")
content = content.replace('Name								= "FlowXAbsorptionReversal_ES";', 'Name								= "FlowXAbsorptionReversal_ES_LowFreq";')
content = content.replace('"strategy": "FlowXAbsorptionReversal_ES"', '"strategy": "FlowXAbsorptionReversal_ES_LowFreq"')
content = content.replace("lock (typeof(FlowXAbsorptionReversal_ES))", "lock (typeof(FlowXAbsorptionReversal_ES_LowFreq))")

with open(dst_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Created FlowXAbsorptionReversal_ES_LowFreq.cs successfully!")

arch_dir = r"C:\Users\yasser\.gemini\antigravity\scratch\trading\low_freq_champion"
os.makedirs(arch_dir, exist_ok=True)
for f in ["trades_es06_adaptive.txt", "trades_es09_adaptive.txt", "trades_es12_adaptive.txt", "stitch_upgraded_7months.py"]:
    p = os.path.join(r"C:\Users\yasser\.gemini\antigravity\scratch\trading", f)
    if os.path.exists(p):
        shutil.copy2(p, os.path.join(arch_dir, f))
print("Archived low frequency setup files to:", arch_dir)
