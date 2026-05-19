"""Main prediction engine orchestrating all analysis services."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.prediction import Prediction
from app.services.ml.model_store import ModelStore


SIGNAL_WEIGHTS_DEFAULT = {
    "technical": 0.25,
    "sentiment": 0.20,
    "momentum": 0.20,
    "catalyst": 0.20,
    "macro": 0.10,
    "volume_anomaly": 0.05,
}


def _generate_explanation(
    ticker: str,
    confidence: float,
    tech_score: float,
    sentiment_score: float,
    catalyst_data: Dict,
    tech_data: Dict,
    upside_prob: float,
    expected_move: float,
    risk_rating: str,
) -> str:
    """Generate plain-English explanation for the prediction."""
    parts = []

    # Opening
    if confidence >= 80:
        parts.append(f"**{ticker}** shows a HIGH-CONFIDENCE setup ({confidence:.0f}%).")
    elif confidence >= 70:
        parts.append(f"**{ticker}** presents a GOOD setup ({confidence:.0f}% confidence).")
    else:
        parts.append(f"**{ticker}** is a WATCHLIST candidate ({confidence:.0f}% confidence).")

    # Technical
    trend = tech_data.get("trend", "neutral")
    if trend == "bullish":
        parts.append("The stock is in a bullish uptrend with price above key moving averages.")
    elif trend == "bearish":
        parts.append("Caution: stock shows bearish technical structure.")

    if tech_data.get("breakout"):
        parts.append("Breaking out above recent resistance — a key bullish signal.")

    gap = tech_data.get("gap_pct", 0)
    if gap > 2:
        parts.append(f"Pre-market gap up of {gap:.1f}% indicates strong buying interest.")

    # RSI
    rsi = tech_data.get("rsi")
    if rsi:
        if rsi < 35:
            parts.append(f"RSI at {rsi:.0f} suggests oversold conditions — potential bounce.")
        elif 50 <= rsi <= 65:
            parts.append(f"RSI at {rsi:.0f} is in the ideal bullish momentum zone.")
        elif rsi > 72:
            parts.append(f"RSI at {rsi:.0f} is elevated — watch for pullback before entry.")

    # Sentiment
    if sentiment_score > 0.3:
        parts.append("Market sentiment is strongly positive with bullish news flow.")
    elif sentiment_score > 0.1:
        parts.append("Sentiment is mildly positive.")
    elif sentiment_score < -0.2:
        parts.append("Negative sentiment headwinds — manage risk carefully.")

    # Catalyst
    catalyst_type = catalyst_data.get("primary_type", "none")
    catalyst_summary = catalyst_data.get("summary", "")
    if catalyst_type != "none" and catalyst_type != "":
        parts.append(f"Key catalyst detected: {catalyst_type.replace('_', ' ').title()}.")
        if catalyst_summary:
            parts.append(catalyst_summary[:150])

    # Probability and targets
    parts.append(
        f"Model estimates {upside_prob:.0f}% probability of upside with expected move of {expected_move:+.1f}%."
    )

    # Risk rating
    risk_emoji = {"low": "GREEN", "medium": "YELLOW", "high": "ORANGE", "very_high": "RED"}.get(risk_rating, "")
    parts.append(f"Risk rating: {risk_rating.upper()} {risk_emoji}.")

    return " ".join(parts)


class PredictionEngine:
    """Orchestrates all analysis services to produce a unified prediction."""

    def __init__(self) -> None:
        self.model_store = ModelStore()
        self._weights = self.model_store.load_signal_weights()

    async def predict(
        self,
        ticker: str,
        db: Optional[AsyncSession] = None,
        save_to_db: bool = True,
    ) -> Optional[Prediction]:
        """
        Run full analysis pipeline for a ticker.
        Returns None if confidence is below threshold.
        """
        logger.info("Running prediction for {}", ticker)

        try:
            # 1. Fetch market data
            from app.services.data_ingestion.market_data import MarketDataService
            market_svc = MarketDataService()
            df = await market_svc.fetch_ohlcv(ticker, period="6mo", interval="1d")

            if df is None or len(df) < 20:
                logger.warning("Insufficient price data for {}", ticker)
                return None

            # Check liquidity filters
            quote = await market_svc._fetch_single_quote(ticker)
            price = quote.get("price", 0)
            volume = quote.get("volume", 0)

            if price < settings.MIN_PRICE_THRESHOLD:
                logger.debug("{} below price threshold ({})", ticker, price)
                return None

            if (volume or 0) < settings.MIN_VOLUME_THRESHOLD:
                logger.debug("{} below volume threshold ({})", ticker, volume)
                return None

            # 2. Run analyses concurrently
            from app.services.analysis.technical_analysis import TechnicalAnalyzer
            from app.services.analysis.sentiment_analysis import SentimentAnalyzer
            from app.services.analysis.catalyst_detection import CatalystDetector
            from app.services.analysis.fundamental_analysis import FundamentalAnalyzer
            from app.services.data_ingestion.macro_data import MacroDataService

            tech_analyzer = TechnicalAnalyzer()
            sentiment_analyzer = SentimentAnalyzer()
            catalyst_detector = CatalystDetector()
            fundamental_analyzer = FundamentalAnalyzer()
            macro_svc = MacroDataService()

            (
                tech_result,
                sentiment_result,
                catalyst_result,
                macro_result,
                fundamental_result,
            ) = await asyncio.gather(
                tech_analyzer.analyze(ticker, df),
                sentiment_analyzer.analyze_ticker(ticker),
                catalyst_detector.analyze_ticker_catalysts(ticker),
                macro_svc.get_market_overview(),
                fundamental_analyzer.analyze(ticker),
                return_exceptions=True,
            )

            # Handle exceptions from gather
            if isinstance(tech_result, Exception):
                logger.warning("Technical analysis failed for {}: {}", ticker, tech_result)
                tech_result = {"score": 50.0, "trend": "neutral"}
            if isinstance(sentiment_result, Exception):
                sentiment_result = {"score": 0.0, "normalized_score": 50.0, "momentum": "stable"}
            if isinstance(catalyst_result, Exception):
                catalyst_result = {"score": 0.0, "primary_type": "none", "count": 0}
            if isinstance(macro_result, Exception):
                macro_result = {}
            if isinstance(fundamental_result, Exception):
                fundamental_result = {"score": 50.0}

            macro_score = await macro_svc.get_macro_score()

            # 3. Build feature vector
            from app.services.ml.feature_engineering import FeatureEngineer
            fe = FeatureEngineer()
            features = fe.build_feature_vector(
                df=df,
                technical_analysis=tech_result,
                sentiment_data=sentiment_result,
                catalyst_data=catalyst_result,
                macro_data={**macro_result, "macro_score": macro_score},
                fundamental_data=fundamental_result,
            )

            # 4. Volume anomaly score
            avg_vol = df["Volume"].tail(20).mean() if "Volume" in df.columns else 0
            current_vol = quote.get("volume", 0) or 0
            rel_vol = current_vol / avg_vol if avg_vol > 0 else 1.0
            volume_anomaly_score = min(100.0, rel_vol * 50)

            # 5. Momentum score (0-100)
            ret_5d = features.get("return_5d", 0)
            ret_20d = features.get("return_20d", 0)
            momentum_score = max(0.0, min(100.0, 50 + ret_5d * 3 + ret_20d * 1))

            # 6. ML ensemble prediction
            from app.services.ml.ensemble_model import EnsembleModel
            ensemble = EnsembleModel()
            upside_probability, expected_move = ensemble.predict(features)

            # 7. Weighted confidence score
            tech_score = float(tech_result.get("score", 50))
            sentiment_normalized = float(sentiment_result.get("normalized_score", 50))
            catalyst_raw = float(catalyst_result.get("score", 0))
            catalyst_score_normalized = max(0.0, min(100.0, (catalyst_raw + 10) / 20 * 100))

            weights = self._weights
            confidence_raw = (
                tech_score * weights.get("technical", 0.25)
                + sentiment_normalized * weights.get("sentiment", 0.20)
                + momentum_score * weights.get("momentum", 0.20)
                + catalyst_score_normalized * weights.get("catalyst", 0.20)
                + macro_score * weights.get("macro", 0.10)
                + volume_anomaly_score * weights.get("volume_anomaly", 0.05)
            )

            # Normalize to 0-100
            confidence_score = max(0.0, min(100.0, confidence_raw))

            # Anti-overtrading gate
            if confidence_score < settings.MIN_CONFIDENCE_THRESHOLD:
                logger.info(
                    "{} below confidence threshold ({:.1f} < {:.1f})",
                    ticker,
                    confidence_score,
                    settings.MIN_CONFIDENCE_THRESHOLD,
                )
                return None

            # 8. Risk rating
            volatility = features.get("volatility_20d", 20.0)
            if volatility < 15 and confidence_score > 75:
                risk_rating = "low"
            elif volatility < 25:
                risk_rating = "medium"
            elif volatility < 40:
                risk_rating = "high"
            else:
                risk_rating = "very_high"

            # 9. Entry/exit zones from technical analysis
            entry_low = tech_result.get("entry_zone_low") or price * 0.99
            entry_high = tech_result.get("entry_zone_high") or price * 1.01
            stop_loss = tech_result.get("stop_loss") or price * 0.93
            atr = tech_result.get("atr") or price * 0.02

            profit_target_1 = round(entry_high * (1 + abs(expected_move) * 0.01), 2)
            profit_target_2 = round(entry_high * (1 + abs(expected_move) * 0.02), 2)

            # 10. Recommendation type
            if confidence_score >= settings.MIN_CONFIDENCE_FOR_PRIMARY:
                recommendation_type = "primary"
            elif confidence_score >= settings.MIN_CONFIDENCE_FOR_SECONDARY:
                recommendation_type = "secondary"
            else:
                recommendation_type = "watchlist"

            # 11. Hold duration
            catalyst_duration = catalyst_result.get("duration", "1d")
            if confidence_score >= 80:
                hold_duration = "1w"
            elif confidence_score >= 70:
                hold_duration = "3d"
            else:
                hold_duration = catalyst_duration

            # 12. Plain English explanation
            explanation = _generate_explanation(
                ticker=ticker,
                confidence=confidence_score,
                tech_score=tech_score,
                sentiment_score=float(sentiment_result.get("score", 0)),
                catalyst_data=catalyst_result,
                tech_data=tech_result,
                upside_prob=upside_probability,
                expected_move=expected_move,
                risk_rating=risk_rating,
            )

            # 13. Create prediction object
            prediction = Prediction(
                ticker=ticker,
                confidence_score=round(confidence_score, 2),
                upside_probability=round(upside_probability, 2),
                downside_risk=round(100 - upside_probability, 2),
                volatility_score=round(min(100, volatility * 2), 2),
                momentum_score=round(momentum_score, 2),
                sentiment_score=round(float(sentiment_result.get("score", 0)) * 100, 2),
                technical_score=round(tech_score, 2),
                catalyst_score=round(catalyst_raw, 2),
                macro_score=round(macro_score, 2),
                volume_anomaly_score=round(volume_anomaly_score, 2),
                entry_zone_low=round(float(entry_low), 2),
                entry_zone_high=round(float(entry_high), 2),
                stop_loss=round(float(stop_loss), 2),
                profit_target_1=round(profit_target_1, 2),
                profit_target_2=round(profit_target_2, 2),
                expected_move_pct=round(expected_move, 2),
                expected_hold_duration=hold_duration,
                risk_rating=risk_rating,
                recommendation_type=recommendation_type,
                catalyst_summary=catalyst_result.get("summary"),
                technical_summary=(
                    f"Trend: {tech_result.get('trend')}. "
                    f"RSI: {tech_result.get('rsi', 'N/A')}. "
                    f"Breakout: {'Yes' if tech_result.get('breakout') else 'No'}."
                ),
                sentiment_summary=(
                    f"Score: {sentiment_result.get('score', 0):.2f}. "
                    f"Momentum: {sentiment_result.get('momentum', 'stable')}. "
                    f"Articles: {sentiment_result.get('article_count', 0)}."
                ),
                plain_english_explanation=explanation,
                signal_types={
                    "breakout": bool(tech_result.get("breakout")),
                    "trend_bullish": tech_result.get("trend") == "bullish",
                    "volume_surge": rel_vol >= 2.0,
                    "catalyst": catalyst_result.get("count", 0) > 0,
                    "sentiment_positive": float(sentiment_result.get("score", 0)) > 0.1,
                    "gap_up": float(tech_result.get("gap_pct", 0)) > 1.0,
                },
                feature_values={k: round(v, 4) for k, v in list(features.items())[:30]},
                prediction_date=datetime.now(timezone.utc),
            )

            # 14. Save to database
            if save_to_db and db is not None:
                db.add(prediction)
                await db.flush()
                await db.refresh(prediction)
                logger.info(
                    "Prediction saved: {} {} conf={:.1f}",
                    ticker,
                    recommendation_type,
                    confidence_score,
                )

            return prediction

        except Exception as exc:
            logger.error("Prediction engine error for {}: {}", ticker, exc)
            import traceback
            logger.debug(traceback.format_exc())
            return None
