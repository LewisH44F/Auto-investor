"""Sentiment and news endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from app.services.news_service import NewsService
from app.services.market_data import MarketDataService

router = APIRouter()
news_svc = NewsService()
market_svc = MarketDataService()


@router.get("/market-overview")
async def get_market_sentiment():
    macro = await market_svc.get_macro_snapshot()
    articles = await news_svc.fetch_all_news(max_articles=20)
    scores = [a.get("sentiment_score", 0) for a in articles]
    avg = sum(scores) / len(scores) if scores else 0
    return {
        "overall_sentiment": round(avg, 3),
        "sentiment_label": "BULLISH" if avg > 0.1 else ("BEARISH" if avg < -0.1 else "NEUTRAL"),
        "vix": macro.get("vix", 20),
        "market_condition": macro.get("market_condition", "NORMAL"),
        "nasdaq_change_pct": macro.get("nasdaq_change_pct", 0),
        "articles_analyzed": len(articles),
    }


@router.get("/news")
async def get_latest_news(limit: int = 30):
    articles = await news_svc.fetch_all_news(max_articles=limit)
    return {"articles": articles, "total": len(articles)}


@router.get("/{ticker}")
async def get_ticker_sentiment(ticker: str):
    articles = await news_svc.fetch_ticker_news(ticker.upper())
    scores = [a.get("sentiment_score", 0) for a in articles]
    avg = sum(scores) / len(scores) if scores else 0
    return {
        "ticker": ticker.upper(),
        "sentiment_score": round(avg, 3),
        "sentiment_label": "BULLISH" if avg > 0.1 else ("BEARISH" if avg < -0.1 else "NEUTRAL"),
        "articles": articles,
        "article_count": len(articles),
    }
