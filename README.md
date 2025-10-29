# Simplified Binance Futures Testnet Trading Bot

This project is a simplified trading bot for Binance USDT-M Futures Testnet.

## Features
- Place MARKET and LIMIT orders on Binance Futures Testnet (USDT-M).
- Support for BUY and SELL sides.
- Simple STOP-LIMIT and OCO-like (two-order) implementations.
- CLI for placing orders.
- Request/response logging to `bot.log`.

## Structure
```
/src
  ├─ bot_core.py       # Core REST order logic (uses testnet base URL)
  ├─ market_orders.py
  ├─ limit_orders.py
  └─ /advanced
      └─ oco.py
bot.log
report.pdf
README.md
requirements.txt
```

## Setup
1. Create a Binance Futures Testnet account and generate API key/secret. Use the **Futures (USDT-M) Testnet** API and the base URL `https://testnet.binancefuture.com` as required.
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage examples
Place a market order:
```bash
python bot.py --api-key DHFzcB8LEYpDPB5MPXQ1mfl8kJchKb6DTKAYcpEDo2VOhEeS61ciuh5TdrhUTMb3 --api-secret 7AHGSvC2GyhhK6kBOoJJuiMiXwDlXmjZmT48sLpinNktO9EuSV4PXwMtbCCzewnL --type market --symbol BTCUSDT --side BUY --qty 0.001
```

Place a limit order:
```bash
python bot.py --api-key DHFzcB8LEYpDPB5MPXQ1mfl8kJchKb6DTKAYcpEDo2VOhEeS61ciuh5TdrhUTMb3 --api-secret 7AHGSvC2GyhhK6kBOoJJuiMiXwDlXmjZmT48sLpinNktO9EuSV4PXwMtbCCzewnL --type limit --symbol BTCUSDT --side SELL --qty 0.001 --price 107500
```

Stop-limit:
```bash
python bot.py --api-key DHFzcB8LEYpDPB5MPXQ1mfl8kJchKb6DTKAYcpEDo2VOhEeS61ciuh5TdrhUTMb3 --api-secret 7AHGSvC2GyhhK6kBOoJJuiMiXwDlXmjZmT48sLpinNktO9EuSV4PXwMtbCCzewnL --type stop_limit --symbol BTCUSDT --side SELL --qty 0.001 --stop_price 106500 --limit_price 106400
```

OCO (simple):
```bash
python bot.py --api-key DHFzcB8LEYpDPB5MPXQ1mfl8kJchKb6DTKAYcpEDo2VOhEeS61ciuh5TdrhUTMb3 --api-secret 7AHGSvC2GyhhK6kBOoJJuiMiXwDlXmjZmT48sLpinNktO9EuSV4PXwMtbCCzewnL --type oco --symbol BTCUSDT --side BUY --qty 0.001 --take_profit 107500 --stop_price 106800 --limit_price 106700
```

## Notes & Safety
- This tool sends real orders to the Binance Futures **testnet** when using testnet base URL; ensure your keys are for the testnet.
- Understand margin, leverage and trading risks. This code is educational and simplified for the assignment.
- Logging is written to `bot.log` in the project root.
