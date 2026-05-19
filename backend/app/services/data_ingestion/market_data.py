"""Market data ingestion service using yfinance as primary source."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
import yfinance as yf
from loguru import logger

# Top 200 NASDAQ tickers for scanning (curated, liquid universe)
NASDAQ_UNIVERSE: List[str] = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "AVGO", "COST",
    "NFLX", "AMD", "ADBE", "QCOM", "INTU", "INTC", "CSCO", "AMAT", "PANW", "SBUX",
    "ADI", "MRVL", "LRCX", "KLAC", "SNPS", "CDNS", "MELI", "REGN", "GILD", "ADP",
    "ASML", "MDLZ", "BKNG", "VRTX", "PYPL", "ISRG", "CSX", "ATVI", "MU", "ORLY",
    "MNST", "CHTR", "CTAS", "CRWD", "ABNB", "DDOG", "ZS", "FTNT", "TEAM", "SNOW",
    "ENPH", "PCAR", "BIIB", "SGEN", "ILMN", "IDXX", "NXPI", "FAST", "ROST", "VRSK",
    "WDAY", "ODFL", "KDP", "CPRT", "PAYX", "ANSS", "MCHP", "DXCM", "MRNA", "ALGN",
    "EXC", "DLTR", "SIRI", "WBA", "MAR", "TTWO", "CEG", "AEP", "XEL", "FANG",
    "ON", "RIVN", "LCID", "SOFI", "UPST", "AFRM", "HOOD", "RBLX", "U", "PLTR",
    "COIN", "MSTR", "ROKU", "PINS", "SNAP", "TWLO", "SQ", "SHOP", "SE", "GRAB",
    "ZM", "DOCU", "OKTA", "SPLK", "MDB", "NET", "CFLT", "GTLB", "BILL", "HUBS",
    "CRM", "NOW", "VEEV", "FIVN", "PCTY", "PAYC", "SMAR", "ASAN", "ESTC", "SUMO",
    "AMGN", "CELG", "BMRN", "ALXN", "EXAS", "ACAD", "SAGE", "SRPT", "BLUE", "FATE",
    "NUAN", "OKTA", "ZI", "BRZE", "SEMR", "IONQ", "ARRY", "MTTR", "DLO", "CLOV",
    "LMND", "ROOT", "OPEN", "OPENDOOR", "DKNG", "PENN", "MGM", "LVS", "WYNN", "CZR",
    "UBER", "LYFT", "DASH", "ABNB", "EXPE", "BKNG", "TRIP", "NCLH", "CCL", "RCL",
    "AAL", "DAL", "UAL", "LUV", "JBLU", "SAVE", "HA", "ALK", "SKYW", "MESA",
    "NVAX", "BNTX", "PFE", "JNJ", "ABBV", "LLY", "BMY", "MRK", "AZN", "GSK",
]

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


class MarketDataService:
    """Async market data service backed by yfinance."""

    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}

    async def fetch_ohlcv(
        self,
        ticker: str,
        period: str = "3mo",
        interval: str = "1d",
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data for a ticker using yfinance."""
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: yf.download(
                    ticker,
                    period=period,
                    interval=interval,
                    progress=False,
                    auto_adjust=True,
                ),
            )
            if df is None or df.empty:
                logger.warning("No data returned for {}", ticker)
                return None

            # Flatten multi-level columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df.dropna(subset=["Close"])
            logger.debug("Fetched {} rows for {} ({})", len(df), ticker, period)
            return df

        except Exception as exc:
            logger.error("Failed to fetch OHLCV for {}: {}", ticker, exc)
            return None

    async def fetch_ticker_info(self, ticker: str) -> Dict[str, Any]:
        """Fetch fundamental info for a ticker."""
        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None,
                lambda: yf.Ticker(ticker).info,
            )
            return info or {}
        except Exception as exc:
            logger.error("Failed to fetch info for {}: {}", ticker, exc)
            return {}

    async def fetch_current_price(self, ticker: str) -> Optional[float]:
        """Get current price for a single ticker."""
        try:
            info = await self.fetch_ticker_info(ticker)
            price = (
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or info.get("previousClose")
            )
            return float(price) if price else None
        except Exception:
            return None

    async def fetch_batch_quotes(
        self, tickers: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch current quotes for multiple tickers."""
        results: Dict[str, Dict[str, Any]] = {}
        chunk_size = 10

        for i in range(0, len(tickers), chunk_size):
            chunk = tickers[i : i + chunk_size]
            tasks = [self._fetch_single_quote(t) for t in chunk]
            quotes = await asyncio.gather(*tasks, return_exceptions=True)

            for ticker, quote in zip(chunk, quotes):
                if isinstance(quote, dict):
                    results[ticker] = quote
                else:
                    results[ticker] = {}

        return results

    async def _fetch_single_quote(self, ticker: str) -> Dict[str, Any]:
        """Fetch single ticker quote data."""
        info = await self.fetch_ticker_info(ticker)

        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose", 0)
        )
        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose", price)

        change = float(price or 0) - float(prev_close or 0)
        change_pct = (change / float(prev_close)) * 100 if prev_close else 0.0

        return {
            "ticker": ticker,
            "price": float(price or 0),
            "previous_close": float(prev_close or 0),
            "change": round(change, 4),
            "change_pct": round(change_pct, 2),
            "volume": info.get("volume") or info.get("regularMarketVolume", 0),
            "avg_volume": info.get("averageVolume", 0),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "week_52_high": info.get("fiftyTwoWeekHigh"),
            "week_52_low": info.get("fiftyTwoWeekLow"),
            "pre_market_price": info.get("preMarketPrice"),
            "after_hours_price": info.get("postMarketPrice"),
        }

    async def calculate_relative_volume(
        self, ticker: str, current_volume: int, lookback_days: int = 20
    ) -> float:
        """Calculate relative volume vs N-day average."""
        try:
            df = await self.fetch_ohlcv(ticker, period="3mo", interval="1d")
            if df is None or len(df) < lookback_days:
                return 1.0

            avg_vol = df["Volume"].tail(lookback_days).mean()
            if avg_vol <= 0:
                return 1.0

            return round(current_volume / avg_vol, 2)
        except Exception:
            return 1.0

    async def detect_unusual_volume(
        self, ticker: str, threshold: float = 2.0
    ) -> bool:
        """Return True if today's volume is >threshold × 20-day average."""
        try:
            df = await self.fetch_ohlcv(ticker, period="3mo", interval="1d")
            if df is None or len(df) < 21:
                return False

            today_vol = df["Volume"].iloc[-1]
            avg_vol = df["Volume"].iloc[-21:-1].mean()

            if avg_vol <= 0:
                return False

            rel_vol = today_vol / avg_vol
            return rel_vol >= threshold
        except Exception:
            return False

    async def get_earnings_calendar(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch next/last earnings date and surprise."""
        try:
            loop = asyncio.get_event_loop()
            t = yf.Ticker(ticker)
            info = await loop.run_in_executor(None, lambda: t.info)

            return {
                "next_earnings_date": info.get("earningsTimestamp"),
                "earnings_quarterly_growth": info.get("earningsQuarterlyGrowth"),
                "trailing_eps": info.get("trailingEps"),
                "forward_eps": info.get("forwardEps"),
            }
        except Exception as exc:
            logger.warning("Earnings calendar fetch failed for {}: {}", ticker, exc)
            return None

    async def get_watchlist_tickers(self, limit: int = 100) -> List[str]:
        """Return the default scanning universe."""
        return NASDAQ_UNIVERSE[:limit]

    async def batch_fetch_nasdaq_universe(
        self,
        min_price: float = 5.0,
        min_volume: int = 500_000,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """Scan NASDAQ universe and return stocks passing liquidity filters."""
        tickers = NASDAQ_UNIVERSE[:limit]
        logger.info("Batch fetching {} tickers from NASDAQ universe", len(tickers))

        quotes = await self.fetch_batch_quotes(tickers)

        filtered = []
        for ticker, q in quotes.items():
            price = q.get("price", 0)
            volume = q.get("volume", 0)
            if price >= min_price and (volume or 0) >= min_volume:
                filtered.append({**q, "ticker": ticker})

        logger.info(
            "NASDAQ scan: {} / {} tickers passed liquidity filters",
            len(filtered),
            len(tickers),
        )
        return filtered
