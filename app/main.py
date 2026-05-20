"""FastAPI application factory."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.core.config import settings
from app.core.database import close_db, init_db

ROOT_DIR = Path(__file__).parent.parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AutoInvestor backend starting...")
    await init_db()

    if settings.ENABLE_SCHEDULER:
        from app.workers.scheduler import start_scheduler
        app.state.scheduler = start_scheduler()

    asyncio.create_task(_background_startup())
    yield

    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown(wait=False)
    await close_db()
    logger.info("AutoInvestor backend stopped.")


async def _background_startup():
    await asyncio.sleep(2)
    try:
        from app.services.market_data import MarketDataService
        macro = await MarketDataService().get_macro_snapshot()
        from app.core.cache import cache
        cache.set("macro_snapshot", macro, ttl=900)
        logger.info("Macro snapshot loaded. VIX={}", macro.get("vix", "?"))
    except Exception as e:
        logger.warning("Background startup partial failure: {}", e)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── API Routes ────────────────────────────────────────────────────────────
    from app.api.routes import predictions, portfolio, charts, sentiment, analytics, watchlist, ws
    app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
    app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
    app.include_router(charts.router, prefix="/api/charts", tags=["charts"])
    app.include_router(sentiment.router, prefix="/api/sentiment", tags=["sentiment"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
    app.include_router(watchlist.router, prefix="/api/watchlist", tags=["watchlist"])
    app.include_router(ws.router, tags=["websocket"])

    # ── Health ────────────────────────────────────────────────────────────────
    @app.get("/health", include_in_schema=False)
    async def health():
        return {"status": "ok", "app": settings.APP_NAME, "version": settings.VERSION}

    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error("Unhandled exception: {}", exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    # ── Frontend static files ─────────────────────────────────────────────────
    dist = Path(settings.FRONTEND_DIST_PATH)
    if dist.exists() and (dist / "index.html").exists():
        assets = dist / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_spa(full_path: str):
            if full_path.startswith(("api/", "docs", "redoc", "health", "ws")):
                return JSONResponse(status_code=404, content={"detail": "Not found"})
            return FileResponse(str(dist / "index.html"))
    else:
        dashboard = ROOT_DIR / "dashboard.html"
        if dashboard.exists():
            @app.get("/", include_in_schema=False)
            async def serve_dashboard():
                return FileResponse(str(dashboard))

    return app
