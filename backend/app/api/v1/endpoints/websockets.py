import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.infra.cache.redis import get_redis
from app.core.config import settings
from app.core.logging import logger

router = APIRouter()


@router.websocket("/matches/{match_id}")
async def match_events_ws(match_id: str, websocket: WebSocket):
    """
    WebSocket endpoint for real-time match events.

    Clients connect here and receive live updates:
    - Match events (goals, cards, substitutions)
    - Stats updates (possession, xG, shots)
    - Score changes
    """
    await websocket.accept()
    logger.info("ws_client_connected", match_id=match_id)

    redis = await get_redis()
    pubsub = redis.pubsub()
    channel = f"match:{match_id}:events"

    await pubsub.subscribe(channel)

    # Send heartbeat and listen for events concurrently
    async def heartbeat():
        while True:
            try:
                await asyncio.sleep(settings.WS_HEARTBEAT_INTERVAL)
                await websocket.send_json({"type": "PING"})
            except Exception:
                break

    heartbeat_task = asyncio.create_task(heartbeat())

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
    except WebSocketDisconnect:
        logger.info("ws_client_disconnected", match_id=match_id)
    except Exception as exc:
        logger.error("ws_error", match_id=match_id, error=str(exc))
    finally:
        heartbeat_task.cancel()
        await pubsub.unsubscribe(channel)
        await pubsub.close()


@router.websocket("/live")
async def all_live_matches_ws(websocket: WebSocket):
    """
    WebSocket endpoint for all live matches summary feed.
    Useful for dashboard overview showing all ongoing games.
    """
    await websocket.accept()
    logger.info("ws_live_dashboard_connected")

    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.psubscribe("match:*:events")

    try:
        async for message in pubsub.listen():
            if message["type"] == "pmessage":
                data = json.loads(message["data"])
                await websocket.send_json(data)
    except WebSocketDisconnect:
        logger.info("ws_live_dashboard_disconnected")
    finally:
        await pubsub.punsubscribe("match:*:events")
        await pubsub.close()
