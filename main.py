# =========================
# MAIN.PY (FINAL FIXED)
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

LOOP_INTERVAL   = 30
PRODUCT_ID      = 84
STATE_FILE      = "trade_state.json"
SLIPPAGE_BUFFER = 0.002

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
        size = position.get("size", 0)

        if size == 0:
            print("[Entry] No position found on exchange.")
            return None

        entry_price = position.get("entry_price")

        if entry_price is None:
            print("[Entry] Entry price is None (order might be pending).")
            return None

        entry_price = float(entry_price)

        if size < 0:
            entry_price = abs(entry_price)

        print(f"[Entry] Real entry price from exchange: {entry_price}")
        return entry_price
    except Exception as e:
        print(f"[Entry] Could not fetch real entry price: {e}")
        return None


# =========================
# HELPER: CONFIRM POSITION CLOSED
# =========================

def _wait_for_position_close(max_attempts=6, delay=1):
    for attempt in range(max_attempts):
        time.sleep(delay)
        try:
            pos = broker.get_position()
            if pos.get("size", 0) == 0:
                print("[Close] Position confirmed closed.")
                return True
        except Exception as e:
            print(f"[Close] Error checking position: {e}")

    print("[Close] WARNING: Position might still be open. Check manually.")
    return False


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

    # ✅ Pair tracking variables
    pair_entry_taken = False
    last_pair_time   = None

    # --- Startup: Check for existing open position ---
    print("[Startup] Checking for existing position...")
    try:
        position = broker.get_position()
        size = position["size"]

        if size != 0:
            restored = _load_state()
            if not restored:
                print("[Startup] No state file found. Monitoring position without SL/Target.")
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
            # STEP 1.5 — SELF-HEALING
            # ----------------------------
            try:
                actual_position = broker.get_position()
                actual_size = actual_position["size"]

                if actual_size == 0 and config.order_in_progress:
                    print("[SYNC] Exchange shows NO position, but bot thought trade was open. Resetting...")
                    _reset_trade(pnl=0)
                    pair_entry_taken = False  # ✅ reset on sync

                elif actual_size != 0 and not config.order_in_progress:
                    print("[SYNC] Exchange shows OPEN position, but bot has no state. Recovering...")
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

                    # --- EXIT: LONG ---
                    if config.order_type == "BUY":

                        if current_price >= config.target:
                            print("[EXIT] Target hit — closing LONG")
                            broker.close_position()
                            _wait_for_position_close()
                            _reset_trade(pnl=+abs(config.target - config.entry_price) * config.quantity)
                            pair_entry_taken = False  # ✅ reset after trade closes

                        elif current_price <= config.stop_loss:
                            print("[EXIT] Stop Loss hit — Placing Stop-Market order")
                            side = "SELL"
                            qty_to_close = abs(config.quantity) if config.quantity else 0
                            if qty_to_close > 0:
                                broker.place_stop_market_order(side, config.stop_loss, qty_to_close)
                                _wait_for_position_close()
                                _reset_trade(pnl=-abs(config.entry_price - config.stop_loss) * config.quantity)
                                pair_entry_taken = False  # ✅ reset after trade closes
                            else:
                                print(f"[EXIT] Cannot close - invalid quantity: {config.quantity}")
                                _reset_trade(pnl=0)

                    # --- EXIT: SHORT ---
                    elif config.order_type == "SELL":

                        if current_price <= config.target:
                            print("[EXIT] Target hit — closing SHORT")
                            broker.close_position()
                            _wait_for_position_close()
                            _reset_trade(pnl=+abs(config.entry_price - config.target) * config.quantity)
                            pair_entry_taken = False  # ✅ reset after trade closes

                        elif current_price >= config.stop_loss:
                            print("[EXIT] Stop Loss hit — Placing Stop-Market order")
                            side = "BUY"
                            qty_to_close = abs(config.quantity) if config.quantity else 0
                            if qty_to_close > 0:
                                broker.place_stop_market_order(side, config.stop_loss, qty_to_close)
                                _wait_for_position_close()
                                _reset_trade(pnl=-abs(config.stop_loss - config.entry_price) * config.quantity)
                                pair_entry_taken = False  # ✅ reset after trade closes
                            else:
                                print(f"[EXIT] Cannot close - invalid quantity: {config.quantity}")
                                _reset_trade(pnl=0)


            # ----------------------------
            # STEP 3 — Look for new signal
            # ----------------------------

            else:

                df = strategy.get_candles()

                # ✅ 4 values ab return hoti hain
                signal, range_high, range_low, pair_time = strategy.get_signal(df, current_price)

                # ✅ Naya pair detect karo — flag reset karo
                if pair_time != last_pair_time:
                    pair_entry_taken = False
                    last_pair_time   = pair_time
                    print(f"[Pair] Naya pair detected at time {pair_time}")

                # ✅ Agar is pair pe entry already le li hai toh ignore karo
                if pair_entry_taken:
                    signal = "NO SIGNAL"
                    print("[Pair] Entry already taken for this pair — ignoring")

                print(f"[Signal] {signal} | Range High: {range_high} | Range Low: {range_low}")

                # --- ENTRY: LONG ---
                if signal == "BUY":

                    temp_entry = current_price
                    sl         = range_low
                    target     = temp_entry + (config.REWARD_RATIO * abs(temp_entry - sl))
                    qty        = risk.calculate_quantity(temp_entry, sl)

                    if qty > 0:
                        qty_btc = max(0.001, round(qty, 4))
                        

                        if range_high <= current_price:
                            print(f"[BUY] Trigger already breached. Placing MARKET order.")
                            broker.place_buy_order(qty_btc)

                            time.sleep(2)
                            real_entry = _get_real_entry_price()
                            if real_entry is not None:
                                real_sl     = sl
                                real_target = real_entry + (config.REWARD_RATIO * abs(real_entry - real_sl))
                                real_qty    = risk.calculate_quantity(real_entry, real_sl)
                                real_qty_int = max(1, int(real_qty))
                                _set_trade("BUY", real_entry, real_sl, real_target, real_qty_int)
                            else:
                                print("[BUY] Could not fetch real entry. Using temporary entry.")
                                _set_trade("BUY", temp_entry, sl, target, qty)

                        else:
                            trigger_price = range_high
                            limit_price   = range_high * (1 + SLIPPAGE_BUFFER)
                            print(f"[BUY] Stop-Limit: Trigger {trigger_price}, Limit {limit_price}, Qty {qty_int}")
                            broker.place_stop_limit_order("BUY", trigger_price, limit_price, qty_int)

                            time.sleep(5)
                            real_entry = None
                            for attempt in range(3):
                                real_entry = _get_real_entry_price()
                                if real_entry is not None:
                                    break
                                time.sleep(2)

                            if real_entry is not None:
                                real_sl      = sl
                                real_target  = real_entry + (config.REWARD_RATIO * abs(real_entry - real_sl))
                                real_qty     = risk.calculate_quantity(real_entry, real_sl)
                                real_qty_int = max(1, int(real_qty))
                                _set_trade("BUY", real_entry, real_sl, real_target, real_qty_int)
                            else:
                                print("[BUY] Could not fetch real entry. Using temporary entry.")
                                _set_trade("BUY", temp_entry, sl, target, qty)

                        pair_entry_taken = True  # ✅ is pair pe dobara entry nahi leni

                    else:
                        print("[BUY] Qty = 0, skipping order")


                # --- ENTRY: SHORT ---
                elif signal == "SELL":

                    temp_entry = current_price
                    sl         = range_high
                    target     = temp_entry - (config.REWARD_RATIO * abs(sl - temp_entry))
                    qty        = risk.calculate_quantity(temp_entry, sl)

                    if qty > 0:
                        qty_btc = max(0.001, round(qty, 4))

                        if range_low >= current_price:
                            print(f"[SELL] Trigger already breached. Placing MARKET order.")
                            broker.place_sell_order(qty_btc)

                            time.sleep(2)
                            real_entry = _get_real_entry_price()
                            if real_entry is not None:
                                real_sl      = sl
                                real_target  = real_entry - (config.REWARD_RATIO * abs(real_sl - real_entry))
                                real_qty     = risk.calculate_quantity(real_entry, real_sl)
                                real_qty_int = max(1, int(real_qty))
                                _set_trade("SELL", real_entry, real_sl, real_target, real_qty_int)
                            else:
                                print("[SELL] Could not fetch real entry. Using temporary entry.")
                                _set_trade("SELL", temp_entry, sl, target, qty)

                        else:
                            trigger_price = range_low
                            limit_price   = range_low * (1 - SLIPPAGE_BUFFER)
                            print(f"[SELL] Stop-Limit: Trigger {trigger_price}, Limit {limit_price}, Qty {qty_int}")
                            broker.place_stop_limit_order("SELL", trigger_price, limit_price, qty_int)

                            time.sleep(5)
                            real_entry = None
                            for attempt in range(3):
                                real_entry = _get_real_entry_price()
                                if real_entry is not None:
                                    break
                                time.sleep(2)

                            if real_entry is not None:
                                real_sl      = sl
                                real_target  = real_entry - (config.REWARD_RATIO * abs(real_sl - real_entry))
                                real_qty     = risk.calculate_quantity(real_entry, real_sl)
                                real_qty_int = max(1, int(real_qty))
                                _set_trade("SELL", real_entry, real_sl, real_target, real_qty_int)
                            else:
                                print("[SELL] Could not fetch real entry. Using temporary entry.")
                                _set_trade("SELL", temp_entry, sl, target, qty)

                        pair_entry_taken = True  # ✅ is pair pe dobara entry nahi leni

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
