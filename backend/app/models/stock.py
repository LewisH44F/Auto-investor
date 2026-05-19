"""SQLAlchemy ORM models for stock data."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, DateTime, Float, Index, Integer,
    String, Text, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Stock(Base):
    """Master stock record."""

    __tablename__ = "stocks"
    __table_args__ = (
        Index("ix_stocks_ticker", "ticker", unique=True),
        Index("ix_stocks_sector", "sector"),
        Index("ix_stocks_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    industry: Mapped[Optional[str]] = mapped_column(String(150))
    market_cap: Mapped[Optional[float]] = mapped_column(Float)
    float_shares: Mapped[Optional[float]] = mapped_column(Float)
    is_nasdaq: Mapped[bool] = mapped_column(Boolean, default=True)
    is_sp500: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(String(255))
    country: Mapped[Optional[str]] = mapped_column(String(50))
    exchange: Mapped[Optional[str]] = mapped_column(String(20))
    ipo_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_updated: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    prices: Mapped[list["StockPrice"]] = relationship(
        "StockPrice", back_populates="stock", cascade="all, delete-orphan"
    )
    fundamentals: Mapped[list["StockFundamentals"]] = relationship(
        "StockFundamentals", back_populates="stock", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Stock {self.ticker}>"


class StockPrice(Base):
    """OHLCV price record with extended market data."""

    __tablename__ = "stock_prices"
    __table_args__ = (
        Index("ix_stock_prices_ticker_ts", "ticker", "timestamp"),
        Index("ix_stock_prices_timestamp", "timestamp"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    stock_id: Mapped[Optional[int]] = mapped_column(
        Integer, index=True
    )

    # OHLCV
    open: Mapped[Optional[float]] = mapped_column(Float)
    high: Mapped[Optional[float]] = mapped_column(Float)
    low: Mapped[Optional[float]] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    adjusted_close: Mapped[Optional[float]] = mapped_column(Float)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)

    # Extended market data
    pre_market_price: Mapped[Optional[float]] = mapped_column(Float)
    pre_market_volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    after_hours_price: Mapped[Optional[float]] = mapped_column(Float)
    after_hours_volume: Mapped[Optional[int]] = mapped_column(BigInteger)

    # Derived metrics
    relative_volume: Mapped[Optional[float]] = mapped_column(Float)  # vs 20-day avg
    vwap: Mapped[Optional[float]] = mapped_column(Float)
    dollar_volume: Mapped[Optional[float]] = mapped_column(Float)
    change_pct: Mapped[Optional[float]] = mapped_column(Float)
    gap_pct: Mapped[Optional[float]] = mapped_column(Float)  # gap from prev close

    # Timeframe
    interval: Mapped[str] = mapped_column(String(10), default="1d")  # 1m, 5m, 1h, 1d
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship
    stock: Mapped["Stock"] = relationship("Stock", back_populates="prices",
                                          foreign_keys=[stock_id],
                                          primaryjoin="StockPrice.stock_id == Stock.id")

    def __repr__(self) -> str:
        return f"<StockPrice {self.ticker} @ {self.timestamp}>"


class StockFundamentals(Base):
    """Fundamental financial metrics for a stock."""

    __tablename__ = "stock_fundamentals"
    __table_args__ = (
        Index("ix_fundamentals_ticker_date", "ticker", "report_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    stock_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)

    # Valuation
    pe_ratio: Mapped[Optional[float]] = mapped_column(Float)
    forward_pe: Mapped[Optional[float]] = mapped_column(Float)
    pb_ratio: Mapped[Optional[float]] = mapped_column(Float)
    ps_ratio: Mapped[Optional[float]] = mapped_column(Float)
    peg_ratio: Mapped[Optional[float]] = mapped_column(Float)
    ev_ebitda: Mapped[Optional[float]] = mapped_column(Float)

    # Per-share metrics
    eps: Mapped[Optional[float]] = mapped_column(Float)
    eps_ttm: Mapped[Optional[float]] = mapped_column(Float)
    eps_growth_yoy: Mapped[Optional[float]] = mapped_column(Float)
    book_value_per_share: Mapped[Optional[float]] = mapped_column(Float)
    dividend_yield: Mapped[Optional[float]] = mapped_column(Float)

    # Income statement
    revenue: Mapped[Optional[float]] = mapped_column(Float)
    revenue_growth_yoy: Mapped[Optional[float]] = mapped_column(Float)
    revenue_growth_qoq: Mapped[Optional[float]] = mapped_column(Float)
    gross_margin: Mapped[Optional[float]] = mapped_column(Float)
    operating_margin: Mapped[Optional[float]] = mapped_column(Float)
    net_margin: Mapped[Optional[float]] = mapped_column(Float)
    ebitda: Mapped[Optional[float]] = mapped_column(Float)

    # Balance sheet
    total_debt: Mapped[Optional[float]] = mapped_column(Float)
    total_cash: Mapped[Optional[float]] = mapped_column(Float)
    debt_to_equity: Mapped[Optional[float]] = mapped_column(Float)
    current_ratio: Mapped[Optional[float]] = mapped_column(Float)
    quick_ratio: Mapped[Optional[float]] = mapped_column(Float)

    # Cash flow
    free_cash_flow: Mapped[Optional[float]] = mapped_column(Float)
    operating_cash_flow: Mapped[Optional[float]] = mapped_column(Float)

    # 52-week
    week_52_high: Mapped[Optional[float]] = mapped_column(Float)
    week_52_low: Mapped[Optional[float]] = mapped_column(Float)
    week_52_high_pct: Mapped[Optional[float]] = mapped_column(Float)
    week_52_low_pct: Mapped[Optional[float]] = mapped_column(Float)

    # Short interest
    short_ratio: Mapped[Optional[float]] = mapped_column(Float)
    short_float_pct: Mapped[Optional[float]] = mapped_column(Float)

    # Institutional ownership
    institutional_ownership_pct: Mapped[Optional[float]] = mapped_column(Float)
    insider_ownership_pct: Mapped[Optional[float]] = mapped_column(Float)

    # Earnings
    next_earnings_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_earnings_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    earnings_surprise_pct: Mapped[Optional[float]] = mapped_column(Float)

    report_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    stock: Mapped["Stock"] = relationship(
        "Stock", back_populates="fundamentals",
        foreign_keys=[stock_id],
        primaryjoin="StockFundamentals.stock_id == Stock.id"
    )
