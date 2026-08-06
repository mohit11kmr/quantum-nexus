"""
Trading Workflow - LangGraph StateGraph orchestration.

Adopts the DAG pattern from ai-trading-agents (workflows/trading_graph.py):

    Market Data -> Signal Detection -> Strategy Decision
                                     -> Risk Validation -> Execution -> Portfolio Update

Unlike the source project (which used placeholders/simulation), every node here
runs a REAL quantum_nexus service: real market data + indicators, the real
signal generator, the real price predictor, the real risk engine, and a
paper-safe execution path (broker if connected, else PaperTradingSimulator).
"""

import json
import time
from datetime import datetime, timezone
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from services.stock_data import fetch_stock_data, fetch_live_quote, normalize_symbol
from services.indicators import calculate_indicators
from services.signal_generator import signal_generator
from services.price_predictor import price_predictor
from services.risk_engine import RiskEngine
from services.broker_adapter import broker_adapter
from services.learning_brain import ai_confidence_from_df
from services.paper_portfolio import paper_portfolio


class TradingState(TypedDict, total=False):
    symbol: str
    raw_market_data: dict
    market_df: Any
    normalized_market: dict
    signal: dict
    decision: dict
    risk_result: dict
    execution: dict
    portfolio: dict
    should_trade: bool
    error: str
    portfolio_state: dict


