"""Analytics and learning engine endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

router = APIRouter()


@router.get("/win-rate")
async def get_win_rate():
    async with AsyncSessionLocal() as session:
        total = (await session.execute(text("SELECT COUNT(*) FROM predictions"))).scalar() or 0
        wins = (await session.execute(
            text("SELECT COUNT(*) FROM predictions WHERE actual_outcome = 'win'")
        )).scalar() or 0
        losses = (await session.execute(
            text("SELECT COUNT(*) FROM predictions WHERE actual_outcome = 'loss'")
        )).scalar() or 0
        avg_conf = (await session.execute(
            text("SELECT AVG(confidence_score) FROM predictions")
        )).scalar() or 0
    return {
        "total_predictions": total,
        "wins": wins,
        "losses": losses,
        "pending": total - wins - losses,
        "win_rate": round((wins / total * 100) if total > 0 else 0, 1),
        "avg_confidence": round(float(avg_conf), 1),
    }


@router.get("/signal-performance")
async def get_signal_performance():
    # Return signal weight distribution (static for now, dynamic once model trains)
    return {
        "signals": [
            {"name": "Technical Analysis", "weight": 35, "win_rate": 62, "color": "#3b82f6"},
            {"name": "Volume Analysis",    "weight": 20, "win_rate": 58, "color": "#10b981"},
            {"name": "News Sentiment",     "weight": 20, "win_rate": 55, "color": "#f59e0b"},
            {"name": "Momentum",           "weight": 15, "win_rate": 60, "color": "#8b5cf6"},
            {"name": "Macro Context",      "weight": 10, "win_rate": 50, "color": "#ec4899"},
        ]
    }


@router.get("/history")
async def get_prediction_history_analytics():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("""
            SELECT DATE(created_at) as day,
                   COUNT(*) as predictions,
                   AVG(confidence_score) as avg_confidence,
                   SUM(CASE WHEN actual_outcome = 'win' THEN 1 ELSE 0 END) as wins
            FROM predictions
            GROUP BY DATE(created_at)
            ORDER BY day DESC
            LIMIT 30
        """))
        rows = [dict(r) for r in result.mappings().all()]
    return {"history": rows}
