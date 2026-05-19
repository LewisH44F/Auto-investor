"""Application configuration using Pydantic Settings."""

from __future__ import annotations

import json
from typing import Any, List, Optional
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────────
    APP_NAME: str = "AutoInvestor Intelligence System"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-in-production-min-32-characters-long"
    API_V1_PREFIX: str = "/api"

    # ── Database ─────────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/autoinvestor"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    # ── Redis ────────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300  # seconds

    # ── External API Keys ────────────────────────────────────────────────────────
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    POLYGON_API_KEY: Optional[str] = None
    NEWS_API_KEY: Optional[str] = None
    FINNHUB_API_KEY: Optional[str] = None

    # ── Email (SMTP) ─────────────────────────────────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@autoinvestor.ai"
    SMTP_FROM_NAME: str = "AutoInvestor"
    NOTIFICATION_EMAIL: Optional[str] = None

    # ── Discord ──────────────────────────────────────────────────────────────────
    DISCORD_WEBHOOK_URL: Optional[str] = None

    # ── Telegram ─────────────────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # ── ML / Prediction ──────────────────────────────────────────────────────────
    MIN_CONFIDENCE_THRESHOLD: float = 65.0
    MIN_VOLUME_THRESHOLD: int = 500_000
    MIN_PRICE_THRESHOLD: float = 5.0
    MAX_PORTFOLIO_POSITIONS: int = 10
    MODEL_STORE_PATH: str = "./model_store"

    # ── Market Hours (ET) ────────────────────────────────────────────────────────
    MARKET_OPEN_HOUR: int = 9
    MARKET_OPEN_MINUTE: int = 30
    MARKET_CLOSE_HOUR: int = 16
    MARKET_CLOSE_MINUTE: int = 0
    PRE_MARKET_HOUR: int = 4
    AFTER_HOURS_CLOSE_HOUR: int = 20

    # ── CORS ─────────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    # ── Scheduler ────────────────────────────────────────────────────────────────
    ENABLE_SCHEDULER: bool = True
    TIMEZONE: str = "America/New_York"

    # ── Derived / computed ───────────────────────────────────────────────────────
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
