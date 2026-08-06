import pandas as pd
import numpy as np
from typing import Dict, Any, List

from services.regime_classifier import MarketRegimeClassifier

_regime_classifier = MarketRegimeClassifier()

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
    money_flow_mult = money_flow_mult.fillna(0)
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

def compute_volume_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute volume indicators: Surge Ratio, OBV, VWAP, CMF, ADL, MFI, VPT, Z-Score, Pocket Pivot."""
    if df is None or df.empty or len(df) < 2:
        return df

    df = df.copy()

    # 20-Day SMA Volume & Surge Ratio
    df["Vol_SMA20"] = df["Volume"].rolling(window=min(20, len(df)), min_periods=1).mean()
    df["Vol_Surge_Ratio"] = np.where(
        df["Vol_SMA20"] > 0,
        np.round(df["Volume"] / df["Vol_SMA20"], 2),
        1.0
    )

    # On-Balance Volume (OBV)
    obv = [0.0]
    for i in range(1, len(df)):
        if df["Close"].iloc[i] > df["Close"].iloc[i - 1]:
            obv.append(obv[-1] + df["Volume"].iloc[i])
        elif df["Close"].iloc[i] < df["Close"].iloc[i - 1]:
            obv.append(obv[-1] - df["Volume"].iloc[i])
        else:
            obv.append(obv[-1])
    df["OBV"] = obv
    df["OBV_EMA20"] = df["OBV"].ewm(span=min(20, len(df)), adjust=False).mean()

    # Volume Weighted Average Price (VWAP)
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3.0
    tp_vol = typical_price * df["Volume"]
    df["VWAP"] = np.round(tp_vol.cumsum() / np.maximum(1, df["Volume"].cumsum()), 2)

    # Chaikin Money Flow (CMF 20)
    mf_multiplier = np.where(
        (df["High"] - df["Low"]) > 0,
        ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / (df["High"] - df["Low"]),
        0.0
    )
    mf_volume = mf_multiplier * df["Volume"]
    cmf_sum_vol = df["Volume"].rolling(window=min(20, len(df)), min_periods=1).sum()
    df["CMF"] = np.where(
        cmf_sum_vol > 0,
        np.round(mf_volume.rolling(window=min(20, len(df)), min_periods=1).sum() / cmf_sum_vol, 3),
        0.0
    )

    # Accumulation / Distribution Line (ADL) — CLV * Volume cumulative
    clv = np.where(
        (df["High"] - df["Low"]) > 0,
        ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / (df["High"] - df["Low"]),
        0.0
    )
    df["ADL"] = np.round((clv * df["Volume"]).cumsum(), 2)
    df["ADL_EMA20"] = df["ADL"].ewm(span=min(20, len(df)), adjust=False).mean()

    # Money Flow Index (MFI, 14-period) — bounded 0..100 oscillator
    mfi_period = min(14, len(df))
    raw_money_flow = typical_price * df["Volume"]
    pos_flow = raw_money_flow.where(typical_price > typical_price.shift(1), 0.0)
    neg_flow = raw_money_flow.where(typical_price < typical_price.shift(1), 0.0)
    pos_sum = pos_flow.rolling(window=mfi_period, min_periods=1).sum()
    neg_sum = neg_flow.rolling(window=mfi_period, min_periods=1).sum()
    mfr = pos_sum / np.maximum(neg_sum, 1e-9)
    df["MFI"] = np.round(100.0 - (100.0 / (1.0 + mfr)), 2)

    # Volume Price Trend (VPT) — % price change weighted by volume
    pct_change = df["Close"].pct_change().fillna(0.0)
    df["VPT"] = np.round((pct_change * df["Volume"]).cumsum(), 2)

    # Volume Z-Score — statistical volume spike detection (20d window)
    vol_std = df["Volume"].rolling(window=min(20, len(df)), min_periods=1).std()
    df["Volume_ZScore"] = np.round(
        np.where(
            vol_std > 0,
            (df["Volume"] - df["Vol_SMA20"]) / vol_std,
            0.0
        ),
        2
    )

    # Pocket Pivot — up-day volume today exceeds all down-day volumes in last 10 sessions
    pocket_pivot = []
    for i in range(len(df)):
        if i == 0:
            pocket_pivot.append(False)
            continue
        up_day = df["Close"].iloc[i] > df["Close"].iloc[i - 1]
        if not up_day:
            pocket_pivot.append(False)
            continue
        window_start = max(0, i - 10)
        slice_df = df.loc[window_start:i - 1]
        down_mask = slice_df["Close"].values < slice_df["Close"].shift(1).fillna(df["Close"].iloc[0]).values
        down_days = slice_df.loc[down_mask, "Volume"]
        max_down_vol = float(down_days.max()) if len(down_days) > 0 else 0.0
        pocket_pivot.append(bool(df["Volume"].iloc[i] > max_down_vol))
    df["Pocket_Pivot"] = pocket_pivot

    # Price Change Pct
    df["Price_Change_Pct"] = np.round(df["Close"].pct_change().fillna(0.0) * 100.0, 2)

    # Signal Text (enhanced with MFI overbought/oversold and pocket pivot)
    df["Volume_Signal"] = np.where(
        (df["Vol_Surge_Ratio"] >= 2.0) & (df["Price_Change_Pct"] > 0),
        "BULLISH BREAKOUT",
        np.where(
            (df["Vol_Surge_Ratio"] >= 2.0) & (df["Price_Change_Pct"] < 0),
            "BEARISH DISTRIBUTION",
            np.where(
                df["Pocket_Pivot"].fillna(False),
                "POCKET PIVOT (Institutional Uptick)",
                "NEUTRAL / CONSOLIDATION"
            )
        )
    )

    return df

def calculate_volume_profile(df: pd.DataFrame, bins_count: int = 12) -> List[Dict[str, Any]]:
    """Compute Price-wise Volume Profile and Point of Control (POC)."""
    if df is None or df.empty or len(df) < 2:
        return []

    min_p = float(df["Low"].min())
    max_p = float(df["High"].max())

    if min_p == max_p:
        return [{"priceRange": f"₹{min_p:.2f}", "volume": int(df["Volume"].sum()), "isPOC": True}]

    bins = np.linspace(min_p, max_p, bins_count + 1)
    profile = []
    max_vol = -1
    poc_idx = -1

    for i in range(bins_count):
        p_low = bins[i]
        p_high = bins[i + 1]
        mask = (df["Close"] >= p_low) & (df["Close"] <= p_high)
        vol_sum = int(df.loc[mask, "Volume"].sum())

        if vol_sum > max_vol:
            max_vol = vol_sum
            poc_idx = i

        profile.append({
            "priceLow": round(p_low, 2),
            "priceHigh": round(p_high, 2),
            "priceRange": f"₹{p_low:.1f} - ₹{p_high:.1f}",
            "volume": vol_sum,
            "isPOC": False
        })

    if 0 <= poc_idx < len(profile):
        profile[poc_idx]["isPOC"] = True

    return profile

def calculate_value_area(profile: List[Dict[str, Any]], pct: float = 0.70) -> Dict[str, Any]:
    """Compute Value Area High (VAH) and Value Area Low (VAL) from a volume profile.

    Expands outward from the POC until `pct` of total volume is captured.
    """
    if not profile:
        return {"vah": 0.0, "val": 0.0, "poc": 0.0, "pocVolume": 0, "totalVolume": 0}

    poc_idx = next((i for i, p in enumerate(profile) if p.get("isPOC")), 0)
    total_vol = float(sum(p["volume"] for p in profile))
    if total_vol <= 0:
        return {"vah": 0.0, "val": 0.0, "poc": profile[poc_idx]["priceLow"], "pocVolume": 0, "totalVolume": 0}

    target = total_vol * pct
    captured = float(profile[poc_idx]["volume"])
    lo = hi = poc_idx

    while captured < target and (lo > 0 or hi < len(profile) - 1):
        lo_next = profile[lo - 1]["volume"] if lo > 0 else -1.0
        hi_next = profile[hi + 1]["volume"] if hi < len(profile) - 1 else -1.0
        if lo_next >= hi_next and lo > 0:
            lo -= 1
            captured += lo_next
        elif hi < len(profile) - 1:
            hi += 1
            captured += hi_next
        else:
            break

    return {
        "vah": round(profile[hi]["priceHigh"], 2),
        "val": round(profile[lo]["priceLow"], 2),
        "poc": round((profile[poc_idx]["priceLow"] + profile[poc_idx]["priceHigh"]) / 2.0, 2),
        "pocVolume": int(profile[poc_idx]["volume"]),
        "totalVolume": int(total_vol),
        "valueAreaPct": round(captured / total_vol * 100.0, 1)
    }

def generate_ai_analysis(symbol: str, df: pd.DataFrame) -> Dict[str, Any]:
    """Generate AI market report incorporating the real market regime classifier."""
    if df is None or df.empty:
        return {
            "symbol": symbol,
            "summary": "No data available.",
            "recommendation": "NEUTRAL",
            "keyLevels": {"support": 0, "resistance": 0, "poc": 0},
            "marketRegime": {"regime": "SIDEWAYS", "confidence": 50.0}
        }

    latest = df.iloc[-1]
    vol_surge = float(latest.get("Vol_Surge_Ratio", 1.0))
    cmf_val = float(latest.get("CMF", 0.0))
    mfi_val = float(latest.get("MFI", 50.0))
    adl_val = float(latest.get("ADL", 0.0))
    adl_ema = float(latest.get("ADL_EMA20", 0.0))
    price_chg = float(latest.get("Price_Change_Pct", 0.0))
    close_p = float(latest.get("Close", 0.0))
    obv_val = float(latest.get("OBV", 0.0))
    obv_ema = float(latest.get("OBV_EMA20", 0.0))
    vwap_val = float(latest.get("VWAP", 0.0))
    pocket_pivot = bool(latest.get("Pocket_Pivot", False))
    vol_z = float(latest.get("Volume_ZScore", 0.0))

    try:
        regime_info = _regime_classifier.classify(df)
    except Exception:
        regime_info = {"regime": "SIDEWAYS", "confidence": 50.0}

    supp = round(float(df["Low"].tail(20).min()), 2)
    resist = round(float(df["High"].tail(20).max()), 2)
    poc_val = round(float((df["High"].tail(20).max() + df["Low"].tail(20).min()) / 2.0), 2)

    adl_divergence = ""
    if adl_val < adl_ema and price_chg > 0:
        adl_divergence = "A/D line divergence suggests the rally lacks accumulation support."
    elif adl_val > adl_ema and price_chg < 0:
        adl_divergence = "Positive A/D divergence hints at hidden accumulation during the dip."

    score = 0
    if vol_surge >= 2.0: score += 2
    if vol_z >= 2.0: score += 1
    if cmf_val > 0.1: score += 2
    if 60.0 < mfi_val < 80.0: score += 1
    if obv_val > obv_ema: score += 1
    if adl_val > adl_ema: score += 1
    if pocket_pivot: score += 2
    if close_p > vwap_val: score += 1
    if regime_info.get("regime") == "BULLISH": score += 2

    if mfi_val >= 80.0:
        recommendation = "OVERBOUGHT (FADE)"
        summary = f"{symbol} is overbought (MFI: {mfi_val}) after a {vol_surge}x volume surge. Profit booking risk is elevated near ₹{resist}."
    elif mfi_val <= 20.0:
        recommendation = "OVERSOLD (REVERSAL WATCH)"
        summary = f"{symbol} is oversold (MFI: {mfi_val}) on heavy distribution. Watch for a reversal once selling pressure exhausts near ₹{supp}."
    elif score >= 7:
        recommendation = "STRONG BUY (Institutional Surge)"
        summary = f"{symbol} exhibits massive institutional volume accumulation ({vol_surge}x 20-day SMA, {vol_z:.1f} sigma). Market regime is {regime_info.get('regime')} with CMF at +{cmf_val}. {adl_divergence}"
    elif score >= 4:
        recommendation = "BUY ON DIPS"
        summary = f"{symbol} shows positive money flow (CMF: +{cmf_val}, MFI: {mfi_val}) above VWAP ₹{vwap_val}. Market regime is {regime_info.get('regime')}. {adl_divergence}"
    elif score <= 1 and price_chg < -1.5:
        recommendation = "BEARISH AVOID / SHORT"
        summary = f"{symbol} experiencing heavy selling pressure with negative money flow (CMF: {cmf_val}, MFI: {mfi_val}). {adl_divergence}"
    else:
        recommendation = "NEUTRAL / HOLD"
        summary = f"{symbol} is consolidating near VWAP ₹{vwap_val}. Market regime is {regime_info.get('regime')}. {adl_divergence}"

    return {
        "symbol": symbol,
        "summary": summary.strip(),
        "recommendation": recommendation,
        "marketRegime": {
            "regime": regime_info.get("regime", "SIDEWAYS"),
            "confidence": float(regime_info.get("confidence", 50.0))
        },
        "keyLevels": {
            "support": supp,
            "resistance": resist,
            "vwap": round(float(vwap_val), 2),
            "poc": poc_val,
            "mfi": round(float(mfi_val), 2),
            "volumeZScore": round(float(vol_z), 2)
        }
    }
