"""Portfolio management API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.redis_client import cache_delete_pattern, cache_get, cache_set
from app.models.portfolio import Holding, PortfolioMetrics, Transaction
from app.schemas.portfolio import (
    HoldingCreate,
    HoldingRead,
    HoldingRecommendation,
    HoldingUpdate,
    PortfolioMetricsRead,
    PortfolioSummary,
    TransactionCreate,
    TransactionRead,
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/holdings", response_model=List[HoldingRead])
async def get_holdings(
    active_only: bool = True,
    db: AsyncSession = Depends(get_session),
) -> List[HoldingRead]:
    """Return all portfolio holdings."""
    query = select(Holding)
    if active_only:
        query = query.where(Holding.is_active == True)
    result = await db.execute(query)
    holdings = result.scalars().all()
    return [HoldingRead.model_validate(h) for h in holdings]


@router.post("/holdings", response_model=HoldingRead, status_code=status.HTTP_201_CREATED)
async def add_holding(
    payload: HoldingCreate,
    db: AsyncSession = Depends(get_session),
) -> HoldingRead:
    """Add a new holding to the portfolio."""
    holding = Holding(
        ticker=payload.ticker.upper(),
        shares=payload.shares,
        purchase_price=payload.purchase_price,
        purchase_date=payload.purchase_date,
        notes=payload.notes,
        stop_loss_price=payload.stop_loss_price,
        target_price=payload.target_price,
        cost_basis=payload.shares * payload.purchase_price,
    )
    db.add(holding)
    await db.flush()
    await db.refresh(holding)
    await cache_delete_pattern("portfolio:*")
    return HoldingRead.model_validate(holding)


@router.put("/holdings/{holding_id}", response_model=HoldingRead)
async def update_holding(
    holding_id: int,
    payload: HoldingUpdate,
    db: AsyncSession = Depends(get_session),
) -> HoldingRead:
    """Update an existing holding."""
    result = await db.execute(select(Holding).where(Holding.id == holding_id))
    holding = result.scalar_one_or_none()
    if holding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(holding, field, value)

    await db.flush()
    await db.refresh(holding)
    await cache_delete_pattern("portfolio:*")
    return HoldingRead.model_validate(holding)


@router.delete("/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_holding(
    holding_id: int,
    db: AsyncSession = Depends(get_session),
) -> None:
    """Soft-delete a holding (mark as inactive)."""
    result = await db.execute(select(Holding).where(Holding.id == holding_id))
    holding = result.scalar_one_or_none()
    if holding is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found")

    holding.is_active = False
    await db.flush()
    await cache_delete_pattern("portfolio:*")


@router.post("/transactions", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
async def add_transaction(
    payload: TransactionCreate,
    db: AsyncSession = Depends(get_session),
) -> TransactionRead:
    """Record a buy/sell transaction."""
    tx = Transaction(
        ticker=payload.ticker.upper(),
        transaction_type=payload.transaction_type,
        shares=payload.shares,
        price=payload.price,
        total_amount=payload.shares * payload.price + payload.commission,
        commission=payload.commission,
        notes=payload.notes,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(tx)
    await db.flush()
    await db.refresh(tx)
    await cache_delete_pattern("portfolio:*")
    return TransactionRead.model_validate(tx)


@router.get("/transactions", response_model=List[TransactionRead])
async def get_transactions(
    ticker: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_session),
) -> List[TransactionRead]:
    """List transactions with optional ticker filter."""
    from sqlalchemy import desc

    query = select(Transaction).order_by(desc(Transaction.timestamp)).limit(limit)
    if ticker:
        query = query.where(Transaction.ticker == ticker.upper())
    result = await db.execute(query)
    txs = result.scalars().all()
    return [TransactionRead.model_validate(tx) for tx in txs]


@router.get("/metrics", response_model=Optional[PortfolioMetricsRead])
async def get_portfolio_metrics(
    db: AsyncSession = Depends(get_session),
) -> Optional[PortfolioMetricsRead]:
    """Return the latest portfolio metrics snapshot."""
    from sqlalchemy import desc

    result = await db.execute(
        select(PortfolioMetrics).order_by(desc(PortfolioMetrics.date)).limit(1)
    )
    metrics = result.scalar_one_or_none()
    if metrics is None:
        return None
    return PortfolioMetricsRead.model_validate(metrics)


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    db: AsyncSession = Depends(get_session),
) -> PortfolioSummary:
    """Full portfolio dashboard summary with live prices."""
    cache_key = "portfolio:summary"
    cached = await cache_get(cache_key)
    if cached:
        return PortfolioSummary(**cached)

    from app.services.portfolio.tracker import PortfolioTracker

    tracker = PortfolioTracker()
    summary = await tracker.get_summary(db)

    await cache_set(cache_key, summary.model_dump(mode="json"), ttl=120)
    return summary


@router.get("/recommendations", response_model=List[HoldingRecommendation])
async def get_holding_recommendations(
    db: AsyncSession = Depends(get_session),
) -> List[HoldingRecommendation]:
    """AI recommendations for all current holdings."""
    from app.services.portfolio.tracker import PortfolioTracker

    tracker = PortfolioTracker()
    recs = await tracker.get_ai_recommendations(db)
    return recs
