# =========================
# BROKER.PY
# =========================

import config

from config import delta_client

from delta_rest_client import OrderType


# =========================
# CURRENT PRICE
# =========================

def get_current_price():

    ticker = delta_client.get_ticker(
        config.SYMBOL
    )

    return float(
        ticker["mark_price"]
    )







# =========================
# BALANCE (DEBUG VERSION)
# =========================

def get_balance():
    import requests
    import time
    import hashlib
    import hmac

    method = "GET"
    path = "/v2/wallet/balances"
    timestamp = str(int(time.time()))
    signature_data = method + timestamp + path
    signature = hmac.new(
        config.DELTA_API_SECRET.encode(),
        signature_data.encode(),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "api-key": config.DELTA_API_KEY,
        "timestamp": timestamp,
        "signature": signature,
        "User-Agent": "python-requests"
    }

    try:
        response = requests.get(
            "https://cdn-ind.testnet.deltaex.org" + path,
            headers=headers,
            timeout=10          # ⬅️ 10 seconds timeout
        )
        response.raise_for_status()   # agar 4xx/5xx aaye toh exception
        data = response.json()

        for asset in data["result"]:
            if asset["asset_symbol"] == "USD":
                return float(asset["available_balance"])

    except Exception as e:
        print(f"[ERROR] get_balance() failed: {e}")
        return 0.0

    return 0.0


# =========================
# BUY ORDER
# =========================

def place_buy_order(quantity):

    order = delta_client.place_order(
        product_id=config.PRODUCT_ID,
        size=quantity,
        side="buy",
        order_type=OrderType.MARKET
    )

    return order


# =========================
# SELL ORDER
# =========================

def place_sell_order(quantity):

    order = delta_client.place_order(
        product_id=config.PRODUCT_ID,
        size=quantity,
        side="sell",
        order_type=OrderType.MARKET
    )

    return order


# =========================
# CLOSE POSITION
# =========================

def close_position():

    position = get_position()

    size = position["size"]

    if size == 0:

        print("No Open Position")

        return

    if size > 0:

        order = delta_client.place_order(
            product_id=config.PRODUCT_ID,
            size=abs(size),
            side="sell",
            order_type=OrderType.MARKET
        )

        return order

    if size < 0:

        order = delta_client.place_order(
            product_id=config.PRODUCT_ID,
            size=abs(size),
            side="buy",
            order_type=OrderType.MARKET
        )

        return order