# ── Node 1: Real market data + indicators ─────────────────────────────
def market_data_node(state: TradingState) -> TradingState:
    symbol = state.get("symbol", "NIFTY")
    try:
        quote = fetch_live_quote(symbol)
        df = fetch_stock_data(symbol, period="3mo")
        indicators = {}
        if df is not None and not df.empty and len(df) >= 20:
            df = calculate_indicators(df)
            state["market_df"] = df
            row = df.iloc[-1]
            indicators = {
                "rsi_14": round(float(row.get("RSI", 50)), 2),
                "adx_14": round(float(row.get("ADX", 20)), 2),
                "vwap": round(float(row.get("VWAP", 0)), 2),
                "sma_20": round(float(df["Close"].tail(20).mean()), 2),
                "atr": round(float(row.get("ATR", 0)), 2),
                "vol_surge_ratio": round(float(row.get("Vol_Surge_Ratio", 1.0)), 2),
                "supertrend_dir": str(row.get("SuperTrend_Dir", "UP")),
            }
        state["normalized_market"] = {
            "symbol": symbol,
            "price": float(quote.get("current_price") or 0.0),
            "volume": int(quote.get("volume") or 0),
            "change_pct": float(quote.get("change_pct") or 0.0),
            "status": quote.get("status", "OFFLINE"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **indicators,
        }
    except Exception as e:
        state["error"] = f"Market data node failed: {e}"
    return state


# ── Node 2: Real signal detection ─────────────────────────────────────
def signal_detection_node(state: TradingState) -> TradingState:
    if state.get("error"):
        return state
    symbol = state.get("symbol", "NIFTY")
    df = state.get("market_df")
    try:
        ai_confidence = ai_confidence_from_df(df) if df is not None and not df.empty else 75.0
        st_dir = str(state.get("normalized_market", {}).get("supertrend_dir", ""))
        mtf = "BULLISH" if st_dir.upper() in ("UP", "1.0", "TRUE") else "BEARISH"
        result = signal_generator.generate_signal(df, ai_confidence=ai_confidence, mtf_trend=mtf)

        signal_type = result.get("signal", "NEUTRAL")
        if signal_type in ("STRONG_BUY", "BUY", "WEAK_BUY"):
            side = "buy"
        elif signal_type in ("STRONG_SELL", "SELL"):
            side = "sell"
        else:
            side = "hold"

        state["signal"] = {
            "signal_id": f"sig_{int(time.time())}",
            "symbol": symbol,
            "signal_type": side,
            "raw_signal": signal_type,
            "confidence": float(result.get("confidence", 0.0)),
            "quality": result.get("quality", "C"),
            "indicator": "Weighted Multi-Source",
            "price_at_signal": float(result.get("entry_price", 0.0) or 0.0),
            "stop_loss": float(result.get("stop_loss", 0.0) or 0.0),
            "target_price": float(result.get("target_price", 0.0) or 0.0),
            "reason": result.get("reason", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        state["should_trade"] = side in ("buy", "sell")
    except Exception as e:
        state["error"] = f"Signal detection failed: {e}"
    return state


# ── Node 3: Strategy decision (real price predictor cross-check) ──────
def strategy_decision_node(state: TradingState) -> TradingState:
    if state.get("error") or not state.get("should_trade", False):
        state["decision"] = {"approved": False, "reason": "No actionable signal"}
        return state
    signal = state.get("signal", {})
    df = state.get("market_df")
    try:
        prediction = {}
        if df is not None and not df.empty:
            prediction = price_predictor.predict_next_candles(df, num_predictions=3)
        pred_dir = str(prediction.get("direction", "mixed"))
        conf = float(signal.get("confidence", 0.0))
        side = signal.get("signal_type")

        # Cross-check: real predictor direction should not contradict the side.
        contradicts = (side == "buy" and "bear" in pred_dir) or (side == "sell" and "bull" in pred_dir)
        approved = conf >= 55.0 and not contradicts
        entry = signal.get("price_at_signal", 0.0)
        state["decision"] = {
            "signal_id": signal.get("signal_id"),
            "approved": approved,
            "reason": "Signal meets strategy + predictor alignment"
                     if approved else
                     (f"Confidence {conf} below 55" if conf < 55 else
                      f"Predictor direction {pred_dir} contradicts {side} signal"),
            "strategy_name": "MultiSource+Ensemble",
            "side": side,
            "entry_price": entry,
            "stop_loss": signal.get("stop_loss"),
            "take_profit": signal.get("target_price"),
            "ai_confidence": conf,
            "predictor_direction": pred_dir,
        }
    except Exception as e:
        state["error"] = f"Strategy decision failed: {e}"
    return state


# ── Node 4: Risk validation (real risk engine) ────────────────────────
def risk_validation_node(state: TradingState) -> TradingState:
    if state.get("error"):
        return state
    decision = state.get("decision", {})
    if not decision.get("approved", False):
        state["risk_result"] = {"passed": False, "reason": "Decision not approved"}
        return state
    try:
        capital = float(state.get("portfolio_state", {}).get("total_capital", 100000))
        entry = float(decision.get("entry_price", 0.0) or 0.0)
        sl = float(decision.get("stop_loss", 0.0) or 0.0)
        engine = RiskEngine(initial_capital=capital)
        risk = engine.evaluate_trade_risk(entry, sl)
        passed = risk.get("approved", False)
        if passed:
            size = int(risk.get("position_size", 0) or 0)
            max_affordable = int(capital / entry) if entry > 0 else 0
            size = max(0, min(size, max_affordable))
            if size < 1:
                passed = False
                risk["reason"] = "Not enough capital for even 1 unit"
            risk["position_size"] = size
        state["risk_result"] = {
            "passed": passed,
            "reason": risk.get("reason", "All risk checks passed" if passed else "Rejected"),
            "position_size": risk.get("position_size", 0),
            "risk_amount": risk.get("risk_amount", 0.0),
            "risk_score": round(min(1.0, float(risk.get("risk_amount", 0.0)) / max(0.01, capital)), 3),
        }
    except Exception as e:
        state["error"] = f"Risk validation failed: {e}"
    return state


# ── Node 5: Execution (broker if connected, else paper-safe) ──────────
def execution_node(state: TradingState) -> TradingState:
    if state.get("error"):
        return state
    risk = state.get("risk_result", {})
    if not risk.get("passed", False):
        state["execution"] = {"status": "skipped", "reason": risk.get("reason", "Risk rejected")}
        return state
    signal = state.get("signal", {})
    decision = state.get("decision", {})
    try:
        symbol = signal.get("symbol", state.get("symbol", "NIFTY"))
        qty = int(risk.get("position_size", 1) or 1)
        side = decision.get("side", signal.get("signal_type", "buy"))

        status = broker_adapter.get_broker_status()
        if status.get("connected") and not status.get("paper_mode", True):
            order = broker_adapter.place_live_order(symbol, qty=qty, side=side.upper())
            mode = "LIVE"
        else:
            price = float(decision.get("entry_price", 0.0) or 0.0)
            if price <= 0:
                price = float(signal.get("price_at_signal", 0.0) or 0.0)
            order = paper_portfolio.place_order(symbol, price, qty, side)
            mode = "PAPER"

        state["execution"] = {
            "mode": mode,
            "symbol": symbol,
            "side": side,
            "quantity": qty,
            "order": order,
            "status": order.get("status", "unknown"),
            "order_id": order.get("order_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        state["error"] = f"Execution failed: {e}"
    return state


# ── Node 6: Portfolio update ──────────────────────────────────────────
def portfolio_update_node(state: TradingState) -> TradingState:
    if state.get("error"):
        return state
    execution = state.get("execution", {})
    if execution.get("status") != "SUCCESS" and execution.get("order", {}).get("status") != "SUCCESS":
        if execution.get("status") == "skipped":
            state["portfolio"] = paper_portfolio.get_portfolio()
        return state
    try:
        state["portfolio"] = paper_portfolio.get_portfolio()
    except Exception as e:
        state["error"] = f"Portfolio update failed: {e}"
    return state


# ── Conditional edges ─────────────────────────────────────────────────
def should_continue_after_signal(state: TradingState) -> str:
    if state.get("error"):
        return "end"
    return "strategy_decision" if state.get("should_trade", False) else "end"


def should_continue_after_risk(state: TradingState) -> str:
    if state.get("error"):
        return "end"
    return "execution_node" if state.get("risk_result", {}).get("passed", False) else "end"


# ── Graph builder ─────────────────────────────────────────────────────
def build_trading_graph():
    graph = StateGraph(TradingState)

    graph.add_node("market_data", market_data_node)
    graph.add_node("signal_detection", signal_detection_node)
    graph.add_node("strategy_decision", strategy_decision_node)
    graph.add_node("risk_validation", risk_validation_node)
    graph.add_node("execution_node", execution_node)
    graph.add_node("portfolio_update", portfolio_update_node)

    graph.set_entry_point("market_data")
    graph.add_edge("market_data", "signal_detection")
    graph.add_conditional_edges("signal_detection", should_continue_after_signal,
                                {"strategy_decision": "strategy_decision", "end": END})
    graph.add_edge("strategy_decision", "risk_validation")
    graph.add_conditional_edges("risk_validation", should_continue_after_risk,
                                {"execution_node": "execution_node", "end": END})
    graph.add_edge("execution_node", "portfolio_update")
    graph.add_edge("portfolio_update", END)

    return graph.compile()


# ── Convenience runner ────────────────────────────────────────────────
def run_trading_workflow(symbol: str, portfolio_state: dict | None = None) -> TradingState:
    compiled = build_trading_graph()
    initial_state: TradingState = {
        "symbol": symbol,
        "portfolio_state": portfolio_state or paper_portfolio.get_portfolio(),
        "should_trade": False,
    }
    return compiled.invoke(initial_state)
