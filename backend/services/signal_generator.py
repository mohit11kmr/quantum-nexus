from typing import Dict, Any

class SignalGenerator:
    def __init__(self):
        pass
        
    def generate_signal(self, ml_score: float, tech_score: float, sentiment_score: float) -> Dict[str, Any]:
        """
        Multi-source signal fusion.
        Weights: ML (40%), Technical (35%), Sentiment (25%)
        """
        combined = (ml_score * 0.40) + (tech_score * 0.35) + (sentiment_score * 0.25)
        
        if combined > 70:
            signal = "STRONG_BUY"
        elif combined > 55:
            signal = "BUY"
        elif combined < 30:
            signal = "STRONG_SELL"
        elif combined < 45:
            signal = "SELL"
        else:
            signal = "NEUTRAL"
            
        return {
            "signal": signal,
            "confidence": combined,
            "breakdown": {
                "ml": ml_score,
                "technical": tech_score,
                "sentiment": sentiment_score
            }
        }
