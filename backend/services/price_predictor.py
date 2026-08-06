"""
Price Prediction & Market Structure Engine v1.0

Adopted from trading_bot's PricePredictor / EnsemblePredictor with honest
naming and quantum_nexus conventions (capitalized OHLCV columns):
  - Feature engineering reuses the real indicator columns computed by
    calculate_indicators() (RSI, MACD, EMA, BB, ATR, VWAP, ...)
  - Pivot points, Fibonacci retracements, Support/Resistance, chart patterns
  - Polynomial trend projection (honest name — the source called this
    'Prophet' while it was really a polyfit; we label it accurately)
  - Optional PyTorch LSTM via lazy import (degraded cleanly when torch is
    not installed — no hard dependency)
  - Ensemble confidence fused with the Learning Brain win probability

All methods are pandas/numpy only (plus optional torch for deep mode).
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime

logger = logging.getLogger("quantum_nexus.price_predictor")


class PricePredictor:
    def __init__(self):
        self.sequence_length = 60
        self.prediction_horizon = 5

    # ── Feature engineering (reuses quantum_nexus indicator columns) ──
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for col in ("Open", "High", "Low", "Close", "Volume"):
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df["Volume"] = df["Volume"].fillna(0)

        close = df["Close"]
        df["returns"] = close.pct_change()
        df["log_returns"] = np.log(close / close.shift(1))

        for window in (5, 10, 20, 50):
            df[f"sma_{window}"] = close.rolling(window=window).mean()
            df[f"ema_{window}"] = close.ewm(span=window, adjust=False).mean()
            df[f"volatility_{window}"] = df["returns"].rolling(window=window).std()

        if "RSI" not in df.columns:
            df["RSI"] = self._rsi(close)
        if "MACD" not in df.columns:
            macd, sig = self._macd(close)
            df["MACD"], df["MACD_Signal"] = macd, sig
        if "ATR" not in df.columns:
            df["ATR"] = self._atr(df)
        if "BB_Upper" not in df.columns:
            up, lo = self._bollinger(close)
            df["BB_Upper"], df["BB_Lower"] = up, lo

        vol_sma = df["Volume"].rolling(window=20).mean().replace(0, np.nan)
        df["volume_ratio"] = (df["Volume"] / vol_sma).fillna(1.0)
        return df

    def _rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss.replace(0, np.nan)
        return (100 - (100 / (1 + rs.fillna(0)))).fillna(50)

    def _bollinger(self, prices: pd.Series, window: int = 20, num_std: float = 2) -> Tuple[pd.Series, pd.Series]:
        middle = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        return middle + (std * num_std), middle - (std * num_std)

    def _macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
        macd = prices.ewm(span=fast, adjust=False).mean() - prices.ewm(span=slow, adjust=False).mean()
        return macd, macd.ewm(span=signal, adjust=False).mean()

    def _atr(self, df: pd.DataFrame, window: int = 14) -> pd.Series:
        hl = df["High"] - df["Low"]
        hc = (df["High"] - df["Close"].shift()).abs()
        lc = (df["Low"] - df["Close"].shift()).abs()
        return pd.concat([hl, hc, lc], axis=1).max(axis=1).rolling(window).mean()

    # ── Market structure analysis ──────────────────────────────
    def analyze_market_structure(self, df: pd.DataFrame) -> Dict:
        df_f = self.prepare_features(df)
        return {
            "pivot_points": self._calculate_pivot_points(df),
            "fibonacci_levels": self._calculate_fibonacci_levels(df),
            "support_resistance": self._find_support_resistance(df),
            "chart_pattern": self._detect_chart_pattern(df),
            "market_structure": self._determine_market_structure(df_f),
            "timestamp": datetime.now().isoformat(),
        }

    def _calculate_pivot_points(self, df: pd.DataFrame) -> Dict:
        high = float(df["High"].iloc[-1])
        low = float(df["Low"].iloc[-1])
        close = float(df["Close"].iloc[-1])
        pivot = (high + low + close) / 3
        return {
            "pivot": round(pivot, 2),
            "r1": round(2 * pivot - low, 2),
            "r2": round(pivot + (high - low), 2),
            "r3": round(high + 2 * (pivot - low), 2),
            "s1": round(2 * pivot - high, 2),
            "s2": round(pivot - (high - low), 2),
            "s3": round(low - 2 * (high - pivot), 2),
        }

    def _calculate_fibonacci_levels(self, df: pd.DataFrame) -> Dict:
        high = float(df["High"].tail(50).max())
        low = float(df["Low"].tail(50).min())
        diff = high - low
        return {f"fib_{name}": round(low + diff * ratio, 2)
                for ratio, name in zip([0, 0.236, 0.382, 0.5, 0.618, 0.786, 1],
                                       ["0", "23.6", "38.2", "50", "61.8", "78.6", "100"])}

    def _find_support_resistance(self, df: pd.DataFrame) -> Dict:
        prices = df["Close"].values
        levels = []
        for i in range(2, len(prices) - 2):
            if prices[i] > prices[i - 1] and prices[i] > prices[i - 2] and \
               prices[i] > prices[i + 1] and prices[i] > prices[i + 2]:
                levels.append(("resistance", prices[i]))
            elif prices[i] < prices[i - 1] and prices[i] < prices[i - 2] and \
                 prices[i] < prices[i + 1] and prices[i] < prices[i + 2]:
                levels.append(("support", prices[i]))
        resistance = sorted((r for t, r in levels if t == "resistance"), reverse=True)[:3]
        support = sorted((s for t, s in levels if t == "support"))[:3]
        current = float(df["Close"].iloc[-1])
        nearest_support = max([s for s in support if s < current], default=current * 0.98)
        nearest_resistance = min([r for r in resistance if r > current], default=current * 1.02)
        return {
            "resistance_levels": [round(r, 2) for r in resistance],
            "support_levels": [round(s, 2) for s in support],
            "nearest_support": round(nearest_support, 2),
            "nearest_resistance": round(nearest_resistance, 2),
        }

    def _detect_chart_pattern(self, df: pd.DataFrame) -> str:
        if len(df) < 20:
            return "insufficient_data"
        recent = df.tail(20)
        highs = recent["High"].values
        lows = recent["Low"].values

        higher_highs = sum(1 for i in range(1, len(highs) - 1) if highs[i] > highs[i - 1] and highs[i] > highs[i + 1])
        lower_highs = sum(1 for i in range(1, len(highs) - 1) if highs[i] < highs[i - 1] and highs[i] < highs[i + 1])
        higher_lows = sum(1 for i in range(1, len(lows) - 1) if lows[i] > lows[i - 1] and lows[i] > lows[i + 1])
        lower_lows = sum(1 for i in range(1, len(lows) - 1) if lows[i] < lows[i - 1] and lows[i] < lows[i + 1])

        if higher_highs >= 3 and higher_lows >= 3:
            return "ascending_triangle"
        if lower_highs >= 3 and lower_lows >= 3:
            return "descending_triangle"
        if abs(higher_highs - lower_highs) <= 1 and abs(higher_lows - lower_lows) <= 1:
            return "rectangle"
        if higher_highs > lower_highs and higher_lows > lower_lows:
            return "bullish_flag"
        if lower_highs > higher_highs and lower_lows > higher_lows:
            return "bearish_flag"
        if higher_highs > 3 and higher_lows > 3:
            return "double_top"
        if lower_highs > 3 and lower_lows > 3:
            return "double_bottom"
        return "no_clear_pattern"

    def _determine_market_structure(self, df: pd.DataFrame) -> str:
        if len(df) < 20:
            return "unknown"
        current = float(df["Close"].iloc[-1])
        if "EMA9" in df.columns and "EMA21" in df.columns and "EMA50" in df.columns:
            e9, e21, e50 = float(df["EMA9"].iloc[-1]), float(df["EMA21"].iloc[-1]), float(df["EMA50"].iloc[-1])
        else:
            e9 = float(df["Close"].ewm(span=9, adjust=False).mean().iloc[-1])
            e21 = float(df["Close"].ewm(span=21, adjust=False).mean().iloc[-1])
            e50 = float(df["Close"].ewm(span=50, adjust=False).mean().iloc[-1])
        if e9 > e21 > e50 and current > e9:
            return "strong_bullish"
        if e9 < e21 < e50 and current < e9:
            return "strong_bearish"
        if e9 > e21:
            return "bullish"
        if e9 < e21:
            return "bearish"
        return "neutral"

    # ── Trend projection (honest polynomial fit) ───────────────
    def predict_trend(self, df: pd.DataFrame, days: int = 5) -> Dict:
        if len(df) < 30:
            return {"error": "Insufficient data for trend prediction"}
        close = df["Close"].values
        x = np.arange(len(close))
        coeffs = np.polyfit(x, close, 2)
        poly = np.poly1d(coeffs)
        future_x = np.arange(len(close), len(close) + days)
        predictions = poly(future_x)

        last = float(close[-1])
        direction = "upward" if predictions[-1] > last else "downward"
        volatility = np.std(np.diff(close)) / np.mean(close) * 100 if len(close) > 1 else 0.0
        confidence = max(0.0, min(100.0, 100.0 - volatility * 10))
        return {
            "trend": direction,
            "predictions": [round(p, 2) for p in predictions.tolist()],
            "confidence": round(confidence, 2),
            "daily_change_pct": round((predictions[-1] - last) / last * 100, 2),
            "volatility": round(volatility, 2),
            "period_days": days,
        }

    # ── Ensemble prediction ─────────────────────────────────────
    def predict_next_candles(self, df: pd.DataFrame, num_predictions: int = 5, ai_confidence: float = 75.0) -> Dict:
        if df is None or len(df) < 20:
            return {"error": "Insufficient data for prediction"}

        structure = self.analyze_market_structure(df)
        trend = self.predict_trend(df, days=num_predictions)
        if "error" in trend:
            return {"error": trend["error"]}

        structure_dir = structure["market_structure"]
        structure_bullish = "bull" in structure_dir
        trend_bullish = trend["trend"] == "upward"

        directions = sum([trend_bullish, structure_bullish])
        if directions == 2:
            final_direction = "strong_bullish"
        elif directions == 0:
            final_direction = "strong_bearish"
        else:
            final_direction = "mixed"

        confidence = round((float(trend["confidence"]) * 0.5 + float(ai_confidence) * 0.5), 2)
        if final_direction == "mixed":
            confidence = round(min(confidence, 55.0), 2)
        recommendation = self._generate_recommendation(final_direction, confidence)

        predictions = [round(p, 2) for p in trend.get("predictions", [])]
        last_close = float(df["Close"].iloc[-1])

        return {
            "current_price": round(last_close, 2),
            "predictions": predictions,
            "direction": final_direction,
            "confidence": confidence,
            "recommendation": recommendation,
            "trend_projection": trend,
            "market_structure": structure,
            "ai_confidence": ai_confidence,
            "lstm_available": self.lstm_available(),
            "timestamp": datetime.now().isoformat(),
        }

    def _generate_recommendation(self, direction: str, confidence: float) -> str:
        if direction == "mixed":
            return "HOLD"
        if "bear" in direction:
            return "STRONG_SELL" if confidence >= 70 else "SELL" if confidence >= 50 else "HOLD"
        return "STRONG_BUY" if confidence >= 70 else "BUY" if confidence >= 50 else "HOLD"

    # ── Optional PyTorch LSTM (lazy import) ─────────────────────
    def lstm_available(self) -> bool:
        try:
            import torch  # noqa: F401
            return True
        except ImportError:
            return False

    def predict_lstm(self, df: pd.DataFrame, window_size: int = 60, epochs: int = 30) -> Dict:
        """
        Train a small LSTM on the fly and forecast the next candles.
        Only usable when PyTorch is installed; otherwise returns a clear error.
        """
        if not self.lstm_available():
            return {"error": "PyTorch not installed. Run: pip install torch", "available": False}
        try:
            import torch
            import torch.nn as nn
        except ImportError as e:
            return {"error": str(e), "available": False}

        close = df["Close"].values.reshape(-1, 1).astype(np.float32)
        if len(close) < window_size + 5:
            return {"error": "Insufficient data for LSTM", "available": True}

        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        scaled = scaler.fit_transform(close).flatten()

        X, y = [], []
        for i in range(len(scaled) - window_size - 1):
            X.append(scaled[i:i + window_size])
            y.append(scaled[i + window_size])
        X, y = np.array(X), np.array(y)
        split = int(len(X) * 0.8)
        X_train, y_train = torch.tensor(X[:split]).unsqueeze(-1), torch.tensor(y[:split]).unsqueeze(1)
        X_test, y_test = torch.tensor(X[split:]).unsqueeze(-1), torch.tensor(y[split:]).unsqueeze(1)

        class _LSTM(nn.Module):
            def __init__(self):
                super().__init__()
                self.lstm = nn.LSTM(1, 64, 2, batch_first=True, dropout=0.2)
                self.fc = nn.Linear(64, 1)

            def forward(self, x):
                out, _ = self.lstm(x)
                return self.fc(out[:, -1, :])

        model = _LSTM()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
        criterion = nn.MSELoss()
        for epoch in range(epochs):
            model.train()
            optimizer.zero_grad()
            loss = criterion(model(X_train), y_train)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            last_seq = torch.tensor(scaled[-window_size:]).unsqueeze(0).unsqueeze(-1)
            forecast = []
            seq = last_seq.clone()
            for _ in range(self.prediction_horizon):
                pred = model(seq).item()
                forecast.append(pred)
                seq = torch.cat([seq[:, 1:, :], torch.tensor([[[pred]]])], dim=1)
            dummy = np.zeros((len(forecast), 1))
            dummy[:, 0] = forecast
            forecast_prices = scaler.inverse_transform(dummy)[:, 0].tolist()

        return {
            "available": True,
            "model": "LSTM (2-layer, hidden=64)",
            "train_loss": round(float(loss.item()), 6),
            "predictions": [round(p, 2) for p in forecast_prices],
            "direction": "bullish" if forecast_prices[-1] > close[-1][0] else "bearish",
            "timestamp": datetime.now().isoformat(),
        }


# Global Predictor Instance
price_predictor = PricePredictor()
