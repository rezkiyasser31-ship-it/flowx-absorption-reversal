import os
import random
import math

def parse_trades(file_path, quarter_name):
    trades = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if '|' in line and ('Long' in line or 'Short' in line):
                parts = [p.strip() for p in line.split('|')]
                idx = int(parts[0])
                entry_time = parts[1]
                exit_time = parts[2]
                direction = parts[3]
                entry_px = float(parts[4])
                exit_px = float(parts[5])
                pnl_str = parts[6].replace('$', '').replace(',', '').replace('(', '-').replace(')', '').strip()
                pnl = float(pnl_str)
                mae_str = parts[7].replace('$', '').replace(',', '').strip()
                mfe_str = parts[8].replace('$', '').replace(',', '').strip()
                mae = float(mae_str) if mae_str else 0.0
                mfe = float(mfe_str) if mfe_str else 0.0
                trades.append({
                    'quarter': quarter_name,
                    'idx': idx,
                    'entry_time': entry_time,
                    'exit_time': exit_time,
                    'dir': direction,
                    'entry_px': entry_px,
                    'exit_px': exit_px,
                    'pnl': pnl,
                    'mae': mae,
                    'mfe': mfe
                })
    return trades

base_dir = os.path.dirname(os.path.abspath(__file__))
t_spring = parse_trades(os.path.join(base_dir, "trades_es06_combined.txt"), "Spring (ES 06-26)")
t_summer = parse_trades(os.path.join(base_dir, "trades_es09_combined.txt"), "Summer (ES 09-26)")
t_autumn = parse_trades(os.path.join(base_dir, "trades_es12_combined.txt"), "Autumn (ES 12-26)")

all_trades = t_spring + t_summer + t_autumn
print(f"Total Combined stitched trades: {len(all_trades)}")

q_order = {"Spring (ES 06-26)": 1, "Summer (ES 09-26)": 2, "Autumn (ES 12-26)": 3}
all_trades = sorted(all_trades, key=lambda x: (q_order[x['quarter']], x['entry_time']))

cum_pnl = 0.0
peak_pnl = 0.0
max_dd = 0.0

gross_profit = 0.0
gross_loss = 0.0
wins = 0
losses = 0
scratches = 0

for i, t in enumerate(all_trades, 1):
    p = t['pnl']
    cum_pnl += p
    if p > 0:
        gross_profit += p
        wins += 1
    elif p < 0:
        gross_loss += abs(p)
        losses += 1
    else:
        scratches += 1
        
    if cum_pnl > peak_pnl:
        peak_pnl = cum_pnl
    dd = peak_pnl - cum_pnl
    if dd > max_dd:
        max_dd = dd
    t['cum_pnl'] = cum_pnl
    t['dd'] = dd

total_trades = len(all_trades)
win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
pf = (gross_profit / gross_loss) if gross_loss > 0 else 99.0

returns = [t['pnl'] for t in all_trades]
mean_ret = sum(returns) / len(returns)
var_ret = sum((r - mean_ret)**2 for r in returns) / len(returns)
std_ret = math.sqrt(var_ret) if var_ret > 0 else 1.0

downside_returns = [min(0, r) for r in returns]
var_down = sum(r**2 for r in downside_returns) / len(downside_returns)
std_down = math.sqrt(var_down) if var_down > 0 else 1.0

annual_trades = 50.0
sharpe = (mean_ret / std_ret) * math.sqrt(annual_trades) if std_ret > 0 else 0
sortino = (mean_ret / std_down) * math.sqrt(annual_trades) if std_down > 0 else 0

print("=" * 95)
print("       COMBINED REFINEMENT ENGINE: 7-MONTH CONTINUOUS STITCHED REPORT (2.0-Sigma | 17:00-20:30)    ")
print("                     (03/16/2026 to 10/09/2026 | 154 Trading Days)                   ")
print("=" * 95)
print(f"Net Cumulative Profit:     ${cum_pnl:>10,.2f}")
print(f"Gross Profit:              ${gross_profit:>10,.2f}")
print(f"Gross Loss:               -${gross_loss:>10,.2f}")
print(f"Profit Factor:              {pf:>10.2f}")
print(f"Total Trades:               {total_trades:>10d} (Wins: {wins}, Losses: {losses}, Scratches: {scratches})")
print(f"Win Rate:                   {win_rate:>9.1f}%")
print(f"Peak-to-Trough Max DD:    -${max_dd:>10,.2f}")
print(f"Annualized Sharpe Ratio:    {sharpe:>10.2f}")
print(f"Annualized Sortino Ratio:   {sortino:>10.2f}")
print("-" * 95)

