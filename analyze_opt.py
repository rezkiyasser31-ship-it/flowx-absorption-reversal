import csv

path = r"C:\Users\yasser\.gemini\antigravity\scratch\trading\optimization_log.csv"

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

# Sort by NetProfit descending
rows_by_profit = sorted(rows, key=lambda x: x["NetProfit"], reverse=True)

print("\n--- TOP 10 CONFIGURATIONS BY NET PROFIT ---")
header = f"{'Rank':<5} | {'VwapDev2':<8} | {'SweepSz':<7} | {'BE_Trig':<7} | {'MaxLoss':<7} | {'NetProfit':<11} | {'PF':<6} | {'Trades':<6} | {'WinRate':<7} | {'Sharpe':<6}"
print(header)
print("-" * len(header))
for i, r in enumerate(rows_by_profit[:15]):
    print(f"{i+1:<5} | {r['VwapDev2']:<8.2f} | {r['MinBigTradeSize']:<7} | {r['BreakevenTrigger']:<7.1f} | {r['MaxLosses']:<7} | ${r['NetProfit']:<10.2f} | {r['ProfitFactor']:<6.2f} | {r['TotalTrades']:<6} | {r['WinRate']:<6.1f}% | {r['Sharpe']:<6.2f}")

# Sort by ProfitFactor descending (min 3 trades)
valid_pf = [r for r in rows if r["TotalTrades"] >= 3]
rows_by_pf = sorted(valid_pf, key=lambda x: x["ProfitFactor"], reverse=True)

print("\n--- TOP 10 CONFIGURATIONS BY PROFIT FACTOR (>=3 Trades) ---")
print(header)
print("-" * len(header))
for i, r in enumerate(rows_by_pf[:10]):
    print(f"{i+1:<5} | {r['VwapDev2']:<8.2f} | {r['MinBigTradeSize']:<7} | {r['BreakevenTrigger']:<7.1f} | {r['MaxLosses']:<7} | ${r['NetProfit']:<10.2f} | {r['ProfitFactor']:<6.2f} | {r['TotalTrades']:<6} | {r['WinRate']:<6.1f}% | {r['Sharpe']:<6.2f}")
