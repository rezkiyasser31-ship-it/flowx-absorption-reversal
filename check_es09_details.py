import glob
import os

path = r"C:\Users\yasser\Documents\NinjaTrader 8\db\tick\ES 09-26"
files = sorted(glob.glob(os.path.join(path, "*.Last.ncd")))
print(f"Total tick files: {len(files)}")
total_size = sum(os.path.getsize(f) for f in files)
print(f"Total size: {total_size / (1024*1024):.2f} MB")
