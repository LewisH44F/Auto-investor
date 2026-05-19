"""Discord notification service via webhooks."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from app.core.config import settings


class DiscordService:
    """Send notifications to Discord via webhook."""

    async def send_message(
        self,
        content: str,
        username: str = "AutoInvestor AI",
        embeds: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """Send a message to Discord webhook."""
        if not settings.DISCORD_WEBHOOK_URL:
            logger.debug("Discord webhook not configured")
            return False

        payload: Dict[str, Any] = {
            "username": username,
            "content": content[:2000],
        }

        if embeds:
            payload["embeds"] = embeds

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(settings.DISCORD_WEBHOOK_URL, json=payload)
                resp.raise_for_status()
                logger.info("Discord message sent")
                return True
        except Exception as exc:
            logger.error("Discord send failed: {}", exc)
            return False

    async def send_prediction_embed(
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
        """Send a rich embed for a prediction alert."""
        color = {
            "primary": 0x00FF00,    # green
            "secondary": 0xFFFF00,  # yellow
            "watchlist": 0x0099FF,  # blue
        }.get(recommendation_type, 0x888888)

        fields = []

        if entry_low and entry_high:
            fields.append({
                "name": "Entry Zone",
                "value": f"`${entry_low:.2f} - ${entry_high:.2f}`",
                "inline": True,
            })
        if stop_loss:
            fields.append({
                "name": "Stop Loss",
                "value": f"`${stop_loss:.2f}`",
                "inline": True,
            })
        if target:
            fields.append({
                "name": "Target",
                "value": f"`${target:.2f}`",
                "inline": True,
            })

        embed = {
            "title": f"{'🚨' if recommendation_type == 'primary' else '📊'} {recommendation_type.upper()}: {ticker}",
            "description": explanation[:1000],
            "color": color,
            "fields": [
                {"name": "Confidence", "value": f"**{confidence:.1f}%**", "inline": True},
                {"name": "Type", "value": recommendation_type.title(), "inline": True},
                *fields,
            ],
            "footer": {"text": "AutoInvestor AI • Not financial advice"},
        }

        return await self.send_message(
            content=f"New AI Signal: **{ticker}**",
            embeds=[embed],
        )
