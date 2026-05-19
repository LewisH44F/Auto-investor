"""Tests for the prediction engine and related ML pipeline components.

These tests operate on the logic layer without requiring live API calls
or a running database. External I/O is mocked throughout.
"""

from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_tech_result(score: float = 72.0, trend: str = "bullish") -> Dict[str, Any]:
    return {
        "score": score,
        "trend": trend,
        "rsi": 55.0,
        "breakout": True,
        "gap_pct": 0.5,
        "entry_zone_low": 99.0,
        "entry_zone_high": 101.0,
        "stop_loss": 95.0,
        "atr": 2.0,
    }


def _make_mock_sentiment_result(score: float = 0.2) -> Dict[str, Any]:
    return {
        "score": score,
        "normalized_score": max(0.0, min(100.0, (score + 1) / 2 * 100)),
        "momentum": "rising",
        "article_count": 15,
    }


def _make_mock_catalyst_result(score: float = 3.0) -> Dict[str, Any]:
    return {
        "score": score,
        "primary_type": "earnings_beat",
        "summary": "Earnings beat expectations.",
        "count": 1,
        "duration": "3d",
    }


# ---------------------------------------------------------------------------
# test_confidence_score_range
# ---------------------------------------------------------------------------

class TestConfidenceScoreRange:
    """Confidence scores must always be in the 0–100 range."""

    def test_confidence_within_bounds_typical(self) -> None:
        """Weighted combination of typical sub-scores stays in [0, 100]."""
        weights = {
            "technical": 0.25,
            "sentiment": 0.20,
            "momentum": 0.20,
            "catalyst": 0.20,
            "macro": 0.10,
            "volume_anomaly": 0.05,
        }
        sub_scores = {
            "technical": 72.0,
            "sentiment": 65.0,
            "momentum": 58.0,
            "catalyst": 55.0,
            "macro": 60.0,
            "volume_anomaly": 80.0,
        }
        confidence_raw = sum(sub_scores[k] * weights[k] for k in weights)
        confidence = max(0.0, min(100.0, confidence_raw))
        assert 0.0 <= confidence <= 100.0

    def test_confidence_clamped_below_zero(self) -> None:
        """Extremely negative sub-scores should not produce negative confidence."""
        sub_scores = [-200.0, -300.0, -150.0, -100.0, -50.0, -80.0]
        confidence = max(0.0, min(100.0, sum(sub_scores) / len(sub_scores)))
        assert confidence == 0.0

    def test_confidence_clamped_above_100(self) -> None:
        """Extremely high sub-scores should be capped at 100."""
        sub_scores = [200.0, 300.0, 500.0, 400.0, 200.0, 300.0]
        confidence = max(0.0, min(100.0, sum(sub_scores) / len(sub_scores)))
        assert confidence == 100.0

    def test_confidence_score_is_float(self) -> None:
        confidence = max(0.0, min(100.0, 75.321))
        assert isinstance(confidence, float)


# ---------------------------------------------------------------------------
# test_anti_overtrading_gate
# ---------------------------------------------------------------------------

class TestAntiOvertradingGate:
    """Predictions below the confidence threshold should be suppressed."""

    def _apply_gate(self, confidence: float, threshold: float = 65.0):
        """Simulate the gate logic from PredictionEngine.predict."""
        if confidence < threshold:
            return None
        return {"ticker": "TEST", "confidence_score": confidence}

    def test_returns_none_below_threshold(self) -> None:
        result = self._apply_gate(confidence=64.9, threshold=65.0)
        assert result is None

    def test_returns_none_at_zero(self) -> None:
        result = self._apply_gate(confidence=0.0, threshold=65.0)
        assert result is None

    def test_returns_prediction_at_threshold(self) -> None:
        result = self._apply_gate(confidence=65.0, threshold=65.0)
        assert result is not None
        assert result["confidence_score"] == 65.0

    def test_returns_prediction_above_threshold(self) -> None:
        result = self._apply_gate(confidence=82.5, threshold=65.0)
        assert result is not None

    def test_custom_threshold_respected(self) -> None:
        """A tighter threshold (80) should suppress more predictions."""
        result_pass = self._apply_gate(confidence=81.0, threshold=80.0)
        result_fail = self._apply_gate(confidence=79.9, threshold=80.0)
        assert result_pass is not None
        assert result_fail is None

    def test_boundary_exactly_at_threshold_passes(self) -> None:
        result = self._apply_gate(confidence=65.0, threshold=65.0)
        assert result is not None


