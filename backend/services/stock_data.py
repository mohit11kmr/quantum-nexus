import yfinance as yf
import pandas as pd
import numpy as np
import time
import requests
from datetime import datetime
from typing import Dict, Any, List

YFINANCE_AVAILABLE = True

# Full NIFTY 50 universe (name / sector / exchange metadata) + a few US tech names.
NIFTY50_STOCKS = [
    {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "sector": "Energy / Conglomerate", "exchange": "NSE"},
    {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "sector": "Information Technology", "exchange": "NSE"},
    {"symbol": "HDFCBANK.NS", "name": "HDFC Bank", "sector": "Banking & Finance", "exchange": "NSE"},
    {"symbol": "ICICIBANK.NS", "name": "ICICI Bank", "sector": "Banking & Finance", "exchange": "NSE"},
    {"symbol": "INFY.NS", "name": "Infosys Ltd", "sector": "Information Technology", "exchange": "NSE"},
    {"symbol": "BHARTIARTL.NS", "name": "Bharti Airtel", "sector": "Telecom", "exchange": "NSE"},
    {"symbol": "SBIN.NS", "name": "State Bank of India", "sector": "Banking & Finance", "exchange": "NSE"},
    {"symbol": "ITC.NS", "name": "ITC Limited", "sector": "FMCG", "exchange": "NSE"},
    {"symbol": "LT.NS", "name": "Larsen & Toubro", "sector": "Infrastructure", "exchange": "NSE"},
    {"symbol": "AXISBANK.NS", "name": "Axis Bank", "sector": "Banking & Finance", "exchange": "NSE"},
    {"symbol": "ADANIENT.NS", "name": "Adani Enterprises", "sector": "Conglomerate", "exchange": "NSE"},
    {"symbol": "ADANIPORTS.NS", "name": "Adani Ports & SEZ", "sector": "Infrastructure", "exchange": "NSE"},
    {"symbol": "APOLLOHOSP.NS", "name": "Apollo Hospitals", "sector": "Healthcare", "exchange": "NSE"},
    {"symbol": "ASIANPAINT.NS", "name": "Asian Paints", "sector": "Consumer Goods", "exchange": "NSE"},
    {"symbol": "BAJAJ-AUTO.NS", "name": "Bajaj Auto", "sector": "Automobile", "exchange": "NSE"},
    {"symbol": "BAJFINANCE.NS", "name": "Bajaj Finance", "sector": "Banking & Finance", "exchange": "NSE"},
    {"symbol": "BAJAJFINSV.NS", "name": "Bajaj Finserv", "sector": "Banking & Finance", "exchange": "NSE"},
    {"symbol": "BPCL.NS", "name": "Bharat Petroleum", "sector": "Energy", "exchange": "NSE"},
    {"symbol": "BRITANNIA.NS", "name": "Britannia Industries", "sector": "FMCG", "exchange": "NSE"},
    {"symbol": "CIPLA.NS", "name": "Cipla", "sector": "Pharmaceuticals", "exchange": "NSE"},
    {"symbol": "COALINDIA.NS", "name": "Coal India", "sector": "Energy / Mining", "exchange": "NSE"},
    {"symbol": "DIVISLAB.NS", "name": "Divi's Laboratories", "sector": "Pharmaceuticals", "exchange": "NSE"},
    {"symbol": "DRREDDY.NS", "name": "Dr. Reddy's Labs", "sector": "Pharmaceuticals", "exchange": "NSE"},
    {"symbol": "EICHERMOT.NS", "name": "Eicher Motors", "sector": "Automobile", "exchange": "NSE"},
    {"symbol": "GRASIM.NS", "name": "Grasim Industries", "sector": "Cement / Textiles", "exchange": "NSE"},
    {"symbol": "HCLTECH.NS", "name": "HCL Technologies", "sector": "Information Technology", "exchange": "NSE"},
    {"symbol": "HDFCLIFE.NS", "name": "HDFC Life Insurance", "sector": "Insurance", "exchange": "NSE"},
    {"symbol": "HEROMOTOCO.NS", "name": "Hero MotoCorp", "sector": "Automobile", "exchange": "NSE"},
    {"symbol": "HINDALCO.NS", "name": "Hindalco Industries", "sector": "Metals & Mining", "exchange": "NSE"},
    {"symbol": "HINDUNILVR.NS", "name": "Hindustan Unilever", "sector": "FMCG", "exchange": "NSE"},
    {"symbol": "JSWSTEEL.NS", "name": "JSW Steel", "sector": "Metals & Mining", "exchange": "NSE"},
    {"symbol": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank", "sector": "Banking & Finance", "exchange": "NSE"},
    {"symbol": "M&M.NS", "name": "Mahindra & Mahindra", "sector": "Automobile", "exchange": "NSE"},
    {"symbol": "MARUTI.NS", "name": "Maruti Suzuki", "sector": "Automobile", "exchange": "NSE"},
    {"symbol": "NESTLEIND.NS", "name": "Nestle India", "sector": "FMCG", "exchange": "NSE"},
    {"symbol": "NTPC.NS", "name": "NTPC Limited", "sector": "Energy / Power", "exchange": "NSE"},
    {"symbol": "ONGC.NS", "name": "Oil & Natural Gas Corp", "sector": "Energy", "exchange": "NSE"},
    {"symbol": "POWERGRID.NS", "name": "Power Grid Corp", "sector": "Energy / Power", "exchange": "NSE"},
    {"symbol": "SBILIFE.NS", "name": "SBI Life Insurance", "sector": "Insurance", "exchange": "NSE"},
    {"symbol": "SHRIRAMFIN.NS", "name": "Shriram Finance", "sector": "Banking & Finance", "exchange": "NSE"},
    {"symbol": "SUNPHARMA.NS", "name": "Sun Pharmaceuticals", "sector": "Pharmaceuticals", "exchange": "NSE"},
    {"symbol": "TATACONSUM.NS", "name": "Tata Consumer Products", "sector": "FMCG", "exchange": "NSE"},
    {"symbol": "TATAMOTORS.NS", "name": "Tata Motors", "sector": "Automobile", "exchange": "NSE"},
    {"symbol": "TATASTEEL.NS", "name": "Tata Steel", "sector": "Metals & Mining", "exchange": "NSE"},
    {"symbol": "TECHM.NS", "name": "Tech Mahindra", "sector": "Information Technology", "exchange": "NSE"},
    {"symbol": "TITAN.NS", "name": "Titan Company", "sector": "Consumer Goods", "exchange": "NSE"},
    {"symbol": "TRENT.NS", "name": "Trent Limited", "sector": "Retail", "exchange": "NSE"},
    {"symbol": "ULTRACEMCO.NS", "name": "Ultratech Cement", "sector": "Cement", "exchange": "NSE"},
    {"symbol": "WIPRO.NS", "name": "Wipro", "sector": "Information Technology", "exchange": "NSE"},
    {"symbol": "ZOMATO.NS", "name": "Zomato Limited", "sector": "Internet / F&B", "exchange": "NSE"},
]

US_STOCKS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "US Tech", "exchange": "NASDAQ"},
    {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "US Tech & AI", "exchange": "NASDAQ"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "US Auto & Tech", "exchange": "NASDAQ"},
    {"symbol": "MSFT", "name": "Microsoft Corp", "sector": "US Tech", "exchange": "NASDAQ"},
]

