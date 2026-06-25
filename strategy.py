# =========================
# STRATEGY.PY (FULLY DEBUGGED & FIXED)
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
    
    # 🔥 FIX: 3 की जगह 5 candles fetch करो (safety ke liye)
    candles_to_fetch = 5
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

    # 📌 Bot -2 aur -3 candle use कर रहा है (2 पिछली पूरी हुई candles)
    candle_1 = df.iloc[-2]  # Immediate previous closed candle
    candle_2 = df.iloc[-3]  # Usse pehle wali closed candle

    # 🔥 DEBUG: हर बार ये Print होगा, ताकि आप Chart से Match कर सकें
    # API UTC time देता है, इसे IST (+5:30) में बदल रहे हैं
    t1 = time.strftime('%H:%M:%S', time.localtime(candle_1["time"] + 19800))
    t2 = time.strftime('%H:%M:%S', time.localtime(candle_2["time"] + 19800))
    
    c1_color = "GREEN" if is_green(candle_1) else "RED"
    c2_color = "GREEN" if is_green(candle_2) else "RED"
    
    print(f"[DEBUG] 📊 Candle -2: Time {t1} IST | Color: {c1_color} | Close: {candle_1['close']}")
    print(f"[DEBUG] 📊 Candle -3: Time {t2} IST | Color: {c2_color} | Close: {candle_2['close']}")

    # 🟢 Pair Check
    pair_bana = is_pair(candle_1, candle_2)

    if not pair_bana:
        print("[DEBUG] ❌ Pair NOT formed (colors are same, not opposite). Waiting for next candle.")
        return "NO SIGNAL", None, None, None

    print("[DEBUG] ✅ Pair FORMED! (Opposite colors detected)")

    # 📐 Range Calculate
    range_high, range_low = get_pair_range(candle_1, candle_2)

    # ⏳ Age Check (15 minute rule)
    current_time  = int(time.time())
    candle_1_time = int(candle_1["time"])
    pair_age_min  = (current_time - candle_1_time) // 60

    if pair_age_min > 15:
        print(f"[DEBUG] ⏳ Pair {pair_age_min} min purana (Limit 15 min). Ignoring this pair.")
        return "NO SIGNAL", None, None, None

    # 📏 Risk Check (Range Width)
    risk = range_high - range_low
    # 🔥 FIX: Print statement को Code के हिसाब से ठीक किया (300)
    if risk > 300:
        print(f"[DEBUG] 📏 Range width {risk} > 300. Skipping (too wide).")
        return "NO SIGNAL", None, None, None

    # ✅ सब ठीक है, अब Breakout Check करो
    print(f"[DEBUG] ✅ Valid Pair! Age: {pair_age_min}min, Range: {range_high}-{range_low} (Width: {risk})")
    print(f"[DEBUG] 💰 Current Price: {current_price}")

    # 🔥 FIX 2: '>' की जगह '>=' और '<' की जगह '<=' use करो (Exact touch पर भी Entry ले)
    if current_price >= range_high:
        print("[DEBUG] 🚀 BREAKOUT UP! Generating BUY signal.")
        return "BUY", range_high, range_low, candle_1_time

    if current_price <= range_low:
        print("[DEBUG] 🚀 BREAKOUT DOWN! Generating SELL signal.")
        return "SELL", range_high, range_low, candle_1_time

    # अगर Price Range के अंदर है
    print("[DEBUG] ⏳ Price is inside the range. Waiting for breakout.")
    return "NO SIGNAL", range_high, range_low, None
