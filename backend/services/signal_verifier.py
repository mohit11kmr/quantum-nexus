from typing import Dict, Any

class SignalVerifier:
    def __init__(self):
        pass
        
    def verify_signal(self, technical_data: Dict[str, Any], greeks_data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        3-layer cross-verification: Technical + Greeks + Market Data.
        Returns confidence score and rating (EXCELLENT/GOOD/CAUTION/REJECT).
        """
        score = 0
        
        # Tech layer
        if technical_data.get('rsi', 50) > 60: score += 10
        if technical_data.get('macd_bullish', False): score += 15
        
        # Greeks layer
        if 0.3 < greeks_data.get('delta', 0) < 0.6: score += 20
        if greeks_data.get('theta', 0) > -5: score += 15
        
        # Market data layer
        if market_data.get('volume_surge', False): score += 20
        if market_data.get('trend_up', False): score += 20
        
        if score >= 80:
            rating = "EXCELLENT"
        elif score >= 60:
            rating = "GOOD"
        elif score >= 40:
            rating = "CAUTION"
        else:
            rating = "REJECT"
            
        return {
            "verified_score": score,
            "rating": rating,
            "layers_passed": sum([1 for x in [technical_data, greeks_data, market_data] if x])
        }
