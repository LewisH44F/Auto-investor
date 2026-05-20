"""SQLAlchemy ORM models for AI predictions."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, Index, Integer, JSON,
    String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        Index("ix_predictions_ticker_date", "ticker", "prediction_date"),
        Index("ix_predictions_prediction_date", "prediction_date"),
        Index("ix_predictions_recommendation_type", "recommendation_type"),
        Index("ix_predictions_confidence_score", "confidence_score"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    upside_probability: Mapped[Optional[float]] = mapped_column(Float)
    downside_risk: Mapped[Optional[float]] = mapped_column(Float)
    volatility_score: Mapped[Optional[float]] = mapped_column(Float)
    momentum_score: Mapped[Optional[float]] = mapped_column(Float)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)
    technical_score: Mapped[Optional[float]] = mapped_column(Float)
    catalyst_score: Mapped[Optional[float]] = mapped_column(Float)
    macro_score: Mapped[Optional[float]] = mapped_column(Float)
    volume_anomaly_score: Mapped[Optional[float]] = mapped_column(Float)

    entry_zone_low: Mapped[Optional[float]] = mapped_column(Float)
    entry_zone_high: Mapped[Optional[float]] = mapped_column(Float)
    stop_loss: Mapped[Optional[float]] = mapped_column(Float)
    profit_target_1: Mapped[Optional[float]] = mapped_column(Float)
    profit_target_2: Mapped[Optional[float]] = mapped_column(Float)

    expected_move_pct: Mapped[Optional[float]] = mapped_column(Float)
    expected_hold_duration: Mapped[Optional[str]] = mapped_column(String(20))
    risk_rating: Mapped[Optional[str]] = mapped_column(String(20))
    recommendation_type: Mapped[str] = mapped_column(String(20), nullable=False, default="watchlist")

    catalyst_summary: Mapped[Optional[str]] = mapped_column(Text)
    technical_summary: Mapped[Optional[str]] = mapped_column(Text)
    sentiment_summary: Mapped[Optional[str]] = mapped_column(Text)
    plain_english_explanation: Mapped[Optional[str]] = mapped_column(Text)

    signal_types: Mapped[Optional[dict]] = mapped_column(JSON)
    feature_values: Mapped[Optional[dict]] = mapped_column(JSON)

    actual_outcome: Mapped[Optional[str]] = mapped_column(String(20))
    actual_move_pct: Mapped[Optional[float]] = mapped_column(Float)
    outcome_recorded_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_outcome_recorded: Mapped[bool] = mapped_column(Boolean, default=False)

    prediction_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    feedback: Mapped[list["PredictionFeedback"]] = relationship(
        "PredictionFeedback", back_populates="prediction", cascade="all, delete-orphan",
        primaryjoin="Prediction.id == foreign(PredictionFeedback.prediction_id)",
    )

    def __repr__(self) -> str:
        return f"<Prediction {self.ticker} {self.recommendation_type} conf={self.confidence_score:.1f}>"


class PredictionFeedback(Base):
    __tablename__ = "prediction_feedback"
    __table_args__ = (
        Index("ix_feedback_prediction_id", "prediction_id"),
        Index("ix_feedback_ticker", "ticker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prediction_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)

    actual_close: Mapped[Optional[float]] = mapped_column(Float)
    entry_price: Mapped[Optional[float]] = mapped_column(Float)
    holding_days: Mapped[Optional[int]] = mapped_column(Integer)
    realized_gain_pct: Mapped[Optional[float]] = mapped_column(Float)
    max_gain_pct: Mapped[Optional[float]] = mapped_column(Float)
    max_loss_pct: Mapped[Optional[float]] = mapped_column(Float)
    hit_target_1: Mapped[Optional[bool]] = mapped_column(Boolean)
    hit_stop_loss: Mapped[Optional[bool]] = mapped_column(Boolean)
    outcome_label: Mapped[Optional[str]] = mapped_column(String(20))
    lessons_learned: Mapped[Optional[str]] = mapped_column(Text)

    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    prediction: Mapped["Prediction"] = relationship(
        "Prediction", back_populates="feedback",
        primaryjoin="PredictionFeedback.prediction_id == Prediction.id",
        foreign_keys="[PredictionFeedback.prediction_id]",
    )

    def __repr__(self) -> str:
        return f"<PredictionFeedback pred={self.prediction_id} outcome={self.outcome_label}>"
