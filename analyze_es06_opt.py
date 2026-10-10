import csv

with open(r"C:\Users\yasser\.gemini\antigravity\scratch\trading\optimization_log_es.csv", "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

# Filter ES 06-26 runs
es06_runs = [r for r in rows if '06-26' in r.get('Instrument', '') or 'JUN26' in r.get('Instrument', '')]
print(f"Total runs logged for ES 06-26: {len(es06_runs)}")

if not es06_runs:
    # Check latest runs from today
    today_runs = [r for r in rows if '2026-10-08 14:' in r.get('Timestamp', '') or '2026-10-08 13:' in r.get('Timestamp', '') or '2026-10-08 02:' in r.get('Timestamp', '')]
    print(f"Latest runs: {len(today_runs)}")
    if today_runs:
        print("Sample latest instrument:", today_runs[0].get('Instrument'))
        es06_runs = today_runs

# Convert numeric columns
for r in es06_runs:
    for k in ['VwapDev2', 'MinBigTradeSize', 'MinStopPoints', 'BreakevenTrigger', 'NetProfit', 'GrossProfit', 'GrossLoss', 'ProfitFactor', 'TotalTrades', 'WinTrades', 'LossTrades', 'WinRate', 'Sharpe', 'Sortino']:
        try:
            r[k] = float(r[k])
        except:
            r[k] = 0.0

# Deduplicate
unique_runs = {}
for r in es06_runs:
    key = (r['VwapDev2'], r['MinBigTradeSize'], r['MinStopPoints'], r['BreakevenTrigger'])
    unique_runs[key] = r

runs = list(unique_runs.values())
print(f"Total unique combinations: {len(runs)}")

# Sort by Net Profit descending
sorted_by_profit = sorted(runs, key=lambda x: (x['NetProfit'], x['Sharpe']), reverse=True)

header = f"{'Rank':<5} | {'VwapDev2':<8} | {'SweepSz':<7} | {'StopPts':<7} | {'BE_Trig':<7} | {'NetProfit':<12} | {'PF':<6} | {'Trades':<6} | {'WinRate':<7} | {'Sharpe':<6}"
print("\n--- TOP 15 ES 06-26 CONFIGURATIONS BY NET PROFIT ---")
print(header)
print("-" * len(header))
for i, r in enumerate(sorted_by_profit[:15], 1):
    print(f"{i:<5} | {r['VwapDev2']:<8.2f} | {int(r['MinBigTradeSize']):<7} | {r['MinStopPoints']:<7.1f} | {r['BreakevenTrigger']:<7.1f} | ${r['NetProfit']:<11.2f} | {r['ProfitFactor']:<6.2f} | {int(r['TotalTrades']):<6} | {r['WinRate']:<6.1f}% | {r['Sharpe']:<6.2f}")

# Filter for min trades >= 10
min_10 = [r for r in runs if r['TotalTrades'] >= 10]
if min_10:
    sorted_10 = sorted(min_10, key=lambda x: (x['ProfitFactor'], x['NetProfit']), reverse=True)
    print("\n--- TOP CONFIGURATIONS (>= 10 TRADES) BY PROFIT FACTOR ---")
    print(header)
    print("-" * len(header))
    for i, r in enumerate(sorted_10[:10], 1):
        print(f"{i:<5} | {r['VwapDev2']:<8.2f} | {int(r['MinBigTradeSize']):<7} | {r['MinStopPoints']:<7.1f} | {r['BreakevenTrigger']:<7.1f} | ${r['NetProfit']:<11.2f} | {r['ProfitFactor']:<6.2f} | {int(r['TotalTrades']):<6} | {r['WinRate']:<6.1f}% | {r['Sharpe']:<6.2f}")

# Group by VwapDev2 and MinBigTradeSize to map out the plateau
from collections import defaultdict
plateau = defaultdict(list)
for r in runs:
    plateau[(r['VwapDev2'], r['MinBigTradeSize'])].append(r)

print("\n--- PARAMETER PLATEAU MAP (Q2 SPRING: 67 TRADING DAYS) ---")
print(f"{'VwapDev':<8} | {'Sweep':<6} | {'Avg Profit':<12} | {'Avg WinRate':<12} | {'Avg Trades':<11} | {'Avg PF':<8} | {'Avg Sharpe':<11}")
print("-" * 80)
for (dev, sweep), cl in sorted(plateau.items()):
    avg_p = sum(c['NetProfit'] for c in cl) / len(cl)
    avg_wr = sum(c['WinRate'] for c in cl) / len(cl)
    avg_tr = sum(c['TotalTrades'] for c in cl) / len(cl)
    avg_pf = sum(c['ProfitFactor'] for c in cl) / len(cl)
    avg_sh = sum(c['Sharpe'] for c in cl) / len(cl)
    print(f"{dev:8.2f} | {int(sweep):6d} | ${avg_p:11.2f} | {avg_wr:10.1f}% | {avg_tr:10.1f} | {avg_pf:8.2f} | {avg_sh:10.2f}")
