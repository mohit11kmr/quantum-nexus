"""Options valuation & strategy routes."""
from typing import Dict, Any

from fastapi import APIRouter

from services.stock_data import fetch_live_quote, fetch_stock_data
from services.indicators import calculate_indicators, supertrend_bullish
from services.options_engine import BlackScholesEngine
from services.options_strategy import AdvancedOptionsBuyingStrategy
from services.learning_brain import ai_confidence_from_df
from services.broker_adapter import broker_adapter
from services.options_intel import compute_options_intel

router = APIRouter()


@router.get("/api/options/intel")
@router.get("/api/options/flow")
def get_options_intel(symbol: str = "NIFTY"):
    """NSE-style option-chain intelligence: PCR, max pain, OI walls, IV rank & direction score."""
    return compute_options_intel(symbol)


@router.get("/api/options/strategy")
@router.get("/api/strategy/{symbol}")
def get_options_strategy(symbol: str = "NIFTY"):
    quote = fetch_live_quote(symbol)
    spot = quote.get("current_price") or 24649.0
    strategy = AdvancedOptionsBuyingStrategy()
    df = fetch_stock_data(symbol, period="3mo")
    if df.empty:
        df = fetch_stock_data("RELIANCE.NS", period="3mo")
    df = calculate_indicators(df)
    latest = df.iloc[-1]
    data = {
        "supertrend_bullish": supertrend_bullish(df),
        "close": spot,
        "vwap": float(latest.get("VWAP", spot)),
        "rsi": float(latest.get("RSI", 55.0)),
        "ema_bullish": float(latest.get("EMA9", 0.0)) > float(latest.get("EMA21", 0.0)),
        "volume_spike_ratio": float(latest.get("Vol_Surge_Ratio", 1.0)),
        "adx": float(latest.get("ADX", 20.0)),
        "ai_confidence": ai_confidence_from_df(df),
    }
    return strategy.evaluate_entry(data)


@router.get("/api/options/analysis")
@router.get("/api/options/{symbol}")
def get_options_analysis(symbol: str = "NIFTY", S: float = 0.0, K: float = 0.0, T: float = 30 / 365, sigma: float = 0.15):
    quote = fetch_live_quote(symbol)
    spot = S if S > 0 else (quote.get("current_price") or 24649.0)
    strike = K if K > 0 else round(spot / 50.0) * 50 if "NIFTY" in symbol.upper() else round(spot)
    if spot <= 0 or strike <= 0:
        spot = 24649.0
        strike = round(spot / 50.0) * 50
    engine = BlackScholesEngine()
    greeks = engine.calculate_greeks(spot, strike, T, sigma)
    market_premium = None
    try:
        chain = broker_adapter.get_live_option_chain_ltp(symbol)
        for row in chain:
            if abs(row["strike_price"] - strike) <= 1 and row["option_type"] == "CE" and row["ltp"] > 0:
                market_premium = row["ltp"]
                break
    except Exception:
        pass
    valuation = "MARKET_PREMIUM_UNAVAILABLE"
    if market_premium:
        valuation = engine.analyze_option_strike_valuation(market_premium, greeks['fair_value'])
    return {
        "symbol": symbol,
        "spot_price": spot,
        "strike_price": strike,
        "quote": quote,
        "greeks": greeks,
        "valuation": valuation,
        "market_premium_ce": market_premium,
    }
