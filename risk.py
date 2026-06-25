# =========================
# RISK.PY
# =========================
import config
from broker import get_balance

def calculate_risk_amount():
    capital = get_balance()
    risk_amount = capital * config.RISK_PER_TRADE / 100
    print(f"Live Balance: {capital}")
    print(f"Risk Amount: {risk_amount}")
    return risk_amount

def calculate_quantity(entry_price, stop_loss):
    risk_amount   = calculate_risk_amount()
    stop_distance = abs(entry_price - stop_loss)
    if stop_distance == 0:
        return 0
    # ✅ Delta futures = USD contracts, 1 contract = 1 USD
    # quantity = risk_amount / stop_distance gives contracts
    quantity = risk_amount / stop_distance
    quantity = max(1, int(quantity))  # ✅ integer, minimum 1
    return quantity

def move_to_break_even(entry_price, current_price, stop_loss):
    risk   = abs(entry_price - stop_loss)
    reward = abs(current_price - entry_price)
    if reward >= risk:
        return entry_price
    return stop_loss
