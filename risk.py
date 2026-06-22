# =========================
# RISK.PY
# =========================

import config
from broker import get_balance


# =========================
# RISK AMOUNT
# =========================

def calculate_risk_amount():

    capital = get_balance()

    risk_amount = (
        capital
        * config.RISK_PER_TRADE
        / 100
    )

    print(f"Live Balance: {capital}")
    print(f"Risk Amount: {risk_amount}")

    return risk_amount


# =========================
# QUANTITY CALCULATION
# =========================

def calculate_quantity(
    entry_price,
    stop_loss
):

    risk_amount = calculate_risk_amount()

    stop_distance = abs(
        entry_price - stop_loss
    )

    if stop_distance == 0:
        return 0

    quantity = (
        risk_amount
        / stop_distance
    )

    return quantity


# =========================
# BREAK EVEN
# =========================

def move_to_break_even(
    entry_price,
    current_price,
    stop_loss
):

    risk = abs(
        entry_price - stop_loss
    )

    reward = abs(
        current_price - entry_price
    )

    if reward >= risk:
        return entry_price

    return stop_loss
