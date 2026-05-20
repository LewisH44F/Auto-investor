"""Chart data endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Query
from app.services.market_data import MarketDataService
from app.core.cache import cached

router = APIRouter()
svc = MarketDataService()


@router.get("/price/{ticker}")
async def get_price_chart(
    ticker: str,
    period: str = Query("3mo", regex="^(5d|1mo|3mo|6mo|1y|2y)$"),
):
    df = await svc.fetch_ohlcv(ticker.upper(), period=period)
    if df is None or df.empty:
        return {"ticker": ticker, "candles": []}

    candles = []
    for ts, row in df.iterrows():
        candles.append({
            "date": str(ts)[:10],
            "open": round(float(row.get("Open", 0)), 2),
            "high": round(float(row.get("High", 0)), 2),
            "low": round(float(row.get("Low", 0)), 2),
            "close": round(float(row.get("Close", 0)), 2),
            "volume": int(row.get("Volume", 0)),
        })
    return {"ticker": ticker.upper(), "period": period, "candles": candles}


@router.get("/sector-heatmap")
async def get_sector_heatmap():
    macro = await svc.get_macro_snapshot()
    sectors = macro.get("sector_performance", {})
    return {
        "sectors": [
            {"name": name, "change_pct": chg, "etf": _sector_etf(name)}
            for name, chg in sectors.items()
        ]
    }


@router.get("/market-overview")
async def get_market_overview():
    return await svc.get_macro_snapshot()


def _sector_etf(sector: str) -> str:
    mapping = {
        "Technology": "XLK", "Financials": "XLF", "Energy": "XLE",
        "Healthcare": "XLV", "Consumer Discretionary": "XLY",
        "Consumer Staples": "XLP", "Industrials": "XLI",
        "Utilities": "XLU", "Real Estate": "XLRE",
        "Materials": "XLB", "Communication Services": "XLC",
    }
    return mapping.get(sector, "SPY")
