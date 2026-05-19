"""Technical analysis service using pandas-ta."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from loguru import logger

try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
except ImportError:
    logger.warning("pandas-ta not available, using manual calculations")
    PANDAS_TA_AVAILABLE = False


class TechnicalAnalyzer:
    """Compute technical indicators and derive a composite score."""

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicator columns to the OHLCV dataframe."""
        if df is None or len(df) < 20:
            return df

        close = df["Close"]
        high = df["High"] if "High" in df.columns else close
        low = df["Low"] if "Low" in df.columns else close
        volume = df["Volume"] if "Volume" in df.columns else pd.Series([0] * len(df))

        if PANDAS_TA_AVAILABLE:
            # RSI
            df["RSI"] = ta.rsi(close, length=14)

            # MACD
            macd = ta.macd(close, fast=12, slow=26, signal=9)
            if macd is not None:
                df["MACD"] = macd.get("MACD_12_26_9")
                df["MACD_signal"] = macd.get("MACDs_12_26_9")
                df["MACD_hist"] = macd.get("MACDh_12_26_9")

            # Bollinger Bands
            bb = ta.bbands(close, length=20)
            if bb is not None:
                df["BB_upper"] = bb.get("BBU_20_2.0")
                df["BB_mid"] = bb.get("BBM_20_2.0")
                df["BB_lower"] = bb.get("BBL_20_2.0")
                df["BB_pct"] = bb.get("BBP_20_2.0")

            # EMAs
            df["EMA_9"] = ta.ema(close, length=9)
            df["EMA_21"] = ta.ema(close, length=21)
            df["EMA_50"] = ta.ema(close, length=50)
            df["EMA_200"] = ta.ema(close, length=200)

            # ATR
            df["ATR"] = ta.atr(high, low, close, length=14)

            # Volume SMA
            df["Vol_SMA_20"] = ta.sma(volume, length=20)

            # Stochastic
            stoch = ta.stoch(high, low, close)
            if stoch is not None:
                df["Stoch_K"] = stoch.get("STOCHk_14_3_3")
                df["Stoch_D"] = stoch.get("STOCHd_14_3_3")

            # OBV
            df["OBV"] = ta.obv(close, volume)

        else:
            # Manual fallback calculations
            delta = close.diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.ewm(com=13, adjust=False).mean()
            avg_loss = loss.ewm(com=13, adjust=False).mean()
            rs = avg_gain / avg_loss.replace(0, np.nan)
            df["RSI"] = 100 - (100 / (1 + rs))

            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            df["MACD"] = ema12 - ema26
            df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
            df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

            sma20 = close.rolling(20).mean()
            std20 = close.rolling(20).std()
            df["BB_upper"] = sma20 + 2 * std20
            df["BB_mid"] = sma20
            df["BB_lower"] = sma20 - 2 * std20

            df["EMA_9"] = close.ewm(span=9, adjust=False).mean()
            df["EMA_21"] = close.ewm(span=21, adjust=False).mean()
            df["EMA_50"] = close.ewm(span=50, adjust=False).mean()
            df["EMA_200"] = close.ewm(span=200, adjust=False).mean()

            tr = pd.concat([
                high - low,
                (high - close.shift()).abs(),
                (low - close.shift()).abs(),
            ], axis=1).max(axis=1)
            df["ATR"] = tr.ewm(com=13, adjust=False).mean()

            df["Vol_SMA_20"] = volume.rolling(20).mean()

        return df

    def detect_trend(self, df: pd.DataFrame) -> str:
        """Identify bullish/bearish/neutral trend."""
        if df is None or len(df) < 50:
            return "neutral"

        last = df.iloc[-1]
        close = last.get("Close", 0)
        ema_50 = last.get("EMA_50")
        ema_200 = last.get("EMA_200")
        ema_21 = last.get("EMA_21")
        ema_9 = last.get("EMA_9")

        if ema_50 is None or ema_200 is None:
            return "neutral"

        bullish_signals = 0
        bearish_signals = 0

        # Golden/Death cross
        if ema_50 > ema_200:
            bullish_signals += 2
        else:
            bearish_signals += 2

        # Price vs EMA
        if close > ema_50:
            bullish_signals += 1
        else:
            bearish_signals += 1

        if ema_9 and ema_21:
            if ema_9 > ema_21:
                bullish_signals += 1
            else:
                bearish_signals += 1

        if bullish_signals > bearish_signals + 1:
            return "bullish"
        elif bearish_signals > bullish_signals + 1:
            return "bearish"
        return "neutral"

    def detect_breakout(self, df: pd.DataFrame, lookback: int = 20) -> bool:
        """Detect price breakout above recent resistance."""
        if df is None or len(df) < lookback + 1:
            return False

        recent = df.tail(lookback + 1)
        current_close = recent["Close"].iloc[-1]
        prior_high = recent["High"].iloc[:-1].max() if "High" in recent.columns else recent["Close"].iloc[:-1].max()

        return bool(current_close > prior_high * 1.005)

    def detect_gap(self, df: pd.DataFrame) -> float:
        """Detect gap-up or gap-down as percentage."""
        if df is None or len(df) < 2:
            return 0.0

        today_open = df["Open"].iloc[-1] if "Open" in df.columns else df["Close"].iloc[-1]
        yesterday_close = df["Close"].iloc[-2]

        if yesterday_close <= 0:
            return 0.0

        return (today_open - yesterday_close) / yesterday_close * 100

    def find_support_resistance(
        self, df: pd.DataFrame, window: int = 10
    ) -> Tuple[float, float]:
        """Find nearest support and resistance levels."""
        if df is None or len(df) < window * 2:
            close = df["Close"].iloc[-1] if df is not None and len(df) > 0 else 100.0
            return close * 0.95, close * 1.05

        highs = df["High"] if "High" in df.columns else df["Close"]
        lows = df["Low"] if "Low" in df.columns else df["Close"]

        # Simple pivot-based support/resistance
        pivots_high = highs[
            (highs.shift(window) < highs) & (highs.shift(-window) < highs)
        ]
        pivots_low = lows[
            (lows.shift(window) > lows) & (lows.shift(-window) > lows)
        ]

        current_price = df["Close"].iloc[-1]

        resistance = (
            pivots_high[pivots_high > current_price].min()
            if not pivots_high[pivots_high > current_price].empty
            else current_price * 1.05
        )
        support = (
            pivots_low[pivots_low < current_price].max()
            if not pivots_low[pivots_low < current_price].empty
            else current_price * 0.95
        )

        return float(support), float(resistance)

    def calculate_composite_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate composite technical score (0-100).
        Returns dict with score, components, and entry zone.
        """
        if df is None or len(df) < 20:
            return {
                "score": 50.0,
                "trend": "neutral",
                "components": {},
                "entry_zone_low": None,
                "entry_zone_high": None,
                "stop_loss": None,
                "breakout": False,
                "gap_pct": 0.0,
            }

        df_with_indicators = self.compute_indicators(df.copy())
        last = df_with_indicators.iloc[-1]

        close = float(last.get("Close", 100))
        rsi = last.get("RSI")
        macd = last.get("MACD")
        macd_sig = last.get("MACD_signal")
        macd_hist = last.get("MACD_hist")
        bb_pct = last.get("BB_pct")
        ema_9 = last.get("EMA_9")
        ema_21 = last.get("EMA_21")
        ema_50 = last.get("EMA_50")
        ema_200 = last.get("EMA_200")
        atr = last.get("ATR")
        vol_sma = last.get("Vol_SMA_20")

        components: Dict[str, float] = {}
        total_weight = 0.0
        weighted_score = 0.0

        # RSI Score (ideal: 50-70 for longs)
        if rsi is not None and not np.isnan(rsi):
            if 50 <= rsi <= 70:
                rsi_score = 80.0
            elif 30 <= rsi < 50:
                rsi_score = 60.0
            elif rsi > 70:
                rsi_score = 40.0  # overbought
            else:
                rsi_score = 20.0  # oversold
            components["rsi"] = rsi_score
            weighted_score += rsi_score * 0.20
            total_weight += 0.20

        # MACD Score
        if macd is not None and macd_sig is not None and not (np.isnan(macd) or np.isnan(macd_sig)):
            macd_score = 70.0 if macd > macd_sig else 30.0
            if macd_hist and not np.isnan(macd_hist) and macd_hist > 0:
                macd_score = min(macd_score + 10, 90.0)
            components["macd"] = macd_score
            weighted_score += macd_score * 0.20
            total_weight += 0.20

        # Trend (EMA stack)
        trend = self.detect_trend(df_with_indicators)
        trend_score = {"bullish": 80.0, "neutral": 50.0, "bearish": 20.0}[trend]
        components["trend"] = trend_score
        weighted_score += trend_score * 0.25
        total_weight += 0.25

        # Breakout
        breakout = self.detect_breakout(df_with_indicators)
        breakout_score = 85.0 if breakout else 45.0
        components["breakout"] = breakout_score
        weighted_score += breakout_score * 0.15
        total_weight += 0.15

        # Volume
        volume = float(df_with_indicators["Volume"].iloc[-1]) if "Volume" in df_with_indicators.columns else 0.0
        if vol_sma and not np.isnan(vol_sma) and vol_sma > 0:
            rel_vol = volume / vol_sma
            vol_score = min(100.0, rel_vol * 50)
        else:
            vol_score = 50.0
        components["volume"] = vol_score
        weighted_score += vol_score * 0.20
        total_weight += 0.20

        composite = (weighted_score / total_weight) if total_weight > 0 else 50.0
        composite = max(0.0, min(100.0, composite))

        # Entry zone calculation
        atr_val = float(atr) if atr and not np.isnan(atr) else close * 0.02
        entry_low = round(close - atr_val * 0.5, 2)
        entry_high = round(close + atr_val * 0.3, 2)
        stop_loss = round(close - atr_val * 2.0, 2)

        support, resistance = self.find_support_resistance(df_with_indicators)
        gap_pct = self.detect_gap(df_with_indicators)

        return {
            "score": round(composite, 2),
            "trend": trend,
            "components": components,
            "entry_zone_low": max(entry_low, support * 0.98),
            "entry_zone_high": entry_high,
            "stop_loss": stop_loss,
            "support": support,
            "resistance": resistance,
            "breakout": breakout,
            "gap_pct": gap_pct,
            "rsi": float(rsi) if rsi and not np.isnan(rsi) else None,
            "atr": float(atr_val),
        }

    async def analyze(self, ticker: str, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Main async entry point for technical analysis."""
        if df is None:
            from app.services.data_ingestion.market_data import MarketDataService
            market_svc = MarketDataService()
            df = await market_svc.fetch_ohlcv(ticker, period="6mo", interval="1d")

        if df is None or df.empty:
            logger.warning("No price data for technical analysis of {}", ticker)
            return {"score": 50.0, "trend": "neutral"}

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.calculate_composite_score, df)
        return result
