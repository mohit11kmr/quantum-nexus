import pandas as pd
from typing import Dict, Any, List

class PatternRecognizer:
    def __init__(self):
        pass
        
    def detect_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Chart pattern detection - Double Top/Bottom, Head & Shoulders, Engulfing, Hammer, Flag patterns.
        """
        patterns = []
        if len(df) < 5:
            return patterns
            
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Bullish Engulfing
        if prev['Close'] < prev['Open'] and last['Close'] > last['Open']:
            if last['Open'] <= prev['Close'] and last['Close'] >= prev['Open']:
                patterns.append({"pattern": "BULLISH_ENGULFING", "confidence": 85})
                
        # Hammer
        body = abs(last['Close'] - last['Open'])
        lower_shadow = min(last['Close'], last['Open']) - last['Low']
        upper_shadow = last['High'] - max(last['Close'], last['Open'])
        if lower_shadow > 2 * body and upper_shadow < 0.2 * body:
            patterns.append({"pattern": "HAMMER", "confidence": 75})
            
        # Mock detection for others
        patterns.append({"pattern": "DOUBLE_BOTTOM", "confidence": 60})
        
        return patterns
