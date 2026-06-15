import json
from app.domain.interfaces.match_repository import IMatchEventPublisher
from app.core.logging import logger


class RedisMatchEventPublisher(IMatchEventPublisher):
    """Publishes match events to Redis Pub/Sub channels."""

    def __init__(self, redis):
        self._redis = redis

    async def publish(self, match_id: str, event: dict) -> None:
        channel = f"match:{match_id}:events"
        payload = json.dumps(event)
        await self._redis.publish(channel, payload)
        logger.debug("event_published", channel=channel, event_type=event.get("type"))

    async def subscribe(self, match_id: str):
        pubsub = self._redis.pubsub()
        channel = f"match:{match_id}:events"
        await pubsub.subscribe(channel)
        return pubsub
