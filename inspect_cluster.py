import csv

with open(r"C:\Users\yasser\.gemini\antigravity\scratch\trading\optimization_log_es.csv", "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

for r in rows:
    for k in ['VwapDev2', 'MinBigTradeSize', 'MinStopPoints', 'BreakevenTrigger', 'NetProfit', 'GrossProfit', 'GrossLoss', 'ProfitFactor', 'TotalTrades', 'WinTrades', 'LossTrades', 'WinRate', 'Sharpe', 'Sortino']:
        try:
            r[k] = float(r[k])
        except:
            r[k] = 0.0

subset = [r for r in rows if r['VwapDev2'] in [2.0, 2.2, 2.4] and r['MinBigTradeSize'] in [200, 250, 300] and r['MinStopPoints'] == 5.0]
print(f"Total configurations in champion cluster: {len(subset)}")
print(f"{'Dev':<5} | {'Sweep':<5} | {'Stop':<5} | {'BE':<5} | {'NetProfit':<10} | {'PF':<5} | {'Trades':<6} | {'WR':<6} | {'Sharpe':<6}")
print("-" * 65)
for s in sorted(subset, key=lambda x: x['NetProfit'], reverse=True):
    print(f"{s['VwapDev2']:<5.2f} | {int(s['MinBigTradeSize']):<5} | {s['MinStopPoints']:<5.1f} | {s['BreakevenTrigger']:<5.1f} | ${s['NetProfit']:<9.2f} | {s['ProfitFactor']:<5.2f} | {int(s['TotalTrades']):<6} | {s['WinRate']:<5.1f}% | {s['Sharpe']:<5.2f}")