STOCK_UNIVERSE: List[Dict[str, str]] = NIFTY50_STOCKS + US_STOCKS

# US tickers must NOT get a .NS suffix during normalization.
US_TICKERS = {s["symbol"] for s in US_STOCKS}

# Backwards-compatible flat list of symbols (used by legacy endpoints).
POPULAR_STOCKS: List[str] = [
    "NIFTY", "BANKNIFTY", "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS",
    "ICICIBANK.NS", "HUL.NS", "SBI.NS", "BAJFINANCE.NS", "BHARTIARTL.NS", "ITC.NS"
]

def normalize_symbol(symbol: str) -> str:
    """Normalize trading symbols for Yahoo Finance API."""
    sym = symbol.strip().upper()
    if sym in ["NIFTY", "NIFTY50", "NIFTY 50", "^NSEI"]:
        return "^NSEI"
    if sym in ["BANKNIFTY", "NIFTYBANK", "NIFTY BANK", "^NSEBANK"]:
        return "^NSEBANK"
    if sym in ["FINNIFTY", "^CNXFIN"]:
        return "^CNXFIN"
    if sym in US_TICKERS:
        return sym
    if not sym.startswith("^") and not sym.endswith(".NS") and not sym.endswith(".BO"):
        return f"{sym}.NS"
    return sym

def _stable_seed(symbol: str) -> int:
    """Deterministic per-symbol seed (stable across processes, unlike builtin hash)."""
    return int.from_bytes(symbol.encode("utf-8")[:8].ljust(8, b"\0"), "big") % 10000

