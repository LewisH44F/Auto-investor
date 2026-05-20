"""Technical analysis service using pandas. No external TA library required."""
from __future__ import annotations

from typing import Optional
import pandas as pd
import numpy as np
from loguru import logger


class TechnicalAnalyzer:
    """Computes indicators and a composite technical score (0-100)."""

    def analyze(self, df: pd.DataFrame) -> dict:
        """Full analysis on a daily OHLCV DataFrame. Returns indicator dict + score."""
        if df is None or len(df) < 20:
            return self._empty_result()
        try:
            df = df.copy()
            df.columns = [c.capitalize() for c in df.columns]
            close = df["Close"]
            high = df["High"]
            low = df["Low"]
            volume = df["Volume"]

            result = {}
            result.update(self._rsi(close))
            result.update(self._macd(close))
            result.update(self._bollinger(close))
            result.update(self._ema(close))
            result.update(self._atr(high, low, close))
            result.update(self._volume_analysis(volume, close))
            result.update(self._support_resistance(high, low, close))
            result["composite_score"] = self._composite_score(result, close)
            result["trend"] = self._trend_label(result)
            result["breakout"] = self._detect_breakout(result, close, volume)
            result["entry_zone_low"] = round(float(close.iloc[-1]) * 0.99, 2)
            result["entry_zone_high"] = round(float(close.iloc[-1]) * 1.005, 2)
            result["stop_loss"] = round(float(result.get("support", close.iloc[-1] * 0.93)), 2)
            result["profit_target_1"] = round(float(close.iloc[-1]) * 1.05, 2)
            result["profit_target_2"] = round(float(close.iloc[-1]) * 1.10, 2)
            return result
        except Exception as e:
            logger.warning("Technical analysis error: {}", e)
            return self._empty_result()

    # ── Indicators ────────────────────────────────────────────────────────────

    def _rsi(self, close: pd.Series, period: int = 14) -> dict:
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        val = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
        return {"rsi": round(val, 2)}

    def _macd(self, close: pd.Series) -> dict:
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        hist = macd - signal
        return {
            "macd": round(float(macd.iloc[-1]), 4),
            "macd_signal": round(float(signal.iloc[-1]), 4),
            "macd_hist": round(float(hist.iloc[-1]), 4),
            "macd_bullish": bool(hist.iloc[-1] > 0 and hist.iloc[-1] > hist.iloc[-2]),
        }

    def _bollinger(self, close: pd.Series, period: int = 20, std: float = 2.0) -> dict:
        mid = close.rolling(period).mean()
        sd = close.rolling(period).std()
        upper = mid + std * sd
        lower = mid - std * sd
        price = float(close.iloc[-1])
        m = float(mid.iloc[-1])
        u = float(upper.iloc[-1])
        l = float(lower.iloc[-1])
        bw = (u - l) / m if m else 0
        pct_b = (price - l) / (u - l) if (u - l) else 0.5
        return {
            "bb_upper": round(u, 2),
            "bb_mid": round(m, 2),
            "bb_lower": round(l, 2),
            "bb_bandwidth": round(bw, 4),
            "bb_pct_b": round(pct_b, 4),
            "bb_squeeze": bw < 0.1,
        }

    def _ema(self, close: pd.Series) -> dict:
        price = float(close.iloc[-1])
        res = {}
        for span in [9, 21, 50, 200]:
            ema = float(close.ewm(span=span, adjust=False).mean().iloc[-1])
            res[f"ema_{span}"] = round(ema, 2)
            res[f"above_ema_{span}"] = price > ema
        return res

    def _atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> dict:
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ], axis=1).max(axis=1)
        atr = float(tr.rolling(period).mean().iloc[-1])
        atr_pct = atr / float(close.iloc[-1]) * 100 if close.iloc[-1] else 0
        return {"atr": round(atr, 2), "atr_pct": round(atr_pct, 2)}

    def _volume_analysis(self, volume: pd.Series, close: pd.Series) -> dict:
        avg_vol = float(volume.rolling(20).mean().iloc[-1])
        curr_vol = float(volume.iloc[-1])
        rel_vol = curr_vol / avg_vol if avg_vol else 1.0
        # OBV
        obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
        return {
            "avg_volume_20d": int(avg_vol),
            "current_volume": int(curr_vol),
            "relative_volume": round(rel_vol, 2),
            "unusual_volume": rel_vol > 2.0,
            "obv": float(obv.iloc[-1]),
            "obv_trending_up": float(obv.iloc[-1]) > float(obv.iloc[-5]) if len(obv) >= 5 else True,
        }

    def _support_resistance(self, high: pd.Series, low: pd.Series, close: pd.Series) -> dict:
        lookback = min(20, len(close))
        recent_highs = high.iloc[-lookback:]
        recent_lows = low.iloc[-lookback:]
        resistance = float(recent_highs.max())
        support = float(recent_lows.min())
        price = float(close.iloc[-1])
        pct_from_resistance = (resistance - price) / price * 100
        pct_from_support = (price - support) / price * 100
        return {
            "resistance": round(resistance, 2),
            "support": round(support, 2),
            "pct_from_resistance": round(pct_from_resistance, 2),
            "pct_from_support": round(pct_from_support, 2),
        }

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _composite_score(self, r: dict, close: pd.Series) -> float:
        score = 50.0

        # RSI: 30-50 = bullish setup, 50-70 = momentum, >70 = overbought
        rsi = r.get("rsi", 50)
        if 40 <= rsi <= 60:
            score += 5
        elif 60 < rsi <= 70:
            score += 10
        elif rsi < 35:
            score += 8   # oversold bounce potential
        elif rsi > 75:
            score -= 10  # overbought

        # MACD
        if r.get("macd_bullish"):
            score += 10
        elif r.get("macd_hist", 0) < 0:
            score -= 8

        # EMA alignment
        above_count = sum(1 for span in [9, 21, 50, 200] if r.get(f"above_ema_{span}", False))
        score += above_count * 4  # up to +16

        # Bollinger
        pct_b = r.get("bb_pct_b", 0.5)
        if 0.4 <= pct_b <= 0.7:
            score += 5
        elif pct_b > 0.95:
            score -= 8
        if r.get("bb_squeeze"):
            score += 6  # potential breakout

        # Volume
        rel_vol = r.get("relative_volume", 1.0)
        if rel_vol > 1.5:
            score += 5
        if rel_vol > 2.5:
            score += 5

        # OBV trend
        if r.get("obv_trending_up"):
            score += 5

        return round(min(100.0, max(0.0, score)), 1)

    def _trend_label(self, r: dict) -> str:
        above_emas = sum(1 for span in [21, 50, 200] if r.get(f"above_ema_{span}", False))
        if above_emas == 3:
            return "STRONG BULLISH"
        elif above_emas == 2:
            return "BULLISH"
        elif above_emas == 1:
            return "NEUTRAL"
        else:
            return "BEARISH"

    def _detect_breakout(self, r: dict, close: pd.Series, volume: pd.Series) -> bool:
        price = float(close.iloc[-1])
        resistance = r.get("resistance", price * 1.1)
        rel_vol = r.get("relative_volume", 1.0)
        near_breakout = price >= resistance * 0.98
        volume_confirm = rel_vol > 1.5
        return near_breakout and volume_confirm

    def _empty_result(self) -> dict:
        return {
            "rsi": 50.0, "macd": 0.0, "macd_signal": 0.0, "macd_hist": 0.0,
            "macd_bullish": False, "bb_upper": 0.0, "bb_mid": 0.0, "bb_lower": 0.0,
            "bb_bandwidth": 0.0, "bb_pct_b": 0.5, "bb_squeeze": False,
            "ema_9": 0.0, "ema_21": 0.0, "ema_50": 0.0, "ema_200": 0.0,
            "above_ema_9": False, "above_ema_21": False, "above_ema_50": False, "above_ema_200": False,
            "atr": 0.0, "atr_pct": 0.0, "avg_volume_20d": 0, "current_volume": 0,
            "relative_volume": 1.0, "unusual_volume": False,
            "resistance": 0.0, "support": 0.0, "pct_from_resistance": 0.0, "pct_from_support": 0.0,
            "composite_score": 50.0, "trend": "NEUTRAL", "breakout": False,
            "entry_zone_low": 0.0, "entry_zone_high": 0.0,
            "stop_loss": 0.0, "profit_target_1": 0.0, "profit_target_2": 0.0,
            "obv": 0.0, "obv_trending_up": False,
        }
