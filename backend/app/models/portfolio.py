"""SQLAlchemy ORM models for portfolio management."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, Index, Integer,
    String, Text, JSON, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Holding(Base):
    """Active portfolio holding."""

    __tablename__ = "holdings"
    __table_args__ = (
        Index("ix_holdings_ticker", "ticker"),
        Index("ix_holdings_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    shares: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Current market data (updated periodically)
    current_price: Mapped[Optional[float]] = mapped_column(Float)
    current_value: Mapped[Optional[float]] = mapped_column(Float)
    unrealized_pnl: Mapped[Optional[float]] = mapped_column(Float)
    unrealized_pnl_pct: Mapped[Optional[float]] = mapped_column(Float)
    cost_basis: Mapped[Optional[float]] = mapped_column(Float)

    # AI assessment
    ai_recommendation: Mapped[Optional[str]] = mapped_column(String(30))
    # hold / sell / buy_more / average_down
    conviction_score: Mapped[Optional[float]] = mapped_column(Float)  # 0-100
    ai_reasoning: Mapped[Optional[str]] = mapped_column(Text)
    stop_loss_price: Mapped[Optional[float]] = mapped_column(Float)
    target_price: Mapped[Optional[float]] = mapped_column(Float)
    last_assessed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_ai_initiated: Mapped[bool] = mapped_column(Boolean, default=False)
    original_prediction_id: Mapped[Optional[int]] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<Holding {self.ticker} {self.shares}sh @ {self.purchase_price}>"


class Transaction(Base):
    """Buy/sell transaction record."""

    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_ticker", "ticker"),
        Index("ix_transactions_timestamp", "timestamp"),
        Index("ix_transactions_type", "transaction_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)  # buy / sell
    shares: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    total_amount: Mapped[Optional[float]] = mapped_column(Float)
    commission: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # References
    holding_id: Mapped[Optional[int]] = mapped_column(Integer)
    prediction_id: Mapped[Optional[int]] = mapped_column(Integer)

    # Realized P&L (populated on sell)
    realized_pnl: Mapped[Optional[float]] = mapped_column(Float)
    realized_pnl_pct: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.transaction_type} {self.ticker} {self.shares}sh @ {self.price}>"


class PortfolioMetrics(Base):
    """Daily portfolio snapshot for performance tracking."""

    __tablename__ = "portfolio_metrics"
    __table_args__ = (
        Index("ix_portfolio_metrics_date", "date", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, unique=True)

    # Value breakdown
    total_value: Mapped[float] = mapped_column(Float, default=0.0)
    cash: Mapped[float] = mapped_column(Float, default=0.0)
    invested: Mapped[float] = mapped_column(Float, default=0.0)
    num_positions: Mapped[int] = mapped_column(Integer, default=0)

    # P&L
    total_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    total_pnl_pct: Mapped[float] = mapped_column(Float, default=0.0)
    day_pnl: Mapped[Optional[float]] = mapped_column(Float)
    day_pnl_pct: Mapped[Optional[float]] = mapped_column(Float)

    # Risk metrics
    win_rate: Mapped[Optional[float]] = mapped_column(Float)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Float)
    sortino_ratio: Mapped[Optional[float]] = mapped_column(Float)
    max_drawdown: Mapped[Optional[float]] = mapped_column(Float)
    portfolio_beta: Mapped[Optional[float]] = mapped_column(Float)
    var_95: Mapped[Optional[float]] = mapped_column(Float)  # 95% Value at Risk

    # Breakdown by sector
    sector_allocations: Mapped[Optional[dict]] = mapped_column(JSON)
    top_performers: Mapped[Optional[dict]] = mapped_column(JSON)
    worst_performers: Mapped[Optional[dict]] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<PortfolioMetrics {self.date} total={self.total_value:.2f}>"
