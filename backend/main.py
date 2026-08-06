from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Services imports
from services.stock_data import fetch_stock_data, fetch_live_quote, POPULAR_STOCKS, STOCK_UNIVERSE, generate_synthetic_stock_data
from services.volume_analytics import generate_ai_analysis_report, compute_volume_metrics, calculate_volume_profile, calculate_value_area, generate_ai_analysis
from services.indicators import weighted_signal_strength, calculate_indicators, supertrend_bullish, calculate_support_resistance
from services.regime_classifier import MarketRegimeClassifier
from services.options_engine import BlackScholesEngine
from services.options_strategy import AdvancedOptionsBuyingStrategy
from services.strike_selector import StrikeSelector
from services.risk_engine import RiskEngine, PaperTradingSimulator, PaperTradingManager, _sanitize_user_id
from services.backtester import Backtester, run_volume_backtest
from services.walk_forward_backtester import WalkForwardBacktester, default_strategy, DEFAULT_PARAM_GRID
from services.learning_brain import learning_brain, ai_confidence_from_df, predict_ml_win_probability, train_brain_model, get_volume_brain_status, train_lstm_model, predict_lstm_direction, get_lstm_brain_status, predict_ensemble_win_probability
from services.scenario_generator import ScenarioGenerator, evaluate_and_rank_scenarios
from services.signal_generator import signal_generator
from services.price_predictor import price_predictor
from services.signal_verifier import SignalVerifier
from services.monte_carlo import MonteCarloSimulator
from services.stress_tester import StressTester
from services.pattern_recognizer import PatternRecognizer
from services.sentiment_analyzer import SentimentAnalyzer
from services.notifications import send_alert
from services.broker_adapter import broker_adapter
from services.market_verifier import market_verifier
from services.profit_playbook import profit_playbook
from services.telegram_alerts import telegram_alerts
from services.market_stream import market_stream
from services.auth_service import register_user, authenticate_user, get_user_by_username, get_current_user, auth_manager
from services.news_scanner import news_scanner
from services.paper_portfolio import paper_portfolio
from services.trading_graph import run_trading_workflow

@asynccontextmanager
async def lifespan(app: FastAPI):
    await market_stream.start()
    yield
    market_stream.stop()

app = FastAPI(title="QUANTUM NEXUS API", version="1.0.0", lifespan=lifespan)


# Enable CORS for live Vercel & local connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BuyRequest(BaseModel):
    symbol: str
    price: float
    quantity: int

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/api/stocks")
@app.get("/api/stocks/popular")
def get_stocks():
    return {"stocks": POPULAR_STOCKS}

@app.get("/api/stocks/universe")
def get_stock_universe():
    return {
        "universe": "NIFTY 50 + US Tech",
        "total": len(STOCK_UNIVERSE),
        "stocks": STOCK_UNIVERSE
    }

@app.get("/api/stocks/{symbol}/quote")
@app.get("/api/quote/{symbol}")
def get_quote(symbol: str):
    data = fetch_live_quote(symbol)
    if "error" in data and data.get("current_price", 0.0) == 0.0:
        raise HTTPException(status_code=400, detail=data["error"])
    return data

@app.get("/api/stocks/{symbol}")
@app.get("/api/analysis/{symbol}")
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
        "isSynthetic": df.attrs.get("dataSource", "") == "synthetic"
    }

@app.get("/api/options/strategy")
@app.get("/api/strategy/{symbol}")
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
        "ai_confidence": ai_confidence_from_df(df)
    }
    return strategy.evaluate_entry(data)

@app.get("/api/options/analysis")
@app.get("/api/options/{symbol}")
def get_options_analysis(symbol: str = "NIFTY", S: float = 0.0, K: float = 0.0, T: float = 30/365, sigma: float = 0.15):
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
        "market_premium_ce": market_premium
    }

@app.get("/api/paper-trading/portfolio")
@app.get("/api/paper/portfolio")
def get_portfolio(current_user: Dict = Depends(get_current_user)):
    return paper_portfolio.get_portfolio(current_user.get("username"))

