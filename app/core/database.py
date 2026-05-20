"""Async SQLAlchemy database engine using SQLite + aiosqlite."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

ROOT_DIR = Path(__file__).parent.parent.parent
DB_PATH = ROOT_DIR / "autoinvestor.db"

DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"
SYNC_DATABASE_URL = f"sqlite:///{DB_PATH}"


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables and seed initial data."""
    # Import all models so Base knows about them
    from app.models import stock, prediction, portfolio, news, sentiment, learning, watchlist  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables initialised at {}", DB_PATH)
    await _seed_stocks()


def init_db_sync() -> None:
    """Called from main.py before async loop starts."""
    asyncio.run(init_db())


async def close_db() -> None:
    """Dispose the engine connection pool."""
    await engine.dispose()
    logger.info("Database engine disposed.")


# ── NASDAQ stock universe seed data ──────────────────────────────────────────

NASDAQ_SEED: list[tuple[str, str, str]] = [
    ("AAPL", "Apple Inc.", "Technology"),
    ("MSFT", "Microsoft Corporation", "Technology"),
    ("NVDA", "NVIDIA Corporation", "Technology"),
    ("GOOGL", "Alphabet Inc.", "Technology"),
    ("AMZN", "Amazon.com Inc.", "Consumer Discretionary"),
    ("META", "Meta Platforms Inc.", "Technology"),
    ("TSLA", "Tesla Inc.", "Consumer Discretionary"),
    ("AVGO", "Broadcom Inc.", "Technology"),
    ("COST", "Costco Wholesale Corporation", "Consumer Staples"),
    ("NFLX", "Netflix Inc.", "Communication Services"),
    ("AMD", "Advanced Micro Devices Inc.", "Technology"),
    ("ADBE", "Adobe Inc.", "Technology"),
    ("QCOM", "QUALCOMM Inc.", "Technology"),
    ("INTU", "Intuit Inc.", "Technology"),
    ("CSCO", "Cisco Systems Inc.", "Technology"),
    ("AMAT", "Applied Materials Inc.", "Technology"),
    ("PANW", "Palo Alto Networks Inc.", "Technology"),
    ("ADI", "Analog Devices Inc.", "Technology"),
    ("MRVL", "Marvell Technology Inc.", "Technology"),
    ("LRCX", "Lam Research Corporation", "Technology"),
    ("KLAC", "KLA Corporation", "Technology"),
    ("SNPS", "Synopsys Inc.", "Technology"),
    ("CDNS", "Cadence Design Systems Inc.", "Technology"),
    ("MELI", "MercadoLibre Inc.", "Consumer Discretionary"),
    ("REGN", "Regeneron Pharmaceuticals Inc.", "Healthcare"),
    ("GILD", "Gilead Sciences Inc.", "Healthcare"),
    ("ADP", "Automatic Data Processing Inc.", "Technology"),
    ("MDLZ", "Mondelez International Inc.", "Consumer Staples"),
    ("BKNG", "Booking Holdings Inc.", "Consumer Discretionary"),
    ("VRTX", "Vertex Pharmaceuticals Inc.", "Healthcare"),
    ("PYPL", "PayPal Holdings Inc.", "Technology"),
    ("ISRG", "Intuitive Surgical Inc.", "Healthcare"),
    ("MU", "Micron Technology Inc.", "Technology"),
    ("ORLY", "O'Reilly Automotive Inc.", "Consumer Discretionary"),
    ("MNST", "Monster Beverage Corporation", "Consumer Staples"),
    ("CRWD", "CrowdStrike Holdings Inc.", "Technology"),
    ("DDOG", "Datadog Inc.", "Technology"),
    ("ZS", "Zscaler Inc.", "Technology"),
    ("FTNT", "Fortinet Inc.", "Technology"),
    ("TEAM", "Atlassian Corporation", "Technology"),
    ("SNOW", "Snowflake Inc.", "Technology"),
    ("WDAY", "Workday Inc.", "Technology"),
    ("IDXX", "IDEXX Laboratories Inc.", "Healthcare"),
    ("FAST", "Fastenal Company", "Industrials"),
    ("ROST", "Ross Stores Inc.", "Consumer Discretionary"),
    ("VRSK", "Verisk Analytics Inc.", "Industrials"),
    ("PAYX", "Paychex Inc.", "Technology"),
    ("ANSS", "ANSYS Inc.", "Technology"),
    ("MCHP", "Microchip Technology Inc.", "Technology"),
    ("DXCM", "DexCom Inc.", "Healthcare"),
    ("MRNA", "Moderna Inc.", "Healthcare"),
    ("ON", "ON Semiconductor Corporation", "Technology"),
    ("PLTR", "Palantir Technologies Inc.", "Technology"),
    ("COIN", "Coinbase Global Inc.", "Financials"),
    ("ROKU", "Roku Inc.", "Technology"),
    ("PINS", "Pinterest Inc.", "Technology"),
    ("SNAP", "Snap Inc.", "Technology"),
    ("SQ", "Block Inc.", "Technology"),
    ("SHOP", "Shopify Inc.", "Technology"),
    ("ZM", "Zoom Video Communications Inc.", "Technology"),
    ("OKTA", "Okta Inc.", "Technology"),
    ("MDB", "MongoDB Inc.", "Technology"),
    ("NET", "Cloudflare Inc.", "Technology"),
    ("BILL", "BILL Holdings Inc.", "Technology"),
    ("HUBS", "HubSpot Inc.", "Technology"),
    ("CRM", "Salesforce Inc.", "Technology"),
    ("NOW", "ServiceNow Inc.", "Technology"),
    ("VEEV", "Veeva Systems Inc.", "Healthcare"),
    ("AMGN", "Amgen Inc.", "Healthcare"),
    ("BIIB", "Biogen Inc.", "Healthcare"),
    ("UBER", "Uber Technologies Inc.", "Technology"),
    ("LYFT", "Lyft Inc.", "Technology"),
    ("DASH", "DoorDash Inc.", "Consumer Discretionary"),
    ("ABNB", "Airbnb Inc.", "Consumer Discretionary"),
    ("EXPE", "Expedia Group Inc.", "Consumer Discretionary"),
    ("DKNG", "DraftKings Inc.", "Consumer Discretionary"),
    ("NXPI", "NXP Semiconductors NV", "Technology"),
    ("ASML", "ASML Holding NV", "Technology"),
    ("SBUX", "Starbucks Corporation", "Consumer Discretionary"),
    ("EXC", "Exelon Corporation", "Utilities"),
    ("DLTR", "Dollar Tree Inc.", "Consumer Staples"),
    ("MAR", "Marriott International Inc.", "Consumer Discretionary"),
    ("ODFL", "Old Dominion Freight Line Inc.", "Industrials"),
    ("CTAS", "Cintas Corporation", "Industrials"),
    ("CPRT", "Copart Inc.", "Industrials"),
    ("KDP", "Keurig Dr Pepper Inc.", "Consumer Staples"),
    ("AEP", "American Electric Power", "Utilities"),
    ("XEL", "Xcel Energy Inc.", "Utilities"),
    ("PCAR", "PACCAR Inc.", "Industrials"),
    ("RIVN", "Rivian Automotive Inc.", "Consumer Discretionary"),
    ("SOFI", "SoFi Technologies Inc.", "Financials"),
    ("AFRM", "Affirm Holdings Inc.", "Technology"),
    ("HOOD", "Robinhood Markets Inc.", "Financials"),
    ("RBLX", "Roblox Corporation", "Technology"),
    ("GTLB", "GitLab Inc.", "Technology"),
    ("CFLT", "Confluent Inc.", "Technology"),
    ("TWLO", "Twilio Inc.", "Technology"),
    ("U", "Unity Software Inc.", "Technology"),
    ("IONQ", "IonQ Inc.", "Technology"),
]


async def _seed_stocks() -> None:
    """Insert NASDAQ universe if stock table is empty."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM stocks"))
        count = result.scalar()
        if count == 0:
            logger.info("Seeding {} NASDAQ stocks into database...", len(NASDAQ_SEED))
            for ticker, name, sector in NASDAQ_SEED:
                await session.execute(
                    text(
                        "INSERT OR IGNORE INTO stocks "
                        "(ticker, name, sector, is_nasdaq, is_active) "
                        "VALUES (:t, :n, :s, 1, 1)"
                    ),
                    {"t": ticker, "n": name, "s": sector},
                )
            await session.commit()
            logger.info("Stock universe seeded successfully.")
        else:
            logger.debug("Stock table already has {} rows, skipping seed.", count)
