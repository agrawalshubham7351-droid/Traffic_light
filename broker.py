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
# BALANCE
# =========================

# # BAAD (sahi)
# def get_balance():
#     balances = delta_client.get_balances()
#     for asset in balances:
#         if asset["asset_symbol"] == "USDT":
#             return float(asset["available_balance"])
# #     return 0.0
# def get_balance():
#     balance = delta_client.get_balances(config.USDT_ASSET_ID)
#     return float(balance["available_balance"])
# def get_balance():
#     balance = delta_client.get_balances(config.USDT_ASSET_ID)
#     print(f"[DEBUG] balance response: {balance}")   # <-- ye line add kar
#     return float(balance["available_balance"])
def get_balance():
    try:
        balance = delta_client.get_balances(config.USDT_ASSET_ID)
        print(f"[DEBUG] balance response: {balance}", flush=True)
        return float(balance["available_balance"])
    except Exception as e:
        print(f"[DEBUG] get_balance ERROR: {type(e).__name__}: {e}", flush=True)
        return 0.0

# =========================
# POSITION
# =========================

def get_position():

    position = delta_client.get_position(
        config.PRODUCT_ID
    )

    return position


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

    # Long Position Close
    if size > 0:

        order = delta_client.place_order(
            product_id=config.PRODUCT_ID,
            size=abs(size),
            side="sell",
            order_type=OrderType.MARKET
        )

        return order

    # Short Position Close
    if size < 0:

        order = delta_client.place_order(
            product_id=config.PRODUCT_ID,
            size=abs(size),
            side="buy",
            order_type=OrderType.MARKET
        )

        return order
