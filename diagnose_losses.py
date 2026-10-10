with open(r"C:\Users\yasser\.gemini\antigravity\scratch\trading\latest_backtest_summary.txt", "r") as f:
    lines = f.readlines()

trades = []
for l in lines:
    if '|' in l and ('Short' in l or 'Long' in l):
        p = [x.strip() for x in l.split('|')]
        idx = int(p[0])
        entry_t = p[1]
        exit_t = p[2]
        direction = p[3]
        entry_px = float(p[4])
        exit_px = float(p[5])
        pnl = float(p[6].replace('$', '').replace(',', '').replace('(', '-').replace(')', ''))
        mae = float(p[7].replace('$', '').replace(',', ''))
        mfe = float(p[8].replace('$', '').replace(',', ''))
        trades.append({'idx': idx, 'entry_t': entry_t, 'dir': direction, 'pnl': pnl, 'mae': mae, 'mfe': mfe})

print(f"Total trades: {len(trades)}")
losses = [t for t in trades if t['pnl'] < 0]
wins = [t for t in trades if t['pnl'] > 0]

print(f"Total wins: {len(wins)}, Total losses: {len(losses)}")

# 1. Losses by direction
loss_long = [t for t in losses if t['dir'] == 'Long']
loss_short = [t for t in losses if t['dir'] == 'Short']
win_long = [t for t in wins if t['dir'] == 'Long']
win_short = [t for t in wins if t['dir'] == 'Short']

print(f"\nLongs:  {len(win_long)} wins (${sum(t['pnl'] for t in win_long):.2f}) | {len(loss_long)} losses (${sum(t['pnl'] for t in loss_long):.2f}) -> Net: ${sum(t['pnl'] for t in trades if t['dir']=='Long'):.2f}")
print(f"Shorts: {len(win_short)} wins (${sum(t['pnl'] for t in win_short):.2f}) | {len(loss_short)} losses (${sum(t['pnl'] for t in loss_short):.2f}) -> Net: ${sum(t['pnl'] for t in trades if t['dir']=='Short'):.2f}")

# 2. How many losses had significant MFE (profit)?
mfe_3pts = [t for t in losses if t['mfe'] >= 150]
mfe_5pts = [t for t in losses if t['mfe'] >= 250]
print(f"\nLosses with peak MFE >= 3.0 pts ($150): {len(mfe_3pts)} of {len(losses)}")
print(f"Losses with peak MFE >= 5.0 pts ($250): {len(mfe_5pts)} of {len(losses)}")

# 3. Analyze time-of-day for losses
from collections import defaultdict
hour_pnl = defaultdict(float)
hour_count = defaultdict(int)
for t in trades:
    hr = t['entry_t'].split()[1][:2]
    hour_pnl[hr] += t['pnl']
    hour_count[hr] += 1

print("\n--- Hourly Performance Breakdown ---")
for hr in sorted(hour_pnl.keys()):
    print(f"Hour {hr}: {hour_count[hr]:3d} trades | Net: ${hour_pnl[hr]:9.2f}")
