# =========================
# 1. IMPORTS
# =========================

import os
from dotenv import load_dotenv

load_dotenv()


# =========================
# 2. CONFIG
# =========================

# API Keys
DELTA_API_KEY = os.getenv("DELTA_API_KEY")
DELTA_API_SECRET = os.getenv("DELTA_API_SECRET")

# Capital
CAPITAL = 100000

REWARD_RATIO = 2

# Risk Per Trade (%)
RISK_PER_TRADE = 2

# Symbol
SYMBOL = "BTCUSD"

# Timeframe
TIMEFRAME = "5m"


# =========================
# 3. BROKER CONNECTION
# =========================

from delta_rest_client import DeltaRestClient

delta_client = DeltaRestClient(
    # base_url="https://api.india.delta.exchange"
    base_url="https://cdn-ind.testnet.deltaex.org",
    api_key=DELTA_API_KEY,
    api_secret=DELTA_API_SECRET
)


# =========================
# VARIABLES
# =========================

order_in_progress = False

order_type = None

entry_price = None

stop_loss = None

target = None

quantity = 0

daily_pnl = 0