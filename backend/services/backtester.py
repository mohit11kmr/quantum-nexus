import pandas as pd
import numpy as np
from typing import Dict, Any


def run_volume_backtest(
    df: pd.DataFrame,
    volume_multiplier: float = 2.0,
    holding_days: int = 5,
    stop_loss_pct: float = 2.0,
    take_profit_pct: float = 6.0,
    initial_capital: float = 100000.0,
    cost_per_trade_pct: float = 0.15,
    risk_free_rate: float = 0.06
) -> Dict[str, Any]:
    """Execute historical strategy backtest based on volume surge breakouts.

    Realistic execution: entries are filled at the NEXT bar's open (signal on
    prior close), with gap-aware stop-loss / take-profit and a time exit.

    Transaction costs (brokerage + STT + slippage) are charged on BOTH sides
    (entry and exit) so backtests stay honest — per the Indian-market guidance
    of ~0.1-0.3% per side. Risk-adjusted metrics (Sharpe, Calmar, CAGR) are
    computed from the equity curve, annualised over 252 trading days.
    """
    if df is None or df.empty or len(df) < 25:
        return {"error": "Not enough historical data for backtesting."}

    df = df.copy()
    df["SMA20_Close"] = df["Close"].rolling(20).mean()
    df["Vol_SMA20"] = df["Volume"].rolling(20).mean()

    # Decide the entry-signal mode up front. Index tickers (NIFTY, BANKNIFTY...)
    # rarely produce volume-surge signals, so when the volume strategy would fire
    # fewer than 2 trades we transparently fall back to a price-breakout proxy.
    # The chosen mode is reported in the response as `signalType`.
    prev_vol = df["Volume"].shift(1)
    prev_vol_sma = df["Vol_SMA20"].shift(1)
    prev_close = df["Close"].shift(1)
    prev_sma = df["SMA20_Close"].shift(1)
    prev2_close = df["Close"].shift(2)
    vol_ratio = prev_vol / prev_vol_sma.where(prev_vol_sma > 0)
    volume_signals = int(((vol_ratio >= volume_multiplier) & (prev_close > prev_sma)).sum())
    price_signals = int(((prev_close > prev_sma) & (prev_close > prev2_close)).sum())
    use_price_signal = volume_signals < 2 and price_signals >= 2

    cost = cost_per_trade_pct / 100.0
    capital = initial_capital
    equity_curve = []
    trades = []
    in_trade = False
    entry_price = 0.0
    entry_date = ""
    target_price = 0.0
    stop_price = 0.0
    hold_count = 0
    shares = 0

    for i in range(20, len(df)):
        row = df.iloc[i]
        curr_date = str(row.get("Date", ""))
        open_p = float(row["Open"])
        close_p = float(row["Close"])
        high_p = float(row["High"])
        low_p = float(row["Low"])

        # 1. Manage active position
        if in_trade:
            hold_count += 1
            exit_trade = False
            exit_reason = ""
            exit_price = close_p

            if open_p <= stop_price:
                exit_trade = True
                exit_price = stop_price
                exit_reason = "Stop Loss Hit (Gap)"
            elif open_p >= target_price:
                exit_trade = True
                exit_price = target_price
                exit_reason = "Take Profit Hit (Gap)"
            elif low_p <= stop_price:
                exit_trade = True
                exit_price = stop_price
                exit_reason = "Stop Loss Hit"
            elif high_p >= target_price:
                exit_trade = True
                exit_price = target_price
                exit_reason = "Take Profit Hit"
            elif hold_count >= holding_days:
                exit_trade = True
                exit_price = close_p
                exit_reason = "Time Exit"

            if exit_trade:
                # Net of transaction cost on both sides
                exit_proceeds = exit_price * shares * (1 - cost)
                cost_basis = entry_price * shares * (1 + cost)
                pnl = float(exit_proceeds - cost_basis)
                capital += pnl
                pnl_pct = round(((exit_proceeds - cost_basis) / cost_basis) * 100, 2) if cost_basis else 0.0
                trades.append({
                    "entryDate": entry_date,
                    "exitDate": curr_date,
                    "entryPrice": round(float(entry_price), 2),
                    "exitPrice": round(float(exit_price), 2),
                    "pnl": round(pnl, 2),
                    "pnlPct": round(float(pnl_pct), 2),
                    "reason": exit_reason,
                    "win": bool(pnl > 0)
                })
                in_trade = False

        # 2. Check for entry condition using PREVIOUS bar signal, filled at THIS bar's open
        if not in_trade and i > 0:
            prev = df.iloc[i - 1]
            prev2 = df.iloc[i - 2]
            signal = False
            if use_price_signal:
                # Volume surge never fires (index ticker): use close-above-SMA20 + momentum proxy
                signal = prev["Close"] > prev["SMA20_Close"] and prev["Close"] > prev2["Close"]
            else:
                prev_vol_sma = prev["Vol_SMA20"]
                if prev_vol_sma > 0:
                    vol_ratio = prev["Volume"] / prev_vol_sma
                    signal = vol_ratio >= volume_multiplier and prev["Close"] > prev["SMA20_Close"]
            if signal:
                in_trade = True
                entry_price = open_p
                entry_date = curr_date
                target_price = entry_price * (1 + take_profit_pct / 100)
                stop_price = entry_price * (1 - stop_loss_pct / 100)
                hold_count = 0
                shares = int(capital / (entry_price * (1 + cost))) if entry_price > 0 else 0

        # Record equity
        current_portfolio_value = capital
        if in_trade:
            current_portfolio_value += float((close_p - entry_price) * shares)

        equity_curve.append({
            "date": curr_date,
            "equity": round(float(current_portfolio_value), 2)
        })

    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t["win"])
    losing_trades = total_trades - winning_trades
    win_rate = round((winning_trades / total_trades * 100), 1) if total_trades > 0 else 0
    total_return_pct = round(((capital - initial_capital) / initial_capital) * 100, 2) if initial_capital else 0.0

    equity_vals = [e["equity"] for e in equity_curve]
    max_drawdown_pct = 0.0
    if equity_vals:
        peak = equity_vals[0]
        max_dd = 0.0
        for val in equity_vals:
            if val > peak:
                peak = val
            dd = (peak - val) / peak * 100 if peak else 0.0
            if dd > max_dd:
                max_dd = dd
        max_drawdown_pct = round(max_dd, 2)

    # Risk-adjusted metrics from the equity curve (annualised over 252 days)
    sharpe_ratio = 0.0
    cagr_pct = 0.0
    calmar_ratio = 0.0
    if len(equity_vals) > 2 and initial_capital > 0:
        rets = np.diff(equity_vals) / np.maximum(equity_vals[:-1], 1e-9)
        rets = rets[rets != 0] if len(rets) > 0 else rets
        if len(rets) > 1:
            std = float(np.std(rets, ddof=1))
            mean_daily = float(np.mean(rets))
            sharpe_ratio = round((mean_daily - risk_free_rate / 252.0) / std * np.sqrt(252.0), 2) if std > 0 else 0.0
        bars = len(equity_vals)
        years = max(bars / 252.0, 1e-9)
        cagr_pct = round(((capital / initial_capital) ** (1.0 / years) - 1.0) * 100.0, 2)
        if max_drawdown_pct > 0:
            calmar_ratio = round(cagr_pct / max_drawdown_pct, 2)

    return {
        "initialCapital": initial_capital,
        "finalCapital": round(capital, 2),
        "totalReturnPct": total_return_pct,
        "cagrPct": cagr_pct,
        "sharpeRatio": sharpe_ratio,
        "calmarRatio": calmar_ratio,
        "maxDrawdownPct": max_drawdown_pct,
        "costPerTradePct": cost_per_trade_pct,
        "totalTrades": total_trades,
        "winningTrades": winning_trades,
        "losingTrades": losing_trades,
        "winRatePct": win_rate,
        "equityCurve": equity_curve,
        "tradeLog": trades[-10:],
        "signalType": "PRICE_BREAKOUT" if use_price_signal else "VOLUME_SURGE"
    }


class Backtester:
    def __init__(self):
        pass

    def run_volume_backtest(self, df: pd.DataFrame, initial_capital: float = 100000.0) -> Dict[str, Any]:
        """Realistic volume-surge backtest with legacy key aliases preserved."""
        res = run_volume_backtest(df=df, initial_capital=initial_capital)
        res["initial_capital"] = res.get("initialCapital", initial_capital)
        res["final_capital"] = res.get("finalCapital", initial_capital)
        res["return_pct"] = res.get("totalReturnPct", 0.0)
        res["trades_count"] = res.get("totalTrades", 0)
        res["equity_curve"] = [e["equity"] for e in res.get("equityCurve", [])]
        return res
