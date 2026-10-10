import glob
import os
import struct

# Let's count trades and volume in October 2026 files
path = r"C:\Users\yasser\Documents\NinjaTrader 8\db\tick\NQ 12-26"
files = sorted(glob.glob(os.path.join(path, "202610*.Last.ncd")))

print(f"Total October files found: {len(files)}")
