import csv

path = r"C:\Users\yasser\.gemini\antigravity\scratch\trading\optimization_log_es.csv"

rows = []
with open(path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        try:
            rows.append({
                "Timestamp": r.get("Timestamp"),
                "Instrument": r.get("Instrument"),
                "VwapDev2": float(r.get("VwapDev2", 0)),
                "MinBigTradeSize": int(r.get("MinBigTradeSize", 0)),
                "MinStopPoints": float(r.get("MinStopPoints", 0)),
                "BreakevenTrigger": float(r.get("BreakevenTrigger", 0)),
                "MaxLosses": int(r.get("MaxLosses", 0)),
                "NetProfit": float(r.get("NetProfit", 0)),
                "GrossProfit": float(r.get("GrossProfit", 0)),
                "GrossLoss": float(r.get("GrossLoss", 0)),
                "ProfitFactor": float(r.get("ProfitFactor", 0)),
                "TotalTrades": int(r.get("TotalTrades", 0)),
                "WinTrades": int(r.get("WinTrades", 0)),
                "LossTrades": int(r.get("LossTrades", 0)),
                "WinRate": float(r.get("WinRate", 0)),
                "Sharpe": float(r.get("Sharpe", 0)),
                "Sortino": float(r.get("Sortino", 0))
            })
        except Exception as e:
            pass

print(f"Total valid runs: {len(rows)}")

# Deduplicate identical parameter combinations (keeping latest)
unique_runs = {}
for r in rows:
    key = (r["VwapDev2"], r["MinBigTradeSize"], r["MinStopPoints"], r["BreakevenTrigger"])
    unique_runs[key] = r

runs = list(unique_runs.values())
print(f"Total unique combinations: {len(runs)}")

# Sort by Net Profit descending
sorted_by_profit = sorted(runs, key=lambda x: x["NetProfit"], reverse=True)

header = f"{'Rank':<5} | {'VwapDev2':<8} | {'SweepSz':<7} | {'StopPts':<7} | {'BE_Trig':<7} | {'NetProfit':<11} | {'PF':<6} | {'Trades':<6} | {'WinRate':<7} | {'Sharpe':<6}"
print("\n--- TOP 15 ES CONFIGURATIONS BY NET PROFIT ---")
print(header)
print("-" * len(header))
for i, r in enumerate(sorted_by_profit[:15]):
    print(f"{i+1:<5} | {r['VwapDev2']:<8.2f} | {r['MinBigTradeSize']:<7} | {r['MinStopPoints']:<7.1f} | {r['BreakevenTrigger']:<7.1f} | ${r['NetProfit']:<10.2f} | {r['ProfitFactor']:<6.2f} | {r['TotalTrades']:<6} | {r['WinRate']:<6.1f}% | {r['Sharpe']:<6.2f}")

# Filter for min 5 trades and sort by Profit Factor
min_trades = [r for r in runs if r["TotalTrades"] >= 5]
sorted_by_pf = sorted(min_trades, key=lambda x: (x["ProfitFactor"], x["NetProfit"]), reverse=True)

print("\n--- TOP 10 ES CONFIGURATIONS BY PROFIT FACTOR (>= 5 Trades) ---")
print(header)
print("-" * len(header))
for i, r in enumerate(sorted_by_pf[:10]):
    print(f"{i+1:<5} | {r['VwapDev2']:<8.2f} | {r['MinBigTradeSize']:<7} | {r['MinStopPoints']:<7.1f} | {r['BreakevenTrigger']:<7.1f} | ${r['NetProfit']:<10.2f} | {r['ProfitFactor']:<6.2f} | {r['TotalTrades']:<6} | {r['WinRate']:<6.1f}% | {r['Sharpe']:<6.2f}")

# Filter for min 8 trades
min_trades_8 = [r for r in runs if r["TotalTrades"] >= 8]
if min_trades_8:
    sorted_by_8 = sorted(min_trades_8, key=lambda x: x["NetProfit"], reverse=True)
    print("\n--- TOP CONFIGURATIONS WITH HIGHEST SAMPLE SIZE (>= 8 Trades) ---")
    print(header)
    print("-" * len(header))
    for i, r in enumerate(sorted_by_8[:10]):
        print(f"{i+1:<5} | {r['VwapDev2']:<8.2f} | {r['MinBigTradeSize']:<7} | {r['MinStopPoints']:<7.1f} | {r['BreakevenTrigger']:<7.1f} | ${r['NetProfit']:<10.2f} | {r['ProfitFactor']:<6.2f} | {r['TotalTrades']:<6} | {r['WinRate']:<6.1f}% | {r['Sharpe']:<6.2f}")
