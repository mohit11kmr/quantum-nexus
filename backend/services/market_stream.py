"""
Realtime Market Stream Service.

Adopts the subscriber/broadcast WebSocket pattern from the ai-trading-agents
project (market_data_service.py + /ws/market endpoint), but feeds REAL market
data via stock_data.fetch_live_quote() instead of simulated GBM ticks.
"""

import asyncio
import time
from typing import Dict, List, Optional

from services.stock_data import fetch_live_quote

DEFAULT_INTERVAL_SEC = 2.0
HEARTBEAT_INTERVAL_SEC = 15.0


class MarketStreamService:
    def __init__(self, interval_sec: float = DEFAULT_INTERVAL_SEC):
        self.interval_sec = interval_sec
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._session: Dict[str, Dict[str, float]] = {}
        self._last_tick: Dict[str, Dict] = {}
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None

    def subscribe(self, symbol: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._subscribers.setdefault(symbol, []).append(q)
        last = self._last_tick.get(symbol)
        if last is not None:
            try:
                q.put_nowait(last)
            except asyncio.QueueFull:
                pass
        self._ensure_loop(symbol)
        return q

    def unsubscribe(self, symbol: str, q: asyncio.Queue) -> None:
        subs = self._subscribers.get(symbol, [])
        if q in subs:
            subs.remove(q)
        if not subs:
            self._subscribers.pop(symbol, None)
            self._stop_loop(symbol)

    def _ensure_loop(self, symbol: str) -> None:
        if symbol not in self._tasks or self._tasks[symbol].done():
            self._tasks[symbol] = asyncio.create_task(self._feed_loop(symbol))

    def _stop_loop(self, symbol: str) -> None:
        task = self._tasks.pop(symbol, None)
        if task:
            task.cancel()

    async def _feed_loop(self, symbol: str) -> None:
        while self._running:
            try:
                quote = await asyncio.to_thread(fetch_live_quote, symbol)
                if quote and float(quote.get("current_price") or 0.0) > 0:
                    tick = self._build_tick(symbol, quote)
                    self._last_tick[symbol] = tick
                else:
                    tick = {"symbol": symbol, "status": "OFFLINE",
                            "price": 0.0, "timestamp": time.time()}
                await self._broadcast(symbol, tick)
            except Exception:
                pass
            await asyncio.sleep(self.interval_sec)

    def _build_tick(self, symbol: str, quote: Dict) -> Dict:
        sess = self._session.setdefault(symbol, {"high": 0.0, "low": float("inf")})
        price = float(quote.get("current_price") or 0.0)
        sess["high"] = max(sess["high"], price)
        sess["low"] = min(sess["low"], price)
        now = time.time()
        return {
            "symbol": symbol,
            "price": price,
            "previous_close": float(quote.get("previous_close") or 0.0),
            "change": float(quote.get("change") or 0.0),
            "change_pct": float(quote.get("change_pct") or 0.0),
            "volume": int(quote.get("volume") or 0),
            "session_high": round(sess["high"], 2),
            "session_low": round(sess["low"], 2),
            "timestamp": now,
            "age_sec": 0.0,
            "status": quote.get("status", "LIVE_REALTIME"),
            "data_source": quote.get("data_source", "unknown"),
        }

    def get_tick(self, symbol: str) -> Optional[Dict]:
        """Freshest cached tick (served by the REST /api/market/ticks endpoint)."""
        tick = self._last_tick.get(symbol)
        if tick is not None:
            tick["age_sec"] = round(time.time() - tick.get("timestamp", time.time()), 2)
        return dict(tick) if tick else None

    async def _broadcast(self, symbol: str, tick: Dict) -> None:
        for q in list(self._subscribers.get(symbol, [])):
            try:
                q.put_nowait(tick)
            except asyncio.QueueFull:
                pass

    async def _heartbeat_loop(self) -> None:
        while self._running:
            await asyncio.sleep(HEARTBEAT_INTERVAL_SEC)
            if not self._subscribers:
                continue
            heartbeat = {
                "type": "heartbeat",
                "timestamp": time.time(),
                "active_symbols": list(self._last_tick.keys()),
            }
            for q in list(self._subscribers.values()):
                for sub_q in list(q):
                    try:
                        sub_q.put_nowait(heartbeat)
                    except asyncio.QueueFull:
                        pass

    async def start(self) -> None:
        self._running = True
        if self._heartbeat_task is None or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    def stop(self) -> None:
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None
        for task in self._tasks.values():
            task.cancel()
        self._tasks.clear()
        self._subscribers.clear()

    def get_status(self) -> Dict:
        return {
            "running": self._running,
            "interval_sec": self.interval_sec,
            "active_symbols": list(self._tasks.keys()),
            "subscribers": {s: len(qs) for s, qs in self._subscribers.items()},
            "last_prices": {s: t.get("price") for s, t in self._last_tick.items()},
            "last_updated": {s: t.get("timestamp") for s, t in self._last_tick.items()},
        }


market_stream = MarketStreamService()
