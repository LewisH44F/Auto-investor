"""Email notification service using aiosmtplib."""

from __future__ import annotations

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import aiosmtplib
from loguru import logger

from app.core.config import settings


class EmailService:
    """Async email notification sender."""

    async def send_email(
        self,
        subject: str,
        body: str,
        to_email: Optional[str] = None,
        html_body: Optional[str] = None,
    ) -> bool:
        """Send an email via SMTP."""
        if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
            logger.warning("Email not configured (missing SMTP credentials)")
            return False

        recipient = to_email or settings.NOTIFICATION_EMAIL
        if not recipient:
            logger.warning("No recipient email configured")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = recipient

            msg.attach(MIMEText(body, "plain"))
            if html_body:
                msg.attach(MIMEText(html_body, "html"))

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USERNAME,
                password=settings.SMTP_PASSWORD,
                start_tls=True,
            )

            logger.info("Email sent to {}: {}", recipient, subject)
            return True

        except Exception as exc:
            logger.error("Email send failed: {}", exc)
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
        """Send a formatted prediction alert email."""
        subject = f"🚨 AutoInvestor Alert: {recommendation_type.upper()} Signal - {ticker}"

        body_lines = [
            f"AutoInvestor AI - {recommendation_type.upper()} Signal",
            f"Ticker: {ticker}",
            f"Confidence: {confidence:.1f}%",
            f"",
            explanation,
            f"",
        ]

        if entry_low and entry_high:
            body_lines.append(f"Entry Zone: ${entry_low:.2f} - ${entry_high:.2f}")
        if stop_loss:
            body_lines.append(f"Stop Loss: ${stop_loss:.2f}")
        if target:
            body_lines.append(f"Target: ${target:.2f}")

        body_lines.extend([
            "",
            "⚠️ This is not financial advice. Always do your own research.",
            "AutoInvestor Intelligence System",
        ])

        return await self.send_email(
            subject=subject,
            body="\n".join(body_lines),
        )
