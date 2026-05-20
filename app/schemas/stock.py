"""Stock-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class StockRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    is_nasdaq: bool = True
    is_active: bool = True
    float_shares: Optional[float] = None
    exchange: Optional[str] = None
    last_updated: Optional[datetime] = None
    created_at: datetime


class StockQuote(BaseModel):
    ticker: str
    price: float
    change: float
    change_pct: float
    volume: int
    avg_volume: Optional[int] = None
    relative_volume: Optional[float] = None
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    timestamp: datetime
