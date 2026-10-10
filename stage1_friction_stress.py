import os
import math
from stitch_combined_7months import parse_trades

base_dir = os.path.dirname(os.path.abspath(__file__))
t_spring = parse_trades(os.path.join(base_dir, "trades_es06_combined.txt"), "Spring (ES 06-26)")
t_summer = parse_trades(os.path.join(base_dir, "trades_es09_combined.txt"), "Summer (ES 09-26)")
t_autumn = parse_trades(os.path.join(base_dir, "trades_es12_combined.txt"), "Autumn (ES 12-26)")

all_trades = t_spring + t_summer + t_autumn
q_order = {"Spring (ES 06-26)": 1, "Summer (ES 09-26)": 2, "Autumn (ES 12-26)": 3}
all_trades = sorted(all_trades, key=lambda x: (q_order[x['quarter']], x['entry_time']))

print(f"Total trades loaded: {len(all_trades)}")

# Standard CME futures round-turn commission for retail/institutional:
# 2 contracts * $4.20 / round-turn = $8.40 per trade
comm_per_trade = 8.40 

def evaluate_friction(additional_slippage_ticks, apply_commission):
    # On ES, 1 tick = 0.25 pts = $12.50 per contract.
    # For a 2-contract position with 2 fills (entry + exit),
    # each 1 tick of additional slippage costs: 2 contracts * 2 fills * $12.50 = $50.00 per trade!
    # Or if slippage is applied per round-trip tick (1 tick entry + 1 tick exit):
    # 2 contracts * 0.25 pts * $50/pt * 2 = $25/contract = $50/trade per tick of entry/exit slip.
    # Let's be rigorous and conservative:
    # 1 extra tick on entry + 1 extra tick on exit = 2 ticks total slippage per contract.
    # Cost per trade = additional_slippage_ticks * 2 contracts * $12.50 * 2 fills = additional_slippage_ticks * $50.00
    # Wait, usually "1 tick slippage" means 1 tick on entry (or 0.5 tick avg).
    # If Strategy Analyzer Slippage = 2 ticks: it applies 2 ticks adverse to entry price and 2 ticks adverse to exit price.
    # So additional 1 tick over baseline = 1 tick on entry ($25) + 1 tick on exit ($25) = $50 penalty per trade.
    
    cost_per_trade = (additional_slippage_ticks * 50.0) + (comm_per_trade if apply_commission else 0.0)
    
    adj_trades = []
    cum_pnl = 0.0
    peak_pnl = 0.0
    max_dd = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    wins = 0
    losses = 0
    scratches = 0
    
    for t in all_trades:
        adj_p = t['pnl'] - cost_per_trade
        cum_pnl += adj_p
        if adj_p > 0:
            gross_profit += adj_p
            wins += 1
        elif adj_p < 0:
            gross_loss += abs(adj_p)
            losses += 1
        else:
            scratches += 1
            
        if cum_pnl > peak_pnl:
            peak_pnl = cum_pnl
        dd = peak_pnl - cum_pnl
        if dd > max_dd:
            max_dd = dd
        adj_trades.append(adj_p)
        
    pf = (gross_profit / gross_loss) if gross_loss > 0 else 99.0
    wr = (wins / len(all_trades) * 100) if all_trades else 0
    
    # Sharpe
    mean_ret = sum(adj_trades) / len(adj_trades)
    var_ret = sum((r - mean_ret)**2 for r in adj_trades) / len(adj_trades)
    std_ret = math.sqrt(var_ret) if var_ret > 0 else 1.0
    sharpe = (mean_ret / std_ret) * math.sqrt(50.0) if std_ret > 0 else 0
    
    return {
        'net_pnl': cum_pnl,
        'gross_profit': gross_profit,
        'gross_loss': gross_loss,
        'pf': pf,
        'wins': wins,
        'losses': losses,
        'scratches': scratches,
        'wr': wr,
        'max_dd': max_dd,
        'sharpe': sharpe,
        'cost_per_trade': cost_per_trade,
        'total_friction': cost_per_trade * len(all_trades)
    }

scenarios = [
    ("Baseline (1-Tick Slip, $0 Comm)", 0, False),
    ("Real-World Standard (1-Tick Slip + $4.20/rt Comm)", 0, True),
    ("Stress Test 1: +1 Extra Tick Slip ($25/cnt) + Comm", 1, True),
    ("Stress Test 2: +2 Extra Ticks Slip ($50/cnt) + Comm", 2, True),
    ("Severe Stress: +3 Extra Ticks Slip ($75/cnt) + Comm", 3, True),
]

print("=" * 105)
print("             STAGE 1: MICROSTRUCTURE FRICTION & EXECUTION DRAG STRESS TEST            ")
print("                     (29 Trades Across 7 Continuous Macro Months)                     ")
print("=" * 105)
header = f"{'Scenario':<42} | {'Net PnL':<10} | {'PF':<5} | {'WinRate':<7} | {'Max DD':<8} | {'Sharpe':<6} | {'Total Drag':<10}"
print(header)
print("-" * len(header))

for name, add_slip, comm in scenarios:
    res = evaluate_friction(add_slip, comm)
    print(f"{name:<42} | ${res['net_pnl']:<9,.2f} | {res['pf']:<5.2f} | {res['wr']:<5.1f}% | -${res['max_dd']:<7,.2f} | {res['sharpe']:<6.2f} | -${res['total_friction']:<9,.2f}")

# Calculate exact breakeven slippage ticks
# Net PnL = $4,812.50 - 29 * (slip_ticks * 50 + 8.40) = 0
# slip_ticks * 50 = (4812.50 / 29) - 8.40 = 165.95 - 8.40 = 157.55
# slip_ticks = 157.55 / 50 = 3.15 extra ticks (or 4.15 total ticks per fill!)
be_slip = (4812.50 / len(all_trades) - comm_per_trade) / 50.0
print("-" * len(header))
print(f"Mathematical Slippage Ruin Threshold: +{be_slip:.2f} extra adverse ticks per trade (+{be_slip * 0.25:.2f} ES points).")
print("=" * 105)
