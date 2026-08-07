"""Market data & screener routes."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from services.stock_data import (
    fetch_stock_data,
    fetch_live_quote,
    POPULAR_STOCKS,
    STOCK_UNIVERSE,
    generate_synthetic_stock_data,
)
from services.volume_analytics import (
    compute_volume_metrics,
    calculate_volume_profile,
    calculate_value_area,
    generate_ai_analysis,
    generate_ai_analysis_report,
)
from services.learning_brain import predict_ensemble_win_probability, predict_ml_win_probability
from services.market_stream import market_stream

router = APIRouter()


@router.get("/api/stocks")
@router.get("/api/stocks/popular")
def get_stocks():
    return {"stocks": POPULAR_STOCKS}


@router.get("/api/stocks/universe")
def get_stock_universe():
    return {
        "universe": "NIFTY 50 + US Tech",
        "total": len(STOCK_UNIVERSE),
        "stocks": STOCK_UNIVERSE,
    }


@router.get("/api/stocks/{symbol}/quote")
@router.get("/api/quote/{symbol}")
def get_quote(symbol: str):
    data = fetch_live_quote(symbol)
    if "error" in data and data.get("current_price", 0.0) == 0.0:
        raise HTTPException(status_code=400, detail=data["error"])
    return data


@router.get("/api/stocks/{symbol}")
@router.get("/api/analysis/{symbol}")
def get_stock_details(symbol: str):
    df = fetch_stock_data(symbol, period="6mo")
    if df.empty or len(df) < 5:
        df = generate_synthetic_stock_data(symbol, days=120)
    df = compute_volume_metrics(df)
    volume_profile = calculate_volume_profile(df, bins_count=12)
    value_area = calculate_value_area(volume_profile)
    ai_report = generate_ai_analysis(symbol, df)
    candles = df.to_dict(orient="records")
    latest = candles[-1] if candles else {}
    surge_val = float(latest.get("Vol_Surge_Ratio", 1.0))
    cmf_val = float(latest.get("CMF", 0.0))
    obv_trend = "RISING" if float(latest.get("OBV", 0)) > float(latest.get("OBV_EMA20", 0)) else "FALLING"
    ml_prediction = predict_ensemble_win_probability(df, surge_val, cmf_val, obv_trend)
    return {
        "symbol": symbol.upper(),
        "latest": latest,
        "candles": candles,
        "volumeProfile": volume_profile,
        "valueArea": value_area,
        "aiReport": ai_report,
        "mlPrediction": ml_prediction,
        "analysis": generate_ai_analysis_report(df),
        "dataSource": df.attrs.get("dataSource", "unknown"),
        "isSynthetic": df.attrs.get("dataSource", "") == "synthetic",
    }


@router.get("/api/market-stream/status")
def market_stream_status():
    return market_stream.get_status()


@router.get("/api/market/ticks")
def market_ticks(symbol: str = "NIFTY"):
    """Serve the freshest cached tick for a symbol straight from the WS stream state.

    Returns 404 only when no tick has ever been captured (client can fall back to the REST quote).
    """
    tick = market_stream.get_tick(symbol)
    if tick is None:
        raise HTTPException(status_code=404, detail="No tick cached for symbol")
    return tick


_SCREENER_CACHE: Dict[str, Dict[str, Any]] = {}
_SCREENER_CACHE_TTL = 120


def _screen_single_stock(item: Dict[str, str], min_surge: float) -> Optional[Dict[str, Any]]:
    sym = item["symbol"]
    try:
        df_raw = fetch_stock_data(sym, period="3mo", interval="1d")
        if df_raw.empty or len(df_raw) < 5:
            df_raw = generate_synthetic_stock_data(sym, days=60)

        df = compute_volume_metrics(df_raw)
        latest = df.iloc[-1]

        surge = float(latest["Vol_Surge_Ratio"])
        price_chg = float(latest["Price_Change_Pct"])
        cmf_val = float(latest["CMF"])
        mfi_val = float(latest.get("MFI", 50.0))
        vol_z = float(latest.get("Volume_ZScore", 0.0))
        pocket_pivot = bool(latest.get("Pocket_Pivot", False))
        close_p = float(latest["Close"])
        vol_val = int(latest["Volume"])
        signal_text = str(latest["Volume_Signal"])
        obv_trend = "RISING" if float(latest["OBV"]) > float(latest["OBV_EMA20"]) else "FALLING"
        adl_trend = "RISING" if float(latest.get("ADL", 0.0)) > float(latest.get("ADL_EMA20", 0.0)) else "FALLING"

        value_area = calculate_value_area(calculate_volume_profile(df_raw))

        ml_pred = predict_ml_win_probability(surge, cmf_val, obv_trend)

        if surge >= min_surge:
            score = round(min(100.0, surge * 20 + max(0.0, cmf_val) * 15 + (vol_z + 2) * 10 + (5 if pocket_pivot else 0)), 1)
            return {
                "symbol": sym,
                "name": item["name"],
                "sector": item["sector"],
                "exchange": item["exchange"],
                "closePrice": close_p,
                "priceChangePct": price_chg,
                "volume": vol_val,
                "volumeSurgeRatio": surge,
                "volumeZScore": vol_z,
                "cmf": cmf_val,
                "mfi": mfi_val,
                "pocketPivot": pocket_pivot,
                "adlTrend": adl_trend,
                "signal": signal_text,
                "valueArea": value_area,
                "mlWinProbability": ml_pred["mlWinProbabilityPct"],
                "score": score,
                "dataSource": df.attrs.get("dataSource", "unknown"),
            }
    except Exception as e:
        print(f"Screener error processing {sym}: {e}")
    return None


@router.get("/api/screener")
@router.get("/api/screener/volume")
def run_screener(min_surge: float = 1.5, sector: Optional[str] = None,
                 limit: int = 50, force_refresh: bool = False):
    cache_key = f"{min_surge}|{sector}"
    cached = _SCREENER_CACHE.get(cache_key)
    if cached and not force_refresh and (time.time() - cached["ts"]) < _SCREENER_CACHE_TTL:
        results = [r for r in cached["results"] if sector is None or sector.lower() in r["sector"].lower()]
        return {
            "count": len(results),
            "minSurgeApplied": min_surge,
            "sector": sector,
            "dataSource": cached.get("dataSource"),
            "fromCache": True,
            "results": results[:limit],
        }

    results = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(_screen_single_stock, item, min_surge) for item in STOCK_UNIVERSE]
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)

    results.sort(key=lambda x: x["volumeSurgeRatio"], reverse=True)
    if sector:
        results = [r for r in results if sector.lower() in r["sector"].lower()]

    sources = {r["dataSource"] for r in results}
    primary_source = "live" if sources and sources <= {"yfinance", "nse-direct"} else ("synthetic" if not sources else "mixed")

    _SCREENER_CACHE[cache_key] = {
        "ts": time.time(),
        "results": results,
        "dataSource": primary_source,
    }

    return {
        "count": len(results),
        "minSurgeApplied": min_surge,
        "sector": sector,
        "dataSource": primary_source,
        "fromCache": False,
        "results": results[:limit],
    }
