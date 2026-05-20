"""SQLAlchemy ORM models for sentiment and analyst ratings."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime, Float, Index, Integer, JSON,
    String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SentimentRecord(Base):
    __tablename__ = "sentiment_records"
    __table_args__ = (
        Index("ix_sentiment_ticker_ts", "ticker", "timestamp"),
        Index("ix_sentiment_source", "source"),
        Index("ix_sentiment_ticker", "ticker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False)

    score: Mapped[float] = mapped_column(Float, nullable=False)
    score_normalized: Mapped[Optional[float]] = mapped_column(Float)
    volume: Mapped[Optional[int]] = mapped_column(Integer)
    bullish_count: Mapped[Optional[int]] = mapped_column(Integer)
    bearish_count: Mapped[Optional[int]] = mapped_column(Integer)
    neutral_count: Mapped[Optional[int]] = mapped_column(Integer)

    score_prev: Mapped[Optional[float]] = mapped_column(Float)
    momentum: Mapped[Optional[str]] = mapped_column(String(20))

    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)

    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<SentimentRecord {self.ticker} src={self.source} score={self.score:.2f}>"


class AnalystRating(Base):
    __tablename__ = "analyst_ratings"
    __table_args__ = (
        Index("ix_analyst_ticker_ts", "ticker", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    firm: Mapped[Optional[str]] = mapped_column(String(200))
    analyst: Mapped[Optional[str]] = mapped_column(String(200))

    rating: Mapped[Optional[str]] = mapped_column(String(50))
    previous_rating: Mapped[Optional[str]] = mapped_column(String(50))
    rating_change: Mapped[Optional[str]] = mapped_column(String(30))

    price_target: Mapped[Optional[float]] = mapped_column(Float)
    previous_price_target: Mapped[Optional[float]] = mapped_column(Float)
    price_target_change_pct: Mapped[Optional[float]] = mapped_column(Float)

    notes: Mapped[Optional[str]] = mapped_column(Text)
    source_url: Mapped[Optional[str]] = mapped_column(String(1000))

    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<AnalystRating {self.ticker} {self.firm} {self.rating}>"
