import csv

with open(r"C:\Users\yasser\.gemini\antigravity\scratch\trading\optimization_log_es.csv", "r") as f:
    rows = list(csv.DictReader(f))

# Filter today's runs on ES DEC26
recent = [r for r in rows if r['Timestamp'].startswith('2026-10-08') and 'DEC26' in r['Instrument']]
print(f"Total recent runs on ES DEC26: {len(recent)}")

for r in recent:
    for k in ['VwapDev2', 'MinBigTradeSize', 'MinStopPoints', 'BreakevenTrigger', 'NetProfit', 'GrossProfit', 'GrossLoss', 'ProfitFactor', 'TotalTrades', 'WinTrades', 'LossTrades', 'WinRate', 'Sharpe']:
        try:
            r[k] = float(r[k])
        except:
            r[k] = 0.0

sorted_profit = sorted(recent, key=lambda x: (x['NetProfit'], x['Sharpe']), reverse=True)

print("\n--- TOP 15 CONFIGURATIONS BY NET PROFIT ---")
header = f"{'Rank':<4} | {'VwapDev':<7} | {'Sweep':<5} | {'MinStop':<7} | {'BE':<4} | {'Trades':<6} | {'WinRate':<7} | {'NetProfit':<10} | {'ProfitFactor':<12} | {'Sharpe':<6}"
print(header)
print("-" * len(header))
for i, r in enumerate(sorted_profit[:15], 1):
    print(f"{i:<4} | {r['VwapDev2']:7.2f} | {int(r['MinBigTradeSize']):5d} | {r['MinStopPoints']:7.2f} | {r['BreakevenTrigger']:4.1f} | {int(r['TotalTrades']):6d} | {r['WinRate']:6.1f}% | ${r['NetProfit']:9.2f} | {r['ProfitFactor']:12.2f} | {r['Sharpe']:6.2f}")

# Group by Sweep & Dev to identify the plateau
from collections import defaultdict
plateau = defaultdict(list)
for r in recent:
    plateau[(r['VwapDev2'], r['MinBigTradeSize'])].append(r)

print("\n--- PARAMETER PLATEAU SUMMARY ---")
print(f"{'VwapDev':<8} | {'Sweep':<6} | {'Avg Profit':<11} | {'Avg WinRate':<12} | {'Avg Sharpe':<11} | {'Total Configs':<13}")
print("-" * 75)
for (dev, sweep), config_list in sorted(plateau.items()):
    avg_prof = sum(c['NetProfit'] for c in config_list) / len(config_list)
    avg_wr = sum(c['WinRate'] for c in config_list) / len(config_list)
    avg_sh = sum(c['Sharpe'] for c in config_list) / len(config_list)
    print(f"{dev:8.2f} | {int(sweep):6d} | ${avg_prof:10.2f} | {avg_wr:10.1f}% | {avg_sh:10.2f} | {len(config_list):13d}")
