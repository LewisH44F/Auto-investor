"""Sentiment analysis service using FinBERT or TextBlob fallback."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from loguru import logger

# Try to load FinBERT, fall back to TextBlob
FINBERT_AVAILABLE = False
_finbert_pipeline = None


def _try_load_finbert():
    global FINBERT_AVAILABLE, _finbert_pipeline
    if _finbert_pipeline is not None:
        return

    try:
        from transformers import pipeline
        _finbert_pipeline = pipeline(
            "text-classification",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            device=-1,  # CPU
            truncation=True,
            max_length=512,
        )
        FINBERT_AVAILABLE = True
        logger.info("FinBERT loaded successfully")
    except Exception as exc:
        logger.warning("FinBERT unavailable ({}), using TextBlob fallback", exc)
        FINBERT_AVAILABLE = False


def _textblob_score(text: str) -> float:
    """Fallback: TextBlob polarity (-1 to 1)."""
    try:
        from textblob import TextBlob
        return TextBlob(text).sentiment.polarity
    except Exception:
        return 0.0


def _finbert_score(text: str) -> float:
    """Score text using FinBERT. Returns -1 to 1."""
    global _finbert_pipeline
    if _finbert_pipeline is None:
        return _textblob_score(text)

    try:
        result = _finbert_pipeline(text[:512])[0]
        label = result["label"].lower()
        score = result["score"]

        if label == "positive":
            return score
        elif label == "negative":
            return -score
        return 0.0
    except Exception as exc:
        logger.debug("FinBERT scoring failed: {}", exc)
        return _textblob_score(text)


SOURCE_CREDIBILITY: Dict[str, float] = {
    "reuters": 1.0,
    "bloomberg": 1.0,
    "wsj": 1.0,
    "cnbc": 0.9,
    "marketwatch": 0.85,
    "yahoo finance": 0.8,
    "seekingalpha": 0.7,
    "benzinga": 0.7,
    "reddit": 0.5,
    "stocktwits": 0.5,
    "twitter": 0.45,
    "default": 0.6,
}


def _get_credibility(source: Optional[str]) -> float:
    if not source:
        return SOURCE_CREDIBILITY["default"]
    src_lower = source.lower()
    for key, weight in SOURCE_CREDIBILITY.items():
        if key in src_lower:
            return weight
    return SOURCE_CREDIBILITY["default"]


class SentimentAnalyzer:
    """Aggregate sentiment from multiple sources with credibility weighting."""

    def __init__(self) -> None:
        _try_load_finbert()

    def score_text(self, text: str) -> float:
        """Score a single text string (-1 to 1)."""
        if FINBERT_AVAILABLE:
            return _finbert_score(text)
        return _textblob_score(text)

    def score_articles(
        self,
        articles: List[Dict[str, Any]],
        decay_factor: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Aggregate sentiment across articles.
        Applies recency decay and source credibility weighting.
        """
        if not articles:
            return {
                "overall_score": 0.0,
                "overall_label": "neutral",
                "momentum": "stable",
                "article_count": 0,
                "source_breakdown": {},
            }

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        weighted_scores: List[float] = []
        source_scores: Dict[str, List[float]] = {}

        for i, article in enumerate(articles):
            headline = article.get("headline", "")
            summary = article.get("summary", "")
            text = f"{headline}. {summary}"
            source = article.get("source")

            # Base sentiment score
            raw_score = self.score_text(text)

            # Use precomputed score if available
            if article.get("sentiment_score") is not None:
                raw_score = float(article["sentiment_score"])

            # Credibility weighting
            credibility = _get_credibility(source)

            # Recency decay (most recent = 1.0, oldest = decay^n)
            recency_weight = decay_factor ** i

            weighted = raw_score * credibility * recency_weight
            weighted_scores.append(weighted)

            src_key = source or "unknown"
            source_scores.setdefault(src_key, []).append(raw_score)

        total_weight = sum(
            SOURCE_CREDIBILITY.get(
                articles[i].get("source", "default") or "default",
                SOURCE_CREDIBILITY["default"]
            ) * (decay_factor ** i)
            for i in range(len(articles))
        )

        overall = sum(weighted_scores) / total_weight if total_weight > 0 else 0.0
        overall = max(-1.0, min(1.0, overall))

        source_breakdown = {
            src: round(sum(scores) / len(scores), 3)
            for src, scores in source_scores.items()
        }

        # Label
        if overall > 0.15:
            label = "positive"
        elif overall < -0.15:
            label = "negative"
        else:
            label = "neutral"

        # Momentum: compare first half vs second half
        mid = len(articles) // 2
        if mid > 0:
            recent_avg = sum(s for s in weighted_scores[:mid]) / mid
            older_avg = sum(s for s in weighted_scores[mid:]) / (len(weighted_scores) - mid)
            if recent_avg > older_avg + 0.1:
                momentum = "improving"
            elif recent_avg < older_avg - 0.1:
                momentum = "deteriorating"
            else:
                momentum = "stable"
        else:
            momentum = "stable"

        return {
            "overall_score": round(overall, 3),
            "overall_label": label,
            "momentum": momentum,
            "article_count": len(articles),
            "source_breakdown": source_breakdown,
        }

    async def analyze_ticker(self, ticker: str) -> Dict[str, Any]:
        """Full async sentiment analysis for a ticker."""
        from app.services.data_ingestion.news_scraper import NewsScraper
        from app.services.data_ingestion.sentiment_collector import SentimentCollector

        scraper = NewsScraper()
        collector = SentimentCollector()

        # Fetch news and social data concurrently
        news_task = scraper.get_ticker_news(ticker, limit=15)
        social_task = collector.collect_all_sentiment(ticker)

        news_articles, social_data = await asyncio.gather(news_task, social_task)

        # Score news articles
        news_result = self.score_articles(news_articles)

        # Aggregate social scores
        social_score = 0.0
        if social_data:
            social_score = sum(s.get("score", 0) for s in social_data) / len(social_data)

        # Combined score (news 60%, social 40%)
        combined_score = news_result["overall_score"] * 0.6 + social_score * 0.4

        if combined_score > 0.15:
            label = "positive"
        elif combined_score < -0.15:
            label = "negative"
        else:
            label = "neutral"

        # Normalized score for model features (0-100)
        normalized = (combined_score + 1) / 2 * 100

        return {
            "score": round(combined_score, 3),
            "normalized_score": round(normalized, 1),
            "label": label,
            "momentum": news_result["momentum"],
            "news_score": news_result["overall_score"],
            "social_score": round(social_score, 3),
            "article_count": news_result["article_count"],
            "source_breakdown": news_result["source_breakdown"],
        }
