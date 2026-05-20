"""Portfolio CRUD endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services.portfolio_tracker import PortfolioTracker

router = APIRouter()
tracker = PortfolioTracker()


class AddHoldingRequest(BaseModel):
    ticker: str
    shares: float
    purchase_price: float
    notes: Optional[str] = ""


class CloseHoldingRequest(BaseModel):
    sell_price: float


@router.get("/holdings")
async def get_holdings():
    holdings = await tracker.get_holdings()
    return {"holdings": holdings}


@router.post("/holdings")
async def add_holding(req: AddHoldingRequest):
    result = await tracker.add_holding(req.ticker, req.shares, req.purchase_price, req.notes or "")
    return result


@router.post("/holdings/{holding_id}/close")
async def close_holding(holding_id: int, req: CloseHoldingRequest):
    result = await tracker.close_holding(holding_id, req.sell_price)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/metrics")
async def get_portfolio_metrics():
    return await tracker.get_portfolio_metrics()


@router.get("/recommendations")
async def get_portfolio_recommendations():
    holdings = await tracker.get_holdings()
    recs = [
        {
            "ticker": h["ticker"],
            "recommendation": h["ai_recommendation"],
            "reasoning": h["reasoning"],
            "conviction_score": h["conviction_score"],
            "unrealized_pnl_pct": h["unrealized_pnl_pct"],
        }
        for h in holdings
    ]
    return {"recommendations": recs}
