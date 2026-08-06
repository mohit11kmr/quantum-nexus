"""
Walk-Forward Backtester v1.0

Adopted from trading_bot's walk_forward_backtester.py and adapted to
quantum_nexus conventions (capitalized OHLCV columns, DatetimeIndex).

Methodology (anti-overfitting):
  - In-sample (training) period: parameter grid optimization
  - Out-of-sample (validation) period: tested with the SAME params, no re-fit
  - Rolling windows step forward across history
  - Reports an overfitting check: OOS win-rate vs IS win-rate
"""

import math
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Callable, Optional
from datetime import timedelta
from itertools import product

from services.indicators import calculate_indicators


def _ensure_datetime_index(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize OHLCV frame to a sorted DatetimeIndex (yfinance returns a
    'Date' column after reset_index)."""
    df = data.copy()
    for col in ("Date", "Datetime", "datetime", "Timestamp"):
        if col in df.columns and not isinstance(df.index, pd.DatetimeIndex):
            df[col] = pd.to_datetime(df[col], errors="coerce")
            df = df.set_index(col).dropna()
            break
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors="coerce")
    return df.sort_index()


def _prepare_default(df: pd.DataFrame) -> pd.DataFrame:
    return calculate_indicators(df)


def default_strategy(df: pd.DataFrame, vol_surge: float = 1.5, rsi_zone: float = 55.0,
                     stop_loss_pct: float = 0.02, take_profit_pct: float = 0.04) -> List[Dict]:
    """
    Default ruleset for backtesting: VWAP + volume-surge + RSI long entry,
    fixed % stop loss / take profit. Returns trades as [{'pnl': fraction}].
    """
    if not {"RSI", "VWAP", "Vol_Surge_Ratio"}.issubset(df.columns):
        df = calculate_indicators(df)
    trades: List[Dict] = []
    position = None
    for i in range(1, len(df)):
        row = df.iloc[i]
        close = float(row["Close"])
        rsi = float(row["RSI"]) if pd.notna(row.get("RSI")) else 50.0
        vol = float(row["Vol_Surge_Ratio"]) if pd.notna(row.get("Vol_Surge_Ratio")) else 1.0
        vwap = float(row["VWAP"]) if pd.notna(row.get("VWAP")) else close

        if position is None:
            if close > vwap and vol >= vol_surge and rsi > rsi_zone:
                position = {"entry": close}
        else:
            if close <= position["entry"] * (1 - stop_loss_pct):
                trades.append({"pnl": (close - position["entry"]) / position["entry"]})
                position = None
            elif close >= position["entry"] * (1 + take_profit_pct):
                trades.append({"pnl": (close - position["entry"]) / position["entry"]})
                position = None

    if position is not None:
        close = float(df["Close"].iloc[-1])
        trades.append({"pnl": (close - position["entry"]) / position["entry"]})
    return trades


# Optimization hook: computed once per window, reused across every param combo.
default_strategy.prepare = _prepare_default


DEFAULT_PARAM_GRID: Dict[str, List] = {
    "vol_surge": [1.2, 1.5, 2.0],
    "rsi_zone": [50.0, 55.0],
    "stop_loss_pct": [0.02, 0.03],
    "take_profit_pct": [0.04, 0.06],
}


def _calc_metrics(trades: List[Dict]) -> Dict:
    """Compute standard backtest metrics from a trade list."""
    if not trades:
        return {"num_trades": 0, "win_rate": 0.0, "avg_trade_pnl": 0.0,
                "total_pnl": 0.0, "max_drawdown": 0.0, "sharpe_ratio": 0.0,
                "calmar_ratio": 0.0, "profit_factor": 0.0}

    pnl_values = np.array([float(t.get("pnl", 0.0)) for t in trades])
    win_count = int((pnl_values > 0).sum())
    win_rate = win_count / len(pnl_values)
    total_pnl = float(pnl_values.sum())
    avg_pnl = float(pnl_values.mean())

    cumulative = np.cumsum(pnl_values)
    running_max = np.maximum.accumulate(cumulative)
    max_drawdown = float(np.max(running_max - cumulative)) if len(cumulative) else 0.0

    if len(pnl_values) > 1:
        std = float(pnl_values.std())
        sharpe = float(pnl_values.mean() / std * np.sqrt(252)) if std > 0 else 0.0
    else:
        sharpe = 0.0

    gains = pnl_values[pnl_values > 0].sum()
    losses = -pnl_values[pnl_values < 0].sum()
    profit_factor = float(gains / losses) if losses > 0 else (float("inf") if gains > 0 else 0.0)

    calmar = float(total_pnl / max_drawdown) if max_drawdown > 0 else 0.0
    return {"num_trades": len(trades), "win_rate": round(win_rate, 4), "avg_trade_pnl": round(avg_pnl, 6),
            "total_pnl": round(total_pnl, 6), "max_drawdown": round(max_drawdown, 6),
            "sharpe_ratio": round(sharpe, 3), "calmar_ratio": round(calmar, 3),
            "profit_factor": round(profit_factor, 3)}


def _sanitize_result(obj):
    """Replace non-JSON-safe float values (inf/nan) recursively."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _sanitize_result(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_result(v) for v in obj]
    return obj


class WalkForwardBacktester:
    def __init__(self, in_sample_months: int = 3,
                 out_sample_months: int = 1,
                 step_months: int = 1):
        self.in_sample_months = in_sample_months
        self.out_sample_months = out_sample_months
        self.step_months = step_months

    def generate_windows(self, data: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
        data = _ensure_datetime_index(data)
        start_date = data.index[0]
        end_date = data.index[-1]
        windows = []
        current_date = start_date

        while True:
            in_sample_end = current_date + timedelta(days=30 * self.in_sample_months)
            if in_sample_end > end_date:
                break
            in_sample_data = data[(data.index >= current_date) & (data.index < in_sample_end)]
            if len(in_sample_data) == 0:
                current_date += timedelta(days=30 * self.step_months)
                continue

            out_sample_end = in_sample_end + timedelta(days=30 * self.out_sample_months)
            if out_sample_end > end_date:
                out_sample_end = end_date
            out_sample_data = data[(data.index >= in_sample_end) & (data.index < out_sample_end)]

            if len(out_sample_data) > 0:
                windows.append((in_sample_data, out_sample_data))
            current_date += timedelta(days=30 * self.step_months)
        return windows

    def optimize_parameters(self, in_sample_data: pd.DataFrame,
                            param_grid: Dict[str, List],
                            strategy_func: Callable) -> Dict:
        results = []
        param_names = list(param_grid.keys())
        for combo in product(*(param_grid[n] for n in param_names)):
            params = dict(zip(param_names, combo))
            try:
                trades = strategy_func(in_sample_data, **params) or []
                if not trades:
                    continue
                metrics = _calc_metrics(trades)
                results.append({"parameters": params, **metrics})
            except Exception:
                continue

        if not results:
            return {"best_parameters": {}, "best_performance": {}, "all_results": []}

        def _key(r):
            pf = r["profit_factor"]
            return (0.0 if pf == float("inf") else pf, r["total_pnl"])

        best = max(results, key=_key)
        return {
            "best_parameters": best["parameters"],
            "best_performance": {k: best[k] for k in
                                 ("num_trades", "win_rate", "avg_trade_pnl", "total_pnl", "profit_factor")},
            "all_results": results,
        }

    def backtest_window(self, in_sample_data: pd.DataFrame, out_sample_data: pd.DataFrame,
                        strategy_func: Callable, param_grid: Dict[str, List],
                        optimize: bool = True) -> Dict:
        # Pre-compute the enriched frame ONCE so every param combo reuses it
        # (default_strategy skips re-computation when the columns exist).
        prepare = getattr(strategy_func, "prepare", None)
        if prepare is not None:
            in_sample_data = prepare(_ensure_datetime_index(in_sample_data))
            out_sample_data = prepare(_ensure_datetime_index(out_sample_data))

        if optimize:
            opt = self.optimize_parameters(in_sample_data, param_grid, strategy_func)
            best_params = opt["best_parameters"]
        else:
            best_params = {k: v[0] for k, v in param_grid.items()}

        in_sample_trades = strategy_func(in_sample_data, **best_params) or []
        out_sample_trades = strategy_func(out_sample_data, **best_params) or []

        in_sample_metrics = _calc_metrics(in_sample_trades)
        out_sample_metrics = _calc_metrics(out_sample_trades)

        is_start = str(in_sample_data.index[0].date())
        is_end = str(in_sample_data.index[-1].date())
        oos_start = str(out_sample_data.index[0].date())
        oos_end = str(out_sample_data.index[-1].date())

        return {
            "best_parameters": best_params,
            "in_sample": {**in_sample_metrics, "start_date": is_start, "end_date": is_end},
            "out_sample": {**out_sample_metrics, "start_date": oos_start, "end_date": oos_end},
            "overfitting_check": {
                "is_overfit": bool(out_sample_metrics["win_rate"] < in_sample_metrics["win_rate"] * 0.8),
                "in_sample_wr": in_sample_metrics["win_rate"],
                "out_sample_wr": out_sample_metrics["win_rate"],
            },
        }

    def run_walk_forward(self, data: pd.DataFrame, strategy_func: Callable,
                         param_grid: Dict[str, List], optimize: bool = True) -> Dict:
        windows = self.generate_windows(data)
        if not windows:
            return {"error": "Insufficient data for walk-forward analysis",
                    "needed_months": self.in_sample_months + self.out_sample_months}

        window_results = [self.backtest_window(ins, oos, strategy_func, param_grid, optimize)
                          for ins, oos in windows]

        in_pnl = sum(w["in_sample"]["total_pnl"] for w in window_results)
        out_pnl = sum(w["out_sample"]["total_pnl"] for w in window_results)
        avg_is_wr = float(np.mean([w["in_sample"]["win_rate"] for w in window_results]))
        avg_oos_wr = float(np.mean([w["out_sample"]["win_rate"] for w in window_results]))
        out_trades = sum(w["out_sample"]["num_trades"] for w in window_results)

        robustness = round(avg_oos_wr / max(avg_is_wr, 0.01), 3)
        recommendation = ("Strategy appears robust" if avg_oos_wr > avg_is_wr * 0.7
                          else "Strategy may be overfit - avoid live deployment")

        return _sanitize_result({
            "num_windows": len(window_results),
            "total_in_sample_pnl": round(in_pnl, 4),
            "total_out_sample_pnl": round(out_pnl, 4),
            "avg_in_sample_win_rate": round(avg_is_wr, 4),
            "avg_out_sample_win_rate": round(avg_oos_wr, 4),
            "out_of_sample_trades": out_trades,
            "overfitting_detected": bool(avg_oos_wr < avg_is_wr * 0.75),
            "robustness_score": robustness,
            "recommendation": recommendation,
            "strategy_params_optimized": optimize,
            "window_results": window_results,
        })
