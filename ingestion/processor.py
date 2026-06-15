"""
Match processor: after each match (or on startup), compute:
1. team_form — aggregated team stats
2. match_stats_enriched — real or calculated match stats
3. prediction_features — ML features for each upcoming match
4. head_to_head records

Run: python -c "import asyncio; from processor import MatchProcessor; from config import IngestionConfig; asyncio.run(MatchProcessor(IngestionConfig()).run_full_compute())"
"""
import asyncio
import httpx
from datetime import datetime
from typing import Optional
from config import IngestionConfig
from stats_engine import (
    estimate_match_stats,
    calculate_win_probabilities,
    update_elo,
    ELO_BASE,
)
from enricher import ApiFootballEnricher


class MatchProcessor:
    """Computes derived stats and ML features from raw match data."""

    def __init__(self, config: IngestionConfig):
        self.config = config
        self.enricher = ApiFootballEnricher(config)
        self._backend: Optional[httpx.AsyncClient] = None

    async def _get_backend(self) -> httpx.AsyncClient:
        if not self._backend:
            self._backend = httpx.AsyncClient(
                base_url=self.config.BACKEND_URL,
                timeout=30.0,
                follow_redirects=True,
            )
        return self._backend

    async def close(self):
        if self._backend:
            await self._backend.aclose()
        await self.enricher.close()

    async def run_full_compute(self) -> None:
        """Full recompute: process all finished matches, then compute predictions."""
        print("[processor] Starting full stats computation...")
        backend = await self._get_backend()

        # 1. Fetch all matches from backend
        r = await backend.get("/api/v1/matches")
        r.raise_for_status()
        all_matches = r.json().get("matches", [])
        finished = [m for m in all_matches if m["status"] in ("FINISHED",)]
        scheduled = [m for m in all_matches if m["status"] in ("SCHEDULED", "TIMED")]

        print(f"[processor] {len(finished)} finished, {len(scheduled)} scheduled")

        # 2. Build API-Football fixture map (if key available)
        if self.enricher._is_available():
            await self.enricher.build_fixture_map()

        # 3. Process finished matches
        team_elos: dict[str, float] = {}  # team_id -> ELO
        team_stats: dict[str, dict] = {}  # team_id -> aggregated

        for match in finished:
            match_id = match["id"]
            home_id = match["home_team"]["id"]
            away_id = match["away_team"]["id"]
            home_goals = match["score"]["home"]
            away_goals = match["score"]["away"]

            # Init team ELO/stats if needed
            for tid in (home_id, away_id):
                if tid not in team_elos:
                    team_elos[tid] = float(ELO_BASE)
                if tid not in team_stats:
                    team_stats[tid] = _empty_team_stats(match["home_team"]["name"] if tid == home_id else match["away_team"]["name"])

            home_elo = team_elos[home_id]
            away_elo = team_elos[away_id]

            # Try to get real stats from API-Football
            real_stats = None
            if self.enricher._is_available():
                real_stats = await self.enricher.get_match_stats(
                    match_id=match_id,
                    kickoff_utc=match.get("kickoff_utc", ""),
                    home_name=match["home_team"]["name"],
                    away_name=match["away_team"]["name"],
                )

            # Fall back to calculated stats
            stats = real_stats or estimate_match_stats(
                home_goals=home_goals,
                away_goals=away_goals,
                home_attack_rating=team_stats[home_id]["attack_rating"],
                away_attack_rating=team_stats[away_id]["attack_rating"],
                home_defense_rating=team_stats[home_id]["defense_rating"],
                away_defense_rating=team_stats[away_id]["defense_rating"],
                seed=int(match_id),
            )

            # Upsert match stats to backend
            await self._upsert_match_stats(backend, match_id, stats)

            # Determine outcome
            if home_goals > away_goals:
                home_score, away_score = 1.0, 0.0
                outcome = "HOME_WIN"
            elif home_goals < away_goals:
                home_score, away_score = 0.0, 1.0
                outcome = "AWAY_WIN"
            else:
                home_score, away_score = 0.5, 0.5
                outcome = "DRAW"

            # Update ELO
            team_elos[home_id], team_elos[away_id] = update_elo(home_elo, away_elo, home_score)

            # Update team form
            _update_team_stats(team_stats[home_id], home_goals, away_goals, home_score, stats, is_home=True)
            _update_team_stats(team_stats[away_id], away_goals, home_goals, away_score, stats, is_home=False)

            # Upsert to backend
            await self._upsert_team_form(backend, home_id, team_stats[home_id], team_elos[home_id])
            await self._upsert_team_form(backend, away_id, team_stats[away_id], team_elos[away_id])

            print(f"[processor] ✓ {match['home_team']['name']} {home_goals}-{away_goals} {match['away_team']['name']} ({stats['data_source']})")

        # 4. Compute predictions for scheduled matches
        for match in scheduled:
            home_id = match["home_team"]["id"]
            away_id = match["away_team"]["id"]

            if home_id not in team_elos or away_id not in team_elos:
                continue  # No data yet

            hs = team_stats.get(home_id, {})
            as_ = team_stats.get(away_id, {})

            p_home, p_draw, p_away = calculate_win_probabilities(
                home_elo=team_elos[home_id],
                away_elo=team_elos[away_id],
                home_avg_goals=hs.get("avg_goals_for", 1.2),
                away_avg_goals=as_.get("avg_goals_for", 1.2),
                home_form_points=hs.get("form_points5", 7),
                away_form_points=as_.get("form_points5", 7),
            )

            features = {
                "match_id": match["id"],
                "home_attack_rating": hs.get("attack_rating", 50.0),
                "home_defense_rating": hs.get("defense_rating", 50.0),
                "away_attack_rating": as_.get("attack_rating", 50.0),
                "away_defense_rating": as_.get("defense_rating", 50.0),
                "home_form_points5": hs.get("form_points5", 7),
                "away_form_points5": as_.get("form_points5", 7),
                "home_played": hs.get("played", 0),
                "away_played": as_.get("played", 0),
                "home_avg_goals_for": hs.get("avg_goals_for", 1.2),
                "home_avg_goals_against": hs.get("avg_goals_against", 1.0),
                "away_avg_goals_for": as_.get("avg_goals_for", 1.2),
                "away_avg_goals_against": as_.get("avg_goals_against", 1.0),
                "expected_home_goals": round(hs.get("avg_goals_for", 1.2) * (team_elos[home_id] / 1000), 3),
                "expected_away_goals": round(as_.get("avg_goals_for", 1.2) * (team_elos[away_id] / 1000), 3),
                "prob_home_win": p_home,
                "prob_draw": p_draw,
                "prob_away_win": p_away,
            }
            await self._upsert_prediction(backend, features)

        print(f"[processor] Done. Processed {len(finished)} matches, {len(team_stats)} teams, {len(scheduled)} predictions.")

    async def process_live_match(self, match: dict) -> None:
        """Process a single live/updated match stats."""
        backend = await self._get_backend()
        match_id = match["id"]
        home_goals = match["score"]["home"]
        away_goals = match["score"]["away"]
        minute = match.get("minute") or 90

        # For live matches, estimate stats based on current score + time played
        time_factor = min(1.0, minute / 90.0)
        real_stats = None
        if self.enricher._is_available():
            real_stats = await self.enricher.get_match_stats(
                match_id=match_id,
                kickoff_utc=match.get("kickoff_utc", ""),
                home_name=match["home_team"]["name"],
                away_name=match["away_team"]["name"],
            )

        stats = real_stats or estimate_match_stats(
            home_goals=home_goals,
            away_goals=away_goals,
            seed=int(match_id),
        )

        # Scale by time for live matches
        if not real_stats:
            for k in ("shots_home", "shots_away", "corners_home", "corners_away", "fouls_home", "fouls_away"):
                if k in stats:
                    stats[k] = max(
                        int(k.endswith("goals")),
                        round(stats[k] * time_factor)
                    )

        await self._upsert_match_stats(backend, match_id, stats)

    async def _upsert_match_stats(self, backend: httpx.AsyncClient, match_id: str, stats: dict) -> None:
        try:
            r = await backend.post(f"/api/v1/internal/match-stats/{match_id}", json=stats)
            if r.status_code not in (200, 201):
                print(f"[processor] Stats upsert failed for {match_id}: {r.status_code}")
        except Exception as e:
            print(f"[processor] Stats upsert error for {match_id}: {e}")

    async def _upsert_team_form(self, backend: httpx.AsyncClient, team_id: str, stats: dict, elo: float) -> None:
        try:
            payload = {**stats, "team_id": team_id, "elo": elo}
            r = await backend.post(f"/api/v1/internal/team-form/{team_id}", json=payload)
            if r.status_code not in (200, 201):
                print(f"[processor] Team form upsert failed for {team_id}: {r.status_code}")
        except Exception as e:
            print(f"[processor] Team form error for {team_id}: {e}")

    async def _upsert_prediction(self, backend: httpx.AsyncClient, features: dict) -> None:
        try:
            r = await backend.post("/api/v1/internal/predictions", json=features)
            if r.status_code not in (200, 201):
                print(f"[processor] Prediction upsert failed: {r.status_code}")
        except Exception as e:
            print(f"[processor] Prediction error: {e}")


