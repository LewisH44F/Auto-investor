"""SQLAlchemy ORM models for self-learning and model performance tracking."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime, Float, Index, Integer, JSON,
    String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ModelPerformance(Base):
    __tablename__ = "model_performance"
    __table_args__ = (
        Index("ix_model_perf_date", "date", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, unique=True)

    win_rate: Mapped[Optional[float]] = mapped_column(Float)
    avg_confidence: Mapped[Optional[float]] = mapped_column(Float)
    avg_return: Mapped[Optional[float]] = mapped_column(Float)
    total_predictions: Mapped[Optional[int]] = mapped_column(Integer)
    total_wins: Mapped[Optional[int]] = mapped_column(Integer)
    total_losses: Mapped[Optional[int]] = mapped_column(Integer)
    total_neutral: Mapped[Optional[int]] = mapped_column(Integer)

    sharpe: Mapped[Optional[float]] = mapped_column(Float)
    max_drawdown: Mapped[Optional[float]] = mapped_column(Float)

    signal_type_weights: Mapped[Optional[dict]] = mapped_column(JSON)
    signal_type_win_rates: Mapped[Optional[dict]] = mapped_column(JSON)

    model_version: Mapped[Optional[str]] = mapped_column(String(50))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<ModelPerformance {self.date} win_rate={self.win_rate}>"


class PatternRecord(Base):
    __tablename__ = "pattern_records"
    __table_args__ = (
        Index("ix_pattern_name", "pattern_name", unique=True),
        Index("ix_pattern_win_rate", "win_rate"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pattern_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(50))

    occurrences: Mapped[int] = mapped_column(Integer, default=0)
    win_rate: Mapped[Optional[float]] = mapped_column(Float)
    avg_return: Mapped[Optional[float]] = mapped_column(Float)
    avg_hold_days: Mapped[Optional[float]] = mapped_column(Float)

    confidence_adjustment: Mapped[float] = mapped_column(Float, default=0.0)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_active: Mapped[int] = mapped_column(Integer, default=1)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return f"<PatternRecord '{self.pattern_name}' wr={self.win_rate}>"
