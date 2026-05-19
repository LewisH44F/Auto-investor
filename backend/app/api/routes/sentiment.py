"""Sentiment and news API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.core.redis_client import cache_get, cache_set
from app.models.news import NewsArticle
from app.models.sentiment import AnalystRating, SentimentRecord
from app.schemas.sentiment import (
    AnalystRatingRead,
    MarketSentimentResponse,
    NewsArticleRead,
    SentimentRecordRead,
    TickerSentimentResponse,
)

router = APIRouter(tags=["sentiment"])


@router.get("/sentiment/{ticker}", response_model=TickerSentimentResponse)
async def get_ticker_sentiment(
    ticker: str,
    db: AsyncSession = Depends(get_session),
) -> TickerSentimentResponse:
    """Comprehensive sentiment analysis for a ticker."""
    ticker = ticker.upper()
    cache_key = f"sentiment:ticker:{ticker}"
    cached = await cache_get(cache_key)
    if cached:
        return TickerSentimentResponse(**cached)

    # Fetch recent sentiment records
    result = await db.execute(
        select(SentimentRecord)
        .where(SentimentRecord.ticker == ticker)
        .order_by(desc(SentimentRecord.timestamp))
        .limit(20)
    )
    records = result.scalars().all()

    # Fetch analyst ratings
    analyst_result = await db.execute(
        select(AnalystRating)
        .where(AnalystRating.ticker == ticker)
        .order_by(desc(AnalystRating.timestamp))
        .limit(10)
    )
    analyst_ratings = analyst_result.scalars().all()

    # Aggregate scores
    if records:
        overall_score = sum(r.score for r in records) / len(records)
    else:
        overall_score = 0.0

    if overall_score > 0.1:
        overall_label = "positive"
    elif overall_score < -0.1:
        overall_label = "negative"
    else:
        overall_label = "neutral"

    news_records = [r for r in records if r.source == "news"]
    news_score = (
        sum(r.score for r in news_records) / len(news_records)
        if news_records else None
    )

    avg_price_target = None
    if analyst_ratings:
        targets = [r.price_target for r in analyst_ratings if r.price_target]
        avg_price_target = sum(targets) / len(targets) if targets else None

    response = TickerSentimentResponse(
        ticker=ticker,
        overall_score=round(overall_score, 3),
        overall_label=overall_label,
        sentiment_momentum="stable",
        confidence=min(len(records) / 10.0 * 100, 100.0),
        news_score=round(news_score, 3) if news_score is not None else None,
        analyst_consensus=analyst_ratings[0].rating if analyst_ratings else None,
        analyst_ratings=[AnalystRatingRead.model_validate(r) for r in analyst_ratings],
        avg_price_target=avg_price_target,
        num_analysts=len(analyst_ratings),
        recent_records=[SentimentRecordRead.model_validate(r) for r in records[:5]],
        generated_at=datetime.now(timezone.utc),
    )

    await cache_set(cache_key, response.model_dump(mode="json"), ttl=300)
    return response


@router.get("/sentiment/market-overview", response_model=MarketSentimentResponse)
async def get_market_sentiment(
    db: AsyncSession = Depends(get_session),
) -> MarketSentimentResponse:
    """Broad market sentiment overview."""
    cache_key = "sentiment:market_overview"
    cached = await cache_get(cache_key)
    if cached:
        return MarketSentimentResponse(**cached)

    from app.services.data_ingestion.macro_data import MacroDataService

    macro = MacroDataService()
    macro_data = await macro.get_market_overview()

    vix = macro_data.get("vix")
    spy_change = macro_data.get("spy_change_pct", 0.0)

    # Compute fear/greed approximation
    if vix:
        if vix > 30:
            fear_greed = max(0, 50 - (vix - 20) * 2)
            label = "fear" if vix < 35 else "extreme_fear"
        elif vix < 15:
            fear_greed = min(100, 70 + (15 - vix) * 2)
            label = "greed" if vix > 12 else "extreme_greed"
        else:
            fear_greed = 50.0
            label = "neutral"
    else:
        fear_greed = 50.0
        label = "neutral"

    response = MarketSentimentResponse(
        market_fear_greed=round(fear_greed, 1),
        market_label=label,
        vix_level=vix,
        spy_change_pct=spy_change,
        qqq_change_pct=macro_data.get("qqq_change_pct"),
        sector_sentiment=macro_data.get("sector_sentiment", {}),
        top_bullish_tickers=[],
        top_bearish_tickers=[],
        generated_at=datetime.now(timezone.utc),
    )

    await cache_set(cache_key, response.model_dump(mode="json"), ttl=300)
    return response


@router.get("/news/latest", response_model=List[NewsArticleRead])
async def get_latest_news(
    ticker: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_session),
) -> List[NewsArticleRead]:
    """Fetch the latest news articles."""
    query = (
        select(NewsArticle)
        .order_by(desc(NewsArticle.published_at))
        .limit(limit)
    )
    if ticker:
        query = query.where(NewsArticle.ticker == ticker.upper())

    result = await db.execute(query)
    articles = result.scalars().all()
    return [NewsArticleRead.model_validate(a) for a in articles]
