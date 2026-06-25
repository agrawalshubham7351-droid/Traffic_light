# =========================
# BROKER.PY
# =========================
import config
from config import delta_client
from delta_rest_client import OrderType

def get_current_price():
    ticker = delta_client.get_ticker(config.SYMBOL)
    return float(ticker["mark_price"])

def get_balance():
    balance = delta_client.get_balances(3)
    return float(balance["available_balance"])

def get_position():
    position = delta_client.get_position(config.PRODUCT_ID)
    return position

def place_buy_order(quantity):
    order = delta_client.place_order(
        product_id=config.PRODUCT_ID,
        size=int(quantity),          # ✅ integer ensure karo
        side="buy",
        order_type=OrderType.MARKET
    )
    return order

def place_sell_order(quantity):
    order = delta_client.place_order(
        product_id=config.PRODUCT_ID,
        size=int(quantity),          # ✅ integer ensure karo
        side="sell",
        order_type=OrderType.MARKET
    )
    return order

def close_position():
    position = get_position()
    size = position["size"]
    if size == 0:
        print("No Open Position")
        return
    if size > 0:
        order = delta_client.place_order(
            product_id=config.PRODUCT_ID,
            size=abs(int(size)),
            side="sell",
            order_type=OrderType.MARKET
        )
        return order
    if size < 0:
        order = delta_client.place_order(
            product_id=config.PRODUCT_ID,
            size=abs(int(size)),
            side="buy",
            order_type=OrderType.MARKET
        )
        return order

def place_stop_limit_order(side, stop_price, limit_price, quantity):
    side = side.lower()
    order = delta_client.place_stop_order(
        product_id=config.PRODUCT_ID,
        size=int(quantity),
        side=side,
        stop_price=stop_price,
        limit_price=limit_price,
        order_type=OrderType.LIMIT
    )
    print(f"[Order] Stop-Limit {side.upper()} | Trigger: {stop_price} | Limit: {limit_price}")
    return order

def place_stop_market_order(side, stop_price, quantity):
    side = side.lower()
    order = delta_client.place_stop_order(
        product_id=config.PRODUCT_ID,
        size=int(quantity),
        side=side,
        stop_price=stop_price,
        order_type=OrderType.MARKET
    )
    print(f"[Order] Stop-Market {side.upper()} | Trigger: {stop_price}")
    return order
