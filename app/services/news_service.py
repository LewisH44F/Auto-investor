"""News aggregation service using RSS feeds and NewsAPI."""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta
from typing import Optional

import feedparser
import httpx
from loguru import logger
from sqlalchemy import text

from app.core.cache import cached, cache
from app.core.config import settings
from app.core.database import AsyncSessionLocal

RSS_FEEDS = [
    ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
    ("Reuters Business", "https://feeds.reuters.com/reuters/businessNews"),
    ("CNBC", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
    ("MarketWatch", "https://feeds.marketwatch.com/marketwatch/topstories"),
    ("Seeking Alpha", "https://seekingalpha.com/feed.xml"),
    ("Investopedia", "https://www.investopedia.com/feedbuilder/feed/getfeed/?feedName=rss_headline"),
]

CATALYST_KEYWORDS = {
    "earnings_beat": ["beat expectations", "earnings beat", "exceeded estimates", "topped estimates"],
    "earnings_miss": ["missed expectations", "earnings miss", "below estimates", "fell short"],
    "fda_approval": ["fda approved", "fda approval", "clearance granted", "regulatory approval"],
    "merger_acquisition": ["merger", "acquisition", "takeover", "buyout", "acquired"],
    "analyst_upgrade": ["upgrade", "outperform", "buy rating", "raised price target"],
    "analyst_downgrade": ["downgrade", "underperform", "sell rating", "cut price target"],
    "partnership": ["partnership", "agreement", "collaboration", "joint venture"],
    "layoffs": ["layoffs", "job cuts", "workforce reduction", "restructuring"],
    "ceo_change": ["ceo", "chief executive", "leadership change", "appointed"],
    "guidance_raise": ["raised guidance", "raised outlook", "increased forecast"],
    "guidance_cut": ["lowered guidance", "cut guidance", "reduced outlook"],
}


class NewsService:
    """Aggregates news from RSS feeds and NewsAPI, scores sentiment."""

    async def fetch_all_news(self, max_articles: int = 50) -> list[dict]:
        """Fetch from all RSS feeds concurrently, deduplicate, return list."""
        cached_news = cache.get("all_news")
        if cached_news:
            return cached_news

        tasks = [self._fetch_rss(name, url) for name, url in RSS_FEEDS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        articles = []
        seen_urls = set()
        for result in results:
            if isinstance(result, list):
                for article in result:
                    url = article.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        articles.append(article)

        # Sort by published date
        articles.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        articles = articles[:max_articles]

        # Try NewsAPI if key available
        if settings.NEWS_API_KEY:
            newsapi_articles = await self._fetch_newsapi()
            for article in newsapi_articles:
                url = article.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    articles.insert(0, article)

        cache.set("all_news", articles, ttl=300)
        return articles

    async def fetch_ticker_news(self, ticker: str) -> list[dict]:
        """Get news articles mentioning a specific ticker."""
        all_news = await self.fetch_all_news()
        ticker_news = [
            a for a in all_news
            if ticker.upper() in (a.get("headline", "") + a.get("summary", "")).upper()
            or ticker.upper() in a.get("tickers", [])
        ]
        return ticker_news[:10]

    async def _fetch_rss(self, source: str, url: str) -> list[dict]:
        try:
            loop = asyncio.get_event_loop()
            feed = await loop.run_in_executor(None, feedparser.parse, url)
            articles = []
            for entry in feed.entries[:15]:
                text_content = f"{entry.get('title', '')} {entry.get('summary', '')}"
                sentiment = self._simple_sentiment(text_content)
                catalyst = self._detect_catalyst(text_content)
                articles.append({
                    "headline": entry.get("title", ""),
                    "summary": entry.get("summary", "")[:300],
                    "url": entry.get("link", ""),
                    "source": source,
                    "published_at": entry.get("published", datetime.utcnow().isoformat()),
                    "sentiment_score": sentiment,
                    "impact_score": abs(sentiment) * 5 + (2 if catalyst else 0),
                    "catalyst_type": catalyst or "general",
                    "tickers": self._extract_tickers(text_content),
                })
            return articles
        except Exception as e:
            logger.debug("RSS fetch failed for {}: {}", source, e)
            return []

    async def _fetch_newsapi(self) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://newsapi.org/v2/top-headlines",
                    params={"category": "business", "language": "en", "pageSize": 20, "apiKey": settings.NEWS_API_KEY},
                )
                data = resp.json()
                articles = []
                for item in data.get("articles", []):
                    text_content = f"{item.get('title', '')} {item.get('description', '')}"
                    sentiment = self._simple_sentiment(text_content)
                    articles.append({
                        "headline": item.get("title", ""),
                        "summary": item.get("description", "")[:300],
                        "url": item.get("url", ""),
                        "source": item.get("source", {}).get("name", "NewsAPI"),
                        "published_at": item.get("publishedAt", datetime.utcnow().isoformat()),
                        "sentiment_score": sentiment,
                        "impact_score": abs(sentiment) * 5,
                        "catalyst_type": self._detect_catalyst(text_content) or "general",
                        "tickers": self._extract_tickers(text_content),
                    })
                return articles
        except Exception as e:
            logger.debug("NewsAPI fetch failed: {}", e)
            return []

    def _simple_sentiment(self, text: str) -> float:
        """Fast rule-based sentiment (-1 to 1) without heavy ML dependencies."""
        text_lower = text.lower()
        positive = [
            "beat", "surge", "soar", "rally", "gain", "rise", "growth", "profit",
            "record", "strong", "upgrade", "buy", "outperform", "bullish", "breakthrough",
            "approved", "partnership", "deal", "win", "positive", "success",
        ]
        negative = [
            "miss", "fall", "drop", "decline", "loss", "cut", "downgrade", "sell",
            "underperform", "bearish", "risk", "concern", "warning", "fraud",
            "lawsuit", "layoff", "recession", "below", "disappointing",
        ]
        pos = sum(1 for w in positive if w in text_lower)
        neg = sum(1 for w in negative if w in text_lower)
        total = pos + neg
        if total == 0:
            return 0.0
        return round((pos - neg) / total, 2)

    def _detect_catalyst(self, text: str) -> Optional[str]:
        text_lower = text.lower()
        for catalyst_type, keywords in CATALYST_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return catalyst_type
        return None

    def _extract_tickers(self, text: str) -> list[str]:
        """Extract uppercase ticker-like words (2-5 chars) from text."""
        from app.services.market_data import NASDAQ_TICKERS
        found = []
        words = re.findall(r'\b[A-Z]{1,5}\b', text)
        for word in words:
            if word in NASDAQ_TICKERS and word not in found:
                found.append(word)
        return found[:5]
