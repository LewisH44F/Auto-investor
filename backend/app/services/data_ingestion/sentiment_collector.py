"""Sentiment data collection from multiple sources."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from app.core.config import settings


class SentimentCollector:
    """Collects sentiment from Reddit, social sources, and news aggregators."""

    async def collect_reddit_sentiment(
        self, ticker: str, subreddits: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Collect sentiment from Reddit (using public API endpoints)."""
        if subreddits is None:
            subreddits = ["wallstreetbets", "stocks", "investing", "StockMarket"]

        all_posts: List[Dict] = []

        async with httpx.AsyncClient(
            timeout=10.0,
            headers={"User-Agent": "AutoInvestor/1.0"},
        ) as client:
            for sub in subreddits[:2]:  # Limit to avoid rate limits
                try:
                    url = f"https://www.reddit.com/r/{sub}/search.json"
                    params = {
                        "q": ticker,
                        "sort": "new",
                        "limit": 25,
                        "t": "day",
                    }
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        posts = data.get("data", {}).get("children", [])
                        all_posts.extend(posts)
                except Exception as exc:
                    logger.debug("Reddit fetch failed for {} in r/{}: {}", ticker, sub, exc)

        if not all_posts:
            return {
                "source": "reddit",
                "ticker": ticker,
                "score": 0.0,
                "volume": 0,
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
            }

        # Simple keyword-based scoring
        bullish_keywords = [
            "buy", "bull", "long", "moon", "rocket", "calls", "growth",
            "breakout", "undervalued", "accumulate", "strong", "beat"
        ]
        bearish_keywords = [
            "sell", "bear", "short", "puts", "crash", "dump", "overvalued",
            "miss", "weak", "avoid", "falling", "decline"
        ]

        bullish = 0
        bearish = 0
        neutral = 0

        for post in all_posts:
            post_data = post.get("data", {})
            text = (
                f"{post_data.get('title', '')} {post_data.get('selftext', '')}".lower()
            )

            b_score = sum(1 for kw in bullish_keywords if kw in text)
            be_score = sum(1 for kw in bearish_keywords if kw in text)

            if b_score > be_score:
                bullish += 1
            elif be_score > b_score:
                bearish += 1
            else:
                neutral += 1

        total = bullish + bearish + neutral
        if total == 0:
            score = 0.0
        else:
            score = (bullish - bearish) / total

        return {
            "source": "reddit",
            "ticker": ticker,
            "score": round(score, 3),
            "volume": len(all_posts),
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": neutral,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def collect_stocktwits_sentiment(
        self, ticker: str
    ) -> Dict[str, Any]:
        """Collect sentiment from StockTwits public API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
                resp = await client.get(url)
                if resp.status_code != 200:
                    return {"source": "stocktwits", "ticker": ticker, "score": 0.0, "volume": 0}

                data = resp.json()
                messages = data.get("messages", [])

                if not messages:
                    return {"source": "stocktwits", "ticker": ticker, "score": 0.0, "volume": 0}

                bullish = sum(
                    1 for m in messages
                    if m.get("entities", {}).get("sentiment", {}).get("basic") == "Bullish"
                )
                bearish = sum(
                    1 for m in messages
                    if m.get("entities", {}).get("sentiment", {}).get("basic") == "Bearish"
                )
                total = len(messages)

                score = (bullish - bearish) / total if total > 0 else 0.0

                return {
                    "source": "stocktwits",
                    "ticker": ticker,
                    "score": round(score, 3),
                    "volume": total,
                    "bullish_count": bullish,
                    "bearish_count": bearish,
                    "neutral_count": total - bullish - bearish,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

        except Exception as exc:
            logger.debug("StockTwits fetch failed for {}: {}", ticker, exc)
            return {"source": "stocktwits", "ticker": ticker, "score": 0.0, "volume": 0}

    async def collect_all_sentiment(self, ticker: str) -> List[Dict[str, Any]]:
        """Collect sentiment from all available sources."""
        tasks = [
            self.collect_reddit_sentiment(ticker),
            self.collect_stocktwits_sentiment(ticker),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid = []
        for r in results:
            if isinstance(r, dict) and "score" in r:
                r.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
                valid.append(r)

        return valid
