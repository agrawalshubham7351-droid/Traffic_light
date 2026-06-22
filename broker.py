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

def get_balance():

    wallet = delta_client.get_wallet()

    balance = float(
        wallet["balance"]
    )

    return balance



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
