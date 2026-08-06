"""
Technical Indicators Engine v2.0 — REAL implementations.

Adopted & hardened from system-repair 'trading/indicators.py' with fixes for:
  - Real ADX (Wilder) with +DI/-DI  (was: placeholder returning ATR)
  - Real SuperTrend (was: placeholder returning hl2)
  - Real weighted signal strength scoring with reasons (was: hardcoded 0.75)
  - CMF, OBV, VWAP, Vol Surge Ratio, BB% and true volume-aware VWAP

All original function signatures are preserved for backward compatibility.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Union


# ── Moving Averages ─────────────────────────────────────────
def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (14) with division-by-zero safety."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs.fillna(0)))).fillna(50)


def calculate_stoch_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    rsi = calculate_rsi(series, period)
    min_rsi = rsi.rolling(window=period).min()
    max_rsi = rsi.rolling(window=period).max()
    return (((rsi - min_rsi) / (max_rsi - min_rsi).replace(0, np.nan)) * 100).fillna(50)


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
    fast_ema = calculate_ema(series, fast)
    slow_ema = calculate_ema(series, slow)
    macd = fast_ema - slow_ema
    sig = calculate_ema(macd, signal)
    return macd, sig


# ── Volatility ──────────────────────────────────────────────
def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return true_range.rolling(period).mean()


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """REAL Wilder ADX with +DI / -DI direction indicators."""
    high, low, close = df['High'], df['Low'], df['Close']
    plus_dm = high.diff()
    minus_dm = -(low.diff())
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0.0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0.0)

    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    plus_di = 100 * (plus_dm.rolling(period).mean() / atr.replace(0, np.nan))
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr.replace(0, np.nan))

    denom = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / denom
    return dx.rolling(period).mean().fillna(0)


def calculate_bollinger_bands(series: pd.Series, period: int = 20, std_dev: int = 2) -> Tuple[pd.Series, pd.Series]:
    sma = series.rolling(window=period).mean()
    std = series.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, lower


def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.Series:
    """REAL SuperTrend indicator. Returns the supertrend line.
    Trend direction is available via the 'SuperTrend_Dir' column after
    calculate_indicators(), or from the sign of (Close - SuperTrend).
    """
    hl2 = (df['High'] + df['Low']) / 2
    atr = df['ATR'] if 'ATR' in df else calculate_atr(df, period)
    atr = atr.fillna(0)

    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)

    n = len(df)
    final_upper = pd.Series(index=df.index, dtype=float)
    final_lower = pd.Series(index=df.index, dtype=float)
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=float)  # +1 bullish, -1 bearish

    if n == 0:
        return supertrend

    final_upper.iloc[0] = upperband.iloc[0]
    final_lower.iloc[0] = lowerband.iloc[0]
    direction.iloc[0] = 1.0
    supertrend.iloc[0] = lowerband.iloc[0]

    for i in range(1, n):
        up = float(upperband.iloc[i])
        low_b = float(lowerband.iloc[i])
        close = float(df['Close'].iloc[i])
        prev_close = float(df['Close'].iloc[i - 1])
        prev_fu = float(final_upper.iloc[i - 1])
        prev_fl = float(final_lower.iloc[i - 1])
        prev_dir = float(direction.iloc[i - 1])

        # Final bands (SuperTrend carry logic)
        fu = up if (up < prev_fu or prev_close > prev_fu) else prev_fu
        fl = low_b if (low_b > prev_fl or prev_close < prev_fl) else prev_fl

        # Trend flip
        if prev_dir == 1.0:
            new_dir = 1.0 if close > fl else -1.0
        else:
            new_dir = -1.0 if close < fu else 1.0

        direction.iloc[i] = new_dir
        final_upper.iloc[i] = fu
        final_lower.iloc[i] = fl
        supertrend.iloc[i] = fl if new_dir == 1.0 else fu

    return supertrend


# ── Volume ──────────────────────────────────────────────────
def calculate_obv(df: pd.DataFrame) -> pd.Series:
    obv = [0]
    closes = df['Close'].values
    vols = df['Volume'].values
    for i in range(1, len(df)):
        if closes[i] > closes[i - 1]:
            obv.append(obv[-1] + vols[i])
        elif closes[i] < closes[i - 1]:
            obv.append(obv[-1] - vols[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """True volume-weighted VWAP with a documented fallback when volume is zero."""
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    if 'Volume' in df.columns and df['Volume'].sum() > 0:
        cum_vol = df['Volume'].cumsum().replace(0, np.nan)
        vwap = (typical_price * df['Volume']).cumsum() / cum_vol
        return vwap.ffill().fillna(typical_price)
    return typical_price.rolling(window=20).mean()


def calculate_cmf(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Chaikin Money Flow (20)."""
    money_flow_mult = ((df['Close'] - df['Low']) - (df['High'] - df['Close'])) / (df['High'] - df['Low']).replace(0, np.nan)
    money_flow_mult = money_flow_mult.fillna(0)
    money_flow_vol = money_flow_mult * df['Volume']
    return (money_flow_vol.rolling(window=period).sum() / df['Volume'].rolling(window=period).sum().replace(0, np.nan)).fillna(0)


