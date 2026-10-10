import math
from stitch_combined_7months import parse_trades
import os

base_dir = os.path.dirname(os.path.abspath(__file__))
t_spring = parse_trades(os.path.join(base_dir, "trades_es06_combined.txt"), "Spring (ES 06-26)")
t_summer = parse_trades(os.path.join(base_dir, "trades_es09_combined.txt"), "Summer (ES 09-26)")
t_autumn = parse_trades(os.path.join(base_dir, "trades_es12_combined.txt"), "Autumn (ES 12-26)")
all_trades = t_spring + t_summer + t_autumn

returns = [t['pnl'] for t in all_trades]
wins = [r for r in returns if r > 0]
losses = [abs(r) for r in returns if r < 0]

win_rate = len(wins) / len(returns)
avg_win = sum(wins) / len(wins)
avg_loss = sum(losses) / len(losses)
win_loss_ratio = avg_win / avg_loss

# Full Kelly
# K = W - (1 - W) / R
kelly_full = win_rate - (1.0 - win_rate) / win_loss_ratio
kelly_half = kelly_full / 2.0
kelly_quarter = kelly_full / 4.0

print("=" * 85)
print("             STAGE 3: POSITION SIZING & CAPITAL ALLOCATION MODEL              ")
print("                     (Based on 29 Stitched Benchmark Trades)                  ")
print("=" * 85)
print(f"Empirical Win Rate (W)       : {win_rate * 100:.2f}%")
print(f"Average Win                  : ${avg_win:,.2f}")
print(f"Average Loss                 : ${avg_loss:,.2f}")
print(f"Win / Loss Payoff Ratio (R)  : {win_loss_ratio:.2f}")
print(f"Full Kelly Fraction          : {kelly_full * 100:.2f}% (Theoretical upper bound)")
print(f"Half Kelly Fraction          : {kelly_half * 100:.2f}% (Aggressive institutional)")
print(f"Quarter Kelly Fraction       : {kelly_quarter * 100:.2f}% (Recommended conservative)")
print("-" * 85)

# Capital requirements for ES (2 contracts, $50/pt)
# Max stop loss = 5.0 pts = $500 per trade
# Max DD historical = $550, MC 99% = $1,075
es_max_stop = 500.0
es_mc99_dd = 1075.0

print("\n--- RECOMMENDED ACCOUNT TIERS: E-MINI S&P 500 (ES) [2 CONTRACTS] ---")
tiers_es = [
    ("Conservative (1% Risk / Trade | DD < 4%)", 0.01, 50000.0),
    ("Institutional (2% Risk / Trade | DD < 7%)", 0.02, 25000.0),
    ("Aggressive Prop / Funded (3.3% Risk | DD < 11%)", 0.033, 15000.0),
    ("Minimum Safety Floor (5% Risk | DD < 18%)", 0.05, 10000.0),
]
for name, risk_pct, min_cap in tiers_es:
    dd_pct = (es_mc99_dd / min_cap) * 100
    print(f"{name:<45} : Min Capital: ${min_cap:>7,.0f} | 99% MC DD: {dd_pct:>4.1f}%")

print("\n--- RECOMMENDED ACCOUNT TIERS: MICRO E-MINI (MES) [2 CONTRACTS, 1/10th] ---")
tiers_mes = [
    ("Conservative (1% Risk / Trade | DD < 4%)", 0.01, 5000.0),
    ("Institutional (2% Risk / Trade | DD < 7%)", 0.02, 2500.0),
    ("Aggressive Prop / Funded (3.3% Risk | DD < 11%)", 0.033, 1500.0),
    ("Minimum Safety Floor (5% Risk | DD < 18%)", 0.05, 1000.0),
]
for name, risk_pct, min_cap in tiers_mes:
    dd_pct = ((es_mc99_dd / 10.0) / min_cap) * 100
    print(f"{name:<45} : Min Capital: ${min_cap:>7,.0f} | 99% MC DD: {dd_pct:>4.1f}%")
print("=" * 85)