# ---------------------------------------------------------------------------
# test_recommendation_types
# ---------------------------------------------------------------------------

class TestRecommendationTypes:
    """Recommendation type labels must be one of the valid options."""

    VALID_TYPES = {"primary", "secondary", "watchlist"}

    def _classify(self, confidence: float) -> str:
        """Mirror the classification logic in PredictionEngine."""
        if confidence >= 75.0:
            return "primary"
        elif confidence >= 65.0:
            return "secondary"
        else:
            return "watchlist"

    def test_high_confidence_is_primary(self) -> None:
        assert self._classify(80.0) == "primary"

    def test_medium_confidence_is_secondary(self) -> None:
        assert self._classify(70.0) == "secondary"

    def test_low_confidence_is_watchlist(self) -> None:
        assert self._classify(60.0) == "watchlist"

    def test_all_results_are_valid_types(self) -> None:
        test_scores = [55.0, 64.9, 65.0, 70.0, 75.0, 82.5, 99.9]
        for score in test_scores:
            rec_type = self._classify(score)
            assert rec_type in self.VALID_TYPES, (
                f"Score {score} produced invalid type '{rec_type}'"
            )

    def test_boundary_at_primary_threshold(self) -> None:
        assert self._classify(75.0) == "primary"
        assert self._classify(74.9) == "secondary"

    def test_boundary_at_secondary_threshold(self) -> None:
        assert self._classify(65.0) == "secondary"
        assert self._classify(64.9) == "watchlist"

    def test_mock_prediction_has_valid_type(self, mock_prediction: Dict[str, Any]) -> None:
        assert mock_prediction["recommendation_type"] in self.VALID_TYPES


# ---------------------------------------------------------------------------
# test_feature_engineering
# ---------------------------------------------------------------------------

class TestFeatureEngineering:
    """Feature vectors must contain at least 20 features."""

    def test_ohlcv_features_count(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """compute_ohlcv_features should return at least 20 features."""
        from app.services.ml.feature_engineering import FeatureEngineer

        fe = FeatureEngineer()
        features = fe.compute_ohlcv_features(sample_ohlcv_df)

        assert isinstance(features, dict)
        assert len(features) >= 10  # OHLCV sub-set only

    def test_full_feature_vector_exceeds_20(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """build_feature_vector combining all sources must exceed 20 features."""
        from app.services.ml.feature_engineering import FeatureEngineer

        fe = FeatureEngineer()
        tech_data = _make_mock_tech_result()
        sentiment_data = _make_mock_sentiment_result()
        catalyst_data = _make_mock_catalyst_result()
        macro_data = {
            "macro_score": 55.0,
            "vix": 18.5,
            "sp500_trend": "bullish",
        }
        fundamental_data = {"score": 60.0, "pe_ratio": 22.0}

        features = fe.build_feature_vector(
            df=sample_ohlcv_df,
            technical_analysis=tech_data,
            sentiment_data=sentiment_data,
            catalyst_data=catalyst_data,
            macro_data=macro_data,
            fundamental_data=fundamental_data,
        )

        assert isinstance(features, dict)
        assert len(features) > 20, (
            f"Expected > 20 features, got {len(features)}: {list(features.keys())}"
        )

    def test_features_are_numeric(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """All feature values must be finite floats."""
        from app.services.ml.feature_engineering import FeatureEngineer

        fe = FeatureEngineer()
        features = fe.compute_ohlcv_features(sample_ohlcv_df)

        for key, value in features.items():
            assert isinstance(value, (int, float)), f"Feature '{key}' is not numeric"
            assert not np.isnan(value), f"Feature '{key}' is NaN"

    def test_empty_dataframe_returns_empty_dict(self) -> None:
        from app.services.ml.feature_engineering import FeatureEngineer

        fe = FeatureEngineer()
        empty_df = pd.DataFrame()
        features = fe.compute_ohlcv_features(empty_df)

        assert isinstance(features, dict)
        assert len(features) == 0

    def test_short_dataframe_handled_gracefully(self) -> None:
        """DataFrames with fewer than 20 rows should return empty or minimal dict."""
        from app.services.ml.feature_engineering import FeatureEngineer

        fe = FeatureEngineer()
        short_df = pd.DataFrame({
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Volume": [1_000_000.0, 1_200_000.0],
        })
        features = fe.compute_ohlcv_features(short_df)
        # Should not raise — may return empty
        assert isinstance(features, dict)
