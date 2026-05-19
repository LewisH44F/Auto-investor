"""SQLAlchemy ORM models for predictions and prediction feedback."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, Index, Integer,
    String, Text, JSON, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Prediction(Base):
    """AI-generated stock prediction record."""

    __tablename__ = "predictions"
    __table_args__ = (
        Index("ix_predictions_ticker_date", "ticker", "prediction_date"),
        Index("ix_predictions_prediction_date", "prediction_date"),
        Index("ix_predictions_recommendation_type", "recommendation_type"),
        Index("ix_predictions_confidence_score", "confidence_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # Core prediction scores (0-100)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    upside_probability: Mapped[Optional[float]] = mapped_column(Float)   # 0-100
    downside_risk: Mapped[Optional[float]] = mapped_column(Float)        # 0-100
    volatility_score: Mapped[Optional[float]] = mapped_column(Float)     # 0-100
    momentum_score: Mapped[Optional[float]] = mapped_column(Float)       # 0-100
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)      # -100 to 100
    technical_score: Mapped[Optional[float]] = mapped_column(Float)      # 0-100
    catalyst_score: Mapped[Optional[float]] = mapped_column(Float)       # 0-10
    macro_score: Mapped[Optional[float]] = mapped_column(Float)          # 0-100
    volume_anomaly_score: Mapped[Optional[float]] = mapped_column(Float) # 0-100

    # Entry / exit zones
    entry_zone_low: Mapped[Optional[float]] = mapped_column(Float)
    entry_zone_high: Mapped[Optional[float]] = mapped_column(Float)
    stop_loss: Mapped[Optional[float]] = mapped_column(Float)
    profit_target_1: Mapped[Optional[float]] = mapped_column(Float)
    profit_target_2: Mapped[Optional[float]] = mapped_column(Float)

    # Expectations
    expected_move_pct: Mapped[Optional[float]] = mapped_column(Float)
    expected_hold_duration: Mapped[Optional[str]] = mapped_column(String(20))  # 1d, 3d, 1w, 1m
    risk_rating: Mapped[Optional[str]] = mapped_column(String(20))  # low/medium/high/very_high

    # Classification
    recommendation_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="watchlist"
    )  # primary / secondary / watchlist

    # Narrative summaries
    catalyst_summary: Mapped[Optional[str]] = mapped_column(Text)
    technical_summary: Mapped[Optional[str]] = mapped_column(Text)
    sentiment_summary: Mapped[Optional[str]] = mapped_column(Text)
    plain_english_explanation: Mapped[Optional[str]] = mapped_column(Text)

    # Signal metadata
    signal_types: Mapped[Optional[dict]] = mapped_column(JSON)   # {"breakout": true, ...}
    feature_values: Mapped[Optional[dict]] = mapped_column(JSON) # raw features used

    # Outcome tracking
    actual_outcome: Mapped[Optional[str]] = mapped_column(String(20))  # win/loss/neutral
    actual_move_pct: Mapped[Optional[float]] = mapped_column(Float)
    outcome_recorded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    prediction_error: Mapped[Optional[float]] = mapped_column(Float)
    is_outcome_recorded: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    prediction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    feedback: Mapped[list["PredictionFeedback"]] = relationship(
        "PredictionFeedback", back_populates="prediction", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Prediction {self.ticker} {self.recommendation_type} conf={self.confidence_score:.1f}>"


class PredictionFeedback(Base):
    """Records actual outcomes for self-learning."""

    __tablename__ = "prediction_feedback"
    __table_args__ = (
        Index("ix_feedback_prediction_id", "prediction_id"),
        Index("ix_feedback_ticker", "ticker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prediction_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)

    # Actual price data after N days
    actual_high: Mapped[Optional[float]] = mapped_column(Float)
    actual_low: Mapped[Optional[float]] = mapped_column(Float)
    actual_close: Mapped[Optional[float]] = mapped_column(Float)
    entry_price: Mapped[Optional[float]] = mapped_column(Float)
    holding_days: Mapped[Optional[int]] = mapped_column(Integer)

    # Performance
    realized_gain_pct: Mapped[Optional[float]] = mapped_column(Float)
    max_gain_pct: Mapped[Optional[float]] = mapped_column(Float)
    max_loss_pct: Mapped[Optional[float]] = mapped_column(Float)
    hit_target_1: Mapped[Optional[bool]] = mapped_column(Boolean)
    hit_target_2: Mapped[Optional[bool]] = mapped_column(Boolean)
    hit_stop_loss: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Outcome classification
    outcome_label: Mapped[Optional[str]] = mapped_column(String(20))  # win/loss/neutral
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text)
    weight_adjustments: Mapped[Optional[dict]] = mapped_column(JSON)

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship
    prediction: Mapped["Prediction"] = relationship(
        "Prediction", back_populates="feedback",
        foreign_keys=[prediction_id],
        primaryjoin="PredictionFeedback.prediction_id == Prediction.id"
    )

    def __repr__(self) -> str:
        return f"<PredictionFeedback pred={self.prediction_id} outcome={self.outcome_label}>"
