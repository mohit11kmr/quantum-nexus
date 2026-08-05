import yfinance as yf
import pandas as pd
import numpy as np
import random
import time
from typing import Dict, Any, List

POPULAR_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", 
    "HUL.NS", "SBI.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "ITC.NS",
    "KOTAKBANK.NS", "LT.NS", "AXISBANK.NS", "MARUTI.NS"
]

def fetch_stock_data(symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
    """Fetch historical stock data."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return pd.DataFrame()
        df.reset_index(inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def generate_synthetic_stock_data(symbol: str, days: int = 100, interval: str = "1d") -> pd.DataFrame:
    """Generate synthetic stock data for testing."""
    dates = pd.date_range(end=pd.Timestamp.today(), periods=days, freq='B')
    base_price = 1000.0
    close = [base_price]
    for _ in range(1, days):
        change = random.uniform(-0.02, 0.02)
        close.append(close[-1] * (1 + change))
    
    high = [c * random.uniform(1.0, 1.02) for c in close]
    low = [c * random.uniform(0.98, 1.0) for c in close]
    open_price = [random.uniform(l, h) for l, h in zip(low, high)]
    volume = [random.randint(10000, 1000000) for _ in range(days)]
    
    df = pd.DataFrame({
        "Date": dates,
        "Open": open_price,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume
    })
    return df

def fetch_live_quote(symbol: str) -> Dict[str, Any]:
    """Fetch live quote for a given symbol."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "symbol": symbol,
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0.0)),
            "previous_close": info.get("previousClose", 0.0),
            "volume": info.get("volume", 0),
            "timestamp": time.time()
        }
    except Exception as e:
        print(f"Error fetching quote for {symbol}: {e}")
        return {"symbol": symbol, "error": str(e)}
