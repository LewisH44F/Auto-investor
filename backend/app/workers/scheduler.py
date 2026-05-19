"""APScheduler-based task scheduler."""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from app.core.config import settings

_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)
    return _scheduler


async def _run_pre_market_scan() -> None:
    """6:00 AM EST - Pre-market scan."""
    logger.info("=== Running pre-market scan ===")
    from app.workers.market_scanner import MarketScanner

    scanner = MarketScanner()
    await scanner.run_pre_market_scan()


async def _run_intraday_monitor() -> None:
    """Every 5 min during market hours - monitor holdings."""
    logger.info("=== Running intraday monitor ===")
    from app.workers.market_scanner import MarketScanner

    scanner = MarketScanner()
    await scanner.run_intraday_monitor()


async def _run_nightly_analysis() -> None:
    """8:00 PM EST - Full nightly analysis."""
    logger.info("=== Running nightly analysis ===")
    from app.workers.nightly_analysis import NightlyAnalysisWorker

    worker = NightlyAnalysisWorker()
    await worker.run()


async def _run_feedback_recording() -> None:
    """10:00 PM EST - Record prediction outcomes."""
    logger.info("=== Recording prediction feedback ===")
    from app.core.database import AsyncSessionLocal
    from app.services.learning.feedback_engine import FeedbackEngine

    async with AsyncSessionLocal() as session:
        engine = FeedbackEngine()
        await engine.record_outcomes(session, days_after=3)
        await engine.record_model_performance(session)
        await session.commit()


async def _run_weekly_review() -> None:
    """Sunday 8 PM - Weekly model performance review."""
    logger.info("=== Running weekly model review ===")
    from app.core.database import AsyncSessionLocal
    from app.services.learning.pattern_detector import PatternDetector
    from app.services.learning.feedback_engine import FeedbackEngine

    async with AsyncSessionLocal() as session:
        detector = PatternDetector()
        await detector.detect_and_update(session)

        engine = FeedbackEngine()
        await engine.update_signal_weights(session)
        await session.commit()


def start_scheduler() -> None:
    """Register all scheduled tasks and start the scheduler."""
    if not settings.ENABLE_SCHEDULER:
        logger.info("Scheduler disabled (ENABLE_SCHEDULER=false)")
        return

    scheduler = get_scheduler()

    # Pre-market scan: 6:00 AM EST Mon-Fri
    scheduler.add_job(
        _run_pre_market_scan,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour=6,
            minute=0,
            timezone=settings.TIMEZONE,
        ),
        id="pre_market_scan",
        replace_existing=True,
    )

    # Intraday monitor: every 5 min, 9:30-16:00 EST Mon-Fri
    scheduler.add_job(
        _run_intraday_monitor,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour="9-15",
            minute="*/5",
            timezone=settings.TIMEZONE,
        ),
        id="intraday_monitor",
        replace_existing=True,
    )

    # Nightly analysis: 8:00 PM EST Mon-Fri
    scheduler.add_job(
        _run_nightly_analysis,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour=20,
            minute=0,
            timezone=settings.TIMEZONE,
        ),
        id="nightly_analysis",
        replace_existing=True,
    )

    # Feedback recording: 10:00 PM EST daily
    scheduler.add_job(
        _run_feedback_recording,
        trigger=CronTrigger(
            hour=22,
            minute=0,
            timezone=settings.TIMEZONE,
        ),
        id="feedback_recording",
        replace_existing=True,
    )

    # Weekly review: Sunday 8 PM EST
    scheduler.add_job(
        _run_weekly_review,
        trigger=CronTrigger(
            day_of_week="sun",
            hour=20,
            minute=0,
            timezone=settings.TIMEZONE,
        ),
        id="weekly_review",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "Scheduler started with {} jobs",
        len(scheduler.get_jobs()),
    )


def stop_scheduler() -> None:
    """Gracefully stop the scheduler."""
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
