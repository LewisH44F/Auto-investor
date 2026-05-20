"""WebSocket endpoint for live market updates."""
from __future__ import annotations

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

router = APIRouter()
_clients: list[WebSocket] = []


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await websocket.accept()
    _clients.append(websocket)
    logger.debug("WebSocket client connected. Total: {}", len(_clients))
    try:
        while True:
            snapshot = await _build_snapshot()
            await websocket.send_json(snapshot)
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug("WebSocket error: {}", e)
    finally:
        if websocket in _clients:
            _clients.remove(websocket)
        logger.debug("WebSocket client disconnected. Total: {}", len(_clients))


async def _build_snapshot() -> dict:
    from app.core.cache import cache
    macro = cache.get("macro_snapshot") or {}
    tonight = cache.get("tonight_predictions") or []
    primary = next((p for p in tonight if p.get("recommendation_type") == "primary"), None)
    return {
        "type": "market_update",
        "timestamp": datetime.utcnow().isoformat(),
        "vix": macro.get("vix", 0),
        "nasdaq_change_pct": macro.get("nasdaq_change_pct", 0),
        "market_condition": macro.get("market_condition", "NORMAL"),
        "tonight_top_pick": primary["ticker"] if primary else None,
        "tonight_confidence": primary["confidence_score"] if primary else None,
    }


async def broadcast(data: dict) -> None:
    """Broadcast a message to all connected WebSocket clients."""
    dead = []
    for ws in _clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in _clients:
            _clients.remove(ws)
