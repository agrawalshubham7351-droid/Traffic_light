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

def place_stop_limit_order(side, stop_price, limit_price, quantity):
    """
    Entry ke liye Stop-Limit order.
    
    Parameters:
    -----------
    side : str
        'BUY' ya 'SELL' (Case-insensitive)
    stop_price : float
        Trigger price (jis par order active ho)
    limit_price : float
        Execution limit (is se bura price nahi milega)
    quantity : int
        Order size (contracts)
    """
    # side ko lowercase mein convert karo (Delta API expects 'buy' or 'sell')
    side = side.lower()
    
    order = delta_client.place_order(
        product_id=config.PRODUCT_ID,
        size=quantity,
        side=side,
        order_type=OrderType.STOP_LIMIT,
        stop_price=stop_price,
        limit_price=limit_price,
        reduce_only=False,   # Naya position open kar rahe hain
        time_in_force="GTC"  # Good Till Cancel
    )
    print(f"[Order] Stop-Limit {side.upper()} placed | Trigger: {stop_price} | Limit: {limit_price}")
    return order


# =========================
# STOP-MARKET ORDER (SL EXIT - GUARANTEED EXIT)
# =========================

def place_stop_market_order(side, stop_price, quantity):
    """
    Stop Loss ke liye Stop-Market order.
    Guaranteed exit deta hai, thodi slippage ho sakti hai par position band ho jayegi.
    
    Parameters:
    -----------
    side : str
        'BUY' (short cover karne ke liye) ya 'SELL' (long close karne ke liye)
    stop_price : float
        Trigger price (jis par order active ho)
    quantity : int
        Order size (contracts)
    """
    # side ko lowercase mein convert karo
    side = side.lower()
    
    order = delta_client.place_order(
        product_id=config.PRODUCT_ID,
        size=quantity,
        side=side,
        order_type=OrderType.STOP_MARKET,
        stop_price=stop_price,
        reduce_only=True,   # Sirf existing position close karega (safe guard)
        time_in_force="GTC"
    )
    print(f"[Order] Stop-Market {side.upper()} placed | Trigger: {stop_price}")
    return order
