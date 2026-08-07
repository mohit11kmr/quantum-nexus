"""Playbook, alerts, news & workflow routes."""
from typing import Dict, Any

from fastapi import APIRouter

from services.profit_playbook import profit_playbook
from services.telegram_alerts import telegram_alerts
from services.news_scanner import news_scanner
from services.trading_graph import run_trading_workflow

router = APIRouter()


@router.get("/api/profit-playbook")
def get_profit_playbook(symbol: str = "NIFTY", capital: float = 100000.0):
    res = profit_playbook.evaluate_wealth_trade(symbol, capital)
    # Auto-dispatch Telegram alert if signal is active
    telegram_alerts.send_trade_signal_alert(res)
    return res


@router.post("/api/telegram/dispatch")
def dispatch_telegram_alert(payload: Dict[str, Any] = {}):
    sent = telegram_alerts.send_trade_signal_alert(payload)
    return {"status": "dispatched" if sent else "failed", "channel": telegram_alerts.chat_id}


@router.get("/api/news/sentiment/{symbol}")
def get_news_sentiment(symbol: str):
    return news_scanner.analyze_sentiment(symbol)


@router.get("/api/news/{symbol}")
def get_news(symbol: str, limit: int = 10):
    return {"symbol": symbol, "articles": news_scanner.fetch_news(symbol, limit)}


@router.post("/api/workflow/run")
def run_workflow(payload: Dict[str, Any] = {}):
    symbol = payload.get("symbol", "NIFTY")
    result = run_trading_workflow(symbol, payload.get("portfolio_state"))
    out = {k: v for k, v in result.items() if k != "market_df"}
    out["symbol"] = symbol
    return out
