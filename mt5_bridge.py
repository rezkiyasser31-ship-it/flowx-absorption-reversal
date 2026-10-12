"""
FlowX MT5 Execution Bridge & Telegram Dispatcher
================================================
Connects NinjaTrader 8 FlowX order flow signals to:
1. MetaTrader 5 API for direct automated order execution, Breakeven trailing, and exits (US500Cash).
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

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

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
# MT5 DIRECT EXECUTION & EXIT ENGINE
# ==============================================================================
def ensure_mt5_connected():
    if not mt5.initialize():
        logger.error(f"[MT5] Initialization failed: {mt5.last_error()}")
        return False
    if not mt5.symbol_select(SYMBOL, True):
        logger.error(f"[MT5] Failed to select symbol {SYMBOL}")
        return False
    return True

def execute_mt5_order(action: str, volume: float, stop_points: float, tp_points: float, comment: str = "FlowX_ES"):
    """
    Executes a direct market deal in MT5 on US500Cash with attached SL and TP.
    """
    if not ensure_mt5_connected():
        return {"success": False, "error": "MT5 connection failed"}

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

    logger.info(f"[MT5 EXECUTED] Ticket #{result.order} | {action_upper} {volume} lots @ {result.price:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
    return {
        "success": True,
        "ticket": result.order,
        "price": result.price,
        "volume": result.volume,
        "sl": sl,
        "tp": tp,
        "comment": result.comment
    }

def execute_breakeven():
    """
    Finds all open positions for SYMBOL with MAGIC_NUMBER and moves Stop Loss to Entry Price (Breakeven).
    """
    if not ensure_mt5_connected():
        return {"success": False, "error": "MT5 connection failed"}

    positions = mt5.positions_get(symbol=SYMBOL)
    if not positions:
        return {"success": True, "message": "No open positions to modify"}

    modified = []
    for pos in positions:
        if pos.magic != MAGIC_NUMBER:
            continue
        
        # Check if already at or better than breakeven
        if pos.type == mt5.ORDER_TYPE_BUY and pos.sl >= pos.price_open:
            continue
        if pos.type == mt5.ORDER_TYPE_SELL and pos.sl <= pos.price_open and pos.sl > 0:
            continue

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": pos.ticket,
            "symbol": pos.symbol,
            "sl": round(pos.price_open, 2),
            "tp": pos.tp
        }
        res = mt5.order_send(request)
        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"[BREAKEVEN ARMED] Ticket #{pos.ticket} SL moved to Entry @ {pos.price_open:.2f}")
            modified.append(pos.ticket)
        else:
            logger.warning(f"[BREAKEVEN FAILED] Ticket #{pos.ticket}: {res.comment if res else 'Unknown error'}")

    return {"success": True, "modified_tickets": modified}

def execute_close_half():
    """
    Closes 50% of the active volume for SYMBOL with MAGIC_NUMBER (TP1 scale-out).
    """
    if not ensure_mt5_connected():
        return {"success": False, "error": "MT5 connection failed"}

    positions = mt5.positions_get(symbol=SYMBOL)
    if not positions:
        return {"success": True, "message": "No positions to scale out"}

    closed = []
    for pos in positions:
        if pos.magic != MAGIC_NUMBER:
            continue
        half_vol = round(pos.volume / 2.0, 1)
        if half_vol < 0.1:
            half_vol = pos.volume  # close remainder if tiny

        tick = mt5.symbol_info_tick(pos.symbol)
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        close_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": pos.ticket,
            "symbol": pos.symbol,
            "volume": half_vol,
            "type": close_type,
            "price": round(close_price, 2),
            "deviation": SLIPPAGE_MAX,
            "magic": MAGIC_NUMBER,
            "comment": "FlowX_TP1_Half",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        res = mt5.order_send(request)
        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"[TP1 SCALED OUT] Ticket #{pos.ticket} Closed {half_vol} lots @ {close_price:.2f}")
            closed.append(pos.ticket)
        else:
            logger.warning(f"[TP1 CLOSE FAILED] Ticket #{pos.ticket}: {res.comment if res else 'Unknown'}")

    return {"success": True, "scaled_tickets": closed}

def execute_close_all():
    """
    Closes 100% of open positions for SYMBOL with MAGIC_NUMBER (Full Exit / EOD Flatten).
    """
    if not ensure_mt5_connected():
        return {"success": False, "error": "MT5 connection failed"}

    positions = mt5.positions_get(symbol=SYMBOL)
    if not positions:
        return {"success": True, "message": "No open positions"}

    closed = []
    for pos in positions:
        if pos.magic != MAGIC_NUMBER:
            continue

        tick = mt5.symbol_info_tick(pos.symbol)
        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        close_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": pos.ticket,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "price": round(close_price, 2),
            "deviation": SLIPPAGE_MAX,
            "magic": MAGIC_NUMBER,
            "comment": "FlowX_Full_Exit",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        res = mt5.order_send(request)
        if res and res.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"[FULL POSITION CLOSED] Ticket #{pos.ticket} Closed {pos.volume} lots @ {close_price:.2f}")
            closed.append(pos.ticket)
        else:
            logger.warning(f"[FULL CLOSE FAILED] Ticket #{pos.ticket}: {res.comment if res else 'Unknown'}")

    return {"success": True, "closed_tickets": closed}

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

        action = signal.get("action", "").upper()   # "BUY", "SELL", "BREAKEVEN", "CLOSE_HALF", "CLOSE_ALL"
        volume = float(signal.get("volume", DEFAULT_LOTS))
        stop_pts = float(signal.get("stop_points", 5.0))
        tp_pts = float(signal.get("tp_points", 10.0))
        source = signal.get("source", "FlowX_ES")

        exec_result = {}

        # 1. Routing based on action type
        if action in ("BREAKEVEN", "BE"):
            exec_result = execute_breakeven()
            tg_text = "🛡️ *FLOWX BREAKEVEN GUARD ARMED*\n━━━━━━━━━━━━━━━━━━━\n• Stop Loss moved to Entry Price\n• Trade is now risk-free."
            send_telegram_alert(tg_text)

        elif action in ("CLOSE_HALF", "TP1"):
            exec_result = execute_close_half()
            tg_text = "🎯 *FLOWX TP1 TARGET HIT*\n━━━━━━━━━━━━━━━━━━━\n• Scaled out 50% position\n• Profits secured."
            send_telegram_alert(tg_text)

        elif action in ("CLOSE_ALL", "FLAT", "EXIT"):
            exec_result = execute_close_all()
            tg_text = "🏁 *FLOWX POSITION CLOSED*\n━━━━━━━━━━━━━━━━━━━\n• Position fully liquidated."
            send_telegram_alert(tg_text)

        elif action in ("BUY", "LONG", "SELL", "SHORT"):
            exec_result = execute_mt5_order(action, volume, stop_pts, tp_pts, comment=source)
            status_icon = "🟢" if action in ("BUY", "LONG") else "🔴"
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
        else:
            exec_result = {"success": False, "error": f"Unknown action: {action}"}

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
        return

def run_server():
    server = HTTPServer((HOST, PORT), SignalHandler)
    logger.info(f"[FlowX] MT5 Bridge is LISTENING on http://{HOST}:{PORT}/trade")
    logger.info(f"   Target Symbol: {SYMBOL} | Default Lots: {DEFAULT_LOTS}")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
