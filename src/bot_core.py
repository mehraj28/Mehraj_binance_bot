"""
Enhanced BasicBot core using Binance Futures Testnet REST API (USDT-M).
Now includes automatic notional-size validation and quantity adjustment.
"""

import time
import hmac
import hashlib
import requests
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class BasicBot:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True, base_url: str = "https://testnet.binancefuture.com"):
        self.api_key = api_key
        self.api_secret = api_secret.encode()
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-MBX-APIKEY": self.api_key}
        logger.info("BasicBot initialized for base_url=%s", self.base_url)

    # ---------------------------------------------
    # Utility functions
    # ---------------------------------------------

    def _sign_payload(self, payload: dict):
        payload = payload.copy()
        if "timestamp" not in payload:
            payload["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(payload, doseq=True)
        signature = hmac.new(self.api_secret, query_string.encode(), hashlib.sha256).hexdigest()
        payload["signature"] = signature
        return payload

    def _get(self, path: str, params: dict = None):
        url = f"{self.base_url}{path}"
        resp = requests.get(url, headers=self.headers, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: dict):
        url = f"{self.base_url}{path}"
        signed = self._sign_payload(payload)
        logger.debug("POST %s payload=%s", url, payload)
        resp = requests.post(url, headers=self.headers, params=signed, timeout=10)
        logger.info("Response %s %s", resp.status_code, resp.text)
        resp.raise_for_status()
        return resp.json()

    # ---------------------------------------------
    # Market Data Helpers
    # ---------------------------------------------

    def get_symbol_info(self, symbol: str):
        """Fetch trading rules and filters for a given symbol."""
        info = self._get("/fapi/v1/exchangeInfo")
        for s in info["symbols"]:
            if s["symbol"] == symbol.upper():
                return s
        raise ValueError(f"Symbol {symbol} not found in exchangeInfo")

    def get_price(self, symbol: str) -> float:
        """Get current market price for a symbol."""
        data = self._get("/fapi/v1/ticker/price", {"symbol": symbol.upper()})
        return float(data["price"])

    # ---------------------------------------------
    # Validation Helpers
    # ---------------------------------------------

    def _validate_quantity(self, symbol: str, quantity: float):
        """
        Ensures quantity meets Binance Futures filters:
        - minQty
        - stepSize
        - minimum notional value (minQty * price)
        """
        info = self.get_symbol_info(symbol)
        price = self.get_price(symbol)

        filters = {f["filterType"]: f for f in info["filters"]}
        min_qty = float(filters["LOT_SIZE"]["minQty"])
        step_size = float(filters["LOT_SIZE"]["stepSize"])

        # Some markets use "MARKET_LOT_SIZE" instead
        if "MARKET_LOT_SIZE" in filters:
            min_qty = float(filters["MARKET_LOT_SIZE"]["minQty"])
            step_size = float(filters["MARKET_LOT_SIZE"]["stepSize"])

        # Futures don't always return minNotional, but let's enforce at least a $5 minimum
        min_notional = 5.0
        notional_value = price * quantity

        if notional_value < min_notional:
            new_qty = round(min_notional / price / step_size) * step_size
            logger.warning(
                f"⚠️ Quantity too small: {quantity} ({notional_value:.2f} USDT). Adjusted to {new_qty} for min notional {min_notional}."
            )
            quantity = new_qty

        # Snap to step size
        quantity = (quantity // step_size) * step_size
        if quantity < min_qty:
            logger.warning(f"⚠️ Quantity below minQty. Adjusted to {min_qty}.")
            quantity = min_qty

        return round(quantity, 8)

    # ---------------------------------------------
    # Order Placement
    # ---------------------------------------------

    def place_market_order(self, symbol: str, side: str, quantity: float, reduce_only: bool = False):
        assert side.upper() in ("BUY", "SELL"), "side must be BUY or SELL"
        quantity = self._validate_quantity(symbol, quantity)
        payload = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": "MARKET",
            "quantity": quantity,
            "reduceOnly": str(reduce_only).lower(),
        }
        return self._post("/fapi/v1/order", payload)

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float, time_in_force: str = "GTC", reduce_only: bool = False):
        assert side.upper() in ("BUY", "SELL"), "side must be BUY or SELL"
        quantity = self._validate_quantity(symbol, quantity)
        payload = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": "LIMIT",
            "quantity": quantity,
            "price": str(price),
            "timeInForce": time_in_force,
            "reduceOnly": str(reduce_only).lower(),
        }
        return self._post("/fapi/v1/order", payload)

    def place_stop_limit_order(self, symbol: str, side: str, quantity: float, stop_price: float, limit_price: float, time_in_force: str = "GTC", reduce_only: bool = False):
        assert side.upper() in ("BUY", "SELL"), "side must be BUY or SELL"
        quantity = self._validate_quantity(symbol, quantity)
        payload = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": "STOP",
            "quantity": quantity,
            "price": str(limit_price),
            "stopPrice": str(stop_price),
            "timeInForce": time_in_force,
            "reduceOnly": str(reduce_only).lower(),
        }
        return self._post("/fapi/v1/order", payload)

    def place_oco(self, symbol: str, side: str, quantity: float, take_profit_price: float, stop_price: float, stop_limit_price: float, stop_limit_time_in_force: str = "GTC"):
        assert side.upper() in ("BUY", "SELL"), "side must be BUY or SELL"
        quantity = self._validate_quantity(symbol, quantity)

        tp_side = "SELL" if side.upper() == "BUY" else "BUY"
        sl_side = tp_side

        logger.info("Placing take-profit LIMIT order")
        tp = self.place_limit_order(symbol, tp_side, quantity, take_profit_price, time_in_force="GTC", reduce_only=True)

        logger.info("Placing stop-limit (stop-loss) order")
        sl = self.place_stop_limit_order(symbol, sl_side, quantity, stop_price, stop_limit_price, time_in_force=stop_limit_time_in_force, reduce_only=True)

        return {"take_profit": tp, "stop_loss": sl}
