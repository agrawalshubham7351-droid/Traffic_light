# =========================
# STRATEGY.PY
# =========================
import requests
import pandas as pd
import time
import config

# =========================
# FETCH DATA
# =========================
def get_candles():
    end_time = int(time.time())
    candles_to_fetch = 3
    timeframe_in_minutes = int(config.TIMEFRAME[:-1])
    start_time = end_time - (candles_to_fetch * timeframe_in_minutes * 60)

    r = requests.get(
        "https://api.india.delta.exchange/v2/history/candles",
        params={
            "resolution": config.TIMEFRAME,
            "symbol": config.SYMBOL,
            "start": start_time,
            "end": end_time
        }
    )
    data = r.json()
    df = pd.DataFrame(data["result"])
    df = df.sort_values("time").reset_index(drop=True)
    return df

# =========================
# HELPER FUNCTIONS
# =========================
def is_green(candle):
    return candle["close"] > candle["open"]

def is_red(candle):
    return candle["close"] < candle["open"]

def is_pair(current_candle, previous_candle):
    if is_green(current_candle) and is_red(previous_candle):
        return True
    if is_red(current_candle) and is_green(previous_candle):
        return True
    return False

def get_pair_range(candle1, candle2):
    range_high = max(candle1["high"], candle2["high"])
    range_low  = min(candle1["low"],  candle2["low"])
    return range_high, range_low

# =========================
# SIGNAL GENERATION
# =========================
def get_signal(df, current_price):
    if len(df) < 3:
        return "NO SIGNAL", None, None, None

    candle_1 = df.iloc[-2]  # last completed candle
    candle_2 = df.iloc[-3]  # usse pehle wali

    pair_bana = is_pair(candle_1, candle_2)

    if not pair_bana:
        return "NO SIGNAL", None, None, None

    range_high, range_low = get_pair_range(candle_1, candle_2)

    current_time  = int(time.time())
    candle_1_time = int(candle_1["time"])
    pair_age_min  = (current_time - candle_1_time) // 60

    if pair_age_min > 15:
        print(f"[Skip] Pair {pair_age_min} min purana — fresh pair ka wait karo")
        return "NO SIGNAL", None, None, None

    risk = range_high - range_low
    if risk > 300:
        print(f"[Skip] Risk {risk} > 100 — wide range, skip")
        return "NO SIGNAL", None, None, None

    # ✅ Jo pehle break ho — wahi entry
    if current_price > range_high:
        return "BUY", range_high, range_low, candle_1_time

    if current_price < range_low:
        return "SELL", range_high, range_low, candle_1_time

    return "NO SIGNAL", None, None, None
