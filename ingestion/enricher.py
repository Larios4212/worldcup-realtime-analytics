"""
API-Football (api-sports.io) enrichment service.
Free tier: 100 requests/day.
Provides: shots, possession, corners, fouls, cards, passes, xG.

Register free at: https://www.api-football.com/dashboard
Set API_SPORTS_KEY in .env
"""
import asyncio
import httpx
from typing import Optional
from config import IngestionConfig

BASE_URL = "https://v3.football.api-sports.io"
# World Cup 2026 league ID in API-Football
WC_LEAGUE_ID = 1
WC_SEASON = 2026


class ApiFootballEnricher:
    """Fetches detailed match statistics from API-Football."""

    def __init__(self, config: IngestionConfig):
        self.config = config
        self._client: Optional[httpx.AsyncClient] = None
        # Cache: football-data match_id -> api-football fixture_id
        self._fixture_map: dict[str, int] = {}

    def _is_available(self) -> bool:
        key = self.config.API_SPORTS_KEY or ""
        return bool(key) and not key.startswith("your_api")

    async def _get_client(self) -> httpx.AsyncClient:
        if not self._client:
            self._client = httpx.AsyncClient(
                base_url=BASE_URL,
                headers={"x-apisports-key": self.config.API_SPORTS_KEY},
                timeout=15.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def build_fixture_map(self) -> None:
        """Fetch all WC 2026 fixtures from API-Football and build ID map."""
        if not self._is_available():
            return
        try:
            client = await self._get_client()
            r = await client.get(
                "/fixtures",
                params={"league": WC_LEAGUE_ID, "season": WC_SEASON},
            )
            r.raise_for_status()
            fixtures = r.json().get("response", [])
            for f in fixtures:
                fix = f.get("fixture", {})
                teams = f.get("teams", {})
                # Map by date + home/away team names (fuzzy approach)
                date_str = (fix.get("date") or "")[:10]
                home_name = teams.get("home", {}).get("name", "")
                away_name = teams.get("away", {}).get("name", "")
                key = f"{date_str}_{_normalize_name(home_name)}_{_normalize_name(away_name)}"
                self._fixture_map[key] = fix["id"]
            print(f"[enricher] Built fixture map with {len(self._fixture_map)} entries")
        except Exception as e:
            print(f"[enricher] Could not build fixture map: {e}")

    async def get_match_stats(
        self,
        match_id: str,
        kickoff_utc: str,
        home_name: str,
        away_name: str,
    ) -> Optional[dict]:
        """
        Returns enriched stats dict or None if not available.
        Stats dict keys: shots_home, shots_away, shots_on_target_home, shots_on_target_away,
        possession_home, possession_away, corners_home, corners_away,
        fouls_home, fouls_away, yellow_cards_home, yellow_cards_away,
        passes_home, passes_away, pass_accuracy_home, pass_accuracy_away,
        offsides_home, offsides_away, xg_home, xg_away
        """
        if not self._is_available():
            return None

        date_str = (kickoff_utc or "")[:10]
        lookup_key = f"{date_str}_{_normalize_name(home_name)}_{_normalize_name(away_name)}"
        fixture_id = self._fixture_map.get(lookup_key)

        if not fixture_id:
            # Rebuild map and retry once
            await self.build_fixture_map()
            fixture_id = self._fixture_map.get(lookup_key)

        if not fixture_id:
            print(f"[enricher] No fixture ID found for {home_name} vs {away_name} on {date_str}")
            return None

        try:
            client = await self._get_client()
            r = await client.get("/fixtures/statistics", params={"fixture": fixture_id})
            r.raise_for_status()
            data = r.json().get("response", [])
            return _parse_api_football_stats(data)
        except Exception as e:
            print(f"[enricher] Could not fetch stats for fixture {fixture_id}: {e}")
            return None


def _normalize_name(name: str) -> str:
    return name.lower().replace(" ", "_").replace("-", "_")


def _parse_api_football_stats(response: list) -> Optional[dict]:
    """Parse API-Football /fixtures/statistics response into internal format."""
    if not response or len(response) < 2:
        return None

    home_raw = {s["type"]: s["value"] for s in response[0].get("statistics", [])}
    away_raw = {s["type"]: s["value"] for s in response[1].get("statistics", [])}

    def _int(val) -> int:
        if val is None:
            return 0
        try:
            return int(str(val).replace("%", ""))
        except (ValueError, TypeError):
            return 0

    def _pct(val) -> float:
        if val is None:
            return 50.0
        try:
            return float(str(val).replace("%", ""))
        except (ValueError, TypeError):
            return 50.0

    def _float(val) -> float:
        if val is None:
            return 0.0
        try:
            return float(val)
        except (ValueError, TypeError):
            return 0.0

    return {
        "shots_home": _int(home_raw.get("Total Shots")),
        "shots_away": _int(away_raw.get("Total Shots")),
        "shots_on_target_home": _int(home_raw.get("Shots on Goal")),
        "shots_on_target_away": _int(away_raw.get("Shots on Goal")),
        "shots_blocked_home": _int(home_raw.get("Blocked Shots")),
        "shots_blocked_away": _int(away_raw.get("Blocked Shots")),
        "possession_home": _pct(home_raw.get("Ball Possession")),
        "possession_away": _pct(away_raw.get("Ball Possession")),
        "corners_home": _int(home_raw.get("Corner Kicks")),
        "corners_away": _int(away_raw.get("Corner Kicks")),
        "offsides_home": _int(home_raw.get("Offsides")),
        "offsides_away": _int(away_raw.get("Offsides")),
        "fouls_home": _int(home_raw.get("Fouls")),
        "fouls_away": _int(away_raw.get("Fouls")),
        "yellow_cards_home": _int(home_raw.get("Yellow Cards")),
        "yellow_cards_away": _int(away_raw.get("Yellow Cards")),
        "red_cards_home": _int(home_raw.get("Red Cards")),
        "red_cards_away": _int(away_raw.get("Red Cards")),
        "passes_home": _int(home_raw.get("Total passes")),
        "passes_away": _int(away_raw.get("Total passes")),
        "pass_accuracy_home": _pct(home_raw.get("Passes %")),
        "pass_accuracy_away": _pct(away_raw.get("Passes %")),
        "xg_home": _float(home_raw.get("expected_goals") or home_raw.get("xG")),
        "xg_away": _float(away_raw.get("expected_goals") or away_raw.get("xG")),
        "data_source": "api_football",
    }
