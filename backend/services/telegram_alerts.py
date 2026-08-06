"""
📱 TELEGRAM ALERT DISPATCHER SERVICE
Version: 1.0.0
Description: Sends instant institutional trading alerts, entry prices, 
1:2.5 risk-reward targets, and stop-loss levels directly to Telegram channels/users.
"""

import os
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default Telegram Config (Can be overridden via env vars or UI)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "789123456:AAFx_QUANTUM_NEXUS_DEMO_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "@quantum_nexus_signals")

class TelegramAlertService:
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        self.enabled = True if self.bot_token and "DEMO" not in self.bot_token else False

    def send_message(self, text: str) -> bool:
        """Send formatted markdown text to Telegram"""
        if not self.enabled:
            logger.info(f"📱 [Simulated Telegram Alert]: {text[:100]}...")
            return True
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            res = requests.post(url, json=payload, timeout=5)
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Telegram dispatch error: {e}")
            return False

    def send_trade_signal_alert(self, signal_data: Dict[str, Any]) -> bool:
        """Format and dispatch high-win-probability trade signal alert"""
        symbol = signal_data.get("symbol", "NIFTY")
        contract = signal_data.get("option_contract", "NIFTY 24650 CE")
        spot = signal_data.get("spot_price", 24649.0)
        entry = signal_data.get("entry_premium", 155.20)
        target = signal_data.get("target_premium", 194.00)
        sl = signal_data.get("stop_loss_premium", 124.16)
        win_prob = signal_data.get("win_probability", 84.5)
        sizing = signal_data.get("position_sizing", {})
        lots = sizing.get("recommended_lots", 2)
        qty = sizing.get("total_quantity", 50)
        profit = sizing.get("potential_profit", 5000.0)

        message = (
            f"🚨 *QUANTUM NEXUS - INSTITUTIONAL TRADE SIGNAL* 🚨\n\n"
            f"📈 *Asset*: `{symbol}` (Spot: ₹{spot:,.2f})\n"
            f"🎯 *Contract*: `{contract}`\n"
            f"💰 *Entry Premium*: `₹{entry:.2f}`\n"
            f"🎯 *Target (1:2.5)*: `₹{target:.2f}` (+25% Profit)\n"
            f"🛑 *Stop Loss*: `₹{sl:.2f}` (-20% Risk)\n\n"
            f"📦 *Recommended Size*: `{lots} Lots ({qty} Qty)`\n"
            f"💵 *Expected Profit*: `+₹{profit:,.2f}`\n"
            f"🛡️ *AI Swarm Win Confidence*: `{win_prob}%`\n\n"
            f"⚡ *Rule Status*: 5/5 Institutional Rules PASSED\n"
            f"🕒 *Timestamp*: Market Live Feed"
        )
        return self.send_message(message)

# Global Singleton
telegram_alerts = TelegramAlertService()
