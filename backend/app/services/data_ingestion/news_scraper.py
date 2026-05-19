"""Async news scraping and aggregation service."""

from __future__ import annotations

import asyncio
import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import feedparser
import httpx
from bs4 import BeautifulSoup
from loguru import logger

from app.core.config import settings

RSS_FEEDS: List[Dict[str, str]] = [
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/rss/topstories"},
    {"name": "Reuters Business", "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"name": "CNBC", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
    {"name": "MarketWatch", "url": "https://feeds.content.dowjones.io/public/rss/mw_topstories"},
    {"name": "Seeking Alpha", "url": "https://seekingalpha.com/market_currents.xml"},
    {"name": "Benzinga", "url": "https://www.benzinga.com/feed"},
    {"name": "Investopedia", "url": "https://www.investopedia.com/feedbuilder/feed/getfeed/?feedName=investopedia_401k"},
]

CATALYST_KEYWORDS: Dict[str, List[str]] = {
    "earnings": ["earnings", "beat", "miss", "eps", "revenue", "quarterly", "profit", "q1", "q2", "q3", "q4"],
    "merger": ["merger", "acquisition", "acquire", "buyout", "takeover", "deal", "m&a"],
    "fda": ["fda", "approval", "clinical trial", "phase 3", "drug", "therapy", "biotech", "nda", "bla"],
    "partnership": ["partnership", "agreement", "collaboration", "joint venture", "alliance", "contract"],
    "analyst": ["upgrade", "downgrade", "price target", "rating", "outperform", "buy rating", "sell rating"],
    "leadership": ["ceo", "cfo", "president", "director", "resign", "appointed", "executive"],
    "contract": ["government contract", "defense contract", "award", "billion contract"],
    "macro": ["federal reserve", "fed", "inflation", "interest rate", "gdp", "recession", "jobs report"],
    "legal": ["lawsuit", "settlement", "sec", "investigation", "fine", "penalty", "regulatory"],
    "insider": ["insider buying", "insider selling", "sec filing", "13f", "form 4"],
}


def _compute_url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:64]


def _extract_tickers_from_text(text: str) -> List[str]:
    """Heuristically extract uppercase ticker symbols from text."""
    pattern = r"\b([A-Z]{1,5})\b"
    candidates = re.findall(pattern, text)
    # Filter out common English words that look like tickers
    exclusions = {
        "A", "I", "IT", "IN", "AT", "AS", "BE", "BY", "DO", "GO", "IF",
        "IS", "NO", "OF", "ON", "OR", "SO", "TO", "UP", "US", "CEO", "CFO",
        "COO", "CTO", "IPO", "ETF", "FDA", "SEC", "GDP", "AI", "EPS",
        "Q1", "Q2", "Q3", "Q4", "YOY", "QOQ", "YTD", "TTM", "NYSE", "NASDAQ",
        "OTC", "USA", "UK", "EU", "AM", "PM", "EST", "PST",
    }
    return list(set(t for t in candidates if t not in exclusions and len(t) >= 2))


def _classify_catalyst(text: str) -> tuple[Optional[str], float]:
    """Return (catalyst_type, strength) from headline/summary text."""
    text_lower = text.lower()
    scores: Dict[str, int] = {}

    for catalyst, keywords in CATALYST_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > 0:
            scores[catalyst] = count

    if not scores:
        return None, 0.0

    best = max(scores, key=lambda k: scores[k])
    strength = min(scores[best] * 2.0, 10.0)
    return best, strength


def _estimate_catalyst_duration(catalyst_type: Optional[str]) -> str:
    duration_map = {
        "earnings": "3d",
        "merger": "1w",
        "fda": "1w",
        "partnership": "1d",
        "analyst": "1d",
        "leadership": "3d",
        "contract": "1d",
        "macro": "1w",
        "legal": "3d",
        "insider": "3d",
    }
    return duration_map.get(catalyst_type or "", "1d")


