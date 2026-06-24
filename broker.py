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
    balance = delta_client.get_balances(3)
    return float(balance["available_balance"])


# =========================
# POSITION
# =========================

def get_position():
    position = delta_client.get_position(
        config.PRODUCT_ID
    )
    return position


# =========================
# BUY ORDER (MARKET)
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
# SELL ORDER (MARKET)
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
# CLOSE POSITION (MARKET)
# =========================

def close_position():
    position = get_position()
    size = position["size"]

    if size == 0:
        print("No Open Position")
        return

    if size > 0:   # LONG position hai
        order = delta_client.place_order(
            product_id=config.PRODUCT_ID,
            size=abs(size),
            side="sell",
            order_type=OrderType.MARKET
        )
        return order

    if size < 0:   # SHORT position hai
        order = delta_client.place_order(
            product_id=config.PRODUCT_ID,
            size=abs(size),
            side="buy",
            order_type=OrderType.MARKET
        )
        return order


# =========================
# STOP-LIMIT ORDER (ENTRY - SLIPPAGE CONTROL)
# =========================

# =========================
# STOP-LIMIT ORDER (ENTRY - SLIPPAGE CONTROL)
# =========================

def place_stop_limit_order(side, stop_price, limit_price, quantity):
    """
    Entry ke liye Stop-Limit order.
    """
    side = side.lower()
    
    # ✅ FIX: 'stop_price' ki jagah 'trigger_price' use karo
    order = delta_client.place_order(
        product_id=config.PRODUCT_ID,
        size=quantity,
        side=side,
        order_type="stop_limit",
        trigger_price=stop_price,      # <--- CHANGE YAHAN
        limit_price=limit_price,
        reduce_only=False
    )
    print(f"[Order] Stop-Limit {side.upper()} placed | Trigger: {stop_price} | Limit: {limit_price}")
    return order


# =========================
# STOP-MARKET ORDER (SL EXIT - GUARANTEED EXIT)
# =========================

def place_stop_market_order(side, stop_price, quantity):
    """
    Stop Loss ke liye Stop-Market order.
    """
    side = side.lower()
    
    # ✅ FIX: 'stop_price' ki jagah 'trigger_price' use karo
    order = delta_client.place_order(
        product_id=config.PRODUCT_ID,
        size=quantity,
        side=side,
        order_type="stop_market",
        trigger_price=stop_price,      # <--- CHANGE YAHAN
        reduce_only=True
    )
    print(f"[Order] Stop-Market {side.upper()} placed | Trigger: {stop_price}")
    return order