# ──────────────────────────────────────────────────
# Team stats aggregation helpers
# ──────────────────────────────────────────────────

def _empty_team_stats(name: str) -> dict:
    return {
        "team_name": name,
        "played": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0,
        "form_last5": "",
        "form_points5": 0,
        "attack_rating": 50.0,
        "defense_rating": 50.0,
        "avg_goals_for": 0.0,
        "avg_goals_against": 0.0,
        "avg_shots": 0.0,
        "avg_shots_on_target": 0.0,
        "avg_possession": 50.0,
        "avg_corners": 0.0,
        "avg_fouls": 0.0,
        "clean_sheets": 0,
        "xg_scored_avg": 0.0,
        "xg_conceded_avg": 0.0,
    }


def _update_team_stats(ts: dict, goals_for: int, goals_against: int, score: float, stats: dict, is_home: bool) -> None:
    n = ts["played"] + 1
    ts["played"] = n
    ts["goals_for"] += goals_for
    ts["goals_against"] += goals_against

    if score == 1.0:
        ts["wins"] += 1
        form_char = "W"
    elif score == 0.5:
        ts["draws"] += 1
        form_char = "D"
    else:
        ts["losses"] += 1
        form_char = "L"

    # Rolling last-5 form
    form = ts["form_last5"] + form_char
    ts["form_last5"] = form[-5:]
    ts["form_points5"] = sum(3 if c == "W" else 1 if c == "D" else 0 for c in ts["form_last5"])

    # Averages (rolling)
    shots = stats["shots_home"] if is_home else stats["shots_away"]
    on_target = stats["shots_on_target_home"] if is_home else stats["shots_on_target_away"]
    possession = stats["possession_home"] if is_home else stats["possession_away"]
    corners = stats["corners_home"] if is_home else stats["corners_away"]
    fouls = stats["fouls_home"] if is_home else stats["fouls_away"]
    xg = stats["xg_home"] if is_home else stats["xg_away"]
    xg_against = stats["xg_away"] if is_home else stats["xg_home"]

    def _rolling(old_avg, new_val, n):
        return round((old_avg * (n - 1) + new_val) / n, 3)

    ts["avg_goals_for"] = _rolling(ts["avg_goals_for"], goals_for, n)
    ts["avg_goals_against"] = _rolling(ts["avg_goals_against"], goals_against, n)
    ts["avg_shots"] = _rolling(ts["avg_shots"], shots, n)
    ts["avg_shots_on_target"] = _rolling(ts["avg_shots_on_target"], on_target, n)
    ts["avg_possession"] = _rolling(ts["avg_possession"], possession, n)
    ts["avg_corners"] = _rolling(ts["avg_corners"], corners, n)
    ts["avg_fouls"] = _rolling(ts["avg_fouls"], fouls, n)
    ts["xg_scored_avg"] = _rolling(ts["xg_scored_avg"], xg, n)
    ts["xg_conceded_avg"] = _rolling(ts["xg_conceded_avg"], xg_against, n)

    if goals_against == 0:
        ts["clean_sheets"] += 1

    # Attack/Defense ratings (ELO-inspired, 0-100)
    # High goals scored = high attack; low goals conceded = high defense
    ts["attack_rating"] = min(95, max(5, round(
        50 + (ts["avg_goals_for"] - 1.2) * 20 + (ts["form_points5"] - 7) * 1.5
    )))
    ts["defense_rating"] = min(95, max(5, round(
        50 + (1.2 - ts["avg_goals_against"]) * 20 + (ts["clean_sheets"] / max(1, n)) * 20
    )))
