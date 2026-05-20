"""Core prediction engine: scores each stock, generates ranked recommendations."""
from __future__ import annotations

import asyncio
from datetime import datetime, date
from typing import Optional

from loguru import logger
from sqlalchemy import text

from app.core.cache import cache
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.market_data import MarketDataService, NASDAQ_TICKERS
from app.services.technical import TechnicalAnalyzer
from app.services.news_service import NewsService

market_svc = MarketDataService()
tech_analyzer = TechnicalAnalyzer()
news_svc = NewsService()

# Signal weights (learned over time, stored in DB)
DEFAULT_WEIGHTS = {
    "technical": 0.35,
    "sentiment": 0.20,
    "volume": 0.20,
    "momentum": 0.15,
    "macro": 0.10,
}


class PredictionEngine:

    async def generate_prediction(self, ticker: str) -> Optional[dict]:
        """
        Analyse a single ticker. Returns prediction dict or None if confidence
        is below threshold / stock fails liquidity filters.
        """
        try:
            # 1. Fetch OHLCV
            df = await market_svc.fetch_ohlcv(ticker, period="3mo")
            if df is None or len(df) < 20:
                return None

            # 2. Liquidity filter
            quote = await market_svc.get_quote(ticker)
            price = quote.get("price", 0)
            volume = quote.get("volume", 0)
            if price < settings.MIN_PRICE_THRESHOLD or volume < settings.MIN_VOLUME_THRESHOLD:
                return None

            # 3. Technical analysis
            tech = tech_analyzer.analyze(df)

            # 4. News sentiment
            articles = await news_svc.fetch_ticker_news(ticker)
            sentiment_score = 0.0
            if articles:
                scores = [a.get("sentiment_score", 0) for a in articles]
                sentiment_score = sum(scores) / len(scores)
            catalyst = next((a.get("catalyst_type") for a in articles if a.get("catalyst_type") != "general"), None)

            # 5. Macro context
            macro = cache.get("macro_snapshot") or {}
            vix = macro.get("vix", 20)
            macro_score = max(0.0, min(100.0, 80.0 - (vix - 15) * 2))

            # 6. Compute sub-scores (0-100)
            technical_score = tech.get("composite_score", 50.0)
            sentiment_norm = (sentiment_score + 1) / 2 * 100  # -1..1 -> 0..100
            volume_score = min(100.0, tech.get("relative_volume", 1.0) * 40)
            momentum_score = self._momentum_score(df, tech)

            # 7. Weighted ensemble
            w = DEFAULT_WEIGHTS
            confidence = (
                technical_score * w["technical"] +
                sentiment_norm  * w["sentiment"] +
                volume_score    * w["volume"] +
                momentum_score  * w["momentum"] +
                macro_score     * w["macro"]
            )
            confidence = round(min(100.0, max(0.0, confidence)), 1)

            # 8. Anti-overtrading gate
            if confidence < settings.MIN_CONFIDENCE_THRESHOLD:
                return None

            # 9. Build prediction
            current_price = price
            expected_move = round((confidence - 50) / 50 * tech.get("atr_pct", 2.0) * 3, 2)
            hold_duration = self._estimate_hold_duration(tech, catalyst)
            risk_rating = "low" if confidence > 80 else ("medium" if confidence > 70 else "high")

            explanation = self._generate_explanation(
                ticker, confidence, tech, sentiment_score, catalyst, hold_duration, articles
            )

            signals_used = ["technical", "volume"]
            if articles:
                signals_used.append("sentiment")
            if catalyst:
                signals_used.append("catalyst")
            if tech.get("unusual_volume"):
                signals_used.append("unusual_volume")

            return {
                "ticker": ticker,
                "confidence_score": confidence,
                "upside_probability": round(confidence * 0.9, 1),
                "downside_risk": round((100 - confidence) * 0.6, 1),
                "volatility_score": round(tech.get("atr_pct", 2.0) * 10, 1),
                "momentum_score": round(momentum_score, 1),
                "catalyst_summary": catalyst or "Technical setup",
                "technical_summary": f"RSI {tech.get('rsi', 50):.0f} | {tech.get('trend', 'NEUTRAL')} | {'Breakout' if tech.get('breakout') else 'No breakout'}",
                "sentiment_summary": f"Sentiment {'+' if sentiment_score >= 0 else ''}{sentiment_score:.2f} from {len(articles)} articles",
                "entry_zone_low": tech.get("entry_zone_low", current_price * 0.99),
                "entry_zone_high": tech.get("entry_zone_high", current_price * 1.005),
                "stop_loss": tech.get("stop_loss", current_price * 0.93),
                "profit_target_1": tech.get("profit_target_1", current_price * 1.05),
                "profit_target_2": tech.get("profit_target_2", current_price * 1.10),
                "expected_move_pct": expected_move,
                "expected_hold_duration": hold_duration,
                "risk_rating": risk_rating,
                "plain_english_explanation": explanation,
                "signal_types": signals_used,
                "prediction_date": date.today().isoformat(),
                "current_price": current_price,
                "company_name": quote.get("name", ticker),
                "sector": quote.get("sector", ""),
            }
        except Exception as e:
            logger.warning("Prediction failed for {}: {}", ticker, e)
            return None

    def _momentum_score(self, df, tech: dict) -> float:
        """Rate of change + EMA alignment."""
        score = 50.0
        try:
            close = df["Close"] if "Close" in df.columns else df.iloc[:, 3]
            roc_5 = (float(close.iloc[-1]) - float(close.iloc[-5])) / float(close.iloc[-5]) * 100
            if roc_5 > 5:
                score += 25
            elif roc_5 > 2:
                score += 15
            elif roc_5 > 0:
                score += 5
            elif roc_5 < -5:
                score -= 20
            above_emas = sum(1 for s in [9, 21, 50] if tech.get(f"above_ema_{s}", False))
            score += above_emas * 8
        except Exception:
            pass
        return round(min(100.0, max(0.0, score)), 1)

    def _estimate_hold_duration(self, tech: dict, catalyst: Optional[str]) -> str:
        if catalyst in ("fda_approval", "merger_acquisition", "earnings_beat"):
            return "2-5 days"
        if tech.get("breakout"):
            return "2-5 days"
        if tech.get("bb_squeeze"):
            return "overnight"
        return "overnight"

    def _generate_explanation(
        self, ticker: str, confidence: float, tech: dict,
        sentiment: float, catalyst: Optional[str], hold: str, articles: list
    ) -> str:
        parts = [f"{ticker} shows a {confidence:.0f}% confidence setup for {hold}."]
        trend = tech.get("trend", "NEUTRAL")
        rsi = tech.get("rsi", 50)
        parts.append(f"The stock is in a {trend} trend with RSI at {rsi:.0f}.")
        if tech.get("breakout"):
            parts.append("Price is near a key resistance breakout with elevated volume confirmation.")
        if tech.get("bb_squeeze"):
            parts.append("Bollinger Band squeeze detected — a directional move is likely imminent.")
        if catalyst:
            readable = catalyst.replace("_", " ").title()
            parts.append(f"A {readable} catalyst has been identified in recent news.")
        if sentiment > 0.2:
            parts.append(f"News sentiment is positive (+{sentiment:.2f}), supporting bullish momentum.")
        elif sentiment < -0.2:
            parts.append(f"Note: news sentiment is cautious ({sentiment:.2f}) — monitor for adverse developments.")
        if tech.get("unusual_volume"):
            parts.append(f"Unusual volume detected ({tech.get('relative_volume', 1):.1f}x avg) — potential institutional activity.")
        parts.append(f"Risk rating: {('Low' if confidence > 80 else 'Medium' if confidence > 70 else 'High')}. Always use stop-loss discipline.")
        return " ".join(parts)


