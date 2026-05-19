"""Analytics API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.redis_client import cache_get, cache_set
from app.models.learning import ModelPerformance, PatternRecord
from app.models.prediction import Prediction
from app.schemas.analytics import (
    BacktestRequest,
    BacktestResult,
    ModelEvolutionPoint,
    ModelEvolutionResponse,
    PatternHistoryItem,
    SignalPerformance,
    SignalPerformanceResponse,
    WinRateResponse,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/win-rate", response_model=WinRateResponse)
async def get_win_rate(
    days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_session),
) -> WinRateResponse:
    """Overall win-rate analytics."""
    cache_key = f"analytics:win_rate:{days}"
    cached = await cache_get(cache_key)
    if cached:
        return WinRateResponse(**cached)

    result = await db.execute(
        select(Prediction).where(Prediction.is_outcome_recorded == True)
    )
    preds = result.scalars().all()

    wins = [p for p in preds if p.actual_outcome == "win"]
    losses = [p for p in preds if p.actual_outcome == "loss"]
    neutral = [p for p in preds if p.actual_outcome == "neutral"]
    total = len(preds)

    avg_win = sum(p.actual_move_pct or 0 for p in wins) / len(wins) if wins else 0.0
    avg_loss = sum(p.actual_move_pct or 0 for p in losses) / len(losses) if losses else 0.0
    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0

    response = WinRateResponse(
        period_days=days,
        total_predictions=total,
        wins=len(wins),
        losses=len(losses),
        neutral=len(neutral),
        win_rate=len(wins) / total * 100 if total > 0 else 0.0,
        avg_win_pct=round(avg_win, 2),
        avg_loss_pct=round(avg_loss, 2),
        profit_factor=round(profit_factor, 2),
        by_recommendation_type={},
        by_signal_type={},
        by_sector={},
        calculated_at=datetime.now(timezone.utc),
    )

    await cache_set(cache_key, response.model_dump(mode="json"), ttl=600)
    return response


@router.get("/signal-performance", response_model=SignalPerformanceResponse)
async def get_signal_performance(
    db: AsyncSession = Depends(get_session),
) -> SignalPerformanceResponse:
    """Performance breakdown by signal type."""
    cache_key = "analytics:signal_performance"
    cached = await cache_get(cache_key)
    if cached:
        return SignalPerformanceResponse(**cached)

    # Default signal weights
    default_signals = [
        SignalPerformance(signal_name="technical", occurrences=0, win_rate=0.0,
                          avg_return=0.0, current_weight=0.25),
        SignalPerformance(signal_name="sentiment", occurrences=0, win_rate=0.0,
                          avg_return=0.0, current_weight=0.20),
        SignalPerformance(signal_name="momentum", occurrences=0, win_rate=0.0,
                          avg_return=0.0, current_weight=0.20),
        SignalPerformance(signal_name="catalyst", occurrences=0, win_rate=0.0,
                          avg_return=0.0, current_weight=0.20),
        SignalPerformance(signal_name="macro", occurrences=0, win_rate=0.0,
                          avg_return=0.0, current_weight=0.10),
        SignalPerformance(signal_name="volume_anomaly", occurrences=0, win_rate=0.0,
                          avg_return=0.0, current_weight=0.05),
    ]

    response = SignalPerformanceResponse(
        signals=default_signals,
        last_updated=datetime.now(timezone.utc),
    )
    await cache_set(cache_key, response.model_dump(mode="json"), ttl=3600)
    return response


@router.get("/pattern-history", response_model=List[PatternHistoryItem])
async def get_pattern_history(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
) -> List[PatternHistoryItem]:
    """Detected patterns and their success rates."""
    result = await db.execute(
        select(PatternRecord)
        .order_by(desc(PatternRecord.win_rate))
        .limit(limit)
    )
    patterns = result.scalars().all()
    return [PatternHistoryItem.model_validate(p) for p in patterns]


@router.get("/model-evolution", response_model=ModelEvolutionResponse)
async def get_model_evolution(
    days: int = Query(default=90, ge=7, le=365),
    db: AsyncSession = Depends(get_session),
) -> ModelEvolutionResponse:
    """How model performance has changed over time."""
    result = await db.execute(
        select(ModelPerformance)
        .order_by(desc(ModelPerformance.date))
        .limit(days)
    )
    records = result.scalars().all()

    history = [
        ModelEvolutionPoint(
            date=r.date,
            win_rate=r.win_rate or 0.0,
            avg_confidence=r.avg_confidence or 0.0,
            avg_return=r.avg_return or 0.0,
            sharpe=r.sharpe,
            notes=r.notes,
        )
        for r in reversed(records)
    ]

    return ModelEvolutionResponse(
        history=history,
        current_version="1.0.0",
        total_predictions=sum(r.total_predictions or 0 for r in records),
        improvement_trend="stable",
    )


@router.post("/backtest", response_model=BacktestResult)
async def run_backtest(
    request: BacktestRequest,
    db: AsyncSession = Depends(get_session),
) -> BacktestResult:
    """Run backtesting simulation for a ticker."""
    from app.services.ml.backtesting import BacktestEngine

    engine = BacktestEngine()
    result = await engine.run_backtest(
        ticker=request.ticker.upper(),
        start_date=request.start_date,
        end_date=request.end_date,
        initial_capital=request.initial_capital,
        position_size_pct=request.position_size_pct,
    )
    return result