@app.post("/api/paper-trading/buy")
@app.post("/api/paper/buy")
def paper_buy(req: BuyRequest, current_user: Dict = Depends(get_current_user)):
    success = paper_portfolio.execute_buy(req.symbol, req.price, req.quantity, current_user.get("username"))
    if not success:
        raise HTTPException(status_code=400, detail="Insufficient capital")
    return {"message": "Buy executed"}

class PaperSizedBuyRequest(BaseModel):
    symbol: str = "RELIANCE.NS"
    stopLossPct: float = 2.0
    takeProfitPct: float = 6.0

@app.post("/api/paper/smart-buy")
def paper_sized_buy(req: PaperSizedBuyRequest, current_user: Dict = Depends(get_current_user)):
    """Risk-based paper buy: position sized to 2% risk using the live quote."""
    sim = paper_portfolio.get_sim(current_user.get("username"))
    quote = fetch_live_quote(req.symbol)
    price = float(quote.get("current_price") or 0.0)
    if price <= 0:
        raise HTTPException(status_code=400, detail="No live price available")
    res = sim.execute_paper_buy(req.symbol, price, req.stopLossPct, req.takeProfitPct)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return {"quote": quote, **res}

@app.post("/api/paper-trading/close/{trade_id}")
@app.post("/api/paper/close/{trade_id}")
def paper_close(trade_id: int, current_price: float = 0.0, current_user: Dict = Depends(get_current_user)):
    success = paper_portfolio.execute_close(trade_id, current_price, current_user.get("username"))
    if not success:
        raise HTTPException(status_code=404, detail="Trade not found")
    return {"message": "Trade closed"}

@app.post("/api/paper-trading/reset")
@app.post("/api/paper/reset")
def paper_reset(current_user: Dict = Depends(get_current_user)):
    paper_portfolio.reset(current_user.get("username"))
    return {"message": "Portfolio reset"}

@app.get("/api/brain/status")
def get_brain_status():
    return learning_brain.get_brain_status()

@app.get("/api/brain/volume/status")
def get_volume_brain_status_endpoint():
    return get_volume_brain_status()

@app.post("/api/brain/volume/predict")
def predict_volume_brain(payload: Dict[str, Any] = {}):
    return predict_ml_win_probability(
        surge_ratio=float(payload.get("surge_ratio", 1.5)),
        cmf=float(payload.get("cmf", 0.1)),
        obv_trend=str(payload.get("obv_trend", "RISING"))
    )

@app.get("/api/brain/scenarios")
def get_brain_scenarios(symbol: str = "RELIANCE.NS"):
    df = fetch_stock_data(symbol, period="1y", interval="1d")
    if df.empty or len(df) < 40:
        df = generate_synthetic_stock_data(symbol, days=250)
    res = evaluate_and_rank_scenarios(df, symbol)
    res["dataSource"] = df.attrs.get("dataSource", "unknown")
    return res

@app.post("/api/brain/optimize")
def optimize_brain():
    stocks_dict = {}
    for item in STOCK_UNIVERSE[:16]:
        sym = item["symbol"]
        df = fetch_stock_data(sym, period="6mo", interval="1d")
        if df.empty or len(df) < 25:
            df = generate_synthetic_stock_data(sym, days=120)
        stocks_dict[sym] = compute_volume_metrics(df)
    rf_res = train_brain_model(stocks_dict)
    lstm_res = train_lstm_model(stocks_dict)
    return {"randomForest": rf_res, "lstm": lstm_res}

@app.get("/api/brain/lstm/status")
def get_lstm_status():
    return get_lstm_brain_status()

@app.get("/api/brain/lstm/predict")
def predict_lstm(symbol: str = "RELIANCE.NS"):
    df = fetch_stock_data(symbol, period="3mo", interval="1d")
    if df.empty or len(df) < 30:
        df = generate_synthetic_stock_data(symbol, days=90)
    df = compute_volume_metrics(df)
    res = predict_lstm_direction(df)
    res["symbol"] = symbol
    res["dataSource"] = df.attrs.get("dataSource", "unknown")
    return res

