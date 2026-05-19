"""Analytics-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class WinRateResponse(BaseModel):
    """Overall win-rate analytics."""

    period_days: int
    total_predictions: int
    wins: int
    losses: int
    neutral: int
    win_rate: float
    avg_win_pct: float
    avg_loss_pct: float
    profit_factor: float
    by_recommendation_type: Dict[str, Any] = {}
    by_signal_type: Dict[str, Any] = {}
    by_sector: Dict[str, Any] = {}
    calculated_at: datetime


class SignalPerformance(BaseModel):
    """Performance breakdown by signal type."""

    signal_name: str
    occurrences: int
    win_rate: float
    avg_return: float
    current_weight: float
    suggested_weight: Optional[float] = None


class SignalPerformanceResponse(BaseModel):
    signals: List[SignalPerformance]
    last_updated: datetime


class PatternHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pattern_name: str
    description: Optional[str] = None
    category: Optional[str] = None
    occurrences: int
    win_rate: Optional[float] = None
    avg_return: Optional[float] = None
    confidence_adjustment: float
    last_seen: Optional[datetime] = None


class ModelEvolutionPoint(BaseModel):
    date: datetime
    win_rate: float
    avg_confidence: float
    avg_return: float
    sharpe: Optional[float] = None
    notes: Optional[str] = None


class ModelEvolutionResponse(BaseModel):
    history: List[ModelEvolutionPoint]
    current_version: str
    total_predictions: int
    improvement_trend: str  # improving / stable / declining


class BacktestRequest(BaseModel):
    ticker: str
    start_date: str  # YYYY-MM-DD
    end_date: str
    initial_capital: float = 10000.0
    position_size_pct: float = 10.0


class BacktestResult(BaseModel):
    ticker: str
    start_date: str
    end_date: str
    initial_capital: float
    final_capital: float
    total_return_pct: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win_pct: float
    avg_loss_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    profit_factor: float
    avg_hold_days: float
    trade_log: List[Dict[str, Any]] = []
