"""Prediction-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PredictionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    confidence_score: float
    upside_probability: Optional[float] = None
    downside_risk: Optional[float] = None
    volatility_score: Optional[float] = None
    momentum_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    technical_score: Optional[float] = None
    catalyst_score: Optional[float] = None
    macro_score: Optional[float] = None
    volume_anomaly_score: Optional[float] = None

    entry_zone_low: Optional[float] = None
    entry_zone_high: Optional[float] = None
    stop_loss: Optional[float] = None
    profit_target_1: Optional[float] = None
    profit_target_2: Optional[float] = None

    expected_move_pct: Optional[float] = None
    expected_hold_duration: Optional[str] = None
    risk_rating: Optional[str] = None
    recommendation_type: str

    catalyst_summary: Optional[str] = None
    technical_summary: Optional[str] = None
    sentiment_summary: Optional[str] = None
    plain_english_explanation: Optional[str] = None

    signal_types: Optional[Dict[str, Any]] = None

    actual_outcome: Optional[str] = None
    actual_move_pct: Optional[float] = None
    outcome_recorded_at: Optional[datetime] = None
    is_outcome_recorded: bool

    prediction_date: datetime
    created_at: datetime


class PredictionSummary(BaseModel):
    """Lightweight prediction summary for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    confidence_score: float
    recommendation_type: str
    expected_move_pct: Optional[float] = None
    risk_rating: Optional[str] = None
    plain_english_explanation: Optional[str] = None
    prediction_date: datetime
    actual_outcome: Optional[str] = None


class TonightPredictions(BaseModel):
    """Tonight's AI picks response."""

    primary: Optional[PredictionRead] = None
    secondary: List[PredictionRead] = Field(default_factory=list)
    watchlist: List[PredictionRead] = Field(default_factory=list)
    generated_at: datetime
    model_confidence: float
    total_stocks_scanned: int


class PredictionPerformance(BaseModel):
    """Model performance statistics."""

    period_days: int
    total_predictions: int
    win_rate: float
    avg_return_pct: float
    avg_confidence: float
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    signal_breakdown: Dict[str, Any] = Field(default_factory=dict)
    recent_trend: str  # improving / deteriorating / stable


class ManualScanRequest(BaseModel):
    tickers: Optional[List[str]] = None  # None = scan default universe
    min_confidence: float = Field(default=65.0, ge=0, le=100)


class ManualScanResponse(BaseModel):
    predictions: List[PredictionRead]
    scan_duration_seconds: float
    tickers_scanned: int


class PredictionFeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prediction_id: int
    ticker: str
    actual_close: Optional[float] = None
    realized_gain_pct: Optional[float] = None
    outcome_label: Optional[str] = None
    lessons_learned: Optional[str] = None
    recorded_at: datetime
