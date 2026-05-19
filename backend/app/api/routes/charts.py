"""Chart data API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.redis_client import cache_get, cache_set

router = APIRouter(prefix="/charts", tags=["charts"])

VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"}


@router.get("/price/{ticker}")
async def get_price_chart(
    ticker: str,
    period: str = Query(default="1mo", pattern="^(1d|5d|1mo|3mo|6mo|1y|2y|5y)$"),
    interval: str = Query(default="1d", pattern="^(1m|5m|15m|1h|1d|1wk|1mo)$"),
) -> Dict[str, Any]:
    """OHLCV price data for charting."""
    ticker = ticker.upper()
    cache_key = f"charts:price:{ticker}:{period}:{interval}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    from app.services.data_ingestion.market_data import MarketDataService

    market_svc = MarketDataService()
    data = await market_svc.fetch_ohlcv(ticker, period=period, interval=interval)

    if data is None or data.empty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price data found for {ticker}",
        )

    result = {
        "ticker": ticker,
        "period": period,
        "interval": interval,
        "timestamps": data.index.strftime("%Y-%m-%dT%H:%M:%SZ").tolist(),
        "open": data["Open"].round(4).tolist(),
        "high": data["High"].round(4).tolist(),
        "low": data["Low"].round(4).tolist(),
        "close": data["Close"].round(4).tolist(),
        "volume": data["Volume"].fillna(0).astype(int).tolist(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    ttl = 60 if period == "1d" else 300
    await cache_set(cache_key, result, ttl=ttl)
    return result


@router.get("/predictions-overlay/{ticker}")
async def get_predictions_overlay(
    ticker: str,
    days: int = Query(default=30, ge=7, le=365),
    db: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Price data with prediction entry/exit zones overlaid."""
    ticker = ticker.upper()
    cache_key = f"charts:predictions_overlay:{ticker}:{days}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    from sqlalchemy import desc, select
    from app.models.prediction import Prediction
    from app.services.data_ingestion.market_data import MarketDataService

    market_svc = MarketDataService()
    price_data = await market_svc.fetch_ohlcv(ticker, period="3mo", interval="1d")

    result_db = await db.execute(
        select(Prediction)
        .where(Prediction.ticker == ticker)
        .order_by(desc(Prediction.prediction_date))
        .limit(days)
    )
    preds = result_db.scalars().all()

    overlay_points = [
        {
            "date": p.prediction_date.strftime("%Y-%m-%d"),
            "confidence": p.confidence_score,
            "type": p.recommendation_type,
            "entry_low": p.entry_zone_low,
            "entry_high": p.entry_zone_high,
            "stop_loss": p.stop_loss,
            "target_1": p.profit_target_1,
            "target_2": p.profit_target_2,
            "outcome": p.actual_outcome,
        }
        for p in preds
    ]

    result = {
        "ticker": ticker,
        "price_data": {
            "timestamps": price_data.index.strftime("%Y-%m-%d").tolist() if price_data is not None and not price_data.empty else [],
            "close": price_data["Close"].round(4).tolist() if price_data is not None and not price_data.empty else [],
        },
        "prediction_overlays": overlay_points,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    await cache_set(cache_key, result, ttl=300)
    return result


@router.get("/sector-heatmap")
async def get_sector_heatmap() -> Dict[str, Any]:
    """Sector performance heatmap data."""
    cache_key = "charts:sector_heatmap"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    from app.services.data_ingestion.macro_data import MacroDataService

    macro = MacroDataService()
    data = await macro.get_sector_performance()

    result = {
        "sectors": data,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    await cache_set(cache_key, result, ttl=300)
    return result


@router.get("/portfolio-allocation")
async def get_portfolio_allocation(
    db: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Portfolio allocation breakdown for pie chart."""
    from sqlalchemy import select
    from app.models.portfolio import Holding

    result = await db.execute(
        select(Holding).where(Holding.is_active == True)
    )
    holdings = result.scalars().all()

    if not holdings:
        return {
            "allocations": [],
            "total_value": 0,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    total_value = sum(h.current_value or (h.shares * h.purchase_price) for h in holdings)

    allocations = [
        {
            "ticker": h.ticker,
            "value": round(h.current_value or (h.shares * h.purchase_price), 2),
            "pct": round(
                (h.current_value or (h.shares * h.purchase_price)) / total_value * 100,
                2,
            ) if total_value > 0 else 0,
            "pnl_pct": h.unrealized_pnl_pct,
        }
        for h in holdings
    ]

    return {
        "allocations": sorted(allocations, key=lambda x: x["value"], reverse=True),
        "total_value": round(total_value, 2),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
