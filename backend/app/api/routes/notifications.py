"""Notification settings and management API routes."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.redis_client import cache_get, cache_set

router = APIRouter(prefix="/notifications", tags=["notifications"])

NOTIFICATION_SETTINGS_KEY = "notifications:settings"


class NotificationSettings(BaseModel):
    email_enabled: bool = False
    email_address: str = ""
    discord_enabled: bool = False
    discord_webhook: str = ""
    telegram_enabled: bool = False
    telegram_chat_id: str = ""
    notify_on_primary: bool = True
    notify_on_secondary: bool = True
    notify_on_watchlist: bool = False
    notify_on_stop_loss: bool = True
    notify_on_target: bool = True
    min_confidence_for_alert: float = 70.0


class TestNotificationRequest(BaseModel):
    channel: str  # email / discord / telegram


@router.get("/settings", response_model=NotificationSettings)
async def get_notification_settings() -> NotificationSettings:
    """Get current notification settings."""
    data = await cache_get(NOTIFICATION_SETTINGS_KEY)
    if data:
        return NotificationSettings(**data)
    return NotificationSettings(
        email_enabled=bool(settings.SMTP_USERNAME),
        discord_enabled=bool(settings.DISCORD_WEBHOOK_URL),
        telegram_enabled=bool(settings.TELEGRAM_BOT_TOKEN),
    )


@router.put("/settings", response_model=NotificationSettings)
async def update_notification_settings(
    payload: NotificationSettings,
) -> NotificationSettings:
    """Update notification settings."""
    await cache_set(
        NOTIFICATION_SETTINGS_KEY, payload.model_dump(), ttl=86400 * 365
    )
    return payload


@router.post("/test")
async def send_test_notification(
    request: TestNotificationRequest,
) -> Dict[str, Any]:
    """Send a test notification to verify setup."""
    channel = request.channel.lower()

    test_message = (
        "AutoInvestor AI - Test Notification\n"
        "This is a test message to confirm your notification channel is working correctly."
    )

    if channel == "discord":
        from app.services.notifications.discord_service import DiscordService

        svc = DiscordService()
        success = await svc.send_message(test_message)
        return {"channel": "discord", "success": success}

    elif channel == "telegram":
        from app.services.notifications.telegram_service import TelegramService

        svc = TelegramService()
        success = await svc.send_message(test_message)
        return {"channel": "telegram", "success": success}

    elif channel == "email":
        from app.services.notifications.email_service import EmailService

        svc = EmailService()
        success = await svc.send_email(
            subject="AutoInvestor - Test Notification",
            body=test_message,
        )
        return {"channel": "email", "success": success}

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown channel: {channel}. Use 'email', 'discord', or 'telegram'.",
        )


@router.get("/history")
async def get_notification_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent notification history."""
    data = await cache_get("notifications:history") or []
    return data[-limit:]
