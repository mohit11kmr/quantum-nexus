"""
Options Market Intelligence (NSE-style chain analytics).

Computes institutional option-flow metrics from the live option chain:
  - PCR (OI & volume based)
  - Max pain strike
  - Call / Put OI walls (resistance / support)
  - IV rank & IV skew
  - Delta-weighted net OI sentiment
  - A normalized direction score (0-100) for a quick AI-style read

All raw features are exposed under `features` so a supervised model (e.g.
XGBoost) can consume them later without changing the endpoint contract.
"""

from typing import Any, Dict, List

from services.broker_adapter import broker_adapter
from services.stock_data import fetch_live_quote


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        val = float(v)
        return val if val == val else default  # NaN guard
    except (TypeError, ValueError):
        return default


def _classify_strike(spot: float, strike: float) -> str:
    if strike > spot * 1.01:
        return "OTM"
    if strike < spot * 0.99:
        return "ITM"
    return "ATM"


def compute_options_intel(symbol: str = "NIFTY") -> Dict[str, Any]:
    quote = fetch_live_quote(symbol)
    spot = _safe_float(quote.get("current_price"), 0.0)
    if spot <= 0:
        spot = 24649.0  # last-resort fallback keeps the feature set populated

    chain = broker_adapter.get_live_option_chain_ltp(symbol)
    if not chain:
        chain = broker_adapter.get_live_option_chain_ltp("NIFTY")

    strikes_map: Dict[float, Dict[str, Any]] = {}
    total_ce_oi = total_pe_oi = 0.0
    total_ce_vol = total_pe_vol = 0.0
    sum_ce_iv = sum_pe_iv = 0.0
    n_ce_iv = n_pe_iv = 0
    all_ivs: List[float] = []
    net_delta_oi = 0.0

    for row in chain:
        strike = _safe_float(row.get("strike_price"))
        opt_type = str(row.get("option_type", "")).upper()
        oi = _safe_float(row.get("open_interest"))
        iv = _safe_float(row.get("iv"), 0.0)
        delta = _safe_float(row.get("delta"))
        volume = _safe_float(row.get("volume"))
        entry = strikes_map.setdefault(strike, {"strike": strike})
        entry[f"{opt_type}_oi"] = oi
        entry[f"{opt_type}_ltp"] = _safe_float(row.get("ltp"))
        entry[f"{opt_type}_iv"] = iv
        entry[f"{opt_type}_delta"] = delta
        entry[f"{opt_type}_volume"] = volume
        if iv > 0:
            all_ivs.append(iv)
        if opt_type == "CE":
            total_ce_oi += oi
            total_ce_vol += volume
            if iv > 0:
                sum_ce_iv += iv
                n_ce_iv += 1
            net_delta_oi += delta * oi
        elif opt_type == "PE":
            total_pe_oi += oi
            total_pe_vol += volume
            if iv > 0:
                sum_pe_iv += iv
                n_pe_iv += 1
            net_delta_oi -= abs(delta) * oi

    strikes = sorted(strikes_map.keys())
    oi_map = [
        {
            "strike": s,
            "moneyness": _classify_strike(spot, s),
            "ceOi": int(strikes_map[s].get("CE_oi", 0)),
            "ceLtp": round(strikes_map[s].get("CE_ltp", 0.0), 2),
            "ceIv": round(strikes_map[s].get("CE_iv", 0.0), 2),
            "peOi": int(strikes_map[s].get("PE_oi", 0)),
            "peLtp": round(strikes_map[s].get("PE_ltp", 0.0), 2),
            "peIv": round(strikes_map[s].get("PE_iv", 0.0), 2),
        }
        for s in strikes
    ]

    pcr_oi = round(total_pe_oi / total_ce_oi, 3) if total_ce_oi > 0 else None
    pcr_volume = round(total_pe_vol / total_ce_vol, 3) if total_ce_vol > 0 else None

    # Max pain: strike minimizing total buyer pain across all contracts.
    max_pain = None
    if strikes:
        best = min(strikes, key=lambda s: _max_pain_cost(strikes_map, s))
        max_pain = best

    # OI walls
    call_wall = max(strikes, key=lambda s: strikes_map[s].get("CE_oi", 0)) if strikes else None
    put_wall = max(strikes, key=lambda s: strikes_map[s].get("PE_oi", 0)) if strikes else None

    # IV rank: percentile of the ATM IV within the observed chain IVs.
    atm_strike = min(strikes, key=lambda s: abs(s - spot)) if strikes else None
    atm_iv_ce = strikes_map.get(atm_strike, {}).get("CE_iv", 0.0) if atm_strike else 0.0
    atm_iv_pe = strikes_map.get(atm_strike, {}).get("PE_iv", 0.0) if atm_strike else 0.0
    atm_iv = max(atm_iv_ce, atm_iv_pe)
    iv_rank_pct = _percentile(all_ivs, atm_iv) if all_ivs else 50.0

    avg_iv_ce = sum_ce_iv / n_ce_iv if n_ce_iv else 0.0
    avg_iv_pe = sum_pe_iv / n_pe_iv if n_pe_iv else 0.0
    iv_skew = round(avg_iv_pe - avg_iv_ce, 2)

    # ── Direction score (0-100) from institutional flows ──
    score = 50.0
    reasons: List[str] = []
    if pcr_oi is not None:
        if pcr_oi >= 1.2:
            score += 12
            reasons.append("PCR_OI>1.2 (put-heavy hedged floor → bullish drift)")
        elif pcr_oi <= 0.8:
            score -= 12
            reasons.append("PCR_OI<0.8 (call-heavy chase → risk of pullback)")
    if pcr_volume is not None:
        if pcr_volume >= 1.1:
            score += 6
        elif pcr_volume <= 0.9:
            score -= 6
    if atm_strike is not None and call_wall is not None and put_wall is not None:
        call_dist = (call_wall - spot) / spot if spot else 0.0
        put_dist = (spot - put_wall) / spot if spot else 0.0
        if call_dist > 0.015 and put_dist > 0.015:
            score += 6
            reasons.append("Both walls far OTM (room to run)")
        elif call_dist < 0.005 and call_dist > -0.005:
            score -= 8
            reasons.append("Call wall pinned near spot (resistance)")
        elif put_dist < 0.005 and put_dist > -0.005:
            score += 8
            reasons.append("Put wall pinned near spot (support)")
    if iv_skew < -1.5:
        score -= 6
        reasons.append("Put IV premium → fear/hedging")
    elif iv_skew > 1.5:
        score += 6
        reasons.append("Call IV premium → call demand")
    if net_delta_oi > 0:
        score += 6
        reasons.append("Delta-weighted OI net long")
    else:
        score -= 6
        reasons.append("Delta-weighted OI net short")

    score = max(0.0, min(100.0, round(score, 1)))
    if score >= 62:
        label = "BULLISH"
    elif score <= 38:
        label = "BEARISH"
    else:
        label = "NEUTRAL"

    return {
        "symbol": symbol.upper(),
        "spot_price": round(spot, 2),
        "atm_strike": atm_strike,
        "max_pain_strike": max_pain,
        "call_wall": call_wall,
        "put_wall": put_wall,
        "pcr_oi": pcr_oi,
        "pcr_volume": pcr_volume,
        "iv_rank_pct": round(iv_rank_pct, 1),
        "atm_iv": round(atm_iv, 2),
        "avg_iv_ce": round(avg_iv_ce, 2),
        "avg_iv_pe": round(avg_iv_pe, 2),
        "iv_skew": iv_skew,
        "net_delta_oi": round(net_delta_oi, 0),
        "directionScore": score,
        "directionLabel": label,
        "reasons": reasons,
        "oiMap": oi_map,
        "totalCeOi": int(total_ce_oi),
        "totalPeOi": int(total_pe_oi),
        "dataSource": chain[0].get("data_source", "unknown") if chain else "unknown",
        "features": {
            "pcr_oi": pcr_oi,
            "pcr_volume": pcr_volume,
            "max_pain_distance_pct": round((max_pain - spot) / spot * 100, 3) if max_pain and spot else 0.0,
            "iv_rank_pct": round(iv_rank_pct, 1),
            "iv_skew": iv_skew,
            "call_wall_distance_pct": round((call_wall - spot) / spot * 100, 3) if call_wall and spot else 0.0,
            "put_wall_distance_pct": round((spot - put_wall) / spot * 100, 3) if put_wall and spot else 0.0,
            "net_delta_oi_norm": round(net_delta_oi / (total_ce_oi + total_pe_oi + 1), 4),
            "oi_concentration_atm": round(
                (strikes_map.get(atm_strike, {}).get("CE_oi", 0) + strikes_map.get(atm_strike, {}).get("PE_oi", 0))
                / (total_ce_oi + total_pe_oi + 1), 4,
            ) if atm_strike else 0.0,
        },
    }


def _max_pain_cost(strikes_map: Dict[float, Dict[str, Any]], candidate: float) -> float:
    """Sum of buyer payout obligations if price settles at `candidate`."""
    total = 0.0
    for strike, entry in strikes_map.items():
        ce_oi = entry.get("CE_oi", 0)
        pe_oi = entry.get("PE_oi", 0)
        if ce_oi:
            total += ce_oi * max(0.0, strike - candidate)   # CE buyers lose if strike > settle
        if pe_oi:
            total += pe_oi * max(0.0, candidate - strike)   # PE buyers lose if strike < settle
    return total


def _percentile(values: List[float], x: float) -> float:
    if not values:
        return 50.0
    below = sum(1 for v in values if v <= x)
    return round(below / len(values) * 100.0, 1)
