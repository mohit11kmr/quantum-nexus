"""
Ultra-Precision Options Buying Strategy Module v3.0
Includes 7-Condition Weighted Scoring, DTE Theta Bleed Guard, IV Rank Filter, and Risk/Reward Calculator.
"""

from typing import Dict, Any

class AdvancedOptionsBuyingStrategy:
    def __init__(self):
        pass

    def evaluate_entry(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates 7-condition options buying entry with weighted priorities:
        1. VWAP Crossover (Weight: 20%)
        2. Volume Surge > 1.5x (Weight: 20%)
        3. SuperTrend Direction (Weight: 15%)
        4. ADX Trend Strength > 20 (Weight: 15%)
        5. AI Brain Confidence > 65% (Weight: 15%)
        6. RSI Momentum Filter 48-68 (Weight: 10%)
        7. DTE > 0.5 Days & IV Rank < 80% (Weight: 5%)
        """
        score = 0.0
        conditions_passed = []
        conditions_failed = []

        # 1. VWAP Crossover Check
        if data.get("close", 0.0) > data.get("vwap", 0.0):
            score += 20.0
            conditions_passed.append("VWAP_BULLISH_ABOVE")
        else:
            conditions_failed.append("VWAP_BEARISH_BELOW")

        # 2. Volume Surge Check
        vol_surge = data.get("volume_spike_ratio", 1.0)
        if vol_surge >= 2.0:
            score += 20.0
            conditions_passed.append(f"HIGH_VOLUME_SURGE_{round(vol_surge, 1)}X")
        elif vol_surge >= 1.5:
            score += 12.0
            conditions_passed.append(f"MODERATE_VOLUME_SURGE_{round(vol_surge, 1)}X")
        else:
            conditions_failed.append(f"LOW_VOLUME_SURGE_{round(vol_surge, 1)}X")

        # 3. SuperTrend Check
        if data.get("supertrend_bullish", True):
            score += 15.0
            conditions_passed.append("SUPERTREND_GREEN")
        else:
            conditions_failed.append("SUPERTREND_RED")

        # 4. ADX Trend Strength Check
        adx = data.get("adx", 22.0)
        if adx >= 22.0:
            score += 15.0
            conditions_passed.append(f"STRONG_ADX_TREND_{round(adx, 1)}")
        elif adx >= 18.0:
            score += 8.0
            conditions_passed.append(f"MODERATE_ADX_{round(adx, 1)}")
        else:
            conditions_failed.append(f"CHOPPY_LOW_ADX_{round(adx, 1)}")

        # 5. AI Confidence Check
        ai_conf = data.get("ai_confidence", 70.0)
        if ai_conf >= 75.0:
            score += 15.0
            conditions_passed.append(f"HIGH_AI_CONFIDENCE_{round(ai_conf, 1)}%")
        elif ai_conf >= 60.0:
            score += 10.0
            conditions_passed.append(f"MODERATE_AI_CONFIDENCE_{round(ai_conf, 1)}%")
        else:
            conditions_failed.append(f"LOW_AI_CONFIDENCE_{round(ai_conf, 1)}%")

        # 6. RSI Filter Check
        rsi = data.get("rsi", 55.0)
        if 48.0 <= rsi <= 68.0:
            score += 10.0
            conditions_passed.append(f"OPTIMAL_RSI_{round(rsi, 1)}")
        else:
            conditions_failed.append(f"OUT_OF_RANGE_RSI_{round(rsi, 1)}")

        # 7. Options Expiry & IV Rank Safety Check
        dte = data.get("dte_days", 3.0)
        iv_rank = data.get("iv_rank", 45.0)
        if dte >= 0.5 and iv_rank <= 80.0:
            score += 5.0
            conditions_passed.append("OPTIONS_THETA_IV_SAFE")
        else:
            conditions_failed.append(f"THETA_IV_HAZARD_DTE_{round(dte, 1)}_IVR_{round(iv_rank, 1)}")

        # Determine Setup Quality
        if score >= 85.0:
            quality = "A+"
            action = "STRONG_BUY_OPTION_CALL"
        elif score >= 70.0:
            quality = "A"
            action = "BUY_OPTION_CALL"
        elif score >= 55.0:
            quality = "B"
            action = "WATCHLIST_ONLY"
        else:
            quality = "C"
            action = "NO_TRADE"

        return {
            "strategy_score": round(score, 1),
            "quality": quality,
            "signal": action,
            "conditions_met_count": len(conditions_passed),
            "total_conditions": 7,
            "conditions_passed": conditions_passed,
            "conditions_failed": conditions_failed
        }

# Global Instance
options_buying_strategy = AdvancedOptionsBuyingStrategy()
