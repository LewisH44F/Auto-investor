"""Self-learning feedback engine."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import LearningLog, ModelPerformance, PatternRecord
from app.models.prediction import Prediction, PredictionFeedback
from app.services.ml.model_store import ModelStore


class FeedbackEngine:
    """Records outcomes, learns from predictions, and updates signal weights."""

    def __init__(self) -> None:
        self.model_store = ModelStore()

    async def record_outcomes(
        self,
        db: AsyncSession,
        days_after: int = 3,
    ) -> int:
        """
        Find predictions that are N days old without an outcome,
        fetch actual price data, and record the result.
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_after)

        result = await db.execute(
            select(Prediction).where(
                Prediction.is_outcome_recorded == False,
                Prediction.prediction_date <= cutoff_date,
            )
        )
        pending_predictions = result.scalars().all()

        logger.info(
            "Recording outcomes for {} pending predictions", len(pending_predictions)
        )

        recorded_count = 0
        for pred in pending_predictions:
            try:
                outcome_data = await self._fetch_outcome(
                    ticker=pred.ticker,
                    entry_date=pred.prediction_date,
                    days=days_after,
                )

                if outcome_data is None:
                    continue

                actual_move_pct = outcome_data["move_pct"]

                # Classify outcome
                if actual_move_pct > 3.0:
                    outcome_label = "win"
                elif actual_move_pct < -3.0:
                    outcome_label = "loss"
                else:
                    outcome_label = "neutral"

                # Generate lesson
                lesson = self._generate_lesson(pred, actual_move_pct, outcome_label)

                # Update prediction
                pred.actual_outcome = outcome_label
                pred.actual_move_pct = round(actual_move_pct, 2)
                pred.outcome_recorded_at = datetime.now(timezone.utc)
                pred.prediction_error = round(
                    abs(actual_move_pct - (pred.expected_move_pct or 0)), 2
                )
                pred.is_outcome_recorded = True

                # Create feedback record
                feedback = PredictionFeedback(
                    prediction_id=pred.id,
                    ticker=pred.ticker,
                    actual_close=outcome_data.get("actual_close"),
                    entry_price=outcome_data.get("entry_price"),
                    holding_days=days_after,
                    realized_gain_pct=round(actual_move_pct, 2),
                    max_gain_pct=outcome_data.get("max_gain_pct"),
                    max_loss_pct=outcome_data.get("max_loss_pct"),
                    hit_target_1=(
                        outcome_data.get("actual_high", 0) >= (pred.profit_target_1 or 0)
                        if pred.profit_target_1 else None
                    ),
                    hit_stop_loss=(
                        outcome_data.get("actual_low", float("inf")) <= (pred.stop_loss or float("-inf"))
                        if pred.stop_loss else None
                    ),
                    outcome_label=outcome_label,
                    lessons_learned=lesson,
                )
                db.add(feedback)

                # Log the learning event
                log_entry = LearningLog(
                    event_type="outcome_recorded",
                    ticker=pred.ticker,
                    prediction_id=pred.id,
                    actual_vs_predicted=f"Predicted: {pred.expected_move_pct:.1f}%, Actual: {actual_move_pct:.1f}%",
                    lesson=lesson,
                    severity="info" if outcome_label == "win" else "warning",
                )
                db.add(log_entry)

                recorded_count += 1

            except Exception as exc:
                logger.error(
                    "Failed to record outcome for prediction {}: {}", pred.id, exc
                )

        await db.flush()

        if recorded_count > 0:
            await self.update_signal_weights(db)
            logger.info("Recorded {} outcomes and updated weights", recorded_count)

        return recorded_count

    async def _fetch_outcome(
        self, ticker: str, entry_date: datetime, days: int
    ) -> Optional[Dict[str, Any]]:
        """Fetch actual price data for outcome recording."""
        from app.services.data_ingestion.market_data import MarketDataService
        import yfinance as yf

        try:
            end_date = entry_date + timedelta(days=days + 5)
            loop = asyncio.get_event_loop()

            df = await loop.run_in_executor(
                None,
                lambda: yf.download(
                    ticker,
                    start=entry_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                    progress=False,
                    auto_adjust=True,
                ),
            )

            if df is None or df.empty or len(df) < 2:
                return None

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            entry_price = float(df["Close"].iloc[0])
            outcome_idx = min(days, len(df) - 1)
            actual_close = float(df["Close"].iloc[outcome_idx])

            move_pct = (actual_close / entry_price - 1) * 100

            window = df.iloc[: outcome_idx + 1]
            max_high = float(window["High"].max()) if "High" in window.columns else actual_close
            min_low = float(window["Low"].min()) if "Low" in window.columns else actual_close

            return {
                "entry_price": entry_price,
                "actual_close": actual_close,
                "move_pct": round(move_pct, 2),
                "actual_high": max_high,
                "actual_low": min_low,
                "max_gain_pct": round((max_high / entry_price - 1) * 100, 2),
                "max_loss_pct": round((min_low / entry_price - 1) * 100, 2),
            }

        except Exception as exc:
            logger.warning("Outcome fetch failed for {}: {}", ticker, exc)
            return None

    def _generate_lesson(
        self,
        pred: Prediction,
        actual_move: float,
        outcome: str,
    ) -> str:
        """Generate a lesson string from the prediction vs reality."""
        parts = []

        if outcome == "win":
            parts.append(f"Correct call: {pred.ticker} moved {actual_move:.1f}%.")
            if pred.catalyst_score and pred.catalyst_score > 5:
                parts.append("Catalyst strength was a key driver.")
            if pred.technical_score and pred.technical_score > 70:
                parts.append("Strong technicals confirmed the move.")
        elif outcome == "loss":
            parts.append(f"Incorrect call: {pred.ticker} moved {actual_move:.1f}% (expected +).")
            if pred.macro_score and pred.macro_score < 40:
                parts.append("Macro headwinds may have overridden the setup.")
            if pred.sentiment_score and pred.sentiment_score < 0:
                parts.append("Negative sentiment was underweighted.")
        else:
            parts.append(f"Neutral: {pred.ticker} moved only {actual_move:.1f}%.")
            parts.append("Signal may have been premature or lacked conviction.")

        return " ".join(parts)

    async def update_signal_weights(self, db: AsyncSession) -> Dict[str, float]:
        """
        Update signal weights based on recent prediction outcomes.
        Weights are adjusted up for features correlated with wins,
        down for features correlated with losses.
        """
        result = await db.execute(
            select(Prediction).where(Prediction.is_outcome_recorded == True)
        )
        all_predictions = result.scalars().all()

        if len(all_predictions) < 10:
            logger.info("Not enough predictions to update weights ({} < 10)", len(all_predictions))
            return self.model_store.load_signal_weights()

        # Compute win rates by signal contribution
        weights = self.model_store.load_signal_weights()

        win_correlations = {
            "technical": [],
            "sentiment": [],
            "momentum": [],
            "catalyst": [],
            "macro": [],
            "volume_anomaly": [],
        }

        for pred in all_predictions:
            is_win = 1.0 if pred.actual_outcome == "win" else 0.0

            if pred.technical_score is not None:
                win_correlations["technical"].append(
                    (pred.technical_score / 100, is_win)
                )
            if pred.sentiment_score is not None:
                win_correlations["sentiment"].append(
                    ((pred.sentiment_score + 100) / 200, is_win)
                )
            if pred.momentum_score is not None:
                win_correlations["momentum"].append(
                    (pred.momentum_score / 100, is_win)
                )
            if pred.catalyst_score is not None:
                win_correlations["catalyst"].append(
                    ((pred.catalyst_score + 10) / 20, is_win)
                )
            if pred.macro_score is not None:
                win_correlations["macro"].append(
                    (pred.macro_score / 100, is_win)
                )
            if pred.volume_anomaly_score is not None:
                win_correlations["volume_anomaly"].append(
                    (pred.volume_anomaly_score / 100, is_win)
                )

        # Adjust weights based on correlation with wins
        import numpy as np
        new_weights = dict(weights)
        alpha = 0.05  # Learning rate

        for signal, data in win_correlations.items():
            if len(data) < 5:
                continue

            signal_values = [d[0] for d in data]
            win_values = [d[1] for d in data]

            # Pearson correlation
            if len(set(signal_values)) > 1 and len(set(win_values)) > 1:
                correlation = float(np.corrcoef(signal_values, win_values)[0, 1])
                if not np.isnan(correlation):
                    # Increase weight if positively correlated, decrease if negative
                    adjustment = correlation * alpha
                    new_weights[signal] = max(
                        0.01, min(0.50, weights.get(signal, 0.1) + adjustment)
                    )

        # Normalize
        total = sum(new_weights.values())
        if total > 0:
            new_weights = {k: round(v / total, 4) for k, v in new_weights.items()}

        self.model_store.save_signal_weights(new_weights)

        # Log the update
        log_entry = LearningLog(
            event_type="weight_updated",
            lesson=f"Weights updated based on {len(all_predictions)} predictions",
            before_state=weights,
            after_state=new_weights,
            severity="info",
        )
        db.add(log_entry)
        await db.flush()

        logger.info("Signal weights updated: {}", new_weights)
        return new_weights

    async def record_model_performance(self, db: AsyncSession) -> None:
        """Snapshot daily model performance to DB."""
        result = await db.execute(
            select(Prediction).where(Prediction.is_outcome_recorded == True)
        )
        predictions = result.scalars().all()

        if not predictions:
            return

        wins = [p for p in predictions if p.actual_outcome == "win"]
        losses = [p for p in predictions if p.actual_outcome == "loss"]
        total = len(predictions)
        win_rate = len(wins) / total if total > 0 else 0.0
        avg_return = sum(p.actual_move_pct or 0 for p in predictions) / total
        avg_conf = sum(p.confidence_score for p in predictions) / total

        perf = ModelPerformance(
            date=datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0),
            win_rate=round(win_rate, 4),
            avg_confidence=round(avg_conf, 2),
            avg_return=round(avg_return, 2),
            total_predictions=total,
            total_wins=len(wins),
            total_losses=len(losses),
            total_neutral=total - len(wins) - len(losses),
            signal_type_weights=self.model_store.load_signal_weights(),
        )
        db.add(perf)
        await db.flush()
        logger.info(
            "Model performance recorded: win_rate={:.2%}, avg_return={:.2f}%",
            win_rate,
            avg_return,
        )


# Avoid circular import
import pandas as pd