class NightlyScanner:
    """Runs the full NASDAQ scan and persists tonight's top picks."""

    engine = PredictionEngine()

    async def run(self) -> list[dict]:
        logger.info("Starting nightly NASDAQ scan...")
        tickers = NASDAQ_TICKERS[:80]  # limit for speed; extend for production
        predictions = []

        # Process in batches to avoid rate-limiting
        batch_size = 10
        for i in range(0, len(tickers), batch_size):
            batch = tickers[i:i + batch_size]
            tasks = [self.engine.generate_prediction(t) for t in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, dict):
                    predictions.append(result)
            await asyncio.sleep(1)  # be gentle with yfinance

        # Sort by confidence
        predictions.sort(key=lambda x: x["confidence_score"], reverse=True)

        # Assign recommendation types
        for i, pred in enumerate(predictions[:settings.MAX_PREDICTIONS_PER_NIGHT]):
            if i == 0 and pred["confidence_score"] >= settings.MIN_CONFIDENCE_FOR_PRIMARY:
                pred["recommendation_type"] = "primary"
            elif i < 3 and pred["confidence_score"] >= settings.MIN_CONFIDENCE_FOR_SECONDARY:
                pred["recommendation_type"] = "secondary"
            else:
                pred["recommendation_type"] = "watchlist"

        top = predictions[:settings.MAX_PREDICTIONS_PER_NIGHT]

        # Persist to DB
        await self._save_predictions(top)
        cache.set("tonight_predictions", top, ttl=3600)
        logger.info("Nightly scan complete: {} predictions saved", len(top))
        return top

    async def _save_predictions(self, predictions: list[dict]) -> None:
        async with AsyncSessionLocal() as session:
            for p in predictions:
                await session.execute(
                    text("""
                        INSERT INTO predictions (
                            ticker, confidence_score, upside_probability, downside_risk,
                            volatility_score, momentum_score, catalyst_summary, technical_summary,
                            sentiment_summary, entry_zone_low, entry_zone_high, stop_loss,
                            profit_target_1, profit_target_2, expected_move_pct,
                            expected_hold_duration, risk_rating, recommendation_type,
                            plain_english_explanation, signal_types, prediction_date, created_at
                        ) VALUES (
                            :ticker, :confidence_score, :upside_probability, :downside_risk,
                            :volatility_score, :momentum_score, :catalyst_summary, :technical_summary,
                            :sentiment_summary, :entry_zone_low, :entry_zone_high, :stop_loss,
                            :profit_target_1, :profit_target_2, :expected_move_pct,
                            :expected_hold_duration, :risk_rating, :recommendation_type,
                            :plain_english_explanation, :signal_types, :prediction_date, :created_at
                        )
                    """),
                    {
                        **{k: v for k, v in p.items() if k in [
                            "ticker","confidence_score","upside_probability","downside_risk",
                            "volatility_score","momentum_score","catalyst_summary","technical_summary",
                            "sentiment_summary","entry_zone_low","entry_zone_high","stop_loss",
                            "profit_target_1","profit_target_2","expected_move_pct",
                            "expected_hold_duration","risk_rating","recommendation_type",
                            "plain_english_explanation","prediction_date",
                        ]},
                        "signal_types": ",".join(p.get("signal_types", [])),
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )
            await session.commit()