def generate_synthetic_stock_data(symbol: str, days: int = 100, interval: str = "1d") -> pd.DataFrame:
    """Deterministic synthetic OHLCV fallback generator (stable per symbol)."""
    if interval in ["1m", "5m", "15m"]:
        candles_count = 75 if interval == "5m" else 150
        end = datetime.now()
        dates = [end - pd.Timedelta(minutes=i * 5) for i in range(candles_count)]
        dates.reverse()
        seed_val = _stable_seed(symbol)
        base_price = 100.0 + float(seed_val % 2500)
        vol_base = 50000 + (seed_val % 200000)
        rng = np.random.default_rng(seed_val)
        returns = rng.normal(0.0002, 0.004, len(dates))
        spike_idx = rng.choice(len(dates), size=max(1, int(len(dates) * 0.1)), replace=False)
        for idx in spike_idx:
            returns[idx] += float(rng.choice([0.015, -0.012]))
        prices = base_price * np.exp(np.cumsum(returns))
        df_list = []
        for i in range(len(dates)):
            close_p = float(prices[i])
            high_p = close_p * (1.0 + abs(float(rng.normal(0, 0.005))))
            low_p = close_p * (1.0 - abs(float(rng.normal(0, 0.005))))
            open_p = low_p + float(rng.uniform(0, max(0.01, high_p - low_p)))
            vol = int(vol_base * rng.uniform(2.5, 4.2)) if i in spike_idx else int(vol_base * rng.uniform(0.6, 1.4))
            df_list.append({
                "Date": dates[i].strftime("%H:%M"),
                "Open": round(open_p, 2),
                "High": round(high_p, 2),
                "Low": round(low_p, 2),
                "Close": round(close_p, 2),
                "Volume": vol
            })
        df = pd.DataFrame(df_list)
        df.attrs["dataSource"] = "synthetic"
        return df

    dates = pd.date_range(end=pd.Timestamp.today(), periods=days, freq='B')
    seed_val = _stable_seed(symbol)
    rng = np.random.default_rng(seed_val)
    base_price = 24500.0 if "NIFTY" in symbol.upper() else (1000.0 + float(seed_val % 1500))
    returns = rng.normal(0.0002, 0.015, days)
    spike_idx = rng.choice(days, size=max(1, int(days * 0.08)), replace=False)
    for idx in spike_idx:
        returns[idx] += float(rng.choice([0.025, -0.02]))

    close = list(base_price * np.exp(np.cumsum(returns)))
    high = [c * float(rng.uniform(1.0, 1.015)) for c in close]
    low = [c * float(rng.uniform(0.985, 1.0)) for c in close]
    open_price = [float(rng.uniform(l, h)) for l, h in zip(low, high)]
    volume = [int(rng.uniform(50000, 5000000)) for _ in range(days)]
    for idx in spike_idx:
        volume[idx] = int(volume[idx] * float(rng.uniform(2.0, 3.5)))

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_price,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume
    })
    df.attrs["dataSource"] = "synthetic"
    return df

def fetch_stock_data(symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
    """Fetch historical stock data with symbol normalization and dataSource tagging."""
    norm_sym = normalize_symbol(symbol)
    try:
        ticker = yf.Ticker(norm_sym)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return pd.DataFrame()
        df.reset_index(inplace=True)
        date_col = None
        for col in df.columns:
            if "date" in str(col).lower() or "time" in str(col).lower():
                date_col = col
                break
        if date_col and "Date" not in df.columns:
            df.rename(columns={date_col: "Date"}, inplace=True)
        for req_col in ["Open", "High", "Low", "Close", "Volume"]:
            if req_col not in df.columns:
                df[req_col] = 0.0
            df[req_col] = pd.to_numeric(df[req_col], errors="coerce").fillna(0.0)
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]].copy() if "Date" in df.columns else df
        df = df.fillna(0.0)
        df.attrs["dataSource"] = "yfinance"
        return df
    except Exception as e:
        print(f"Error fetching data for {symbol} ({norm_sym}): {e}")
        return pd.DataFrame()

def _is_market_open(now: datetime) -> bool:
    """Indian market hours: Mon-Fri 9:15 to 15:30 IST."""
    is_weekday = now.weekday() < 5
    return is_weekday and ((now.hour == 9 and now.minute >= 15) or (9 < now.hour < 15) or (now.hour == 15 and now.minute <= 30))

_nse_last_attempt = 0.0


