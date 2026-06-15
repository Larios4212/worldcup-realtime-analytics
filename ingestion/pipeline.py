import asyncio
import json
import httpx
import redis.asyncio as aioredis
from tenacity import retry, stop_after_attempt, wait_exponential
from ingestion.config import IngestionConfig
from ingestion.normalizer import normalize_football_data_match


class IngestionPipeline:
    """
    Polls football-data.org API at a configurable interval,
    normalizes the response, and publishes events to Redis.
    """

    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self, config: IngestionConfig):
        self.config = config
        self._redis: aioredis.Redis | None = None
        self._http: httpx.AsyncClient | None = None

    async def run(self) -> None:
        self._redis = aioredis.from_url(self.config.REDIS_URL, decode_responses=True)
        self._http = httpx.AsyncClient(
            headers={"X-Auth-Token": self.config.FOOTBALL_DATA_API_KEY},
            timeout=10.0,
        )

        print(f"[ingestion] Starting pipeline. Poll interval: {self.config.POLL_INTERVAL_SECONDS}s")

        try:
            while True:
                await self._poll_live_matches()
                await asyncio.sleep(self.config.POLL_INTERVAL_SECONDS)
        finally:
            await self._http.aclose()
            await self._redis.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _poll_live_matches(self) -> None:
        url = f"{self.BASE_URL}/competitions/{self.config.COMPETITION_ID}/matches"
        params = {"status": "LIVE,IN_PLAY,PAUSED"}

        response = await self._http.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        matches = data.get("matches", [])

        print(f"[ingestion] Fetched {len(matches)} live matches")

        for raw_match in matches:
            match_payload = normalize_football_data_match(raw_match)
            channel = f"match:{match_payload['id']}:events"
            await self._redis.publish(channel, json.dumps(match_payload))

            # Also update the global live feed
            await self._redis.publish("live:all", json.dumps(match_payload))
