"""
Internal endpoints — only called by the ingestion service, not exposed publicly.
These are not authenticated because they run inside the Docker network.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.domain.entities.match import Match, Team, Score, MatchStats, MatchStatus
from app.services.match_service import MatchService
from app.api.v1.dependencies import get_match_service

router = APIRouter()


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
async def upsert_match(
    payload: UpsertMatchPayload,
    service: MatchService = Depends(get_match_service),
):
    """Called by the ingestion service to persist / update a match."""
    try:
        status = MatchStatus(payload.status)
    except ValueError:
        status = MatchStatus.SCHEDULED

    kickoff = datetime.utcnow()
    if payload.kickoff_utc:
        try:
            kickoff = datetime.fromisoformat(payload.kickoff_utc.replace("Z", "+00:00"))
        except ValueError:
            pass

    match = Match(
        id=payload.id,
        home_team=Team(
            id=payload.home_team.get("id", ""),
            name=payload.home_team.get("name", ""),
            short_name=payload.home_team.get("short_name", ""),
            crest_url=payload.home_team.get("crest_url"),
        ),
        away_team=Team(
            id=payload.away_team.get("id", ""),
            name=payload.away_team.get("name", ""),
            short_name=payload.away_team.get("short_name", ""),
            crest_url=payload.away_team.get("crest_url"),
        ),
        status=status,
        kickoff_utc=kickoff,
        score=Score(
            home=payload.score.get("home", 0),
            away=payload.score.get("away", 0),
            home_ht=payload.score.get("home_ht"),
            away_ht=payload.score.get("away_ht"),
        ),
        stats=MatchStats(),
        minute=payload.minute,
        stage=payload.stage,
        group=payload.group,
        venue=payload.venue,
    )

    await service.update_match(match)
    return {"ok": True, "id": match.id}
