"""
bot.py - Command-line interface to interact with BasicBot for placing orders. I Have added automatic notional adjustment for orders below Binance Futures minimum notional value. I have mentioned api key and secret in the
Usage examples:
python bot.py --api-key DHFzcB8LEYpDPB5MPXQ1mfl8kJchKb6DTKAYcpEDo2VOhEeS61ciuh5TdrhUTMb3 --api-secret 7AHGSvC2GyhhK6kBOoJJuiMiXwDlXmjZmT48sLpinNktO9EuSV4PXwMtbCCzewnL --type market --symbol BTCUSDT --side BUY --qty 0.001

python bot.py --api-key DHFzcB8LEYpDPB5MPXQ1mfl8kJchKb6DTKAYcpEDo2VOhEeS61ciuh5TdrhUTMb3 --api-secret 7AHGSvC2GyhhK6kBOoJJuiMiXwDlXmjZmT48sLpinNktO9EuSV4PXwMtbCCzewnL --type limit --symbol BTCUSDT --side SELL --qty 0.001 --price 107500

python bot.py --api-key DHFzcB8LEYpDPB5MPXQ1mfl8kJchKb6DTKAYcpEDo2VOhEeS61ciuh5TdrhUTMb3 --api-secret 7AHGSvC2GyhhK6kBOoJJuiMiXwDlXmjZmT48sLpinNktO9EuSV4PXwMtbCCzewnL --type stop_limit --symbol BTCUSDT --side SELL --qty 0.001 --stop_price 106500 --limit_price 106400

python bot.py --api-key DHFzcB8LEYpDPB5MPXQ1mfl8kJchKb6DTKAYcpEDo2VOhEeS61ciuh5TdrhUTMb3 --api-secret 7AHGSvC2GyhhK6kBOoJJuiMiXwDlXmjZmT48sLpinNktO9EuSV4PXwMtbCCzewnL --type oco --symbol BTCUSDT --side BUY --qty 0.001 --take_profit 107500 --stop_price 106800 --limit_price 106700
"""

import argparse
import logging
import requests
from src.bot_core import BasicBot

logging.basicConfig(filename="bot.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def parse_args():
    p = argparse.ArgumentParser(description="Simplified Binance Futures Testnet Trading Bot CLI")
    p.add_argument("--api-key", required=True)
    p.add_argument("--api-secret", required=True)
    p.add_argument("--type", required=True, choices=["market","limit","stop_limit","oco"], help="order type")
    p.add_argument("--symbol", required=True, help="Trading pair, e.g., BTCUSDT")
    p.add_argument("--side", required=True, choices=["BUY","SELL"])
    p.add_argument("--qty", required=True, type=float)
    p.add_argument("--price", type=float, help="Limit price (for limit orders)")
    p.add_argument("--stop_price", type=float, help="Stop price (for stop/stop-limit)")
    p.add_argument("--limit_price", type=float, help="Limit price for stop-limit or OCO stop-limit leg")
    p.add_argument("--take_profit", type=float, help="Take profit price for OCO")
    return p.parse_args()

def main():
    args = parse_args()
    bot = BasicBot(args.api_key, args.api_secret, testnet=True)

    try:
        min_notional = 100  # Binance Futures min notional (USD value)

        # --- Validate and adjust notional automatically ---
        if args.type == "limit":
            if args.price is None:
                raise ValueError("Price required for limit order")
            notional = args.price * args.qty
            if notional < min_notional:
                new_qty = round(min_notional / args.price, 3)
                print(f"[⚠️] Notional ${notional:.2f} < ${min_notional}. Adjusting qty from {args.qty} → {new_qty}")
                args.qty = new_qty

        elif args.type == "stop_limit":
            if args.stop_price is None or args.limit_price is None:
                raise ValueError("stop_price and limit_price required for stop-limit order")
            notional = args.limit_price * args.qty
            if notional < min_notional:
                new_qty = round(min_notional / args.limit_price, 3)
                print(f"[⚠️] Notional ${notional:.2f} < ${min_notional}. Adjusting qty from {args.qty} → {new_qty}")
                args.qty = new_qty

        elif args.type == "oco":
            if args.take_profit is None or args.stop_price is None or args.limit_price is None:
                raise ValueError("take_profit, stop_price, and limit_price required for OCO order")
            notional = args.take_profit * args.qty
            if notional < min_notional:
                new_qty = round(min_notional / args.take_profit, 3)
                print(f"[⚠️] Notional ${notional:.2f} < ${min_notional}. Adjusting qty from {args.qty} → {new_qty}")
                args.qty = new_qty

        # --- Execute orders ---
        if args.type == "market":
            r = bot.place_market_order(args.symbol, args.side, args.qty)

        elif args.type == "limit":
            r = bot.place_limit_order(args.symbol, args.side, args.qty, args.price)

        elif args.type == "stop_limit":
            r = bot.place_stop_limit_order(
                symbol=args.symbol,
                side=args.side,
                quantity=args.qty,
                stop_price=args.stop_price,
                limit_price=args.limit_price
            )

        elif args.type == "oco":
            r = bot.place_oco(
                args.symbol,
                args.side,
                args.qty,
                args.take_profit,
                args.stop_price,
                args.limit_price
            )

        print("✅ Order response:", r)

    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            print("❌ Binance Error Response:", e.response.text)
            logger.error("Binance HTTP Error: %s", e.response.text)
        else:
            print("❌ HTTP Error:", e)
    except Exception as e:
        logger.exception("Error placing order: %s", e)
        print("❌ Unexpected Error:", e)

if __name__ == "__main__":
    main()
