"""
Ultra-Precision Multi-Source Signal Generator Engine v3.0
Fixes 7 critical glitches:
1. Dynamic Weighted Scoring (Volume 30%, VWAP 25%, AI 20%, Greeks 15%, Indicators 10%)
2. Multi-Timeframe (MTF) Trend Alignment Guard
3. Implied Volatility (IV Crush) Protection
4. Theta Decay Expiry Guard (DTE Safety)
5. Choppy Market (ADX < 18) Sideways Whipsaw Filter
6. Real OHLCV & Technical Indicator Binding
7. Precise Non-Conflicting Threshold Routing
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

class UltraSignalGenerator:
    def __init__(self):
        pass

    def generate_signal(self, df: pd.DataFrame, ai_confidence: float = 75.0, 
                        option_greeks: Dict[str, Any] = None, 
                        mtf_trend: str = "BULLISH") -> Dict[str, Any]:
        """
        Generates production-grade precision trading signals by fusing
        Technical OHLCV indicators, Multi-Timeframe Alignment, Options Greeks, and AI Brain.
        """
        if df.empty or len(df) < 20:
            return {"signal": "NEUTRAL", "confidence": 0.0, "reason": "Insufficient market candles"}

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        close = float(latest.get("Close", 0.0))
        vwap = float(latest.get("VWAP", close))
        vol_surge = float(latest.get("Vol_Surge_Ratio", 1.0))
        rsi = float(latest.get("RSI", 50.0))
        adx = float(latest.get("ADX", 20.0))
        cmf = float(latest.get("CMF", 0.0))
        atr = float(latest.get("ATR", 10.0))

        # --- 1. CHOPPINESS & NO-TRADE ZONE FILTER ---
        if adx < 18.0:
            return {
                "signal": "NO_TRADE_ZONE",
                "confidence": 35.0,
                "reason": f"Market is Choppy/Sideways (ADX {round(adx, 1)} < 18.0). High whipsaw risk.",
                "quality": "REJECT"
            }

        # --- 2. THETA DECAY & EXPIRY GUARD ---
        greeks = option_greeks or {}
        dte_days = float(greeks.get("dte_days", 5.0))
        theta = float(greeks.get("theta", -10.0))
        iv_rank = float(greeks.get("iv_rank_pct", 45.0))
        delta = float(greeks.get("delta", 0.50))

        if dte_days < 0.25: # Less than 6 hours to expiry
            return {
                "signal": "EXPIRY_THETA_BLOCK",
                "confidence": 20.0,
                "reason": "Option Expiry Theta Bleed Hazard (<6 hours to expiry). Option buying blocked.",
                "quality": "REJECT"
            }

        # --- 3. IV CRUSH PROTECTION ---
        if iv_rank > 85.0:
            return {
                "signal": "IV_CRUSH_WARNING",
                "confidence": 40.0,
                "reason": f"Extreme IV Rank ({round(iv_rank, 1)}% > 85%). Option buying blocked due to IV collapse risk.",
                "quality": "CAUTION"
            }

        # --- 4. WEIGHTED MULTI-LAYER SCORING ---
        # A) Volume & Accumulation Layer (Weight: 30%)
        vol_score = 100.0 if vol_surge >= 3.0 else 80.0 if vol_surge >= 2.0 else 60.0 if vol_surge >= 1.5 else 40.0
        if cmf > 0.15: vol_score = min(100.0, vol_score + 15.0)
        elif cmf < -0.15: vol_score = max(0.0, vol_score - 15.0)

        # B) Price & VWAP Trend Layer (Weight: 25%)
        vwap_score = 90.0 if close > vwap else 20.0
        if prev.get("Close", close) <= prev.get("VWAP", vwap) and close > vwap:
            vwap_score = 100.0 # Bullish VWAP Crossover

        # C) AI Brain & ML Layer (Weight: 20%)
        ai_score = float(np.clip(ai_confidence, 0.0, 100.0))

        # D) Options Greeks Layer (Weight: 15%)
        greeks_score = 80.0 if (0.35 <= abs(delta) <= 0.65) else 40.0
        if abs(theta) > 25.0: greeks_score -= 20.0

        # E) Technical Oscillator Layer (Weight: 10%)
        tech_score = 85.0 if (50 <= rsi <= 68 and adx > 22) else 50.0

        # Fused Weighted Confidence Score
        total_confidence = round(
            (vol_score * 0.30) +
            (vwap_score * 0.25) +
            (ai_score * 0.20) +
            (greeks_score * 0.15) +
            (tech_score * 0.10),
            1
        )

        # --- 5. MULTI-TIMEFRAME (MTF) ALIGNMENT GUARD ---
        if mtf_trend == "BEARISH" and total_confidence > 60:
            total_confidence -= 15.0 # Penalty for trading against 1H higher timeframe trend

        # --- 6. PRECISION SIGNAL DETERMINATION ---
        if total_confidence >= 80.0:
            signal = "STRONG_BUY"
            quality = "A+"
        elif total_confidence >= 68.0:
            signal = "BUY"
            quality = "A"
        elif total_confidence >= 55.0:
            signal = "WEAK_BUY"
            quality = "B"
        elif total_confidence <= 35.0:
            signal = "STRONG_SELL"
            quality = "A+"
        elif total_confidence <= 45.0:
            signal = "SELL"
            quality = "B"
        else:
            signal = "NEUTRAL"
            quality = "C"

        # Risk-Reward levels calculation
        sl_distance = max(atr * 1.5, close * 0.008)
        target_distance = sl_distance * 2.0 # 1:2 Risk Reward Ratio

        return {
            "signal": signal,
            "confidence": total_confidence,
            "quality": quality,
            "entry_price": round(close, 2),
            "target_price": round(close + target_distance if "BUY" in signal else close - target_distance, 2),
            "stop_loss": round(close - sl_distance if "BUY" in signal else close + sl_distance, 2),
            "risk_reward_ratio": "1:2.0",
            "scores_breakdown": {
                "volume_layer": round(vol_score, 1),
                "vwap_layer": round(vwap_score, 1),
                "ai_brain_layer": round(ai_score, 1),
                "options_greeks_layer": round(greeks_score, 1),
                "technical_layer": round(tech_score, 1)
            },
            "guards_passed": {
                "adx_choppiness": True,
                "theta_expiry": True,
                "iv_crush_check": True,
                "mtf_alignment": mtf_trend
            }
        }

# Global Generator Instance
signal_generator = UltraSignalGenerator()
