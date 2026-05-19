"""Backtesting API routes."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.analytics import BacktestRequest, BacktestResult

router = APIRouter(prefix="/backtesting", tags=["backtesting"])


@router.post("/run", response_model=BacktestResult)
async def run_backtest(
    request: BacktestRequest,
) -> BacktestResult:
    """Run a backtesting simulation for a given ticker and period."""
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


@router.get("/quick/{ticker}")
async def quick_backtest(
    ticker: str,
    period: str = Query(default="1y", pattern="^(3mo|6mo|1y|2y|5y)$"),
    initial_capital: float = Query(default=10000.0, gt=0),
) -> Dict[str, Any]:
    """Quick 1-click backtest with default settings."""
    from datetime import datetime, timedelta
    from app.services.ml.backtesting import BacktestEngine

    end_date = datetime.now().strftime("%Y-%m-%d")
    period_days = {
        "3mo": 90, "6mo": 180, "1y": 365, "2y": 730, "5y": 1825
    }[period]
    start_date = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d")

    engine = BacktestEngine()
    result = await engine.run_backtest(
        ticker=ticker.upper(),
        start_date=start_date,
        end_date=end_date,
        initial_capital=initial_capital,
    )
    return result.model_dump()


@router.get("/compare")
async def compare_backtests(
    tickers: str = Query(description="Comma-separated tickers e.g. AAPL,MSFT,NVDA"),
    period: str = Query(default="1y"),
) -> List[Dict[str, Any]]:
    """Compare backtests across multiple tickers."""
    from datetime import datetime, timedelta
    from app.services.ml.backtesting import BacktestEngine

    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()][:5]

    end_date = datetime.now().strftime("%Y-%m-%d")
    period_days = {"3mo": 90, "6mo": 180, "1y": 365, "2y": 730}.get(period, 365)
    start_date = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d")

    engine = BacktestEngine()
    results = []

    for ticker in ticker_list:
        try:
            res = await engine.run_backtest(ticker, start_date, end_date)
            results.append(res.model_dump())
        except Exception:
            results.append({"ticker": ticker, "error": "backtest_failed"})

    return sorted(results, key=lambda x: x.get("total_return_pct", 0), reverse=True)
