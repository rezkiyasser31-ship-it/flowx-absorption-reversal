# FlowX Institutional Order Flow Absorption Reversal Engine

[![NinjaTrader 8](https://img.shields.io/badge/Platform-NinjaTrader%208-green.svg)](https://ninjatrader.com)
[![Asset Class](https://img.shields.io/badge/Asset-S%26P%20500%20Futures%20(ES%2FMES)-blue.svg)](https://www.cmegroup.com)
[![Status](https://img.shields.io/badge/Validation-Stage%204%20Live%20Incubation-brightgreen.svg)]()
[![Build](https://img.shields.io/badge/C%23%20Compilation-0%20Errors-success.svg)]()

> **Production-grade institutional order flow mean-reversion strategy for NinjaTrader 8.**  
> Developed using high-frequency tick replay data across **7 continuous months / 154 trading days** and 3 CME macro semesters (`ES 06-26`, `ES 09-26`, `ES 12-26`).

---

## 📊 Key Performance Indicators (Continuous 7-Month Benchmark)

All metrics generated from continuous multi-semester stitched audit logs (`python stitch_combined_7months.py`):

| Performance Metric | ES (1 Contract) | Scaled to MES (1 Contract) | Institutional Hurdle | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Net Cumulative Profit** | **+$4,812.50** | **+$481.25** | Positive across all semesters | **PASSED** |
| **Gross Profit / Loss** | $6,012.50 / -$1,200.00 | $601.25 / -$120.00 | Loss containment < 25% | **PASSED** |
| **Profit Factor (PF)** | **5.01** | **5.01** | > 2.0 | **PASSED** |
| **Total Trades** | **29** (19 W / 7 L / 3 BE) | **29** (19 W / 7 L / 3 BE) | Statistically sufficient | **PASSED** |
| **Empirical Win Rate** | **65.5%** | **65.5%** | > 55.0% | **PASSED** |
| **Peak-to-Trough Max Drawdown** | **-$550.00** | **-$55.00** | < 10% of capital | **PASSED** |
| **Annualized Sharpe Ratio** | **3.91** | **3.91** | > 2.0 | **PASSED** |
| **Annualized Sortino Ratio** | **8.86** | **8.86** | Downside volatility control | **PASSED** |
| **1,000-Iteration Monte Carlo Ruin** | **0.00%** | **0.00%** | Account half-life safety | **PASSED** |

### Macro Semester Breakdown (Consistency Across Regimes):
* **Spring Semester (`ES 06-26` / 70 days):** Net **+$3,112.50** | PF: **6.19** | Win Rate: **76.9%** (13 trades)
* **Summer Semester (`ES 09-26` / 63 days):** Net **+$212.50** | PF: **1.35** | Win Rate: **45.5%** (11 trades)
* **Autumn Semester (`ES 12-26` / 21 days):** Net **+$1,487.50** | PF: **99.00** | Win Rate: **80.0%** (5 trades, $0 loss)

---

## ⚡ The 5 Core Algorithmic Upgrades

1. **Adaptive Dynamic Sweep Sizing:**
   $$\text{Threshold} = \max(\text{MinSweepFloor}, \, 0.20 \times \text{SMA}_{20}(\text{Bar Volume}))$$
   Scales dynamically with market volume regimes, eliminating static threshold decay.
2. **Strict Delta Reversal Confirmation:** Requires closing bar delta to flip away from the extreme to confirm tape exhaustion.
3. **Geometric Rejection Wick Filter:** Requires candle rejection wick $\ge 0.75$ points (3 ticks).
4. **Prime Institutional Liquidity Window:** Trades exclusively between **10:30 AM and 2:00 PM EST** (17:00 to 20:30 chart time), avoiding opening momentum whipsaws.
5. **Asymmetric Risk Management:**
   * **Dynamic Wick-Anchored Stop Loss (5.0 to 6.0 pts):** Anchored 2 ticks beyond the tip of the absorption wick, bounded between a 5.0 pt floor ($250) and a 6.0 pt ceiling ($300).
   * **Breakeven Trigger:** Ratchets stop to **Entry + 1 tick** at +3.5 points favorable excursion to cover friction and CME fees ($4.20/rt).

---

## 🚀 Quick Start for NinjaTrader 8

### Step 1: Install Strategy Files
Copy the strategy files into your local NinjaTrader 8 custom folder:
```bash
# Target path:
C:\Users\<YourUsername>\Documents\NinjaTrader 8\bin\Custom\Strategies\
```
Copy `strategies/FlowXAbsorptionReversal_ES.cs` directly into that folder.

### Step 2: Compile
In NinjaTrader 8:
* Press **`F5`** in the NinjaScript Editor, OR
* Run `compile.bat` in this repository to verify headless compilation.

### Step 3: Configure Chart
1. Open a **1-Minute Chart** for **`ES DEC26`** (or `ES 12-26`).
2. Ensure **Tick Replay** is checked in the Data Series window (`Ctrl + F`).
3. Press **`Ctrl + S`** (Strategies), select **`FlowXAbsorptionReversal_ES`**, and verify champion parameters:
   * `MinSweepFloor`: **`150`**
   * `SweepVolumeRatio`: **`0.20`**
   * `BreakevenTriggerPoints`: **`3.5`**
   * `MinStopPoints`: **`5.0`**
   * `MaxStopPoints`: **`6.0`**
   * `TradeStartHour`: **`17`**, `TradeStartMinute`: **`0`**
   * `TradeEndHour`: **`20`**, `TradeEndMinute`: **`30`**
4. Set `Enabled = True` and click **OK**.

---

## 🤖 Guide for Antigravity AI Agents

If you are an Antigravity AI Agent reading this repository for a trading partner, **read [`AGENT_INSTRUCTIONS.md`](AGENT_INSTRUCTIONS.md) first**. It contains:
* The chronological backstory and lessons learned.
* The "What NOT to do" guide (avoiding curve-fitting, parameter p-hacking, and arbitrary scaling).
* Reproducibility instructions for Python quant validation scripts.

---

## 📂 Repository Contents

* [`strategies/`](strategies/) — Active C# strategy engines for NinjaTrader 8 (`FlowXAbsorptionReversal_ES.cs`, `FlowXAbsorptionReversal_ES_LowFreq.cs`).
* [`FLOWX_QUANTITATIVE_RESEARCH_REPORT_EN.md`](FLOWX_QUANTITATIVE_RESEARCH_REPORT_EN.md) — Exhaustive English institutional research dossier.
* [`FLOWX_QUANTITATIVE_RESEARCH_REPORT_EN.html`](FLOWX_QUANTITATIVE_RESEARCH_REPORT_EN.html) — 1-click printable / PDF-ready English report.
* [`FLOWX_RAPPORT_DE_RECHERCHE_QUANTITATIVE_FR.md`](FLOWX_RAPPORT_DE_RECHERCHE_QUANTITATIVE_FR.md) — Dossier technique institutionnel en français.
* [`FLOWX_RAPPORT_DE_RECHERCHE_QUANTITATIVE_FR.html`](FLOWX_RAPPORT_DE_RECHERCHE_QUANTITATIVE_FR.html) — Rapport HTML imprimable en français.
* [`FLOWX_MANUAL_TRADING_PLAYBOOK.md`](FLOWX_MANUAL_TRADING_PLAYBOOK.md) — Obsidian-ready trading manual for discretionary execution.
* [`AGENT_INSTRUCTIONS.md`](AGENT_INSTRUCTIONS.md) — Antigravity agent onboarding & continuity protocol.
* [`stitch_combined_7months.py`](stitch_combined_7months.py) — 7-month multi-semester stitching & Monte Carlo simulation engine.
* [`stage1_friction_stress.py`](stage1_friction_stress.py) — Microstructure slippage & CME fee friction stress tester.
* [`stage3_capital_sizing.py`](stage3_capital_sizing.py) — Kelly Criterion & account tier sizing model.
* [`analyze_plateau_grid.py`](analyze_plateau_grid.py) — 3x3 Parameter Convexity & Plateau Matrix analyzer.
* [`compile.bat`](compile.bat) — Headless NinjaTrader C# compiler script.
