# =========================
# MAIN.PY (FULLY UPDATED WITH STATE SYNC)
# =========================

import time
import json
import os
import config
import strategy
import risk
import broker
from flask import Flask
import threading
import sys
sys.stdout.reconfigure(line_buffering=True)


# =========================
# CONSTANTS
# =========================

LOOP_INTERVAL = 30          # seconds
PRODUCT_ID    = 84          # BTC Futures (Testnet)
STATE_FILE    = "trade_state.json"
SLIPPAGE_BUFFER = 0.002     # 0.2% buffer for stop-limit entries

# Inject product ID into config
config.PRODUCT_ID = PRODUCT_ID


# =========================
# TRADE STATE — SAVE / LOAD / DELETE
# =========================

def _save_state():
    state = {
        "order_type"  : config.order_type,
        "entry_price" : config.entry_price,
        "stop_loss"   : config.stop_loss,
        "target"      : config.target,
        "quantity"    : config.quantity,
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    print(f"[State] Saved to {STATE_FILE}")


def _load_state():
    if not os.path.exists(STATE_FILE):
        return False

    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    config.order_in_progress = True
    config.order_type        = state["order_type"]
    config.entry_price       = state["entry_price"]
    config.stop_loss         = state["stop_loss"]
    config.target            = state["target"]
    config.quantity          = state["quantity"]

    print(f"[State] Restored from {STATE_FILE}")
    print(f"[State] {config.order_type} | Entry: {config.entry_price} | SL: {config.stop_loss} | Target: {config.target} | Qty: {config.quantity}")
    return True


def _delete_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
        print(f"[State] {STATE_FILE} deleted")


# =========================
# HELPER: GET REAL ENTRY PRICE FROM EXCHANGE
# =========================

def _get_real_entry_price():
    try:
        position = broker.get_position()
        size = position["size"]
        entry_price = float(position["entry_price"])
        
        if size < 0:
            entry_price = abs(entry_price)
            
        print(f"[Entry] Real entry price from exchange: {entry_price}")
        return entry_price
    except Exception as e:
        print(f"[Entry] Could not fetch real entry price: {e}")
        return None


# =========================
# MAIN LOOP
# =========================

def run():

    print("=== Traffic Light Pairs Bot Started ===")
    print(f"Symbol     : {config.SYMBOL}")
    print(f"Timeframe  : {config.TIMEFRAME}")
    print(f"Risk/Trade : {config.RISK_PER_TRADE}%")
    print(f"Reward     : {config.REWARD_RATIO}x")
    print("=" * 40)

    # --- Startup: Check for existing open position ---
    print("[Startup] Checking for existing position...")
    try:
        position = broker.get_position()
        size = position["size"]

        if size != 0:
            restored = _load_state()
            if not restored:
                print("[Startup] No state file found. Monitoring position without SL/Target.")
                print("[Startup] Please close this position manually or wait for next trade.")
                config.order_in_progress = True
        else:
            _delete_state()
            print("[Startup] No open position. Starting fresh.")

    except ConnectionError as e:
        print(f"[NETWORK ERROR] Internet/API connection issue: {e}")

    except ValueError as e:
        print(f"[DATA ERROR] Unexpected data from API: {e}")

    except Exception as e:
        print(f"[UNKNOWN ERROR] {type(e).__name__}: {e}")


    while True:

        try:

            # ----------------------------
            # STEP 1 — Fetch current price
            # ----------------------------

            current_price = broker.get_current_price()
            print(f"\n[Price] {current_price}")

            # ----------------------------
            # STEP 1.5 — SELF-HEALING: Check if position actually exists on exchange
            # ----------------------------
            try:
                actual_position = broker.get_position()
                actual_size = actual_position["size"]
                
                # Agar exchange pe position nahi hai, par bot soch raha hai ki trade open hai
                if actual_size == 0 and config.order_in_progress:
                    print("[SYNC] Exchange shows NO position, but bot thought trade was open. Resetting state...")
                    _reset_trade(pnl=0)  # Force reset
                    
                # Agar exchange pe position hai, par bot ko nahi pata (kisi aur ne trade li)
                elif actual_size != 0 and not config.order_in_progress:
                    print("[SYNC] Exchange shows OPEN position, but bot has no state. Attempting to recover...")
                    # Try to load state, agar nahi hai toh manual monitoring start karo
                    if not _load_state():
                        print("[SYNC] No state file. Setting manual monitoring mode.")
                        config.order_in_progress = True
                        
            except Exception as e:
                print(f"[SYNC ERROR] {e}")


            # ----------------------------
            # STEP 2 — Manage open trade
            # ----------------------------

            if config.order_in_progress:

                if config.stop_loss is None or config.target is None:
                    print("[Trade] Open position found but no SL/Target. Waiting for manual close...")

                else:

                    print(f"[Trade] {config.order_type} open | Entry: {config.entry_price} | SL: {config.stop_loss} | Target: {config.target}")

                    # --- Break-Even Check ---
                    new_sl = risk.move_to_break_even(
                        config.entry_price,
                        current_price,
                        config.stop_loss
                    )

                    if new_sl != config.stop_loss:
                        print(f"[Break-Even] SL moved from {config.stop_loss} → {new_sl}")
                        config.stop_loss = new_sl
                        _save_state()


                    # --- EXIT: LONG trade ---
                    if config.order_type == "BUY":

                        if current_price >= config.target:
                            print("[EXIT] Target hit — closing LONG")
                            broker.close_position()
                            _reset_trade(pnl=+abs(config.target - config.entry_price) * config.quantity)

                        elif current_price <= config.stop_loss:
                            print("[EXIT] Stop Loss hit — Placing Stop-Market order")
                            side = "SELL"
                            qty_to_close = abs(config.quantity) if config.quantity else 0
                            if qty_to_close > 0:
                                broker.place_stop_market_order(side, config.stop_loss, qty_to_close)
                                _reset_trade(pnl=-abs(config.entry_price - config.stop_loss) * config.quantity)
                            else:
                                print(f"[EXIT] Cannot close - invalid quantity: {config.quantity}")
                                _reset_trade(pnl=0)  # Force reset if quantity is bad


                    # --- EXIT: SHORT trade ---
                    elif config.order_type == "SELL":

                        if current_price <= config.target:
                            print("[EXIT] Target hit — closing SHORT")
                            broker.close_position()
                            _reset_trade(pnl=+abs(config.entry_price - config.target) * config.quantity)

                        elif current_price >= config.stop_loss:
                            print("[EXIT] Stop Loss hit — Placing Stop-Market order")
                            side = "BUY"
                            qty_to_close = abs(config.quantity) if config.quantity else 0
                            if qty_to_close > 0:
                                broker.place_stop_market_order(side, config.stop_loss, qty_to_close)
                                _reset_trade(pnl=-abs(config.stop_loss - config.entry_price) * config.quantity)
                            else:
                                print(f"[EXIT] Cannot close - invalid quantity: {config.quantity}")
                                _reset_trade(pnl=0)  # Force reset if quantity is bad


            # ----------------------------
            # STEP 3 — Look for new signal
            # ----------------------------

            else:

                df = strategy.get_candles()

                signal, range_high, range_low = strategy.get_signal(df, current_price)

                print(f"[Signal] {signal} | Range High: {range_high} | Range Low: {range_low}")

                # --- ENTRY: LONG ---
                if signal == "BUY":

                    temp_entry = current_price
                    sl = range_low
                    target = temp_entry + (config.REWARD_RATIO * abs(temp_entry - sl))
                    qty = risk.calculate_quantity(temp_entry, sl)

                    if qty > 0:
                        trigger_price = range_high
                        limit_price = range_high * (1 + SLIPPAGE_BUFFER)
                        qty_int = max(1, int(qty))
                        
                        print(f"[BUY] Placing Stop-Limit: Trigger {trigger_price}, Limit {limit_price}, Qty {qty_int}")
                        broker.place_stop_limit_order("BUY", trigger_price, limit_price, qty_int)
                        
                        print("[BUY] Waiting 3 seconds for order to fill...")
                        time.sleep(3)
                        
                        real_entry = _get_real_entry_price()
                        if real_entry is not None:
                            real_sl = sl
                            real_target = real_entry + (config.REWARD_RATIO * abs(real_entry - real_sl))
                            print(f"[BUY] Real Entry: {real_entry} | Recalculated Target: {real_target}")
                            
                            real_qty = risk.calculate_quantity(real_entry, real_sl)
                            real_qty_int = max(1, int(real_qty))
                            
                            _set_trade("BUY", real_entry, real_sl, real_target, real_qty_int)
                        else:
                            print("[BUY] Could not fetch real entry. Using temporary entry.")
                            _set_trade("BUY", temp_entry, sl, target, qty)
                    else:
                        print("[BUY] Qty = 0, skipping order")


                # --- ENTRY: SHORT ---
                elif signal == "SELL":

                    temp_entry = current_price
                    sl = range_high
                    target = temp_entry - (config.REWARD_RATIO * abs(sl - temp_entry))
                    qty = risk.calculate_quantity(temp_entry, sl)

                    if qty > 0:
                        trigger_price = range_low
                        limit_price = range_low * (1 - SLIPPAGE_BUFFER)
                        qty_int = max(1, int(qty))
                        
                        print(f"[SELL] Placing Stop-Limit: Trigger {trigger_price}, Limit {limit_price}, Qty {qty_int}")
                        broker.place_stop_limit_order("SELL", trigger_price, limit_price, qty_int)
                        
                        print("[SELL] Waiting 3 seconds for order to fill...")
                        time.sleep(3)
                        
                        real_entry = _get_real_entry_price()
                        if real_entry is not None:
                            real_sl = sl
                            real_target = real_entry - (config.REWARD_RATIO * abs(real_sl - real_entry))
                            print(f"[SELL] Real Entry: {real_entry} | Recalculated Target: {real_target}")
                            
                            real_qty = risk.calculate_quantity(real_entry, real_sl)
                            real_qty_int = max(1, int(real_qty))
                            
                            _set_trade("SELL", real_entry, real_sl, real_target, real_qty_int)
                        else:
                            print("[SELL] Could not fetch real entry. Using temporary entry.")
                            _set_trade("SELL", temp_entry, sl, target, qty)
                    else:
                        print("[SELL] Qty = 0, skipping order")

                else:
                    print("[Waiting] No valid signal")


        except ConnectionError as e:
            print(f"[NETWORK ERROR] Internet/API connection issue: {e}")

        except ValueError as e:
            print(f"[DATA ERROR] Unexpected data from API: {e}")

        except Exception as e:
            print(f"[UNKNOWN ERROR] {type(e).__name__}: {e}")


        # ----------------------------
        # STEP 4 — Wait for next tick
        # ----------------------------

        print(f"[Daily PnL] {config.daily_pnl:.2f}")
        time.sleep(LOOP_INTERVAL)


# =========================
# HELPERS
# =========================

def _set_trade(order_type, entry, sl, target, qty):
    config.order_in_progress = True
    config.order_type        = order_type
    config.entry_price       = entry
    config.stop_loss         = sl
    config.target            = target
    config.quantity          = qty
    _save_state()


def _reset_trade(pnl=0):
    config.daily_pnl        += pnl
    config.order_in_progress = False
    config.order_type        = None
    config.entry_price       = None
    config.stop_loss         = None
    config.target            = None
    config.quantity          = 0
    _delete_state()
    print(f"[Trade Closed] PnL this trade: {pnl:.2f}")


# =========================
# ENTRY POINT
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "Traffic Light Bot Running"

def start_bot():
    run()

print("[Startup] Starting bot thread...")
bot_thread = threading.Thread(target=start_bot, daemon=True)
bot_thread.start()
print("[Startup] Bot thread started.")

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
