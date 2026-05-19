"""Feature engineering for ML models."""

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger


class FeatureEngineer:
    """Build 50+ features from OHLCV, indicators, sentiment, and macro data."""

    def compute_ohlcv_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Compute OHLCV-derived features."""
        if df is None or len(df) < 20:
            return {}

        close = df["Close"]
        high = df["High"] if "High" in df.columns else close
        low = df["Low"] if "Low" in df.columns else close
        volume = df["Volume"] if "Volume" in df.columns else pd.Series([0] * len(df))
        open_ = df["Open"] if "Open" in df.columns else close

        feats: Dict[str, float] = {}

        # Price returns
        feats["return_1d"] = float((close.iloc[-1] / close.iloc[-2] - 1) * 100) if len(close) >= 2 else 0.0
        feats["return_5d"] = float((close.iloc[-1] / close.iloc[-6] - 1) * 100) if len(close) >= 6 else 0.0
        feats["return_20d"] = float((close.iloc[-1] / close.iloc[-21] - 1) * 100) if len(close) >= 21 else 0.0
        feats["return_60d"] = float((close.iloc[-1] / close.iloc[-61] - 1) * 100) if len(close) >= 61 else 0.0

        # Volatility
        returns = close.pct_change().dropna()
        feats["volatility_20d"] = float(returns.tail(20).std() * np.sqrt(252) * 100)
        feats["volatility_5d"] = float(returns.tail(5).std() * np.sqrt(252) * 100)

        # Volume features
        avg_vol_20 = volume.tail(20).mean()
        feats["relative_volume"] = float(volume.iloc[-1] / avg_vol_20) if avg_vol_20 > 0 else 1.0
        feats["volume_trend"] = float(volume.tail(5).mean() / avg_vol_20) if avg_vol_20 > 0 else 1.0

        # Price position
        high_20 = high.tail(20).max()
        low_20 = low.tail(20).min()
        price_range = high_20 - low_20
        feats["price_position_20d"] = float(
            (close.iloc[-1] - low_20) / price_range * 100
        ) if price_range > 0 else 50.0

        # Gap
        feats["gap_pct"] = float(
            (open_.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100
        ) if len(close) >= 2 else 0.0

        # ATR-based volatility
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs(),
        ], axis=1).max(axis=1)
        atr = tr.ewm(com=13, adjust=False).mean().iloc[-1]
        feats["atr_pct"] = float(atr / close.iloc[-1] * 100) if close.iloc[-1] > 0 else 0.0

        # Candlestick body ratio
        body = (close.iloc[-1] - open_.iloc[-1]).abs()
        candle_range = high.iloc[-1] - low.iloc[-1]
        feats["body_ratio"] = float(body / candle_range) if candle_range > 0 else 0.5

        return feats

    def compute_technical_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Extract features from technical indicators."""
        from app.services.analysis.technical_analysis import TechnicalAnalyzer

        analyzer = TechnicalAnalyzer()
        df_ind = analyzer.compute_indicators(df.copy())

        if df_ind is None or len(df_ind) == 0:
            return {}

        last = df_ind.iloc[-1]
        feats: Dict[str, float] = {}

        def safe_float(val) -> float:
            try:
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    return 0.0
                return float(val)
            except Exception:
                return 0.0

        feats["rsi_14"] = safe_float(last.get("RSI"))
        feats["macd_hist"] = safe_float(last.get("MACD_hist"))
        feats["macd_above_signal"] = 1.0 if safe_float(last.get("MACD", 0)) > safe_float(last.get("MACD_signal", 0)) else 0.0

        # BB position
        bb_upper = safe_float(last.get("BB_upper"))
        bb_lower = safe_float(last.get("BB_lower"))
        close = safe_float(last.get("Close"))
        if bb_upper > bb_lower:
            feats["bb_position"] = (close - bb_lower) / (bb_upper - bb_lower) * 100
        else:
            feats["bb_position"] = 50.0

        # EMA relationships
        ema9 = safe_float(last.get("EMA_9"))
        ema21 = safe_float(last.get("EMA_21"))
        ema50 = safe_float(last.get("EMA_50"))
        ema200 = safe_float(last.get("EMA_200"))

        feats["price_vs_ema50"] = (close / ema50 - 1) * 100 if ema50 > 0 else 0.0
        feats["price_vs_ema200"] = (close / ema200 - 1) * 100 if ema200 > 0 else 0.0
        feats["ema9_vs_ema21"] = (ema9 / ema21 - 1) * 100 if ema21 > 0 else 0.0
        feats["ema50_vs_ema200"] = (ema50 / ema200 - 1) * 100 if ema200 > 0 else 0.0
        feats["golden_cross"] = 1.0 if ema50 > ema200 else 0.0

        # Stochastic
        feats["stoch_k"] = safe_float(last.get("Stoch_K"))
        feats["stoch_oversold"] = 1.0 if safe_float(last.get("Stoch_K", 50)) < 20 else 0.0
        feats["stoch_overbought"] = 1.0 if safe_float(last.get("Stoch_K", 50)) > 80 else 0.0

        return feats

    def build_feature_vector(
        self,
        df: Optional[pd.DataFrame] = None,
        technical_analysis: Optional[Dict[str, Any]] = None,
        sentiment_data: Optional[Dict[str, Any]] = None,
        catalyst_data: Optional[Dict[str, Any]] = None,
        macro_data: Optional[Dict[str, Any]] = None,
        fundamental_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """Build the complete feature vector for a prediction."""
        features: Dict[str, float] = {}

        # OHLCV features
        if df is not None and not df.empty:
            features.update(self.compute_ohlcv_features(df))
            features.update(self.compute_technical_features(df))

        # Technical analysis aggregate
        if technical_analysis:
            features["technical_score"] = float(technical_analysis.get("score", 50))
            features["is_breakout"] = 1.0 if technical_analysis.get("breakout") else 0.0
            features["gap_up"] = 1.0 if float(technical_analysis.get("gap_pct", 0)) > 1.0 else 0.0
            features["gap_down"] = 1.0 if float(technical_analysis.get("gap_pct", 0)) < -1.0 else 0.0
            trend = technical_analysis.get("trend", "neutral")
            features["trend_bullish"] = 1.0 if trend == "bullish" else 0.0
            features["trend_bearish"] = 1.0 if trend == "bearish" else 0.0

        # Sentiment features
        if sentiment_data:
            features["sentiment_score"] = float(sentiment_data.get("score", 0))
            features["sentiment_normalized"] = float(sentiment_data.get("normalized_score", 50))
            features["sentiment_improving"] = 1.0 if sentiment_data.get("momentum") == "improving" else 0.0
            features["sentiment_deteriorating"] = 1.0 if sentiment_data.get("momentum") == "deteriorating" else 0.0
            features["news_score"] = float(sentiment_data.get("news_score", 0))
            features["social_score"] = float(sentiment_data.get("social_score", 0))
            features["article_count"] = float(sentiment_data.get("article_count", 0))

        # Catalyst features
        if catalyst_data:
            features["catalyst_score"] = float(catalyst_data.get("score", 0))
            features["catalyst_bullish"] = 1.0 if catalyst_data.get("is_bullish") else 0.0
            features["catalyst_count"] = float(catalyst_data.get("count", 0))
            features["has_earnings_catalyst"] = 1.0 if any(
                "earnings" in t for t in catalyst_data.get("all_types", [])
            ) else 0.0
            features["has_fda_catalyst"] = 1.0 if any(
                "fda" in t for t in catalyst_data.get("all_types", [])
            ) else 0.0
            features["has_ma_catalyst"] = 1.0 if any(
                "merger" in t for t in catalyst_data.get("all_types", [])
            ) else 0.0

        # Macro features
        if macro_data:
            features["macro_score"] = float(macro_data.get("macro_score", 50))
            features["vix"] = float(macro_data.get("vix") or 20)
            features["spy_change"] = float(macro_data.get("spy_change_pct") or 0)
            features["qqq_change"] = float(macro_data.get("qqq_change_pct") or 0)

        # Fundamental features
        if fundamental_data:
            features["fundamental_score"] = float(fundamental_data.get("score", 50))
            features["pe_ratio"] = float(fundamental_data.get("pe_ratio") or 0)
            features["revenue_growth"] = float(fundamental_data.get("revenue_growth") or 0) * 100

        return features

    def normalize_features(
        self, features: Dict[str, float]
    ) -> Dict[str, float]:
        """Min-max normalization for model input."""
        # Most features are already in [0, 100] or [-1, 1] range
        # Apply soft clipping for outliers
        normalized = {}
        for key, val in features.items():
            try:
                v = float(val)
                # Clip extreme values
                v = max(-200.0, min(200.0, v))
                normalized[key] = v
            except (TypeError, ValueError):
                normalized[key] = 0.0
        return normalized

    def to_array(self, features: Dict[str, float], feature_names: List[str]) -> np.ndarray:
        """Convert feature dict to numpy array in consistent order."""
        return np.array([features.get(name, 0.0) for name in feature_names], dtype=np.float32)
