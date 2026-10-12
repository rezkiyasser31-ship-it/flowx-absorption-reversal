"""
FlowX MT5 Execution Bridge & Telegram Dispatcher
================================================
Connects NinjaTrader 8 FlowX order flow signals to:
1. MetaTrader 5 API for direct automated order execution (US500Cash).
2. Telegram Bot API for instant signal broadcasting to a channel/group.

Zero external dependencies required (uses built-in http.server, urllib, MetaTrader5).
"""

import json
import logging
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.request
import urllib.parse
import MetaTrader5 as mt5

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("FlowXBridge")

# ==============================================================================
# CONFIGURATION
# ==============================================================================
HOST = "127.0.0.1"
PORT = 5005

# Trading Configuration
SYMBOL = "US500Cash"
DEFAULT_LOTS = 2.00          # 2.00 lots = $2.00 per point on XM (Contract size = 1)
SLIPPAGE_MAX = 20           # Max deviation in points/ticks
MAGIC_NUMBER = 20261012     # Unique FlowX identifier in MT5
DRY_RUN = False             # Set to True to validate signals without executing

# Telegram Configuration (Set via environment variables or replace here)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# ==============================================================================
# TELEGRAM DISPATCHER
# ==============================================================================
def send_telegram_alert(message: str):
    """Sends a markdown-formatted message to Telegram channel/chat."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.info("[Telegram] Bot token or Chat ID not configured. Skipping notification.")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                logger.info("[Telegram] Alert successfully sent to Telegram!")
                return True
    except Exception as e:
        logger.error(f"[Telegram] Failed to send alert: {e}")
    return False

# ==============================================================================
# MT5 DIRECT EXECUTION ENGINE
# ==============================================================================
def execute_mt5_order(action: str, volume: float, stop_points: float, tp_points: float, comment: str = "FlowX_ES"):
    """
    Executes a direct market deal in MT5 on US500Cash with attached SL and TP.
    """
    if not mt5.initialize():
        logger.error(f"[MT5] Initialization failed: {mt5.last_error()}")
        return {"success": False, "error": "MT5 initialize failed"}
    
    # Ensure symbol is selected in Market Watch
    if not mt5.symbol_select(SYMBOL, True):
        logger.error(f"[MT5] Failed to select symbol {SYMBOL}")
        return {"success": False, "error": f"Symbol {SYMBOL} not found"}

    tick = mt5.symbol_info_tick(SYMBOL)
    if tick is None:
        logger.error(f"[MT5] Failed to get live tick for {SYMBOL}")
        return {"success": False, "error": "No tick data"}

    action_upper = action.upper()
    if action_upper in ("BUY", "LONG"):
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
        sl = price - stop_points if stop_points > 0 else 0.0
        tp = price + tp_points if tp_points > 0 else 0.0
    elif action_upper in ("SELL", "SHORT"):
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
        sl = price + stop_points if stop_points > 0 else 0.0
        tp = price - tp_points if tp_points > 0 else 0.0
    else:
        return {"success": False, "error": f"Unknown action: {action}"}

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": float(volume),
        "type": order_type,
        "price": round(price, 2),
        "sl": round(sl, 2),
        "tp": round(tp, 2),
        "deviation": SLIPPAGE_MAX,
        "magic": MAGIC_NUMBER,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    # 1. Pre-execution Check
    check = mt5.order_check(request)
    if check is None or check.retcode != 0:
        err_msg = check.comment if check else str(mt5.last_error())
        logger.error(f"[MT5] Order Check Failed: retcode={check.retcode if check else 'None'}, comment={err_msg}")
        return {"success": False, "error": f"Order check failed: {err_msg}"}

    if DRY_RUN:
        logger.info(f"[MT5 DRY RUN] Checked order successfully: {request}")
        return {"success": True, "dry_run": True, "details": request}

    # 2. Live Send
    result = mt5.order_send(request)
    if result is None:
        logger.error(f"[MT5] order_send returned None. Error: {mt5.last_error()}")
        return {"success": False, "error": "Order send returned None"}

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error(f"[MT5] Order Execution Failed: code={result.retcode}, comment={result.comment}")
        return {"success": False, "retcode": result.retcode, "comment": result.comment}

    logger.info(f"✅ [MT5 EXECUTED] Ticket #{result.order} | {action_upper} {volume} lots @ {result.price:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
    return {
        "success": True,
        "ticket": result.order,
        "price": result.price,
        "volume": result.volume,
        "sl": sl,
        "tp": tp,
        "comment": result.comment
    }

# ==============================================================================
# HTTP WEBHOOK LISTENER FOR NINJATRADER 8
# ==============================================================================
class SignalHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        
        try:
            signal = json.loads(post_data.decode("utf-8"))
            logger.info(f"⚡ [RECEIVED SIGNAL FROM NINJATRADER 8]: {signal}")
        except Exception as e:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Invalid JSON: {e}"}).encode("utf-8"))
            return

        action = signal.get("action", "").upper()   # "BUY" or "SELL"
        volume = float(signal.get("volume", DEFAULT_LOTS))
        stop_pts = float(signal.get("stop_points", 5.0))
        tp_pts = float(signal.get("tp_points", 10.0))
        source = signal.get("source", "FlowX_ES")

        # 1. Execute directly in MT5
        exec_result = execute_mt5_order(action, volume, stop_pts, tp_pts, comment=source)

        # 2. Format & Dispatch Telegram Alert
        status_icon = "🟢" if action == "BUY" else "🔴"
        exec_status = f"✅ Executed (Ticket #{exec_result.get('ticket')})" if exec_result.get("success") else f"❌ Failed ({exec_result.get('error')})"
        
        tg_text = (
            f"⚡ *FLOWX INSTITUTIONAL SIGNAL* ⚡\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"• *Direction*: {status_icon} *{action}*\n"
            f"• *Instrument*: `{SYMBOL}` (ES Futures Correlation)\n"
            f"• *Volume*: `{volume:.2f} lots` (~${volume:.2f}/pt)\n"
            f"• *Stop Loss*: `±{stop_pts:.2f} pts` (Risk: ~${stop_pts * volume:.2f})\n"
            f"• *Target (TP)*: `±{tp_pts:.2f} pts` (Reward: ~${tp_pts * volume:.2f})\n"
            f"• *Execution*: {exec_status}\n"
            f"━━━━━━━━━━━━━━━━━━━"
        )
        send_telegram_alert(tg_text)

        # Respond to NinjaTrader
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response_payload = {
            "status": "processed",
            "execution": exec_result
        }
        self.wfile.write(json.dumps(response_payload).encode("utf-8"))

    def log_message(self, format, *args):
        # Suppress noisy HTTP access logs
        return

def run_server():
    server = HTTPServer((HOST, PORT), SignalHandler)
    logger.info(f"🚀 FlowX MT5 Bridge is LISTENING on http://{HOST}:{PORT}/trade")
    logger.info(f"   Target Symbol: {SYMBOL} | Default Lots: {DEFAULT_LOTS}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
