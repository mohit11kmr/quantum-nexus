"""
Automated Daily Market Report.

A scheduler builds a full-market report once per weekday at 15:30 IST (market
close) and stores it in-memory + persists to JSON. The frontend Daily Report
page reads it via GET /api/report/daily, and POST /api/report/daily/generate
forces a build.

The report is logic-driven and detailed: every verdict carries the reasoning
behind it (technical indicators, options flow, news sentiment, portfolio state).
"""

import asyncio
import json
import logging
import os
import threading
from datetime import datetime, timedelta, time as dtime
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from services.stock_data import fetch_live_quote, fetch_stock_data
from services.profit_playbook import profit_playbook
from services.options_intel import compute_options_intel
from services.options_strategy import AdvancedOptionsBuyingStrategy
from services.paper_portfolio import paper_portfolio
from services.news_scanner import news_scanner
from services.indicators import (
    calculate_indicators,
    supertrend_bullish,
    weighted_signal_strength,
    calculate_support_resistance,
)
from services.regime_classifier import MarketRegimeClassifier
from services.learning_brain import ai_confidence_from_df

log = logging.getLogger("quantum_nexus.report")

TZ_IST = ZoneInfo("Asia/Kolkata")
CLOSE_TIME = dtime(15, 30)
SCHEDULER_POLL_SEC = 30.0

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
STORE_PATH = os.path.join(DATA_DIR, "daily_report.json")

INDICES = ["NIFTY", "BANKNIFTY", "FINNIFTY"]

MOVER_SYMBOLS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "SBIN.NS", "LT.NS", "ITC.NS", "AXISBANK.NS", "TATAMOTORS.NS",
    "TATASTEEL.NS", "HINDALCO.NS",
]


def _round(v: Any, nd: int = 2) -> float:
    try:
        return round(float(v), nd)
    except (TypeError, ValueError):
        return 0.0


def _trend_word(change_pct: float) -> str:
    if change_pct >= 0.3:
        return "BULLISH"
    if change_pct <= -0.3:
        return "BEARISH"
    return "FLAT"


def _rsi_read(rsi: float) -> str:
    if rsi >= 70:
        return "overbought (risk of pullback)"
    if rsi >= 60:
        return "strong momentum, not yet overbought"
    if rsi <= 30:
        return "oversold (rebound possible)"
    if rsi <= 45:
        return "weak momentum"
    return "neutral momentum band"


def _technical_logic(rsi: float, adx: float, supertrend: bool, ema_bullish: bool,
                     regime: str, spot: float, vwap: float, vol_surge: float,
                     atr_pct: float) -> List[str]:
    reasons = [
        f"RSI(14) at {rsi:.1f} -> {_rsi_read(rsi)}.",
        f"ADX at {adx:.1f} -> trend is {'strong' if adx >= 25 else 'moderate' if adx >= 20 else 'weak/choppy'}.",
        f"SuperTrend is {'GREEN (bullish)' if supertrend else 'RED (bearish)'}.",
        f"EMA9 {'above' if ema_bullish else 'below'} EMA21 -> short-term trend {'up' if ema_bullish else 'down'}.",
        f"Price {'above' if spot >= vwap else 'below'} VWAP ({vwap:,.0f}) -> intraday bias {'buy-side' if spot >= vwap else 'sell-side'}.",
        f"Volume surge ratio {vol_surge:.2f}x -> {'institutional participation elevated' if vol_surge >= 1.5 else 'normal activity'}.",
        f"ATR {atr_pct:.2f}% of spot -> {'wide' if atr_pct >= 1.5 else 'narrow'} daily range.",
        f"Regime classifier: {regime}.",
    ]
    return reasons


