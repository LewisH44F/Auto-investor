"""Nightly analysis worker - generates next-day picks."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.config import settings
from app.core.database import AsyncSessionLocal


class NightlyAnalysisWorker:
    """
    Full nightly scan of the NASDAQ universe.
    Ranks stocks by confidence and generates predictions.
    """

    async def run(self) -> Dict[str, Any]:
        """Execute the full nightly analysis pipeline."""
        start_time = datetime.now(timezone.utc)
        logger.info("Nightly analysis started at {}", start_time)

        async with AsyncSessionLocal() as session:
            try:
                results = await self._execute_pipeline(session)
                await session.commit()

                # Send notifications
                await self._send_notifications(results)

                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                logger.info(
                    "Nightly analysis completed in {:.1f}s. Primary: {}, Secondary: {}, Watchlist: {}",
                    duration,
                    1 if results["primary"] else 0,
                    len(results["secondary"]),
                    len(results["watchlist"]),
                )

                return {
                    **results,
                    "duration_seconds": duration,
                    "started_at": start_time.isoformat(),
                }

            except Exception as exc:
                logger.error("Nightly analysis failed: {}", exc)
                import traceback
                logger.debug(traceback.format_exc())
                return {"error": str(exc)}

    async def _execute_pipeline(
        self, session
    ) -> Dict[str, Any]:
        """Run the full scan and prediction pipeline."""
        from app.services.data_ingestion.market_data import MarketDataService
        from app.services.ml.prediction_engine import PredictionEngine

        market_svc = MarketDataService()
        engine = PredictionEngine()

        # 1. Get liquid NASDAQ universe
        logger.info("Fetching NASDAQ universe...")
        candidates = await market_svc.batch_fetch_nasdaq_universe(
            min_price=settings.MIN_PRICE_THRESHOLD,
            min_volume=settings.MIN_VOLUME_THRESHOLD,
            limit=200,
        )

        if not candidates:
            logger.warning("No candidates found from NASDAQ universe scan")
            return {"primary": None, "secondary": [], "watchlist": []}

        logger.info("Running predictions on {} candidates...", len(candidates))

        # 2. Run predictions concurrently in batches
        all_predictions = []
        batch_size = 10

        for i in range(0, len(candidates), batch_size):
            batch = candidates[i : i + batch_size]
            tickers = [c["ticker"] for c in batch]

            tasks = [
                engine.predict(ticker, db=session, save_to_db=True)
                for ticker in tickers
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for ticker, pred in zip(tickers, batch_results):
                if isinstance(pred, Exception):
                    logger.debug("Prediction failed for {}: {}", ticker, pred)
                elif pred is not None:
                    all_predictions.append(pred)

            # Small delay between batches to avoid API rate limits
            if i + batch_size < len(candidates):
                await asyncio.sleep(1.0)

        logger.info(
            "Predictions generated: {} / {} stocks passed threshold",
            len(all_predictions),
            len(candidates),
        )

        # 3. Sort by confidence
        all_predictions.sort(key=lambda p: p.confidence_score, reverse=True)

        # 4. Classify picks
        primary = None
        secondary = []
        watchlist = []

        for pred in all_predictions:
            if pred.recommendation_type == "primary" and primary is None:
                primary = pred
            elif pred.recommendation_type == "secondary":
                if len(secondary) < 3:
                    secondary.append(pred)
            elif pred.recommendation_type == "watchlist":
                if len(watchlist) < 10:
                    watchlist.append(pred)

        return {
            "primary": primary,
            "secondary": secondary,
            "watchlist": watchlist,
            "total_scanned": len(candidates),
            "total_predictions": len(all_predictions),
        }

    async def _send_notifications(self, results: Dict[str, Any]) -> None:
        """Send nightly picks via all configured channels."""
        primary = results.get("primary")
        secondary = results.get("secondary", [])
        watchlist = results.get("watchlist", [])

        if not primary and not secondary:
            logger.info("No high-confidence picks tonight, skipping notifications")
            return

        # Build message
        lines = ["🌙 *AutoInvestor AI - Tonight's Picks*", ""]

        if primary:
            lines.extend([
                f"🚨 *PRIMARY PICK: {primary.ticker}*",
                f"Confidence: `{primary.confidence_score:.1f}%`",
                f"{primary.plain_english_explanation or ''}",
                f"Entry: `${primary.entry_zone_low:.2f} - ${primary.entry_zone_high:.2f}`",
                f"Stop Loss: `${primary.stop_loss:.2f}`",
                f"Target: `${primary.profit_target_1:.2f}`",
                "",
            ])

        if secondary:
            lines.append("📊 *Secondary Picks:*")
            for pred in secondary[:3]:
                lines.append(
                    f"• {pred.ticker} — {pred.confidence_score:.0f}% confidence"
                )
            lines.append("")

        if watchlist:
            lines.append("👀 *Watchlist:*")
            lines.append(", ".join(p.ticker for p in watchlist[:5]))
            lines.append("")

        lines.append(f"Stocks scanned: {results.get('total_scanned', 0)}")
        lines.append("_Not financial advice. Always DYOR._")

        message = "\n".join(lines)

        tasks = []

        # Discord
        if settings.DISCORD_WEBHOOK_URL:
            from app.services.notifications.discord_service import DiscordService
            discord = DiscordService()
            tasks.append(discord.send_message(message))

        # Telegram
        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            from app.services.notifications.telegram_service import TelegramService
            telegram = TelegramService()
            tasks.append(telegram.send_message(message))

        # Email
        if settings.SMTP_USERNAME and settings.NOTIFICATION_EMAIL:
            from app.services.notifications.email_service import EmailService
            email_svc = EmailService()
            subject = "AutoInvestor AI - Tonight's Picks"
            body = message.replace("*", "").replace("`", "").replace("_", "")
            tasks.append(email_svc.send_email(subject=subject, body=body))

        if tasks:
            results_notif = await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(
                "Notifications sent: {} channels",
                sum(1 for r in results_notif if r is True),
            )
