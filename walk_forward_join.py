import csv
from collections import defaultdict

with open(r"C:\Users\yasser\.gemini\antigravity\scratch\trading\optimization_log_es.csv", "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

def clean_row(r):
    res = {}
    for k in ['VwapDev2', 'MinBigTradeSize', 'MinStopPoints', 'BreakevenTrigger', 'NetProfit', 'GrossProfit', 'GrossLoss', 'ProfitFactor', 'TotalTrades', 'WinTrades', 'LossTrades', 'WinRate', 'Sharpe', 'Sortino']:
        try:
            res[k] = float(r.get(k, 0))
        except:
            res[k] = 0.0
    res['Instrument'] = r.get('Instrument', '')
    res['Timestamp'] = r.get('Timestamp', '')
    return res

jun_dict = {}
sep_dict = {}

for r in rows:
    c = clean_row(r)
    key = (round(c['VwapDev2'], 2), int(c['MinBigTradeSize']), round(c['MinStopPoints'], 1), round(c['BreakevenTrigger'], 1))
    inst = c['Instrument']
    if 'JUN26' in inst or '06-26' in inst:
        jun_dict[key] = c
    elif 'SEP26' in inst or '09-26' in inst:
        sep_dict[key] = c

print(f"Unique combinations in JUN26: {len(jun_dict)}")
print(f"Unique combinations in SEP26: {len(sep_dict)}")

# Evaluate SEP26 Top Performers
sep_runs = list(sep_dict.values())
sorted_sep = sorted(sep_runs, key=lambda x: (x['NetProfit'], x['Sharpe']), reverse=True)

print("\n=================================================================================")
print("                   TOP 10 ES 09-26 (Q3 SUMMER) BY NET PROFIT                     ")
print("=================================================================================")
header = f"{'Rank':<5} | {'VwapDev':<7} | {'Sweep':<5} | {'Stop':<5} | {'BE':<5} | {'NetProfit':<10} | {'PF':<5} | {'Trades':<6} | {'WR':<6} | {'Sharpe':<6}"
print(header)
print("-" * len(header))
for i, r in enumerate(sorted_sep[:10], 1):
    print(f"{i:<5} | {r['VwapDev2']:<7.2f} | {int(r['MinBigTradeSize']):<5} | {r['MinStopPoints']:<5.1f} | {r['BreakevenTrigger']:<5.1f} | ${r['NetProfit']:<9.2f} | {r['ProfitFactor']:<5.2f} | {int(r['TotalTrades']):<6} | {r['WinRate']:<5.1f}% | {r['Sharpe']:<6.2f}")

# Find overlapping combinations
matched = []
for key, s in sep_dict.items():
    if key in jun_dict:
        j = jun_dict[key]
        comb_net = j['NetProfit'] + s['NetProfit']
        comb_gp = j['GrossProfit'] + s['GrossProfit']
        comb_gl = abs(j['GrossLoss']) + abs(s['GrossLoss'])
        comb_pf = (comb_gp / comb_gl) if comb_gl > 0 else 99.0
        comb_trades = int(j['TotalTrades'] + s['TotalTrades'])
        comb_wins = int(j['WinTrades'] + s['WinTrades'])
        comb_wr = (comb_wins / comb_trades * 100) if comb_trades > 0 else 0.0
        
        matched.append({
            'key': key,
            'VwapDev2': key[0],
            'Sweep': key[1],
            'Stop': key[2],
            'BE': key[3],
            'CombNet': comb_net,
            'CombPF': comb_pf,
            'CombTrades': comb_trades,
            'CombWR': comb_wr,
            'JunNet': j['NetProfit'],
            'SepNet': s['NetProfit'],
            'JunWR': j['WinRate'],
            'SepWR': s['WinRate'],
            'JunSharpe': j['Sharpe'],
            'SepSharpe': s['Sharpe']
        })

print("\n=================================================================================")
print(f"      MULTI-QUARTER WALK-FORWARD JOIN (132 TRADING DAYS): {len(matched)} MATCHED RUNS       ")
print("=================================================================================")
sorted_comb = sorted(matched, key=lambda x: (x['CombNet'], x['CombPF']), reverse=True)

comb_header = f"{'Rank':<4} | {'Dev':<5} | {'Swp':<4} | {'Stp':<4} | {'BE':<4} | {'Comb PnL':<10} | {'Comb PF':<7} | {'Trades':<6} | {'Comb WR':<7} | {'Q2 Spring':<10} | {'Q3 Summer':<10}"
print(comb_header)
print("-" * len(comb_header))
for i, m in enumerate(sorted_comb[:15], 1):
    print(f"{i:<4} | {m['VwapDev2']:<5.2f} | {m['Sweep']:<4} | {m['Stop']:<4.1f} | {m['BE']:<4.1f} | ${m['CombNet']:<9.2f} | {m['CombPF']:<7.2f} | {m['CombTrades']:<6} | {m['CombWR']:<6.1f}% | ${m['JunNet']:<9.2f} | ${m['SepNet']:<9.2f}")

# Check dual-positive configurations
both_positive = [m for m in matched if m['JunNet'] > 0 and m['SepNet'] > 0]
print(f"\nTotal configurations profitable in BOTH Q2 Spring AND Q3 Summer: {len(both_positive)}")
if both_positive:
    print("\n--- DUAL-PROFITABLE CHAMPIONS ---")
    print(comb_header)
    print("-" * len(comb_header))
    for i, m in enumerate(sorted(both_positive, key=lambda x: x['CombNet'], reverse=True), 1):
        print(f"{i:<4} | {m['VwapDev2']:<5.2f} | {m['Sweep']:<4} | {m['Stop']:<4.1f} | {m['BE']:<4.1f} | ${m['CombNet']:<9.2f} | {m['CombPF']:<7.2f} | {m['CombTrades']:<6} | {m['CombWR']:<6.1f}% | ${m['JunNet']:<9.2f} | ${m['SepNet']:<9.2f}")
