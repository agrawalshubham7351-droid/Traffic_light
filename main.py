# =========================
# MAIN.PY
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


# =========================
# CONSTANTS
# =========================

LOOP_INTERVAL = 30          # seconds
PRODUCT_ID    = 84          # BTC Futures (Testnet)
STATE_FILE    = "trade_state.json"

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
                            print("[EXIT] Stop Loss hit — closing LONG")
                            broker.close_position()
                            _reset_trade(pnl=-abs(config.entry_price - config.stop_loss) * config.quantity)


                    # --- EXIT: SHORT trade ---
                    elif config.order_type == "SELL":

                        if current_price <= config.target:
                            print("[EXIT] Target hit — closing SHORT")
                            broker.close_position()
                            _reset_trade(pnl=+abs(config.entry_price - config.target) * config.quantity)

                        elif current_price >= config.stop_loss:
                            print("[EXIT] Stop Loss hit — closing SHORT")
                            broker.close_position()
                            _reset_trade(pnl=-abs(config.stop_loss - config.entry_price) * config.quantity)


            # ----------------------------
            # STEP 3 — Look for new signal
            # ----------------------------

            else:

                df = strategy.get_candles()

                signal, range_high, range_low = strategy.get_signal(df, current_price)

                print(f"[Signal] {signal} | Range High: {range_high} | Range Low: {range_low}")

                # --- ENTRY: LONG ---
                if signal == "BUY":

                    entry  = current_price
                    sl     = range_low
                    target = entry + (config.REWARD_RATIO * abs(entry - sl))
                    qty    = risk.calculate_quantity(entry, sl)

                    if qty > 0:
                        print(f"[BUY] Entry: {entry} | SL: {sl} | Target: {target} | Qty: {qty}")
                        broker.place_buy_order(int(qty))
                        _set_trade("BUY", entry, sl, target, qty)
                    else:
                        print("[BUY] Qty = 0, skipping order")


                # --- ENTRY: SHORT ---
                elif signal == "SELL":

                    entry  = current_price
                    sl     = range_high
                    target = entry - (config.REWARD_RATIO * abs(sl - entry))
                    qty    = risk.calculate_quantity(entry, sl)

                    if qty > 0:
                        print(f"[SELL] Entry: {entry} | SL: {sl} | Target: {target} | Qty: {qty}")
                        broker.place_sell_order(int(qty))
                        _set_trade("SELL", entry, sl, target, qty)
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

# Bot thread global level par start karo (Gunicorn ke liye)
print("[Startup] Starting bot thread...")
bot_thread = threading.Thread(target=start_bot, daemon=True)
bot_thread.start()
print("[Startup] Bot thread started.")

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
