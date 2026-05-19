"""Macro data fetching service."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import yfinance as yf
from loguru import logger

MACRO_TICKERS = {
    "vix": "^VIX",
    "spy": "SPY",
    "qqq": "QQQ",
    "dia": "DIA",
    "iwm": "IWM",
    "tnx": "^TNX",   # 10-year yield
    "dxy": "DX-Y.NYB",  # Dollar index
    "gold": "GC=F",
    "oil": "CL=F",
}

SECTOR_ETFS: Dict[str, str] = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Financials": "XLF",
    "Energy": "XLE",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Industrials": "XLI",
    "Materials": "XLB",
    "Real Estate": "XLRE",
    "Utilities": "XLU",
    "Communication Services": "XLC",
}


class MacroDataService:
    """Service to fetch macro-economic and market-wide data."""

    async def _get_info(self, symbol: str) -> Dict[str, Any]:
        """Fetch yfinance info for a symbol."""
        try:
            loop = asyncio.get_event_loop()
            ticker = yf.Ticker(symbol)
            info = await loop.run_in_executor(None, lambda: ticker.fast_info)
            return {
                "price": getattr(info, "last_price", None),
                "previous_close": getattr(info, "previous_close", None),
                "symbol": symbol,
            }
        except Exception as exc:
            logger.debug("Macro data fetch failed for {}: {}", symbol, exc)
            return {"symbol": symbol, "price": None}

    async def get_vix(self) -> Optional[float]:
        """Get current VIX level."""
        info = await self._get_info("^VIX")
        price = info.get("price")
        return float(price) if price else None

    async def get_treasury_yield(self) -> Optional[float]:
        """Get 10-year treasury yield (TNX)."""
        info = await self._get_info("^TNX")
        price = info.get("price")
        return float(price) if price else None

    async def get_market_overview(self) -> Dict[str, Any]:
        """Fetch broad market data including VIX, SPY, QQQ, yields."""
        symbols = list(MACRO_TICKERS.values())
        tasks = [self._get_info(sym) for sym in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        data: Dict[str, Any] = {}
        for key, result in zip(MACRO_TICKERS.keys(), results):
            if isinstance(result, dict):
                price = result.get("price")
                prev = result.get("previous_close")

                if price and prev and prev != 0:
                    change_pct = (float(price) - float(prev)) / float(prev) * 100
                else:
                    change_pct = 0.0

                data[key] = float(price) if price else None
                data[f"{key}_change_pct"] = round(change_pct, 2)

        return data

    async def get_sector_performance(self) -> Dict[str, Any]:
        """Get performance of all sector ETFs."""
        tasks = [self._get_info(etf) for etf in SECTOR_ETFS.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        sector_data: Dict[str, Any] = {}
        for sector_name, result in zip(SECTOR_ETFS.keys(), results):
            if isinstance(result, dict):
                price = result.get("price")
                prev = result.get("previous_close")
                if price and prev and prev != 0:
                    change_pct = (float(price) - float(prev)) / float(prev) * 100
                else:
                    change_pct = 0.0

                sector_data[sector_name] = {
                    "etf": SECTOR_ETFS[sector_name],
                    "price": float(price) if price else None,
                    "change_pct": round(change_pct, 2),
                }

        return sector_data

    async def calculate_sector_rotation_signals(self) -> Dict[str, str]:
        """Identify which sectors are gaining / losing momentum."""
        sector_data = await self.get_sector_performance()

        signals: Dict[str, str] = {}
        for sector, data in sector_data.items():
            change = data.get("change_pct", 0)
            if change > 1.0:
                signals[sector] = "bullish"
            elif change < -1.0:
                signals[sector] = "bearish"
            else:
                signals[sector] = "neutral"

        return signals

    async def get_macro_score(self) -> float:
        """
        Compute a composite macro score (0-100).
        Higher = more favorable macro environment.
        """
        try:
            overview = await self.get_market_overview()

            vix = overview.get("vix") or 20.0
            spy_change = overview.get("spy_change_pct") or 0.0
            qqq_change = overview.get("qqq_change_pct") or 0.0
            tnx = overview.get("tnx") or 4.0

            # VIX component: lower VIX = better (invert)
            vix_score = max(0.0, min(100.0, (40.0 - vix) / 40.0 * 100))

            # Market trend component: positive change is bullish
            trend_score = max(0.0, min(100.0, 50.0 + spy_change * 10))

            # Yield component: moderate yields are OK
            if tnx < 3.0:
                yield_score = 60.0
            elif tnx < 4.5:
                yield_score = 70.0
            elif tnx < 5.5:
                yield_score = 50.0
            else:
                yield_score = 30.0

            # Composite
            macro_score = vix_score * 0.4 + trend_score * 0.4 + yield_score * 0.2
            return round(macro_score, 1)

        except Exception as exc:
            logger.warning("Macro score calculation failed: {}", exc)
            return 50.0  # neutral fallback
