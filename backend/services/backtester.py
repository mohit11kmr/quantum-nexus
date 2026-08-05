import pandas as pd
from typing import Dict, Any

class Backtester:
    def __init__(self):
        pass
        
    def run_volume_backtest(self, df: pd.DataFrame, initial_capital: float = 100000.0) -> Dict[str, Any]:
        capital = initial_capital
        equity_curve = []
        trades = []
        
        in_position = False
        entry_price = 0.0
        
        for i in range(1, len(df)):
            current = df.iloc[i]
            prev = df.iloc[i-1]
            
            # Simple volume breakout logic
            if not in_position and current['Volume'] > prev['Volume'] * 1.5 and current['Close'] > prev['Close']:
                in_position = True
                entry_price = current['Close']
                trades.append({"type": "BUY", "price": entry_price, "index": i})
            elif in_position and current['Close'] < entry_price * 0.98: # 2% stop loss
                in_position = False
                capital *= (current['Close'] / entry_price)
                trades.append({"type": "SELL", "price": current['Close'], "index": i})
                
            equity_curve.append(capital)
            
        if in_position:
            capital *= (df.iloc[-1]['Close'] / entry_price)
            
        return {
            "initial_capital": initial_capital,
            "final_capital": capital,
            "return_pct": ((capital - initial_capital) / initial_capital) * 100,
            "trades_count": len(trades),
            "equity_curve": equity_curve
        }
