"""Watchlist API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.core.redis_client import cache_delete, cache_get, cache_set

router = APIRouter(prefix="/watchlist", tags=["watchlist"])

WATCHLIST_KEY = "watchlist:tickers"


class WatchlistItem(BaseModel):
    ticker: str
    added_at: str
    notes: str = ""


class WatchlistResponse(BaseModel):
    tickers: List[WatchlistItem]
    count: int


@router.get("/", response_model=WatchlistResponse)
async def get_watchlist() -> WatchlistResponse:
    """Get all watchlisted tickers."""
    data = await cache_get(WATCHLIST_KEY) or []
    return WatchlistResponse(tickers=data, count=len(data))


@router.post("/{ticker}")
async def add_to_watchlist(
    ticker: str,
    notes: str = Query(default=""),
) -> Dict[str, Any]:
    """Add a ticker to the watchlist."""
    ticker = ticker.upper()
    data: List[Dict] = await cache_get(WATCHLIST_KEY) or []

    if not any(item["ticker"] == ticker for item in data):
        data.append(
            {
                "ticker": ticker,
                "added_at": datetime.now(timezone.utc).isoformat(),
                "notes": notes,
            }
        )
        await cache_set(WATCHLIST_KEY, data, ttl=86400 * 30)

    return {"status": "added", "ticker": ticker}


@router.delete("/{ticker}")
async def remove_from_watchlist(ticker: str) -> Dict[str, Any]:
    """Remove a ticker from the watchlist."""
    ticker = ticker.upper()
    data: List[Dict] = await cache_get(WATCHLIST_KEY) or []
    data = [item for item in data if item["ticker"] != ticker]
    await cache_set(WATCHLIST_KEY, data, ttl=86400 * 30)
    return {"status": "removed", "ticker": ticker}


@router.get("/{ticker}/analysis")
async def get_watchlist_ticker_analysis(ticker: str) -> Dict[str, Any]:
    """Quick analysis for a watchlisted ticker."""
    from app.services.ml.prediction_engine import PredictionEngine

    ticker = ticker.upper()
    engine = PredictionEngine()
    pred = await engine.predict(ticker)

    if pred is None:
        return {"ticker": ticker, "status": "insufficient_data", "analysis": None}

    return {
        "ticker": ticker,
        "status": "analysed",
        "confidence_score": pred.confidence_score,
        "technical_score": pred.technical_score,
        "sentiment_score": pred.sentiment_score,
        "momentum_score": pred.momentum_score,
        "recommendation": pred.recommendation_type,
        "plain_english": pred.plain_english_explanation,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
