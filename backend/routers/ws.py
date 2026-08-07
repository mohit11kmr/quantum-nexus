"""WebSocket market feed route."""
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from services.market_stream import market_stream
from services.auth_service import auth_manager, get_user_by_username

router = APIRouter()


@router.websocket("/ws/market")
async def ws_market_feed(websocket: WebSocket, symbol: str = "NIFTY", token: Optional[str] = None):
    """Stream realtime market ticks (real data via fetch_live_quote).

    Optional JWT auth: pass ?token=<access_token> to attach the authenticated
    user. Invalid tokens are rejected with close code 1008; anonymous clients
    still receive the public feed (backward compatible).
    """
    if token:
        try:
            payload = auth_manager.decode_token(token, expected_type="access")
            get_user_by_username(str(payload.get("sub", "")))
        except Exception:
            await websocket.close(code=1008)
            return
    await websocket.accept()
    queue = market_stream.subscribe(symbol)
    try:
        while True:
            tick = await queue.get()
            await websocket.send_json(tick)
    except WebSocketDisconnect:
        pass
    finally:
        market_stream.unsubscribe(symbol, queue)
