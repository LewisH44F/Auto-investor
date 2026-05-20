"""Watchlist endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.services.market_data import MarketDataService

router = APIRouter()
svc = MarketDataService()


class WatchlistItem(BaseModel):
    ticker: str
    notes: str = ""


@router.get("/")
async def get_watchlist():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT * FROM watchlist ORDER BY created_at DESC"))
        items = [dict(r) for r in result.mappings().all()]
    # Enrich with live prices
    enriched = []
    for item in items:
        quote = await svc.get_quote(item["ticker"])
        enriched.append({**item, "current_price": quote.get("price", 0), "change_pct": quote.get("change_pct", 0)})
    return {"watchlist": enriched}


@router.post("/")
async def add_to_watchlist(item: WatchlistItem):
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("INSERT OR IGNORE INTO watchlist (ticker, notes, created_at) VALUES (:ticker, :notes, datetime('now'))"),
            {"ticker": item.ticker.upper(), "notes": item.notes}
        )
        await session.commit()
    return {"status": "added", "ticker": item.ticker.upper()}


@router.delete("/{ticker}")
async def remove_from_watchlist(ticker: str):
    async with AsyncSessionLocal() as session:
        await session.execute(
            text("DELETE FROM watchlist WHERE ticker = :ticker"), {"ticker": ticker.upper()}
        )
        await session.commit()
    return {"status": "removed", "ticker": ticker.upper()}
