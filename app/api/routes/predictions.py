"""Prediction endpoints."""
from __future__ import annotations

import asyncio
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from app.core.cache import cache
from app.core.database import AsyncSessionLocal
from app.services.prediction_engine import NightlyScanner, PredictionEngine

router = APIRouter()
_scanner = NightlyScanner()
_engine = PredictionEngine()


@router.get("/tonight")
async def get_tonight_predictions():
    """Return tonight's ranked AI picks. Runs a quick scan if cache is empty."""
    cached = cache.get("tonight_predictions")
    if cached:
        return {"predictions": cached, "generated_at": cache.get("tonight_generated_at"), "from_cache": True}

    # Run a fast scan on the top 30 tickers
    from app.services.market_data import NASDAQ_TICKERS
    top_tickers = NASDAQ_TICKERS[:30]
    tasks = [_engine.generate_prediction(t) for t in top_tickers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    predictions = [r for r in results if isinstance(r, dict)]
    predictions.sort(key=lambda x: x["confidence_score"], reverse=True)

    for i, p in enumerate(predictions[:10]):
        p["recommendation_type"] = "primary" if i == 0 else ("secondary" if i < 3 else "watchlist")

    top = predictions[:10]
    cache.set("tonight_predictions", top, ttl=1800)
    cache.set("tonight_generated_at", datetime.utcnow().isoformat(), ttl=1800)

    if not top:
        return {
            "predictions": [],
            "no_trade_day": True,
            "message": "No strong setup detected for tomorrow. Confidence thresholds not met across scanned universe.",
            "generated_at": datetime.utcnow().isoformat(),
        }
    return {"predictions": top, "generated_at": datetime.utcnow().isoformat(), "from_cache": False}


@router.get("/history")
async def get_prediction_history(limit: int = Query(50, le=200), offset: int = 0):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT * FROM predictions ORDER BY created_at DESC LIMIT :limit OFFSET :offset"),
            {"limit": limit, "offset": offset}
        )
        rows = [dict(r) for r in result.mappings().all()]
    return {"predictions": rows, "total": len(rows)}


@router.get("/performance")
async def get_model_performance():
    async with AsyncSessionLocal() as session:
        total = (await session.execute(text("SELECT COUNT(*) FROM predictions"))).scalar() or 0
        wins = (await session.execute(
            text("SELECT COUNT(*) FROM predictions WHERE actual_outcome = 'win'")
        )).scalar() or 0
        avg_conf = (await session.execute(
            text("SELECT AVG(confidence_score) FROM predictions")
        )).scalar() or 0
    win_rate = (wins / total * 100) if total > 0 else 0
    return {
        "total_predictions": total,
        "wins": wins,
        "win_rate": round(win_rate, 1),
        "avg_confidence": round(float(avg_conf), 1),
        "signal_weights": {
            "technical": 35, "sentiment": 20, "volume": 20,
            "momentum": 15, "macro": 10,
        },
    }


@router.post("/scan")
async def trigger_manual_scan():
    """Trigger a full nightly scan immediately (runs in background)."""
    cache.delete("tonight_predictions")

    async def _bg():
        try:
            await _scanner.run()
        except Exception:
            pass

    asyncio.create_task(_bg())
    return {"status": "scan_started", "message": "Full NASDAQ scan initiated. Results available in ~2 minutes."}


@router.get("/{ticker}")
async def get_prediction_for_ticker(ticker: str):
    pred = await _engine.generate_prediction(ticker.upper())
    if not pred:
        raise HTTPException(status_code=404, detail=f"No confident prediction generated for {ticker.upper()}")
    return pred
