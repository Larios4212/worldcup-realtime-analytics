import asyncio
import json
import httpx
import redis.asyncio as aioredis
from tenacity import retry, stop_after_attempt, wait_exponential
from config import IngestionConfig
from normalizer import normalize_football_data_match, normalize_all_matches


class IngestionPipeline:
    """
    Polls football-data.org API at a configurable interval,
    normalizes the response, persists to the backend API, and
    publishes live events to Redis Pub/Sub.
    """

    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self, config: IngestionConfig):
        self.config = config
        self._redis: aioredis.Redis | None = None
        self._http: httpx.AsyncClient | None = None
        self._backend: httpx.AsyncClient | None = None

    async def run(self) -> None:
        self._redis = aioredis.from_url(self.config.REDIS_URL, decode_responses=True)
        self._http = httpx.AsyncClient(
            headers={"X-Auth-Token": self.config.FOOTBALL_DATA_API_KEY},
            timeout=15.0,
        )
        self._backend = httpx.AsyncClient(
            base_url=self.config.BACKEND_URL,
            timeout=10.0,
            follow_redirects=True,
        )

        print(f"[ingestion] Starting pipeline. Poll interval: {self.config.POLL_INTERVAL_SECONDS}s")

        # Seed all tournament matches on startup
        await self._seed_all_matches()

        try:
            while True:
                await self._poll_live_matches()
                await asyncio.sleep(self.config.POLL_INTERVAL_SECONDS)
        finally:
            await self._http.aclose()
            await self._backend.aclose()
            await self._redis.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30))
    async def _seed_all_matches(self) -> None:
        """Fetch all tournament matches and store via backend."""
        url = f"{self.BASE_URL}/competitions/{self.config.COMPETITION_ID}/matches"
        try:
            response = await self._http.get(url)
            response.raise_for_status()
            matches = response.json().get("matches", [])
            print(f"[ingestion] Seeding {len(matches)} total matches into DB")
            ok = 0
            for raw in matches:
                payload = normalize_football_data_match(raw)
                try:
                    r = await self._backend.post("/api/v1/internal/matches/upsert", json=payload)
                    if r.status_code == 200:
                        ok += 1
                except Exception as e:
                    print(f"[ingestion] Could not upsert match {payload.get('id')}: {e}")
            print(f"[ingestion] Seeded {ok}/{len(matches)} matches OK")
        except Exception as e:
            print(f"[ingestion] Seed failed (will use live-only mode): {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _poll_live_matches(self) -> None:
        url = f"{self.BASE_URL}/competitions/{self.config.COMPETITION_ID}/matches"
        params = {"status": "IN_PLAY,PAUSED"}

        response = await self._http.get(url, params=params)
        response.raise_for_status()

        matches = response.json().get("matches", [])
        print(f"[ingestion] {len(matches)} live matches")

        for raw_match in matches:
            payload = normalize_football_data_match(raw_match)
            channel = f"match:{payload['id']}:events"
            await self._redis.publish(channel, json.dumps(payload))
            await self._redis.publish("live:all", json.dumps(payload))

            # Keep DB in sync
            try:
                await self._backend.post("/api/v1/internal/matches/upsert", json=payload)
            except Exception:
                pass  # Redis broadcast already sent — DB sync is best-effort

