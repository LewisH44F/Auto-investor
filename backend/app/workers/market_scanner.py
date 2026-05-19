"""Market scanner worker for pre-market and intraday monitoring."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from loguru import logger

from app.core.database import AsyncSessionLocal


class MarketScanner:
    """Scans the market for opportunities in real-time."""

    async def run_pre_market_scan(self) -> List[Dict[str, Any]]:
        """
        Pre-market scan: Check pre-market movers and set up alerts.
        Runs at 6:00 AM EST.
        """
        from app.services.data_ingestion.market_data import MarketDataService

        logger.info("Pre-market scan starting at {}", datetime.now(timezone.utc))
        market_svc = MarketDataService()

        # Get watchlist tickers
        tickers = await market_svc.get_watchlist_tickers(limit=50)

        # Fetch batch quotes
        quotes = await market_svc.fetch_batch_quotes(tickers)

        movers = []
        for ticker, quote in quotes.items():
            pre_market = quote.get("pre_market_price")
            price = quote.get("price")

            if pre_market and price and price > 0:
                gap_pct = (pre_market / price - 1) * 100
                if abs(gap_pct) >= 2.0:  # >2% pre-market move
                    movers.append(
                        {
                            "ticker": ticker,
                            "price": price,
                            "pre_market_price": pre_market,
                            "gap_pct": round(gap_pct, 2),
                            "direction": "up" if gap_pct > 0 else "down",
                        }
                    )

        movers_sorted = sorted(movers, key=lambda x: abs(x["gap_pct"]), reverse=True)

        if movers_sorted:
            logger.info(
                "Pre-market movers found: {} tickers",
                len(movers_sorted),
            )
            for m in movers_sorted[:5]:
                logger.info(
                    "  {} pre-market {}{:.1f}%",
                    m["ticker"],
                    "+" if m["gap_pct"] > 0 else "",
                    m["gap_pct"],
                )

        return movers_sorted

    async def run_intraday_monitor(self) -> None:
        """
        Monitor active holdings and watchlist during market hours.
        Runs every 5 minutes 9:30-4PM EST.
        """
        from app.services.portfolio.risk_manager import RiskManager

        async with AsyncSessionLocal() as session:
            risk_mgr = RiskManager()

            # Check risk alerts
            try:
                risk_report = await risk_mgr.assess_portfolio_risk(session)
                alerts = risk_report.get("alerts", [])

                if alerts:
                    logger.warning("Portfolio risk alerts: {}", alerts)
                    await self._send_risk_alerts(alerts)

                await session.commit()
            except Exception as exc:
                logger.error("Intraday monitor error: {}", exc)

    async def _send_risk_alerts(self, alerts: List[str]) -> None:
        """Send risk alerts via configured notification channels."""
        from app.services.notifications.discord_service import DiscordService
        from app.services.notifications.telegram_service import TelegramService
        from app.core.config import settings

        if not alerts:
            return

        message = "⚠️ AutoInvestor Risk Alert:\n" + "\n".join(f"• {a}" for a in alerts)

        tasks = []
        if settings.DISCORD_WEBHOOK_URL:
            discord = DiscordService()
            tasks.append(discord.send_message(message))

        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            telegram = TelegramService()
            tasks.append(telegram.send_message(message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def scan_for_unusual_volume(
        self,
        tickers: Optional[List[str]] = None,
        threshold: float = 2.0,
    ) -> List[Dict[str, Any]]:
        """Scan for tickers with unusual volume activity."""
        from app.services.data_ingestion.market_data import MarketDataService

        market_svc = MarketDataService()

        if tickers is None:
            tickers = await market_svc.get_watchlist_tickers(limit=100)

        unusual = []
        # Process in chunks to avoid too many concurrent requests
        for i in range(0, len(tickers), 20):
            chunk = tickers[i : i + 20]
            tasks = [
                market_svc.detect_unusual_volume(t, threshold=threshold)
                for t in chunk
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for ticker, result in zip(chunk, results):
                if isinstance(result, bool) and result:
                    unusual.append({"ticker": ticker, "unusual_volume": True})

        logger.info(
            "Volume scan: {} / {} tickers with unusual volume",
            len(unusual),
            len(tickers),
        )
        return unusual
