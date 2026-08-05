from typing import List, Dict, Any

class StrikeSelector:
    def __init__(self):
        pass
        
    def select_best_strikes(self, spot_price: float, strikes_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Smart strike selector scoring by moneyness (ATM/ITM preference),
        Delta sweet spot (0.30-0.55), OI liquidity.
        """
        scored_strikes = []
        for strike in strikes_data:
            score = 0.0
            
            # Delta sweet spot
            delta = abs(strike.get("delta", 0))
            if 0.30 <= delta <= 0.55:
                score += 40
            elif 0.20 <= delta < 0.30 or 0.55 < delta <= 0.65:
                score += 20
                
            # Moneyness preference (assuming slight ITM or ATM is better)
            distance = abs(strike.get("strike", spot_price) - spot_price) / spot_price
            if distance < 0.02:
                score += 30
            elif distance < 0.05:
                score += 10
                
            # OI Liquidity
            oi = strike.get("open_interest", 0)
            if oi > 100000:
                score += 30
            elif oi > 50000:
                score += 15
                
            strike["score"] = score
            scored_strikes.append(strike)
            
        scored_strikes.sort(key=lambda x: x["score"], reverse=True)
        return scored_strikes
