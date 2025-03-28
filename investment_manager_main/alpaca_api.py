"""
Alpaca API Utility Functions
Documentation:
- API Reference: https://alpaca.markets/docs/api-documentation/api-v2/
- GitHub SDK: https://github.com/alpacahq/alpaca-py
"""

import os
from alpaca_trade_api import REST
from dotenv import load_dotenv
import pandas as pd
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import pytz

load_dotenv()
API_KEY = os.getenv("ALPACA_API_KEY")
SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets") 
VALID_TIMEFRAMES = {"1Min", "5Min", "15Min", "1Hour", "1Day"}


api = REST(API_KEY, SECRET_KEY, BASE_URL)

def get_stock_price(symbol: str) -> Optional[float]:
    """
    Get the latest stock price for a given symbol.
    
    Args:
        symbol (str): Stock ticker symbol (e.g., "AAPL").
    
    Returns:
        Optional[float]: The latest trade price, or None if an error occurs.
    """
    try:
        trade = api.get_latest_trade(symbol)
        return trade.price if hasattr(trade, "price") else None
    except Exception as e:
        print(f"Error fetching stock price for {symbol}: {e}")
        return None

def get_historical_data(symbol: str, timeframe: str = "1Day", days: int = 7) -> Optional[pd.DataFrame]:        
    """
    Get historical stock data for a given symbol.
    
    Args:
        symbol (str): Stock ticker symbol.
        timeframe (str): Timeframe for data (e.g., "day", "hour", "minute").
        limit (int): Number of data points to fetch.
    
    Returns:
        Optional[pd.DataFrame]: DataFrame containing historical stock prices, or None if an error occurs.
    """
    try:
        end_date = datetime.now(pytz.UTC)
        start_date = end_date - timedelta(days=days)

        bars = api.get_bars(
            symbol,
            timeframe,
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            feed='iex'
        ).df

        if bars.empty:
            return None

        return bars
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {e}")
        return None



