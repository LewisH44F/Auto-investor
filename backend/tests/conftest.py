"""Shared pytest fixtures for the AutoInvestor test suite."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# OHLCV fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_ohlcv_df() -> pd.DataFrame:
    """
    100 days of realistic OHLCV data seeded for reproducibility.

    Returns a DataFrame with columns: Open, High, Low, Close, Volume.
    """
    rng = np.random.default_rng(seed=42)

    n = 100
    # Simulate a price series with mild upward drift
    daily_returns = rng.normal(loc=0.0005, scale=0.015, size=n)
    close_prices = 100.0 * np.cumprod(1 + daily_returns)

    # Derive OHLCV from close
    opens = np.roll(close_prices, 1)
    opens[0] = close_prices[0] * (1 + rng.normal(0, 0.003))

    highs = np.maximum(opens, close_prices) * (1 + np.abs(rng.normal(0, 0.008, n)))
    lows = np.minimum(opens, close_prices) * (1 - np.abs(rng.normal(0, 0.008, n)))
    volumes = rng.integers(low=500_000, high=5_000_000, size=n).astype(float)

    dates = pd.date_range(
        end=datetime(2025, 5, 1, tzinfo=timezone.utc),
        periods=n,
        freq="B",  # business days
    )

    df = pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": close_prices,
            "Volume": volumes,
        },
        index=dates,
    )

    # Ensure High >= Low (may drift with rounding)
    df["High"] = df[["High", "Low"]].max(axis=1)
    df["Low"] = df[["High", "Low"]].min(axis=1)

    return df


# ---------------------------------------------------------------------------
# Prediction fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_prediction() -> Dict[str, Any]:
    """A representative prediction dictionary as returned by the engine."""
    now = datetime.now(timezone.utc)
    return {
        "id": 1,
        "ticker": "AAPL",
        "confidence_score": 78.5,
        "upside_probability": 68.0,
        "downside_risk": 32.0,
        "volatility_score": 30.2,
        "momentum_score": 62.4,
        "sentiment_score": 15.0,
        "technical_score": 74.8,
        "catalyst_score": 2.1,
        "macro_score": 55.0,
        "volume_anomaly_score": 70.0,
        "entry_zone_low": 182.50,
        "entry_zone_high": 184.00,
        "stop_loss": 177.00,
        "profit_target_1": 192.00,
        "profit_target_2": 198.00,
        "expected_move_pct": 4.5,
        "expected_hold_duration": "1w",
        "risk_rating": "medium",
        "recommendation_type": "primary",
        "catalyst_summary": "Earnings beat expectations by 12%.",
        "technical_summary": "Trend: bullish. RSI: 58. Breakout: Yes.",
        "sentiment_summary": "Score: 0.18. Momentum: rising. Articles: 24.",
        "plain_english_explanation": (
            "**AAPL** presents a GOOD setup (78% confidence). "
            "The stock is in a bullish uptrend with price above key moving averages."
        ),
        "signal_types": {
            "breakout": True,
            "trend_bullish": True,
            "volume_surge": False,
            "catalyst": True,
            "sentiment_positive": True,
            "gap_up": False,
        },
        "feature_values": {
            "return_1d": 0.85,
            "return_5d": 2.10,
            "return_20d": 5.30,
            "volatility_20d": 18.5,
            "relative_volume": 1.4,
        },
        "prediction_date": now,
        "created_at": now,
        "actual_return_pct": None,
        "outcome": None,
    }


# ---------------------------------------------------------------------------
# Holding fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_holding() -> Dict[str, Any]:
    """A representative open portfolio holding."""
    entry_date = datetime.now(timezone.utc) - timedelta(days=3)
    return {
        "id": 1,
        "ticker": "MSFT",
        "entry_price": 415.00,
        "current_price": 423.50,
        "quantity": 10,
        "entry_date": entry_date,
        "stop_loss": 400.00,
        "profit_target_1": 435.00,
        "profit_target_2": 450.00,
        "unrealized_pnl": (423.50 - 415.00) * 10,
        "unrealized_pnl_pct": (423.50 / 415.00 - 1) * 100,
        "status": "open",
        "recommendation_type": "primary",
        "max_hold_days": 10,
        "days_held": 3,
        "days_remaining": 7,
        "risk_rating": "medium",
        "notes": "Strong earnings catalyst. Watch for resistance at 430.",
    }
