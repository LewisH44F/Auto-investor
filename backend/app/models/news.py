"""SQLAlchemy ORM models for news articles."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, Index, Integer,
    String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NewsArticle(Base):
    """News article with sentiment scoring."""

    __tablename__ = "news_articles"
    __table_args__ = (
        Index("ix_news_ticker_published", "ticker", "published_at"),
        Index("ix_news_published_at", "published_at"),
        Index("ix_news_catalyst_type", "catalyst_type"),
        Index("ix_news_is_processed", "is_processed"),
        Index("ix_news_url_hash", "url_hash", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[Optional[str]] = mapped_column(String(10), index=True)  # None = market-wide
    tickers_mentioned: Mapped[Optional[str]] = mapped_column(String(500))  # comma-separated

    # Article data
    headline: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    full_text: Mapped[Optional[str]] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(100))
    author: Mapped[Optional[str]] = mapped_column(String(200))
    url: Mapped[Optional[str]] = mapped_column(String(1000))
    url_hash: Mapped[Optional[str]] = mapped_column(String(64))  # sha256 for dedup

    # Timestamps
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Scoring
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float)  # -1 to 1
    sentiment_label: Mapped[Optional[str]] = mapped_column(String(20))  # positive/negative/neutral
    impact_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-10

    # Catalyst classification
    catalyst_type: Mapped[Optional[str]] = mapped_column(String(50))
    # earnings / merger / fda / partnership / analyst / macro / legal / leadership / contract

    catalyst_strength: Mapped[Optional[float]] = mapped_column(Float)  # 0-10
    catalyst_duration: Mapped[Optional[str]] = mapped_column(String(20))  # 1d / 3d / 1w / 1m

    # Processing flags
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<NewsArticle {self.ticker} '{self.headline[:40]}...'>"
