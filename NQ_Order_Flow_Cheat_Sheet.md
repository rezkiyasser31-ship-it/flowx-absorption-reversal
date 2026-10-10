# NQ Order Flow Absorption Strategy — Cheat Sheet
**NinjaTrader 8 • TheFlowX Kit (BigTrades + VWAP + CVD) • Intraday Reversals**

---

## ⚡ The 3 Pillars of Every Valid Trade (All 3 Must Agree)

1. **WHERE (Location):** Price stretches to the **±2.0σ VWAP Band** (Statistically overextended ~95% value boundary).
2. **WHO (Aggression / Trap):** A **BigTrade Bubble (≥75 contracts)** prints on the extreme wick.
3. **PROOF (Absorption):** Price stalls / wicks away & **TheflowX_cvd** shows delta divergence or failure to follow through.

---

## 🔴 Bearish Absorption Setup (Short)

* **Location:** Price rallies and tests the **+2.0σ VWAP Band** (Upper Grey Band).
* **Institutional Print:** A **Green BigTrade Buy Bubble (≥75 contracts)** prints at or near the top wick (aggressive market buyers hitting the Ask).
* **Absorption Signal:** Price **fails to expand higher**; candle leaves a top rejection wick (passive limit sellers absorbed all orders).
* **CVD Check:** Sub-panel **TheflowX_cvd** makes a **Lower High** (Delta Divergence) or goes flat.
* **Entry:** Enter **Market Short** on rejection candle close (or Sell Stop 1 tick below candle low).
* **Stop Loss:** **1 to 2 points (4–8 ticks)** above the high wick of the BigTrade bubble.
* **Target 1 (TP1):** Close 50% at the **+1.0σ VWAP Band** and move Stop to Break-Even (+1 tick).
* **Target 2 (TP2):** Close remaining 50% at the **VWAP Midline (Orange Line)**.

---

## 🟢 Bullish Absorption Setup (Long)

* **Location:** Price drops and tests the **-2.0σ VWAP Band** (Lower Grey Band).
* **Institutional Print:** A **Red BigTrade Sell Bubble (≥75 contracts)** prints at or near the bottom wick (aggressive market sellers hitting the Bid).
* **Absorption Signal:** Price **fails to expand lower**; candle leaves a bottom rejection wick (passive limit buyers absorbed all orders).
* **CVD Check:** Sub-panel **TheflowX_cvd** makes a **Higher Low** (Delta Divergence) or holds baseline.
* **Entry:** Enter **Market Long** on rejection candle close (or Buy Stop 1 tick above candle high).
* **Stop Loss:** **1 to 2 points (4–8 ticks)** below the low wick of the BigTrade bubble.
* **Target 1 (TP1):** Close 50% at the **-1.0σ VWAP Band** and move Stop to Break-Even (+1 tick).
* **Target 2 (TP2):** Close remaining 50% at the **VWAP Midline (Orange Line)**.

---

## 🚫 Walk-Away Red Flags (NO TRADE)

* ❌ **No trades in the middle:** Never take a reversal trade between the +1.0σ and -1.0σ bands. There is no statistical edge in the value area.
* ❌ **Runaway Trend:** Full-body candles closing completely outside the 2.0σ band with zero wicks. Do NOT stand in front of a steamroller.
* ❌ **High-Impact News:** No entries within 2 minutes of CPI, PPI, FOMC, or NFP.
* ❌ **Missing BigTrade Print:** If price touches the 2.0σ band but no bubble prints, wait. Do not anticipate without institutional footprints.

---

## 📋 Pre-Execution 5-Second Checklist

- [ ] 1. Is price at or testing the **±2.0σ VWAP Band**?
- [ ] 2. Did a **BigTrade Bubble (≥75 contracts)** print on the wick?
- [ ] 3. Did price **stall and reject** instead of continuing through?
- [ ] 4. Does **CVD show divergence or exhaustion**?
- [ ] 5. Is my hard Stop Loss defined **1–2 points outside the wick**?

---

## ⚙️ Configured Indicator Settings Reference

| Indicator | Setting | Value | Purpose |
| :--- | :--- | :--- | :--- |
| **TheflowX_bigtrades** | Minimum Size | **75** | Filters out small retail fills; highlights institutional prints. |
| **TheflowX_bigtrades** | Sweep Grouping | **100 ms** | Bundles fast algorithmic multi-fill sweeps into 1 bubble. |
| **TheflowX_vwap** | 1σ Band Multiplier | **1.0** (Checked) | First scale-out target (TP1). |
| **TheflowX_vwap** | 2σ Band Multiplier | **2.0** (Checked) | Primary reversal entry search zone. |
| **TheflowX_vwap** | Calculate | **On each tick** | Live dynamic volume-weighted tracking. |
| **TheflowX_cvd** | Style & Reset | **Candles / EachSession** | Session-anchored delta divergence tracking. |
| **Data Series (NT8)** | Tick Replay | **Checked ($\checkmark$)** | Required for order flow historical candle rendering. |