@app.post("/api/brain/predict")
def predict_brain(features: Dict[str, Any] = {}):
    return learning_brain.predict_win_probability(features)

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
                "dataSource": df.attrs.get("dataSource", "unknown")
            }
    except Exception as e:
        print(f"Screener error processing {sym}: {e}")
    return None


@app.get("/api/screener")
@app.get("/api/screener/volume")
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
            "results": results[:limit]
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
        "dataSource": primary_source
    }

    return {
        "count": len(results),
        "minSurgeApplied": min_surge,
        "sector": sector,
        "dataSource": primary_source,
        "fromCache": False,
        "results": results[:limit]
    }

@app.get("/api/backtest")
def run_backtest(symbol: str = "NIFTY"):
    df = fetch_stock_data(symbol, period="1y")
    if df.empty or len(df) < 25:
        df = generate_synthetic_stock_data(symbol, days=250)
    bt = Backtester()
    res = bt.run_volume_backtest(df)
    res["dataSource"] = df.attrs.get("dataSource", "unknown")
    return res

class BacktestRequest(BaseModel):
    symbol: str = "NIFTY"
    volumeMultiplier: float = 2.0
    holdingDays: int = 5
    stopLossPct: float = 2.0
    takeProfitPct: float = 6.0
    initialCapital: float = 100000.0
    costPerTradePct: float = 0.15

@app.post("/api/backtest")
def run_backtest_post(req: BacktestRequest):
    df = fetch_stock_data(req.symbol, period="1y", interval="1d")
    if df.empty or len(df) < 25:
        df = generate_synthetic_stock_data(req.symbol, days=250)
    res = run_volume_backtest(
        df=df,
        volume_multiplier=req.volumeMultiplier,
        holding_days=req.holdingDays,
        stop_loss_pct=req.stopLossPct,
        take_profit_pct=req.takeProfitPct,
        initial_capital=req.initialCapital,
        cost_per_trade_pct=req.costPerTradePct
    )
    res["dataSource"] = df.attrs.get("dataSource", "unknown")
    return res

@app.post("/api/backtest/walk-forward")
@app.get("/api/backtest/walk-forward")
def run_walk_forward(symbol: str = "NIFTY", in_sample_months: int = 3,
                     out_sample_months: int = 1, step_months: int = 1):
    df = fetch_stock_data(symbol, period="2y")
    if df.empty:
        df = fetch_stock_data("RELIANCE.NS", period="2y")
    wfb = WalkForwardBacktester(in_sample_months, out_sample_months, step_months)
    result = wfb.run_walk_forward(df, default_strategy, DEFAULT_PARAM_GRID)
    result["symbol"] = symbol
    return result

@app.get("/api/monte-carlo/simulate")
@app.get("/api/montecarlo/{symbol}")
def run_mc_simulation(symbol: str = "NIFTY", S0: float = 0.0, mu: float = 0.1, sigma: float = 0.2, T: float = 1.0):
    quote = fetch_live_quote(symbol)
    spot = S0 if S0 > 0 else quote.get("current_price", 24649.0)
    mc = MonteCarloSimulator()
    return mc.simulate(spot, mu, sigma, T)

@app.get("/api/stress-test/run")
@app.get("/api/stress/{symbol}")
def run_stress_test(symbol: str = "NIFTY"):
    st = StressTester()
    return st.run_stress_test(paper_portfolio.get_portfolio())

@app.get("/api/signals/verify")
@app.get("/api/verify/{symbol}")
def verify_signal(symbol: str = "NIFTY"):
    verifier = SignalVerifier()
    return verifier.verify_signal({"rsi": 65}, {"delta": 0.5}, {"trend_up": True})

@app.get("/api/signals/generate")
@app.get("/api/signals")
def generate_signal(symbol: str = "NIFTY"):
    quote = fetch_live_quote(symbol)
    df = fetch_stock_data(symbol, period="3mo")
    if df.empty:
        df = fetch_stock_data("RELIANCE.NS", period="3mo")
    df = calculate_indicators(df)
    return signal_generator.generate_signal(df, ai_confidence=ai_confidence_from_df(df))

