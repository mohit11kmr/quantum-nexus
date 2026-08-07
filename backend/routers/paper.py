"""Paper trading routes (guest fallback via get_current_user)."""
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from services.paper_portfolio import paper_portfolio
from services.stock_data import fetch_live_quote
from services.auth_service import get_current_user

router = APIRouter()


class BuyRequest(BaseModel):
    symbol: str
    price: float
    quantity: int


class PaperSizedBuyRequest(BaseModel):
    symbol: str = "RELIANCE.NS"
    stopLossPct: float = 2.0
    takeProfitPct: float = 6.0


@router.get("/api/paper-trading/portfolio")
@router.get("/api/paper/portfolio")
def get_portfolio(current_user: Dict = Depends(get_current_user)):
    return paper_portfolio.get_portfolio(current_user.get("username"))


@router.post("/api/paper-trading/buy")
@router.post("/api/paper/buy")
def paper_buy(req: BuyRequest, current_user: Dict = Depends(get_current_user)):
    success = paper_portfolio.execute_buy(req.symbol, req.price, req.quantity, current_user.get("username"))
    if not success:
        raise HTTPException(status_code=400, detail="Insufficient capital")
    return {"message": "Buy executed"}


@router.post("/api/paper/smart-buy")
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


@router.post("/api/paper-trading/close/{trade_id}")
@router.post("/api/paper/close/{trade_id}")
def paper_close(trade_id: int, current_price: float = 0.0, current_user: Dict = Depends(get_current_user)):
    success = paper_portfolio.execute_close(trade_id, current_price, current_user.get("username"))
    if not success:
        raise HTTPException(status_code=404, detail="Trade not found")
    return {"message": "Trade closed"}


@router.post("/api/paper-trading/reset")
@router.post("/api/paper/reset")
def paper_reset(current_user: Dict = Depends(get_current_user)):
    paper_portfolio.reset(current_user.get("username"))
    return {"message": "Portfolio reset"}
