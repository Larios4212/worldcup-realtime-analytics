from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from app.infra.db.session import AsyncSessionLocal

router = APIRouter()


class TeamFormResponse(BaseModel):
    team_id: str
    team_name: str
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_diff: int
    points: int
    form_last5: str
    attack_rating: float
    defense_rating: float
    avg_goals_for: float
    avg_goals_against: float
    avg_shots: float
    avg_shots_on_target: float
    avg_possession: float
    avg_corners: float
    avg_fouls: float
    clean_sheets: int
    xg_scored_avg: float
    xg_conceded_avg: float


class MatchStatsResponse(BaseModel):
    match_id: str
    shots_home: int
    shots_away: int
    shots_on_target_home: int
    shots_on_target_away: int
    shots_blocked_home: int
    shots_blocked_away: int
    possession_home: float
    possession_away: float
    corners_home: int
    corners_away: int
    offsides_home: int
    offsides_away: int
    fouls_home: int
    fouls_away: int
    yellow_cards_home: int
    yellow_cards_away: int
    red_cards_home: int
    red_cards_away: int
    passes_home: int
    passes_away: int
    pass_accuracy_home: float
    pass_accuracy_away: float
    xg_home: float
    xg_away: float
    data_source: str


@router.get("/teams/{team_id}", response_model=TeamFormResponse)
async def get_team_stats(team_id: str):
    """Get aggregated tournament stats and form for a team."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT * FROM team_form WHERE team_id = :tid"),
            {"tid": team_id},
        )
        row = result.mappings().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail=f"No stats found for team {team_id}")
        return TeamFormResponse(**dict(row))


@router.get("/matches/{match_id}", response_model=MatchStatsResponse)
async def get_match_stats(match_id: str):
    """Get detailed stats for a specific match."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            text("SELECT * FROM match_stats_enriched WHERE match_id = :mid"),
            {"mid": match_id},
        )
        row = result.mappings().one_or_none()
        if not row:
            raise HTTPException(status_code=404, detail=f"No enriched stats for match {match_id}")
        return MatchStatsResponse(**dict(row))


@router.get("/standings")
async def get_standings():
    """Get group standings with team form."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT
                tf.team_id, tf.team_name,
                m.group,
                tf.played, tf.wins, tf.draws, tf.losses,
                tf.goals_for, tf.goals_against,
                tf.goals_for - tf.goals_against AS goal_diff,
                tf.wins * 3 + tf.draws AS points,
                tf.form_last5, tf.attack_rating, tf.defense_rating
            FROM team_form tf
            JOIN teams t ON tf.team_id = t.id
            JOIN LATERAL (
                SELECT COALESCE(m2.group, 'Unknown') AS group
                FROM matches m2
                WHERE m2.home_team_id = tf.team_id OR m2.away_team_id = tf.team_id
                LIMIT 1
            ) m ON TRUE
            ORDER BY m.group, tf.wins * 3 + tf.draws DESC, tf.goals_for - tf.goals_against DESC
        """))
        rows = result.mappings().all()
        # Group by group
        standings: dict = {}
        for r in rows:
            g = r["group"] or "Unknown"
            if g not in standings:
                standings[g] = []
            standings[g].append(dict(r))
        return {"standings": standings, "total_teams": len(rows)}

