"""
market_orders.py - thin wrapper exposing market order CLI-friendly function
"""
from .bot_core import BasicBot

def market_order(bot: BasicBot, symbol: str, side: str, qty: float):
    return bot.place_market_order(symbol, side, qty)