def _interpret_technical(spot: float, tech: Dict[str, Any]) -> str:
    rsi = tech.get("rsi", 50)
    adx = tech.get("adx", 0)
    supertrend = tech.get("supertrend_bullish", True)
    ema = tech.get("ema_bullish", True)
    supports = tech.get("supports", [])
    resistances = tech.get("resistances", [])
    s = supports[0] if supports else spot
    r = resistances[0] if resistances else spot
    if supertrend and ema and rsi >= 50:
        bias = f"constructive with upside potential toward {r:,.0f}"
    elif not supertrend and not ema:
        bias = f"defensive with downside risk toward {s:,.0f}"
    else:
        bias = f"two-sided; watch break above {r:,.0f} or below {s:,.0f} for direction"
    return f"NIFTY at {spot:,.0f} is in a {tech.get('regime', 'UNKNOWN')} regime with RSI {rsi:.0f} and ADX {adx:.0f}. Technical picture is {bias}."


def _build_indices() -> List[Dict[str, Any]]:
    indices = []
    for idx in INDICES:
        q = fetch_live_quote(idx)
        price = _round(q.get("current_price"))
        change_pct = _round(q.get("change_pct"))
        indices.append({
            "symbol": idx,
            "price": price,
            "change": _round(q.get("change")),
            "change_pct": change_pct,
            "trend": _trend_word(change_pct),
            "status": q.get("status", "OFFLINE"),
            "data_source": q.get("data_source", "unknown"),
        })
    return indices


def _build_movers() -> Dict[str, List[Dict[str, Any]]]:
    movers = []
    for ms in MOVER_SYMBOLS:
        q = fetch_live_quote(ms)
        price = _round(q.get("current_price"))
        if price > 0:
            movers.append({
                "symbol": ms.replace(".NS", ""),
                "price": price,
                "change_pct": _round(q.get("change_pct")),
                "change": _round(q.get("change")),
            })
    movers.sort(key=lambda m: m["change_pct"], reverse=True)
    return {"gainers": movers[:5], "losers": sorted(movers, key=lambda m: m["change_pct"])[:5]}


def _build_technical(symbol: str, spot: float) -> Dict[str, Any]:
    tech: Dict[str, Any] = {"available": False}
    try:
        df = fetch_stock_data(symbol, period="3mo")
        if df.empty:
            df = fetch_stock_data("RELIANCE.NS", period="3mo")
        if df.empty:
            return tech
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        regime = MarketRegimeClassifier().classify(df)
        strength, score, grade, reasons = weighted_signal_strength(latest)
        supports, resistances = calculate_support_resistance(df)
        rsi = float(latest.get("RSI", 50.0))
        adx = float(latest.get("ADX", 0.0))
        atr = float(latest.get("ATR", 0.0))
        tech = {
            "available": True,
            "regime": regime.get("regime", "UNKNOWN"),
            "regime_confidence": _round(regime.get("confidence", 0.0), 1),
            "supertrend_bullish": bool(supertrend_bullish(df)),
            "ema_bullish": float(latest.get("EMA9", 0.0)) > float(latest.get("EMA21", 0.0)),
            "rsi": _round(rsi, 1),
            "stoch_rsi": _round(latest.get("StochRSI", 50.0), 1),
            "adx": _round(adx, 1),
            "vwap": _round(latest.get("VWAP", spot)),
            "atr_pct": _round((atr / spot) * 100.0, 2) if spot > 0 else 0.0,
            "vol_surge_ratio": _round(latest.get("Vol_Surge_Ratio", 1.0), 2),
            "supports": [_round(float(x)) for x in (supports or [])][:3],
            "resistances": [_round(float(x)) for x in (resistances or [])][:3],
            "signal_grade": grade,
            "signal_score": score,
            "signal_strength": strength,
            "signal_reasons": reasons,
        }
        tech["interpretation"] = _interpret_technical(spot, tech)
        tech["logic"] = _technical_logic(
            rsi, adx, tech["supertrend_bullish"], tech["ema_bullish"],
            tech["regime"], spot, tech["vwap"], tech["vol_surge_ratio"], tech["atr_pct"],
        )
    except Exception as exc:  # noqa: BLE001 - report should never crash
        log.warning("technical build failed: %s", exc)
    return tech


