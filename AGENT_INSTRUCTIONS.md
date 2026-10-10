# ANTIGRAVITY AGENT ONBOARDING & CONTINUITY GUIDE
## Project: FlowX Institutional Order Flow Absorption Strategy
**Author:** Quantitative Trading Team  
**Audience:** Antigravity AI Assistant & Quantitative Engineers  
**Target Instruments:** E-mini S&P 500 (`ES`) & Micro E-mini S&P 500 (`MES`)  
**Platform:** NinjaTrader 8 (C# Engine / Tick Replay / Custom Indicators)  
**Status:** Stage 4 Active Live Forward Incubation  

---

## 1. Context & Mission for the Incoming Antigravity Agent

Welcome, Antigravity Agent. You are taking over a production-grade quantitative futures trading project. 

Your partner and their teammate have already spent extensive research cycles moving this project from a fragile retail concept to a **mathematically validated, institutional-grade order flow engine**.

**Your primary directive:**
1. **Preserve Quantitative Rigor:** Do NOT engage in curve-fitting (*p-hacking*) or subjective parameter tweaks.
2. **Understand the Full Architecture:** Know the history of every failure and breakthrough documented below before proposing changes.
3. **Assist the Partner with Setup & Live Monitoring:** Help the partner compile the code into NinjaTrader 8, configure their charts, and monitor the forward incubation on `Sim101` / `Sim strategytest`.

---

## 2. Chronological Project History (From Failure to Breakthrough)

### Phase 0: The NQ (Nasdaq-100) Experiment & Why It Failed
* **Initial Setup:** We started on `NQ` using a 3-pillar manual setup: VWAP $\pm 2.0\sigma$, BigTrades $\ge 75$ contracts, and CVD divergence.
* **The Failure:** While looking decent on a cherry-picked 3-week slice of Summer `NQ 09-26` (+64% WR), testing on October `NQ 12-26` degraded completely (*"Done, but it's trash"*).
* **The Microstructure Lesson:** NQ is a thin-book, momentum-driven market (5–15 contracts of resting liquidity per tick). When CTA momentum algos sweep the tape, passive limit orders get steamrolled; there is no real absorption. Tweaking parameters on 8 days of NQ was identified as blatant **p-hacking**.
* **The Strategic Pivot:** We pivoted to the **S&P 500 (`ES` / `MES`)**, where deep DOM depth (50–200+ contracts per tick) allows true institutional iceberg absorption to physically occur.

### Phase 1: Macro Multi-Semester Testing (7 Continuous Months / 154 Trading Days)
We acquired CME historical tick replay data across 3 macro semesters:
1. **Spring Semester (`ES 06-26`):** March 16 – June 12, 2026 (70 trading days)
2. **Summer Semester (`ES 09-26`):** June 15 – September 11, 2026 (63 trading days)
3. **Autumn Semester (`ES 12-26`):** September 14 – October 09, 2026 (21 trading days)

### Phase 2: The Static Baseline Curve-Fitting Trap
* The early static ES engine made +$3,000+ in Spring, but suffered a **-$900 drawdown in Autumn** and stagnated in Summer.
* **Why?**
  1. **Fixed Sweep Thresholds (`MinSweepFloor = 200–300`):** Failed because market volume participation shifts between summer and autumn.
  2. **Opening Momentum Whipsaws (09:30–10:30 EST):** False absorption signals into trend opens.

### Phase 3: The 5 Algorithmic Innovations (The Solution)
We upgraded the engine in `FlowXAbsorptionReversal_ES.cs` with 5 structural features:
1. **Adaptive Sweep Volume Ratio (`SweepVolumeRatio = 0.20`):** Threshold dynamically equals $\max(\text{MinSweepFloor}, \, 0.20 \times \text{SMA}_{20}(\text{Bar Volume}))$.
2. **Strict Delta Reversal (`StrictDeltaReversal = True`):** Prohibits entry unless candle delta confirms the reversal direction.
3. **Minimum Wick Geometry (`MinWickPoints = 0.75` / 3 ticks):** Guarantees price rejection before triggering.
4. **Prime Institutional Liquidity Window (10:30 AM to 2:00 PM EST / 17:00 to 20:30 chart time):** Eliminates opening whipsaws.
5. **Asymmetric Bracket:**
   * **Dynamic Wick-Anchored Stop Loss (5.0 to 6.0 pts):** Anchored 2 ticks beyond the tip of the absorption wick (`Math.Max(High[0], High[1]) + 2 ticks`), floored at 5.0 pts ($250) and capped at 6.0 pts ($300).
   * **Breakeven Trigger:** Exactly at +3.5 pts (+14 ticks), ratchets stop to **Entry + 1 tick (+0.25 pt)** to lock in a risk-free trade and cover CME round-turn commissions ($4.20).

---

## 3. Verified Benchmark Results (Do Not Break These Numbers)

Running `python stitch_combined_7months.py` produces the 7-month continuous benchmark:

```
Net Cumulative Profit:     $  4,812.50 (ES 1 Contract)
Gross Profit / Loss:       $  6,012.50 / -$1,200.00
Profit Factor:                    5.01
Total Trades:                       29 (19 Wins, 7 Losses, 3 Scratches)
Win Rate:                        65.5%
Max Peak-to-Trough DD:    -$    550.00
Annualized Sharpe:                3.91
Annualized Sortino:               8.86
1,000-Iteration Monte Carlo:      0.00% Risk of Ruin
```

### Quarter-by-Quarter Breakdown:
* **Q2 Spring (`ES 06-26`):** Net +$3,112.50 | PF: 6.19 | Win Rate: 76.9% (13 trades)
* **Q3 Summer (`ES 09-26`):** Net +$  212.50 | PF: 1.35 | Win Rate: 45.5% (11 trades)
* **Q4 Autumn (`ES 12-26`):** Net +$1,487.50 | PF: 99.0 | Win Rate: 80.0% (5 trades, $0 loss)

---

## 4. The 4-Stage Quantitative Validation Pipeline

1. **Stage 1: Friction & Slippage Stress Test (`python stage1_friction_stress.py`):**
   * Edge survives up to **+3.15 extra adverse ticks per trade (+0.79 ES points)**.
   * Double slippage + commissions retains **+$3,118.90 Net PnL** (PF: 2.71).
2. **Stage 2: Parameter Convexity & Plateau Matrix (`python analyze_plateau_grid.py`):**
   * Evaluated $3 \times 3$ grid (`BE: 3.0, 3.5, 4.0` $\times$ `Ratio: 0.18, 0.20, 0.22`).
   * **9 out of 9 cells are 100% net positive** (PF 1.04 to 6.52). Flat plateau between 0.20 and 0.22 confirms no curve-fitting.
3. **Stage 3: Capital Allocation Model (`python stage3_capital_sizing.py`):**
   * Empirical Payoff Ratio = 1.85:1, Win Rate = 65.52%.
   * Quarter-Kelly = 11.71%. Recommended capital: $25,000 for 2 ES contracts; $2,500 for 2 MES contracts.
4. **Stage 4: Live Forward Incubation Setup:**
   * Active on `Sim101` / `Sim strategytest` during the 10:30–14:00 EST window.

---

## 5. Critical Guidelines: What TO DO and What NOT TO DO

### 🚫 WHAT NOT TO DO (Mistakes We Solved):
1. **DO NOT arbitrarily tweak parameters for MES without backtest data:**
   * The team discussed changing `MinSweepFloor` from 150 to 50 for MES. The user correctly identified that changing it "just by mind" without empirical MES tick optimization violates quant principles. **Run the strategy on ES DEC26 for incubation**, or run a true multi-month optimization on MES tick data first.
2. **DO NOT change the Stop Loss to a static value:**
   * The stop loss is structurally anchored 2 ticks beyond the absorption wick, bounded between 5.0 and 6.0 points. Do not hardcode a flat 5.0 points.
3. **DO NOT trade outside the 10:30–14:00 EST window:**
   * Expanding the window into overnight Globex or the 09:30 open introduces momentum trend whipsaws.
4. **DO NOT allow more than 1 loss per day:**
   * `MaxLossesPerDay = 1` or `2` keeps drawdowns strictly bounded.

### ✅ WHAT TO DO:
1. **Verify Compilation:**
   * Run `compile.bat` to ensure `NinjaTrader.Custom.dll` compiles with **0 errors**.
2. **Deploy to NinjaTrader 8:**
   * Copy `strategies/FlowXAbsorptionReversal_ES.cs` to `Documents\NinjaTrader 8\bin\Custom\Strategies\`.
3. **Run Verification Scripts:**
   * Run `python stitch_combined_7months.py`, `python stage1_friction_stress.py`, and `python stage3_capital_sizing.py` to verify the local benchmark.

---

## 6. Repository File Layout

```
├── strategies/
│   ├── FlowXAbsorptionReversal_ES.cs           # Active Champion Engine (29 trades, PF 5.01)
│   └── FlowXAbsorptionReversal_ES_LowFreq.cs   # Conservative Model (14 trades, PF 8.02)
├── FLOWX_QUANTITATIVE_RESEARCH_REPORT_EN.md    # Complete English Quant Dossier
├── FLOWX_QUANTITATIVE_RESEARCH_REPORT_EN.html  # 1-Click PDF-Ready English Report
├── FLOWX_RAPPORT_DE_RECHERCHE_QUANTITATIVE_FR.md# Complete French Quant Dossier
├── FLOWX_RAPPORT_DE_RECHERCHE_QUANTITATIVE_FR.html# 1-Click PDF-Ready French Report
├── FLOWX_MANUAL_TRADING_PLAYBOOK.md            # Obsidian-Optimized Manual Execution Guide
├── stitch_combined_7months.py                  # 7-Month Continuous Stitched Engine
├── stage1_friction_stress.py                   # Microstructure Friction & Slippage Tester
├── stage3_capital_sizing.py                    # Kelly Criterion & Position Sizing Model
├── analyze_plateau_grid.py                     # 3x3 Parameter Convexity Matrix Script
├── compile.bat                                 # Headless NinjaTrader C# Compiler Script
├── trades_es*.txt                              # Raw 7-month trade audit logs
└── AGENT_INSTRUCTIONS.md                       # This File
```
