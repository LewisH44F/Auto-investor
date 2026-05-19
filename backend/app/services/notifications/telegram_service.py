"""Telegram notification service."""

from __future__ import annotations

from typing import Optional

import httpx
from loguru import logger

from app.core.config import settings


class TelegramService:
    """Send notifications via Telegram Bot API."""

    def __init__(self) -> None:
        self._base_url = (
            f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"
            if settings.TELEGRAM_BOT_TOKEN
            else None
        )

    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "Markdown",
    ) -> bool:
        """Send a Telegram message."""
        if not self._base_url or not settings.TELEGRAM_BOT_TOKEN:
            logger.debug("Telegram bot token not configured")
            return False

        chat = chat_id or settings.TELEGRAM_CHAT_ID
        if not chat:
            logger.warning("Telegram chat ID not configured")
            return False

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    f"{self._base_url}/sendMessage",
                    json={
                        "chat_id": chat,
                        "text": text[:4096],
                        "parse_mode": parse_mode,
                    },
                )
                resp.raise_for_status()
                logger.info("Telegram message sent to {}", chat)
                return True
        except Exception as exc:
            logger.error("Telegram send failed: {}", exc)
            return False

    async def send_prediction_alert(
        self,
        ticker: str,
        confidence: float,
        recommendation_type: str,
        explanation: str,
        entry_low: Optional[float] = None,
        entry_high: Optional[float] = None,
        stop_loss: Optional[float] = None,
        target: Optional[float] = None,
    ) -> bool:
        """Send formatted prediction alert."""
        icon = {"primary": "🚨", "secondary": "📊", "watchlist": "👀"}.get(
            recommendation_type, "📈"
        )

        lines = [
            f"{icon} *AutoInvestor AI - {recommendation_type.upper()} SIGNAL*",
            f"*Ticker:* `{ticker}`",
            f"*Confidence:* `{confidence:.1f}%`",
            "",
            explanation[:500],
            "",
        ]

        if entry_low and entry_high:
            lines.append(f"*Entry Zone:* `${entry_low:.2f} - ${entry_high:.2f}`")
        if stop_loss:
            lines.append(f"*Stop Loss:* `${stop_loss:.2f}`")
        if target:
            lines.append(f"*Target:* `${target:.2f}`")

        lines.append("\n_Not financial advice. Always DYOR._")

        return await self.send_message("\n".join(lines))
