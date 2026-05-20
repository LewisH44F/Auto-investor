"""SQLAlchemy ORM models for portfolio management."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, Float, Index, Integer, JSON,
    String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Holding(Base):
    __tablename__ = "holdings"
    __table_args__ = (
        Index("ix_holdings_ticker", "ticker"),
        Index("ix_holdings_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    shares: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    current_price: Mapped[Optional[float]] = mapped_column(Float)
    current_value: Mapped[Optional[float]] = mapped_column(Float)
    unrealized_pnl: Mapped[Optional[float]] = mapped_column(Float)
    unrealized_pnl_pct: Mapped[Optional[float]] = mapped_column(Float)
    cost_basis: Mapped[Optional[float]] = mapped_column(Float)

    ai_recommendation: Mapped[Optional[str]] = mapped_column(String(30))
    conviction_score: Mapped[Optional[float]] = mapped_column(Float)
    ai_reasoning: Mapped[Optional[str]] = mapped_column(Text)
    stop_loss_price: Mapped[Optional[float]] = mapped_column(Float)
    target_price: Mapped[Optional[float]] = mapped_column(Float)
    last_assessed: Mapped[Optional[datetime]] = mapped_column(DateTime)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_ai_initiated: Mapped[bool] = mapped_column(Boolean, default=False)
    original_prediction_id: Mapped[Optional[int]] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return f"<Holding {self.ticker} {self.shares}sh @ {self.purchase_price}>"


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_ticker", "ticker"),
        Index("ix_transactions_timestamp", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)
    shares: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    total_amount: Mapped[Optional[float]] = mapped_column(Float)
    commission: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    holding_id: Mapped[Optional[int]] = mapped_column(Integer)
    prediction_id: Mapped[Optional[int]] = mapped_column(Integer)

    realized_pnl: Mapped[Optional[float]] = mapped_column(Float)
    realized_pnl_pct: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Transaction {self.transaction_type} {self.ticker} {self.shares}sh @ {self.price}>"


class PortfolioMetrics(Base):
    __tablename__ = "portfolio_metrics"
    __table_args__ = (
        Index("ix_portfolio_metrics_date", "date", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, unique=True)

    total_value: Mapped[float] = mapped_column(Float, default=0.0)
    cash: Mapped[float] = mapped_column(Float, default=100000.0)
    invested: Mapped[float] = mapped_column(Float, default=0.0)
    num_positions: Mapped[int] = mapped_column(Integer, default=0)

    total_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    total_pnl_pct: Mapped[float] = mapped_column(Float, default=0.0)
    day_pnl: Mapped[Optional[float]] = mapped_column(Float)
    day_pnl_pct: Mapped[Optional[float]] = mapped_column(Float)

    win_rate: Mapped[Optional[float]] = mapped_column(Float)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Float)
    max_drawdown: Mapped[Optional[float]] = mapped_column(Float)
    var_95: Mapped[Optional[float]] = mapped_column(Float)

    sector_allocations: Mapped[Optional[dict]] = mapped_column(JSON)
    top_performers: Mapped[Optional[dict]] = mapped_column(JSON)
    worst_performers: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def __repr__(self) -> str:
        return f"<PortfolioMetrics {self.date} total={self.total_value:.2f}>"
