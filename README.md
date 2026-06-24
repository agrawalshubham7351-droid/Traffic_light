# 🚦 Traffic Light Pairs Trading Bot

> **A fully automated, modular algorithmic trading bot designed for Delta Exchange (BTCUSD). Executes a proprietary breakout strategy with dynamic risk management, slippage control, and automated stop-loss protection.**

---

## 📌 Project Overview

This bot is not just a script; it is a **production-ready trading system** built for quantitative execution. It identifies specific **"2-Candle Opposite Color Breakout"** patterns, enters trades using **Stop-Limit Orders** to control slippage, and dynamically manages risk using a **1:2 Risk-Reward Ratio** with a **Trailing Break-Even** mechanism.

**Current Status:** Live on Render.com, fetching real-time data from Delta Exchange API.

---

## 🧠 Core Strategy Logic (The "Alpha")

1. **Pattern Recognition (`strategy.py`)**:
   - Fetches the last 3 closed candles.
   - Detects a "Pair" when the 2 most recent completed candles (`candle_1` & `candle_2`) have **Opposite Colors** (one Green, one Red).
   - Calculates the **Range High** and **Range Low** of this pair.

2. **Entry Execution (`main.py` & `broker.py`)**:
   - If the current live price **breaks above** the `Range High` → **BUY (Long)** signal.
   - If the current live price **breaks below** the `Range Low` → **SELL (Short)** signal.
   - Orders are placed as **Stop-Limit Orders** with a 0.05% buffer to significantly reduce negative slippage during volatile moves.

3. **Risk & Trade Management (`risk.py` & `main.py`)**:
   - **Fixed Risk:** Risks exactly **2%** of the current portfolio balance per trade.
   - **Break-Even Trailing:** Once the trade hits a **1:1 Profit (Risk = Reward)**, the Stop-Loss automatically moves to the **Entry Price**, making the trade completely risk-free.
   - **Risk-Reward Ratio (R:R):** Configurable, currently set to **1:2**.
   - **Guaranteed Stop-Loss:** Uses **Stop-Market Orders** for exits to ensure positions are closed immediately if the price moves against the strategy, preventing catastrophic losses.

4. **State Management (Crash Recovery)**:
   - Saves the current trade state (`entry_price`, `sl`, `target`, `qty`) to a `trade_state.json` file.
   - If the server restarts (Render deployment), the bot **automatically recovers** the open position and continues monitoring the Stop-Loss and Target without manual intervention.

---

## 📁 Project Architecture (Modular Design)

- **`config.py`**: Centralized configuration (API keys, Symbol, Timeframe, Risk parameters).
- **`strategy.py`**: Pure data fetching and pattern recognition logic. No exchange logic here.
- **`risk.py`**: Calculates position sizing (quantity) based on risk % and handles Break-Even logic.
- **`broker.py`**: Exchange interface layer. Handles Market, Stop-Market, and Stop-Limit orders.
- **`main.py`**: The orchestrator. Runs the infinite loop, manages trade lifecycle (Entry -> BreakEven -> Exit), and hosts a Flask web server for Render health checks.

---

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Frameworks:** Flask (Web Server), Pandas (Data Manipulation)
- **Exchange API:** Delta Rest Client
- **Deployment:** Render (Gunicorn + Threading)
- **Key Libraries:** `requests`, `json`, `threading`, `time`

---

## 🔧 How to Run (Local Setup)

1.  Clone the repository:
    ```bash
    git clone https://github.com/agrawalshubham7351-droid/Traffic_light.git
    cd Traffic_light


---

## 🧠 Core Strategy Logic (The "Alpha")

This bot doesn't just follow random indicators; it executes a specific market microstructure strategy:

1. **Pattern Recognition (`strategy.py`)**:
   - Fetches the last 3 closed candles from Delta Exchange.
   - Detects a **"Pair"** when the 2 most recent completed candles (`candle_1` and `candle_2`) have **Opposite Colors** (one Green, one Red).
   - Calculates the **Range High** and **Range Low** of this specific pair.

2. **Entry Execution (`main.py` & `broker.py`)**:
   - **BUY (Long):** Triggers when the current live price breaks **above** the `Range High`.
   - **SELL (Short):** Triggers when the current live price breaks **below** the `Range Low`.
   - **Slippage Control:** Entries are executed using **Stop-Limit Orders** with a built-in 0.05% buffer. This ensures the order gets filled even during fast movements, without suffering from extreme slippage.

3. **Advanced Risk & Trade Management (`risk.py`)**:
   - **Fixed Fractional Risk:** Risks exactly **2%** of the current portfolio balance per trade (Position sizing adjusts automatically).
   - **Dynamic Break-Even:** Once the trade hits a **1:1 Profit (Risk = Reward)**, the Stop-Loss automatically moves to the **Entry Price**. The trade becomes completely risk-free, allowing profits to run.
   - **Risk-Reward Ratio (R:R):** Configurable, currently set to a strict **1:2** (Risking 1 to make 2).
   - **Guaranteed Stop-Loss:** Uses **Stop-Market Orders** for exits. We prioritize *guaranteed exit* over perfect price to protect capital during flash crashes.

4. **Crash Recovery (State Management)**:
   - Saves active trade details (`entry_price`, `sl`, `target`) to a `trade_state.json` file.
   - If the Render server restarts, the bot **automatically recovers** the open position and continues monitoring the Stop-Loss and Target without any manual intervention.

---

## ⚠️ Real-World Execution Logic (Slippage & Market Impact)

Unlike backtesting scripts that assume perfect fills, this bot is built for **real-market conditions**:

- **Entry Buffer:** Uses `STOP_LIMIT` orders with a 0.05% buffer to prevent "Missed Fills" during extreme spikes, keeping slippage negligible.
- **Post-Only Fallback:** Includes logic to handle exchange "Post-Only" mode by falling back to Limit Orders when Market orders are temporarily restricted.
- **Capital Preservation:** Stop-Loss is strictly enforced via `STOP_MARKET` orders. We accept minor slippage on exits to ensure the position is closed, avoiding catastrophic account drawdowns.

---

## 📈 Why This Project Matters (My Edge)

This repository represents my complete approach to **Quantitative Trading**:

- **From Logic to Code:** I define the market microstructure logic (the "Alpha"), and utilize modern development tools to translate complex mathematics into efficient, production-level Python code.
- **Focus on Risk:** Unlike typical retail "signals," this bot emphasizes **risk-first architecture** (Break-Even, Position Sizing, Slippage Control).
- **Living Infrastructure:** This isn't a static script; it's a constantly monitored trading system running 24/7 on the cloud, with modular code that allows for rapid strategy upgrades without breaking the core engine.

---

## 📬 Connect & Feedback

- **Developer:** Shubham Agrawal
- **Platform:** Delta Exchange (Testnet / Mainnet)
- *This project is actively maintained and updated based on live market feedback.*

    
