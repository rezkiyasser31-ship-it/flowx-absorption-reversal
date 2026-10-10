import os
from stitch_full_7months import parse_trades

base_dir = r"C:\Users\yasser\.gemini\antigravity\scratch\trading"
all_t = parse_trades(os.path.join(base_dir, "trades_es06_300.txt"), "Spring") + \
        parse_trades(os.path.join(base_dir, "trades_es09_300.txt"), "Summer") + \
        parse_trades(os.path.join(base_dir, "trades_es12_300.txt"), "Autumn")

print(f"{'#':<3} | {'Quarter':<7} | {'Entry Time':<14} | {'Exit Time':<14} | {'Dir':<5} | {'Entry':<8} | {'Exit':<8} | {'PnL ($)':<9} | {'MAE ($)':<8} | {'MFE ($)':<8}")
print("-" * 95)
for i, t in enumerate(all_t, 1):
    print(f"{i:<3} | {t['quarter'][:7]:<7} | {t['entry_time']:<14} | {t['exit_time']:<14} | {t['dir']:<5} | {t['entry_px']:<8.2f} | {t['exit_px']:<8.2f} | ${t['pnl']:<8.2f} | ${t['mae']:<7.2f} | ${t['mfe']:<7.2f}")
