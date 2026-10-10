import glob
import os

files = sorted(glob.glob(r"C:\Users\yasser\Documents\NinjaTrader 8\db\tick\ES 09-26\*.Last.ncd"))
print(f"Total tick files in ES 09-26: {len(files)}")
if files:
    print("First 5 files:")
    for f in files[:5]:
        print(" ", os.path.basename(f), os.path.getsize(f), "bytes")
    print("Last 5 files:")
    for f in files[-5:]:
        print(" ", os.path.basename(f), os.path.getsize(f), "bytes")
