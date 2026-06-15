from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class TeamStatsResponse(BaseModel):
    team_id: str
    team_name: str
    matches_played: int
    wins: int
    draws: int
    losses: int
    goals_scored: int
    goals_conceded: int
    xg_for: float
    xg_against: float
    avg_possession: float
    pass_accuracy: float


@router.get("/teams/{team_id}", response_model=TeamStatsResponse)
async def get_team_stats(team_id: str):
    """Get aggregated tournament stats for a team."""
    # TODO: wire to DB query
    return TeamStatsResponse(
        team_id=team_id,
        team_name="Team",
        matches_played=0,
        wins=0,
        draws=0,
        losses=0,
        goals_scored=0,
        goals_conceded=0,
        xg_for=0.0,
        xg_against=0.0,
        avg_possession=50.0,
        pass_accuracy=0.0,
    )