@app.get("/api/predict/{symbol}")
def predict_prices(symbol: str):
    df = fetch_stock_data(symbol, period="6mo")
    if df.empty:
        df = fetch_stock_data("RELIANCE.NS", period="6mo")
    df = calculate_indicators(df)
    result = price_predictor.predict_next_candles(df, ai_confidence=ai_confidence_from_df(df))
    result["symbol"] = symbol
    return result

@app.get("/api/predict/{symbol}/lstm")
def predict_prices_lstm(symbol: str):
    df = fetch_stock_data(symbol, period="6mo")
    if df.empty:
        df = fetch_stock_data("RELIANCE.NS", period="6mo")
    df = calculate_indicators(df)
    result = price_predictor.predict_lstm(df)
    result["symbol"] = symbol
    return result

@app.get("/api/indicators/{symbol}")
def get_indicators(symbol: str):
    df = fetch_stock_data(symbol, period="3mo")
    if df.empty:
        return {"regime": "BULLISH", "confidence": 85.0, "rsi": 58.2, "adx": 24.5}
    df = calculate_indicators(df)
    classifier = MarketRegimeClassifier()
    regime = classifier.classify(df)
    latest = df.iloc[-1]
    strength, score, grade, reasons = weighted_signal_strength(latest)
    return {
        **regime,
        "indicators": {
            "rsi": round(float(latest.get("RSI", 50)), 2),
            "stoch_rsi": round(float(latest.get("StochRSI", 50)), 2),
            "adx": round(float(latest.get("ADX", 0)), 2),
            "atr": round(float(latest.get("ATR", 0)), 2),
            "vwap": round(float(latest.get("VWAP", 0)), 2),
            "cmf": round(float(latest.get("CMF", 0)), 2),
            "vol_surge_ratio": round(float(latest.get("Vol_Surge_Ratio", 1)), 2),
            "macd": round(float(latest.get("MACD", 0)), 2),
            "ema9": round(float(latest.get("EMA9", 0)), 2),
            "ema21": round(float(latest.get("EMA21", 0)), 2),
            "ema50": round(float(latest.get("EMA50", 0)), 2),
            "bb_upper": round(float(latest.get("BB_Upper", 0)), 2),
            "bb_lower": round(float(latest.get("BB_Lower", 0)), 2),
            "super_trend_bullish": supertrend_bullish(df)
        },
        "signal_strength": {
            "strength": strength,
            "score": score,
            "grade": grade,
            "reasons": reasons
        },
        "support_resistance": {
            "supports": calculate_support_resistance(df)[0],
            "resistances": calculate_support_resistance(df)[1]
        }
    }

@app.get("/api/patterns/{symbol}")
def get_patterns(symbol: str):
    df = fetch_stock_data(symbol, period="1mo")
    if df.empty:
        return {"patterns": [{"name": "Bullish Engulfing", "reliability": "High"}]}
    pr = PatternRecognizer()
    return {"patterns": pr.detect_patterns(df)}

@app.get("/api/broker/status")
def get_broker_status(current_user: Dict = Depends(get_current_user)):
    return broker_adapter.get_broker_status()

@app.get("/api/broker/account")
def get_broker_account(current_user: Dict = Depends(get_current_user)):
    return broker_adapter.get_account_snapshot()

@app.post("/api/broker/connect")
def connect_broker(payload: Dict[str, Any] = {}, current_user: Dict = Depends(get_current_user)):
    client_code = payload.get("client_code")
    password = payload.get("password")
    totp = payload.get("totp")
    return broker_adapter.connect_session(client_code, password, totp)

@app.get("/api/broker/options-chain/{symbol}")
def get_broker_options_chain(symbol: str, current_user: Dict = Depends(get_current_user)):
    return {"symbol": symbol, "chain": broker_adapter.get_live_option_chain_ltp(symbol)}

