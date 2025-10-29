"""
oco.py - simple demonstration of OCO-like behavior on Futures testnet by placing two orders
"""
from ..bot_core import BasicBot

def place_oco(bot: BasicBot, symbol: str, side: str, qty: float, take_profit: float, stop_price: float, stop_limit_price: float):
    return bot.place_oco(symbol, side, qty, take_profit, stop_price, stop_limit_price)
