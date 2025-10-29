"""
limit_orders.py - thin wrapper exposing limit order CLI-friendly function
"""
from .bot_core import BasicBot

def limit_order(bot: BasicBot, symbol: str, side: str, qty: float, price: float):
    return bot.place_limit_order(symbol, side, qty, price)
