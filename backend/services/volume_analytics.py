import pandas as pd
import numpy as np
from typing import Dict, Any

def calculate_obv(df: pd.DataFrame) -> pd.Series:
    """Calculate On-Balance Volume (OBV)."""
    obv = [0]
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
            obv.append(obv[-1] + df['Volume'].iloc[i])
        elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
            obv.append(obv[-1] - df['Volume'].iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """Calculate Volume Weighted Average Price (VWAP)."""
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    cum_vol = df['Volume'].cumsum()
    cum_vol_price = (typical_price * df['Volume']).cumsum()
    return cum_vol_price / cum_vol

def calculate_cmf(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Calculate Chaikin Money Flow (CMF)."""
    money_flow_mult = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low'])
    money_flow_mult.fillna(0, inplace=True)
    money_flow_vol = money_flow_mult * df['Volume']
    return money_flow_vol.rolling(window=period).sum() / df['Volume'].rolling(window=period).sum()

def analyze_volume_profile(df: pd.DataFrame, bins: int = 50) -> Dict[str, Any]:
    """Calculate Volume Profile and Point of Control (POC)."""
    min_price = df['Low'].min()
    max_price = df['High'].max()
    price_bins = np.linspace(min_price, max_price, bins)
    
    vol_profile = np.zeros(bins-1)
    
    for _, row in df.iterrows():
        typical = (row['High'] + row['Low'] + row['Close']) / 3
        # find the bin
        idx = np.digitize(typical, price_bins) - 1
        if 0 <= idx < len(vol_profile):
            vol_profile[idx] += row['Volume']
            
    poc_idx = np.argmax(vol_profile)
    poc_price = (price_bins[poc_idx] + price_bins[poc_idx+1]) / 2
    
    return {
        "poc": poc_price,
        "profile": list(zip(price_bins[:-1], vol_profile))
    }

def generate_ai_analysis_report(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate AI analysis report based on volume metrics."""
    if df.empty:
        return {"error": "Empty dataframe"}
        
    df['OBV'] = calculate_obv(df)
    df['VWAP'] = calculate_vwap(df)
    df['CMF'] = calculate_cmf(df)
    
    last_close = df['Close'].iloc[-1]
    last_vwap = df['VWAP'].iloc[-1]
    last_cmf = df['CMF'].iloc[-1]
    
    trend = "BULLISH" if last_close > last_vwap and last_cmf > 0 else "BEARISH"
    
    return {
        "trend": trend,
        "last_close": last_close,
        "vwap": last_vwap,
        "cmf": last_cmf,
        "summary": f"Market shows {trend} tendency based on volume flows."
    }