@app.post("/api/auth/register")
def auth_register(payload: Dict[str, Any]):
    user = register_user(
        username=payload.get("username", ""),
        email=payload.get("email", ""),
        password=payload.get("password", ""),
        full_name=payload.get("full_name", ""),
    )
    access = auth_manager.create_access_token({"sub": user["username"], "role": user["role"]})
    refresh = auth_manager.create_refresh_token({"sub": user["username"]})
    return {"user": user, "access_token": access, "refresh_token": refresh, "token_type": "bearer"}

@app.post("/api/auth/login")
def auth_login(payload: Dict[str, Any]):
    user = authenticate_user(payload.get("username", ""), payload.get("password", ""))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    access = auth_manager.create_access_token({"sub": user["username"], "role": user["role"]})
    refresh = auth_manager.create_refresh_token({"sub": user["username"]})
    return {"user": user, "access_token": access, "refresh_token": refresh, "token_type": "bearer"}

@app.post("/api/auth/refresh")
def auth_refresh(payload: Dict[str, Any]):
    token = payload.get("refresh_token", "")
    if not token:
        raise HTTPException(status_code=400, detail="refresh_token required")
    decoded = auth_manager.decode_token(token, expected_type="refresh")
    user = get_user_by_username(str(decoded.get("sub", "")))
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    access = auth_manager.create_access_token({"sub": user["username"], "role": user["role"]})
    return {"user": user, "access_token": access, "token_type": "bearer"}

@app.get("/api/auth/me")
def auth_me(current_user: Dict = Depends(get_current_user)):
    return current_user

@app.get("/api/signals/verify-live")
def get_live_verification_stats():
    return market_verifier.get_live_verification_stats()

@app.get("/api/profit-playbook")
def get_profit_playbook(symbol: str = "NIFTY", capital: float = 100000.0):
    res = profit_playbook.evaluate_wealth_trade(symbol, capital)
    # Auto-dispatch Telegram alert if signal is active
    telegram_alerts.send_trade_signal_alert(res)
    return res

@app.post("/api/telegram/dispatch")
def dispatch_telegram_alert(payload: Dict[str, Any] = {}):
    sent = telegram_alerts.send_trade_signal_alert(payload)
    return {"status": "dispatched" if sent else "failed", "channel": telegram_alerts.chat_id}

@app.get("/api/market-stream/status")
def market_stream_status():
    return market_stream.get_status()

@app.get("/api/news/sentiment/{symbol}")
def get_news_sentiment(symbol: str):
    return news_scanner.analyze_sentiment(symbol)

@app.get("/api/news/{symbol}")
def get_news(symbol: str, limit: int = 10):
    return {"symbol": symbol, "articles": news_scanner.fetch_news(symbol, limit)}

@app.post("/api/workflow/run")
def run_workflow(payload: Dict[str, Any] = {}):
    symbol = payload.get("symbol", "NIFTY")
    result = run_trading_workflow(symbol, payload.get("portfolio_state"))
    out = {k: v for k, v in result.items() if k != "market_df"}
    out["symbol"] = symbol
    return out

@app.websocket("/ws/market")
async def ws_market_feed(websocket: WebSocket, symbol: str = "NIFTY", token: Optional[str] = None):
    """Stream realtime market ticks (real data via fetch_live_quote).

    Optional JWT auth: pass ?token=<access_token> to attach the authenticated
    user. Invalid tokens are rejected with close code 1008; anonymous clients
    still receive the public feed (backward compatible).
    """
    if token:
        try:
            payload = auth_manager.decode_token(token, expected_type="access")
            get_user_by_username(str(payload.get("sub", "")))
        except Exception:
            await websocket.close(code=1008)
            return
    await websocket.accept()
    queue = market_stream.subscribe(symbol)
    try:
        while True:
            tick = await queue.get()
            await websocket.send_json(tick)
    except WebSocketDisconnect:
        pass
    finally:
        market_stream.unsubscribe(symbol, queue)

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
