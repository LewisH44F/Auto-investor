"""Market data service using yfinance as the primary free data source."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf
from loguru import logger
from sqlalchemy import text

from app.core.cache import cached, cache
from app.core.database import AsyncSessionLocal

# ── NASDAQ watchlist – extend as needed ──────────────────────────────────────
NASDAQ_TICKERS = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","AVGO","COST","NFLX",
    "AMD","ADBE","QCOM","INTU","CSCO","AMAT","PANW","ADI","MRVL","LRCX",
    "KLAC","SNPS","CDNS","MELI","REGN","GILD","ADP","BKNG","VRTX","PYPL",
    "ISRG","MU","ORLY","MNST","CRWD","DDOG","ZS","FTNT","TEAM","SNOW",
    "WDAY","IDXX","FAST","ROST","VRSK","PAYX","MCHP","MRNA","ON","PLTR",
    "COIN","ROKU","PINS","SNAP","SQ","SHOP","ZM","OKTA","MDB","NET",
    "HUBS","CRM","NOW","VEEV","AMGN","BIIB","UBER","ABNB","EXPE","NXPI",
    "ASML","SBUX","DLTR","ODFL","CTAS","CPRT","PCAR","RIVN","SOFI","AFRM",
]

SECTOR_ETFS = {
    "Technology": "XLK",
    "Financials": "XLF",
    "Energy": "XLE",
    "Healthcare": "XLV",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Industrials": "XLI",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Materials": "XLB",
    "Communication Services": "XLC",
}


class MarketDataService:
    """Fetches and caches market data from yfinance."""

    async def fetch_ohlcv(self, ticker: str, period: str = "3mo", interval: str = "1d") -> Optional[pd.DataFrame]:
        """Return OHLCV DataFrame for a ticker, or None on error."""
        loop = asyncio.get_event_loop()
        try:
            df = await loop.run_in_executor(None, self._fetch_sync, ticker, period, interval)
            return df
        except Exception as e:
            logger.warning("fetch_ohlcv failed for {}: {}", ticker, e)
            return None

    def _fetch_sync(self, ticker: str, period: str, interval: str) -> pd.DataFrame:
        tk = yf.Ticker(ticker)
        df = tk.history(period=period, interval=interval, auto_adjust=True)
        df.index = pd.to_datetime(df.index)
        df.rename(columns=str.capitalize, inplace=True)
        return df

    @cached(ttl=60, key_prefix="quote")
    async def get_quote(self, ticker: str) -> dict:
        """Current quote: price, change_pct, volume, market_cap."""
        loop = asyncio.get_event_loop()
        try:
            info = await loop.run_in_executor(None, self._get_info_sync, ticker)
            price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
            prev = info.get("regularMarketPreviousClose") or price
            change_pct = ((price - prev) / prev * 100) if prev else 0.0
            return {
                "ticker": ticker,
                "price": round(price, 2),
                "prev_close": round(prev, 2),
                "change_pct": round(change_pct, 2),
                "volume": info.get("regularMarketVolume", 0),
                "avg_volume": info.get("averageVolume", 0),
                "market_cap": info.get("marketCap", 0),
                "sector": info.get("sector", ""),
                "name": info.get("shortName", ticker),
                "week_52_high": info.get("fiftyTwoWeekHigh", 0),
                "week_52_low": info.get("fiftyTwoWeekLow", 0),
                "pe_ratio": info.get("trailingPE"),
                "next_earnings": str(info.get("earningsDate", "")),
            }
        except Exception as e:
            logger.warning("get_quote failed for {}: {}", ticker, e)
            return {"ticker": ticker, "price": 0.0, "change_pct": 0.0, "volume": 0}

    def _get_info_sync(self, ticker: str) -> dict:
        return yf.Ticker(ticker).info

    @cached(ttl=300, key_prefix="macro")
    async def get_macro_snapshot(self) -> dict:
        """VIX, QQQ, SPY, sector ETF performance."""
        loop = asyncio.get_event_loop()
        indices = ["^VIX", "SPY", "QQQ", "^IXIC"]
        results = {}
        for sym in indices:
            try:
                info = await loop.run_in_executor(None, self._get_info_sync, sym)
                price = info.get("regularMarketPrice", 0)
                prev = info.get("regularMarketPreviousClose", price)
                results[sym] = {
                    "price": round(price, 2),
                    "change_pct": round(((price - prev) / prev * 100) if prev else 0, 2),
                }
            except Exception:
                results[sym] = {"price": 0, "change_pct": 0}

        # Sector ETFs
        sector_data = {}
        for sector, etf in SECTOR_ETFS.items():
            try:
                info = await loop.run_in_executor(None, self._get_info_sync, etf)
                price = info.get("regularMarketPrice", 0)
                prev = info.get("regularMarketPreviousClose", price)
                sector_data[sector] = round(((price - prev) / prev * 100) if prev else 0, 2)
            except Exception:
                sector_data[sector] = 0.0

        vix = results.get("^VIX", {}).get("price", 20)
        if vix < 15:
            condition = "LOW VOLATILITY"
        elif vix < 20:
            condition = "NORMAL"
        elif vix < 30:
            condition = "ELEVATED"
        else:
            condition = "HIGH FEAR"

        nasdaq_chg = results.get("^IXIC", {}).get("change_pct", 0)
        return {
            "vix": vix,
            "market_condition": condition,
            "nasdaq_change_pct": nasdaq_chg,
            "spy_change_pct": results.get("SPY", {}).get("change_pct", 0),
            "qqq_change_pct": results.get("QQQ", {}).get("change_pct", 0),
            "sector_performance": sector_data,
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def get_relative_volume(self, ticker: str) -> float:
        """Current volume vs 20-day average volume."""
        df = await self.fetch_ohlcv(ticker, period="1mo")
        if df is None or len(df) < 2:
            return 1.0
        avg_vol = df["Volume"].iloc[:-1].mean()
        curr_vol = df["Volume"].iloc[-1]
        return round(curr_vol / avg_vol, 2) if avg_vol > 0 else 1.0

    async def update_nasdaq_universe(self) -> None:
        """Refresh price data for top tickers and store in DB."""
        logger.info("Updating NASDAQ universe price data...")
        for ticker in NASDAQ_TICKERS[:50]:  # cap at 50 for speed
            try:
                df = await self.fetch_ohlcv(ticker, period="5d")
                if df is None or df.empty:
                    continue
                latest = df.iloc[-1]
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        text("""
                            INSERT INTO stock_prices (ticker, open, high, low, close, volume, timestamp, interval)
                            VALUES (:ticker, :open, :high, :low, :close, :volume, :ts, '1d')
                            ON CONFLICT DO NOTHING
                        """),
                        {
                            "ticker": ticker,
                            "open": float(latest.get("Open", 0)),
                            "high": float(latest.get("High", 0)),
                            "low": float(latest.get("Low", 0)),
                            "close": float(latest.get("Close", 0)),
                            "volume": int(latest.get("Volume", 0)),
                            "ts": datetime.utcnow(),
                        }
                    )
                    await session.commit()
            except Exception as e:
                logger.debug("update_nasdaq skip {}: {}", ticker, e)
        logger.info("NASDAQ universe update complete.")
