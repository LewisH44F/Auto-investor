"""Sentiment-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class SentimentRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    source: str
    score: float
    score_normalized: Optional[float] = None
    volume: Optional[int] = None
    bullish_count: Optional[int] = None
    bearish_count: Optional[int] = None
    momentum: Optional[str] = None
    timestamp: datetime


class AnalystRatingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    firm: Optional[str] = None
    rating: Optional[str] = None
    previous_rating: Optional[str] = None
    rating_change: Optional[str] = None
    price_target: Optional[float] = None
    previous_price_target: Optional[float] = None
    price_target_change_pct: Optional[float] = None
    timestamp: datetime


class TickerSentimentResponse(BaseModel):
    """Comprehensive sentiment analysis for a ticker."""

    ticker: str
    overall_score: float           # -1 to 1
    overall_label: str             # positive / negative / neutral
    sentiment_momentum: str        # improving / deteriorating / stable
    confidence: float

    # Source breakdown
    news_score: Optional[float] = None
    reddit_score: Optional[float] = None
    twitter_score: Optional[float] = None
    analyst_consensus: Optional[str] = None

    # Analyst data
    analyst_ratings: List[AnalystRatingRead] = []
    avg_price_target: Optional[float] = None
    num_analysts: Optional[int] = None

    # Recent records
    recent_records: List[SentimentRecordRead] = []

    generated_at: datetime


class MarketSentimentResponse(BaseModel):
    """Broad market sentiment overview."""

    market_fear_greed: float           # 0-100
    market_label: str                  # extreme_fear / fear / neutral / greed / extreme_greed
    vix_level: Optional[float] = None
    spy_change_pct: Optional[float] = None
    qqq_change_pct: Optional[float] = None
    sector_sentiment: Dict[str, float] = {}
    top_bullish_tickers: List[str] = []
    top_bearish_tickers: List[str] = []
    generated_at: datetime


class NewsArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: Optional[str] = None
    headline: str
    summary: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    published_at: Optional[datetime] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    impact_score: Optional[float] = None
    catalyst_type: Optional[str] = None
    catalyst_strength: Optional[float] = None