print("\n--- PERFORMANCE BREAKDOWN BY SEMESTER / QUARTER ---")
for q_name, q_trades in [("Q2 Spring (ES 06-26)", t_spring), ("Q3 Summer (ES 09-26)", t_summer), ("Q4 Autumn (ES 12-26)", t_autumn)]:
    q_pnl = sum(t['pnl'] for t in q_trades)
    q_wins = sum(1 for t in q_trades if t['pnl'] > 0)
    q_losses = sum(1 for t in q_trades if t['pnl'] < 0)
    q_scr = sum(1 for t in q_trades if t['pnl'] == 0)
    q_gp = sum(t['pnl'] for t in q_trades if t['pnl'] > 0)
    q_gl = abs(sum(t['pnl'] for t in q_trades if t['pnl'] < 0))
    q_pf = (q_gp / q_gl) if q_gl > 0 else 99.0
    q_wr = (q_wins / len(q_trades) * 100) if q_trades else 0
    print(f"{q_name:<25}: Net PnL: ${q_pnl:>9,.2f} | PF: {q_pf:>5.2f} | WinRate: {q_wr:>5.1f}% | Trades: {len(q_trades):>2} (W: {q_wins}, L: {q_losses}, BE: {q_scr})")

print("\n" + "=" * 95)
print("                              COMPLETE 7-MONTH TRADE LOG                              ")
print("=" * 95)
log_header = f"{'#':<3} | {'Quarter':<8} | {'Entry Time':<14} | {'Exit Time':<14} | {'Dir':<5} | {'Entry':<8} | {'Exit':<8} | {'PnL ($)':<9} | {'Cum PnL':<10} | {'Drawdown':<9}"
print(log_header)
print("-" * len(log_header))
for i, t in enumerate(all_trades, 1):
    q_short = "Spring" if "Spring" in t['quarter'] else ("Summer" if "Summer" in t['quarter'] else "Autumn")
    print(f"{i:<3} | {q_short:<8} | {t['entry_time']:<14} | {t['exit_time']:<14} | {t['dir']:<5} | {t['entry_px']:<8.2f} | {t['exit_px']:<8.2f} | ${t['pnl']:<8.2f} | ${t['cum_pnl']:<9.2f} | -${t['dd']:<8.2f}")

# 1,000 MONTE CARLO SIMULATIONS
random.seed(42)
mc_sims = 1000
mc_drawdowns = []
mc_profits = []
ruin_count = 0
starting_capital = 15000.0

for s in range(mc_sims):
    shuffled = returns.copy()
    random.shuffle(shuffled)
    sim_equity = starting_capital
    sim_peak = starting_capital
    sim_max_dd = 0.0
    ruined = False
    for r in shuffled:
        sim_equity += r
        if sim_equity <= (starting_capital * 0.5):
            ruined = True
        if sim_equity > sim_peak:
            sim_peak = sim_equity
        cur_dd = sim_peak - sim_equity
        if cur_dd > sim_max_dd:
            sim_max_dd = cur_dd
    mc_drawdowns.append(sim_max_dd)
    mc_profits.append(sim_equity - starting_capital)
    if ruined:
        ruin_count += 1

mc_drawdowns.sort()
dd_50 = mc_drawdowns[int(mc_sims * 0.50)]
dd_95 = mc_drawdowns[int(mc_sims * 0.95)]
dd_99 = mc_drawdowns[int(mc_sims * 0.99)]

print("\n" + "=" * 95)
print("             1,000-ITERATION MONTE CARLO STRESS TEST (COMBINED REFINEMENT)            ")
print("=" * 95)
print(f"Median Expected Drawdown (50th percentile) :  -${dd_50:,.2f}")
print(f"95% Confidence Maximum Drawdown            :  -${dd_95:,.2f}")
print(f"99% Tail-Risk Maximum Drawdown             :  -${dd_99:,.2f}")
print(f"Probability of Ruin (Account Half-Life)    :   {(ruin_count / mc_sims * 100):.2f}%")
print("=" * 95)
