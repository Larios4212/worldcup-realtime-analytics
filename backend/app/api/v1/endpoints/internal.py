"""
Internal endpoints — only called by the ingestion service, not exposed publicly.
These are not authenticated because they run inside the Docker network.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy import select, text
from app.infra.db.session import AsyncSessionLocal
from app.infra.db.models import TeamModel, MatchModel
from app.infra.cache.redis import get_redis
import json

router = APIRouter()


# ── Match upsert ─────────────────────────────────────────────────────

class UpsertMatchPayload(BaseModel):
    id: str
    status: str
    minute: Optional[int] = None
    home_team: dict
    away_team: dict
    score: dict
    stage: str = "Group Stage"
    group: Optional[str] = None
    kickoff_utc: Optional[str] = None
    venue: Optional[str] = None


@router.post("/matches/upsert", status_code=200)
async def upsert_match(payload: UpsertMatchPayload):
    try:
        async with AsyncSessionLocal() as db:
            home_id = payload.home_team.get("id", "").strip()
            away_id = payload.away_team.get("id", "").strip()
            if not home_id or not away_id:
                return {"ok": True, "id": payload.id, "skipped": "no_teams"}

            await _upsert_team_raw(db, payload.home_team)
            await _upsert_team_raw(db, payload.away_team)

            kickoff = datetime.utcnow()
            if payload.kickoff_utc:
                try:
                    dt = datetime.fromisoformat(payload.kickoff_utc.replace("Z", "+00:00"))
                    kickoff = dt.replace(tzinfo=None)
                except ValueError:
                    pass

            result = await db.execute(select(MatchModel).where(MatchModel.id == payload.id))
            row = result.scalar_one_or_none()
            if row is None:
                row = MatchModel(
                    id=payload.id,
                    home_team_id=home_id,
                    away_team_id=away_id,
                    kickoff_utc=kickoff,
                    stage=payload.stage,
                    group=payload.group,
                    venue=payload.venue,
                    status=payload.status,
                    score_home=payload.score.get("home", 0),
                    score_away=payload.score.get("away", 0),
                    score_home_ht=payload.score.get("home_ht"),
                    score_away_ht=payload.score.get("away_ht"),
                    minute=payload.minute,
                )
                db.add(row)
            else:
                row.status = payload.status
                row.minute = payload.minute
                row.score_home = payload.score.get("home", 0)
                row.score_away = payload.score.get("away", 0)
                row.score_home_ht = payload.score.get("home_ht")
                row.score_away_ht = payload.score.get("away_ht")
                row.kickoff_utc = kickoff
                row.stage = payload.stage
                row.group = payload.group
                row.venue = payload.venue
            await db.commit()

        try:
            redis = await get_redis()
            event = {"type": "STATS_UPDATE", "match_id": payload.id,
                     "score": {"home": payload.score.get("home", 0), "away": payload.score.get("away", 0)},
                     "status": payload.status}
            await redis.publish(f"match:{payload.id}:events", json.dumps(event))
        except Exception:
            pass

        return {"ok": True, "id": payload.id}
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}\n{traceback.format_exc()}")


# ── Match stats enrichment ───────────────────────────────────────────

class MatchStatsPayload(BaseModel):
    shots_home: int = 0
    shots_away: int = 0
    shots_on_target_home: int = 0
    shots_on_target_away: int = 0
    shots_blocked_home: int = 0
    shots_blocked_away: int = 0
    possession_home: float = 50.0
    possession_away: float = 50.0
    corners_home: int = 0
    corners_away: int = 0
    offsides_home: int = 0
    offsides_away: int = 0
    fouls_home: int = 0
    fouls_away: int = 0
    yellow_cards_home: int = 0
    yellow_cards_away: int = 0
    red_cards_home: int = 0
    red_cards_away: int = 0
    passes_home: int = 0
    passes_away: int = 0
    pass_accuracy_home: float = 0.0
    pass_accuracy_away: float = 0.0
    xg_home: float = 0.0
    xg_away: float = 0.0
    data_source: str = "calculated"


@router.post("/match-stats/{match_id}", status_code=200)
async def upsert_match_stats(match_id: str, payload: MatchStatsPayload):
    """Store enriched match statistics."""
    try:
        async with AsyncSessionLocal() as db:
            # Update the matches table stats columns
            result = await db.execute(select(MatchModel).where(MatchModel.id == match_id))
            row = result.scalar_one_or_none()
            if row is None:
                return {"ok": False, "error": "match not found"}

            row.shots_home = payload.shots_home
            row.shots_away = payload.shots_away
            row.shots_on_target_home = payload.shots_on_target_home
            row.shots_on_target_away = payload.shots_on_target_away
            row.possession_home = payload.possession_home
            row.possession_away = payload.possession_away
            row.corners_home = payload.corners_home
            row.corners_away = payload.corners_away
            row.fouls_home = payload.fouls_home
            row.fouls_away = payload.fouls_away
            row.offsides_home = payload.offsides_home
            row.offsides_away = payload.offsides_away
            row.passes_home = payload.passes_home
            row.passes_away = payload.passes_away
            row.pass_accuracy_home = payload.pass_accuracy_home
            row.pass_accuracy_away = payload.pass_accuracy_away
            row.xg_home = payload.xg_home
            row.xg_away = payload.xg_away
            await db.commit()

            # Also upsert into match_stats_enriched
            await db.execute(text("""
                INSERT INTO match_stats_enriched (
                    match_id, shots_home, shots_away, shots_on_target_home, shots_on_target_away,
                    shots_blocked_home, shots_blocked_away, possession_home, possession_away,
                    corners_home, corners_away, offsides_home, offsides_away,
                    fouls_home, fouls_away, yellow_cards_home, yellow_cards_away,
                    red_cards_home, red_cards_away, passes_home, passes_away,
                    pass_accuracy_home, pass_accuracy_away, xg_home, xg_away,
                    data_source, updated_at
                ) VALUES (
                    :match_id, :shots_home, :shots_away, :shots_on_target_home, :shots_on_target_away,
                    :shots_blocked_home, :shots_blocked_away, :possession_home, :possession_away,
                    :corners_home, :corners_away, :offsides_home, :offsides_away,
                    :fouls_home, :fouls_away, :yellow_cards_home, :yellow_cards_away,
                    :red_cards_home, :red_cards_away, :passes_home, :passes_away,
                    :pass_accuracy_home, :pass_accuracy_away, :xg_home, :xg_away,
                    :data_source, NOW()
                )
                ON CONFLICT (match_id) DO UPDATE SET
                    shots_home = EXCLUDED.shots_home, shots_away = EXCLUDED.shots_away,
                    shots_on_target_home = EXCLUDED.shots_on_target_home,
                    shots_on_target_away = EXCLUDED.shots_on_target_away,
                    possession_home = EXCLUDED.possession_home,
                    possession_away = EXCLUDED.possession_away,
                    corners_home = EXCLUDED.corners_home, corners_away = EXCLUDED.corners_away,
                    fouls_home = EXCLUDED.fouls_home, fouls_away = EXCLUDED.fouls_away,
                    xg_home = EXCLUDED.xg_home, xg_away = EXCLUDED.xg_away,
                    data_source = EXCLUDED.data_source, updated_at = NOW()
            """), {**payload.model_dump(), "match_id": match_id})
            await db.commit()

        # Broadcast stats update to Redis
        try:
            redis = await get_redis()
            event = {"type": "STATS_UPDATE", "match_id": match_id,
                     "stats": payload.model_dump()}
            await redis.publish(f"match:{match_id}:events", json.dumps(event))
        except Exception:
            pass

        return {"ok": True, "match_id": match_id, "source": payload.data_source}
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}\n{traceback.format_exc()}")


# ── Team form upsert ─────────────────────────────────────────────────

class TeamFormPayload(BaseModel):
    team_id: str
    team_name: str
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    form_last5: str = ""
    form_points5: int = 0
    attack_rating: float = 50.0
    defense_rating: float = 50.0
    avg_goals_for: float = 0.0
    avg_goals_against: float = 0.0
    avg_shots: float = 0.0
    avg_shots_on_target: float = 0.0
    avg_possession: float = 50.0
    avg_corners: float = 0.0
    avg_fouls: float = 0.0
    clean_sheets: int = 0
    xg_scored_avg: float = 0.0
    xg_conceded_avg: float = 0.0
    elo: float = 1000.0


@router.post("/team-form/{team_id}", status_code=200)
async def upsert_team_form(team_id: str, payload: TeamFormPayload):
    """Store/update aggregated team performance stats."""
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("""
                INSERT INTO team_form (
                    team_id, team_name, played, wins, draws, losses,
                    goals_for, goals_against, form_last5, form_points5,
                    attack_rating, defense_rating, avg_goals_for, avg_goals_against,
                    avg_shots, avg_shots_on_target, avg_possession, avg_corners, avg_fouls,
                    clean_sheets, xg_scored_avg, xg_conceded_avg, updated_at
                ) VALUES (
                    :team_id, :team_name, :played, :wins, :draws, :losses,
                    :goals_for, :goals_against, :form_last5, :form_points5,
                    :attack_rating, :defense_rating, :avg_goals_for, :avg_goals_against,
                    :avg_shots, :avg_shots_on_target, :avg_possession, :avg_corners, :avg_fouls,
                    :clean_sheets, :xg_scored_avg, :xg_conceded_avg, NOW()
                )
                ON CONFLICT (team_id) DO UPDATE SET
                    played = EXCLUDED.played, wins = EXCLUDED.wins,
                    draws = EXCLUDED.draws, losses = EXCLUDED.losses,
                    goals_for = EXCLUDED.goals_for, goals_against = EXCLUDED.goals_against,
                    form_last5 = EXCLUDED.form_last5, form_points5 = EXCLUDED.form_points5,
                    attack_rating = EXCLUDED.attack_rating, defense_rating = EXCLUDED.defense_rating,
                    avg_goals_for = EXCLUDED.avg_goals_for, avg_goals_against = EXCLUDED.avg_goals_against,
                    avg_shots = EXCLUDED.avg_shots, avg_possession = EXCLUDED.avg_possession,
                    avg_corners = EXCLUDED.avg_corners, avg_fouls = EXCLUDED.avg_fouls,
                    clean_sheets = EXCLUDED.clean_sheets,
                    xg_scored_avg = EXCLUDED.xg_scored_avg, xg_conceded_avg = EXCLUDED.xg_conceded_avg,
                    updated_at = NOW()
            """), payload.model_dump())
            await db.commit()
        return {"ok": True, "team_id": team_id}
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}\n{traceback.format_exc()}")


# ── Prediction features upsert ───────────────────────────────────────

class PredictionFeaturesPayload(BaseModel):
    match_id: str
    home_attack_rating: float = 50.0
    home_defense_rating: float = 50.0
    away_attack_rating: float = 50.0
    away_defense_rating: float = 50.0
    home_form_points5: int = 7
    away_form_points5: int = 7
    home_played: int = 0
    away_played: int = 0
    home_avg_goals_for: float = 1.2
    home_avg_goals_against: float = 1.0
    away_avg_goals_for: float = 1.2
    away_avg_goals_against: float = 1.0
    expected_home_goals: float = 1.2
    expected_away_goals: float = 1.0
    prob_home_win: float = 0.333
    prob_draw: float = 0.333
    prob_away_win: float = 0.334


@router.post("/predictions", status_code=200)
async def upsert_prediction(payload: PredictionFeaturesPayload):
    """Store pre-computed ML features for a match."""
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("""
                INSERT INTO prediction_features (
                    match_id, home_attack_rating, home_defense_rating,
                    away_attack_rating, away_defense_rating,
                    home_form_points5, away_form_points5, home_played, away_played,
                    home_avg_goals_for, home_avg_goals_against,
                    away_avg_goals_for, away_avg_goals_against,
                    expected_home_goals, expected_away_goals,
                    prob_home_win, prob_draw, prob_away_win, computed_at
                ) VALUES (
                    :match_id, :home_attack_rating, :home_defense_rating,
                    :away_attack_rating, :away_defense_rating,
                    :home_form_points5, :away_form_points5, :home_played, :away_played,
                    :home_avg_goals_for, :home_avg_goals_against,
                    :away_avg_goals_for, :away_avg_goals_against,
                    :expected_home_goals, :expected_away_goals,
                    :prob_home_win, :prob_draw, :prob_away_win, NOW()
                )
                ON CONFLICT (match_id) DO UPDATE SET
                    prob_home_win = EXCLUDED.prob_home_win,
                    prob_draw = EXCLUDED.prob_draw,
                    prob_away_win = EXCLUDED.prob_away_win,
                    expected_home_goals = EXCLUDED.expected_home_goals,
                    expected_away_goals = EXCLUDED.expected_away_goals,
                    home_attack_rating = EXCLUDED.home_attack_rating,
                    away_attack_rating = EXCLUDED.away_attack_rating,
                    computed_at = NOW()
            """), payload.model_dump())
            await db.commit()
        return {"ok": True, "match_id": payload.match_id}
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}\n{traceback.format_exc()}")


# ── Helpers ─────────────────────────────────────────────────────────

async def _upsert_team_raw(db, team_data: dict) -> None:
    team_id = team_data.get("id", "").strip()
    if not team_id:
        return
    result = await db.execute(select(TeamModel).where(TeamModel.id == team_id))
    row = result.scalar_one_or_none()
    if row is None:
        db.add(TeamModel(
            id=team_id,
            name=team_data.get("name", ""),
            short_name=team_data.get("short_name", team_data.get("name", "")[:3].upper()),
            crest_url=team_data.get("crest_url"),
        ))
    else:
        if team_data.get("crest_url") and not row.crest_url:
            row.crest_url = team_data["crest_url"]

