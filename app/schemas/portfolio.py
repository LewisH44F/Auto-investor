"""Portfolio-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class HoldingCreate(BaseModel):
    ticker: str
    shares: float = Field(gt=0)
    purchase_price: float = Field(gt=0)
    purchase_date: datetime
    notes: Optional[str] = None
    stop_loss_price: Optional[float] = None
    target_price: Optional[float] = None


class HoldingUpdate(BaseModel):
    shares: Optional[float] = None
    purchase_price: Optional[float] = None
    notes: Optional[str] = None
    stop_loss_price: Optional[float] = None
    target_price: Optional[float] = None


class HoldingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    shares: float
    purchase_price: float
    purchase_date: datetime
    notes: Optional[str] = None

    current_price: Optional[float] = None
    current_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    cost_basis: Optional[float] = None

    ai_recommendation: Optional[str] = None
    conviction_score: Optional[float] = None
    ai_reasoning: Optional[str] = None
    stop_loss_price: Optional[float] = None
    target_price: Optional[float] = None
    last_assessed: Optional[datetime] = None

    is_active: bool
    is_ai_initiated: bool
    created_at: datetime


class TransactionCreate(BaseModel):
    ticker: str
    transaction_type: str = Field(pattern="^(buy|sell)$")
    shares: float = Field(gt=0)
    price: float = Field(gt=0)
    commission: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    transaction_type: str
    shares: float
    price: float
    total_amount: Optional[float] = None
    commission: float
    notes: Optional[str] = None
    realized_pnl: Optional[float] = None
    realized_pnl_pct: Optional[float] = None
    timestamp: datetime


class PortfolioMetricsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: datetime
    total_value: float
    cash: float
    invested: float
    num_positions: int
    total_pnl: float
    total_pnl_pct: float
    day_pnl: Optional[float] = None
    day_pnl_pct: Optional[float] = None
    win_rate: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    var_95: Optional[float] = None
    sector_allocations: Optional[Dict[str, Any]] = None


class PortfolioSummary(BaseModel):
    total_value: float
    cash: float
    invested: float
    total_pnl: float
    total_pnl_pct: float
    day_pnl: float
    day_pnl_pct: float
    num_positions: int
    win_rate: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    holdings: List[HoldingRead] = Field(default_factory=list)
    sector_allocations: Dict[str, float] = Field(default_factory=dict)
    updated_at: datetime


class HoldingRecommendation(BaseModel):
    ticker: str
    holding_id: int
    recommendation: str
    conviction_score: float
    reasoning: str
    current_price: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    assessed_at: datetime