def _build_options_detail(symbol: str, spot: float, intel: Dict[str, Any]) -> Dict[str, Any]:
    detail: Dict[str, Any] = {"available": False}
    try:
        strategy = AdvancedOptionsBuyingStrategy()
        df = fetch_stock_data(symbol, period="3mo")
        if df.empty:
            df = fetch_stock_data("RELIANCE.NS", period="3mo")
        df = calculate_indicators(df)
        latest = df.iloc[-1]
        res = strategy.evaluate_entry({
            "supertrend_bullish": supertrend_bullish(df),
            "close": spot,
            "vwap": float(latest.get("VWAP", spot)),
            "rsi": float(latest.get("RSI", 55.0)),
            "ema_bullish": float(latest.get("EMA9", 0.0)) > float(latest.get("EMA21", 0.0)),
            "volume_spike_ratio": float(latest.get("Vol_Surge_Ratio", 1.0)),
            "adx": float(latest.get("ADX", 20.0)),
            "ai_confidence": ai_confidence_from_df(df),
            "iv_rank": intel.get("iv_rank_pct", 45.0),
            "dte_days": 3.0,
        })
        direction = intel.get("directionLabel", "NEUTRAL")
        ivr = intel.get("iv_rank_pct", 45.0)
        if direction == "BULLISH":
            rec = "Buy call debit strategies (CE long / call spread) for upside continuation."
        elif direction == "BEARISH":
            rec = "Buy put debit strategies (PE long / put spread) for downside protection."
        else:
            rec = "Range-bound bias: prefer short strangle / iron condor (theta) or wait for a breakout."
        if ivr > 65:
            iv_read = "IV is elevated — premiums rich, favour credit (selling) strategies or wait for IV crush."
        elif ivr > 40:
            iv_read = "IV is moderate — option premiums are reasonably priced for directional plays."
        else:
            iv_read = "IV is low — debit (buying) strategies are cost-effective."
        detail = {
            "available": True,
            "strategy_score": res.get("strategy_score"),
            "quality": res.get("quality"),
            "signal": res.get("signal"),
            "passed": res.get("conditions_passed", []),
            "failed": res.get("conditions_failed", []),
            "recommendation": rec,
            "iv_interpretation": f"IV Rank {ivr}%: {iv_read}",
            "logic": [
                f"Strategy score {res.get('strategy_score', 0)}/100, quality {res.get('quality', '-')}.",
                f"Direction score {intel.get('directionScore', 50)} -> {direction}.",
                f"PCR(OI) {intel.get('pcr_oi', 0):.2f} -> {'put writers dominate (supportive)' if intel.get('pcr_oi', 1) >= 1.0 else 'call writers dominate (resistance)'}.",
                f"Max pain at {intel.get('max_pain_strike', 0)} acts as the settlement magnet.",
                f"Call wall {intel.get('call_wall', 0)} / Put wall {intel.get('put_wall', 0)} define the trading box.",
            ],
        }
    except Exception as exc:  # noqa: BLE001
        log.warning("options detail build failed: %s", exc)
    return detail


def _build_news(symbol: str) -> Dict[str, Any]:
    news: Dict[str, Any] = {"available": False}
    try:
        sent = news_scanner.analyze_sentiment(symbol)
        news = {
            "available": sent.get("sources_analyzed", 0) > 0,
            "classification": sent.get("classification", "NEUTRAL"),
            "score": _round(sent.get("sentiment_score", 0.0), 3),
            "sources": sent.get("sources_analyzed", 0),
            "headlines": [a.get("title", "") for a in sent.get("articles", [])[:5]],
            "note": sent.get("note", ""),
        }
        if news["available"]:
            news["logic"] = [f"{news['sources']} headlines scanned, aggregate sentiment {news['classification']} (score {news['score']:+.2f})."]
        else:
            news["logic"] = ["News feed unavailable offline; sentiment treated neutral."]
    except Exception as exc:  # noqa: BLE001
        log.warning("news build failed: %s", exc)
    return news


