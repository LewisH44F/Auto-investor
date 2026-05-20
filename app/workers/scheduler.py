"""APScheduler background jobs: pre-market scan, nightly analysis, feedback loop."""
from __future__ import annotations

import asyncio
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger


def _run_async(coro):
    """Helper to run async coroutines from sync scheduler callbacks."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(coro)
    finally:
        loop.close()


def _nightly_scan_job():
    async def _run():
        from app.services.prediction_engine import NightlyScanner
        from app.services.market_data import MarketDataService
        logger.info("Nightly scan starting...")
        try:
            macro = await MarketDataService().get_macro_snapshot()
            from app.core.cache import cache
            cache.set("macro_snapshot", macro, ttl=3600)
        except Exception as e:
            logger.warning("Macro fetch failed: {}", e)
        try:
            scanner = NightlyScanner()
            predictions = await scanner.run()
            logger.info("Nightly scan produced {} picks", len(predictions))
            await _send_notifications(predictions)
        except Exception as e:
            logger.error("Nightly scan failed: {}", e)
    _run_async(_run())


def _pre_market_job():
    async def _run():
        from app.services.market_data import MarketDataService
        from app.core.cache import cache
        logger.info("Pre-market update running...")
        try:
            svc = MarketDataService()
            macro = await svc.get_macro_snapshot()
            cache.set("macro_snapshot", macro, ttl=1800)
            cache.clear_pattern("quote:*")
            logger.info("Pre-market cache refreshed. VIX={}", macro.get("vix", "?"))
        except Exception as e:
            logger.warning("Pre-market job failed: {}", e)
    _run_async(_run())


def _intraday_job():
    async def _run():
        from app.services.market_data import MarketDataService
        from app.services.portfolio_tracker import PortfolioTracker
        from app.core.cache import cache
        try:
            holdings = await PortfolioTracker().get_holdings()
            if holdings:
                cache.set("portfolio_holdings", holdings, ttl=120)
        except Exception as e:
            logger.debug("Intraday job error: {}", e)
    _run_async(_run())


def _macro_refresh_job():
    async def _run():
        from app.services.market_data import MarketDataService
        from app.core.cache import cache
        try:
            macro = await MarketDataService().get_macro_snapshot()
            cache.set("macro_snapshot", macro, ttl=900)
        except Exception as e:
            logger.debug("Macro refresh failed: {}", e)
    _run_async(_run())


async def _send_notifications(predictions: list[dict]) -> None:
    from app.core.config import settings
    if not predictions:
        return
    primary = next((p for p in predictions if p.get("recommendation_type") == "primary"), None)
    if not primary:
        return
    msg = (
        f"Tonight's Best Setup: {primary['ticker']} "
        f"(Confidence: {primary['confidence_score']:.0f}%)\n"
        f"{primary['plain_english_explanation'][:200]}"
    )
    # Discord
    if settings.DISCORD_WEBHOOK_URL:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(settings.DISCORD_WEBHOOK_URL, json={"content": msg})
        except Exception as e:
            logger.debug("Discord notification failed: {}", e)
    # Telegram
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": msg}
                )
        except Exception as e:
            logger.debug("Telegram notification failed: {}", e)


def start_scheduler() -> BackgroundScheduler:
    """Create and start the background job scheduler."""
    scheduler = BackgroundScheduler(timezone="America/New_York")

    # Pre-market refresh at 6:30 AM ET
    scheduler.add_job(
        _pre_market_job,
        CronTrigger(hour=6, minute=30, timezone="America/New_York"),
        id="pre_market",
        name="Pre-Market Data Refresh",
        replace_existing=True,
    )

    # Intraday portfolio monitoring every 5 min during market hours
    scheduler.add_job(
        _intraday_job,
        CronTrigger(
            day_of_week="mon-fri",
            hour="9-16",
            minute="*/5",
            timezone="America/New_York",
        ),
        id="intraday_monitor",
        name="Intraday Portfolio Monitor",
        replace_existing=True,
    )

    # Macro snapshot refresh every 15 min
    scheduler.add_job(
        _macro_refresh_job,
        CronTrigger(minute="*/15", timezone="America/New_York"),
        id="macro_refresh",
        name="Macro Data Refresh",
        replace_existing=True,
    )

    # Nightly analysis at 8:00 PM ET (after market close + after-hours settle)
    scheduler.add_job(
        _nightly_scan_job,
        CronTrigger(
            day_of_week="mon-fri",
            hour=20,
            minute=0,
            timezone="America/New_York",
        ),
        id="nightly_scan",
        name="Nightly NASDAQ Scan",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with {} jobs", len(scheduler.get_jobs()))
    return scheduler
