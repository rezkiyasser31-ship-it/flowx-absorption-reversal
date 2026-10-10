# FlowX Institutional Order Flow Absorption Playbook
#trading #orderflow #futures #es #playbook

> [!NOTE] Strategy Identity
> **Instrument:** E-mini S&P 500 (`ES`) / Micro E-mini (`MES`)  
> **Chart Timeframe:** 1-Minute Candle Chart (Tick Replay Enabled)  
> **Execution Style:** Intraday Institutional Mean-Reversion / Absorption  
> **Standard Sizing:** 2 Contracts (1 Scale-Out Target + 1 Runner)

---

## 1. Indicator & Chart Configuration

Configure your NinjaTrader 8 chart with the following exact settings:

| Indicator | Setting / Parameter | Value | Institutional Purpose |
| :--- | :--- | :---: | :--- |
| **TheFlowX_VWAP** | Anchor Period | **Session** | Resets dynamically each session open. |
| **TheFlowX_VWAP** | Standard Dev Band 1 | **1.0σ** (Active) | First scale-out target area (TP1). |
| **TheFlowX_VWAP** | Standard Dev Band 2 | **2.0σ** (Active) | Primary institutional reversal boundary. |
| **TheFlowX_VWAP** | Calculate Mode | **On each tick** | Real-time dynamic volume weighting. |
| **TheFlowX_BigTrades** | Minimum Size | **150** (ES) | Filters retail noise; flags block tape sweeps. |
| **TheFlowX_BigTrades** | Sweep Window | **100 ms** | Bundles multi-fill algorithmic sweeps into 1 bubble. |
| **TheFlowX_CVD** | Anchor / Reset | **EachSession** | Tracks session delta divergence & exhaustion. |
| **Data Series** | Tick Replay | **Checked ($\checkmark$)** | Required for order flow historical candle rendering. |

---

## 2. Institutional Trading Window

> [!IMPORTANT] Time-of-Day Filter
> * **Active Execution Hours:** **10:30 AM – 2:00 PM EST** *(17:00 – 20:30 Chart Time on UTC+2)*
> * **Hard Rule — No Trading 09:30 – 10:30 EST:** The opening cash hour is dominated by aggressive CTA trend momentum. Fading the opening hour produces false absorption wicks.
> * **Hard Rule — No Trading After 2:00 PM EST:** Order flow shifts to 4:00 PM closing market-on-close (MOC) imbalances.

---

## 3. The 4 Mandatory Entry Confirmations

Do not click Buy or Sell until **all 4 conditions** are verified on the closing 1-minute bar:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        THE 4-PILLAR CHECKLIST                          │
├────────────────────────────────────────────────────────────────────────┤
│ 1. LOCATION    │ Price tests or stretches beyond the ±2.0σ VWAP Band.  │
│ 2. FOOTPRINT   │ BigTrade bubble (≥150 lots) prints on the extreme wick.│
│ 3. GEOMETRY    │ Rejection wick measures AT LEAST 0.75 pts (3 ticks).  │
│ 4. DELTA FLIP  │ Bar Delta confirms absorption (flips away from extreme)│
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Short Execution Blueprint (Bearish Absorption)

```
        Tip of Wick ────── 7,856.50  (Green BigTrade Buy Bubble: +180 lots Ask)
  STOP LOSS (+2 ticks) ─── 7,857.00  ◄── Placed 2 ticks above tip (Floored at 5.0 pts)
                               ▲
                               │ Rejection Wick (≥ 0.75 pt / 3 ticks)
                               ▼
  ENTRY (Candle Close) ─── 7,851.50  ◄── Enter Market Short on bar close (2 Contracts)
                               │
                               ▼  (+3.5 pts / 14 ticks favorable)
  BE RATCHET ───────────── 7,848.00  ◄── Move Stop Loss to 7,851.25 (Entry + 1 tick)
                               │
                               ▼
  TP1 (+1.0σ Band) ─────── 7,844.00  ◄── Close 50% (Contract 1 banks +$375.00)
                               │
                               ▼
  TP2 (VWAP Midline) ───── 7,838.00  ◄── Close Runner (Contract 2 banks +$675.00)
```

### Execution Steps:
1. **Identify Stretch:** Price pushes up to or through the **Upper +2.0σ VWAP Band**.
2. **Detect Trap:** A **Green BigTrade Buy Bubble (≥150 lots)** prints on the high wick (aggressive market buyers hitting the Ask).
3. **Confirm Absorption:** Passive institutional limit sellers (icebergs) swallow the orders; price fails to expand and wicks down.
4. **Wick & Delta:** The 1-minute candle closes with an **upper rejection wick ≥ 0.75 points (3 ticks)** and the candle delta is negative or exhausted.
5. **Entry:** Enter **Market Short** immediately on candle close (or place Sell Stop 1 tick below candle low).

---

## 5. Long Execution Blueprint (Bullish Absorption)

