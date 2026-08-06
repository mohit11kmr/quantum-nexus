"""
AngelOne SmartAPI Broker Adapter & Live Feed Connector v2.0

Adopted & hardened from trading_bot's AngelOne adapter:
  - REAL authentication via SmartConnect + TOTP (pyotp)
  - REAL order placement / status / positions / holdings / funds / profile / LTP
  - Rate-limit retry decorator (AngelOne allows ~3 requests/second)
  - Real option-chain LTP via searchScrip + ltpData, greeks via BlackScholes
  - PAPER-TRADING SAFE BY DEFAULT:
      * PAPER_TRADING_ENABLED defaults to "true"
      * No credentials configured  -> Paper mode
      * SmartApi/pyotp not installed -> Paper mode (lazy imports)
    Live orders are ONLY placed when the flag is false AND a real session exists.

Public interface preserved for backward compatibility:
  connect_session(), get_live_option_chain_ltp(), place_live_order(),
  get_broker_status()
"""

import os
import re
import json
import time
import functools
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger("quantum_nexus.broker_adapter")


def retry_on_rate_limit(max_retries: int = 3, delay: float = 1.5):
    """Decorator to retry AngelOne API calls when rate limited (~3 req/sec)."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    time.sleep(0.5)
                    result = func(*args, **kwargs)
                    if isinstance(result, dict) and not result.get("status"):
                        msg = str(result.get("message", "")).lower()
                        if "access rate" in msg or "too many" in msg:
                            retries += 1
                            time.sleep(delay * retries)
                            continue
                    return result
                except Exception as e:
                    if "access rate" in str(e).lower():
                        retries += 1
                        time.sleep(delay * retries)
                        continue
                    raise e
            return func(*args, **kwargs)
        return wrapper
    return decorator


class SmartAPIBrokerAdapter:
    def __init__(self):
        self.api_key = os.getenv("ANGEL_API_KEY", "") or os.getenv("ANGEL_SECRET_KEY", "")
        self.client_code = os.getenv("ANGEL_CLIENT_ID", "") or os.getenv("ANGEL_CLIENT_CODE", "")
        self.password = os.getenv("ANGEL_PASSWORD", "")
        self.totp_secret = os.getenv("ANGEL_TOTP_SEED", "") or os.getenv("ANGEL_TOTP_SECRET", "")

        self.is_connected = False
        self.session_data: Dict[str, Any] = {}
        self.smart_api = None
        self.paper_trading_mode = os.getenv("PAPER_TRADING_ENABLED", "true").lower() == "true"
        self.live_data: Dict[str, float] = {}
        self.last_ticks: Dict[str, Any] = {}
        self.last_known_prices: Dict[str, float] = {}

    # ── Optional dependency guards ──────────────────────────
    def _smart_connect(self):
        try:
            from SmartApi import SmartConnect
            return SmartConnect
        except ImportError:
            return None

    def _totp_generator(self):
        try:
            import pyotp
            return pyotp
        except ImportError:
            return None

    def _is_live_executable(self) -> bool:
        return (not self.paper_trading_mode) and self.is_connected and self.smart_api is not None

    def _paper_response(self, message: str) -> Dict[str, Any]:
        return {
            "status": True,
            "mode": "PAPER_TRADING",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

    # ── Authentication ──────────────────────────────────────
    def connect_session(self, client_code: str = None, password: str = None, totp: str = None) -> Dict[str, Any]:
        """
        Authenticate a real AngelOne SmartAPI session using TOTP.
        Falls back to Paper Trading when credentials or packages are missing.
        """
        c_code = (client_code or self.client_code).strip()
        pwd = password or self.password

        if not c_code or not pwd or not self.api_key:
            logger.info("No AngelOne credentials configured. Running in Paper Trading Mode.")
            self.is_connected = False
            return self._paper_response(
                "Connected in Virtual Paper Trading Mode (No live broker credentials provided)")

        SmartConnect = self._smart_connect()
        if not SmartConnect:
            self.is_connected = False
            return self._paper_response(
                "SmartApi package not installed. Install 'smartapi-python' for live broker mode.")

        try:
            if not totp:
                pyotp = self._totp_generator()
                if not pyotp or not self.totp_secret:
                    return {"status": False, "error": "pyotp and ANGEL_TOTP_SEED required for TOTP login",
                            "mode": "PAPER_TRADING"}
                totp = pyotp.TOTP(self.totp_secret).now()

            client = SmartConnect(api_key=self.api_key)
            data = client.generateSession(c_code, pwd, totp)

            if not data.get("status"):
                raise RuntimeError(data.get("message", "Authentication failed"))

            self.smart_api = client
            self.is_connected = True
            token_data = data.get("data", {}) or {}
            self.session_data = {
                "client_code": c_code,
                "jwt_token": token_data.get("jwtToken", ""),
                "refresh_token": token_data.get("refreshToken", ""),
                "feed_token": token_data.get("feedToken", ""),
                "connected_at": datetime.now().isoformat()
            }
            return {
                "status": True,
                "mode": "LIVE_BROKER" if not self.paper_trading_mode else "PAPER_TRADING",
                "session": self.session_data,
                "message": "Authenticated with AngelOne SmartAPI"
            }
        except Exception as e:
            logger.error(f"AngelOne authentication failed: {e}")
            self.is_connected = False
            return {"status": False, "error": str(e), "mode": "PAPER_TRADING"}

    # ── LTP / Market Data ───────────────────────────────────
    @retry_on_rate_limit()
    def get_ltp(self, exchange: str, symbol: str, token: str) -> float:
        """Real last traded price. Checks live tick cache first, then API."""
        if token in self.live_data:
            return self.live_data[token]
        if not self.smart_api:
            return self.last_known_prices.get(symbol, 0.0)
        try:
            data = self.smart_api.ltpData(exchange, symbol, str(token))
            if data.get("status"):
                ltp = float(data["data"]["ltp"])
                self.last_known_prices[symbol] = ltp
                return ltp
        except Exception as e:
            logger.warning(f"LTP fetch failed for {symbol} ({token}): {e}")
        return self.last_known_prices.get(symbol, 0.0)

    def _index_token(self, symbol: str) -> str:
        tokens = {"NIFTY": "99926000", "BANKNIFTY": "99926009", "FINNIFTY": "99926037"}
        return tokens.get(symbol.upper(), "99926000")

    # ── Option Chain ────────────────────────────────────────
    def get_live_option_chain_ltp(self, symbol: str, expiry: str = None) -> List[Dict[str, Any]]:
        """
        Real option chain LTP around the ATM strike (searchScrip + ltpData).
        Falls back to a clearly-labelled synthetic chain when disconnected.
        """
        if not self._is_live_executable():
            return self._synthetic_option_chain(symbol)
        try:
            chain = self._fetch_real_option_chain(symbol, expiry)
            if chain:
                return chain
        except Exception as e:
            logger.warning(f"Real option chain unavailable, using synthetic: {e}")
        return self._synthetic_option_chain(symbol)

    def _normalize_expiry(self, expiry: str) -> str:
        if "-" in expiry:
            try:
                return datetime.strptime(expiry, "%Y-%m-%d").strftime("%d%b%y").upper()
            except ValueError:
                pass
        return expiry.upper()

    def _fetch_real_option_chain(self, symbol: str, expiry: str = None) -> List[Dict[str, Any]]:
        idx = symbol.upper()
        search = self.smart_api.searchScrip("NFO", idx)
        if not (search and search.get("status") and search.get("data")):
            return []

        pattern = re.compile(rf"^{idx}(\d{{2}}[A-Z]{{3}}\d{{2}})(\d+)(CE|PE)$")
        expiries = set()
        parsed = []
        for item in search["data"]:
            m = pattern.match(str(item.get("tradingsymbol", "")))
            if m:
                exp, strike, otype = m.groups()
                expiries.add(exp)
                parsed.append({
                    "symbol": item["tradingsymbol"],
                    "token": item["symboltoken"],
                    "expiry": exp,
                    "strike": float(strike),
                    "type": otype,
                })
        if not parsed:
            return []

        if expiry:
            target_exp = self._normalize_expiry(expiry)
            if target_exp not in expiries:
                target_exp = None
        if not expiry or not target_exp:
            def parse_exp(e):
                try:
                    return datetime.strptime(e, "%d%b%y")
                except Exception:
                    return datetime(2099, 1, 1)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            future = sorted((e for e in expiries if parse_exp(e) >= today), key=parse_exp)
            target_exp = future[0] if future else sorted(expiries, key=parse_exp)[0]

        spot = self.get_ltp("NSE", idx, self._index_token(idx))
        if spot <= 0:
            return []
        step = 50 if "NIFTY" in idx else 100
        atm = round(spot / step) * step
        relevant = [p for p in parsed if p["expiry"] == target_exp and abs(p["strike"] - atm) <= 5 * step]

        from services.options_engine import BlackScholesEngine
        bs = BlackScholesEngine()
        t_opt = 5.0 / 365.0
        sigma = 0.15

        results = []
        for p in sorted(relevant, key=lambda x: (x["strike"], x["type"])):
            ltp = self.get_ltp("NFO", p["symbol"], p["token"])
            g = bs.calculate_greeks(S=spot, K=p["strike"], T=t_opt, sigma=sigma, option_type=p["type"])
            results.append({
                "strike_price": p["strike"],
                "option_type": p["type"],
                "expiry": target_exp,
                "ltp": round(ltp, 2),
                "bid": round(ltp * 0.99, 2),
                "ask": round(ltp * 1.01, 2),
                "volume": 0,
                "open_interest": 0,
                "iv": round(sigma * 100, 2),
                "delta": g["delta"],
                "theta": g["theta"],
                "data_source": "REAL_LTP",
            })
        return results

    def _synthetic_option_chain(self, symbol: str) -> List[Dict[str, Any]]:
        """Clearly-labelled synthetic chain used only in paper/offline mode."""
        base_price = 24500.0 if "NIFTY" in symbol.upper() else 52000.0 if "BANK" in symbol.upper() else 1500.0
        strikes = []
        for offset in range(-5, 6):
            strike = round(base_price + (offset * 100 if base_price > 10000 else offset * 50), 2)
            ce_ltp = max(5.0, round(180.0 - (offset * 25.0) + (offset ** 2 * 0.5), 2))
            pe_ltp = max(5.0, round(180.0 + (offset * 25.0) + (offset ** 2 * 0.5), 2))
            strikes.append({
                "strike_price": strike, "option_type": "CE", "ltp": ce_ltp,
                "bid": round(ce_ltp - 0.5, 2), "ask": round(ce_ltp + 0.5, 2),
                "volume": 125000 + abs(offset) * 15000,
                "open_interest": 450000 + (10 - abs(offset)) * 30000,
                "iv": round(15.2 + abs(offset) * 0.4, 2),
                "delta": round(0.50 - (offset * 0.05), 2),
                "theta": -12.4,
                "data_source": "SYNTHETIC",
            })
            strikes.append({
                "strike_price": strike, "option_type": "PE", "ltp": pe_ltp,
                "bid": round(pe_ltp - 0.5, 2), "ask": round(pe_ltp + 0.5, 2),
                "volume": 110000 + abs(offset) * 12000,
                "open_interest": 420000 + (10 - abs(offset)) * 25000,
                "iv": round(16.1 + abs(offset) * 0.4, 2),
                "delta": round(-0.50 - (offset * 0.05), 2),
                "theta": -11.8,
                "data_source": "SYNTHETIC",
            })
        return strikes

    # ── Order Execution ─────────────────────────────────────
    def place_live_order(self, symbol: str, qty: int, side: str, order_type: str = "MARKET",
                         price: float = 0.0, token: str = None, exchange: str = "NSE",
                         product_type: str = "CARRYFORWARD", trigger_price: float = 0.0,
                         variety: str = "NORMAL") -> Dict[str, Any]:
        """
        Place a broker order. In paper mode (default) returns a simulated fill.
        Live orders are only routed when PAPER_TRADING_ENABLED=false + real session.
        """
        if not self._is_live_executable():
            exec_price = price if price and price > 0 else self.last_known_prices.get(symbol, 100.0)
            return {
                "status": "SUCCESS",
                "order_id": f"PAPER_{int(time.time())}",
                "mode": "PAPER_TRADING",
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "executed_price": round(float(exec_price), 2),
                "message": "Order executed in Virtual Paper Trading environment"
            }

        try:
            params = {
                "variety": variety,
                "tradingsymbol": symbol,
                "symboltoken": str(token or ""),
                "transactiontype": side.upper(),
                "exchange": exchange,
                "ordertype": order_type.upper(),
                "producttype": product_type.upper(),
                "duration": "DAY",
                "quantity": str(int(qty)),
            }
            if order_type.upper() in ("LIMIT", "SL", "SL-M") and price and price > 0:
                params["price"] = str(price)
            if order_type.upper() in ("SL", "SL-M") and trigger_price > 0:
                params["triggerprice"] = str(trigger_price)

            res = self.smart_api.placeOrder(params)
            if res.get("status"):
                return {
                    "status": "SUCCESS",
                    "order_id": (res.get("data", {}) or {}).get("orderid"),
                    "mode": "LIVE_BROKER",
                    "symbol": symbol,
                    "qty": qty,
                    "side": side,
                    "response": res,
                }
            return {"status": "FAILED", "error": res.get("message"), "mode": "LIVE_BROKER", "response": res}
        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return {"status": "FAILED", "error": str(e), "mode": "LIVE_BROKER"}

    @retry_on_rate_limit()
    def cancel_order(self, order_id: str, variety: str = "NORMAL") -> Dict[str, Any]:
        if not self.smart_api:
            return {"status": False, "message": "Not authenticated"}
        try:
            return self.smart_api.cancelOrder({"variety": variety, "orderid": order_id})
        except Exception as e:
            return {"status": False, "message": str(e)}

    @retry_on_rate_limit()
    def modify_order(self, order_id: str, quantity: int = None, price: float = None,
                     trigger_price: float = None, order_type: str = None,
                     variety: str = "NORMAL") -> Dict[str, Any]:
        if not self.smart_api:
            return {"status": False, "message": "Not authenticated"}
        try:
            params = {"variety": variety, "orderid": order_id}
            if quantity is not None:
                params["quantity"] = str(quantity)
            if price is not None:
                params["price"] = str(price)
            if trigger_price is not None:
                params["triggerprice"] = str(trigger_price)
            if order_type is not None:
                params["ordertype"] = order_type.upper()
            return self.smart_api.modifyOrder(params)
        except Exception as e:
            return {"status": False, "message": str(e)}

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        if not self.smart_api:
            return {"status": "PENDING", "message": "Not authenticated"}
        book = self.get_order_book()
        if isinstance(book, dict) and book.get("status"):
            for order in book.get("data", []):
                if str(order.get("orderid")) == str(order_id):
                    return {"status": order.get("status"), "message": "Success"}
        return {"status": "PENDING", "message": "Order not found or pending"}

    # ── Account / Portfolio ─────────────────────────────────
    @retry_on_rate_limit()
    def get_order_book(self) -> Dict[str, Any]:
        if not self.smart_api:
            return {"status": False, "message": "Not authenticated"}
        try:
            return self.smart_api.orderBook()
        except Exception as e:
            return {"status": False, "message": str(e)}

    @retry_on_rate_limit()
    def get_positions(self) -> Dict[str, Any]:
        if not self.smart_api:
            return {"status": False, "message": "Not authenticated"}
        try:
            return self.smart_api.position()
        except Exception as e:
            return {"status": False, "message": str(e)}

    @retry_on_rate_limit()
    def get_holdings(self) -> Dict[str, Any]:
        if not self.smart_api:
            return {"status": False, "message": "Not authenticated"}
        try:
            return self.smart_api.holding("DELIVERY")
        except Exception as e:
            return {"status": False, "message": str(e)}

    @retry_on_rate_limit()
    def get_funds(self) -> Dict[str, Any]:
        if not self.smart_api:
            return {"status": False, "message": "Not authenticated"}
        try:
            return self.smart_api.rmsLimit()
        except Exception as e:
            return {"status": False, "message": str(e)}

    @retry_on_rate_limit()
    def get_profile(self) -> Dict[str, Any]:
        if not self.smart_api:
            return {"status": False, "message": "Not authenticated"}
        try:
            return self.smart_api.getProfile(self.smart_api.refreshToken)
        except Exception as e:
            return {"status": False, "message": str(e)}

    # ── Status ──────────────────────────────────────────────
    def get_broker_status(self) -> Dict[str, Any]:
        return {
            "is_connected": self.is_connected,
            "paper_trading_enabled": self.paper_trading_mode,
            "broker": "AngelOne SmartAPI",
            "protocol": "REST API (SmartConnect) + WebSocket-ready",
            "active_client_code": self.client_code or "DEMO_USER",
            "session_active": self.is_connected,
            "mode": "LIVE_BROKER" if self._is_live_executable() else "PAPER_TRADING",
            "libraries_available": {
                "smartapi": self._smart_connect() is not None,
                "pyotp": self._totp_generator() is not None,
            },
        }

    def get_account_snapshot(self) -> Dict[str, Any]:
        """Aggregated account summary (real when live, empty otherwise)."""
        if not self._is_live_executable():
            return {
                "mode": "PAPER_TRADING",
                "funds": {},
                "positions": [],
                "holdings": [],
                "order_book": [],
                "message": "Connect a live broker session to fetch real account data",
            }
        funds = self.get_funds().get("data", {}) if self.get_funds().get("status") else {}
        positions = self.get_positions().get("data", []) if self.get_positions().get("status") else []
        holdings = self.get_holdings().get("data", []) if self.get_holdings().get("status") else []
        order_book = self.get_order_book().get("data", []) if self.get_order_book().get("status") else []
        return {
            "mode": "LIVE_BROKER",
            "funds": funds,
            "positions": positions,
            "holdings": holdings,
            "order_book": order_book,
        }


# Global Broker Adapter Instance
broker_adapter = SmartAPIBrokerAdapter()
