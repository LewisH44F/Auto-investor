"""Watchlist model."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class WatchlistItem(Base):
    __tablename__ = "watchlist"
    __table_args__ = (Index("ix_watchlist_ticker", "ticker", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
