from typing import Dict, Any, List

class RiskEngine:
    def __init__(self, initial_capital: float = 100000.0):
        self.capital = initial_capital
        self.max_risk_per_trade = 0.02
        self.max_daily_drawdown = 0.03
        self.current_daily_drawdown = 0.0
        
    def evaluate_trade_risk(self, entry_price: float, stop_loss: float) -> Dict[str, Any]:
        if self.current_daily_drawdown >= self.max_daily_drawdown:
            return {"approved": False, "reason": "Daily drawdown limit reached (Kill Switch)."}
            
        risk_amount = self.capital * self.max_risk_per_trade
        risk_per_share = entry_price - stop_loss
        
        if risk_per_share <= 0:
            return {"approved": False, "reason": "Invalid stop loss."}
            
        position_size = int(risk_amount / risk_per_share)
        
        return {
            "approved": True,
            "position_size": position_size,
            "risk_amount": risk_amount,
            "capital": self.capital
        }

class PaperTradingSimulator:
    def __init__(self, initial_capital: float = 100000.0):
        self.capital = initial_capital
        self.portfolio = []
        self.history = []
        
    def get_portfolio(self) -> Dict[str, Any]:
        return {
            "capital": self.capital,
            "positions": self.portfolio,
            "history": self.history
        }
        
    def execute_buy(self, symbol: str, price: float, quantity: int) -> bool:
        cost = price * quantity
        if cost > self.capital:
            return False
        self.capital -= cost
        self.portfolio.append({"id": len(self.history)+1, "symbol": symbol, "price": price, "quantity": quantity})
        return True

    def execute_close(self, trade_id: int, current_price: float) -> bool:
        for p in self.portfolio:
            if p["id"] == trade_id:
                revenue = current_price * p["quantity"]
                self.capital += revenue
                p["exit_price"] = current_price
                p["pnl"] = revenue - (p["price"] * p["quantity"])
                self.history.append(p)
                self.portfolio.remove(p)
                return True
        return False
