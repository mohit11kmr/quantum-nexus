from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from typing import Dict, Any, List

# Services imports
from services.stock_data import fetch_stock_data, fetch_live_quote, POPULAR_STOCKS
from services.volume_analytics import generate_ai_analysis_report
from services.indicators import weighted_signal_strength
from services.regime_classifier import MarketRegimeClassifier
from services.options_engine import BlackScholesEngine
from services.options_strategy import OptionsBuyingStrategy
from services.strike_selector import StrikeSelector
from services.risk_engine import RiskEngine, PaperTradingSimulator
from services.backtester import Backtester
from services.learning_brain import LearningBrain
from services.scenario_generator import ScenarioGenerator
from services.signal_generator import SignalGenerator
from services.signal_verifier import SignalVerifier
from services.monte_carlo import MonteCarloSimulator
from services.stress_tester import StressTester
from services.pattern_recognizer import PatternRecognizer
from services.sentiment_analyzer import SentimentAnalyzer
from services.notifications import send_alert
from services.broker_adapter import broker_adapter
from services.market_verifier import market_verifier

app = FastAPI(title="QUANTUM NEXUS API", version="1.0.0")

paper_sim = PaperTradingSimulator()
brain = LearningBrain()

class BuyRequest(BaseModel):
    symbol: str
    price: float
    quantity: int

@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/api/stocks")
def get_stocks():
    return {"stocks": POPULAR_STOCKS}

@app.get("/api/stocks/{symbol}/quote")
def get_quote(symbol: str):
    data = fetch_live_quote(symbol)
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])
    return data

@app.get("/api/stocks/{symbol}")
def get_stock_details(symbol: str):
    df = fetch_stock_data(symbol, period="1mo")
    if df.empty:
        raise HTTPException(status_code=404, detail="Data not found")
    report = generate_ai_analysis_report(df)
    return {"symbol": symbol, "analysis": report}

@app.get("/api/options/analysis")
def get_options_analysis(symbol: str = "NIFTY", S: float = 20000, K: float = 20000, T: float = 30/365, sigma: float = 0.15):
    engine = BlackScholesEngine()
    greeks = engine.calculate_greeks(S, K, T, sigma)
    valuation = engine.analyze_option_strike_valuation(greeks['fair_value'], greeks['fair_value'])
    return {"greeks": greeks, "valuation": valuation}

@app.get("/api/options/strategy")
def get_options_strategy():
    strategy = OptionsBuyingStrategy()
    data = {"supertrend_bullish": True, "close": 105, "vwap": 100, "rsi": 55, "ema_bullish": True, "volume_spike_ratio": 2.0, "adx": 25, "ai_confidence": 75}
    return strategy.evaluate_entry(data)

@app.get("/api/paper-trading/portfolio")
def get_portfolio():
    return paper_sim.get_portfolio()

@app.post("/api/paper-trading/buy")
def paper_buy(req: BuyRequest):
    success = paper_sim.execute_buy(req.symbol, req.price, req.quantity)
    if not success:
        raise HTTPException(status_code=400, detail="Insufficient capital")
    return {"message": "Buy executed"}

@app.post("/api/paper-trading/close/{trade_id}")
def paper_close(trade_id: int, current_price: float = 0.0):
    success = paper_sim.execute_close(trade_id, current_price)
    if not success:
        raise HTTPException(status_code=404, detail="Trade not found")
    return {"message": "Trade closed"}

@app.post("/api/paper-trading/reset")
def paper_reset():
    global paper_sim
    paper_sim = PaperTradingSimulator()
    return {"message": "Portfolio reset"}

@app.get("/api/brain/status")
def get_brain_status():
    return {"is_trained": brain.is_trained}

@app.get("/api/brain/scenarios")
def get_brain_scenarios():
    gen = ScenarioGenerator()
    return {"scenarios": gen.generate_zero_loss_scenarios()}

@app.post("/api/brain/optimize")
def optimize_brain():
    df = fetch_stock_data("RELIANCE.NS", period="3mo")
    return brain.train_brain_model(df)

@app.get("/api/screener")
def get_screener():
    return {"results": [{"symbol": s, "score": 85} for s in POPULAR_STOCKS[:5]]}

@app.post("/api/backtest")
def run_backtest(symbol: str = "RELIANCE.NS"):
    df = fetch_stock_data(symbol, period="1y")
    bt = Backtester()
    return bt.run_volume_backtest(df)

@app.get("/api/monte-carlo/simulate")
def run_mc_simulation(S0: float = 1000, mu: float = 0.1, sigma: float = 0.2, T: float = 1.0):
    mc = MonteCarloSimulator()
    return mc.simulate(S0, mu, sigma, T)

@app.get("/api/stress-test/run")
def run_stress_test():
    st = StressTester()
    return st.run_stress_test(paper_sim.get_portfolio())

@app.get("/api/signals/verify")
def verify_signal():
    verifier = SignalVerifier()
    return verifier.verify_signal({"rsi": 65}, {"delta": 0.5}, {"trend_up": True})

@app.get("/api/signals/generate")
def generate_signal():
    gen = SignalGenerator()
    return gen.generate_signal(80, 60, 90)

@app.get("/api/indicators/{symbol}")
def get_indicators(symbol: str):
    df = fetch_stock_data(symbol, period="1mo")
    if df.empty:
        raise HTTPException(status_code=404, detail="Data not found")
    classifier = MarketRegimeClassifier()
    return classifier.classify(df)

@app.get("/api/patterns/{symbol}")
def get_patterns(symbol: str):
    df = fetch_stock_data(symbol, period="1mo")
    if df.empty:
        raise HTTPException(status_code=404, detail="Data not found")
    pr = PatternRecognizer()
    return {"patterns": pr.detect_patterns(df)}

@app.get("/api/broker/status")
def get_broker_status():
    return broker_adapter.get_broker_status()

@app.post("/api/broker/connect")
def connect_broker(payload: Dict[str, Any] = {}):
    client_code = payload.get("client_code")
    password = payload.get("password")
    totp = payload.get("totp")
    return broker_adapter.connect_session(client_code, password, totp)

@app.get("/api/broker/options-chain/{symbol}")
def get_broker_options_chain(symbol: str):
    return {"symbol": symbol, "chain": broker_adapter.get_live_option_chain_ltp(symbol)}

@app.get("/api/signals/verify-live")
def get_live_verification_stats():
    return market_verifier.get_live_verification_stats()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
