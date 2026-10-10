import glob
import os

files = sorted(glob.glob(r"C:\Users\yasser\Documents\NinjaTrader 8\db\minute\ES 09-26\*.Last.ncd"))
print(f"Total minute files in ES 09-26: {len(files)}")
for f in files[:5]:
    print(os.path.basename(f), os.path.getsize(f), "bytes")
