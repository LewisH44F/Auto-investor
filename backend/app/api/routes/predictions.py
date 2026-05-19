"""Prediction API routes."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.redis_client import cache_get, cache_set
from app.models.prediction import Prediction
from app.schemas.prediction import (
    ManualScanRequest,
    ManualScanResponse,
    PredictionPerformance,
    PredictionRead,
    PredictionSummary,
    TonightPredictions,
)

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/tonight", response_model=TonightPredictions)
async def get_tonight_predictions(
    db: AsyncSession = Depends(get_session),
) -> TonightPredictions:
    """Return tonight's AI-generated picks (primary, secondary, watchlist)."""
    cache_key = "predictions:tonight"
    cached = await cache_get(cache_key)
    if cached:
        return TonightPredictions(**cached)

    today = datetime.now(timezone.utc).date()
    result = await db.execute(
        select(Prediction)
        .where(func.date(Prediction.prediction_date) == today)
        .order_by(desc(Prediction.confidence_score))
    )
    preds = result.scalars().all()

    primary_pred = next(
        (p for p in preds if p.recommendation_type == "primary"), None
    )
    secondary_preds = [p for p in preds if p.recommendation_type == "secondary"][:3]
    watchlist_preds = [p for p in preds if p.recommendation_type == "watchlist"][:10]

    avg_conf = (
        sum(p.confidence_score for p in preds) / len(preds) if preds else 0.0
    )

    response = TonightPredictions(
        primary=PredictionRead.model_validate(primary_pred) if primary_pred else None,
        secondary=[PredictionRead.model_validate(p) for p in secondary_preds],
        watchlist=[PredictionRead.model_validate(p) for p in watchlist_preds],
        generated_at=datetime.now(timezone.utc),
        model_confidence=round(avg_conf, 2),
        total_stocks_scanned=len(preds),
    )

    await cache_set(cache_key, response.model_dump(mode="json"), ttl=300)
    return response


@router.get("/history", response_model=List[PredictionSummary])
async def get_prediction_history(
    days: int = Query(default=30, ge=1, le=365),
    recommendation_type: Optional[str] = Query(default=None),
    ticker: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_session),
) -> List[PredictionSummary]:
    """Historical predictions with optional filters."""
    from sqlalchemy import and_, text

    query = select(Prediction).order_by(desc(Prediction.prediction_date))

    filters = []
    if recommendation_type:
        filters.append(Prediction.recommendation_type == recommendation_type)
    if ticker:
        filters.append(Prediction.ticker == ticker.upper())

    if filters:
        query = query.where(and_(*filters))

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    preds = result.scalars().all()

    return [PredictionSummary.model_validate(p) for p in preds]


@router.get("/performance", response_model=PredictionPerformance)
async def get_prediction_performance(
    days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_session),
) -> PredictionPerformance:
    """Model performance stats over a given period."""
    cache_key = f"predictions:performance:{days}"
    cached = await cache_get(cache_key)
    if cached:
        return PredictionPerformance(**cached)

    result = await db.execute(
        select(Prediction).where(Prediction.is_outcome_recorded == True)
    )
    preds = result.scalars().all()

    wins = [p for p in preds if p.actual_outcome == "win"]
    losses = [p for p in preds if p.actual_outcome == "loss"]
    total = len(preds)

    win_rate = len(wins) / total * 100 if total > 0 else 0.0
    avg_return = (
        sum(p.actual_move_pct or 0 for p in preds) / total if total > 0 else 0.0
    )
    avg_conf = (
        sum(p.confidence_score for p in preds) / total if total > 0 else 0.0
    )

    performance = PredictionPerformance(
        period_days=days,
        total_predictions=total,
        win_rate=round(win_rate, 2),
        avg_return_pct=round(avg_return, 2),
        avg_confidence=round(avg_conf, 2),
        signal_breakdown={},
        recent_trend="stable",
    )

    await cache_set(cache_key, performance.model_dump(mode="json"), ttl=600)
    return performance


@router.get("/{prediction_id}", response_model=PredictionRead)
async def get_prediction(
    prediction_id: int,
    db: AsyncSession = Depends(get_session),
) -> PredictionRead:
    """Get a single prediction by ID."""
    result = await db.execute(
        select(Prediction).where(Prediction.id == prediction_id)
    )
    pred = result.scalar_one_or_none()
    if pred is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prediction not found")
    return PredictionRead.model_validate(pred)


@router.post("/manual-scan", response_model=ManualScanResponse)
async def trigger_manual_scan(
    request: ManualScanRequest,
    db: AsyncSession = Depends(get_session),
) -> ManualScanResponse:
    """Trigger an on-demand prediction scan."""
    from app.services.ml.prediction_engine import PredictionEngine
    from app.services.data_ingestion.market_data import MarketDataService

    start_time = time.time()

    tickers = request.tickers
    if not tickers:
        market_svc = MarketDataService()
        tickers = await market_svc.get_watchlist_tickers(limit=20)

    engine = PredictionEngine()
    predictions_out = []

    for ticker in tickers:
        try:
            pred = await engine.predict(ticker, db=db)
            if pred and pred.confidence_score >= request.min_confidence:
                predictions_out.append(PredictionRead.model_validate(pred))
        except Exception as exc:
            from loguru import logger
            logger.warning("Manual scan failed for {}: {}", ticker, exc)

    elapsed = time.time() - start_time

    return ManualScanResponse(
        predictions=sorted(predictions_out, key=lambda p: p.confidence_score, reverse=True),
        scan_duration_seconds=round(elapsed, 2),
        tickers_scanned=len(tickers),
    )
