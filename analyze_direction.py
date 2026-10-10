import os
from stitch_full_7months import parse_trades

base_dir = r"C:\Users\yasser\.gemini\antigravity\scratch\trading"
t_spring = parse_trades(os.path.join(base_dir, "trades_es06_300.txt"), "Spring")
t_summer = parse_trades(os.path.join(base_dir, "trades_es09_300.txt"), "Summer")
t_autumn = parse_trades(os.path.join(base_dir, "trades_es12_300.txt"), "Autumn")
all_t = t_spring + t_summer + t_autumn

longs = [t for t in all_t if t['dir'] == 'Long']
shorts = [t for t in all_t if t['dir'] == 'Short']

long_net = sum(t['pnl'] for t in longs)
short_net = sum(t['pnl'] for t in shorts)

print("=== LONGS ===")
print(f"Total: {len(longs)} trades | Net PnL: ${long_net:,.2f} | Wins: {len([t for t in longs if t['pnl']>0])} | Losses: {len([t for t in longs if t['pnl']<0])}")
for t in longs:
    print(f"  {t['quarter']:<8} | {t['entry_time']} | PnL: ${t['pnl']:>7.2f} | MAE: ${t['mae']:>6.2f} | MFE: ${t['mfe']:>6.2f}")

print("\n=== SHORTS ===")
print(f"Total: {len(shorts)} trades | Net PnL: ${short_net:,.2f} | Wins: {len([t for t in shorts if t['pnl']>0])} | Losses: {len([t for t in shorts if t['pnl']<0])}")
for t in shorts:
    print(f"  {t['quarter']:<8} | {t['entry_time']} | PnL: ${t['pnl']:>7.2f} | MAE: ${t['mae']:>6.2f} | MFE: ${t['mfe']:>6.2f}")
