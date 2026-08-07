"""Broker integration routes."""
from typing import Dict, Any

from fastapi import APIRouter, Depends

from services.broker_adapter import broker_adapter
from services.auth_service import get_current_user

router = APIRouter()


@router.get("/api/broker/status")
def get_broker_status(current_user: Dict = Depends(get_current_user)):
    return broker_adapter.get_broker_status()


@router.get("/api/broker/account")
def get_broker_account(current_user: Dict = Depends(get_current_user)):
    return broker_adapter.get_account_snapshot()


@router.post("/api/broker/connect")
def connect_broker(payload: Dict[str, Any] = {}, current_user: Dict = Depends(get_current_user)):
    client_code = payload.get("client_code")
    password = payload.get("password")
    totp = payload.get("totp")
    return broker_adapter.connect_session(client_code, password, totp)


@router.get("/api/broker/options-chain/{symbol}")
def get_broker_options_chain(symbol: str, current_user: Dict = Depends(get_current_user)):
    return {"symbol": symbol, "chain": broker_adapter.get_live_option_chain_ltp(symbol)}