def _build_plan(condition: str, tech: Dict[str, Any], options: Dict[str, Any],
                news: Dict[str, Any], signal: Dict[str, Any],
                portfolio: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    logic: List[str] = []
    actions: List[str] = []

    if condition == "BULLISH":
        logic.append("Composite condition BULLISH (index momentum + options flow aligned positive).")
        actions.append("Buy-the-dip on NIFTY strength above VWAP; set SL below day low.")
    elif condition == "BEARISH":
        logic.append("Composite condition BEARISH (index momentum + options flow aligned negative).")
        actions.append("Stay defensive; avoid fresh longs, use puts/hedges on breakdown.")
    else:
        logic.append("Composite condition NEUTRAL (mixed signals).")
        actions.append("Trade only range boundaries — buy near support, sell near resistance.")

    if tech.get("available"):
        logic.extend(tech.get("logic", []))
        if tech.get("signal_grade") == "STRONG":
            actions.append(f"Technical grade STRONG (score {tech.get('signal_score')}) supports active trading.")
        elif tech.get("signal_grade") == "WEAK":
            actions.append(f"Technical grade WEAK (score {tech.get('signal_score')}) - reduce position size.")
        supports = tech.get("supports", [])
        resistances = tech.get("resistances", [])
        if supports:
            actions.append(f"Key support zone: {', '.join(f'{s:,.0f}' for s in supports)}.")
        if resistances:
            actions.append(f"Key resistance zone: {', '.join(f'{r:,.0f}' for r in resistances)}.")

    if options.get("available"):
        logic.append(options.get("iv_interpretation", ""))
        actions.append(options.get("recommendation", ""))
        if options.get("quality") in ("A", "A+"):
            actions.append("Options setup quality A+ — high-probability entry framework active.")
        else:
            actions.append("Options setup quality below A — keep premium risk small, use spreads.")

    if news.get("available"):
        logic.extend(news.get("logic", []))
        if news.get("classification") == "BULLISH":
            actions.append("News sentiment positive — tailwinds for longs.")
        elif news.get("classification") == "BEARISH":
            actions.append("News sentiment negative — headwinds, tighten stops.")
        else:
            actions.append("News sentiment neutral — no macro catalyst.")

    if signal.get("action") and "BUY" in signal.get("action", ""):
        actions.append(f"Playbook flags {signal['action']} on {symbol} {signal.get('contract', '')} (win {signal.get('win_probability', 0)}%).")
    elif signal.get("action") and "WAIT" in signal.get("action", ""):
        actions.append("Playbook says WAIT_FOR_SETUP — no entry until triple confirmation passes.")

    if portfolio.get("total_pnl_pct") is not None and portfolio.get("total_pnl_pct") < 0:
        actions.append("Paper book underwater - avoid adding risk; protect capital.")
    elif portfolio.get("win_rate_pct") is not None and portfolio.get("win_rate_pct", 0) >= 50:
        actions.append("Paper win-rate healthy - existing edge still valid.")

    verdict = f"{condition} outlook for {symbol}. {'Risk-on bias.' if condition == 'BULLISH' else 'Risk-off bias.' if condition == 'BEARISH' else 'Stay range-disciplined.'}"
    return {"verdict": verdict, "actions": actions[:8], "logic": logic}


def build_daily_report(symbol: str = "NIFTY") -> Dict[str, Any]:
    """Compile the complete logic-driven daily report."""
    now_ist = datetime.now(TZ_IST)

    indices = _build_indices()
    movers = _build_movers()
    spot = 0.0
    for i in indices:
        if i["symbol"] == symbol:
            spot = i["price"]
            break
    if not spot and indices:
        spot = indices[0]["price"]

    # Trading signal (playbook)
    signal: Dict[str, Any] = {}
    try:
        pb = profit_playbook.evaluate_wealth_trade(symbol, 100000.0)
        signal = {
            "action": pb.get("trade_status", "WAIT_FOR_SETUP"),
            "contract": pb.get("option_contract", ""),
            "spot_price": _round(pb.get("spot_price")),
            "entry": _round(pb.get("entry_premium")),
            "target": _round(pb.get("target_premium")),
            "stop_loss": _round(pb.get("stop_loss_premium")),
            "rr": pb.get("risk_reward_ratio", "1:2.5"),
            "win_probability": _round(pb.get("win_probability")),
            "rules": pb.get("golden_rules_audit", []),
        }
    except Exception as exc:  # noqa: BLE001
        log.warning("signal build failed: %s", exc)

    # Options intelligence
    options: Dict[str, Any] = {}
    try:
        intel = compute_options_intel(symbol)
        options = {
            "direction_score": intel.get("directionScore"),
            "direction_label": intel.get("directionLabel"),
            "pcr_oi": _round(intel.get("pcr_oi")),
            "pcr_volume": _round(intel.get("pcr_volume")),
            "max_pain_strike": intel.get("max_pain_strike"),
            "iv_rank_pct": _round(intel.get("iv_rank_pct")),
            "atm_iv": _round(intel.get("atm_iv")),
            "call_wall": intel.get("call_wall"),
            "put_wall": intel.get("put_wall"),
            "reasons": intel.get("reasons", []),
            "data_source": intel.get("data_source", "unknown"),
        }
        options["detail"] = _build_options_detail(symbol, spot, intel)
    except Exception as exc:  # noqa: BLE001
        log.warning("options intel build failed: %s", exc)

    # Technical deep-dive
    technical = _build_technical(symbol, spot)

    # News sentiment
    news = _build_news(symbol)

    # Paper portfolio
    portfolio: Dict[str, Any] = {}
    try:
        port = paper_portfolio.get_portfolio()
        portfolio = {
            "total_value": _round(port.get("totalPortfolioValue")),
            "cash": _round(port.get("cashBalance")),
            "total_pnl": _round(port.get("totalPnl")),
            "total_pnl_pct": _round(port.get("totalPnlPct")),
            "realized_pnl": _round(port.get("realizedPnl")),
            "unrealized_pnl": _round(port.get("unrealizedPnl")),
            "win_rate_pct": _round(port.get("winRatePct"), 1),
            "open_positions": port.get("openPositionsCount", 0),
            "closed_trades": port.get("closedTradesCount", 0),
            "positions": [
                {
                    "symbol": p.get("symbol"),
                    "entry": _round(p.get("entryPrice")),
                    "current": _round(p.get("currentPrice")),
                    "unrealized_pnl": _round(p.get("unrealizedPnl")),
                    "pnl_pct": _round(p.get("pnlPct")),
                }
                for p in (port.get("openPositions") or [])
            ][:5],
        }
    except Exception as exc:  # noqa: BLE001
        log.warning("portfolio build failed: %s", exc)

    # Composite market condition
    idx_changes = [i["change_pct"] for i in indices if i["price"] > 0]
    avg_idx_change = (sum(idx_changes) / len(idx_changes)) if idx_changes else 0.0
    dir_score = options.get("direction_score") or 50.0
    cond_score = avg_idx_change * 2.0 + (dir_score - 50.0) * 0.5
    if cond_score >= 8.0:
        condition = "BULLISH"
    elif cond_score <= -8.0:
        condition = "BEARISH"
    else:
        condition = "NEUTRAL"

    if condition == "BULLISH":
        headline = f"Markets closed firm. {symbol} at {spot:,.2f} ({avg_idx_change:+.2f}% avg)."
    elif condition == "BEARISH":
        headline = f"Markets closed lower. {symbol} at {spot:,.2f} ({avg_idx_change:+.2f}% avg)."
    else:
        headline = f"Markets were mixed. {symbol} at {spot:,.2f} ({avg_idx_change:+.2f}% avg)."

    # Risk summary
    risk = {
        "atr_pct": technical.get("atr_pct") if technical.get("available") else None,
        "vol_class": "HIGH" if (technical.get("atr_pct") or 0) >= 1.5 else "LOW" if (technical.get("atr_pct") or 0) < 0.8 else "MEDIUM",
        "iv_rank_pct": options.get("iv_rank_pct"),
        "direction_score": options.get("direction_score"),
        "logic": [
            f"Daily ATR {technical.get('atr_pct')}% of spot -> stop-loss should be at least {max(1.0, (technical.get('atr_pct') or 1.0) * 1.5):.1f}% wide.",
            f"IV Rank {options.get('iv_rank_pct')}% -> {'premium selling favoured' if (options.get('iv_rank_pct') or 0) > 65 else 'premium buying favoured' if (options.get('iv_rank_pct') or 0) < 40 else 'neutral premium pricing'}.",
        ],
    }

    plan = _build_plan(condition, technical, options, news, signal, portfolio, symbol)

    return {
        "date": now_ist.date().isoformat(),
        "generated_at": now_ist.isoformat(),
        "posted": "MANUAL",
        "symbol": symbol,
        "headline": headline,
        "market_condition": condition,
        "cond_score": _round(cond_score),
        "avg_index_change_pct": _round(avg_idx_change),
        "indices": indices,
        "movers": movers,
        "signal": signal,
        "options": options,
        "technical": technical,
        "news": news,
        "portfolio": portfolio,
        "risk": risk,
        "plan": plan,
    }


def _next_scheduled_run() -> str:
    """Next weekday 15:30 IST as ISO string."""
    now = datetime.now(TZ_IST)
    candidate = now.replace(hour=CLOSE_TIME.hour, minute=CLOSE_TIME.minute, second=0, microsecond=0)
    if candidate <= now or candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate.isoformat()


class DailyReportScheduler:
    """Runs once per weekday at 15:30 IST; stores the latest report."""

    def __init__(self) -> None:
        self._latest: Optional[Dict[str, Any]] = None
        self._last_date: Optional[str] = None
        self._lock = threading.Lock()
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._restore()

    # ── persistence ──────────────────────────────────────────────────────
    def _restore(self) -> None:
        try:
            if not os.path.exists(STORE_PATH):
                return
            with open(STORE_PATH, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            self._latest = payload.get("report")
            self._last_date = payload.get("last_date")
            if self._latest:
                log.info("restored daily report from %s", STORE_PATH)
        except Exception as exc:  # noqa: BLE001
            log.warning("failed to restore daily report: %s", exc)

    def _persist(self) -> None:
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with self._lock:
                payload = {"report": self._latest, "last_date": self._last_date}
            tmp = STORE_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False)
            os.replace(tmp, STORE_PATH)
        except Exception as exc:  # noqa: BLE001
            log.warning("failed to persist daily report: %s", exc)

    async def start(self) -> None:
        self._running = True
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop())

    def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _loop(self) -> None:
        while self._running:
            try:
                now = datetime.now(TZ_IST)
                if now.weekday() < 5 and now.hour == CLOSE_TIME.hour and now.minute >= CLOSE_TIME.minute:
                    date_key = now.date().isoformat()
                    if self._last_date != date_key:
                        report = await asyncio.to_thread(build_daily_report)
                        report["posted"] = "AUTO"
                        report["generated_at"] = now.isoformat()
                        report["date"] = date_key
                        with self._lock:
                            self._latest = report
                            self._last_date = date_key
                        self._persist()
                        log.info("auto daily report posted for %s", date_key)
            except asyncio.CancelledError:
                break
            except Exception as exc:  # noqa: BLE001
                log.warning("scheduler error: %s", exc)
            await asyncio.sleep(SCHEDULER_POLL_SEC)

    def get_latest(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            return dict(self._latest) if self._latest else None

    def force_generate(self, symbol: str = "NIFTY") -> Dict[str, Any]:
        report = build_daily_report(symbol)
        report["posted"] = "MANUAL"
        with self._lock:
            self._latest = report
            self._last_date = report.get("date")
        self._persist()
        return report


daily_report_scheduler = DailyReportScheduler()