def calculate_volume_surge_ratio(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """Current volume vs average volume (e.g. 2.0 = double the average)."""
    avg_vol = df['Volume'].rolling(window=period).mean().replace(0, np.nan)
    return (df['Volume'] / avg_vol).fillna(1.0)


# ── Master indicator enrichment ─────────────────────────────
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute every indicator column consumed by the signal engine in one pass:
    EMA9/21/50, RSI, StochRSI, MACD, ADX, ATR, Plus_DI, Minus_DI,
    BB Upper/Mid/Lower/Width/Pct, VWAP, Typical_Price, CMF, OBV,
    Vol_Surge_Ratio, SuperTrend, SuperTrend_Dir.
    """
    df = df.copy()

    for col in ('Open', 'High', 'Low', 'Close', 'Volume'):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Volume'] = df['Volume'].fillna(0)

    df['EMA9'] = calculate_ema(df['Close'], 9)
    df['EMA21'] = calculate_ema(df['Close'], 21)
    df['EMA50'] = calculate_ema(df['Close'], 50)
    df['RSI'] = calculate_rsi(df['Close'], 14)
    df['StochRSI'] = calculate_stoch_rsi(df['Close'], 14)

    macd, sig = calculate_macd(df['Close'])
    df['MACD'] = macd
    df['MACD_Signal'] = sig
    df['MACD_Hist'] = macd - sig

    df['ATR'] = calculate_atr(df, 14)
    df['ADX'] = calculate_adx(df, 14)

    # Recompute +DI / -DI for transparency
    high, low, close = df['High'], df['Low'], df['Close']
    plus_dm = high.diff().where((high.diff() > -(low.diff())) & (high.diff() > 0), 0.0)
    minus_dm = (-(low.diff())).where((-(low.diff()) > high.diff()) & (-(low.diff()) > 0), 0.0)
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()
    df['Plus_DI'] = 100 * (plus_dm.rolling(14).mean() / atr14.replace(0, np.nan))
    df['Minus_DI'] = 100 * (minus_dm.rolling(14).mean() / atr14.replace(0, np.nan))

    bb_upper, bb_lower = calculate_bollinger_bands(df['Close'], 20, 2)
    df['BB_Upper'] = bb_upper
    df['BB_Mid'] = df['Close'].rolling(window=20).mean()
    df['BB_Lower'] = bb_lower
    df['BB_Width'] = ((df['BB_Upper'] - df['BB_Lower']) / df['BB_Mid'].replace(0, np.nan)) * 100
    bb_range = (df['BB_Upper'] - df['BB_Lower']).replace(0, np.nan)
    df['BB_Pct'] = ((df['Close'] - df['BB_Lower']) / bb_range) * 100

    df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = calculate_vwap(df)
    df['CMF'] = calculate_cmf(df, 20)
    df['OBV'] = calculate_obv(df)
    df['Vol_Surge_Ratio'] = calculate_volume_surge_ratio(df, 20)

    st = calculate_supertrend(df, 10, 3.0)
    df['SuperTrend'] = st
    df['SuperTrend_Dir'] = np.where(df['Close'] >= st, 1.0, -1.0)

    return df


def supertrend_bullish(df: pd.DataFrame) -> bool:
    """True if the latest bar is in a bullish SuperTrend."""
    if 'SuperTrend_Dir' in df.columns and len(df) > 0:
        return bool(df['SuperTrend_Dir'].iloc[-1] == 1.0)
    if 'SuperTrend' in df.columns and len(df) > 0:
        return bool(df['Close'].iloc[-1] >= df['SuperTrend'].iloc[-1])
    return True


# ── Support / Resistance ────────────────────────────────────
def calculate_support_resistance(df: pd.DataFrame, n: int = 3) -> Tuple[list, list]:
    """Pivot-based support/resistance levels (4-point swing detection)."""
    recent = df.tail(100)
    highs = recent['High'].values
    lows = recent['Low'].values
    res, sup = [], []
    for i in range(2, len(highs) - 2):
        if highs[i] > max(highs[i - 1], highs[i - 2], highs[i + 1], highs[i + 2]):
            res.append(round(float(highs[i]), 2))
        if lows[i] < min(lows[i - 1], lows[i - 2], lows[i + 1], lows[i + 2]):
            sup.append(round(float(lows[i]), 2))
    return sorted(set(sup))[:n], sorted(set(res))[-n:]


# ── Weighted Signal Strength ────────────────────────────────
def weighted_signal_strength(row: Union[pd.Series, Dict[str, Any]]) -> Tuple[str, int, str, list]:
    """
    Real multi-factor signal scoring.
    Returns: (strength, score, grade, reasons_list)
    Accepts a pandas Series (one row of a computed df) or a dict.
    """
    r = dict(row)

    def g(key, default):
        val = r.get(key, default)
        return float(val) if val is not None else float(default)

    score = 0
    reasons = []

    ema9, ema21, ema50 = g('EMA9', 0), g('EMA21', 0), g('EMA50', 0)
    close = g('Close', 0)
    rsi = g('RSI', 50)
    macd = g('MACD', 0)
    macd_sig = g('MACD_Signal', 0)
    macd_hist = g('MACD_Hist', 0)
    adx = g('ADX', 0)
    bb_lower = g('BB_Lower', 0)
    bb_upper = g('BB_Upper', 0)
    vwap = g('VWAP', 0)

    if ema9 > ema21:
        score += 2; reasons.append({"text": "EMA Bullish Cross", "type": "bull"})
    else:
        score -= 2; reasons.append({"text": "EMA Bearish Cross", "type": "bear"})

    if close > ema50:
        score += 1; reasons.append({"text": "Above EMA50", "type": "bull"})
    else:
        score -= 1; reasons.append({"text": "Below EMA50", "type": "bear"})

    if rsi < 30:
        score += 2; reasons.append({"text": "RSI Deeply Oversold", "type": "bull"})
    elif rsi < 40:
        score += 1; reasons.append({"text": "RSI Oversold Zone", "type": "bull"})
    elif rsi > 70:
        score -= 2; reasons.append({"text": "RSI Overbought", "type": "bear"})
    elif rsi > 60:
        score -= 1; reasons.append({"text": "RSI Hot Zone", "type": "bear"})
    else:
        reasons.append({"text": "RSI Neutral", "type": "neutral"})

    if macd_hist > 0 and macd > macd_sig:
        score += 2; reasons.append({"text": "MACD Bullish", "type": "bull"})
    elif macd_hist < 0:
        score -= 2; reasons.append({"text": "MACD Bearish", "type": "bear"})

    if adx > 25:
        reasons.append({"text": f"Strong Trend (ADX {adx:.0f})", "type": "info"})
        score += 1 if score > 0 else -1

    if bb_lower and close < bb_lower:
        score += 1; reasons.append({"text": "Below BB Lower", "type": "bull"})
    elif bb_upper and close > bb_upper:
        score -= 1; reasons.append({"text": "Above BB Upper", "type": "bear"})

    if vwap and close > vwap:
        score += 1; reasons.append({"text": "Price > VWAP", "type": "bull"})
    else:
        score -= 1; reasons.append({"text": "Price < VWAP", "type": "bear"})

    if score >= 5: strength, grade = "STRONG BUY", "A+"
    elif score >= 3: strength, grade = "BUY", "B+"
    elif score >= 1: strength, grade = "WEAK BUY", "C+"
    elif score <= -5: strength, grade = "STRONG SELL", "A-"
    elif score <= -3: strength, grade = "SELL", "B-"
    elif score <= -1: strength, grade = "WEAK SELL", "C-"
    else: strength, grade = "NEUTRAL", "D"

    return strength, score, grade, reasons
