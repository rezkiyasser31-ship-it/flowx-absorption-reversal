# FlowX: Automated MT5 Execution & Telegram Signal Bridge

This guide explains how to run full end-to-end automated signal dispatch and direct MT5 trade execution completely free of charge.

---

## 1. System Architecture

```
┌──────────────────────────────────────────────┐
│        1. SIGNAL GENERATOR (NinjaTrader 8)   │
│  - Asset: CME ES Futures (ES 12-26)          │
│  - Logic: Institutional Absorption & Delta   │
│  - Trigger: Sends local webhook JSON         │
└──────────────────────┬───────────────────────┘
                       │ HTTP POST (port 5005)
                       ▼
┌──────────────────────────────────────────────┐
│        2. FLOWX PYTHON BRIDGE (mt5_bridge.py)│
│  - Connects to MT5 Terminal via Python API   │
│  - Validates spreads, tick size & margin     │
└──────────────┬───────────────────────────────┘
               │
      ┌────────┴────────────────────┐
      ▼                             ▼
┌──────────────────────┐   ┌──────────────────────┐
│ 3A. DIRECT MT5 TRADE │   │ 3B. TELEGRAM CHANNEL │
│ - Instrument:        │   │ - Direction & Entry  │
│   US500Cash          │   │ - SL / TP in points  │
│ - Volume: 2.00 lots  │   │ - Dollar risk math   │
│ - Bracket SL & TP    │   │ - Execution receipt  │
└──────────────────────┘   └──────────────────────┘
```

---

## 2. Prerequisites & Configuration

### A. MetaTrader 5 Setup
1. Open your **MetaTrader 5** terminal.
2. Ensure **Algo Trading** is enabled:
   - Click the **Algo Trading** button on the top toolbar (it must turn green).
   - Or press **`Ctrl + E`**.
3. In MT5: Go to `Tools` $\rightarrow$ `Options` $\rightarrow$ `Expert Advisors`:
   - Check **"Allow algorithmic trading"**.

### B. Telegram Setup (Optional)
If you want signals sent to a Telegram channel:
1. Message `@BotFather` on Telegram and create a new bot $\rightarrow$ copy the **Bot Token**.
2. Create a public or private Telegram Channel.
3. Add your bot as an **Administrator** to the channel.
4. Set the environment variables or pass them in `mt5_bridge.py`:
   ```bash
   $env:TELEGRAM_BOT_TOKEN="your_token_here"
   $env:TELEGRAM_CHAT_ID="@your_channel_username"
   ```

---

## 3. How to Launch the Bridge

Run the Python bridge from PowerShell:
```powershell
python mt5_bridge.py
```

The bridge will initialize:
```text
[INFO] 🚀 FlowX MT5 Bridge is LISTENING on http://127.0.0.1:5005/trade
[INFO]    Target Symbol: US500Cash | Default Lots: 2.00
```

---

## 4. NinjaTrader 8 Strategy Settings

In NinjaTrader 8, open `FlowXAbsorptionReversal_ES` parameters:
- **Enable MT5 Bridge**: `True`
- **Bridge Webhook URL**: `http://127.0.0.1:5005/trade`
- **MT5 Lots**: `2.0` (Risk: \$10.00 on 5-point stop)
- **Telegram Bot Token**: (Optional, if sending directly from NT8)
- **Telegram Chat ID**: (Optional)

When an institutional absorption signal occurs on ES, NinjaTrader will instantly fire the order into MT5 and notify Telegram.
