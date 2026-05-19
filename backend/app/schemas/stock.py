"""Stock-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StockBase(BaseModel):
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    is_nasdaq: bool = True
    is_active: bool = True


class StockCreate(StockBase):
    pass


class StockRead(StockBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    float_shares: Optional[float] = None
    exchange: Optional[str] = None
    last_updated: Optional[datetime] = None
    created_at: datetime


class StockPriceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: float
    volume: Optional[int] = None
    relative_volume: Optional[float] = None
    vwap: Optional[float] = None
    change_pct: Optional[float] = None
    gap_pct: Optional[float] = None
    pre_market_price: Optional[float] = None
    after_hours_price: Optional[float] = None
    interval: str
    timestamp: datetime


class StockQuote(BaseModel):
    """Real-time quote snapshot."""

    ticker: str
    price: float
    change: float
    change_pct: float
    volume: int
    avg_volume: Optional[int] = None
    relative_volume: Optional[float] = None
    pre_market_price: Optional[float] = None
    after_hours_price: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    timestamp: datetime


class StockFundamentalsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    pe_ratio: Optional[float] = None
    forward_pe: Optional[float] = None
    eps: Optional[float] = None
    eps_growth_yoy: Optional[float] = None
    revenue_growth_yoy: Optional[float] = None
    gross_margin: Optional[float] = None
    net_margin: Optional[float] = None
    debt_to_equity: Optional[float] = None
    free_cash_flow: Optional[float] = None
    dividend_yield: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    short_float_pct: Optional[float] = None
    institutional_ownership_pct: Optional[float] = None
    next_earnings_date: Optional[datetime] = None
    earnings_surprise_pct: Optional[float] = None
    report_date: Optional[datetime] = None
