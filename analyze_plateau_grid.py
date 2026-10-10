import csv
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(base_dir, "optimization_log_es.csv")) as f:
    rows = list(csv.reader(f))

# Header: Timestamp,Instrument,VwapDev2,MinBigTradeSize,MinStopPoints,BreakevenTrigger,MaxLosses,SweepRatio,NetProfit,GrossProfit,GrossLoss,ProfitFactor,TotalTrades,WinTrades,LossTrades,WinRate,Commission,Sharpe,Sortino

# Filter the 9 runs from 05:51
grid_runs = {}
for r in rows:
    if len(r) >= 19 and "2026-10-09 05:51" in r[0]:
        be = float(r[5])
        ratio = float(r[7])
        pnl = float(r[8])
        gp = float(r[9])
        gl = float(r[10])
        pf = float(r[11])
        trades = int(r[12])
        wr = float(r[15])
        grid_runs[(be, ratio)] = {
            'be': be, 'ratio': ratio, 'pnl': pnl, 'gp': gp, 'gl': gl,
            'pf': pf, 'trades': trades, 'wr': wr
        }

print(f"Total unique combinations captured: {len(grid_runs)}")

print("=" * 90)
print("             STAGE 2: PARAMETER CONVEXITY & PLATEAU MATRIX (3x3 GRID)                 ")
print("                     ES 06-26 (Spring 2026 | Full 67 Trading Days)                    ")
print("=" * 90)

ratios = [0.18, 0.20, 0.22]
bes = [3.0, 3.5, 4.0]

# Print Net Profit Table
print("\n--- NET PROFIT SURFACE ($) ---")
print(f"{'Breakeven Trigger':<20} | {'Ratio = 0.18':<20} | {'Ratio = 0.20 (Champion)':<24} | {'Ratio = 0.22':<20}")
print("-" * 90)
for be in bes:
    vals = []
    for r in ratios:
        entry = grid_runs.get((be, r))
        if entry:
            vals.append(f"${entry['pnl']:>9,.2f} ({entry['trades']} tr)")
        else:
            vals.append("N/A")
    print(f"BE = {be:<5.1f} pts          | {vals[0]:<20} | {vals[1]:<24} | {vals[2]:<20}")

# Print Profit Factor Table
print("\n--- PROFIT FACTOR SURFACE ---")
print(f"{'Breakeven Trigger':<20} | {'Ratio = 0.18':<20} | {'Ratio = 0.20 (Champion)':<24} | {'Ratio = 0.22':<20}")
print("-" * 90)
for be in bes:
    vals = []
    for r in ratios:
        entry = grid_runs.get((be, r))
        if entry:
            vals.append(f"PF: {entry['pf']:>5.2f} (WR: {entry['wr']:>4.1f}%)")
        else:
            vals.append("N/A")
    print(f"BE = {be:<5.1f} pts          | {vals[0]:<20} | {vals[1]:<24} | {vals[2]:<20}")

print("\n" + "=" * 90)
