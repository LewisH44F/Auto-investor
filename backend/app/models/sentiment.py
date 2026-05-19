"""SQLAlchemy ORM models for sentiment and analyst ratings."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime, Float, Index, Integer,
    String, Text, JSON, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SentimentRecord(Base):
    """Aggregated sentiment from a given source for a ticker."""

    __tablename__ = "sentiment_records"
    __table_args__ = (
        Index("ix_sentiment_ticker_ts", "ticker", "timestamp"),
        Index("ix_sentiment_source", "source"),
        Index("ix_sentiment_ticker", "ticker"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # Source: reddit / twitter / news / analyst / stocktwits / seeking_alpha
    source: Mapped[str] = mapped_column(String(50), nullable=False)

    # Scores
    score: Mapped[float] = mapped_column(Float, nullable=False)       # -1 to 1
    score_normalized: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    volume: Mapped[Optional[int]] = mapped_column(Integer)            # # of mentions/posts
    bullish_count: Mapped[Optional[int]] = mapped_column(Integer)
    bearish_count: Mapped[Optional[int]] = mapped_column(Integer)
    neutral_count: Mapped[Optional[int]] = mapped_column(Integer)

    # Momentum
    score_prev: Mapped[Optional[float]] = mapped_column(Float)        # previous period score
    momentum: Mapped[Optional[str]] = mapped_column(String(20))       # improving/deteriorating/stable

    # Raw data snapshot
    raw_data: Mapped[Optional[dict]] = mapped_column(JSON)

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<SentimentRecord {self.ticker} src={self.source} score={self.score:.2f}>"


class AnalystRating(Base):
    """Wall Street analyst ratings and price targets."""

    __tablename__ = "analyst_ratings"
    __table_args__ = (
        Index("ix_analyst_ticker_ts", "ticker", "timestamp"),
        Index("ix_analyst_firm", "firm"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    firm: Mapped[Optional[str]] = mapped_column(String(200))
    analyst: Mapped[Optional[str]] = mapped_column(String(200))

    # Rating
    rating: Mapped[Optional[str]] = mapped_column(String(50))           # buy / sell / hold / outperform ...
    previous_rating: Mapped[Optional[str]] = mapped_column(String(50))
    rating_change: Mapped[Optional[str]] = mapped_column(String(30))    # upgrade / downgrade / initiate / reiterate

    # Price target
    price_target: Mapped[Optional[float]] = mapped_column(Float)
    previous_price_target: Mapped[Optional[float]] = mapped_column(Float)
    price_target_change_pct: Mapped[Optional[float]] = mapped_column(Float)

    # Context
    notes: Mapped[Optional[str]] = mapped_column(Text)
    source_url: Mapped[Optional[str]] = mapped_column(String(1000))

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<AnalystRating {self.ticker} {self.firm} {self.rating}>"
