"""Application configuration using Pydantic Settings - SQLite edition."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "AutoInvestor Intelligence System"
    VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "autoinvestor-dev-secret-change-in-production-32chars"

    # ── Database - SQLite by default ──────────────────────────────────────────
    DATABASE_URL: str = f"sqlite+aiosqlite:///{ROOT_DIR}/autoinvestor.db"
    DATABASE_ECHO: bool = False

    # ── Optional API keys (system works without them using yfinance) ──────────
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    POLYGON_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None

    # ── Notifications (all optional) ──────────────────────────────────────────
    DISCORD_WEBHOOK_URL: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    NOTIFICATION_EMAIL: Optional[str] = None

    # ── ML / Trading ──────────────────────────────────────────────────────────
    MIN_CONFIDENCE_THRESHOLD: float = 65.0
    MIN_CONFIDENCE_FOR_PRIMARY: float = 80.0
    MIN_CONFIDENCE_FOR_SECONDARY: float = 70.0
    MIN_VOLUME_THRESHOLD: int = 500_000
    MIN_PRICE_THRESHOLD: float = 5.0
    MAX_PORTFOLIO_POSITIONS: int = 10
    MAX_PREDICTIONS_PER_NIGHT: int = 10
    PORTFOLIO_INITIAL_CASH: float = 100_000.0
    MAX_POSITION_SIZE_PCT: float = 20.0
    DEFAULT_STOP_LOSS_PCT: float = 7.0

    # ── Market Hours (ET) ─────────────────────────────────────────────────────
    MARKET_OPEN_HOUR: int = 9
    MARKET_OPEN_MINUTE: int = 30
    MARKET_CLOSE_HOUR: int = 16
    TIMEZONE: str = "America/New_York"

    # ── Scheduler ────────────────────────────────────────────────────────────
    ENABLE_SCHEDULER: bool = True

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # ── Frontend ──────────────────────────────────────────────────────────────
    FRONTEND_DIST_PATH: str = str(ROOT_DIR / "frontend" / "dist")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() == "development"


settings = Settings()