class NewsScraper:
    """Aggregates news from multiple sources and enriches with metadata."""

    def __init__(self) -> None:
        self._seen_hashes: set[str] = set()

    async def fetch_from_newsapi(
        self, query: str = "stock market", page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """Fetch articles from NewsAPI."""
        if not settings.NEWS_API_KEY:
            logger.debug("NewsAPI key not configured, skipping")
            return []

        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": settings.NEWS_API_KEY,
            "pageSize": page_size,
            "sortBy": "publishedAt",
            "language": "en",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            articles = []
            for art in data.get("articles", []):
                url_hash = _compute_url_hash(art.get("url", ""))
                if url_hash in self._seen_hashes:
                    continue
                self._seen_hashes.add(url_hash)

                headline = art.get("title", "")
                summary = art.get("description", "")
                combined = f"{headline} {summary}"

                catalyst_type, catalyst_strength = _classify_catalyst(combined)
                tickers = _extract_tickers_from_text(combined)

                articles.append(
                    {
                        "headline": headline,
                        "summary": summary,
                        "source": art.get("source", {}).get("name"),
                        "url": art.get("url"),
                        "url_hash": url_hash,
                        "published_at": art.get("publishedAt"),
                        "tickers_mentioned": ",".join(tickers),
                        "catalyst_type": catalyst_type,
                        "catalyst_strength": catalyst_strength,
                        "catalyst_duration": _estimate_catalyst_duration(catalyst_type),
                    }
                )
            return articles

        except Exception as exc:
            logger.error("NewsAPI fetch failed: {}", exc)
            return []

    async def fetch_rss_feeds(self) -> List[Dict[str, Any]]:
        """Parse RSS feeds from major financial news sources."""
        all_articles: List[Dict[str, Any]] = []
        tasks = [self._fetch_single_rss(feed) for feed in RSS_FEEDS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)

        return all_articles

    async def _fetch_single_rss(self, feed: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse a single RSS feed."""
        try:
            loop = asyncio.get_event_loop()
            parsed = await loop.run_in_executor(
                None,
                lambda: feedparser.parse(feed["url"]),
            )

            articles = []
            for entry in parsed.entries[:20]:
                headline = entry.get("title", "")
                summary = entry.get("summary", "")
                url = entry.get("link", "")

                if not headline or not url:
                    continue

                url_hash = _compute_url_hash(url)
                if url_hash in self._seen_hashes:
                    continue
                self._seen_hashes.add(url_hash)

                combined = f"{headline} {summary}"
                catalyst_type, catalyst_strength = _classify_catalyst(combined)
                tickers = _extract_tickers_from_text(combined)

                published_at = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        import time
                        ts = time.mktime(entry.published_parsed)
                        published_at = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
                    except Exception:
                        pass

                articles.append(
                    {
                        "headline": headline[:500],
                        "summary": BeautifulSoup(summary, "lxml").get_text()[:1000] if summary else None,
                        "source": feed["name"],
                        "url": url,
                        "url_hash": url_hash,
                        "published_at": published_at,
                        "tickers_mentioned": ",".join(tickers),
                        "catalyst_type": catalyst_type,
                        "catalyst_strength": catalyst_strength,
                        "catalyst_duration": _estimate_catalyst_duration(catalyst_type),
                    }
                )
            return articles

        except Exception as exc:
            logger.warning("RSS feed {} failed: {}", feed["name"], exc)
            return []

    async def aggregate_all(self, max_articles: int = 100) -> List[Dict[str, Any]]:
        """Fetch from all sources and deduplicate."""
        rss_articles = await self.fetch_rss_feeds()
        newsapi_articles = await self.fetch_from_newsapi()

        all_articles = rss_articles + newsapi_articles

        # Deduplicate by url_hash
        seen: set[str] = set()
        unique = []
        for art in all_articles:
            h = art.get("url_hash", "")
            if h and h not in seen:
                seen.add(h)
                unique.append(art)

        logger.info(
            "News aggregation: {} articles from {} sources",
            len(unique),
            len(RSS_FEEDS),
        )
        return unique[:max_articles]

    async def get_ticker_news(
        self, ticker: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get news specific to a ticker using yfinance."""
        try:
            import asyncio
            import yfinance as yf

            loop = asyncio.get_event_loop()
            t = yf.Ticker(ticker)
            news_raw = await loop.run_in_executor(None, lambda: t.news)

            articles = []
            for item in (news_raw or [])[:limit]:
                headline = item.get("title", "")
                url = item.get("link", "")
                url_hash = _compute_url_hash(url)

                catalyst_type, catalyst_strength = _classify_catalyst(headline)

                ts = item.get("providerPublishTime")
                published_at = (
                    datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else None
                )

                articles.append(
                    {
                        "ticker": ticker,
                        "headline": headline,
                        "summary": item.get("summary"),
                        "source": item.get("publisher"),
                        "url": url,
                        "url_hash": url_hash,
                        "published_at": published_at,
                        "catalyst_type": catalyst_type,
                        "catalyst_strength": catalyst_strength,
                        "catalyst_duration": _estimate_catalyst_duration(catalyst_type),
                    }
                )
            return articles
        except Exception as exc:
            logger.error("Ticker news fetch failed for {}: {}", ticker, exc)
            return []
