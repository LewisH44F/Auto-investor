"""FastAPI application entry point."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.redis_client import close_redis, init_redis

# ── Prometheus metrics ────────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "autoinvestor_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "autoinvestor_request_latency_seconds",
    "HTTP request latency",
    ["endpoint"],
)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application startup and shutdown lifecycle."""
    # Startup
    logger.info("Starting {} ({})", settings.APP_NAME, settings.APP_ENV)

    try:
        await init_db()
        logger.info("Database initialised")
    except Exception as exc:
        logger.error("Database init failed: {}", exc)

    try:
        await init_redis()
        logger.info("Redis connected")
    except Exception as exc:
        logger.warning("Redis init failed (continuing without cache): {}", exc)

    # Start background scheduler
    try:
        from app.workers.scheduler import start_scheduler
        start_scheduler()
    except Exception as exc:
        logger.warning("Scheduler start failed: {}", exc)

    yield

    # Shutdown
    logger.info("Shutting down...")

    try:
        from app.workers.scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass

    await close_redis()
    await close_db()
    logger.info("Shutdown complete")


# ── Application factory ───────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        description=(
            "AI-powered stock analysis platform providing intelligent predictions, "
            "portfolio tracking, and self-learning insights."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Request logging + metrics middleware ──────────────────────────────────
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next) -> Response:
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration = time.perf_counter() - start

        endpoint = request.url.path
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)

        if settings.DEBUG:
            logger.debug(
                "{} {} {} {:.3f}s",
                request.method,
                endpoint,
                response.status_code,
                duration,
            )

        return response

    # ── Routers ───────────────────────────────────────────────────────────────
    from app.api.routes import (
        analytics,
        backtesting,
        charts,
        notifications,
        portfolio,
        predictions,
        sentiment,
        watchlist,
    )

    api_prefix = settings.API_V1_PREFIX

    app.include_router(predictions.router, prefix=api_prefix)
    app.include_router(portfolio.router, prefix=api_prefix)
    app.include_router(analytics.router, prefix=api_prefix)
    app.include_router(charts.router, prefix=api_prefix)
    app.include_router(sentiment.router, prefix=api_prefix)
    app.include_router(watchlist.router, prefix=api_prefix)
    app.include_router(notifications.router, prefix=api_prefix)
    app.include_router(backtesting.router, prefix=api_prefix)

    # ── Built-in endpoints ────────────────────────────────────────────────────
    @app.get("/health", tags=["system"])
    async def health_check() -> dict:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": "1.0.0",
            "environment": settings.APP_ENV,
        }

    @app.get("/metrics", tags=["system"])
    async def prometheus_metrics() -> Response:
        """Prometheus metrics endpoint."""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    @app.get("/", tags=["system"])
    async def root() -> dict:
        return {
            "message": f"Welcome to {settings.APP_NAME}",
            "docs": "/docs",
            "health": "/health",
        }

    # ── Global exception handler ──────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled exception on {} {}: {}", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error. Please try again later.",
                "type": type(exc).__name__,
            },
        )

    return app


app = create_app()
