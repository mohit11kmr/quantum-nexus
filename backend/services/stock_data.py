import yfinance as yf
import pandas as pd
import numpy as np
import random
import time
from typing import Dict, Any, List

POPULAR_STOCKS = [
    "NIFTY", "BANKNIFTY", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", 
    "ICICIBANK.NS", "HUL.NS", "SBI.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "ITC.NS"
]

def normalize_symbol(symbol: str) -> str:
    """Normalize trading symbols for Yahoo Finance."""
    sym = symbol.strip().upper()
    if sym in ["NIFTY", "NIFTY50", "NIFTY 50", "^NSEI"]:
        return "^NSEI"
    if sym in ["BANKNIFTY", "NIFTYBANK", "NIFTY BANK", "^NSEBANK"]:
        return "^NSEBANK"
    if sym in ["FINNIFTY", "^CNXFIN"]:
        return "^CNXFIN"
    if not sym.startswith("^") and not sym.endswith(".NS") and not sym.endswith(".BO"):
        return f"{sym}.NS"
    return sym

def fetch_stock_data(symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
    """Fetch historical stock data with symbol normalization."""
    norm_sym = normalize_symbol(symbol)
    try:
        ticker = yf.Ticker(norm_sym)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return pd.DataFrame()
        df.reset_index(inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol} ({norm_sym}): {e}")
        return pd.DataFrame()

def generate_synthetic_stock_data(symbol: str, days: int = 100, interval: str = "1d") -> pd.DataFrame:
    """Generate synthetic stock data for testing."""
    dates = pd.date_range(end=pd.Timestamp.today(), periods=days, freq='B')
    base_price = 24500.0 if "NIFTY" in symbol.upper() else 1000.0
    close = [base_price]
    for _ in range(1, days):
        change = random.uniform(-0.015, 0.015)
        close.append(close[-1] * (1 + change))
    
    high = [c * random.uniform(1.0, 1.015) for c in close]
    low = [c * random.uniform(0.985, 1.0) for c in close]
    open_price = [random.uniform(l, h) for l, h in zip(low, high)]
    volume = [random.randint(50000, 5000000) for _ in range(days)]
    
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
    """Fetch real-time live quote with robust fast_info & historical fallback."""
    norm_sym = normalize_symbol(symbol)
    try:
        ticker = yf.Ticker(norm_sym)
        price = 0.0
        prev_close = 0.0
        volume = 0
        
        # 1. Try fast_info (fastest and handles index symbols ^NSEI)
        try:
            fast = ticker.fast_info
            price = float(fast.get("last_price", 0.0) or 0.0)
            prev_close = float(fast.get("previous_close", 0.0) or 0.0)
            volume = int(fast.get("last_volume", 0) or 0)
        except Exception:
            pass

        # 2. Fallback to latest candle history if fast_info is empty
        if price == 0.0:
            hist = ticker.history(period="5d", interval="1m")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                volume = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0
                daily_hist = ticker.history(period="5d", interval="1d")
                if len(daily_hist) >= 2:
                    prev_close = float(daily_hist["Close"].iloc[-2])

        # 3. Fallback to info dict
        if price == 0.0:
            info = ticker.info or {}
            price = float(info.get("currentPrice", info.get("regularMarketPrice", 0.0)))
            prev_close = float(info.get("previousClose", 0.0))

        change = round(price - prev_close, 2) if prev_close else 0.0
        change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close else 0.0

        return {
            "symbol": symbol,
            "normalized_symbol": norm_sym,
            "current_price": round(price, 2),
            "previous_close": round(prev_close, 2),
            "change": change,
            "change_pct": change_pct,
            "volume": volume,
            "timestamp": time.time()
        }
    except Exception as e:
        print(f"Error fetching quote for {symbol} ({norm_sym}): {e}")
        return {"symbol": symbol, "error": str(e), "current_price": 0.0}
