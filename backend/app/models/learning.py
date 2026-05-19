"""SQLAlchemy ORM models for self-learning and model performance tracking."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime, Float, Index, Integer,
    String, Text, JSON, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ModelPerformance(Base):
    """Daily model performance snapshot."""

    __tablename__ = "model_performance"
    __table_args__ = (
        Index("ix_model_perf_date", "date", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, unique=True)

    # Performance stats
    win_rate: Mapped[Optional[float]] = mapped_column(Float)
    avg_confidence: Mapped[Optional[float]] = mapped_column(Float)
    avg_return: Mapped[Optional[float]] = mapped_column(Float)
    total_predictions: Mapped[Optional[int]] = mapped_column(Integer)
    total_wins: Mapped[Optional[int]] = mapped_column(Integer)
    total_losses: Mapped[Optional[int]] = mapped_column(Integer)
    total_neutral: Mapped[Optional[int]] = mapped_column(Integer)

    # Risk-adjusted
    sharpe: Mapped[Optional[float]] = mapped_column(Float)
    sortino: Mapped[Optional[float]] = mapped_column(Float)
    max_drawdown: Mapped[Optional[float]] = mapped_column(Float)
    calmar_ratio: Mapped[Optional[float]] = mapped_column(Float)

    # Signal type performance breakdown
    signal_type_weights: Mapped[Optional[dict]] = mapped_column(JSON)
    signal_type_win_rates: Mapped[Optional[dict]] = mapped_column(JSON)

    # Model version info
    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<ModelPerformance {self.date} win_rate={self.win_rate}>"


class PatternRecord(Base):
    """Track recurring patterns and their success rates."""

    __tablename__ = "pattern_records"
    __table_args__ = (
        Index("ix_pattern_name", "pattern_name", unique=True),
        Index("ix_pattern_win_rate", "win_rate"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pattern_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(50))  # technical / sentiment / catalyst / macro

    # Stats
    occurrences: Mapped[int] = mapped_column(Integer, default=0)
    win_rate: Mapped[Optional[float]] = mapped_column(Float)
    avg_return: Mapped[Optional[float]] = mapped_column(Float)
    avg_hold_days: Mapped[Optional[float]] = mapped_column(Float)
    avg_max_gain: Mapped[Optional[float]] = mapped_column(Float)
    avg_max_loss: Mapped[Optional[float]] = mapped_column(Float)

    # Learning
    confidence_adjustment: Mapped[float] = mapped_column(Float, default=0.0)  # +/- applied to confidence
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<PatternRecord '{self.pattern_name}' wr={self.win_rate}>"


class LearningLog(Base):
    """Granular log of every learning event."""

    __tablename__ = "learning_logs"
    __table_args__ = (
        Index("ix_learning_log_ts", "timestamp"),
        Index("ix_learning_log_event_type", "event_type"),
        Index("ix_learning_log_ticker", "ticker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # outcome_recorded / weight_updated / pattern_detected / model_retrained

    ticker: Mapped[Optional[str]] = mapped_column(String(10))
    prediction_id: Mapped[Optional[int]] = mapped_column(Integer)

    # What happened
    actual_vs_predicted: Mapped[Optional[str]] = mapped_column(Text)
    lesson: Mapped[Optional[str]] = mapped_column(Text)
    weight_adjustment: Mapped[Optional[dict]] = mapped_column(JSON)

    # Before/after state
    before_state: Mapped[Optional[dict]] = mapped_column(JSON)
    after_state: Mapped[Optional[dict]] = mapped_column(JSON)

    severity: Mapped[Optional[str]] = mapped_column(String(20))  # info / warning / critical

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<LearningLog {self.event_type} {self.ticker}>"
