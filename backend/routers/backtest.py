"""Backtest, walk-forward, Monte Carlo & stress test routes."""
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.stock_data import fetch_stock_data, fetch_live_quote, generate_synthetic_stock_data
from services.backtester import Backtester, run_volume_backtest
from services.walk_forward_backtester import WalkForwardBacktester, default_strategy, DEFAULT_PARAM_GRID
from services.monte_carlo import MonteCarloSimulator
from services.stress_tester import StressTester
from services.paper_portfolio import paper_portfolio

router = APIRouter()


class BacktestRequest(BaseModel):
    symbol: str = "NIFTY"
    volumeMultiplier: float = 2.0
    holdingDays: int = 5
    stopLossPct: float = 2.0
    takeProfitPct: float = 6.0
    initialCapital: float = 100000.0
    costPerTradePct: float = 0.15


@router.get("/api/backtest")
def run_backtest(symbol: str = "NIFTY"):
    df = fetch_stock_data(symbol, period="1y")
    if df.empty or len(df) < 25:
        df = generate_synthetic_stock_data(symbol, days=250)
    bt = Backtester()
    res = bt.run_volume_backtest(df)
    res["dataSource"] = df.attrs.get("dataSource", "unknown")
    return res


@router.post("/api/backtest")
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
        cost_per_trade_pct=req.costPerTradePct,
    )
    res["dataSource"] = df.attrs.get("dataSource", "unknown")
    return res


@router.post("/api/backtest/walk-forward")
@router.get("/api/backtest/walk-forward")
def run_walk_forward(symbol: str = "NIFTY", in_sample_months: int = 3,
                     out_sample_months: int = 1, step_months: int = 1):
    df = fetch_stock_data(symbol, period="2y")
    if df.empty:
        df = fetch_stock_data("RELIANCE.NS", period="2y")
    wfb = WalkForwardBacktester(in_sample_months, out_sample_months, step_months)
    result = wfb.run_walk_forward(df, default_strategy, DEFAULT_PARAM_GRID)
    result["symbol"] = symbol
    return result


@router.get("/api/monte-carlo/simulate")
@router.get("/api/montecarlo/{symbol}")
def run_mc_simulation(symbol: str = "NIFTY", S0: float = 0.0, mu: float = 0.1, sigma: float = 0.2, T: float = 1.0):
    quote = fetch_live_quote(symbol)
    spot = S0 if S0 > 0 else quote.get("current_price", 24649.0)
    mc = MonteCarloSimulator()
    return mc.simulate(spot, mu, sigma, T)


@router.get("/api/stress-test/run")
@router.get("/api/stress/{symbol}")
def run_stress_test(symbol: str = "NIFTY"):
    st = StressTester()
    return st.run_stress_test(paper_portfolio.get_portfolio())
