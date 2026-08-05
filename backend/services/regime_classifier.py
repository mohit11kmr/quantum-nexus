import pandas as pd
import numpy as np
from typing import Dict, Any

class MarketRegimeClassifier:
    def __init__(self):
        pass
        
    def classify(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Classify market regime using SMA20/50, ATR, RSI, Volume."""
        if len(df) < 50:
            return {"regime": "UNKNOWN", "confidence": 0.0}
            
        close = df['Close']
        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1]
        last_close = close.iloc[-1]
        
        # Volatility
        high_low = df['High'] - df['Low']
        atr = high_low.rolling(14).mean().iloc[-1]
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rs = gain / loss if loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        
        # Volume Surge
        vol_sma20 = df['Volume'].rolling(20).mean().iloc[-1]
        last_vol = df['Volume'].iloc[-1]
        vol_surge = last_vol > vol_sma20 * 1.5
        
        score = 0
        if last_close > sma20 > sma50: score += 2
        elif last_close < sma20 < sma50: score -= 2
        
        if rsi > 60: score += 1
        elif rsi < 40: score -= 1
        
        if vol_surge:
            score *= 1.5
            
        if score > 1.5:
            regime = "BULLISH"
            conf = min(100, 50 + score * 10)
        elif score < -1.5:
            regime = "BEARISH"
            conf = min(100, 50 + abs(score) * 10)
        else:
            regime = "SIDEWAYS"
            conf = 60.0
            
        return {
            "regime": regime,
            "confidence": conf,
            "sma20": sma20,
            "sma50": sma50,
            "rsi": rsi,
            "atr": atr,
            "vol_surge": vol_surge
        }
