"""
Paper Portfolio - single source of truth for paper (simulated) trading state.

Wraps PaperTradingManager so:
  * the LangGraph execution node shares the "default" simulated portfolio, and
  * authenticated REST /api/paper/* routes get isolated per-user portfolios,
    each persisted to its own JSON state file (survives server restarts).

Always paper-safe.
"""

import time
from typing import Dict, Any

from services.risk_engine import PaperTradingManager, PaperTradingSimulator


class PaperPortfolio:
    def __init__(self, initial_capital: float = 100000.0):
        self._manager = PaperTradingManager(initial_capital=initial_capital)

    def get_sim(self, user_id: str = None) -> PaperTradingSimulator:
        return self._manager.get(user_id)

    def get_portfolio(self, user_id: str = None) -> Dict[str, Any]:
        return self.get_sim(user_id).get_portfolio()

    def execute_buy(self, symbol: str, price: float, quantity: int, user_id: str = None) -> bool:
        return self.get_sim(user_id).execute_buy(symbol, price, quantity)

    def execute_close(self, trade_id: int, current_price: float = 0.0, user_id: str = None) -> bool:
        return self.get_sim(user_id).execute_close(trade_id, current_price)

    def reset(self, user_id: str = None) -> None:
        self.get_sim(user_id).reset_portfolio()

    def place_order(self, symbol: str, price: float, qty: int, side: str = "buy",
                    user_id: str = None) -> Dict[str, Any]:
        """Buy opens a position; sell closes an existing one. Paper only."""
        sim = self.get_sim(user_id)
        side = side.lower()
        if side == "buy":
            ok = sim.execute_buy(symbol, price, qty)
            return {
                "status": "SUCCESS" if ok else "REJECTED",
                "order_id": f"PAPER_{int(time.time())}",
                "mode": "PAPER_TRADING",
                "symbol": symbol,
                "side": "BUY",
                "quantity": qty,
                "price": price,
                "message": "Buy executed (paper)" if ok else "Insufficient capital (paper)",
            }
        if side == "sell":
            for p in sim.open_positions:
                if p["symbol"].upper() == symbol.upper():
                    ok = sim.close_position(p["id"], price)["success"]
                    return {
                        "status": "SUCCESS" if ok else "REJECTED",
                        "order_id": f"PAPER_{int(time.time())}",
                        "mode": "PAPER_TRADING",
                        "symbol": symbol,
                        "side": "SELL",
                        "quantity": p["shares"],
                        "price": price,
                        "message": "Position closed (paper)" if ok else "Close failed (paper)",
                    }
            return {
                "status": "SKIPPED",
                "order_id": f"PAPER_{int(time.time())}",
                "mode": "PAPER_TRADING",
                "symbol": symbol,
                "side": "SELL",
                "quantity": 0,
                "price": price,
                "message": "No open position to sell (paper)",
            }
        return {"status": "REJECTED", "message": f"Unsupported side: {side}"}


paper_portfolio = PaperPortfolio()
