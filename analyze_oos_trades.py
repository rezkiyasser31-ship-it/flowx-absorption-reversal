import csv

with open(r"C:\Users\yasser\.gemini\antigravity\scratch\trading\latest_backtest_summary.txt", "r") as f:
    lines = f.readlines()

trade_lines = [l for l in lines if '|' in l and ('Short' in l or 'Long' in l)]
print(f"Total trades parsed: {len(trade_lines)}")

# Parse each trade
trades = []
for l in trade_lines:
    parts = [p.strip() for p in l.split('|')]
    if len(parts) >= 9:
        idx = int(parts[0])
        entry_time = parts[1]
        exit_time = parts[2]
        direction = parts[3]
        entry_px = float(parts[4])
        exit_px = float(parts[5])
        pnl_str = parts[6].replace('$', '').replace(',', '').replace('(', '-').replace(')', '')
        pnl = float(pnl_str)
        mae = float(parts[7].replace('$', '').replace(',', ''))
        mfe = float(parts[8].replace('$', '').replace(',', ''))
        trades.append({
            'idx': idx, 'entry_time': entry_time, 'direction': direction,
            'pnl': pnl, 'mae': mae, 'mfe': mfe
        })

wins = [t for t in trades if t['pnl'] > 0]
losses = [t for t in trades if t['pnl'] < 0]
breakevens = [t for t in trades if t['pnl'] == 0]

print(f"Wins: {len(wins)} (Sum: ${sum(t['pnl'] for t in wins):.2f}, Avg: ${sum(t['pnl'] for t in wins)/len(wins):.2f})")
print(f"Losses: {len(losses)} (Sum: ${sum(t['pnl'] for t in losses):.2f}, Avg: ${sum(t['pnl'] for t in losses)/len(losses):.2f})")
print(f"BE: {len(breakevens)}")

# Analyze MFE on losing trades
print("\n--- MFE on Losing Trades ---")
losses_with_profit = [t for t in losses if t['mfe'] >= 175] # Had at least 3.5 points in profit!
print(f"Losses that were in profit by >= $175 (3.5 pts): {len(losses_with_profit)} of {len(losses)}")
for t in losses_with_profit:
    print(f"  Trade {t['idx']}: {t['entry_time']} {t['direction']} PnL: ${t['pnl']} (Peak MFE: ${t['mfe']})")

# Analyze by Direction
longs = [t for t in trades if t['direction'] == 'Long']
shorts = [t for t in trades if t['direction'] == 'Short']
long_pnl = sum(t['pnl'] for t in longs)
short_pnl = sum(t['pnl'] for t in shorts)
print(f"\nLongs:  {len(longs)} trades, PnL: ${long_pnl:.2f}, WinRate: {len([t for t in longs if t['pnl']>0])/len(longs)*100:.1f}%")
print(f"Shorts: {len(shorts)} trades, PnL: ${short_pnl:.2f}, WinRate: {len([t for t in shorts if t['pnl']>0])/len(shorts)*100:.1f}%")