def _fetch_nse_direct_quote(symbol: str) -> Dict[str, Any]:
    """Fetch a real-time quote from NSE India's public API (for NSE equity symbols).

    Returns None when NSE is unreachable or the symbol is not an NSE equity.
    A cooldown guards NSE's public API from aggressive polling.
    """
    global _nse_last_attempt
    if not symbol.endswith(".NS"):
        return None
    now_ts = time.time()
    if now_ts - _nse_last_attempt < 5.0:
        return None
    _nse_last_attempt = now_ts
    base_symbol = symbol.replace(".NS", "")
    try:
        session = requests.Session()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/",
        }
        session.get("https://www.nseindia.com", headers=headers, timeout=6)
        r = session.get(
            f"https://www.nseindia.com/api/quote-equity?symbol={base_symbol}",
            headers=headers,
            timeout=8
        )
        r.raise_for_status()
        data = r.json()
        price_info = data.get("priceInfo", {})
        last_price = price_info.get("lastPrice")
        if not last_price:
            return None
        now = datetime.now()
        change = float(price_info.get("change", 0.0) or 0.0)
        return {
            "symbol": symbol.upper(),
            "normalized_symbol": symbol.upper(),
            "current_price": round(float(last_price), 2),
            "previous_close": round(float(last_price) - change, 2),
            "change": round(change, 2),
            "change_pct": round(float(price_info.get("pChange", 0.0) or 0.0), 2),
            "volume": int(float(price_info.get("totalTradedVolume", 0) or 0)),
            "day_high": round(float(price_info.get("intraDayHighLow", {}).get("max", 0.0) or 0.0), 2),
            "day_low": round(float(price_info.get("intraDayHighLow", {}).get("min", 0.0) or 0.0), 2),
            "market_status": "LIVE OPEN" if _is_market_open(now) else "CLOSED / AFTER HOURS",
            "last_updated": now.strftime("%H:%M:%S IST"),
            "timestamp": time.time(),
            "status": "LIVE_REALTIME",
            "data_source": "nse-direct"
        }
    except Exception:
        return None

def fetch_live_quote(symbol: str) -> Dict[str, Any]:
    """Fetch live quote. Source priority: NSE Direct API -> Yahoo Chart REST -> fast_info -> history -> synthetic."""
    clean_symbol = symbol.strip().upper()

    # 1. NSE India public API (real-time, best for .NS symbols)
    nse_quote = _fetch_nse_direct_quote(clean_symbol)
    if nse_quote is not None:
        return nse_quote

    norm_sym = normalize_symbol(clean_symbol)
    price = 0.0
    prev_close = 0.0
    volume = 0

    # 2. Primary Engine: Direct Yahoo Chart REST API (Fastest, zero cloud rate limits)
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{norm_sym}?interval=1m&range=1d"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(url, headers=headers, timeout=4)
        if res.status_code == 200:
            chart_data = res.json().get("chart", {}).get("result", [])[0]
            meta = chart_data.get("meta", {})
            price = float(meta.get("regularMarketPrice", 0.0) or 0.0)
            prev_close = float(meta.get("chartPreviousClose", meta.get("previousClose", price)) or price)
            volume = int(meta.get("regularMarketVolume", 0) or 0)
    except Exception as e:
        print(f"Direct Chart API warning for {symbol}: {e}")

    # 3. Secondary Engine: yfinance fast_info
    if price == 0.0:
        try:
            ticker = yf.Ticker(norm_sym)
            fast = ticker.fast_info
            price = float(fast.get("last_price", 0.0) or 0.0)
            prev_close = float(fast.get("previous_close", 0.0) or 0.0)
            volume = int(fast.get("last_volume", 0) or 0)
        except Exception:
            pass

    # 4. Tertiary Fallback: latest candle history
    if price == 0.0:
        try:
            ticker = yf.Ticker(norm_sym)
            hist = ticker.history(period="5d", interval="1m")
            if not hist.empty:
                price = float(hist["Close"].iloc[-1])
                volume = int(hist["Volume"].iloc[-1]) if "Volume" in hist.columns else 0
                daily_hist = ticker.history(period="5d", interval="1d")
                if len(daily_hist) >= 2:
                    prev_close = float(daily_hist["Close"].iloc[-2])
        except Exception:
            pass

    change = round(price - prev_close, 2) if prev_close else 0.0
    change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close else 0.0

    return {
        "symbol": clean_symbol,
        "normalized_symbol": norm_sym,
        "current_price": round(price, 2),
        "previous_close": round(prev_close, 2),
        "change": change,
        "change_pct": change_pct,
        "volume": volume,
        "day_high": round(price * 1.01, 2) if price else 0.0,
        "day_low": round(price * 0.99, 2) if price else 0.0,
        "market_status": "LIVE OPEN" if _is_market_open(datetime.now()) else "CLOSED / AFTER HOURS",
        "last_updated": datetime.now().strftime("%H:%M:%S IST"),
        "timestamp": time.time(),
        "status": "LIVE_REALTIME" if price > 0 else "OFFLINE",
        "data_source": "yahoo"
    }
