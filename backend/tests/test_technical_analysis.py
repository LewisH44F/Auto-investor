"""Tests for the TechnicalAnalyzer service.

All tests operate on the sample_ohlcv_df fixture (100 days of OHLCV data)
and do not require network access or a database.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd
import pytest

from app.services.analysis.technical_analysis import TechnicalAnalyzer


# ---------------------------------------------------------------------------
# test_rsi_range
# ---------------------------------------------------------------------------

class TestRSIRange:
    """RSI values must always fall in [0, 100]."""

    def test_rsi_within_bounds(self, sample_ohlcv_df: pd.DataFrame) -> None:
        analyzer = TechnicalAnalyzer()
        df_with_indicators = analyzer.compute_indicators(sample_ohlcv_df.copy())

        rsi_series = df_with_indicators["RSI"].dropna()
        assert len(rsi_series) > 0, "RSI column was empty after compute_indicators"
        assert (rsi_series >= 0).all(), "RSI contains values below 0"
        assert (rsi_series <= 100).all(), "RSI contains values above 100"

    def test_rsi_is_numeric(self, sample_ohlcv_df: pd.DataFrame) -> None:
        analyzer = TechnicalAnalyzer()
        df_with_indicators = analyzer.compute_indicators(sample_ohlcv_df.copy())

        rsi_series = df_with_indicators["RSI"].dropna()
        assert rsi_series.dtype in (np.float32, np.float64), (
            f"RSI dtype should be float, got {rsi_series.dtype}"
        )

    def test_rsi_last_row_in_range(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """The most recent RSI value specifically must be valid."""
        analyzer = TechnicalAnalyzer()
        df_with_indicators = analyzer.compute_indicators(sample_ohlcv_df.copy())

        last_rsi = df_with_indicators["RSI"].dropna().iloc[-1]
        assert 0 <= last_rsi <= 100, f"Last RSI value {last_rsi} out of range"

    def test_rsi_computed_for_standard_period(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """RSI(14) should have at least (n - 14) non-NaN values for n rows."""
        n = len(sample_ohlcv_df)
        analyzer = TechnicalAnalyzer()
        df_with_indicators = analyzer.compute_indicators(sample_ohlcv_df.copy())

        non_null_rsi = df_with_indicators["RSI"].dropna()
        assert len(non_null_rsi) >= n - 15, (
            f"Too many NaN RSI values: got {len(non_null_rsi)} non-null from {n} rows"
        )


# ---------------------------------------------------------------------------
# test_technical_score_range
# ---------------------------------------------------------------------------

class TestTechnicalScoreRange:
    """Composite technical score must always be in [0, 100]."""

    def test_score_within_bounds(self, sample_ohlcv_df: pd.DataFrame) -> None:
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_composite_score(sample_ohlcv_df)

        score = result["score"]
        assert 0.0 <= score <= 100.0, f"Technical score {score} out of [0, 100]"

    def test_score_is_float(self, sample_ohlcv_df: pd.DataFrame) -> None:
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_composite_score(sample_ohlcv_df)

        assert isinstance(result["score"], float)

    def test_score_not_nan(self, sample_ohlcv_df: pd.DataFrame) -> None:
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_composite_score(sample_ohlcv_df)

        assert not np.isnan(result["score"]), "Technical score is NaN"

    def test_short_dataframe_returns_default_score(self) -> None:
        """DataFrames with fewer than 20 rows should return the 50.0 default."""
        analyzer = TechnicalAnalyzer()
        short_df = pd.DataFrame({
            "Open": [100.0] * 10,
            "High": [102.0] * 10,
            "Low": [99.0] * 10,
            "Close": [101.0] * 10,
            "Volume": [1_000_000.0] * 10,
        })
        result = analyzer.calculate_composite_score(short_df)

        assert result["score"] == 50.0, (
            f"Expected default score 50.0 for short df, got {result['score']}"
        )

    def test_score_components_each_in_range(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """Every sub-component in the result dict should also be 0-100."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_composite_score(sample_ohlcv_df)

        components = result.get("components", {})
        for name, value in components.items():
            assert 0.0 <= value <= 100.0, (
                f"Component '{name}' value {value} out of [0, 100]"
            )

    def test_trend_field_is_valid_string(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_composite_score(sample_ohlcv_df)

        assert result.get("trend") in {"bullish", "bearish", "neutral"}, (
            f"Invalid trend value: {result.get('trend')}"
        )


# ---------------------------------------------------------------------------
# test_bollinger_bands_structure
# ---------------------------------------------------------------------------

class TestBollingerBandsStructure:
    """Bollinger Bands columns must exist and be structurally correct."""

    EXPECTED_BB_KEYS = {"BB_upper", "BB_mid", "BB_lower"}

    def test_bollinger_bands_columns_present(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        analyzer = TechnicalAnalyzer()
        df_with_indicators = analyzer.compute_indicators(sample_ohlcv_df.copy())

        for col in self.EXPECTED_BB_KEYS:
            assert col in df_with_indicators.columns, (
                f"Expected column '{col}' missing from computed indicators"
            )

    def test_bb_upper_gte_mid(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """Upper band must always be >= middle band."""
        analyzer = TechnicalAnalyzer()
        df_with_indicators = analyzer.compute_indicators(sample_ohlcv_df.copy())

        valid = df_with_indicators[["BB_upper", "BB_mid"]].dropna()
        assert (valid["BB_upper"] >= valid["BB_mid"]).all(), (
            "BB_upper is less than BB_mid on some rows"
        )

    def test_bb_lower_lte_mid(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """Lower band must always be <= middle band."""
        analyzer = TechnicalAnalyzer()
        df_with_indicators = analyzer.compute_indicators(sample_ohlcv_df.copy())

        valid = df_with_indicators[["BB_lower", "BB_mid"]].dropna()
        assert (valid["BB_lower"] <= valid["BB_mid"]).all(), (
            "BB_lower is greater than BB_mid on some rows"
        )

    def test_bb_band_ordering(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """upper >= mid >= lower for all non-NaN rows."""
        analyzer = TechnicalAnalyzer()
        df_with_indicators = analyzer.compute_indicators(sample_ohlcv_df.copy())

        valid = df_with_indicators[["BB_upper", "BB_mid", "BB_lower"]].dropna()
        assert (valid["BB_upper"] >= valid["BB_lower"]).all(), (
            "BB_upper is less than BB_lower — band ordering violated"
        )

    def test_bb_mid_equals_sma20(self, sample_ohlcv_df: pd.DataFrame) -> None:
        """Bollinger midband should closely match the 20-period SMA."""
        analyzer = TechnicalAnalyzer()
        df_with_indicators = analyzer.compute_indicators(sample_ohlcv_df.copy())

        sma20 = sample_ohlcv_df["Close"].rolling(20).mean()
        valid_idx = df_with_indicators["BB_mid"].dropna().index

        # Allow a small floating-point tolerance (0.5%)
        mid = df_with_indicators.loc[valid_idx, "BB_mid"]
        sma = sma20.loc[valid_idx]

        relative_diff = ((mid - sma) / sma).abs()
        assert (relative_diff < 0.005).all(), (
            "BB_mid deviates from SMA-20 by more than 0.5%"
        )

    def test_compute_indicators_returns_dataframe(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        analyzer = TechnicalAnalyzer()
        result = analyzer.compute_indicators(sample_ohlcv_df.copy())

        assert isinstance(result, pd.DataFrame)
        assert len(result) == len(sample_ohlcv_df)

    def test_composite_score_result_has_expected_keys(
        self, sample_ohlcv_df: pd.DataFrame
    ) -> None:
        """calculate_composite_score must return a dict with required keys."""
        required_keys = {
            "score",
            "trend",
            "components",
            "entry_zone_low",
            "entry_zone_high",
            "stop_loss",
            "breakout",
            "gap_pct",
        }
        analyzer = TechnicalAnalyzer()
        result = analyzer.calculate_composite_score(sample_ohlcv_df)

        assert isinstance(result, dict)
        missing = required_keys - result.keys()
        assert not missing, f"calculate_composite_score missing keys: {missing}"