```
  TP2 (VWAP Midline) ───── 7,692.00  ◄── Close Runner (Contract 2 banks +$725.00)
                               ▲
                               │
  TP1 (-1.0σ Band) ─────── 7,684.00  ◄── Close 50% (Contract 1 banks +$337.50)
                               ▲
                               │  (+3.5 pts / 14 ticks favorable)
  BE RATCHET ───────────── 7,680.75  ◄── Move Stop Loss to 7,677.50 (Entry + 1 tick)
                               ▲
  ENTRY (Candle Close) ─── 7,677.25  ◄── Enter Market Long on bar close (2 Contracts)
                               ▲
                               │ Rejection Wick (≥ 0.75 pt / 3 ticks)
                               ▼
  STOP LOSS (-2 ticks) ─── 7,672.25  ◄── Placed 2 ticks below tip (Floored at 5.0 pts)
        Tip of Wick ────── 7,672.75  (Red BigTrade Sell Bubble: -195 lots Bid)
```

### Execution Steps:
1. **Identify Stretch:** Price drops down to or through the **Lower -2.0σ VWAP Band**.
2. **Detect Trap:** A **Red BigTrade Sell Bubble (≥150 lots)** prints on the low wick (aggressive market sellers hitting the Bid).
3. **Confirm Absorption:** Passive institutional limit buyers swallow the orders; price fails to expand lower and wicks up.
4. **Wick & Delta:** The 1-minute candle closes with a **lower rejection wick ≥ 0.75 points (3 ticks)** and the candle delta is positive or holding baseline.
5. **Entry:** Enter **Market Long** immediately on candle close (or place Buy Stop 1 tick above candle high).

---

## 6. Dynamic Stop Loss Calculation (Wick-Anchored)

> [!WARNING] Exact Structural Stop Formula
> The stop loss is **NOT** a static arbitrary number. It is anchored to market structure with safety boundaries:

```
  Stop Formula:
  1. Raw Anchor   = Tip of the Absorption Wick ± 2 Ticks (0.50 pt)
  2. Noise Floor  = Minimum 5.0 Points (20 ticks / $250 per ES contract)
  3. Max Ceiling  = Maximum 6.0 Points (24 ticks / $300 per ES contract)
```

### Operational Rules:
* **Case A — Wick Distance is 3.5 to 5.0 Points:**  
  Set the Stop Loss at **5.0 points** from entry. *(The 5.0 pt floor protects you from random noise).*
* **Case B — Wick Distance is 5.25 to 6.0 Points:**  
  Set the Stop Loss **exactly 2 ticks beyond the tip of the wick** (e.g., 5.50 points).
* **Case C — Wick Distance is GREATER THAN 6.0 Points:**  
  **DO NOT TAKE THE TRADE.** The risk distance is too wide, invalidating the asymmetry.

---

## 7. The Break-Even Ratchet Protocol

> [!TIP] The +3.5 Point Trigger Rule
> When open unrealized profit reaches **+3.5 points (14 ticks / +$175.00 per contract)**:
> 1. Immediately drag the Stop Loss to **Entry Price + 1 Tick (+0.25 pt)**.
>    * *For Longs:* Stop moves to `Entry + 0.25`.
>    * *For Shorts:* Stop moves to `Entry - 0.25`.
> 2. **Why +1 Tick?** This extra tick covers exchange fees and broker commissions ($4.20/rt on ES), guaranteeing a true 100% risk-free trade.

---

## 8. Take Profit Targets (Harvesting)

| Order Leg | Allocation | Target Level | Typical Target Distance | Expected PnL (ES) |
| :--- | :---: | :--- | :---: | :---: |
| **Contract 1 (TP1)** | **50%** | **±1.0σ VWAP Band** (or +4.0 pts) | **+3.5 to +4.5 pts** | **+$175 to +$225** |
| **Contract 2 (TP2)** | **50%** | **VWAP Midline** (Orange Center Line) | **+7.0 to +15.0+ pts** | **+$350 to +$750+** |

* Once **TP1** is banked, the trade is in pure house money with Contract 2 trailing toward the VWAP midline.

---

## 9. Walk-Away Red Flags (NO TRADE)

> [!DANGER] Invalidation & Discipline Rules
> - [ ] ❌ **Inside Fair Value:** Never enter between the `+1.0σ` and `-1.0σ` bands. There is no statistical edge in the value area.
> - [ ] ❌ **Full-Body Candles:** If a candle breaks outside `2.0σ` with a full body and closes on its extreme without a 3-tick wick, **do NOT fade it**.
> - [ ] ❌ **Economic News Embargo:** No entries within **3 minutes** before or after high-impact macro data (CPI, PPI, FOMC, NFP).
> - [ ] ❌ **Max 1 Loss Per Session:** If trade #1 hits the full stop loss, **shut down the platform**. Empirical data proves that fighting a trend day twice accounts for severe drawdowns.

---

## 10. Pre-Execution 5-Second Checklist

Keep this checklist visible before pulling the trigger:

- [ ] **1. Time Check:** Is the current time between 10:30 AM and 2:00 PM EST?
- [ ] **2. Location:** Is price touching or extending beyond the outer ±2.0σ VWAP Band?
- [ ] **3. Institutional Print:** Did a BigTrade bubble (≥150 lots) print on the extreme wick?
- [ ] **4. Rejection Wick:** Does the candle wick measure at least 0.75 points (3 ticks)?
- [ ] **5. Delta Alignment:** Did bar delta flip away from the extreme?
- [ ] **6. Risk Bounds:** Is the wick distance $\le 6.0$ points?
- [ ] **7. Bracket Armed:** Initial stop floored at 5.0 pts, BE ratchet armed for +3.5 pts.
