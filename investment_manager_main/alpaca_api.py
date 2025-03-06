"""Documentation for Alpaca API: 
https://alpaca.markets/docs/api-documentation/api-v2/
https://github.com/alpacahq/alpaca-py"""

import os
from alpaca_trade_api import REST
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_BASE_URL")


api = REST(API_KEY, SECRET_KEY, BASE_URL)


def get_stock_price(symbol):
    barset = api.get_latest_trade(symbol)
    return barset.price  


def get_historical_data(symbol, timeframe="day", limit=30):
    bars = api.get_bars(symbol, timeframe, limit=limit).df
    return bars


def place_mock_trade(symbol, qty, side="buy"):
    order = api.submit_order(
        symbol=symbol,
        qty=qty,
        side=side,
        type="market",
        time_in_force="gtc" 
    )
    return order
